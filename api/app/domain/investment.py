import math


FUND_STATS = {
    "C": {"mu": 0.11847, "sigma": 0.181, "geo_mean": 0.107},
    "S": {"mu": 0.11518, "sigma": 0.202, "geo_mean": 0.099},
    "I": {"mu": 0.08059, "sigma": 0.171, "geo_mean": 0.068},
    "F": {"mu": 0.05268, "sigma": 0.043, "geo_mean": 0.053},
    "G": {"mu": 0.04602, "sigma": 0.003, "geo_mean": 0.047},
}

FUND_NOMINAL_RATES = {fund: values["geo_mean"] for fund, values in FUND_STATS.items()}


def get_fund_monthly_params():
    """Return monthly arithmetic mean and sigma for each TSP proxy fund."""
    params = {}
    for fund, values in FUND_STATS.items():
        monthly_geo = (1 + values["geo_mean"]) ** (1 / 12) - 1
        monthly_sigma = values["sigma"] / math.sqrt(12)
        params[fund] = (monthly_geo + monthly_sigma**2 / 2, monthly_sigma)
    return params


FUND_MONTHLY_PARAMS = get_fund_monthly_params()


def get_lifecycle_allocation(years_to_retire):
    if years_to_retire > 20:
        return {"C": 0.50, "S": 0.25, "I": 0.25, "F": 0.0, "G": 0.0}
    if years_to_retire > 10:
        return {"C": 0.40, "S": 0.15, "I": 0.15, "F": 0.2, "G": 0.1}
    if years_to_retire > 0:
        return {"C": 0.20, "S": 0.05, "I": 0.05, "F": 0.3, "G": 0.4}
    return {"C": 0.0, "S": 0.0, "I": 0.0, "F": 0.3, "G": 0.7}


def get_blended_nominal_return(allocation, years_to_retire):
    """Calculate weighted nominal return, expanding lifecycle fund allocations."""
    l_weight = allocation.get("L", 0.0)
    lifecycle_allocation = get_lifecycle_allocation(years_to_retire) if l_weight > 0 else {}

    total = 0.0
    for fund, weight in allocation.items():
        if fund == "L":
            for sub_fund, sub_weight in lifecycle_allocation.items():
                total += weight * sub_weight * FUND_NOMINAL_RATES.get(sub_fund, 0.0)
        else:
            total += weight * FUND_NOMINAL_RATES.get(fund, 0.0)
    return total

