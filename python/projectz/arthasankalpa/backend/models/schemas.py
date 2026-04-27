"""
schemas.py - All Pydantic request/response models.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class RiskAppetite(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class InvestmentHorizon(str, Enum):
    SHORT  = "short"    # < 1 year
    MEDIUM = "medium"   # 1-3 years
    LONG   = "long"     # 3+ years


class BroadCategory(str, Enum):
    EQUITY = "equity"
    DEBT   = "debt"
    HYBRID = "hybrid"
    INDEX  = "index"
    OTHER  = "other"


# ── User Profile ──────────────────────────────────────────────────────────────

class UserProfileCreate(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=64)
    age: int = Field(..., ge=18, le=75)
    monthly_income_inr: float = Field(..., gt=0)
    monthly_expenses_inr: float = Field(..., ge=0)
    existing_investments_inr: float = Field(0.0, ge=0)
    risk_appetite: RiskAppetite
    investment_horizon: InvestmentHorizon
    financial_goals: list[str] = Field(default_factory=list)
    tax_bracket_pct: float = Field(30.0, ge=0, le=42.744)

    @field_validator("monthly_expenses_inr")
    @classmethod
    def expenses_lt_income(cls, v: float, info) -> float:
        income = info.data.get("monthly_income_inr", 0)
        if income and v >= income:
            raise ValueError("Monthly expenses cannot exceed income")
        return v


# UserProfileResponse is a flat model (does NOT inherit UserProfileCreate)
# to avoid Pydantic warning about computed-property vs field shadowing.
class UserProfileResponse(BaseModel):
    # --- same fields as UserProfileCreate ---
    user_id: str
    age: int
    monthly_income_inr: float
    monthly_expenses_inr: float
    existing_investments_inr: float
    risk_appetite: RiskAppetite
    investment_horizon: InvestmentHorizon
    financial_goals: list[str]
    tax_bracket_pct: float
    # --- extra computed fields ---
    monthly_savings_inr: float
    investable_surplus_inr: float
    savings_rate_pct: float
    risk_score: int


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_id: str
    query: str = Field(..., min_length=2, max_length=2000)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    mode: str = Field("advisor")


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    mode: str


# ── Fund ──────────────────────────────────────────────────────────────────────

class FundSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    category: Optional[BroadCategory] = None
    risk: Optional[RiskAppetite] = None
    min_3y_return: float = 0.0
    sort_by: str = "composite_score"
    limit: int = Field(20, ge=1, le=50)


class FundCard(BaseModel):
    scheme_code: str
    scheme_name: str
    category: str
    nav: float
    date: str
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    expense_ratio: Optional[float] = None
    aum_crores: Optional[float] = None
    rating_stars: Optional[int] = None
    risk_rating: str = "moderate"
    composite_score: Optional[float] = None


# ── Budget ────────────────────────────────────────────────────────────────────

class BudgetAnalysisRequest(BaseModel):
    user_id: str
    monthly_income_inr: float = Field(..., gt=0)
    monthly_expenses_inr: float = Field(..., ge=0)
    existing_investments_inr: float = 0.0
    tax_bracket_pct: float = 30.0


class BudgetAnalysisResponse(BaseModel):
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    savings_rate_pct: float
    recommended_needs_inr: float
    recommended_wants_inr: float
    recommended_savings_inr: float
    surplus_or_shortfall_inr: float
    tax_saving_opportunity_inr: float
    emergency_fund_target_inr: float
    suggestions: list[str]
    ai_insights: str


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    user_id: str
    top_n: int = Field(10, ge=3, le=20)


class SIPAllocation(BaseModel):
    fund_name: str
    scheme_code: str
    monthly_sip_inr: float
    category: str
    expected_cagr_pct: float
    risk_level: str
    reason: str


class RecommendationResponse(BaseModel):
    user_id: str
    total_investable_inr: float
    allocations: list[SIPAllocation]
    top_funds: list[FundCard]
    ai_summary: str