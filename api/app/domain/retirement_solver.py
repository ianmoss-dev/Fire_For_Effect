from app.domain.investment import FUND_NOMINAL_RATES, get_lifecycle_allocation


def build_monthly_real_rates(total_months, allocation, inflation_rate):
    monthly_inflation = (1 + inflation_rate) ** (1 / 12) - 1
    l_weight = allocation.get("L", 0.0)
    manual_allocation = {fund: weight for fund, weight in allocation.items() if fund != "L"}
    funds = ("C", "S", "I", "F", "G")

    monthly_rates = []
    for month in range(total_months):
        years_left = (total_months - month) / 12
        month_allocation = manual_allocation.copy()

        if l_weight > 0:
            lifecycle_allocation = get_lifecycle_allocation(years_left)
            for fund, weight in lifecycle_allocation.items():
                month_allocation[fund] = month_allocation.get(fund, 0) + (l_weight * weight)

        nominal = sum(month_allocation.get(fund, 0) * FUND_NOMINAL_RATES.get(fund, 0) for fund in funds)
        real = (1 + nominal) ** (1 / 12) / (1 + monthly_inflation) - 1
        monthly_rates.append(real)

    return monthly_rates


def build_income_schedule(base_pay_schedule, civilian_monthly, mil_months, total_months, prebuilt_income_schedule=None):
    if prebuilt_income_schedule is not None:
        return list(prebuilt_income_schedule)

    income_schedule = list(base_pay_schedule)
    for _ in range(total_months - mil_months):
        income_schedule.append(civilian_monthly)
    return income_schedule


def project_balance(current_tsp, contribution_schedule, monthly_rates):
    balance = current_tsp
    for contribution, monthly_rate in zip(contribution_schedule, monthly_rates):
        balance = balance * (1 + monthly_rate) + contribution
    return balance


def solve_savings_rate(
    target_nest_egg,
    current_tsp,
    base_pay_schedule,
    civilian_monthly,
    mil_months,
    total_months,
    allocation,
    inflation_rate,
    prebuilt_income_schedule=None,
):
    """
    Binary search for the constant percentage of income needed to reach target.
    """
    monthly_rates = build_monthly_real_rates(total_months, allocation, inflation_rate)
    income_schedule = build_income_schedule(
        base_pay_schedule,
        civilian_monthly,
        mil_months,
        total_months,
        prebuilt_income_schedule,
    )

    def simulate(percent):
        contribution_schedule = [percent * income for income in income_schedule]
        return project_balance(current_tsp, contribution_schedule, monthly_rates)

    lo = 0.0
    hi = 1.0

    for _ in range(60):
        mid = (lo + hi) / 2
        if simulate(mid) < target_nest_egg:
            lo = mid
        else:
            hi = mid

    percent = (lo + hi) / 2
    contribution_schedule = [percent * income for income in income_schedule]
    return percent, contribution_schedule

