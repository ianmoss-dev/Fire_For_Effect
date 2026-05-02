from dataclasses import dataclass

from app.data.loaders import load_military_data


BAS_ENLISTED = 515.00
BAS_OFFICER = 360.00


@dataclass(frozen=True)
class MilitaryPayResult:
    base_pay: float
    bas: float
    bah: float
    mha: str | None = None
    location_name: str | None = None
    housing_label: str = "BAH"


def is_officer_or_warrant(rank):
    return rank.startswith("O") or rank.startswith("W")


def get_bas(rank):
    return BAS_OFFICER if is_officer_or_warrant(rank) else BAS_ENLISTED


def get_base_pay(rank, tis, data=None):
    """Return monthly base pay, snapping TIS down to the nearest table bracket."""
    military_data = data or load_military_data()
    rank_data = military_data.get("base_pay", {}).get(rank, {})

    if not rank_data:
        return 0.0

    available_brackets = sorted(int(bracket) for bracket in rank_data.keys())
    snapped = available_brackets[0]

    for bracket in available_brackets:
        if tis >= bracket:
            snapped = bracket
        else:
            break

    return float(rank_data.get(str(snapped), 0.0))


def get_bah(rank, zip_code, has_dependents, data=None):
    military_data = data or load_military_data()
    zip_info = military_data.get("zip_to_mha", {}).get(str(zip_code))

    if not zip_info:
        return 0.0, None, None

    mha_code = zip_info["mha"]
    location_name = zip_info.get("name")
    dependent_key = "with" if has_dependents else "without"
    bah = (
        military_data
        .get("bah_rates", {})
        .get(mha_code, {})
        .get(rank, {})
        .get(dependent_key, 0.0)
    )

    return float(bah), mha_code, location_name


def calculate_military_pay(rank, tis, zip_code, has_dependents, data=None):
    military_data = data or load_military_data()
    base_pay = get_base_pay(rank, tis, military_data)
    bas = get_bas(rank)
    bah, mha, location_name = get_bah(rank, zip_code, has_dependents, military_data)

    return MilitaryPayResult(
        base_pay=float(base_pay),
        bas=float(bas),
        bah=float(bah),
        mha=mha,
        location_name=location_name,
    )

