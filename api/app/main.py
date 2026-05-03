from dataclasses import asdict

from fastapi import FastAPI

from app.domain.income import calculate_income
from app.domain.monte_carlo import run_monte_carlo, summarize_monte_carlo
from app.domain.retirement_solver import build_monthly_real_rates, project_balance, solve_savings_rate
from app.models.income import IncomeCalculationRequest, IncomeCalculationResponse
from app.models.retirement import MonteCarloRequest, MonteCarloResponse, SavingsRateRequest, SavingsRateResponse


app = FastAPI(
    title="FIRE for Effect API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/income/calculate", response_model=IncomeCalculationResponse)
def calculate_income_endpoint(request: IncomeCalculationRequest):
    result = calculate_income(
        rank=request.rank,
        tis=request.tis,
        has_dependents=request.has_dependents,
        zip_code=request.zip_code,
        is_oconus=request.is_oconus,
        oha_location=request.oha_location,
        cola=request.cola,
        special_pay=request.special_pay,
    )
    return asdict(result)


@app.post("/retirement/solve-savings-rate", response_model=SavingsRateResponse)
def solve_savings_rate_endpoint(request: SavingsRateRequest):
    savings_rate, contribution_schedule = solve_savings_rate(
        target_nest_egg=request.target_nest_egg,
        current_tsp=request.current_tsp,
        base_pay_schedule=request.base_pay_schedule,
        civilian_monthly=request.civilian_monthly,
        mil_months=request.mil_months,
        total_months=request.total_months,
        allocation=request.allocation,
        inflation_rate=request.inflation_rate,
        prebuilt_income_schedule=request.prebuilt_income_schedule,
    )
    monthly_rates = build_monthly_real_rates(request.total_months, request.allocation, request.inflation_rate)
    final_projected_balance = project_balance(request.current_tsp, contribution_schedule, monthly_rates)
    average_contribution = sum(contribution_schedule) / len(contribution_schedule) if contribution_schedule else 0.0

    return {
        "savings_rate": savings_rate,
        "savings_rate_pct": savings_rate * 100,
        "first_month_contribution": contribution_schedule[0] if contribution_schedule else 0.0,
        "average_monthly_contribution": average_contribution,
        "final_projected_balance": final_projected_balance,
        "contribution_schedule": contribution_schedule,
    }


@app.post("/retirement/monte-carlo", response_model=MonteCarloResponse)
def monte_carlo_endpoint(request: MonteCarloRequest):
    results = run_monte_carlo(
        current_age=request.current_age,
        retire_age=request.retire_age,
        initial_balance=request.initial_balance,
        monthly_contribution=request.monthly_contribution,
        l_fund_weight=request.l_fund_weight,
        manual_allocation=request.manual_allocation,
        inflation_rate=request.inflation_rate,
        trials=request.trials,
        seed=request.seed,
    )
    return summarize_monte_carlo(results, request.target_balance)
