"""
budget.py — Budget analysis REST endpoint.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter
from models.schemas import BudgetAnalysisRequest, BudgetAnalysisResponse
from rag.chain import get_budget_insights

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/budget", tags=["budget"])


def compute_budget_analysis(req: BudgetAnalysisRequest) -> dict:
    income = req.monthly_income_inr
    expenses = req.monthly_expenses_inr
    savings = income - expenses
    savings_rate = (savings / income * 100) if income else 0

    recommended_needs = income * 0.50
    recommended_wants = income * 0.30
    recommended_savings = income * 0.20
    surplus = savings - recommended_savings

    # Tax saving opportunity (Section 80C — ₹1,50,000/year limit)
    annual_income = income * 12
    existing_investments = req.existing_investments_inr
    max_80c = 150000.0
    tax_saving_opportunity = max(0.0, max_80c - existing_investments)

    # Tax saved = opportunity × marginal_rate
    tax_rate = req.tax_bracket_pct / 100
    potential_tax_saved = tax_saving_opportunity * tax_rate

    emergency_fund_target = expenses * 6

    suggestions = []
    if savings_rate < 10:
        suggestions.append(
            f"🚨 Your savings rate is {savings_rate:.1f}% — critically low. "
            f"Target at least 20% (₹{recommended_savings:,.0f}/month). "
            f"Identify ₹{abs(surplus):,.0f} in expenses to cut."
        )
    elif savings_rate < 20:
        suggestions.append(
            f"📈 Your savings rate is {savings_rate:.1f}%. Good start, but aim for 20%+ "
            f"by reducing discretionary spend by ₹{abs(surplus):,.0f}/month."
        )
    else:
        suggestions.append(
            f"✅ Excellent savings rate of {savings_rate:.1f}%! "
            f"Put ₹{savings * 0.80:,.0f}/month into SIPs."
        )

    if tax_saving_opportunity > 0:
        suggestions.append(
            f"💰 You can save ₹{potential_tax_saved:,.0f} in taxes by investing "
            f"₹{tax_saving_opportunity:,.0f} more in 80C instruments "
            f"(ELSS, PPF, NPS). Monthly: ₹{tax_saving_opportunity/12:,.0f}."
        )

    if savings < emergency_fund_target:
        suggestions.append(
            f"🏦 Build an emergency fund of ₹{emergency_fund_target:,.0f} "
            f"(6 months of expenses) before aggressive investing."
        )

    return {
        "monthly_income": income,
        "monthly_expenses": expenses,
        "monthly_savings": savings,
        "savings_rate_pct": round(savings_rate, 2),
        "recommended_needs_inr": recommended_needs,
        "recommended_wants_inr": recommended_wants,
        "recommended_savings_inr": recommended_savings,
        "surplus_or_shortfall_inr": surplus,
        "tax_saving_opportunity_inr": tax_saving_opportunity,
        "potential_tax_saved_inr": potential_tax_saved,
        "emergency_fund_target_inr": emergency_fund_target,
        "suggestions": suggestions,
    }


@router.post("/analyze", response_model=BudgetAnalysisResponse)
async def analyze_budget(req: BudgetAnalysisRequest):
    """
    Analyze user's budget and return:
    - 50/30/20 breakdown vs actuals
    - Tax saving opportunities
    - Emergency fund status
    - AI-generated insights via GPT-4o
    """
    analysis = compute_budget_analysis(req)

    user_data = {
        "monthly_income_inr": req.monthly_income_inr,
        "monthly_expenses_inr": req.monthly_expenses_inr,
        "existing_investments_inr": req.existing_investments_inr,
        "tax_bracket_pct": req.tax_bracket_pct,
    }

    ai_insights = await get_budget_insights(user_data, analysis)

    return BudgetAnalysisResponse(
        **{k: v for k, v in analysis.items() if k in BudgetAnalysisResponse.model_fields},
        ai_insights=ai_insights,
    )