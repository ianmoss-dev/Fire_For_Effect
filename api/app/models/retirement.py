from pydantic import BaseModel, Field


class SavingsRateRequest(BaseModel):
    target_nest_egg: float = Field(..., ge=0)
    current_tsp: float = Field(0.0, ge=0)
    base_pay_schedule: list[float] = Field(default_factory=list)
    civilian_monthly: float = Field(0.0, ge=0)
    mil_months: int = Field(..., ge=0)
    total_months: int = Field(..., ge=1)
    allocation: dict[str, float] = Field(default_factory=lambda: {"L": 1.0})
    inflation_rate: float = Field(0.025, ge=0)
    prebuilt_income_schedule: list[float] | None = None


class SavingsRateResponse(BaseModel):
    savings_rate: float
    savings_rate_pct: float
    first_month_contribution: float
    average_monthly_contribution: float
    final_projected_balance: float
    contribution_schedule: list[float]


class MonteCarloRequest(BaseModel):
    current_age: float = Field(..., ge=0)
    retire_age: float = Field(..., gt=0)
    initial_balance: float = Field(0.0, ge=0)
    monthly_contribution: float | list[float] = 0.0
    l_fund_weight: float = Field(0.0, ge=0, le=1)
    manual_allocation: dict[str, float] = Field(default_factory=dict)
    inflation_rate: float = Field(0.025, ge=0)
    trials: int = Field(1000, ge=1, le=5000)
    target_balance: float = Field(..., ge=0)
    seed: int | None = None


class MonteCarloYearPoint(BaseModel):
    month: int
    year: int
    p10: float
    p50: float
    p90: float


class MonteCarloResponse(BaseModel):
    months: int
    trials: int
    success_rate: float
    final_p10: float
    final_p50: float
    final_p90: float
    yearly_points: list[MonteCarloYearPoint]
