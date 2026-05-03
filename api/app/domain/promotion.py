from app.domain.military_pay import get_base_pay


PROMOTION_TIMELINE = {
    "E-1": 0, "E-2": 0.5, "E-3": 1.5, "E-4": 2.0,
    "E-5": 4.0, "E-6": 8.0, "E-7": 14.0, "E-8": 18.0, "E-9": 23.0,
    "W-1": 0, "W-2": 3.0, "W-3": 8.0, "W-4": 14.0, "W-5": 20.0,
    "O-1": 0, "O-1E": 0, "O-2": 2.0, "O-2E": 2.0,
    "O-3": 4.0, "O-3E": 4.0, "O-4": 11.0, "O-5": 17.0, "O-6": 23.0, "O-7": 31.0,
}

PROGRESSION = {
    "officer": ["O-1", "O-2", "O-3", "O-4", "O-5", "O-6", "O-7"],
    "officer_e": ["O-1E", "O-2E", "O-3E", "O-4", "O-5", "O-6", "O-7"],
    "warrant": ["W-1", "W-2", "W-3", "W-4", "W-5"],
    "enlisted": ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9"],
}


def get_progression_chain(rank):
    if rank in ("O-1E", "O-2E", "O-3E"):
        return PROGRESSION["officer_e"]
    if rank.startswith("O"):
        return PROGRESSION["officer"]
    if rank.startswith("W"):
        return PROGRESSION["warrant"]
    return PROGRESSION["enlisted"]


def get_projection_terminal_rank(start_rank):
    if start_rank in ("O-1E", "O-2E", "O-3E"):
        return "O-4"
    if start_rank.startswith("O"):
        return "O-5"
    if start_rank.startswith("W"):
        return "W-5"
    return "E-7"


def project_rank_by_tis(start_rank, tis_value, terminal_rank=None):
    chain = get_progression_chain(start_rank)
    terminal = terminal_rank or get_projection_terminal_rank(start_rank)
    terminal_idx = chain.index(terminal) if terminal in chain else len(chain) - 1

    current_rank = chain[0]
    for rank in chain[:terminal_idx + 1]:
        if tis_value >= PROMOTION_TIMELINE.get(rank, 999):
            current_rank = rank
        else:
            break
    return current_rank


def build_monthly_base_pay_schedule(start_rank, start_tis, career_months, data=None):
    """Build monthly base pay values using legacy promotion timeline assumptions."""
    chain = get_progression_chain(start_rank)
    chain_start = chain.index(start_rank) if start_rank in chain else 0

    schedule = []
    for month in range(career_months):
        tis = start_tis + month / 12.0
        current_rank = chain[chain_start]
        for rank in chain[chain_start:]:
            if tis >= PROMOTION_TIMELINE.get(rank, 999):
                current_rank = rank
            else:
                break
        schedule.append(get_base_pay(current_rank, tis, data))
    return schedule

