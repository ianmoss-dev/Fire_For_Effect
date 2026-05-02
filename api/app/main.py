from dataclasses import asdict

from fastapi import FastAPI

from app.domain.income import calculate_income
from app.models.income import IncomeCalculationRequest, IncomeCalculationResponse


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

