"""
funds.py — REST endpoints for fund search, comparison, and recommendations.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from cache.redis_cache import get_all_funds_cache, get_user_profile
from models.schemas import FundCard, FundSearchRequest, RecommendationResponse, SIPAllocation
from rag.retriever import retrieve_funds

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/funds", tags=["funds"])


def score_fund(fund: dict, user_risk: str = "medium") -> float:
    """Composite scoring — same logic as in the architecture section."""
    weights = {
        "low":    {"ret": 0.25, "risk": 0.45, "qual": 0.30},
        "medium": {"ret": 0.40, "risk": 0.35, "qual": 0.25},
        "high":   {"ret": 0.60, "risk": 0.20, "qual": 0.20},
    }
    w = weights.get(user_risk, weights["medium"])
    import math
    r3 = float(fund.get("returns_3y") or 0)
    r5 = float(fund.get("returns_5y") or 0)
    cagr = 0.5 * r3 + 0.5 * r5
    ret_score = min(100, max(0, cagr * 5))
    sharpe = float(fund.get("sharpe_ratio") or 0)
    expense = float(fund.get("expense_ratio") or 1.5)
    risk_score = min(100, max(0, sharpe * 50 - max(0, (expense - 0.5) * 10)))
    stars = float(fund.get("rating_stars") or 3)
    aum = float(fund.get("aum_crores") or 100)
    qual_score = (stars / 5) * 60 + min(40, math.log10(max(1, aum)) * 10)
    return round(w["ret"] * ret_score + w["risk"] * risk_score + w["qual"] * qual_score, 2)


@router.get("/search", response_model=list[FundCard])
async def search_funds(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="equity|debt|hybrid|index"),
    risk: Optional[str] = Query(None, description="low|medium|high"),
    min_3y_return: float = Query(0.0, ge=0),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Semantic search over fund corpus via Pinecone.
    Supports optional metadata filters for category and risk.
    """
    user_profile = {
        "risk_appetite": risk or "medium",
        "investment_horizon": "long",
        "preferred_category": category,
    }

    docs = retrieve_funds(q, user_profile, top_k=limit * 2)

    results = []
    for doc in docs:
        meta = doc.metadata
        r3 = float(meta.get("returns_3y") or 0)
        if r3 < min_3y_return:
            continue
        results.append(FundCard(
            scheme_code=meta.get("scheme_code", ""),
            scheme_name=meta.get("scheme_name", ""),
            category=meta.get("broad_category", ""),
            nav=float(meta.get("nav", 0)),
            date="",
            returns_3y=r3,
            returns_5y=float(meta.get("returns_5y") or 0),
            sharpe_ratio=float(meta.get("sharpe_ratio") or 0),
            expense_ratio=float(meta.get("expense_ratio") or 0),
            aum_crores=float(meta.get("aum_crores") or 0),
            rating_stars=int(meta.get("rating_stars") or 3),
            risk_rating=meta.get("risk_rating", "moderate"),
            composite_score=score_fund(meta, risk or "medium"),
        ))

    results.sort(key=lambda f: f.composite_score or 0, reverse=True)
    return results[:limit]


@router.post("/compare", response_model=list[FundCard])
async def compare_funds(scheme_codes: list[str]):
    """Fetch details for 2-3 specific funds to compare side by side."""
    if len(scheme_codes) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 funds can be compared at once")
    if len(scheme_codes) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 fund scheme codes")

    funds_data = await get_all_funds_cache() or []
    code_set = set(scheme_codes)
    matched = [f for f in funds_data if f.get("scheme_code") in code_set]

    if not matched:
        raise HTTPException(status_code=404, detail="No fund data found for provided scheme codes")

    return [
        FundCard(
            scheme_code=f.get("scheme_code", ""),
            scheme_name=f.get("scheme_name", ""),
            category=f.get("broad_category", ""),
            nav=float(f.get("nav", 0)),
            date=f.get("date", ""),
            returns_3y=f.get("returns_3y"),
            returns_5y=f.get("returns_5y"),
            sharpe_ratio=f.get("sharpe_ratio"),
            expense_ratio=f.get("expense_ratio"),
            aum_crores=f.get("aum_crores"),
            rating_stars=f.get("rating_stars"),
            risk_rating=f.get("risk_rating", "moderate"),
        )
        for f in matched
    ]


@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(user_id: str, top_n: int = Query(10, ge=3, le=20)):
    """
    Generate personalized fund recommendations for a user.
    Reads user profile from Redis, applies scoring, returns top N funds.
    """
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please complete your risk profile first.",
        )

    query = _build_recommendation_query(profile)
    docs = retrieve_funds(query, profile, top_k=top_n * 3)

    funds = []
    for doc in docs:
        meta = doc.metadata
        funds.append(FundCard(
            scheme_code=meta.get("scheme_code", ""),
            scheme_name=meta.get("scheme_name", ""),
            category=meta.get("broad_category", ""),
            nav=float(meta.get("nav", 0)),
            date="",
            returns_3y=float(meta.get("returns_3y") or 0),
            returns_5y=float(meta.get("returns_5y") or 0),
            sharpe_ratio=float(meta.get("sharpe_ratio") or 0),
            expense_ratio=float(meta.get("expense_ratio") or 1.5),
            aum_crores=float(meta.get("aum_crores") or 0),
            rating_stars=int(meta.get("rating_stars") or 3),
            risk_rating=meta.get("risk_rating", "moderate"),
            composite_score=score_fund(meta, profile.get("risk_appetite", "medium")),
        ))

    funds.sort(key=lambda f: f.composite_score or 0, reverse=True)
    top_funds = funds[:top_n]

    investable = float(profile.get("investable_surplus_inr", 5000))
    allocations = _build_sip_allocations(top_funds, investable, profile)

    return RecommendationResponse(
        user_id=user_id,
        total_investable_inr=investable,
        allocations=allocations,
        top_funds=top_funds,
        ai_summary=f"Based on your {profile.get('risk_appetite')} risk profile and "
                   f"{profile.get('investment_horizon')}-term horizon, here are your top picks.",
    )


def _build_recommendation_query(profile: dict) -> str:
    risk = profile.get("risk_appetite", "medium")
    horizon = profile.get("investment_horizon", "long")
    goals = profile.get("financial_goals", [])
    query = f"best mutual funds for {risk} risk {horizon} term investment"
    if "retirement" in goals:
        query += " retirement planning"
    if "tax" in str(goals).lower():
        query += " tax saving ELSS"
    return query


def _build_sip_allocations(
    funds: list[FundCard],
    total_investable: float,
    profile: dict,
) -> list[SIPAllocation]:
    risk = profile.get("risk_appetite", "medium")
    age = int(profile.get("age", 30))

    # Age-based equity percentage
    equity_pct = max(20, min(80, 100 - age))
    debt_pct = 100 - equity_pct

    equity_funds = [f for f in funds if f.category == "equity"][:3]
    debt_funds = [f for f in funds if f.category in ("debt", "hybrid")][:2]

    allocations = []

    if equity_funds:
        per_eq = (total_investable * equity_pct / 100) / len(equity_funds)
        for f in equity_funds:
            allocations.append(SIPAllocation(
                fund_name=f.scheme_name,
                scheme_code=f.scheme_code,
                monthly_sip_inr=round(per_eq / 500) * 500,
                category=f.category,
                expected_cagr_pct=f.returns_5y or f.returns_3y or 12.0,
                risk_level="high",
                reason=f"Equity growth — {100-age}% equity allocation for age {age}",
            ))

    if debt_funds:
        per_debt = (total_investable * debt_pct / 100) / len(debt_funds)
        for f in debt_funds:
            allocations.append(SIPAllocation(
                fund_name=f.scheme_name,
                scheme_code=f.scheme_code,
                monthly_sip_inr=round(per_debt / 500) * 500,
                category=f.category,
                expected_cagr_pct=f.returns_3y or 7.0,
                risk_level="low",
                reason="Debt stability — balances portfolio risk",
            ))

    return allocations