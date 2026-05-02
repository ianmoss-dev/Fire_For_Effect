from dataclasses import dataclass

from app.data.loaders import load_military_data
from app.domain.military_pay import get_bah, get_bas, get_base_pay
from app.domain.oha import get_oha_rate


@dataclass(frozen=True)
class IncomeCalculationResult:
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


def calculate_income(
    rank,
    tis,
    has_dependents,
    zip_code=None,
    is_oconus=False,
    oha_location=None,
    cola=0.0,
    special_pay=0.0,
    data=None,
):
    """Calculate monthly military compensation for one service member."""
    military_data = data or load_military_data()
    base_pay = get_base_pay(rank, tis, military_data)
    bas = get_bas(rank)
    cola = float(cola or 0.0)
    special_pay = float(special_pay or 0.0)

    bah = 0.0
    oha_rental = 0.0
    oha_utility = 0.0
    housing_total = 0.0
    housing_label = "BAH"
    mha = None
    location_name = None
    oha_location_key = None

    if is_oconus:
        oha = get_oha_rate(oha_location, rank, has_dependents)
        oha_rental = oha.rental
        oha_utility = oha.utility
        oha_location_key = oha.location_key
        housing_total = oha.total
        housing_label = "OHA + Utility"
    else:
        bah, mha, location_name = get_bah(rank, zip_code or "", has_dependents, military_data)
        housing_total = bah

    taxable_pay = base_pay + special_pay
    nontaxable_pay = bas + housing_total + cola
    gross_monthly = taxable_pay + nontaxable_pay

    return IncomeCalculationResult(
        rank=rank,
        tis=float(tis),
        is_oconus=bool(is_oconus),
        has_dependents=bool(has_dependents),
        base_pay=float(base_pay),
        bas=float(bas),
        bah=float(bah),
        oha_rental=float(oha_rental),
        oha_utility=float(oha_utility),
        cola=float(cola),
        special_pay=float(special_pay),
        taxable_pay=float(taxable_pay),
        nontaxable_pay=float(nontaxable_pay),
        gross_monthly=float(gross_monthly),
        housing_total=float(housing_total),
        housing_label=housing_label,
        mha=mha,
        location_name=location_name,
        oha_location_key=oha_location_key,
    )

