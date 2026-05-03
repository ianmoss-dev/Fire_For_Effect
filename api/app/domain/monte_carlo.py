from dataclasses import dataclass

import numpy as np

from app.domain.investment import FUND_MONTHLY_PARAMS, get_lifecycle_allocation


FUNDS = ("C", "S", "I", "F", "G")


@dataclass(frozen=True)
class MonteCarloSummary:
    months: int
    trials: int
    success_rate: float
    final_p10: float
    final_p50: float
    final_p90: float
    yearly_points: list[dict]


def normalize_contribution_schedule(months, monthly_contribution):
    if np.isscalar(monthly_contribution):
        return np.full(months, float(monthly_contribution))

    schedule = np.array(monthly_contribution, dtype=float)
    if len(schedule) < months:
        return np.pad(schedule, (0, months - len(schedule)), "edge")
    return schedule[:months]


def build_monthly_allocations(months, l_fund_weight, manual_allocation):
    monthly_allocations = []

    for month in range(months):
        allocation = manual_allocation.copy()
        if l_fund_weight > 0:
            years_left = (months - month) / 12
            lifecycle_allocation = get_lifecycle_allocation(years_left)
            for fund, weight in lifecycle_allocation.items():
                allocation[fund] = allocation.get(fund, 0) + (l_fund_weight * weight)
        monthly_allocations.append([allocation.get(fund, 0) for fund in FUNDS])

    return np.array(monthly_allocations)


def run_monte_carlo(
    current_age,
    retire_age,
    initial_balance,
    monthly_contribution,
    fund_params=None,
    l_fund_weight=0.0,
    manual_allocation=None,
    inflation_rate=0.025,
    trials=1000,
    seed=None,
):
    """Run the legacy-style parametric Monte Carlo simulation."""
    months = int((retire_age - current_age) * 12)
    if months <= 0:
        return np.zeros((trials, 1))

    fund_params = fund_params or FUND_MONTHLY_PARAMS
    manual_allocation = manual_allocation or {}
    contribution_schedule = normalize_contribution_schedule(months, monthly_contribution)
    monthly_inflation = (1 + inflation_rate) ** (1 / 12) - 1
    allocations = build_monthly_allocations(months, l_fund_weight, manual_allocation)
    mean_array = np.array([fund_params[fund][0] for fund in FUNDS])
    sigma_array = np.array([fund_params[fund][1] for fund in FUNDS])
    rng = np.random.default_rng(seed)

    results = np.zeros((trials, months + 1))
    results[:, 0] = initial_balance

    for trial in range(trials):
        raw_returns = rng.normal(mean_array, sigma_array, size=(months, len(FUNDS)))
        balance = initial_balance
        for month in range(months):
            nominal_return = np.dot(raw_returns[month], allocations[month])
            real_return = (1 + nominal_return) / (1 + monthly_inflation) - 1
            balance = balance * (1 + real_return) + contribution_schedule[month]
            results[trial, month + 1] = balance

    return results


def summarize_monte_carlo(results, target_balance):
    final_values = results[:, -1]
    success_rate = float(np.mean(final_values >= target_balance))
    months = results.shape[1] - 1
    trials = results.shape[0]
    yearly_points = []

    for month in range(12, months + 1, 12):
        values = results[:, month]
        yearly_points.append({
            "month": month,
            "year": month // 12,
            "p10": float(np.percentile(values, 10)),
            "p50": float(np.percentile(values, 50)),
            "p90": float(np.percentile(values, 90)),
        })

    return MonteCarloSummary(
        months=months,
        trials=trials,
        success_rate=success_rate,
        final_p10=float(np.percentile(final_values, 10)),
        final_p50=float(np.percentile(final_values, 50)),
        final_p90=float(np.percentile(final_values, 90)),
        yearly_points=yearly_points,
    )

