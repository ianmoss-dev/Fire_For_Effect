from app.domain.military_pay import get_base_pay
from app.domain.promotion import PROMOTION_TIMELINE, get_progression_chain


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

