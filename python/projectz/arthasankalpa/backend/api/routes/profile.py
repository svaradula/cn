"""
profile.py — User profile CRUD endpoints.
Stores profiles in Redis for fast retrieval during chat.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from models.schemas import UserProfileCreate, UserProfileResponse
from cache.redis_cache import get_user_profile, set_user_profile
from rag.chain import get_risk_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post("", response_model=UserProfileResponse)
async def create_or_update_profile(profile: UserProfileCreate):
    savings = profile.monthly_income_inr - profile.monthly_expenses_inr
    surplus = savings * 0.80
    savings_rate = (savings / profile.monthly_income_inr * 100) if profile.monthly_income_inr else 0

    equity_pct = max(20, min(80, 100 - profile.age))
    risk_score = min(100, max(0,
        (60 - profile.age) +
        int(savings_rate) +
        {"short": 0, "medium": 15, "long": 30}.get(profile.investment_horizon, 15)
    ))

    profile_dict = profile.model_dump()
    profile_dict.update({
        "monthly_savings_inr": savings,
        "investable_surplus_inr": surplus,
        "savings_rate_pct": round(savings_rate, 2),
        "risk_score": risk_score,
        "equity_allocation_pct": equity_pct,
    })

    await set_user_profile(profile.user_id, profile_dict)

    return UserProfileResponse(
        **profile.model_dump(),
        monthly_savings_inr=savings,
        investable_surplus_inr=surplus,
        savings_rate_pct=round(savings_rate, 2),
        risk_score=risk_score,
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: str):
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfileResponse(**profile)


@router.post("/{user_id}/risk-analysis")
async def analyze_risk(user_id: str):
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    analysis = await get_risk_profile(profile)
    return {"analysis": analysis}