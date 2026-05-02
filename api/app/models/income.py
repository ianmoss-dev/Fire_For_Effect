from pydantic import BaseModel, Field


class IncomeCalculationRequest(BaseModel):
    rank: str = Field(..., examples=["E-5"])
    tis: float = Field(..., ge=0, examples=[6])
    has_dependents: bool = Field(False)
    zip_code: str | None = Field(None, examples=["28310"])
    is_oconus: bool = Field(False)
    oha_location: str | None = Field(None, examples=["Germany - Grafenwohr / Vilseck"])
    cola: float = Field(0.0, ge=0)
    special_pay: float = Field(0.0, ge=0)


class IncomeCalculationResponse(BaseModel):
    rank: str
    tis: float
    is_oconus: bool
    has_dependents: bool
    base_pay: float
    bas: float
    bah: float
    oha_rental: float
    oha_utility: float
    cola: float
    special_pay: float
    taxable_pay: float
    nontaxable_pay: float
    gross_monthly: float
    housing_total: float
    housing_label: str
    mha: str | None = None
    location_name: str | None = None
    oha_location_key: str | None = None

