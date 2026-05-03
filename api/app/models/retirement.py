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

