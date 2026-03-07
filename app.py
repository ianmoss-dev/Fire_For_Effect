import streamlit as st
import json
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import requests
import io
import hashlib
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="F.I.R.E. for Effect",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CONFIG = {
    "ranks": ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9", 
              "W-1", "W-2", "W-3", "W-4", "W-5", 
              "O-1", "O-1E", "O-2", "O-2E", "O-3", "O-3E", "O-4", "O-5", "O-6", "O-7"],
    "bas_enlisted": 515.00,
    "bas_officer": 360.00,
}

SHEET_ID = "1dFytsNBUepFXsIR4LOXIpsUZfqHfwhO32URiS37m--M"

# --- ANALYTICS ---
@st.cache_resource
def get_gsheet():
    try:
        creds_dict = json.loads(st.secrets["gcp_service_account"]) \
            if isinstance(st.secrets["gcp_service_account"], str) \
            else dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1

        # Write header if sheet is empty
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "timestamp":
            sheet.append_row([
                "timestamp", "anon_id", "zip", "device_type",
                "session_duration_seconds", "tabs_visited", "max_tab_reached",
                "monte_carlo_run", "quiz_score", "pdf_downloaded",
                "bounced", "error_event"
            ])
        return sheet
    except Exception:
        return None

def get_anon_id():
    try:
        ua  = st.context.headers.get("User-Agent", "")
        raw = ua + st.context.headers.get("Accept-Language", "")
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception:
        return "unknown"

def get_device_type():
    try:
        ua = st.context.headers.get("User-Agent", "").lower()
        if any(x in ua for x in ["iphone", "android", "mobile", "ipad"]):
            return "mobile"
        return "desktop"
    except Exception:
        return "unknown"

def log_session():
    try:
        sheet = get_gsheet()
        if sheet is None:
            return
        elapsed = (datetime.datetime.now() - st.session_state.session_start).seconds
        bounced = 1 if (elapsed < 60 and st.session_state.max_tab_reached <= 1) else 0
        sheet.append_row([
            datetime.datetime.now().isoformat(),
            st.session_state.anon_id,
            st.session_state.tracked_zip,
            st.session_state.device_type,
            elapsed,
            len(st.session_state.tabs_visited),
            st.session_state.max_tab_reached,
            1 if st.session_state.monte_carlo_run else 0,
            st.session_state.quiz_score,
            1 if st.session_state.pdf_downloaded else 0,
            bounced,
            st.session_state.last_error or ""
        ])
    except Exception:
        pass

def log_error(error_msg):
    st.session_state.last_error = str(error_msg)[:200]

# --- Persistent State ---
if "base_pay" not in st.session_state: st.session_state.base_pay = 0.0
if "bah_amt" not in st.session_state: st.session_state.bah_amt = 0.0
if "bas_amt" not in st.session_state: st.session_state.bas_amt = 0.0
if "pmt_target" not in st.session_state: st.session_state.pmt_target = 0.0
if "savings_rate_pct" not in st.session_state: st.session_state.savings_rate_pct = 0.0
if "nest_egg_target" not in st.session_state: st.session_state.nest_egg_target = 0.0
if "est_pension" not in st.session_state: st.session_state.est_pension = 0.0
if "mc_success_rate" not in st.session_state: st.session_state.mc_success_rate = None
if "sim_results" not in st.session_state: st.session_state.sim_results = None
if "sim_savings_pct" not in st.session_state: st.session_state.sim_savings_pct = 0.0
if "sim_current_age" not in st.session_state: st.session_state.sim_current_age = 0
if "sim_age_at_retire" not in st.session_state: st.session_state.sim_age_at_retire = 0
if "sim_target" not in st.session_state: st.session_state.sim_target = 0.0
if "sim_data_source" not in st.session_state: st.session_state.sim_data_source = None
if "tab3_take_home" not in st.session_state: st.session_state.tab3_take_home = 0.0
if "tab3_fixed" not in st.session_state: st.session_state.tab3_fixed = 0.0
if "tab3_invested" not in st.session_state: st.session_state.tab3_invested = 0.0
if "tab3_guilt_free" not in st.session_state: st.session_state.tab3_guilt_free = 0.0
if "bah_manual" not in st.session_state: st.session_state.bah_manual = False
if "les_tsp_actual" not in st.session_state: st.session_state.les_tsp_actual = 0.0

# --- Analytics State ---
if "consent_given" not in st.session_state: st.session_state.consent_given = False
if "session_start" not in st.session_state: st.session_state.session_start = datetime.datetime.now()
if "anon_id" not in st.session_state: st.session_state.anon_id = get_anon_id()
if "device_type" not in st.session_state: st.session_state.device_type = get_device_type()
if "tabs_visited" not in st.session_state: st.session_state.tabs_visited = set()
if "max_tab_reached" not in st.session_state: st.session_state.max_tab_reached = 0
if "tracked_zip" not in st.session_state: st.session_state.tracked_zip = ""
if "monte_carlo_run" not in st.session_state: st.session_state.monte_carlo_run = False
if "quiz_score" not in st.session_state: st.session_state.quiz_score = None
if "pdf_downloaded" not in st.session_state: st.session_state.pdf_downloaded = False
if "last_error" not in st.session_state: st.session_state.last_error = ""
if "session_logged" not in st.session_state: st.session_state.session_logged = False

# --- CONSENT SCREEN ---
if not st.session_state.consent_given:
    st.title("🎖️ F.I.R.E. for Effect")
    st.markdown("""
**Before you go any further — a quick note from the developer.**

This is the first app I've ever built. I think there's something genuinely useful here, but there's probably more wrong with it than right — and the only way I find that out is by seeing how people actually use it.

So I'm asking your permission to collect some anonymous usage data while you're in the app.

**What I collect:**
- When you opened the app and how long you stayed
- What tabs you visited and how far you got
- Your duty station zip code (if you enter one)
- Whether you're on a phone or computer
- Whether you ran the Luck & Timing Roulette simulation, completed the financial quiz, or downloaded the PDF
- Whether anything broke while you were using it

**What I do NOT collect:**
- Your name, email, rank, TIS, or SSN
- Anything that could identify you personally
- Any financial numbers you enter — those never leave your device

**What this lets me do:**
- See if people are using it or closing it immediately
- Find where it breaks
- Understand whether it's spreading or just being perpetually opened by my mom to be nice
- Decide whether this is worth anything or just adding more trash to the pile

**One more thing:** this is a test, so the link may be dead in a few weeks. If there's something worth saving, I'll build it back better.
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Alright, Let's Do This.", type="primary", use_container_width=True):
            st.session_state.consent_given = True
            st.rerun()
    with col2:
        if st.button("❌ No thanks, close the tab.", use_container_width=True):
            st.markdown("### No problem. Come back if you change your mind.")
            st.stop()
    st.stop()

# ==========================================
# --- MONTE CARLO HELPER FUNCTIONS ---
# ==========================================

# ── Single source of truth for all fund return assumptions ───────────────────
# Source: tspfolio.com, since-inception data through 3/5/2026
# geo_mean = target nominal CAGR (what the solver uses)
# sigma     = annualized standard deviation
# mu        = arithmetic mean for proxy sampling = geo_mean + sigma²/2
#             Corrects for variance drag so proxy geometric return matches solver
FUND_STATS = {
    'C': {'mu': 0.11847, 'sigma': 0.181, 'geo_mean': 0.107},
    'S': {'mu': 0.11518, 'sigma': 0.202, 'geo_mean': 0.099},
    'I': {'mu': 0.08059, 'sigma': 0.171, 'geo_mean': 0.068},
    'F': {'mu': 0.05268, 'sigma': 0.043, 'geo_mean': 0.053},
    'G': {'mu': 0.04602, 'sigma': 0.003, 'geo_mean': 0.047},
}

def get_fund_monthly_params():
    """Returns {fund: (monthly_arith_mean, monthly_sigma)} for all funds.
    Arithmetic mean = monthly_geo + sigma^2/2 so geometric compounding matches target CAGR.
    """
    params = {}
    for fund, v in FUND_STATS.items():
        mg = (1 + v['geo_mean']) ** (1/12) - 1
        ms = v['sigma'] / np.sqrt(12)
        params[fund] = (mg + ms**2 / 2, ms)
    return params

FUND_MONTHLY_PARAMS = get_fund_monthly_params()

def scrape_and_prep_tsp_data():
    """Returns fund monthly params. MC generates fresh returns each trial — no pool drift."""
    return FUND_MONTHLY_PARAMS, "Proxy"

def get_lifecycle_allocation(years_to_retire):
    if years_to_retire > 20: return {'C': 0.50, 'S': 0.25, 'I': 0.25, 'F': 0.0, 'G': 0.0}
    elif years_to_retire > 10: return {'C': 0.40, 'S': 0.15, 'I': 0.15, 'F': 0.2, 'G': 0.1}
    elif years_to_retire > 0: return {'C': 0.20, 'S': 0.05, 'I': 0.05, 'F': 0.3, 'G': 0.4}
    else: return {'C': 0.0, 'S': 0.0, 'I': 0.0, 'F': 0.3, 'G': 0.7}

def run_real_monte_carlo(current_age, retire_age, initial_bal, monthly_contrib,
                         fund_params, l_fund_weight, manual_alloc, inflation_rate=0.025, trials=1000):
    """
    Parametric Monte Carlo — draws fresh returns from Normal(mu, sigma) each trial.
    Eliminates pool-sampling bias. Median converges to solver projection by construction.
    fund_params: {fund: (monthly_arith_mean, monthly_sigma)} from FUND_MONTHLY_PARAMS
    """
    months = int((retire_age - current_age) * 12)
    monthly_infl = (1 + inflation_rate)**(1/12) - 1
    funds = ['C', 'S', 'I', 'F', 'G']

    # Normalize contribution schedule
    if np.isscalar(monthly_contrib):
        contrib_schedule = np.full(months, float(monthly_contrib))
    else:
        contrib_schedule = np.array(monthly_contrib, dtype=float)
        if len(contrib_schedule) < months:
            contrib_schedule = np.pad(contrib_schedule, (0, months - len(contrib_schedule)), 'edge')
        else:
            contrib_schedule = contrib_schedule[:months]

    # Pre-calculate monthly allocation weights (gliding L-fund)
    monthly_allocs = []
    for i in range(months):
        alloc = manual_alloc.copy()
        if l_fund_weight > 0:
            years_left = (months - i) / 12
            lc_alloc = get_lifecycle_allocation(years_left)
            for f, w in lc_alloc.items():
                alloc[f] = alloc.get(f, 0) + (l_fund_weight * w)
        monthly_allocs.append([alloc.get(f, 0) for f in funds])
    allocs_arr = np.array(monthly_allocs)   # shape (months, 5)

    # Extract per-fund distribution params as arrays aligned to funds list
    mu_arr    = np.array([fund_params[f][0] for f in funds])   # monthly arith means
    sigma_arr = np.array([fund_params[f][1] for f in funds])   # monthly sigmas

    # Pre-allocate results
    results = np.zeros((trials, months + 1))
    results[:, 0] = initial_bal

    for t in range(trials):
        # Draw fresh independent returns for every fund every month: shape (months, 5)
        raw_returns = np.random.normal(mu_arr, sigma_arr, size=(months, 5))

        balance = initial_bal
        for i in range(months):
            nom_ret  = np.dot(raw_returns[i], allocs_arr[i])
            real_ret = (1 + nom_ret) / (1 + monthly_infl) - 1
            balance  = balance * (1 + real_ret) + contrib_schedule[i]
            results[t, i + 1] = balance

    return results

# --- 2. DATA UTILITIES ---
@st.cache_data
def load_military_data():
    try:
        with open('military_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Data file missing. Please ensure 'military_data.json' is in the folder.")
        return {"base_pay": {}, "zip_to_mha": {}, "bah_rates": {}}

DATA = load_military_data()

def get_base_pay(rank, tis):
    rank_data = DATA.get("base_pay", {}).get(rank, {})
    if not rank_data:
        return 0.0
    available = sorted([int(k) for k in rank_data.keys()])
    snapped = available[0]
    for b in available:
        if tis >= b:
            snapped = b
        else:
            break
    return float(rank_data.get(str(snapped), 0.0))

def get_military_pay(rank, tis, zip_code, has_dep):
    base = get_base_pay(rank, tis)
    bas = CONFIG["bas_officer"] if ("O" in rank or "W" in rank) else CONFIG["bas_enlisted"]
    zip_info = DATA.get("zip_to_mha", {}).get(zip_code)
    bah = 0.0
    if zip_info:
        mha_code = zip_info["mha"]
        dep_key = "with" if has_dep else "without"
        bah = DATA.get("bah_rates", {}).get(mha_code, {}).get(rank, {}).get(dep_key, 0.0)
    return float(base), float(bas), float(bah)

# --- PROMOTION TIMELINE & SAVINGS RATE HELPERS ---

FUND_NOMINAL_RATES = {f: v['geo_mean'] for f, v in FUND_STATS.items()}

# Promotion timelines reflect when pay actually changes (~1 year after selection board).
# Selection happens at typical primary zone TIS; pay follows ~12 months later.
PROMOTION_TIMELINE = {
    # Enlisted
    'E-1': 0, 'E-2': 0.5, 'E-3': 1.5, 'E-4': 2.0,
    'E-5': 4.0, 'E-6': 8.0, 'E-7': 14.0, 'E-8': 18.0, 'E-9': 23.0,
    # Warrant Officers
    'W-1': 0, 'W-2': 3.0, 'W-3': 8.0, 'W-4': 14.0, 'W-5': 20.0,
    # Officers (O-1/O-2 are time-based, minimal lag; O-4+ board-to-pin ~1yr)
    'O-1': 0, 'O-1E': 0, 'O-2': 2.0, 'O-2E': 2.0,
    'O-3': 4.0, 'O-3E': 4.0, 'O-4': 11.0, 'O-5': 17.0, 'O-6': 23.0, 'O-7': 31.0,
}

# Ordered progression chains
PROGRESSION = {
    'officer':  ['O-1','O-2','O-3','O-4','O-5','O-6','O-7'],
    'officer_e':['O-1E','O-2E','O-3E','O-4','O-5','O-6','O-7'],
    'warrant':  ['W-1','W-2','W-3','W-4','W-5'],
    'enlisted': ['E-1','E-2','E-3','E-4','E-5','E-6','E-7','E-8','E-9'],
}

def get_progression_chain(rank):
    if rank in ('O-1E','O-2E','O-3E'): return PROGRESSION['officer_e']
    if rank.startswith('O'): return PROGRESSION['officer']
    if rank.startswith('W'): return PROGRESSION['warrant']
    return PROGRESSION['enlisted']

def build_monthly_base_pay_schedule(start_rank, start_tis, career_months):
    """
    Returns a list of monthly base pay values of length career_months,
    projecting forward using typical promotion timelines from start_rank/start_tis.
    """
    chain = get_progression_chain(start_rank)
    if start_rank not in chain:
        chain_start = 0
    else:
        chain_start = chain.index(start_rank)

    schedule = []
    for m in range(career_months):
        tis = start_tis + m / 12.0
        # Find highest rank in chain that has been reached by this TIS
        current_rank = chain[chain_start]
        for rank in chain[chain_start:]:
            if tis >= PROMOTION_TIMELINE.get(rank, 999):
                current_rank = rank
            else:
                break
        schedule.append(get_base_pay(current_rank, tis))
    return schedule

def get_blended_nominal_return(alloc_dict, years_to_retire):
    """
    Computes weighted nominal return for a custom allocation dict.
    L-fund portion uses get_lifecycle_allocation() to derive its sub-weights.
    alloc_dict keys: C, S, I, F, G, L  (values sum to 1.0)
    """
    l_weight = alloc_dict.get('L', 0.0)
    lc_alloc = get_lifecycle_allocation(years_to_retire) if l_weight > 0 else {}

    total = 0.0
    for fund, weight in alloc_dict.items():
        if fund == 'L':
            # Expand L-fund into its underlying sub-allocation
            for sub_fund, sub_weight in lc_alloc.items():
                total += weight * sub_weight * FUND_NOMINAL_RATES.get(sub_fund, 0.0)
        else:
            total += weight * FUND_NOMINAL_RATES.get(fund, 0.0)
    return total

def solve_savings_rate(target_nest_egg, current_tsp, base_pay_schedule,
                       civilian_monthly, mil_months, total_months,
                       alloc_dict, inflation_rate):
    """
    Binary-searches for the constant % of income that grows to target_nest_egg.
    Uses a month-by-month gliding L-fund allocation — identical logic to the MC —
    so the solver rate and MC median are always calibrated to the same return path.
    Returns (savings_pct_float, contribution_schedule_list).
    """
    monthly_infl = (1 + inflation_rate) ** (1/12) - 1
    l_weight     = alloc_dict.get('L', 0.0)
    manual_alloc = {k: v for k, v in alloc_dict.items() if k != 'L'}
    funds        = ['C', 'S', 'I', 'F', 'G']

    # Pre-compute month-by-month nominal rates (mirrors MC allocation logic exactly)
    monthly_rates = []
    for m in range(total_months):
        years_left = (total_months - m) / 12
        alloc = manual_alloc.copy()
        if l_weight > 0:
            lc_alloc = get_lifecycle_allocation(years_left)
            for f, w in lc_alloc.items():
                alloc[f] = alloc.get(f, 0) + (l_weight * w)
        nom = sum(alloc.get(f, 0) * FUND_NOMINAL_RATES.get(f, 0) for f in funds)
        real = (1 + nom) ** (1/12) / (1 + monthly_infl) - 1
        monthly_rates.append(real)

    # Build full income schedule (military phase + civilian phase)
    income_schedule = list(base_pay_schedule)
    for m in range(total_months - mil_months):
        income_schedule.append(civilian_monthly)

    def simulate(pct):
        balance = current_tsp
        for m in range(total_months):
            balance = balance * (1 + monthly_rates[m]) + pct * income_schedule[m]
        return balance

    # Binary search between 0% and 100%
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if simulate(mid) < target_nest_egg:
            lo = mid
        else:
            hi = mid

    pct = (lo + hi) / 2
    contrib_schedule = [pct * inc for inc in income_schedule]
    return pct, contrib_schedule


# ── SSA 2022 Period Life Table (ssa.gov/oact/STATS/table4c6.html) ─────────────
# Death probabilities (qx) by age. Ages 0-78: exact SSA values.
# Ages 79-119: Gompertz extrapolation from ages 68-78 trend.
_QX_M_RAW = {
    0:0.006064,1:0.000491,2:0.000309,3:0.000248,4:0.000199,
    5:0.000167,6:0.000143,7:0.000126,8:0.000121,9:0.000121,
    10:0.000127,11:0.000143,12:0.000171,13:0.000227,14:0.000320,
    15:0.000451,16:0.000622,17:0.000826,18:0.001026,19:0.001182,
    20:0.001301,21:0.001404,22:0.001498,23:0.001586,24:0.001679,
    25:0.001776,26:0.001881,27:0.001985,28:0.002095,29:0.002219,
    30:0.002332,31:0.002445,32:0.002562,33:0.002653,34:0.002716,
    35:0.002791,36:0.002894,37:0.002994,38:0.003091,39:0.003217,
    40:0.003353,41:0.003499,42:0.003642,43:0.003811,44:0.003996,
    45:0.004175,46:0.004388,47:0.004666,48:0.004973,49:0.005305,
    50:0.005666,51:0.006069,52:0.006539,53:0.007073,54:0.007675,
    55:0.008348,56:0.009051,57:0.009822,58:0.010669,59:0.011548,
    60:0.012458,61:0.013403,62:0.014450,63:0.015571,64:0.016737,
    65:0.017897,66:0.019017,67:0.020213,68:0.021569,69:0.023088,
    70:0.024828,71:0.026705,72:0.028761,73:0.031116,74:0.033861,
    75:0.037088,76:0.041126,77:0.045241,78:0.049793,
}
_QX_F_RAW = {
    0:0.005119,1:0.000398,2:0.000240,3:0.000198,4:0.000160,
    5:0.000134,6:0.000118,7:0.000109,8:0.000106,9:0.000106,
    10:0.000111,11:0.000121,12:0.000140,13:0.000162,14:0.000188,
    15:0.000224,16:0.000276,17:0.000337,18:0.000395,19:0.000450,
    20:0.000496,21:0.000532,22:0.000567,23:0.000610,24:0.000650,
    25:0.000699,26:0.000743,27:0.000796,28:0.000855,29:0.000924,
    30:0.000988,31:0.001053,32:0.001123,33:0.001198,34:0.001263,
    35:0.001324,36:0.001403,37:0.001493,38:0.001596,39:0.001700,
    40:0.001803,41:0.001905,42:0.002009,43:0.002116,44:0.002223,
    45:0.002352,46:0.002516,47:0.002712,48:0.002936,49:0.003177,
    50:0.003407,51:0.003642,52:0.003917,53:0.004238,54:0.004619,
    55:0.005040,56:0.005493,57:0.005987,58:0.006509,59:0.007067,
    60:0.007658,61:0.008305,62:0.008991,63:0.009681,64:0.010343,
    65:0.011018,66:0.011743,67:0.012532,68:0.013512,69:0.014684,
    70:0.016025,71:0.017468,72:0.019195,73:0.021195,74:0.023452,
    75:0.025980,76:0.029153,77:0.032394,78:0.035888,
}

def _gompertz_extend(qx_raw, max_age=119):
    """Extend qx table to max_age via Gompertz fit on ages 68-78."""
    fit_ages = list(range(68, 79))
    B = np.polyfit(fit_ages, np.log([qx_raw[a] for a in fit_ages]), 1)[0]
    result = dict(qx_raw)
    q = qx_raw[78]
    for age in range(79, max_age + 1):
        q = min(q * np.exp(B), 1.0)
        result[age] = q
    return result

def _build_lx(qx):
    lx = {0: 1.0}
    for age in range(1, 120):
        lx[age] = lx[age - 1] * (1 - qx.get(age - 1, 1.0))
    return lx

_QX_MALE   = _gompertz_extend(_QX_M_RAW)
_QX_FEMALE = _gompertz_extend(_QX_F_RAW)
LX_MALE    = _build_lx(_QX_MALE)
LX_FEMALE  = _build_lx(_QX_FEMALE)

def calc_pension_apv(annual_pension, start_age, discount_rate=0.025, sex='male', max_age=100):
    """
    Actuarial Present Value of a pension stream.
    = sum over t of: annual_pension * P(alive at start_age+t | alive at start_age) * (1+r)^-t
    Source: SSA 2022 Period Life Table (2025 Trustees Report)
    """
    lx = LX_MALE if sex == 'male' else LX_FEMALE
    lx_start = lx.get(start_age, 1e-9)
    apv = 0.0
    for t in range(max_age - start_age):
        age = start_age + t
        if age >= 120: break
        survival = lx[age] / lx_start
        apv += annual_pension * survival * (1 + discount_rate) ** (-t)
    return apv

def calc_high3_pension(retire_rank, yrs_at_retire, multiplier):
    """
    Averages base pay over the 3 years immediately preceding retirement,
    accounting for promotion timeline so rank reflects actual pay received.
    """
    chain = get_progression_chain(retire_rank)
    if retire_rank not in chain:
        chain_idx = 0
    else:
        chain_idx = chain.index(retire_rank)

    pays = []
    for yr_offset in [3, 2, 1]:
        tis_check = yrs_at_retire - yr_offset
        # Walk back to find what rank was held at that TIS
        current_rank = chain[0]
        for r in chain[:chain_idx + 1]:
            if tis_check >= PROMOTION_TIMELINE.get(r, 999):
                current_rank = r
            else:
                break
        pays.append(get_base_pay(current_rank, tis_check))

    avg_base = sum(pays) / 3
    return avg_base * (yrs_at_retire * multiplier)

# --- 3. UI LAYOUT ---
st.title("🎖️ F.I.R.E. for Effect: Financial Planning for Soldiers")
st.caption("Finance is boring. Do it once, get it right, and move on.")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 What Do You Make?", "📈 How Much Do You Need to Save?", "💸 Where Does It Go?",
    "🎯 Know the Game", "✅ The Way Ahead", "📬 Feedback", "📄 Your Plan"
])

# --- TAB 1: INCOME TRUTH ---
with tab1:
    st.session_state.tabs_visited.add(1)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 1)
    st.header("Step 1: What You Make")

    col1, col2 = st.columns(2)
    with col1:
        rank = st.selectbox("Current Rank", CONFIG["ranks"], index=14, key="tab1_rank_widget")
        tis = st.number_input("Years of Service (TIS)", 0, 40, 4)
    with col2:
        zip_code = st.text_input("Duty Station Zip Code", "93943")
        dep = st.checkbox("With Dependents?", value=True)
        st.session_state.tracked_zip = zip_code

    with st.expander("🎖️ Optional Special / Incentive Pays (Monthly)"):
        sp1, sp2 = st.columns(2)
        with sp1:
            hdip_static = st.checkbox("HDIP: Parachute (Static Line) (+$150)")
            hdip_mff = st.checkbox("HDIP: Military Free Fall / HALO (+$225)")
            hdip_demo = st.checkbox("HDIP: Demolition (+$150)")
        with sp2:
            hfp_idp = st.checkbox("Hostile Fire / Imminent Danger Pay (up to +$225)") 
            flpb_on = st.checkbox("Foreign Language Proficiency Bonus (FLPB)")
            avip_on = st.checkbox("Aviation Incentive Pay (Army Officer AvIP)")

        flpb_amt = 0
        if flpb_on:
            flpb_amt = st.number_input("FLPB monthly amount (enter your known amount from orders/LES)", min_value=0, max_value=1000, value=0, step=50)

        avip_amt = 0
        if avip_on:
            yas = st.number_input("Years of Aviation Service (YAS)", min_value=0.0, max_value=40.0, value=2.0, step=0.5)
            if yas <= 2: avip_amt = 125
            elif yas <= 6: avip_amt = 200
            elif yas <= 10: avip_amt = 700
            elif yas <= 22: avip_amt = 1000
            elif yas <= 24: avip_amt = 700
            else: avip_amt = 400

        dive_on = st.checkbox("Diving Duty Pay")
        dive_amt = 0
        if dive_on:
            dive_category = st.selectbox("Dive category (Army)", [
                "Under instruction at approved dive school ($110)", "Combat Diver ($215)",
                "Diver Second Class ($150)", "Salvage Diver ($175)", "Diver First Class ($215)",
                "Master Diver ($340)", "Officer: Marine Diving Officer ($240)", "Officer: Diving Medical Officer ($215)",
            ])
            dive_map = {
                "Under instruction at approved dive school ($110)": 110, "Combat Diver ($215)": 215,
                "Diver Second Class ($150)": 150, "Salvage Diver ($175)": 175, "Diver First Class ($215)": 215,
                "Master Diver ($340)": 340, "Officer: Marine Diving Officer ($240)": 240, "Officer: Diving Medical Officer ($215)": 215,
            }
            dive_amt = dive_map.get(dive_category, 0)

        sdap_on = st.checkbox("Special Duty Assignment Pay (SDAP) (Recruiter/Drill/etc.)")
        sdap_amt = 0
        if sdap_on:
            sdap_amt = st.number_input("SDAP monthly amount", min_value=0, max_value=1000, value=0, step=25)

    special_pay = 0
    if hdip_static: special_pay += 150
    if hdip_mff: special_pay += 225
    if hdip_demo: special_pay += 150
    if hfp_idp: special_pay += 225
    special_pay += flpb_amt 
    special_pay += avip_amt 
    special_pay += dive_amt 
    special_pay += sdap_amt 

    st.divider()

    # Calculate dynamically — no button required
    zip_found = DATA.get("zip_to_mha", {}).get(zip_code) is not None

    if zip_found:
        base, bas, bah = get_military_pay(rank, tis, zip_code, dep)
        st.session_state.bah_manual = False
    else:
        base, bas, _ = get_military_pay(rank, tis, "92136", dep)  # get base/bas with fallback zip
        st.warning(
            f"⚠️ Zip code **{zip_code}** was not found in the BAH database. "
            "Make sure you're entering your **duty station** zip code, not your home address. "
            "If your zip is correct and still not found, enter your BAH manually below."
        )
        bah = st.number_input("Manual BAH Entry ($/month)", min_value=0.0, step=50.0,
                              key="manual_bah_input")
        st.session_state.bah_manual = True

    st.session_state.base_pay    = base
    st.session_state.bas_amt     = bas
    st.session_state.bah_amt     = bah
    st.session_state.special_pay = special_pay
    st.session_state.tab1_rank   = rank
    st.session_state.tab1_tis    = tis

    gross = base + bas + bah + special_pay
    annual_gross = gross * 12

    col_monthly, col_annual = st.columns(2)
    with col_monthly: st.info(f"### 🗓️ Monthly Gross\n# ${gross:,.2f}")
    with col_annual: st.success(f"### 💰 Annual Gross\n# ${annual_gross:,.2f}")

    st.write("")

    c_a, c_b, c_c, c_d = st.columns(4)
    c_a.metric("Base Pay",        f"${base:,.2f}")
    c_b.metric("BAH (Tax-Free)",  f"${bah:,.2f}")
    c_c.metric("BAS (Tax-Free)",  f"${bas:,.2f}")
    c_d.metric("Special Pays",    f"${special_pay:,.2f}")

# --- TAB 2: RETIREMENT ---
with tab2:
    st.session_state.tabs_visited.add(2)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 2)
    st.header("Step 2: Retirement & Pension Target")
    st.info("💡 **Reality Check:** We'll calculate the single savings rate — as a % of your base pay — that you can plug directly into MyPay and stay on track for your entire career.")

    # ── Row 1: Career inputs ──────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Career Timeline")
        retire_system = st.radio("Retirement System", ["BRS (2.0%)", "Legacy / High-3 (2.5%)"], horizontal=True)
        multiplier = 0.02 if "BRS" in retire_system else 0.025

        o1_idx = CONFIG["ranks"].index("O-1") if "O-1" in CONFIG["ranks"] else 0
        start_rank = st.selectbox("Current Rank", CONFIG["ranks"], index=o1_idx)
        start_tis  = st.number_input("Current Years of Service", min_value=0.0, max_value=40.0,
                                     value=0.0, step=0.5)
        retire_rank = st.selectbox("Expected Rank at Retirement", CONFIG["ranks"], index=20)
        yrs_at_retire = st.slider("Total Years of Service at Retirement", 20, 40, 20)
        current_age   = st.slider("Current Age", 18, 60, 27)
        age_at_retire = st.slider("Age When You Stop Working Entirely", 38, 75, 60)

        # ── Cross-community warning ───────────────────────────────────────────
        def rank_community(r):
            if r.startswith('O'): return 'officer'
            if r.startswith('W'): return 'warrant'
            return 'enlisted'

        start_com  = rank_community(start_rank)
        retire_com = rank_community(retire_rank)
        if start_com != retire_com:
            st.warning(
                f"⚠️ **Cross-community transition detected** ({start_rank} → {retire_rank}). "
                f"The savings rate solver uses your current promotion timeline "
                f"({'enlisted' if start_com == 'enlisted' else start_com}). "
                f"It cannot model the pay jump from a commissioning or warrant transition — "
                f"your actual savings rate needed is likely lower than shown. "
                f"Consider running two separate scenarios."
            )

    with col_r:
        st.subheader("Assets & Goals")
        current_tsp  = st.number_input("Current TSP / IRA Balance ($)", value=10000, step=1000)
        monthly_goal = st.number_input("Desired Monthly Income in Retirement ($)", value=8000, step=500)

        retire_base, _, _ = get_military_pay(retire_rank, yrs_at_retire, "92136", False)
        no_mil_retirement = st.checkbox(
            "I don't plan to retire from the military",
            value=False,
            help="Check this if you plan to separate before 20 years. Sets pension to $0 and removes the pension floor from all calculations."
        )
        if no_mil_retirement:
            pass
        sex_for_apv = st.radio("Sex (only used for actuarial life expectancy)", ["Male", "Female"],
                              horizontal=True,
                              help="Used only for the actuarial pension value calculation.")

        if no_mil_retirement:
            est_pension = calc_high3_pension(retire_rank, yrs_at_retire, multiplier)
            annual_pension = est_pension * 12
            retire_at_age  = current_age + max(0, yrs_at_retire - start_tis)
            swr_value      = annual_pension / 0.04
            apv_value      = calc_pension_apv(annual_pension, int(retire_at_age), discount_rate=0.025, sex=sex_for_apv.lower())
            st.caption("...and it's gone.")
            est_pension = 0.0
        else:
            est_pension = calc_high3_pension(retire_rank, yrs_at_retire, multiplier)
            annual_pension = est_pension * 12
            retire_at_age  = current_age + max(0, yrs_at_retire - start_tis)
            swr_value      = annual_pension / 0.04
            apv_value      = calc_pension_apv(
                annual_pension, int(retire_at_age),
                discount_rate=0.025,
                sex=sex_for_apv.lower()
            )

            pa, pb, pc = st.columns(3)
            pa.metric("Monthly Pension Amount",  f"${est_pension:,.0f}/mo")
            pb.metric("Annual Pension Amount",   f"${annual_pension:,.0f}/yr")
            pc.metric("Total Expected Years of Pension Payments",
                      f"~{int(apv_value / annual_pension * (1 + 0.025)):.0f} yrs",
                      help="Actuarially expected payment duration")

            pd2, pe = st.columns(2)
            pd2.metric(
                "Pension Value Using SWR-Estimatation🤷",
                f"${swr_value:,.0f}",
                help="How much you'd need in savings to replace this pension at a 4% withdrawal rate."
            )
            pe.metric(
                "Pension Value Using Life Expectancy-Estimatation 💀",
                f"${apv_value:,.0f}",
                delta=f"${swr_value - apv_value:+,.0f} vs SWR",
                delta_color="inverse",
                help="SSA 2022 life tables, 2.5% discount rate. The 'true' financial value accounting for mortality risk."
            )
            st.caption(
                "[4% Rule / SWR](https://www.investopedia.com/terms/f/four-percent-rule.asp) · "
                "[SSA 2022 Actuarial Life Tables](https://www.ssa.gov/oact/STATS/table4c6.html)"
            )

        st.subheader("Post-Military Civilian Salary")
        civilian_monthly = st.number_input("Expected Monthly Civilian Salary ($)", min_value=0.0,
                                           value=0.0, step=100.0)
        total_monthly_civ = civilian_monthly + est_pension
        c1, c2 = st.columns(2)
        c1.metric("Civilian + Pension / Month", f"${total_monthly_civ:,.0f}")
        c2.metric("Civilian + Pension / Year",  f"${total_monthly_civ * 12:,.0f}")

    mil_years    = max(0, yrs_at_retire - start_tis)
    mil_months   = int(mil_years * 12)
    years_to_grow = age_at_retire - current_age
    total_months  = max(1, years_to_grow * 12)

    # ── Row 2: Fund allocation ────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 TSP Fund Allocation")
    st.caption(
        "By default, 100% goes to the L-Fund — TSP's automatic lifecycle strategy that shifts to "
        "bonds as you approach retirement. To customize, move the sliders below. "
        "The L-Fund percentage updates automatically to show what's left over."
    )

    alloc_col, inf_col = st.columns([5, 1])
    with inf_col:
        inflation_input = st.slider("Inflation Rate (%)", 0.0, 10.0, 2.5, 0.1,
                                    help="Adjusts returns into today's purchasing power.")
        inflation_rate = inflation_input / 100.0

    # Real returns (Fisher equation): (1+nominal)/(1+inflation) - 1
    def real(nominal): return round(((1 + nominal) / (1 + inflation_rate) - 1) * 100, 1)
    rc = real(FUND_STATS['C']['geo_mean'])
    rs = real(FUND_STATS['S']['geo_mean'])
    ri = real(FUND_STATS['I']['geo_mean'])
    rf = real(FUND_STATS['F']['geo_mean'])
    rg = real(FUND_STATS['G']['geo_mean'])

    with alloc_col:
        fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
        pct_c = fc1.slider(
            f"C-Fund (S&P 500)\n{rc:+.1f}% real ±18%/yr",
            0, 100, 0, 5,
            help="Large-cap U.S. stocks. Highest long-term growth, highest short-term swings."
        )
        pct_s = fc2.slider(
            f"S-Fund (Small Cap)\n{rs:+.1f}% real ±20.2%/yr",
            0, 100, 0, 5,
            help="Small/mid-cap U.S. stocks. Higher potential, higher volatility than C Fund."
        )
        pct_i = fc3.slider(
            f"I-Fund (Intl)\n{ri:+.1f}% real ±17.1%/yr",
            0, 100, 0, 5,
            help="International stocks. Diversification outside the U.S. market."
        )
        pct_f = fc4.slider(
            f"F-Fund (Bonds)\n{rf:+.1f}% real ±4.3%/yr",
            0, 100, 0, 5,
            help="U.S. bond index. Stabilizes your portfolio but lower long-term growth."
        )
        pct_g = fc5.slider(
            f"G-Fund (Govt)\n{rg:+.1f}% real ±0.3%/yr",
            0, 100, 0, 5,
            help="Government securities. Guaranteed — cannot lose principal. Lowest return."
        )
        manual_sum = pct_c + pct_s + pct_i + pct_f + pct_g
        pct_l = max(0, 100 - manual_sum)
        fc6.metric(
            "L-Fund (Auto)\nLifecycle blend",
            f"{pct_l}%",
            delta="Remainder" if pct_l > 0 else "None",
            delta_color="normal" if pct_l > 0 else "off",
            help="Whatever you don't manually allocate goes here. TSP's default target-date strategy."
        )

    if manual_sum > 100:
        st.error(f"⚠️ Over-allocated by {manual_sum - 100}% — reduce your fund allocations. Total must be ≤ 100%.")
        allocation_valid = False
    else:
        alloc_display = f"C:{pct_c}% | S:{pct_s}% | I:{pct_i}% | F:{pct_f}% | G:{pct_g}% | L-Fund (auto): {pct_l}%"
        st.success(f"✅ Allocation: {alloc_display}")
        allocation_valid = True

    alloc_dict = {
        'C': pct_c / 100, 'S': pct_s / 100, 'I': pct_i / 100,
        'F': pct_f / 100, 'G': pct_g / 100, 'L': pct_l / 100,
    }
    # Monte Carlo allocation (L-fund expands dynamically inside the sim)
    mc_manual_alloc = {k: v for k, v in alloc_dict.items() if k != 'L'}
    use_lc = pct_l > 0

    # Blended nominal & real return
    expected_nom       = get_blended_nominal_return(alloc_dict, years_to_grow)
    expected_real_rate = ((1 + expected_nom) / (1 + inflation_rate)) - 1

    # ── Solver & results ──────────────────────────────────────────────────────
    if years_to_grow > 0 and allocation_valid:
        monthly_income_gap   = max(0, monthly_goal - est_pension)
        total_nest_egg_needed = (monthly_income_gap * 12) / 0.04

        # Build projected base pay schedule for military phase
        base_pay_schedule = build_monthly_base_pay_schedule(start_rank, start_tis, min(mil_months, total_months))

        savings_pct, contrib_schedule = solve_savings_rate(
            total_nest_egg_needed, current_tsp,
            base_pay_schedule, civilian_monthly,
            mil_months, total_months,
            alloc_dict, inflation_rate
        )

        st.session_state.pmt_target = savings_pct * get_base_pay(start_rank, start_tis)
        st.session_state.savings_rate_pct = savings_pct
        st.session_state.nest_egg_target = total_nest_egg_needed
        st.session_state.est_pension = est_pension

        current_base = get_base_pay(start_rank, start_tis)
        # Back-calculate civilian savings rate from blended rate
        avg_mil_income = np.mean(base_pay_schedule) if len(base_pay_schedule) > 0 else current_base
        if civilian_monthly > 0:
            civ_pct = savings_pct * (avg_mil_income / civilian_monthly)
        else:
            civ_pct = None

        monthly_dollar_equiv = savings_pct * current_base

        st.divider()
        r1, r2, r3 = st.columns(3)
        r1.metric("Target Nest Egg (Real $)",    f"${total_nest_egg_needed:,.0f}")
        r2.metric("Blended Nominal Return",       f"{expected_nom * 100:.2f}%")
        r3.metric("Real Return (After Inflation)", f"{expected_real_rate * 100:.2f}%")

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "📌 Military Savings Rate",
            f"{savings_pct * 100:.1f}% of Base Pay",
            delta="This percentage is adjusted in MyPay",
            delta_color="off"
        )
        if civ_pct is not None:
            m2.metric(
                "📌 Civilian Savings Rate",
                f"{civ_pct * 100:.1f}% of Civilian Salary",
                delta="Set this up in your 401k or IRA after separation",
                delta_color="off"
            )
        else:
            m2.metric(
                "📌 Civilian Savings Rate",
                "Enter civilian salary above",
                delta="Required to calculate post-military rate",
                delta_color="off"
            )
        m3.metric(
            "Today's Military Dollar Equivalent",
            f"${monthly_dollar_equiv:,.2f} / month",
            delta="Starting point only — see note below",
            delta_color="off"
        )

        # ── TSP Gap Callout ───────────────────────────────────────────────────
        les_tsp = st.session_state.get("les_tsp_actual", 0.0)
        if les_tsp > 0 and current_base > 0:
            current_tsp_pct = (les_tsp / current_base) * 100
            gap_pct = savings_pct * 100 - current_tsp_pct
            gap_dollars = monthly_dollar_equiv - les_tsp
            if gap_pct > 0.5:
                st.warning(
                    f"**You are currently saving {current_tsp_pct:.1f}% of your base pay (${les_tsp:,.2f}/month) toward TSP.** "
                    f"To meet your financial goals, you need to increase your contributions to "
                    f"**{savings_pct * 100:.1f}%** — an increase of **{gap_pct:.1f} percentage points "
                    f"(${gap_dollars:,.2f}/month)**. You can make this adjustment now in "
                    f"[MyPay](https://mypay.dfas.mil)."
                )
            elif gap_pct < -0.5:
                st.success(
                    f"**You are currently saving {current_tsp_pct:.1f}% of your base pay (${les_tsp:,.2f}/month) toward TSP** — "
                    f"**${abs(gap_dollars):,.2f}/month more than your goal requires.** "
                    f"That surplus increases the odds of hitting your goal, reduces the years you need to save until retirement, "
                    f"and increases the amount you'll have in retirement. However, if there's another priority, "
                    f"you are already expected to meet your retirement goals — this surplus could be considered "
                    f"additional guilt-free spending. Congrats! 🎉"
                )
            else:
                st.success(
                    f"**You are currently saving {current_tsp_pct:.1f}% of your base pay (${les_tsp:,.2f}/month) toward TSP** — "
                    f"right on target. Nothing to change."
                )
        elif les_tsp == 0.0:
            st.caption("💡 *Enter your current TSP contribution from your LES in the Budget tab to see how your current savings compares to your goal.*")

        civ_rate_line = (
            f"After separation, target **{civ_pct * 100:.1f}% of your civilian salary** — "
            f"set this up in your employer's 401k or IRA. These two rates work together to get you to your goal."
            if civ_pct is not None
            else "Enter your expected civilian salary above to calculate your post-military savings rate."
        )

        st.info(
            f"**Why the percentage matters more than the dollar amount.**\n\n"
            f"A fixed ${monthly_dollar_equiv:,.0f}/month sounds simple — but inflation erodes its purchasing power every year. "
            f"A percentage of base pay scales automatically with every promotion and raise, keeping your contributions "
            f"aligned with what your future actually costs. Set it once, let your career do the rest.\n\n"
            f"**Military phase:** Save **{savings_pct * 100:.1f}% of base pay** — set this in MyPay. "
            f"{civ_rate_line}\n\n"
            f"More on why this works: [Time Value of Money](https://www.investopedia.com/terms/t/timevalueofmoney.asp)."
        )

        # ── Interactive Savings Rate Explorer ────────────────────────────────
        st.divider()
        st.subheader("🎯 Savings Rate Explorer")
        st.caption("Drag the slider to see how your savings rate affects your portfolio growth and the age at which you hit your goal. Uses your projected income schedule and expected real return.")
        st.info("💡 **This is a what-if explorer.** Adjusting the slider here does not change your plan — it lets you explore tradeoffs between savings rate and retirement age before you commit. If a different rate or age looks better, go back and update your inputs above. The Luck & Timing Roulette simulation below always runs on your calculated savings rate.")

        explore_pct = st.slider(
            "Savings Rate (% of Base Pay)",
            min_value=0.0, max_value=60.0,
            value=float(round(savings_pct * 100, 1)),
            step=0.5,
            key="explorer_slider"
        )

        # Build deterministic growth curve for the explorer rate
        explore_rate = explore_pct / 100.0
        monthly_real = (1 + expected_real_rate) ** (1/12) - 1

        # Full income schedule (military + civilian phases)
        full_income = list(base_pay_schedule)
        for _ in range(total_months - len(base_pay_schedule)):
            full_income.append(civilian_monthly)
        full_income = full_income[:total_months]

        # Simulate deterministic portfolio growth
        balance = float(current_tsp)
        ages = []
        balances = []
        goal_age = None

        for m in range(total_months):
            age_now = current_age + m / 12.0
            contrib = explore_rate * full_income[m] if m < len(full_income) else 0.0
            balance = balance * (1 + monthly_real) + contrib
            ages.append(age_now)
            balances.append(balance)
            if goal_age is None and balance >= total_nest_egg_needed:
                goal_age = age_now

        # Build Plotly figure
        import plotly.graph_objects as go_ret
        fig_exp = go_ret.Figure()

        # Growth curve
        fig_exp.add_trace(go_ret.Scatter(
            x=ages, y=balances,
            mode='lines',
            name='Portfolio Growth',
            line=dict(color='#00b4d8', width=2.5),
            hovertemplate='Age %{x:.1f}: $%{y:,.0f}<extra></extra>'
        ))

        # Horizontal dashed line — nest egg target
        fig_exp.add_hline(
            y=total_nest_egg_needed,
            line_dash="dash", line_color="#ef476f", line_width=1.5,
            annotation_text=f"Target: ${total_nest_egg_needed:,.0f}",
            annotation_position="top left",
            annotation_font_color="#ef476f"
        )

        # Vertical dashed line + annotation at intersection
        if goal_age is not None and goal_age <= age_at_retire:
            fig_exp.add_vline(
                x=goal_age,
                line_dash="dash", line_color="#06d6a0", line_width=1.5,
            )
            fig_exp.add_annotation(
                x=goal_age,
                y=total_nest_egg_needed,
                text=f"  Goal met at age {goal_age:.1f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#06d6a0",
                font=dict(color="#06d6a0", size=12),
                bgcolor="rgba(0,0,0,0.6)",
                bordercolor="#06d6a0",
                borderwidth=1,
                ax=40, ay=-40
            )
        else:
            fig_exp.add_annotation(
                x=ages[len(ages)//2],
                y=max(balances) * 0.5,
                text="Goal not reached within timeframe — increase savings rate",
                showarrow=False,
                font=dict(color="#ef476f", size=12),
                bgcolor="rgba(0,0,0,0.6)"
            )

        fig_exp.update_layout(
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font=dict(color='#fafafa'),
            height=350,
            margin=dict(l=60, r=30, t=30, b=50),
            xaxis=dict(
                title='Age',
                gridcolor='#2a2a3e',
                zerolinecolor='#2a2a3e',
            ),
            yaxis=dict(
                title='Portfolio Value ($)',
                gridcolor='#2a2a3e',
                zerolinecolor='#2a2a3e',
                tickformat='$,.0f'
            ),
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa')
            ),
            showlegend=True
        )

        st.plotly_chart(fig_exp, use_container_width=True)

        # ── Monte Carlo ───────────────────────────────────────────────────────
        st.divider()
        st.subheader("🎲 Luck & Timing Roulette (1,000 Trials)")
        st.markdown("""
You've done the work. You know what you make, what you need, what you need to save, and how you want 
it invested. The graph above gives you the answer — if I do this, when will I meet my goal? It's 
clean, smooth, predictable.

**But it's a lie.**

Real markets don't move in straight lines. They crash the second you buy in. They go sideways for a 
decade while you wonder if you made a mistake. They drop 40% and every instinct you have screams 
*sell*. The average return is a number drawn through decades of panic, euphoria, and everything in 
between — and the average hides all of it.

**Know that this is what you're actually signing up for.**

Every gray line below is a real possible future. Two soldiers, same plan, same rate, same fund — 
completely different outcomes based on nothing but luck and timing. That's the game. There will be 
years that feel like you're losing. Stay in. Don't touch it. You made a plan — execute it like your 
financial future depends on it, because it does.

And if anyone ever tells you they have a guaranteed return, a cheat code, or a hot tip — run. People 
brag about wins. They never mention the losses. The market has no shortcuts: there is only time, 
consistency, and discipline.

*May the odds be ever in your favor.*
        """)

        if st.button("Run Simulation", type="primary"):
            st.session_state.monte_carlo_run = True
            with st.spinner("Running 1,000 trials..."):
                hist_returns, data_source = scrape_and_prep_tsp_data()
                sim_results = run_real_monte_carlo(
                    current_age, age_at_retire, current_tsp,
                    contrib_schedule, hist_returns,
                    pct_l / 100.0, mc_manual_alloc,
                    inflation_rate=inflation_rate, trials=1000
                )
                # Store everything needed to redraw the chart across reruns
                st.session_state.sim_results = sim_results
                st.session_state.sim_savings_pct = savings_pct
                st.session_state.sim_current_age = current_age
                st.session_state.sim_age_at_retire = age_at_retire
                st.session_state.sim_target = total_nest_egg_needed
                st.session_state.sim_data_source = data_source

        # Render chart from session state — survives all reruns after button press
        if st.session_state.get("sim_results") is not None:
            sim_results       = st.session_state.sim_results
            sim_savings_pct   = st.session_state.sim_savings_pct
            sim_current_age   = st.session_state.sim_current_age
            sim_age_at_retire = st.session_state.sim_age_at_retire
            sim_target        = st.session_state.sim_target
            sim_data_source   = st.session_state.sim_data_source

            if sim_data_source == "Proxy":
                st.warning("⚠️ Live market data unavailable. Running on high-fidelity historical proxy data.")

            fig, ax = plt.subplots(figsize=(12, 6), facecolor='#0e1117')
            ax.set_facecolor('#0e1117')
            time_axis = np.linspace(sim_current_age, sim_age_at_retire, sim_results.shape[1])

            p10 = np.percentile(sim_results, 10, axis=0)
            p50 = np.percentile(sim_results, 50, axis=0)
            p90 = np.percentile(sim_results, 90, axis=0)
            success_rate = np.mean(sim_results[:, -1] >= sim_target) * 100
            st.session_state.mc_success_rate = success_rate

            # 20 paths sampled across 0th–90th percentile — excludes extreme outliers
            final_vals = sim_results[:, -1]
            sorted_idx = np.argsort(final_vals)
            p90_cutoff = int(0.90 * len(sorted_idx)) - 1
            sample_idx = [sorted_idx[int(i * p90_cutoff / 19)] for i in range(20)]

            for k, idx in enumerate(sample_idx):
                label = f'Based on {sim_savings_pct*100:.1f}% military savings rate — Probability of Success: {success_rate:.1f}%' if k == 0 else ""
                ax.plot(time_axis, sim_results[idx], color='#b4b4c8', lw=0.9, alpha=0.35, label=label)

            ax.fill_between(time_axis, p10, p90, color='#00b4d8', alpha=0.15)
            ax.plot(time_axis, p90, color='#00b4d8', lw=1.2, linestyle='dashed',
                    label=f'90th Percentile: ${p90[-1]:,.0f} at age {sim_age_at_retire}')
            ax.plot(time_axis, p50, color='#00b4d8', lw=2.5,
                    label=f'Median: ${p50[-1]:,.0f} at age {sim_age_at_retire}')
            ax.plot(time_axis, p10, color='#00b4d8', lw=1, linestyle='dotted',
                    label=f'10th Percentile: ${p10[-1]:,.0f} at age {sim_age_at_retire}')
            ax.axhline(y=sim_target, color='#ef476f', linestyle='--', lw=1.5,
                       label=f'Target: ${sim_target:,.0f}')

            ax.set_ylabel('Portfolio Value ($)', fontsize=11, color='#fafafa')
            ax.set_xlabel('Age', fontsize=11, color='#fafafa')
            ax.tick_params(colors='#fafafa')
            ax.spines['bottom'].set_color('#2a2a3e')
            ax.spines['left'].set_color('#2a2a3e')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, linestyle='--', alpha=0.2, color='#2a2a3e')
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
            legend = ax.legend(loc='upper left', fontsize=9,
                               facecolor='#14141f', edgecolor='#00b4d8',
                               labelcolor='#fafafa', framealpha=0.85)
            st.pyplot(fig)

            st.caption(
                f"**A note on probability of success:** A result of 50–60% is intentional and appropriate. "
                f"Targeting 80–90% means planning to survive the worst historical market sequences — "
                f"which results in significant over-saving in most scenarios. With a military pension as a floor, "
                f"a 50–60% success rate reflects a realistic, balanced plan. "
                f"If your number is well below 50%, consider adjusting your savings rate or retirement age above."
            )

    # ── Assumptions expander ──────────────────────────────────────────────────
    st.divider()
    with st.expander("📋 Model Assumptions"):
        st.markdown("""
        **Promotion Timeline (Primary Zone — Army)**

        | Community | Progression |
        |---|---|
        | **Officers** | O-1 → O-2 at 2 yrs · O-3 at 4 · O-4 at 11 · O-5 at 17 · O-6 at 23 |
        | **Warrant Officers** | W-1 → CW2 at 3 yrs · CW3 at 8 · CW4 at 14 · CW5 at 20 |
        | **Enlisted** | E-1 → E-2 at 6 mo · E-3 at 18 mo · E-4 at 2 yrs · E-5 at 4 · E-6 at 8 · E-7 at 14 · E-8 at 18 · E-9 at 23 |

        > ⏱️ **Promotion lag:** Timelines reflect when pay actually changes — approximately 12 months after board selection. This makes savings rate estimates slightly conservative, which is intentional.

        **Pension (High-3 Average)**

        Averages base pay across the 3 years immediately before retirement, using the promotion timeline above to determine what rank was actually being paid during those years. More accurate than final-pay alone — and slightly lower.

        **Savings Rate Solver**

        Binary-searches for the constant percentage of income that grows your current TSP balance to your target nest egg. Military phase uses your projected base pay schedule (rank + promotion timeline). Civilian phase uses your entered expected salary. All growth is in real (inflation-adjusted) dollars.

        **Fund Return Assumptions** *(inception-to-date, tspfolio.com)*

        | Fund | Nominal CAGR | Std Dev |
        |---|---|---|
        | C-Fund (S&P 500) | 10.7% | ±18.1%/yr |
        | S-Fund (Small Cap) | 9.9% | ±20.2%/yr |
        | I-Fund (International) | 6.8% | ±17.1%/yr |
        | F-Fund (Bonds) | 5.3% | ±4.3%/yr |
        | G-Fund (Govt Securities) | 4.7% | ±0.3%/yr |
        | L-Fund | Dynamic blend based on years to retirement |

        Real returns shown in sliders use the Fisher equation: `(1 + nominal) / (1 + inflation) - 1`. They update live as you adjust the inflation slider.

        **Luck & Timing Roulette**

        1,000 trials. Each trial randomly samples historical monthly returns from real market data (via yfinance proxies: ^GSPC, ^RUT, EFA, AGG, ^IRX) with replacement, and applies your projected contribution schedule. Returns are deflated by your selected inflation rate. Contributions are nominal dollars. Success = portfolio ≥ target nest egg at your stop-working age.

        **Other:** Nest egg target uses the 4% safe withdrawal rule. Civilian salary is a major unknown — be conservative.
        """)
# --- TAB 3: CONSCIOUS SPENDING ---
with tab3:
    st.session_state.tabs_visited.add(3)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 3)
    st.header("Step 3: Where Does It Go?")

    special_pay = st.session_state.get("special_pay", 0.0)

    pay_mode = st.radio(
        "Income Mode",
        [
            "📋 Using my LES values below",
            "🎲 I'll skip the LES and let an algorithm guess my take-home pay—even though it knows nothing about my deductions, allotments, or tax situation. Honestly, it'll fit right in with the rest of my planning: assumptions, hopes, and vibes."
        ],
        key="pay_mode_radio"
    )

    st.divider()

    # ── LES Form ─────────────────────────────────────────────────────────────
    if "📋" in pay_mode:
        st.subheader("🗂️ Leave & Earnings Statement")
        st.caption(
            "Enter the values directly from your LES. This is the most accurate way to know what you actually take home. "
            "Pull up your LES at [myPay](https://mypay.dfas.mil) and follow along line by line."
        )

    les_col1, les_col2, les_col3 = st.columns(3)

    with les_col1:
        st.markdown("**ENTITLEMENTS**")
        tab1_base = float(st.session_state.get("base_pay", 0.0))
        tab1_bah  = float(st.session_state.get("bah_amt",  0.0))
        tab1_bas  = float(st.session_state.get("bas_amt",  0.0))

        # Pre-initialize keys to 0 only on first load
        if "les_base" not in st.session_state: st.session_state["les_base"] = 0.0
        if "les_bah"  not in st.session_state: st.session_state["les_bah"]  = 0.0
        if "les_bas"  not in st.session_state: st.session_state["les_bas"]  = 0.0

        if st.button("⬇️ Import Base Pay / BAH / BAS from Tab 1", key="import_tab1_pay"):
            st.session_state["les_base"] = tab1_base
            st.session_state["les_bah"]  = tab1_bah
            st.session_state["les_bas"]  = tab1_bas
            st.rerun()

        les_base = st.number_input("Base Pay", min_value=0.0, step=10.0, key="les_base")
        les_bah  = st.number_input("BAH",      min_value=0.0, step=10.0, key="les_bah")
        les_bas  = st.number_input("BAS",      min_value=0.0, step=10.0, key="les_bas")

        mismatch_fields = []
        if tab1_base > 0 and abs(les_base - tab1_base) > 1.0: mismatch_fields.append(f"Base Pay (calculator: ${tab1_base:,.2f})")
        if tab1_bah  > 0 and abs(les_bah  - tab1_bah)  > 1.0: mismatch_fields.append(f"BAH (calculator: ${tab1_bah:,.2f})")
        if tab1_bas  > 0 and abs(les_bas  - tab1_bas)   > 1.0: mismatch_fields.append(f"BAS (calculator: ${tab1_bas:,.2f})")

        if mismatch_fields:
            field_names = ", ".join([f.split(" (")[0] for f in mismatch_fields])
            calc_values = ", ".join([f.split("calculator: ")[1].rstrip(")") for f in mismatch_fields])
            st.warning(
                f"⚠️ The value you entered for **{field_names}** does not match the calculated value ({calc_values}). "
                f"If the Base Pay, BAH, or BAS on your LES does not match the calculated values, you should: "
                f"a) be sure you selected all the right info, "
                f"b) if it's still wrong, check with your S1. "
                f"I'm not going to say I'm right and they're wrong, but... actually, yes, that's exactly what I'm saying."
            )

        # Dynamic special pay entries
        if "les_ent_rows" not in st.session_state: st.session_state.les_ent_rows = 0
        les_extra_ent = 0.0
        for i in range(st.session_state.les_ent_rows):
            ec1, ec2 = st.columns([2, 1])
            ec1.text_input("Pay Type", key=f"les_ent_name_{i}", placeholder="e.g. Flight Pay, Jump Pay")
            les_extra_ent += ec2.number_input("Amount", min_value=0.0, step=10.0, key=f"les_ent_amt_{i}")
        if st.button("＋ Add Entitlement", key="les_add_ent"):
            st.session_state.les_ent_rows += 1
            st.rerun()

        les_tot_ent = les_base + les_bah + les_bas + les_extra_ent
        st.metric("TOT ENT", f"${les_tot_ent:,.2f}")

    with les_col2:
        st.markdown("**DEDUCTIONS**")
        les_fed_tax  = st.number_input("Federal Taxes",       min_value=0.0, value=0.0, step=10.0, key="les_fed")
        les_fica_ss  = st.number_input("FICA - Soc Security", min_value=0.0, value=0.0, step=10.0, key="les_ss")
        les_fica_med = st.number_input("FICA - Medicare",     min_value=0.0, value=0.0, step=10.0, key="les_med")
        les_state    = st.number_input("State Taxes",         min_value=0.0, value=0.0, step=10.0, key="les_state",
                                       help="Enter 0 if you live in a state with no income tax (FL, TX, WA, etc.)")
        les_sgli     = st.number_input("SGLI",                min_value=0.0, value=0.0, step=1.0,  key="les_sgli")
        les_sgli_fam = st.number_input("SGLI Fam/Spouse",     min_value=0.0, value=0.0, step=1.0,  key="les_sgli_fam")
        les_tsp      = st.number_input("TSP Contribution\n(Roth or Traditional)", min_value=0.0, value=0.0, step=10.0, key="les_tsp_input",
                                       help="Enter your total TSP deduction — Roth, Traditional, or both combined.")
        les_midmonth = st.number_input("Mid-Month Pay",       min_value=0.0, value=0.0, step=10.0, key="les_mid",
                                       help="Already received on the 15th — this offsets your EOM deposit but is real income you already have.")

        # Dynamic extra deductions
        if "les_ded_rows" not in st.session_state: st.session_state.les_ded_rows = 0
        les_extra_ded = 0.0
        for i in range(st.session_state.les_ded_rows):
            dc1, dc2 = st.columns([2, 1])
            dc1.text_input("Deduction Type", key=f"les_ded_name_{i}", placeholder="e.g. Dental, Garnishment")
            les_extra_ded += dc2.number_input("Amount", min_value=0.0, step=10.0, key=f"les_ded_amt_{i}")
        if st.button("＋ Add Deduction", key="les_add_ded"):
            st.session_state.les_ded_rows += 1
            st.rerun()

        les_tot_ded = les_fed_tax + les_fica_ss + les_fica_med + les_state + les_sgli + les_sgli_fam + les_tsp + les_midmonth + les_extra_ded
        st.metric("TOT DED", f"${les_tot_ded:,.2f}")

        # Save TSP actual to session state for Tab 2 gap callout
        st.session_state.les_tsp_actual = les_tsp

    with les_col3:
        st.markdown("**ALLOTMENTS**")
        st.caption("Recurring autopays — insurance, savings allotments, etc.")

        if "les_almt_rows" not in st.session_state: st.session_state.les_almt_rows = 1
        les_tot_almt = 0.0
        for i in range(st.session_state.les_almt_rows):
            ac1, ac2 = st.columns([2, 1])
            ac1.text_input("Allotment", key=f"les_almt_name_{i}", placeholder="e.g. TRICARE Dental")
            les_tot_almt += ac2.number_input("Amount", min_value=0.0, step=10.0, key=f"les_almt_amt_{i}")
        if st.button("＋ Add Allotment", key="les_add_almt"):
            st.session_state.les_almt_rows += 1
            st.rerun()

        st.metric("TOT ALMT", f"${les_tot_almt:,.2f}")

        st.divider()
        st.markdown("**SUMMARY**")
        eom_pay     = les_tot_ent - les_tot_ded - les_tot_almt
        mil_takehome = les_midmonth + max(0.0, eom_pay)

        st.metric("TOT ENT",   f"${les_tot_ent:,.2f}")
        st.metric("– TOT DED", f"${les_tot_ded:,.2f}")
        st.metric("– TOT ALMT",f"${les_tot_almt:,.2f}")
        st.metric("= EOM PAY", f"${max(0.0, eom_pay):,.2f}")

    # ── LES summary info or fallback ─────────────────────────────────────────
    if "📋" in pay_mode:
        st.info(
            f"**Mid-Month Pay (${les_midmonth:,.2f}) + EOM Pay (${max(0.0,eom_pay):,.2f}) "
            f"= Total Military Take-Home: ${mil_takehome:,.2f}/month.**\n\n"
            f"Your LES EOM Pay is only the *second half* of your monthly pay — the mid-month deposit already "
            f"hit your account on the 15th. Both deposits together are your actual military take-home."
        )
    else:
        # Fallback values for 🎲 path — LES form was skipped
        les_midmonth = 0.0
        eom_pay      = 0.0
        mil_takehome = 0.0
        les_fed_tax  = 0.0
        les_fica_ss  = 0.0
        les_fica_med = 0.0
        les_state    = 0.0
        les_tot_ent  = 0.0

    st.divider()

    # ── Additional Income ─────────────────────────────────────────────────────
    st.subheader("➕ Additional Income")
    st.write("Add any other income streams below. **All amounts must be after-tax** — enter what actually hits your account, not gross.")

    if "extra_income_rows" not in st.session_state: st.session_state.extra_income_rows = 0
    if st.button("Add Income Stream"): st.session_state.extra_income_rows += 1

    total_extra_income = 0.0
    for i in range(st.session_state.extra_income_rows):
        c_name, c_amt, c_freq = st.columns([2, 1, 1])
        with c_name: st.text_input("Source Name", key=f"ei_name_{i}", placeholder="e.g. Spouse's Job, Uber, Rental")
        with c_amt: amt = st.number_input("Amount ($)", key=f"ei_amt_{i}", min_value=0.0, step=100.0)
        with c_freq:
            freq = st.selectbox("Frequency", ["Monthly", "Bi-weekly", "Annually"], key=f"ei_freq_{i}")

        if freq == "Monthly": monthly_amt = amt
        elif freq == "Bi-weekly": monthly_amt = (amt * 26) / 12
        else: monthly_amt = amt / 12
        total_extra_income += monthly_amt

    if st.session_state.extra_income_rows > 0:
        if st.button("Clear Extra Income", type="secondary"):
            st.session_state.extra_income_rows = 0
            st.rerun()

    st.divider()

    # ── Take-Home Anchor ──────────────────────────────────────────────────────
    if "🎲" in pay_mode:
        mil_taxable    = st.session_state.base_pay + special_pay
        mil_nontaxable = st.session_state.bah_amt + st.session_state.bas_amt
        taxable_monthly = mil_taxable + total_extra_income
        annual_taxable  = taxable_monthly * 12
        std_deduction   = 15000
        tax_base = max(0, annual_taxable - std_deduction)
        tax = 0
        if tax_base > 100525:
            tax += (tax_base - 100525) * 0.24; tax_base = 100525
        if tax_base > 47150:
            tax += (tax_base - 47150) * 0.22; tax_base = 47150
        if tax_base > 11600:
            tax += (tax_base - 11600) * 0.12; tax_base = 11600
        if tax_base > 0:
            tax += tax_base * 0.10
        monthly_fed_tax = tax / 12
        monthly_fica    = taxable_monthly * 0.0765
        take_home = taxable_monthly - monthly_fed_tax - monthly_fica + mil_nontaxable + total_extra_income
        st.caption(f"*Estimated Taxes: Federal **${monthly_fed_tax:,.0f}** | FICA **${monthly_fica:,.0f}** — BAH/BAS excluded from tax. Your actual deductions will differ.*")
    else:
        take_home = mil_takehome + total_extra_income

    st.info(f"💰 Total Combined Monthly Take-Home: **${take_home:,.2f}**")
    st.divider()

    col_a, col_b, col_c = st.columns(3)
    bp = st.session_state.base_pay if st.session_state.base_pay > 0 else (take_home * 0.6)
    
    with col_a:
        st.subheader("🛑 Fixed Costs")
        housing = st.number_input("Housing + Utilities", value=float(st.session_state.bah_amt))
        trans = st.number_input("Car/Insurance/Fuel", value=bp * 0.15)
        health = st.number_input("Healthcare", value=bp * 0.08)
        groceries = st.number_input("Groceries", value=bp * 0.13)
        fixed_total = housing + trans + health + groceries
        fixed_pct = (fixed_total / take_home * 100) if take_home > 0 else 0
        st.metric("Total Fixed", f"${fixed_total:,.2f}", f"{fixed_pct:.1f}%")

    with col_b:
        st.subheader("🚀 Invest/Save")
        retirement = st.number_input("Retirement (TSP/IRA)", value=float(st.session_state.pmt_target))
        emergency = st.number_input("Emergency Savings", value=take_home * 0.05)
        save_invest_total = retirement + emergency
        save_pct = (save_invest_total / take_home * 100) if take_home > 0 else 0
        st.metric("Total Invested", f"${save_invest_total:,.2f}", f"{save_pct:.1f}%")

    with col_c:
        st.subheader("🍹 Guilt-Free")
        available_for_fun = max(0.0, take_home - fixed_total - save_invest_total)

        experiences   = st.number_input("Experiences (Travel, Events)",        min_value=0.0, value=0.0, step=50.0)
        convenience   = st.number_input("Convenience (Delivery, Time-savers)", min_value=0.0, value=0.0, step=50.0)
        hobbies       = st.number_input("Hobbies (Gear, Gym, Gaming)",          min_value=0.0, value=0.0, step=50.0)
        personal      = st.number_input("Personal (Clothes, Grooming)",         min_value=0.0, value=0.0, step=50.0)
        entertainment = st.number_input("Entertainment (Dining Out, Bars)",     min_value=0.0, value=0.0, step=50.0)
        generosity    = st.number_input("Generosity (Gifts, Donations)",        min_value=0.0, value=0.0, step=50.0)

        fun_total = experiences + convenience + hobbies + personal + entertainment + generosity
        fun_pct   = (fun_total / take_home * 100) if take_home > 0 else 0
        remaining = available_for_fun - fun_total

        st.divider()
        if remaining > 0.005:
            st.success(f"**Remaining to allocate: ${remaining:,.2f}**")
        elif remaining >= -0.005:
            st.success("**Fully allocated. Nothing left on the table. ✅**")
        else:
            st.error(f"**Over-allocated by ${abs(remaining):,.2f} — trim a category above.**")

        st.metric("Guilt-Free Total", f"${fun_total:,.2f}", f"{fun_pct:.1f}% of take-home")

    # 1. Calculate Taxes for the Sankey Flow
    if "🎲" in pay_mode:
        sankey_tax = monthly_fed_tax + monthly_fica
        sankey_gross = les_tot_ent + total_extra_income
    else:
        sankey_tax = les_fed_tax + les_fica_ss + les_fica_med + les_state
        sankey_gross = les_tot_ent + total_extra_income

    invest_total = save_invest_total 
    guilt_free_total = fun_total
    surplus_amt = take_home - (fixed_total + invest_total + guilt_free_total)

    # Save for Tab 7
    st.session_state.tab3_take_home  = take_home
    st.session_state.tab3_fixed      = fixed_total
    st.session_state.tab3_invested   = invest_total
    st.session_state.tab3_guilt_free = guilt_free_total

    st.divider()
    st.subheader("📊 Your 2026 Monthly Cash Flow Architecture")

    nodes = ["Gross Income", "Taxes", "Take-Home Pay", "Fixed Costs", "Investments", "Guilt-Free", "Surplus"]
    links = {
        "source": [0, 0, 2, 2, 2, 2],
        "target": [1, 2, 3, 4, 5, 6],
        "value": [
            max(0.1, sankey_tax),      
            max(0.1, take_home),       
            max(0.1, fixed_total),     
            max(0.1, invest_total),    
            max(0.1, guilt_free_total),
            max(0.1, surplus_amt)      
        ],
        "color": [
            "rgba(200, 200, 200, 0.4)", "rgba(0, 212, 255, 0.4)", "rgba(255, 99, 132, 0.5)",  
            "rgba(75, 192, 192, 0.5)", "rgba(255, 206, 86, 0.5)", "rgba(0, 255, 127, 0.7)"    
        ]
    }

    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, label=nodes, color="#00D4FF"),
        link=links
    )])

    fig.update_layout(
        font=dict(color="white", size=12), paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', template="plotly_dark", height=600,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    if surplus_amt < -5: st.error(f"⚠️ **Budget Deficit:** You are over-allocated by **${abs(surplus_amt):,.2f}**.")
    elif surplus_amt > 5: st.success(f"✅ **Budget Surplus:** You have **${surplus_amt:,.2f}** unallocated.")

# --- TAB 4: FINLIT QUIZ ---
with tab4:
    st.session_state.tabs_visited.add(4)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 4)
    st.header("Know the Game: Financial Readiness Quiz")
    st.write("Let's see if you're actually ready to build wealth, or if you're about to become a dealership's favorite customer.")
    
    with st.form("finlit_quiz"):
        st.markdown("### 🪖 The Basics")
        q1 = st.radio("1. If you are in the Blended Retirement System (BRS), what is the maximum percentage the DoD will match?", 
                      ["3% - Standard government match", "4% - The default contribution rate", "5% - The absolute maximum match"], index=None)
        q2 = st.radio("2. Which of the following military pay components are entirely tax-free?", 
                      ["Enlistment and Reenlistment Bonuses", "BAH (Housing) and BAS (Food)", "Hazardous Duty and Flight Pay"], index=None)
        q3 = st.radio("3. When you sell leave days back to the military, what exactly are you getting paid?", 
                      ["Base Pay + BAH + BAS", "Just your Base Pay (taxed)", "Double your Base Pay"], index=None)
        
        st.markdown("### 📈 The TSP (Thrift Savings Plan)")
        q4 = st.radio("4. If you joined after 2018, what fund does your TSP automatically invest in?", 
                      ["The G Fund (Government Securities)", "The C Fund (S&P 500)", "An L Fund (Lifecycle) matched to your age"], index=None) 
        q5 = st.radio("5. What is the fundamental difference between Traditional and Roth TSP?", 
                      ["Roth = Tax-deductible now, taxed later", "Roth = Taxes paid now, tax-free growth and withdrawals later", "Roth = No taxes ever, guaranteed"], index=None)
        q6 = st.radio("6. How much of your base pay are you legally allowed to contribute to the TSP?", 
                      ["Up to 15%", "Up to 60%", "Up to 100% (minus taxes and standard deductions)"], index=None)
        
        st.markdown("### 💳 Debt & Credit")
        q7 = st.radio("7. How does the Servicemembers Civil Relief Act (SCRA) protect you from debt?", 
                      ["Caps interest at 0% for all loans while deployed", "Caps interest at 6% for debt acquired BEFORE joining the military", "Caps interest at 18% for all credit cards"], index=None)
        q8 = st.radio("8. What is the guaranteed return rate of the Savings Deposit Program (SDP) while deployed?", 
                      ["5% annually", "10% annually (on up to $10,000)", "It just matches the S&P 500"], index=None)
        q9 = st.radio("9. What is the mathematical target for a fully funded Emergency Fund?", 
                      ["Exactly $500", "1 month of your Base Pay", "3 to 6 months of your fixed living expenses"], index=None)
        q10 = st.radio("10. Which of these actually hurts your credit score?", 
                       ["Checking your own score on Credit Karma", "Maxing out your credit limit (high utilization)", "Paying off a car loan completely"], index=None)
        q11 = st.radio("11. If you finance a $25,000 car at 24% APR over 72 months, what happens?", 
                       ["You build credit very fast", "You pay about $3,000 in interest", "You end up paying nearly double the car's sticker price"], index=None)
        q12 = st.radio("12. In a normal economic market, what is a realistic, 'good' auto loan rate?", 
                       ["0% is standard everywhere", "4% to 8%", "15% to 20%"], index=None)
        q13 = st.radio("13. Which habit is the absolute best way to build an elite credit score?", 
                       ["Keeping a small balance to 'show usage'", "Paying the minimum due on time every month", "Paying the full statement balance every single month"], index=None) 
        q14 = st.radio("14. What is mathematically the WORST place to store a $10,000 emergency fund?", 
                       ["A High-Yield Savings Account (HYSA)", "A standard checking account earning 0.01%", "A Money Market Account"], index=None)
        
        st.markdown("### 🦅 Big Military Benefits")
        q15 = st.radio("15. The Post-9/11 GI Bill pays your tuition, plus a monthly housing stipend equal to what?", 
                       ["The Base Pay of an E-5", "BAH at the E-5 with dependents rate for your school's zip code", "A flat $1,000 a month"], index=None)
        q16 = st.radio("16. What is the 'catch' for transferring your GI Bill to a spouse or child?", 
                       ["You can do it anytime after 10 years of service",
                        "You must have 6 years of service, commit to 4 MORE years, AND have 100% GI Bill eligibility — which academy and ROTC scholarship grads don't reach until year 8 or 7 respectively",
                        "You can only do it right before you retire"], index=None)
        q17 = st.radio("17. The VA Loan is famous for 'zero down payment'. What is the reality of buying a home?", 
                       ["You need absolutely zero cash to buy a house", "You still need cash for closing costs, earnest money, and inspections", "You are secretly required to put down 3%"], index=None)
        q18 = st.radio("18. How do you get the expensive VA Loan 'Funding Fee' completely waived?", 
                       ["Receive a Good Conduct Medal", "Get a VA disability rating of 10% or higher", "Request a waiver from your Commanding Officer"], index=None)
        q19 = st.radio("19. Can you use a VA Loan to buy a multi-family property (like a duplex or quadplex)?", 
                       ["No, single-family homes only", "Yes, but you must put 20% down", "Yes, as long as you live in one of the units for at least a year"], index=None)
        
        submitted = st.form_submit_button("Submit Answers & Get Scored")
        
        if submitted:
            score = 0
            if q1 == "5% - The absolute maximum match": score += 1
            if q2 == "BAH (Housing) and BAS (Food)": score += 1
            if q3 == "Just your Base Pay (taxed)": score += 1
            if q4 == "An L Fund (Lifecycle) matched to your age": score += 1
            if q5 == "Roth = Taxes paid now, tax-free growth and withdrawals later": score += 1
            if q6 == "Up to 100% (minus taxes and standard deductions)": score += 1
            if q7 == "Caps interest at 6% for debt acquired BEFORE joining the military": score += 1
            if q8 == "10% annually (on up to $10,000)": score += 1
            if q9 == "3 to 6 months of your fixed living expenses": score += 1
            if q10 == "Maxing out your credit limit (high utilization)": score += 1
            if q11 == "You end up paying nearly double the car's sticker price": score += 1
            if q12 == "4% to 8%": score += 1
            if q13 == "Paying the full statement balance every single month": score += 1
            if q14 == "A standard checking account earning 0.01%": score += 1
            if q15 == "BAH at the E-5 with dependents rate for your school's zip code": score += 1
            if q16 == "You must have 6 years of service, commit to 4 MORE years, AND have 100% GI Bill eligibility — which academy and ROTC scholarship grads don't reach until year 8 or 7 respectively": score += 1
            if q17 == "You still need cash for closing costs, earnest money, and inspections": score += 1
            if q18 == "Get a VA disability rating of 10% or higher": score += 1
            if q19 == "Yes, as long as you live in one of the units for at least a year": score += 1
            
            p = int((score / 19) * 100)
            
            st.divider()
            st.metric("Final Score", f"{score}/19", f"{p}%")
            
            if score >= 18: 
                st.success("🏆 **Elite Status.** You understand the game. Don't let lifestyle creep steal your wealth.")
                st.balloons()
            elif score >= 14: 
                st.info("👍 **Solid Baseline.** You are safe from the Mustang trap, but you need to read up on your long-term benefits.")
            else: 
                st.error("🚨 **High Risk.** You are leaving thousands of dollars on the table. Hit Tab 5 (The Action Plan) right now.")

# --- TAB 5: ACTION PLAN ---
with tab5:
    st.session_state.tabs_visited.add(5)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 5)
    st.header("Way Ahead: Your Financial Order of Operations")
    st.write("Gamifying the classic financial order of operations. Expand each step, execute the mission, and check it off.")

    total_steps = 9
    steps_completed = sum([st.session_state.get(f"step_{i}", False) for i in range(1, total_steps + 1)])
    progress_pct = int((steps_completed / total_steps) * 100)
    
    col_pct, col_bar = st.columns([1, 4])
    with col_pct:
        st.metric("Mission Completion", f"{progress_pct}%", f"{steps_completed}/{total_steps} Steps")
    with col_bar:
        st.write("") 
        st.write("")
        st.progress(steps_completed / total_steps)
    
    if steps_completed == total_steps:
        st.balloons()
        st.success("🎉 Outstanding! You have executed the order of operations, killed your toxic debt, and set your wealth generation on autopilot.")
    
    st.divider()

    st.subheader("Phase 1: Stop the Bleeding (Immediate Action)")
    with st.expander("1. Secure the BRS Match (Free Money)"):
        st.markdown("""
        * **The Mission:** If you are in the Blended Retirement System (BRS), the DoD matches up to 5% of your base pay. If you contribute 4%, you are taking a voluntary pay cut.
        * **Action Steps:** Log into MyPay. Navigate to the "Traditional/Roth TSP" section. Set your contribution to a minimum of 5% (Roth is usually best for junior/mid-grade ranks due to tax-free allowances).
        """)
        st.checkbox("✅ I have secured my 5% BRS Match", key="step_1")

    with st.expander("2. The SCRA Debt Hack"):
        st.markdown("""
        * **The Mission:** The Servicemembers Civil Relief Act (SCRA) legally caps interest rates at 6% for any debt you acquired *before* entering active duty. 
        * **Action Steps:** Identify pre-military credit cards, auto loans, or student loans. Call your lender's specific SCRA department. Submit a copy of your active-duty orders. They are legally required to drop the rate and backdate the refund.
        """)
        st.checkbox("✅ I have verified my SCRA eligibility and contacted lenders", key="step_2")

    with st.expander("3. Nuke Toxic Debt (The 24% APR Trap)"):
        st.markdown("""
        * **The Mission:** You cannot out-invest a 20% credit card or a predatory car loan from outside the gate. 
        * **Action Steps:** Take the "Surplus" from your Tab 3 budget and route 100% of it toward your highest-interest debt. Use the Avalanche Method (mathematically optimal) or Snowball Method (psychological wins).
        """)
        st.checkbox("✅ I have a plan in place to eliminate all debt over 8% APR", key="step_3")

    st.subheader("Phase 2: Build Financial Armor")
    with st.expander("4. Escape the 0.01% Checking Account (HYSA)"):
        st.markdown("""
        * **The Mission:** Traditional banks pay you pennies while inflation eats your money. Keep your Emergency Fund in a Higher Yield Option for maximum accessibility *and* high interest (typically 4-5%).
        * **Action Steps:** Open a High-Yield Savings Account (HYSA). Change your direct deposit on MyPay or set up an auto-transfer from your checking account to route your "Emergency Fund" savings directly to this account. Aim for 3-6 months of your Fixed Costs.
        """)
        st.checkbox("✅ My emergency fund is sitting in an HYSA", key="step_4")

    st.subheader("Phase 3: The Engine (Wealth Generation)")
    with st.expander("5. Escape the G-Fund Trap"):
        st.markdown("""
        * **The Mission:** If you joined before 2018, your TSP defaulted into the G-Fund (Government Securities). It is hyper-conservative and barely beats inflation. 
        * **Action Steps:** Move your investments into the C-Fund, S-Fund, I-Fund, or an L-Fund (Lifecycle) that matches your expected retirement year. 
        """)
        st.checkbox("✅ My TSP is out of the G-Fund and properly invested", key="step_5")

    with st.expander("6. Automate the 'Retirement Gap'"):
        st.markdown("""
        * **The Mission:** Tab 2 showed you exactly how much extra you need to invest monthly to hit your FIRE number. Willpower fails; automation doesn't.
        * **Action Steps:** 1. Increase your TSP contributions to the percentage that will meet your monthly retirement goals. 
            2. **Crucial TSP Step:** Log into TSP.gov. You must change your **Contribution Allocation** (where *new* money from your paycheck goes) AND conduct an **Interfund Transfer** (moving the *existing* money already in your account) into your desired funds. 
            3. Alternatively, or if you are on track to max out your TSP entirely, open a Roth IRA. Set up an auto-draft from your checking account on the 1st of every month to fund it.
        """)
        st.checkbox("✅ My required monthly investments are fully automated", key="step_6")

    st.subheader("Phase 4: Military Cheat Codes")
    with st.expander("7. The GI Bill Transfer Trap"):
        st.markdown("""
        * **The Mission:** You cannot transfer the Post-9/11 GI Bill to your spouse or kids as a retirement gift. You must have at least 6 years of service AND commit to serving 4 more years from the date of transfer. You must also have 100% GI Bill eligibility — and this is where many officers get caught off guard. If you commissioned from West Point, your 5-year ADSO does not count toward that eligibility clock, meaning you won't hit 100% until year 8 of total service. ROTC scholarship officers reach it at year 7. OCS and non-scholarship ROTC officers reach it at year 3. Know which category you're in.
        * **Action Steps:** The exact day you meet both requirements — 6 years of service AND 100% eligibility — log into MilConnect and initiate the transfer. If you wait until you are 18 years in, you will be forced to serve until 22 years to keep the benefit.
        """)
        st.checkbox("✅ I have transferred my GI Bill (Or decided not to)", key="step_7")

    with st.expander("8. The Deployment Multiplier (SDP)"):
        st.markdown("""
        * **The Mission:** If you deploy to a combat zone, the military offers the Savings Deposit Program (SDP), which guarantees a massive 10% annual return on up to $10,000.
        * **Action Steps:** Once you are in theater for 30 days, go to the local finance office (or set it up via MyPay) and max this out before investing another dime in the stock market.
        """)
        st.checkbox("✅ I am aware of the SDP and will use it if deployed", key="step_8")

    with st.expander("9. VA Loan & The 'Funding Fee' Waiver"):
        st.markdown("""
        * **The Mission:** The VA loan allows 0% down, but it charges a "Funding Fee" (up to 3.3% of the loan amount). However, if you have a service-connected disability rating of just **10%**, that fee is completely waived—saving you thousands at closing.
        * **Action Steps:** Go to medical. Document your back, your knees, and your tinnitus *now*. When you separate, file your BDD (Benefits Delivery at Discharge) claim 180 days out.
        """)
        st.checkbox("✅ I am documenting my medical records for my BDD claim", key="step_9")

# --- TAB 6: FEEDBACK & AAR ---
with tab6:
    st.session_state.tabs_visited.add(6)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 6)
    st.header("Feedback")
    st.write("Got a question? Found a bug? Want a new feature? Drop it below.")
    
    contact_form = """
    <form action="https://formsubmit.co/ian.moss@nps.edu" method="POST">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_subject" value="F.I.R.E. for Effect — Feedback">
        <input type="text" name="name" placeholder="Your Name/Callsign (Optional)" style="width: 100%; padding: 10px; margin-bottom: 10px; border-radius: 5px; border: 1px solid #ccc;">
        <input type="email" name="email" placeholder="Your Email (If you want a reply)" style="width: 100%; padding: 10px; margin-bottom: 10px; border-radius: 5px; border: 1px solid #ccc;">
        <textarea name="message" placeholder="Questions, comments, or brilliant ideas go here..." rows="5" required style="width: 100%; padding: 10px; margin-bottom: 10px; border-radius: 5px; border: 1px solid #ccc;"></textarea>
        <button type="submit" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Send to the Developer</button>
    </form>
    """
    st.markdown(contact_form, unsafe_allow_html=True)

# --- TAB 7: MY FINANCIAL PLAN (PDF) ---
with tab7:
    st.session_state.tabs_visited.add(7)
    st.session_state.max_tab_reached = max(st.session_state.max_tab_reached, 7)
    st.header("📄 Your Plan")
    st.caption("A snapshot of your numbers from each tab — income, retirement targets, and budget. Download it as a PDF to keep, share, or brief your spouse.")

    # ── Check what data is available ─────────────────────────────────────────
    missing = []
    if st.session_state.get("base_pay", 0.0) == 0.0:
        missing.append("**What You Make** — complete your rank, TIS, and zip code")
    if st.session_state.get("pmt_target", 0.0) == 0.0:
        missing.append("**Retirement Goal Setting** — complete your career inputs and fund allocation")
    tab3_take_home = st.session_state.get("tab3_take_home", 0.0)
    if tab3_take_home == 0.0:
        missing.append("**Where Does It Go?** — enter your take-home pay")

    if missing:
        st.warning(
            "Complete the following tabs before generating your plan:\n\n" +
            "\n".join(f"- {m}" for m in missing)
        )
    else:
        # ── Pull data from session state ──────────────────────────────────────
        base_pay      = st.session_state.get("base_pay", 0.0)
        bah_amt       = st.session_state.get("bah_amt", 0.0)
        bas_amt       = st.session_state.get("bas_amt", 0.0)
        special_pay   = st.session_state.get("special_pay", 0.0)
        gross_monthly = base_pay + bah_amt + bas_amt + special_pay

        pmt_target    = st.session_state.get("pmt_target", 0.0)
        savings_rate  = st.session_state.get("savings_rate_pct", 0.0)
        nest_egg      = st.session_state.get("nest_egg_target", 0.0)
        est_pension   = st.session_state.get("est_pension", 0.0)
        success_prob  = st.session_state.get("mc_success_rate", None)

        take_home     = st.session_state.get("tab3_take_home", 0.0)
        fixed_costs   = st.session_state.get("tab3_fixed", 0.0)
        invested      = st.session_state.get("tab3_invested", 0.0)
        guilt_free    = st.session_state.get("tab3_guilt_free", 0.0)
        surplus       = take_home - fixed_costs - invested - guilt_free

        on_track = surplus >= 0 and invested >= pmt_target * 0.9

        if on_track:
            way_forward = (
                f"Based on your numbers, you're in a strong position. Your budget has a ${surplus:,.0f}/month "
                f"surplus and your investments are on pace. Set your TSP contribution to {savings_rate*100:.1f}% "
                f"of base pay in MyPay and leave it alone. Every promotion is an opportunity to increase your "
                f"contribution rate — not your spending. You're automated and ready to roll."
            )
            st.success(way_forward)
        else:
            shortfall = max(0, pmt_target - invested)
            way_forward = (
                f"Your numbers show there's work to do — your budget is "
                f"{'in deficit by $' + f'{abs(surplus):,.0f}/month' if surplus < 0 else 'tight'} "
                f"and your investments are ${shortfall:,.0f}/month short of your goal. "
                "Start with the BRS match, eliminate high-interest debt, then automate your savings rate. "
                "Small adjustments now compound significantly over a career."
            )
            st.warning(way_forward)

        # ── PDF button at top ─────────────────────────────────────────────────
        if st.button("📥 Generate & Download PDF", type="primary"):
            st.session_state.pdf_downloaded = True
            if not st.session_state.session_logged:
                st.session_state.session_logged = True
                log_session()
            from fpdf import FPDF
            import datetime

            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(15, 15, 15)

            def safe(text):
                return (text
                    .replace('\u2014', '-').replace('\u2013', '-')
                    .replace('\u2190', '<-').replace('\u2192', '->')
                    .replace('\u2019', "'").replace('\u2018', "'")
                    .replace('\u201c', '"').replace('\u201d', '"')
                    .replace('\u2026', '...')
                )

            pdf.set_font("Helvetica", "B", 18)
            pdf.set_fill_color(30, 60, 114)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 12, safe("F.I.R.E. for Effect - Your Financial Plan"), fill=True, ln=True, align="C")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, safe(f"Generated {datetime.date.today().strftime('%B %d, %Y')}  |  For planning purposes only - not financial advice."), ln=True, align="C")
            pdf.ln(4)

            def section_header(title):
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_fill_color(220, 230, 245)
                pdf.cell(0, 7, safe(f"  {title}"), fill=True, ln=True)
                pdf.ln(1)

            def row(label, value, indent=4):
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(80, 6, safe(" " * indent + label), ln=False)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 6, safe(value), ln=True)

            section_header("INCOME SNAPSHOT")
            row("Monthly Gross Pay:", f"${gross_monthly:,.0f}")
            row("  Base Pay:", f"${base_pay:,.0f}")
            row("  BAH (Tax-Free):", f"${bah_amt:,.0f}")
            row("  BAS (Tax-Free):", f"${bas_amt:,.0f}")
            row("  Special Pays:", f"${special_pay:,.0f}")
            pdf.ln(2)

            section_header("RETIREMENT TARGETS")
            row("Estimated Monthly Pension:", f"${est_pension:,.0f}  (High-3 Average)")
            row("Target Nest Egg:", f"${nest_egg:,.0f}")
            row("Required Savings Rate:", f"{savings_rate*100:.1f}% of Base Pay  <- Set this in MyPay" if savings_rate else "N/A")
            if success_prob is not None:
                row("Luck & Timing Roulette — Probability of Success:", f"{success_prob:.0f}%")
            pdf.ln(2)

            section_header("MONTHLY BUDGET SUMMARY")
            row("Take-Home Pay:", f"${take_home:,.0f}")
            row("Fixed Costs:", f"${fixed_costs:,.0f}")
            row("Investments / Savings:", f"${invested:,.0f}")
            row("Guilt-Free Spending:", f"${guilt_free:,.0f}")
            status = "SURPLUS" if surplus >= 0 else "DEFICIT"
            row(f"Budget {status}:", f"${abs(surplus):,.0f}/month")
            pdf.ln(2)

            section_header("YOUR WAY FORWARD")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(15)
            pdf.multi_cell(180, 5, safe(way_forward))
            pdf.ln(2)

            section_header("PRIORITY ACTIONS")
            if on_track:
                actions = [
                    f"Set TSP contribution to {savings_rate*100:.1f}% of base pay in MyPay",
                    "Verify TSP fund allocation matches your plan (Interfund Transfer if needed)",
                    "After every promotion — increase savings rate, not spending",
                    "Keep emergency fund in a High-Yield Savings Account (HYSA)",
                ]
            else:
                actions = [
                    "Secure your 5% BRS match in MyPay immediately — this is free money",
                    "Identify and cut the largest negotiable fixed cost (housing, vehicle)",
                    "Eliminate all debt above 8% APR before increasing discretionary spending",
                    f"Work toward {savings_rate*100:.1f}% TSP contribution — start lower, increase with promotions",
                    "Review full Way Ahead checklist in the app for step-by-step guidance",
                ]
            for i, action in enumerate(actions, 1):
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_x(15)
                pdf.cell(8, 5, f"{i}.", ln=False)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(167, 5, safe(action))
                pdf.set_x(15)

            pdf.ln(3)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(120, 120, 120)
            pdf.multi_cell(180, 4, safe(
                "This document is for educational purposes only. Projections use simplified assumptions including "
                "primary-zone promotion timelines, historical TSP fund return averages, and a 4% safe withdrawal rate. "
                "Actual results will vary. Consult a Certified Financial Planner for personalized advice."))

            pdf_bytes = pdf.output()
            st.download_button(
                label="⬇️ Download Your Financial Plan (PDF)",
                data=bytes(pdf_bytes),
                file_name=f"military_financial_plan_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )
            st.success("✅ PDF ready — click above to download.")

        st.divider()

        # ── On-screen preview ─────────────────────────────────────────────────
        st.subheader("📊 Snapshot Preview")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**💰 Income**")
            st.metric("Monthly Gross", f"${gross_monthly:,.0f}")
            st.metric("Base Pay", f"${base_pay:,.0f}")
            st.metric("BAH", f"${bah_amt:,.0f}")
            st.metric("BAS", f"${bas_amt:,.0f}")
        with col_b:
            st.markdown("**📈 Retirement**")
            st.metric("Est. Monthly Pension", f"${est_pension:,.0f}")
            st.metric("Target Nest Egg", f"${nest_egg:,.0f}")
            st.metric("Required Savings Rate", f"{savings_rate*100:.1f}% of Base Pay" if savings_rate else "—")
            if success_prob is not None:
                st.metric("Luck & Timing Roulette", f"{success_prob:.0f}%")
        with col_c:
            st.markdown("**⚖️ Budget**")
            st.metric("Take-Home", f"${take_home:,.0f}")
            st.metric("Fixed Costs", f"${fixed_costs:,.0f}")
            st.metric("Invested", f"${invested:,.0f}")
            delta_color = "normal" if surplus >= 0 else "inverse"
            st.metric("Surplus / Deficit", f"${surplus:,.0f}",
                      delta="On track" if surplus >= 0 else "Needs attention",
                      delta_color=delta_color)

# --- LOG SESSION ON EXIT (if not already logged via PDF download) ---
if not st.session_state.session_logged:
    st.session_state.session_logged = True
    log_session()

# --- GLOBAL FOOTER & DISCLAIMER ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; font-size: 0.85em; color: gray;'>
<b>Disclaimer:</b> This tool is for educational purposes only. I am not a financial advisor — but financial literacy isn't reserved for people with CFP after their name. Purposeful scrolling through r/personalfinance and r/MilitaryFinance, clicking some links, and reading for a weekend will get you further than you can possibly imagine. Where applicable, model assumptions are documented in the expandable sections throughout the app. Take charge of your money and own your future — the return on investment is 100%. Oh, and I'll take a smash burger with sautéed jalapeños and a cup that's 90% seltzer water with a splash of Coke.
</div>
""", unsafe_allow_html=True)




