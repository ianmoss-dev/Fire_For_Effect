from dataclasses import dataclass


FREQUENCY_MULTIPLIERS = {
    "monthly": 1.0,
    "mid_month": 1.0,
    "end_month": 1.0,
    "semi_monthly": 2.0,
    "biweekly": 26 / 12,
    "weekly": 52 / 12,
    "quarterly": 1 / 3,
    "annual": 1 / 12,
}


@dataclass(frozen=True)
class IncomeStream:
    label: str
    amount: float
    frequency: str = "monthly"


@dataclass(frozen=True)
class BudgetCategory:
    label: str
    amount: float


@dataclass(frozen=True)
class BudgetLine:
    label: str
    group: str
    monthly_amount: float
    annual_amount: float
    pct_of_take_home: float


@dataclass(frozen=True)
class BudgetSummary:
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
    top_spending_categories: list[BudgetLine]
    category_breakdown: list[BudgetLine]
    cash_flow: list[BudgetLine]


def monthlyize_amount(amount: float, frequency: str) -> float:
    if amount < 0:
        raise ValueError("amount must be non-negative")

    key = frequency.lower().strip().replace("-", "_").replace(" ", "_")
    if key not in FREQUENCY_MULTIPLIERS:
        allowed = ", ".join(sorted(FREQUENCY_MULTIPLIERS))
        raise ValueError(f"Unsupported frequency '{frequency}'. Allowed: {allowed}")
    return amount * FREQUENCY_MULTIPLIERS[key]


def monthly_income_from_streams(income_streams: list[IncomeStream]) -> float:
    return sum(monthlyize_amount(stream.amount, stream.frequency) for stream in income_streams)


def summarize_budget(
    *,
    take_home_monthly: float | None = None,
    income_streams: list[IncomeStream] | None = None,
    fixed_expenses: list[BudgetCategory] | None = None,
    investments: list[BudgetCategory] | None = None,
    flexible_spending: list[BudgetCategory] | None = None,
) -> BudgetSummary:
    fixed_expenses = fixed_expenses or []
    investments = investments or []
    flexible_spending = flexible_spending or []

    if take_home_monthly is None:
        take_home_monthly = monthly_income_from_streams(income_streams or [])
    if take_home_monthly < 0:
        raise ValueError("take_home_monthly must be non-negative")

    fixed_total = _sum_categories(fixed_expenses)
    investments_total = _sum_categories(investments)
    flexible_total = _sum_categories(flexible_spending)
    planned_total = fixed_total + investments_total + flexible_total
    surplus = take_home_monthly - planned_total

    category_breakdown = (
        _build_lines(fixed_expenses, "fixed", take_home_monthly)
        + _build_lines(investments, "investments", take_home_monthly)
        + _build_lines(flexible_spending, "flexible", take_home_monthly)
    )
    top_spending_categories = sorted(
        [line for line in category_breakdown if line.group != "investments"],
        key=lambda line: line.monthly_amount,
        reverse=True,
    )[:5]

    cash_flow = [
        _line("Fixed expenses", "fixed", fixed_total, take_home_monthly),
        _line("Investments and savings", "investments", investments_total, take_home_monthly),
        _line("Flexible spending", "flexible", flexible_total, take_home_monthly),
    ]
    if surplus >= 0:
        cash_flow.append(_line("Unallocated surplus", "surplus", surplus, take_home_monthly))
    else:
        cash_flow.append(_line("Monthly deficit", "deficit", abs(surplus), take_home_monthly))

    status, status_message = _budget_status(take_home_monthly, surplus)

    return BudgetSummary(
        take_home_monthly=round(take_home_monthly, 2),
        take_home_annual=round(take_home_monthly * 12, 2),
        fixed_total=round(fixed_total, 2),
        investments_total=round(investments_total, 2),
        flexible_total=round(flexible_total, 2),
        planned_total=round(planned_total, 2),
        surplus=round(surplus, 2),
        surplus_annual=round(surplus * 12, 2),
        fixed_ratio=_ratio(fixed_total, take_home_monthly),
        investments_ratio=_ratio(investments_total, take_home_monthly),
        flexible_ratio=_ratio(flexible_total, take_home_monthly),
        planned_ratio=_ratio(planned_total, take_home_monthly),
        surplus_ratio=_ratio(surplus, take_home_monthly),
        status=status,
        status_message=status_message,
        top_spending_categories=top_spending_categories,
        category_breakdown=category_breakdown,
        cash_flow=cash_flow,
    )


def _sum_categories(categories: list[BudgetCategory]) -> float:
    total = 0.0
    for category in categories:
        if category.amount < 0:
            raise ValueError("budget category amounts must be non-negative")
        total += category.amount
    return total


def _build_lines(categories: list[BudgetCategory], group: str, take_home: float) -> list[BudgetLine]:
    return [_line(category.label, group, category.amount, take_home) for category in categories]


def _line(label: str, group: str, amount: float, take_home: float) -> BudgetLine:
    rounded_amount = round(amount, 2)
    return BudgetLine(
        label=label,
        group=group,
        monthly_amount=rounded_amount,
        annual_amount=round(rounded_amount * 12, 2),
        pct_of_take_home=_ratio(amount, take_home),
    )


def _ratio(amount: float, base: float) -> float:
    if base <= 0:
        return 0.0
    return round(amount / base, 4)


def _budget_status(take_home: float, surplus: float) -> tuple[str, str]:
    if take_home <= 0:
        return "missing_income", "Add take-home income to see your monthly picture."
    if surplus < -5:
        return "deficit", "Your plan spends more than your monthly take-home pay."
    if surplus > 5:
        return "surplus", "You have unallocated money available for debt, savings, or goals."
    return "balanced", "Your planned categories use your monthly take-home pay."
