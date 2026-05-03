from typing import Literal

from pydantic import BaseModel, Field


BudgetFrequency = Literal[
    "monthly",
    "mid_month",
    "end_month",
    "semi_monthly",
    "biweekly",
    "weekly",
    "quarterly",
    "annual",
]


class IncomeStreamInput(BaseModel):
    label: str = Field(..., min_length=1, examples=["Mid-month pay"])
    amount: float = Field(..., ge=0, examples=[2400])
    frequency: BudgetFrequency = "monthly"


class BudgetCategoryInput(BaseModel):
    label: str = Field(..., min_length=1, examples=["Groceries"])
    amount: float = Field(..., ge=0, examples=[650])


class BudgetSummaryRequest(BaseModel):
    take_home_monthly: float | None = Field(None, ge=0)
    income_streams: list[IncomeStreamInput] = Field(default_factory=list)
    fixed_expenses: list[BudgetCategoryInput] = Field(default_factory=list)
    investments: list[BudgetCategoryInput] = Field(default_factory=list)
    flexible_spending: list[BudgetCategoryInput] = Field(default_factory=list)


class BudgetLineResponse(BaseModel):
    label: str
    group: str
    monthly_amount: float
    annual_amount: float
    pct_of_take_home: float


class BudgetSummaryResponse(BaseModel):
    take_home_monthly: float
    take_home_annual: float
    fixed_total: float
    investments_total: float
    flexible_total: float
    planned_total: float
    surplus: float
    surplus_annual: float
    fixed_ratio: float
    investments_ratio: float
    flexible_ratio: float
    planned_ratio: float
    surplus_ratio: float
    status: str
    status_message: str
    top_spending_categories: list[BudgetLineResponse]
    category_breakdown: list[BudgetLineResponse]
    cash_flow: list[BudgetLineResponse]
