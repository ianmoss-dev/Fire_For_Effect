from app.domain.military_pay import get_base_pay
from app.domain.promotion import PROMOTION_TIMELINE, get_progression_chain
import math


def calc_high3_pension(retire_rank, yrs_at_retire, multiplier, data=None):
    """
    Calculate monthly High-3 pension using the legacy app's 3-year lookback logic.
    """
    chain = get_progression_chain(retire_rank)
    chain_idx = chain.index(retire_rank) if retire_rank in chain else 0

    pays = []
    for year_offset in (3, 2, 1):
        tis_check = yrs_at_retire - year_offset
        current_rank = chain[0]
        for rank in chain[:chain_idx + 1]:
            if tis_check >= PROMOTION_TIMELINE.get(rank, 999):
                current_rank = rank
            else:
                break
        pays.append(get_base_pay(current_rank, tis_check, data))

    avg_base = sum(pays) / 3
    return avg_base * (yrs_at_retire * multiplier)


_QX_M_RAW = {
    0: 0.006064, 1: 0.000491, 2: 0.000309, 3: 0.000248, 4: 0.000199,
    5: 0.000167, 6: 0.000143, 7: 0.000126, 8: 0.000121, 9: 0.000121,
    10: 0.000127, 11: 0.000143, 12: 0.000171, 13: 0.000227, 14: 0.000320,
    15: 0.000451, 16: 0.000622, 17: 0.000826, 18: 0.001026, 19: 0.001182,
    20: 0.001301, 21: 0.001404, 22: 0.001498, 23: 0.001586, 24: 0.001679,
    25: 0.001776, 26: 0.001881, 27: 0.001985, 28: 0.002095, 29: 0.002219,
    30: 0.002332, 31: 0.002445, 32: 0.002562, 33: 0.002653, 34: 0.002716,
    35: 0.002791, 36: 0.002894, 37: 0.002994, 38: 0.003091, 39: 0.003217,
    40: 0.003353, 41: 0.003499, 42: 0.003642, 43: 0.003811, 44: 0.003996,
    45: 0.004175, 46: 0.004388, 47: 0.004666, 48: 0.004973, 49: 0.005305,
    50: 0.005666, 51: 0.006069, 52: 0.006539, 53: 0.007073, 54: 0.007675,
    55: 0.008348, 56: 0.009051, 57: 0.009822, 58: 0.010669, 59: 0.011548,
    60: 0.012458, 61: 0.013403, 62: 0.014450, 63: 0.015571, 64: 0.016737,
    65: 0.017897, 66: 0.019017, 67: 0.020213, 68: 0.021569, 69: 0.023088,
    70: 0.024828, 71: 0.026705, 72: 0.028761, 73: 0.031116, 74: 0.033861,
    75: 0.037088, 76: 0.041126, 77: 0.045241, 78: 0.049793,
}

_QX_F_RAW = {
    0: 0.005119, 1: 0.000398, 2: 0.000240, 3: 0.000198, 4: 0.000160,
    5: 0.000134, 6: 0.000118, 7: 0.000109, 8: 0.000106, 9: 0.000106,
    10: 0.000111, 11: 0.000121, 12: 0.000140, 13: 0.000162, 14: 0.000188,
    15: 0.000224, 16: 0.000276, 17: 0.000337, 18: 0.000395, 19: 0.000450,
    20: 0.000496, 21: 0.000532, 22: 0.000567, 23: 0.000610, 24: 0.000650,
    25: 0.000699, 26: 0.000743, 27: 0.000796, 28: 0.000855, 29: 0.000924,
    30: 0.000988, 31: 0.001053, 32: 0.001123, 33: 0.001198, 34: 0.001263,
    35: 0.001324, 36: 0.001403, 37: 0.001493, 38: 0.001596, 39: 0.001700,
    40: 0.001803, 41: 0.001905, 42: 0.002009, 43: 0.002116, 44: 0.002223,
    45: 0.002352, 46: 0.002516, 47: 0.002712, 48: 0.002936, 49: 0.003177,
    50: 0.003407, 51: 0.003642, 52: 0.003917, 53: 0.004238, 54: 0.004619,
    55: 0.005040, 56: 0.005493, 57: 0.005987, 58: 0.006509, 59: 0.007067,
    60: 0.007658, 61: 0.008305, 62: 0.008991, 63: 0.009681, 64: 0.010343,
    65: 0.011018, 66: 0.011743, 67: 0.012532, 68: 0.013512, 69: 0.014684,
    70: 0.016025, 71: 0.017468, 72: 0.019195, 73: 0.021195, 74: 0.023452,
    75: 0.025980, 76: 0.029153, 77: 0.032394, 78: 0.035888,
}


def _linear_slope(xs, ys):
    x_bar = sum(xs) / len(xs)
    y_bar = sum(ys) / len(ys)
    numerator = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))
    denominator = sum((x - x_bar) ** 2 for x in xs)
    return numerator / denominator


def _gompertz_extend(qx_raw, max_age=119):
    fit_ages = list(range(68, 79))
    slope = _linear_slope(fit_ages, [math.log(qx_raw[age]) for age in fit_ages])
    result = dict(qx_raw)
    q = qx_raw[78]

    for age in range(79, max_age + 1):
        q = min(q * math.exp(slope), 1.0)
        result[age] = q

    return result


def _build_lx(qx):
    lx = {0: 1.0}
    for age in range(1, 120):
        lx[age] = lx[age - 1] * (1 - qx.get(age - 1, 1.0))
    return lx


LX_MALE = _build_lx(_gompertz_extend(_QX_M_RAW))
LX_FEMALE = _build_lx(_gompertz_extend(_QX_F_RAW))


def calc_pension_apv(annual_pension, start_age, discount_rate=0.025, sex="male", max_age=100):
    """
    Actuarial present value of a pension stream using the legacy SSA table logic.
    """
    lx = LX_MALE if sex == "male" else LX_FEMALE
    lx_start = lx.get(start_age, 1e-9)
    apv = 0.0

    for t in range(max_age - start_age):
        age = start_age + t
        if age >= 120:
            break
        survival = lx[age] / lx_start
        apv += annual_pension * survival * (1 + discount_rate) ** (-t)

    return apv
