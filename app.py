# ════════════════════════════════════════════════════════════════════════════════
# F.I.R.E. for Effect — Military Financial Planning App
# ════════════════════════════════════════════════════════════════════════════════
# Architecture: Single-file Streamlit app. All state lives in st.session_state.
# Future: Refactor to multipage (pages/*.py) so session state persists across
#         tab navigation — this fixes the rank/TIS sync issues from single-file tabs.
# Data files required in same directory:
#   - military_data.json  (base pay, BAH rates, zip→MHA mapping)
# No external API calls — TSP returns use calibrated parametric proxy (see FUND_STATS).
# ════════════════════════════════════════════════════════════════════════════════
import streamlit as st
import json
import pandas as pd
import numpy as np
import altair as alt         # used for Sankey chart (Tab 3)
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import requests              # retained for future use; no active API calls currently
import io
import hashlib               # SHA-256 anonymous fingerprinting for analytics
import datetime
import gspread               # Google Sheets analytics logging
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
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "timestamp":
            sheet.append_row(["timestamp", "anon_id", "device_type", "event_type", "detail"])
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

def log_event(event_type, detail=""):
    """Fire-and-forget event logger. Each meaningful action writes one row."""
    try:
        sheet = get_gsheet()
        if sheet is None:
            return
        sheet.append_row([
            datetime.datetime.now().isoformat(),
            st.session_state.anon_id,
            st.session_state.device_type,
            event_type,
            str(detail)
        ])
    except Exception:
        pass

# ── Session State Initialization ─────────────────────────────────────────────
# All keys initialized here with defaults. Streamlit reruns the entire script on
# every widget interaction — session_state is the only thing that persists.
# Keys prefixed tab3_ are written by Tab 3 and read by Tab 7 (PDF/plan).
# Keys prefixed sim_ hold Monte Carlo results so the chart survives reruns.
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
if "fund_comparison_results" not in st.session_state: st.session_state.fund_comparison_results = None

# ── Analytics State ───────────────────────────────────────────────────────────
# Event-driven logging — each flag ensures a given event fires exactly once
# per session. log_event() writes one row per action to Google Sheets.
if "consent_given" not in st.session_state: st.session_state.consent_given = False
if "session_start" not in st.session_state: st.session_state.session_start = datetime.datetime.now()
if "anon_id" not in st.session_state: st.session_state.anon_id = get_anon_id()
if "device_type" not in st.session_state: st.session_state.device_type = get_device_type()
if "session_start_logged" not in st.session_state: st.session_state.session_start_logged = False
if "tabs_logged" not in st.session_state: st.session_state.tabs_logged = set()
if "budget_mode_logged" not in st.session_state: st.session_state.budget_mode_logged = False
if "monte_carlo_logged" not in st.session_state: st.session_state.monte_carlo_logged = False
if "fund_comparison_logged" not in st.session_state: st.session_state.fund_comparison_logged = False
if "pdf_logged" not in st.session_state: st.session_state.pdf_logged = False

# ── Consent / Analytics Gate ─────────────────────────────────────────────────
# App does not render until user accepts. consent_given persists in session_state
# so the gate doesn't re-appear on widget interactions within the same session.
# --- CONSENT SCREEN ---
if not st.session_state.consent_given:
    st.title("🎖️ F.I.R.E. for Effect")
    st.markdown("""
The military probably has the most complicated compensation system of any profession. Base pay, BAH, BAS, tax advantages, retirement systems, special pays — it's a lot.

But every service member should be able to answer three simple questions:

**What do I actually make? What do I need to save? Where is my money going?**

Surprisingly, there isn't a simple tool that pulls all of that together in one place.

So we're trying to build one.

The app asks for things like your rank, duty station ZIP code, and a few budget numbers so it can generate realistic estimates. None of that information leaves your device. There's no account, no database, and no way for us to connect anything back to you.

With your permission, we do collect a small amount of anonymous usage data — things like which sections people open, whether the simulations run, whether the PDF downloads, and whether anything breaks.

No names. No financial data. No personal information.

It simply helps us answer one question: is this tool actually useful — or do people close it after 15 seconds?
    """)

    st.markdown("""
<style>
div.stButton > button[kind="primary"] {
    background-color: #2dc653;
    border-color: #2dc653;
    color: white;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #25a244;
    border-color: #25a244;
    color: white;
}
</style>
""", unsafe_allow_html=True)

    if st.button("✅ Let's go.", type="primary", use_container_width=False):
        st.session_state.consent_given = True
        log_event("session_start")
        st.rerun()
    st.stop()

# ==========================================
# ════════════════════════════════════════════════════════════════════════════════
# MONTE CARLO HELPER FUNCTIONS
#
# FUND_STATS: single source of truth for all fund return assumptions.
#   geo_mean  = target CAGR (used by solver and blended return display)
#   mu        = annual arithmetic mean = monthly_geo + monthly_sigma^2/2
#               (not used directly — FUND_MONTHLY_PARAMS derives monthly values)
#   sigma     = annual standard deviation (annualized)
#   Source: tspfolio.com since-inception returns through 3/5/2026
#
# FUND_MONTHLY_PARAMS: derived from FUND_STATS at module load.
#   monthly_arith = monthly_geo + monthly_sigma^2/2
#   This correction (variance drag) ensures parametric MC median matches
#   the solver's deterministic projection over long horizons.
#
# run_real_monte_carlo: parametric approach — draws fresh Normal(mu,sigma) returns
#   per fund per month per trial. Eliminates pool-sampling seed bias that caused
#   S-fund to produce 8.6% success (vs expected ~55%) with a fixed seed.
#   L-fund weight is always passed as 0.0 — see note in Tab 2 alloc section.
#
# scrape_and_prep_tsp_data: previously fetched live data via yfinance API.
#   API removed — drift between live returns and FUND_STATS broke solver/MC
#   alignment. Now returns FUND_MONTHLY_PARAMS directly. Name retained for
#   call-site compatibility.
# ════════════════════════════════════════════════════════════════════════════════
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

# ════════════════════════════════════════════════════════════════════════════════
# 2. DATA UTILITIES
# get_base_pay / get_military_pay: look up pay tables from military_data.json
# build_monthly_base_pay_schedule: projects month-by-month income using promotion
#   timeline so the solver uses accurate income, not a static rank assumption.
# ════════════════════════════════════════════════════════════════════════════════
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

# ════════════════════════════════════════════════════════════════════════════════
# PROMOTION TIMELINE & SAVINGS RATE HELPERS
# PROMOTION_TIMELINE: Army primary-zone TIS thresholds by rank. Other services
#   are approximate. Does not model below-zone, above-zone, or stagnation.
# solve_savings_rate: binary search (60 iterations) over savings percentage.
#   Uses month-by-month gliding L-fund allocation to match MC exactly.
#   Signature: (target, current_tsp, base_pay_schedule, civilian_monthly,
#               mil_months, total_months, alloc_dict, inflation_rate)
# get_blended_nominal_return: weighted average of fund geo_means. Used for
#   display metrics (blended return label) and savings rate explorer chart.
#   NOTE: The solver does NOT use this — it uses per-fund monthly rates directly.
# ════════════════════════════════════════════════════════════════════════════════
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

# ── Tab Layout ────────────────────────────────────────────────────────────────
# All 7 tabs are rendered on every rerun — only the active tab is visible.
# This is the core limitation of single-file Streamlit. Widgets on inactive tabs
# still execute, which can cause unexpected state writes. Known issue; deferred
# to multipage refactor.
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "💰 What Do You Make?", "📈 How Much Do You Need to Save?", "💸 Where Does It Go?",
    "🎯 Know the Game", "✅ The Way Ahead", "📄 Your Plan", "📬 Feedback", "🏠 Rent vs. Buy"
])

# --- TAB 1: INCOME TRUTH ---
with tab1:
    if 1 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(1)
        log_event("tab_visited", 1)
    st.header("What You Make")

    col1, col2 = st.columns(2)
    with col1:
        rank = st.selectbox("Current Rank", CONFIG["ranks"], index=14, key="tab1_rank_widget")
        tis = st.number_input("Years of Service (TIS)", 0, 40, 0)
    with col2:
        zip_code = st.text_input("Duty Station Zip Code", "93943")
        dep = st.checkbox("With Dependents?", value=True)

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
    with col_monthly: st.info(f"### 🗓️ Monthly Gross\n# \\${gross:,.2f}")
    with col_annual: st.success(f"### 💰 Annual Gross\n# \\${annual_gross:,.2f}")

    st.write("")

    c_a, c_b, c_c, c_d = st.columns(4)
    c_a.metric("Base Pay",        f"${base:,.2f}")
    c_b.metric("BAH (Tax-Free)",  f"${bah:,.2f}")
    c_c.metric("BAS (Tax-Free)",  f"${bas:,.2f}")
    c_d.metric("Special Pays",    f"${special_pay:,.2f}")

    st.divider()
    st.subheader("Projected Annual Compensation by Year of Service")

    with st.expander("Model assumptions"):
        st.markdown("""
- Projection runs from your current **TIS** through **20 years of service**
- **BAH changes with projected rank**, using your current **duty-station ZIP** and dependent status
- **BAS** changes only if you cross between enlisted/officer/warrant categories
- **Special pays are held constant** at the values you entered above
- Promotion timing uses the app's built-in **typical promotion timeline**
- **Terminal rank caps:** Officers project to O-5, Warrant Officers to W-5, Enlisted to E-7 — ranks above those caps are not modeled in this projection
- This is an illustrative model, not a prediction of your exact career
        """)

    def get_projection_terminal_rank(start_rank):
        if start_rank in ["O-1E", "O-2E", "O-3E"]:
            return "O-4"
        if start_rank.startswith("O"):
            return "O-5"
        if start_rank.startswith("W"):
            return "W-5"
        return "E-7"

    def project_rank_by_tis(start_rank, tis_value):
        chain = get_progression_chain(start_rank)
        terminal_rank = get_projection_terminal_rank(start_rank)

        if terminal_rank not in chain:
            terminal_idx = len(chain) - 1
        else:
            terminal_idx = chain.index(terminal_rank)

        current_rank = chain[0]
        for r in chain[:terminal_idx + 1]:
            if tis_value >= PROMOTION_TIMELINE.get(r, 999):
                current_rank = r
            else:
                break
        return current_rank

    proj_start_tis = int(np.ceil(tis))
    proj_end_tis = 20

    # Fixed: was >= which hid the chart for anyone at exactly TIS 20
    if proj_start_tis > proj_end_tis:
        st.info("Projection chart is only shown for users below 20 years of service.")
    else:
        projection_rows = []

        for tis_year in range(proj_start_tis, proj_end_tis + 1):
            projected_rank = project_rank_by_tis(rank, tis_year)

            if st.session_state.bah_manual:
                proj_base = get_base_pay(projected_rank, tis_year)
                proj_bas = CONFIG["bas_officer"] if ("O" in projected_rank or "W" in projected_rank) else CONFIG["bas_enlisted"]
                proj_bah = bah
            else:
                proj_base, proj_bas, proj_bah = get_military_pay(
                    projected_rank,
                    tis_year,
                    zip_code,
                    dep
                )

            annual_base = proj_base * 12
            annual_bas = proj_bas * 12
            annual_bah = proj_bah * 12
            annual_special = special_pay * 12
            annual_total = annual_base + annual_bas + annual_bah + annual_special

            projection_rows.append({
                "TIS": tis_year,
                "Projected Rank": projected_rank,
                "Base Pay": annual_base,
                "BAS": annual_bas,
                "BAH": annual_bah,
                "Special Pays": annual_special,
                "Total Compensation": annual_total
            })

        proj_df = pd.DataFrame(projection_rows)

        # ── Color palette: taxable anchor → tax-free warm → bonus ────────────
        # Base Pay: solid steel blue (dominant — largest component, taxable)
        # BAH: amber/gold (tax-free housing — visually warm to signal advantage)
        # BAS: muted teal (tax-free subsistence — smaller, quieter)
        # Special Pays: bright accent only appears when non-zero
        COMP_COLORS = {
            "Base Pay":    "#4C9BE8",   # steel blue — dominant, taxable
            "BAH":         "#F0A500",   # amber gold — tax-free housing
            "BAS":         "#3ABFAB",   # teal — tax-free subsistence
            "Special Pays":"#E8654C",   # coral — bonus / accent only if present
        }

        # Build traces — skip Special Pays entirely if user has none
        has_special = proj_df["Special Pays"].sum() > 0
        components = ["Base Pay", "BAH", "BAS"]
        if has_special:
            components.append("Special Pays")

        fig_proj = go.Figure()

        for component in components:
            fig_proj.add_trace(go.Bar(
                x=proj_df["TIS"],
                y=proj_df[component],
                name=component,
                marker_color=COMP_COLORS[component],
                customdata=np.stack([
                    proj_df["Projected Rank"],
                    proj_df["Total Compensation"]
                ], axis=-1),
                hovertemplate=(
                    "<b>TIS %{x}  ·  %{customdata[0]}</b><br>"
                    f"{component}: $%{{y:,.0f}}<br>"
                    "Total: $%{customdata[1]:,.0f}"
                    "<extra></extra>"
                )
            ))

        # ── Promotion milestone annotations ──────────────────────────────────
        # Detect TIS years where rank changes and annotate directly on the chart
        # so the story of "why did comp jump?" is visible without hovering.
        prev_rank = proj_df["Projected Rank"].iloc[0]
        for _, row_data in proj_df.iterrows():
            cur_rank = row_data["Projected Rank"]
            if cur_rank != prev_rank:
                fig_proj.add_vline(
                    x=row_data["TIS"] - 0.5,
                    line_width=1.2,
                    line_dash="dot",
                    line_color="rgba(255,255,255,0.25)"
                )
                fig_proj.add_annotation(
                    x=row_data["TIS"],
                    y=row_data["Total Compensation"] * 1.04,
                    text=f"↑ {cur_rank}",
                    showarrow=False,
                    font=dict(size=10, color="#F0A500"),
                    xanchor="center"
                )
                prev_rank = cur_rank

        fig_proj.update_layout(
            barmode="stack",
            height=440,
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            font=dict(color="#fafafa", family="sans-serif"),
            margin=dict(l=60, r=20, t=20, b=50),
            xaxis=dict(
                title="Years of Service (TIS)",
                tickmode="linear",
                dtick=1,
                gridcolor="#1e2130",
                linecolor="#2a2a3e",
                tickfont=dict(size=11),
            ),
            yaxis=dict(
                title="Annual Compensation ($)",
                tickformat="$,.0f",
                gridcolor="#1e2130",
                linecolor="#2a2a3e",
            ),
            legend=dict(
                orientation="v",
                yanchor="bottom",
                y=0.04,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(14,17,23,0.7)",
                bordercolor="#2a2a3e",
                borderwidth=1,
                font=dict(size=11),
            ),
            bargap=0.18,
        )

        st.plotly_chart(fig_proj, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2: RETIREMENT SAVINGS RATE SOLVER
# Core logic: binary search finds the single % of base pay that, compounded at
# the blended real return over the full career, hits the nest egg target exactly.
# Inputs: rank, TIS, retirement assumptions, TSP allocation, inflation rate.
# Outputs: savings_pct (→ MyPay), contrib_schedule (→ MC sim), nest egg target.
# ════════════════════════════════════════════════════════════════════════════════
# --- TAB 2: RETIREMENT ---
with tab2:
    if 2 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(2)
        log_event("tab_visited", 2)
    st.header("Retirement & Pension Target")
    st.info(
        "💡 **Why doesn't every financial app do this?** Because calculating a single savings rate that actually works "
        "requires assumptions — about promotion timelines, fund returns, inflation, and your post-military income. "
        "Most tools skip it because the assumptions make them uncomfortable. This one doesn't. "
        "Every assumption baked into this model is documented in the **📋 Model Assumptions** expander at the bottom of this tab. "
        "They are all intentionally conservative — the goal is to make sure you *hit* your targets, not just feel good about the math."
    )

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
                      help="Actuarially expected payment duration: or how long after you retire from military until you're dead 💀, probablistically.")

            pd2, pe = st.columns(2)
            pd2.metric(
                "Pension Value Using SWR-Estimatation",
                f"${swr_value:,.0f}",
                help="How much you'd need in savings to replace this pension at a 4% withdrawal rate."
            )
            pe.metric(
                "Pension Value Using Life Expectancy-Estimatation",
                f"${apv_value:,.0f}",
                delta=f"${swr_value - apv_value:+,.0f} vs SWR",
                delta_color="inverse",
                help="Based on SSA 2022 life tables, 2.5% discount rate. The 'true' financial value of the pension accounting for mortality risk."
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

    # ── Fund allocation: user enters C/S/I/F; G auto-fills as remainder ─────────
    # NOTE: L-fund is intentionally excluded from manual allocation.
    # The L-fund glide path cannot be modeled accurately in the parametric MC
    # (it inflates success rates because the lifecycle assumptions don't match
    # the parametric Normal(mu,sigma) draws used per-fund). G absorbs the remainder
    # so allocations always sum to 100% without user friction.
    with alloc_col:
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        pct_c = fc1.number_input(
            f"C-Fund\n{rc:+.1f}% real",
            min_value=0, max_value=100, value=0, step=5,
            help="Large-cap U.S. stocks (S&P 500 index). Highest long-term growth, highest short-term swings."
        )
        pct_s = fc2.number_input(
            f"S-Fund\n{rs:+.1f}% real",
            min_value=0, max_value=100, value=0, step=5,
            help="Small/mid-cap U.S. stocks. Higher potential, higher volatility than C Fund."
        )
        pct_i = fc3.number_input(
            f"I-Fund\n{ri:+.1f}% real",
            min_value=0, max_value=100, value=0, step=5,
            help="International stocks. Diversification outside the U.S. market."
        )
        pct_f = fc4.number_input(
            f"F-Fund\n{rf:+.1f}% real",
            min_value=0, max_value=100, value=0, step=5,
            help="U.S. bond index. Stabilizes your portfolio but lower long-term growth."
        )
        # G-fund is the auto-computed remainder — always makes total = 100%
        manual_sum_no_g = pct_c + pct_s + pct_i + pct_f
        pct_g = max(0, 100 - manual_sum_no_g)
        fc5.metric(
            f"G-Fund (auto)\n{rg:+.1f}% real",
            f"{pct_g}%",
            delta="Remainder" if pct_g > 0 else "Fully allocated",
            delta_color="normal" if pct_g > 0 else "off",
            help="Government securities. Remainder after C+S+I+F — always keeps total at 100%."
        )
        manual_sum = manual_sum_no_g + pct_g  # always 100 unless over-allocated

    # Validate: C+S+I+F cannot exceed 100 (G would go negative)
    if manual_sum_no_g > 100:
        st.error(f"⚠️ Over-allocated by {manual_sum_no_g - 100}% — C+S+I+F cannot exceed 100%. G-Fund floored at 0%.")
        allocation_valid = False
    else:
        alloc_display = f"C:{pct_c}% | S:{pct_s}% | I:{pct_i}% | F:{pct_f}% | G:{pct_g}%"
        st.success(f"✅ Allocation: {alloc_display}")
        allocation_valid = True

    # alloc_dict feeds the solver. No L key — L-fund removed entirely.
    alloc_dict = {
        'C': pct_c / 100, 'S': pct_s / 100, 'I': pct_i / 100,
        'F': pct_f / 100, 'G': pct_g / 100, 'L': 0.0,
    }
    # mc_manual_alloc is what the parametric MC uses — pure 5-fund allocation, no L-fund.
    mc_manual_alloc = {'C': pct_c/100, 'S': pct_s/100, 'I': pct_i/100, 'F': pct_f/100, 'G': pct_g/100}
    # NOTE: use_lc is now always False. L-fund glide path is excluded from MC.
    # Kept as a variable for clarity in the MC call below — do not re-enable without
    # rebuilding the MC to properly handle the lifecycle blend.
    use_lc = False

    # ── Fund Comparison: What $500/month looks like across all funds ──────────
    # Hardcoded educational visualization — ages 25–75, $500/mo, $0 starting.
    # Runs once on first render and caches in session_state. Not tied to user inputs.
    with st.expander("📊 Not sure which fund to pick? See what $500/month looks like across all funds →"):
        st.markdown(
            "This chart shows what a consistent **\\$500/month contribution starting at age 25** "
            "looks like across each TSP fund through age 75 — using 1,000 simulated market scenarios per fund. "
            "The solid line is the median outcome. The shaded band is the 10th–90th percentile range — "
            "the spread is the risk. "
            "**Click a fund in the legend to hide it. Double-click to isolate one.**"
        )

        if st.session_state.fund_comparison_results is None:
            with st.spinner("Generating fund comparison..."):
                _COMP_MONTHLY  = 500.0
                _COMP_MONTHS   = 600          # ages 25–75
                _COMP_TRIALS   = 1000
                _FUNDS         = ['C', 'S', 'I', 'F', 'G']
                _comp = {}
                for _f in _FUNDS:
                    _mu, _sig = FUND_MONTHLY_PARAMS[_f]
                    _res = np.zeros((_COMP_TRIALS, _COMP_MONTHS + 1))
                    for _t in range(_COMP_TRIALS):
                        _bal  = 0.0
                        _rets = np.random.normal(_mu, _sig, _COMP_MONTHS)
                        for _i in range(_COMP_MONTHS):
                            _bal = _bal * (1 + _rets[_i]) + _COMP_MONTHLY
                            _res[_t, _i + 1] = _bal
                    _comp[_f] = _res
                st.session_state.fund_comparison_results = _comp
                if not st.session_state.fund_comparison_logged:
                    st.session_state.fund_comparison_logged = True
                    log_event("fund_comparison_viewed")

        _comp_res = st.session_state.fund_comparison_results
        _ages     = np.linspace(25, 75, 601)

        # Age marker slider — drives the vertical line and per-fund annotations
        _marker_age = st.slider(
            "Marker age", min_value=30, max_value=75, value=65, step=1,
            key="fund_cmp_marker_age",
            help="Drag to move the reference line and update the balance annotations."
        )
        _marker_i = int((_marker_age - 25) * 12)   # index into the 601-point array

        _COLORS = {
            'C': '#00b4d8',
            'S': '#06d6a0',
            'I': '#ffd166',
            'F': '#ff9f1c',
            'G': '#b5838d',
        }
        _LABELS = {
            'C': 'C-Fund',
            'S': 'S-Fund',
            'I': 'I-Fund',
            'F': 'F-Fund',
            'G': 'G-Fund',
        }

        def _hex_rgba(hx, a):
            h = hx.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"rgba({r},{g},{b},{a})"

        fig_cmp = go.Figure()

        for _f in ['C', 'S', 'I', 'F', 'G']:
            _res  = _comp_res[_f]
            _col  = _COLORS[_f]
            _lbl  = _LABELS[_f]
            _p10  = np.percentile(_res, 10, axis=0)
            _p50  = np.percentile(_res, 50, axis=0)
            _p90  = np.percentile(_res, 90, axis=0)

            # Upper band edge (invisible line, anchors the fill)
            fig_cmp.add_trace(go.Scatter(
                x=_ages, y=_p90,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                legendgroup=_f,
            ))
            # Lower band edge + fill to upper
            fig_cmp.add_trace(go.Scatter(
                x=_ages, y=_p10,
                mode='lines',
                fill='tonexty',
                fillcolor=_hex_rgba(_col, 0.12),
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                legendgroup=_f,
            ))
            # Median line — this is the legend entry that toggles the whole group
            fig_cmp.add_trace(go.Scatter(
                x=_ages, y=_p50,
                mode='lines',
                name=_lbl,
                line=dict(color=_col, width=2.5),
                hoverinfo='skip',
                legendgroup=_f,
                legendgrouptitle_text=None,
            ))
            # Marker-age annotation — updates with slider
            _med_at_marker = _p50[_marker_i]
            _marker_label  = f"${_med_at_marker/1e6:.2f}M" if _med_at_marker >= 1e6 else f"${_med_at_marker:,.0f}"
            fig_cmp.add_annotation(
                x=_marker_age, y=_med_at_marker,
                text=_marker_label,
                showarrow=False,
                font=dict(color=_col, size=9),
                bgcolor="rgba(14,17,23,0.75)",
                borderpad=2,
                xanchor='left',
                xshift=6,
            )

        # $1M target line
        fig_cmp.add_hline(
            y=1_000_000,
            line_dash="dash",
            line_color="#2dc653",
            line_width=1.5,
            annotation_text="  $1,000,000",
            annotation_position="top left",
            annotation_font_color="#2dc653",
            annotation_font_size=10,
        )
        # Vertical marker line — moves with slider
        fig_cmp.add_vline(
            x=_marker_age,
            line_dash="dot",
            line_color="#888899",
            line_width=1.2,
        )

        fig_cmp.update_layout(
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font=dict(color='#fafafa'),
            height=520,
            hovermode=False,
            margin=dict(l=60, r=40, t=20, b=60),
            xaxis=dict(
                title='Age',
                range=[25, 75],
                gridcolor='#2a2a3e',
                zerolinecolor='#2a2a3e',
                dtick=5,
            ),
            yaxis=dict(
                title='Portfolio Value',
                gridcolor='#2a2a3e',
                zerolinecolor='#2a2a3e',
                tickformat='$,.0f',
            ),
            legend=dict(
                bgcolor='rgba(14,17,23,0.85)',
                bordercolor='#2a2a3e',
                borderwidth=1,
                font=dict(color='#fafafa'),
                orientation='h',
                yanchor='bottom',
                y=1.01,
                xanchor='left',
                x=0,
            ),
        )

        st.plotly_chart(fig_cmp, use_container_width=True)
        st.caption(
            "**\\$500/month from age 25 · \\$0 starting balance · nominal returns · 1,000 trials per fund.** "
            "Solid line = median. Shaded band = 10th–90th percentile range. "
            "Annotations show median value at the marker age. "
            "Funds are modeled independently — real portfolios mix them."
        )

        st.divider()
        st.markdown("#### Still not sure? Three things worth knowing.")
        st.markdown("""
**The cost of waiting**

Good enough, funded today, beats perfect, funded someday. Every month you spend deciding is a month of compounding you don't get back. Pick something reasonable and start. You can always adjust later — you can't recover time.

[Does Market Timing Work? — Schwab](https://www.schwab.com/learn/story/does-market-timing-work)

---

**Your behavior is the variable**

The best allocation in the world doesn't survive a panic-sell during a 30% dip. What you pick matters less than whether you can watch your balance get cut in half and do absolutely nothing. That's the actual skill.

[The Behavior Gap — Carl Richards](https://behaviorgap.com)

---

**The best investors aren't watching**

Fidelity reportedly found their highest-performing accounts belonged to people who forgot they had them. True or not, the point holds: the urge to tinker is the enemy. Set it. Ignore it. Let it compound.

[Are the Best Investors Dead? — Meridian Financial](https://meridianfinancialadvisors.com/are-the-best-investors-dead/)
        """)

    # Blended nominal & real return
    expected_nom       = get_blended_nominal_return(alloc_dict, years_to_grow)
    expected_real_rate = ((1 + expected_nom) / (1 + inflation_rate)) - 1

    # ── Solver & results ──────────────────────────────────────────────────────
    if years_to_grow > 0 and allocation_valid:
        monthly_income_gap   = max(0, monthly_goal - est_pension)
        total_nest_egg_needed = (monthly_income_gap * 12) / 0.04

        # Build projected base pay schedule for military phase
        base_pay_schedule = build_monthly_base_pay_schedule(start_rank, start_tis, min(mil_months, total_months))

        # Binary search solver: returns (savings_pct, monthly_contrib_schedule)
        # savings_pct = % of base pay to save each month during military phase
        # contrib_schedule = list of dollar amounts per month (military + civilian phases)
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
                    f"**You are currently saving {current_tsp_pct:.1f}% of your base pay (\\${les_tsp:,.2f}/month) toward TSP.** "
                    f"To meet your financial goals, you need to increase your contributions to "
                    f"**{savings_pct * 100:.1f}%** — an increase of **{gap_pct:.1f} percentage points "
                    f"(\\${gap_dollars:,.2f}/month)**. You can make this adjustment now in "
                    f"[MyPay](https://mypay.dfas.mil)."
                )
            elif gap_pct < -0.5:
                st.success(
                    f"**You are currently saving {current_tsp_pct:.1f}% of your base pay (\\${les_tsp:,.2f}/month) toward TSP** — "
                    f"**\\${abs(gap_dollars):,.2f}/month more than your goal requires.** "
                    f"That surplus increases the odds of hitting your goal, reduces the years you need to save until retirement, "
                    f"and increases the amount you'll have in retirement. However, if there's another priority, "
                    f"you are already expected to meet your retirement goals — this surplus could be considered "
                    f"additional guilt-free spending. Congrats! 🎉"
                )
            else:
                st.success(
                    f"**You are currently saving {current_tsp_pct:.1f}% of your base pay (\\${les_tsp:,.2f}/month) toward TSP** — "
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

        with st.expander("💡 Most apps give you a chart. Why does this give you a % to set in MyPay?"):
            st.write(
                "Most calculators won't commit to a number because doing it right requires assumptions — "
                "about promotion timelines, fund returns, inflation, and your post-military income. "
                "Making those assumptions feels risky, so most tools hand you a chart and leave the hard part to you. "
                "\n\n"
                "The problem is that without financial expertise, defining those assumptions yourself is genuinely difficult. "
                "The learning curve is steep, the material is dense, and most people don't have time to become experts "
                "just to answer the question: *am I saving enough?*"
                "\n\n"
                "This calculator takes your inputs, applies conservative assumptions, and does the math for you — "
                f"outputting a single, actionable percentage you can set in MyPay today. "
                "Every assumption is documented in the **📋 Model Assumptions** expander at the bottom of this tab."
            )

        # ── TSP Ceiling / Overflow Cascade ───────────────────────────────────
        # 2026 IRS limits: TSP employee $24,500/yr; catch-up (50+) $31,000/yr; IRA $7,000/yr
        _TSP_ANNUAL      = 31000 if current_age >= 50 else 24500
        _TSP_MONTHLY_MAX = _TSP_ANNUAL / 12
        _IRA_MONTHLY_MAX = 7000 / 12          # per person

        if current_base > 0 and monthly_dollar_equiv > _TSP_MONTHLY_MAX:
            _mypay_pct   = (_TSP_MONTHLY_MAX / current_base) * 100
            _overflow    = monthly_dollar_equiv - _TSP_MONTHLY_MAX

            # Build the cascade message
            _cascade_lines = [
                f"**This is a good problem to have — you've leveled up.**\n\n"
                f"Your required savings of **\\${monthly_dollar_equiv:,.0f}/month** exceeds "
                f"the {'catch-up ' if current_age >= 50 else ''}TSP contribution limit "
                f"(**\\${_TSP_MONTHLY_MAX:,.0f}/month** in 2026). "
                f"Here's where each dollar goes:\n"
            ]

            _remaining = _overflow
            _step = 1

            _cascade_lines.append(
                f"**{_step}. Set MyPay to {_mypay_pct:.1f}% of base pay** "
                f"→ maxes your TSP at **\\${_TSP_MONTHLY_MAX:,.0f}/month** "
                f"({'\\$31,000' if current_age >= 50 else '\\$24,500'}/yr). "
                f"[Log in to MyPay](https://mypay.dfas.mil)"
            )
            _step += 1

            if _remaining > 0:
                _ira_contrib = min(_remaining, _IRA_MONTHLY_MAX)
                _remaining  -= _ira_contrib
                _cascade_lines.append(
                    f"**{_step}. Contribute \\${_ira_contrib:,.0f}/month to your IRA** "
                    f"→ \\${_ira_contrib * 12:,.0f}/yr "
                    f"({'maxed' if _ira_contrib >= _IRA_MONTHLY_MAX - 0.5 else f'of \\${_IRA_MONTHLY_MAX*12:,.0f} allowed'}). "
                    f"[IRA overview](https://www.investopedia.com/terms/i/ira.asp)"
                )
                _step += 1

            if _remaining > 0:
                _sp_ira_contrib = min(_remaining, _IRA_MONTHLY_MAX)
                _remaining     -= _sp_ira_contrib
                _cascade_lines.append(
                    f"**{_step}. Contribute \\${_sp_ira_contrib:,.0f}/month to a spouse IRA** "
                    f"→ \\${_sp_ira_contrib * 12:,.0f}/yr "
                    f"({'maxed' if _sp_ira_contrib >= _IRA_MONTHLY_MAX - 0.5 else f'of \\${_IRA_MONTHLY_MAX*12:,.0f} allowed'})."
                )
                _step += 1

            if _remaining > 0.50:
                _cascade_lines.append(
                    f"**{_step}. Invest the remaining \\${_remaining:,.0f}/month in a taxable brokerage account.** "
                    f"No contribution limits. Low-cost index funds work the same way here. "
                    f"[Taxable brokerage overview](https://www.investopedia.com/terms/b/brokerageaccount.asp)"
                )

            st.success("\n\n".join(_cascade_lines))

            if current_age >= 50:
                st.caption(
                    "Catch-up contribution limit applied (age 50+): $31,000/yr TSP employee limit for 2026. "
                    "[IRS TSP limits](https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-contributions)"
                )
            else:
                st.caption(
                    "At age 50 your TSP limit increases to $31,000/yr. "
                    "[IRS TSP limits](https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-contributions)"
                )

        # ── Interactive Savings Rate Explorer ────────────────────────────────
        st.divider()
        with st.expander("🎯 Want to see how your savings rate affects your timeline? → Savings Rate Explorer"):
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

        # ── Luck & Timing Roulette (Parametric Monte Carlo) ──────────────────────
        # Draws fresh Normal(mu, sigma) returns each trial — no pool sampling.
        # This ensures MC median converges to solver projection regardless of seed.
        # L-fund excluded: lifecycle glide path inflates success rates when modeled
        # with static parametric distributions. G-fund absorbs the allocation gap.
        # Results stored in session_state so chart survives widget reruns.
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
            if not st.session_state.monte_carlo_logged:
                st.session_state.monte_carlo_logged = True
                log_event("monte_carlo_run")
            with st.spinner("Running 1,000 trials..."):
                hist_returns, data_source = scrape_and_prep_tsp_data()
                # l_fund_weight=0.0 — L-fund removed from MC. See note above alloc_dict.
                sim_results = run_real_monte_carlo(
                    current_age, age_at_retire, current_tsp,
                    contrib_schedule, hist_returns,
                    0.0, mc_manual_alloc,
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

        **Actuarial Pension Value (APV)**

        Discounts the lifetime pension stream to a single present value. Uses a **2.5% real discount rate** and **SSA Period Life Tables** (2020) to model survival probability by age and sex. This produces a conservative lump-sum equivalent — useful for comparing pension value to a TSP balance side-by-side.
        """)
# ════════════════════════════════════════════════════════════════════════════════
# TAB 3: CONSCIOUS SPENDING / BUDGET
# Two paths: LES entry (accurate, pulls real deductions) or skip (estimate only).
# Key outputs written to session_state for Tab 7 PDF:
#   tab3_take_home, tab3_fixed, tab3_invested, tab3_guilt_free
# Tax estimates are rough — BAH/BAS excluded from taxable income per law.
# les_tsp_actual is read by Tab 2 to show the TSP gap callout.
# ════════════════════════════════════════════════════════════════════════════════
# --- TAB 3: CONSCIOUS SPENDING ---
with tab3:
    if 3 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(3)
        log_event("tab_visited", 3)
    st.header("Where Does It Go?")

    special_pay = st.session_state.get("special_pay", 0.0)

    pay_mode = st.radio(
        "Income Mode",
        [
            "📋 Using my LES values below",
            "🎲 I'll skip the LES and let an algorithm guess my take-home pay—even though it knows nothing about my deductions, allotments, or tax situation. Honestly, it'll fit right in with the rest of my planning: assumptions, hopes, and vibes."
        ],
        key="pay_mode_radio"
    )

    if not st.session_state.budget_mode_logged:
        st.session_state.budget_mode_logged = True
        log_event("budget_mode", "LES" if "📋" in pay_mode else "manual")

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
            calc_values = ", ".join([
                f.split("calculator: ")[1].rstrip(")").replace("$", "\\$")
                for f in mismatch_fields
            ])
            st.warning(
                f"The value you entered for **{field_names}** does not match the calculated value ({calc_values}). "
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
        st.metric("💰 Monthly Take-Home", f"${mil_takehome:,.2f}")

    # ── LES fallback ──────────────────────────────────────────────────────────
    if "📋" not in pay_mode:
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
        st.caption(f"*Estimated Taxes: Federal **\\${monthly_fed_tax:,.0f}** | FICA **\\${monthly_fica:,.0f}** — BAH/BAS excluded from tax. Your actual deductions will differ.*")
        with st.expander("📋 Tax Estimate Assumptions"):
            st.markdown("""
- **Filing status:** Single (most conservative — married filing jointly would lower your tax bill)
- **Standard deduction:** $15,000 (2025)
- **Federal brackets applied:** 10% · 12% · 22% · 24% on taxable income above each threshold
- **BAH and BAS are excluded from taxable income** per federal law — only base pay and special pays are taxed
- **FICA:** Flat 7.65% on taxable monthly income (6.2% Social Security + 1.45% Medicare)
- **State taxes not modeled** — several states exempt military pay entirely; your actual state liability will vary
- These are rough estimates. Your LES deductions tab gives you exact numbers.
            """)
    else:
        take_home = mil_takehome + total_extra_income

    st.info(f"💰 Total Combined Monthly Take-Home: **\\${take_home:,.2f}**")
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
            st.success(f"**Remaining to allocate: \\${remaining:,.2f}**")
        elif remaining >= -0.005:
            st.success("**Fully allocated. Nothing left on the table. ✅**")
        else:
            st.error(f"**Over-allocated by \\${abs(remaining):,.2f} — trim a category above.**")

        st.metric("Guilt-Free Total", f"${fun_total:,.2f}", f"{fun_pct:.1f}% of take-home")

        with st.expander("🤔 Can't figure out where your money is actually going?"):
            st.markdown("""
If you filled this out and still felt like you were guessing — or you know your numbers don't add up but can't find the leak — a dedicated budgeting app can help you connect real transactions to real categories and surface the blind spots.

**Three worth your time:**

**[Copilot](https://copilot.money)** — Best-in-class transaction intelligence. Automatically categorizes spending with high accuracy and lets you customize rules. Strong on the "where did it actually go?" question. Apple only.

**[Monarch Money](https://monarchmoney.com)** — The most complete picture: budgets, net worth, investments, and goals in one place. Works on all platforms. Best for people who want everything in one dashboard.

**[YNAB (You Need A Budget)](https://ynab.com)** — Built around giving every dollar a job before you spend it. Steeper learning curve, but it's the gold standard for people who want to actively control spending rather than just track it.
            """)

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

    if surplus_amt < -5: st.error(f"⚠️ **Budget Deficit:** You are over-allocated by **\\${abs(surplus_amt):,.2f}**.")
    elif surplus_amt > 5: st.success(f"✅ **Budget Surplus:** You have **\\${surplus_amt:,.2f}** unallocated.")

# --- TAB 4: KNOW THE SYSTEM ---
with tab4:
    if 4 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(4)
        log_event("tab_visited", 4)
    st.header("Know the System")
    st.write(
        "Most of this stuff isn't complicated. But a lot of it isn't obvious until someone points it out. "
        "Some questions have clear answers. Some are just prompts to think about how you use money. "
        "Take what's useful and ignore the rest."
    )

    # -----------------------------
    # Debt & Interest
    # -----------------------------
    with st.expander("💳 Debt & Interest"):
        st.markdown("**Money grows in both directions.**")
        st.markdown("Know which direction yours is going.")
        st.caption("Question 1 of 4")

        debt_q1 = st.radio(
            "If you have debt with an interest rate above about **8%**, what is generally the smarter financial move?",
            [
                "Invest instead",
                "Pay off the debt first",
                "Ignore it",
                "Take on more debt",
            ],
            index=None,
            key="debt_q1",
        )
        if debt_q1:
            st.info(
                "High-interest debt grows faster than most investments.\n\n"
                "If your debt is above roughly **8%**, the smarter move is usually to eliminate that debt before investing.\n\n"
                "Investing while carrying expensive debt is like trying to fill a bucket with a hole in the bottom."
            )

        st.divider()
        st.caption("Question 2 of 4")

        debt_q2 = st.radio(
            "Which strategy mathematically minimizes the total interest you pay?",
            [
                "Pay off the smallest balance first",
                "Pay off the highest interest rate first",
                "Pay minimum payments forever",
                "Consolidate everything immediately",
            ],
            index=None,
            key="debt_q2",
        )
        if debt_q2:
            if debt_q2 == "Pay off the highest interest rate first":
                st.info(
                    "Paying the **highest interest rate first** is called the **Debt Avalanche**.\n\n"
                    "It's the mathematically optimal strategy because it minimizes how much interest you pay over time.\n\n"
                    "Learn more: [Debt Avalanche](https://www.investopedia.com/terms/d/debt-avalanche.asp)"
                )
            elif debt_q2 == "Pay off the smallest balance first":
                st.info(
                    "While not mathematically optimal, paying the smallest balance first is called the **Debt Snowball**.\n\n"
                    "You'll end up paying a little more to the credit card company, but knocking out debts early can build momentum when you're trying to get out from under debt.\n\n"
                    "Learn more: [Debt Snowball](https://www.investopedia.com/articles/personal-finance/080716/debt-avalanche-vs-debt-snowball-which-best-you.asp)"
                )
            else:
                st.info(
                    "The strategy that saves the most money is paying the **highest interest rate first**.\n\n"
                    "That approach is called the **Debt Avalanche**. Paying the smallest balance first is the **Debt Snowball**.\n\n"
                    "Learn more: [Debt Avalanche vs Debt Snowball](https://www.investopedia.com/articles/personal-finance/080716/debt-avalanche-vs-debt-snowball-which-best-you.asp)"
                )

        st.divider()
        st.caption("Question 3 of 4")

        debt_q3 = st.radio(
            "If your credit utilization is **80%**, what does that mean?",
            [
                "80% of your cards are paid off",
                "You are using 80% of your available credit",
                "Your credit score is excellent",
                "Your credit report is 80% positive",
            ],
            index=None,
            key="debt_q3",
        )
        if debt_q3:
            st.info(
                "Credit utilization is the percentage of available credit you're using.\n\n"
                "High utilization can **significantly lower your credit score**, even if you make payments on time.\n\n"
                "For monitoring: **[AnnualCreditReport.com](https://www.annualcreditreport.com)** gives you your actual credit reports from all three bureaus — Equifax, TransUnion, and Experian — and is the legally mandated free source. "
                "Services like **[Credit Karma](https://www.creditkarma.com)** provide estimated scores and summarized data, which is useful for regular monitoring, "
                "but may not catch every item on your full reports. YMMV — check the actual reports periodically to make sure nothing has been missed."
            )

        st.divider()
        st.caption("Question 4 of 4")

        debt_q4 = st.radio(
            "Under the **Servicemembers Civil Relief Act (SCRA)**, interest rates on pre-service debt are capped at:",
            [
                "4%",
                "6%",
                "8%",
                "10%",
            ],
            index=None,
            key="debt_q4",
        )
        if debt_q4:
            st.info(
                "If you had debt **before entering active duty**, lenders must cap the interest rate at **6%**.\n\n"
                "If you've already paid interest above that rate, the lender must **refund the difference**.\n\n"
                "Learn more: [SCRA Overview](https://www.justice.gov/servicemembers)"
            )

    # -----------------------------
    # Emergency Fund
    # -----------------------------
    with st.expander("🛟 Emergency Fund"):
        st.markdown("**Unexpected expenses are expected.**")
        st.markdown("Don't let them steal your progress.")
        st.caption("Question 1 of 5")

        emergency_q1 = st.radio(
            "What is an emergency fund designed for?",
            [
                "Vacations",
                "Investment opportunities",
                "Unexpected expenses",
                "Shopping",
            ],
            index=None,
            key="emergency_q1",
        )
        if emergency_q1:
            st.info(
                "Emergencies covered with credit cards can quietly derail financial plans.\n\n"
                "They seem small at first, but they often create debt that takes months or years to unwind.\n\n"
                "An emergency fund protects the progress you're making.\n\n"
                "Learn more: [Emergency Fund Basics](https://www.consumerfinance.gov/consumer-tools/savings-goals/)"
            )

        st.divider()
        st.caption("Question 2 of 5")

        emergency_q2 = st.radio(
            "What is a common target for a fully funded emergency fund?",
            [
                "$500",
                "One paycheck",
                "3–6 months of living expenses",
                "$50,000",
            ],
            index=None,
            key="emergency_q2",
        )
        if emergency_q2:
            st.info(
                "A common target is **3–6 months of essential expenses**.\n\n"
                "The goal is to have enough cash to absorb major disruptions like job transitions, medical expenses, or unexpected repairs.\n\n"
                "Learn more: [Emergency Savings](https://www.militaryonesource.mil/financial-legal/personal-finance/building-emergency-savings/)"
            )

        st.divider()
        st.caption("Question 3 of 5")

        emergency_q3 = st.radio(
            "Where is the best place to store an emergency fund?",
            [
                "Checking account",
                "Stock market",
                "High-yield savings account",
                "Cryptocurrency",
            ],
            index=None,
            key="emergency_q3",
        )
        if emergency_q3:
            st.info(
                "Emergency funds should be **safe, liquid, and easily accessible**.\n\n"
                "A **high-yield savings account (HYSA)** provides liquidity while still earning interest.\n\n"
                "Learn more: [High-Yield Savings Account](https://www.investopedia.com/personal-finance/high-yield-savings-account/)"
            )

        st.divider()
        st.caption("Question 4 of 5")

        emergency_q4 = st.radio(
            "Where is your emergency fund currently stored?",
            [
                "I don't have one",
                "Checking account",
                "Cash at home",
                "Credit cards are my emergency plan",
                "High-yield savings account",
            ],
            index=None,
            key="emergency_q4",
        )
        if emergency_q4:
            st.info(
                "If emergencies are being covered with credit cards, it often slows financial progress dramatically.\n\n"
                "A HYSA is usually a better default than checking because it keeps the money accessible while earning something."
            )

        st.divider()
        st.caption("Question 5 of 5")

        emergency_q5 = st.radio(
            "Your car suddenly needs a **$600 repair today**. What do you do?",
            [
                "Put it on a credit card and pay it off slowly",
                "Pay with emergency savings",
                "Ignore it",
                "Hope insurance covers it",
            ],
            index=None,
            key="emergency_q5",
        )
        if emergency_q5:
            st.info(
                "Unexpected expenses happen regularly. The goal is to absorb them **without creating new debt**."
            )

    # -----------------------------
    # Budgeting
    # -----------------------------
    with st.expander("🧭 Budgeting"):
        st.markdown("**Money needs direction.**")
        st.markdown("Give it one.")
        st.caption("Question 1 of 5")

        budget_q1 = st.radio(
            "What is the real purpose of a budget?",
            [
                "Restrict spending",
                "Track where money goes",
                "Eliminate fun purchases",
                "Impress financial planners",
            ],
            index=None,
            key="budget_q1",
        )
        if budget_q1:
            st.info(
                "A budget is simply understanding where your money is going so you can decide whether that aligns with what you actually care about."
            )

        st.divider()
        st.caption("Question 2 of 5")

        budget_q2 = st.radio(
            "What is the easiest way to save consistently?",
            [
                "Track spending daily",
                "Invest when markets look good",
                "Automatically invest a percentage of each paycheck",
                "Save what's left at the end of the month",
            ],
            index=None,
            key="budget_q2",
        )
        if budget_q2:
            st.info(
                "Automation beats motivation.\n\n"
                "When investing happens automatically, it stops depending on willpower."
            )

        st.divider()
        st.caption("Question 3 of 5")

        budget_q3 = st.radio(
            "Which approach tends to create the most satisfaction over time?",
            [
                "Minimize all spending",
                "Spend randomly",
                "Spend freely on things you love and cut the rest",
                "Track every dollar forever",
            ],
            index=None,
            key="budget_q3",
        )
        if budget_q3:
            st.info(
                "The goal isn't to spend less.\n\n"
                "It's to spend intentionally on things that actually improve your life."
            )

        st.divider()
        st.caption("Question 4 of 5")

        budget_q4_joy = st.multiselect(
            "Which spending categories bring you the most enjoyment? Select 1–2.",
            [
                "Travel",
                "Eating out",
                "Hobbies",
                "Home improvements",
                "Subscriptions",
                "Cooking",
                "Convenience services",
            ],
            key="budget_q4_joy",
        )
        budget_q4_dontcare = st.multiselect(
            "Which of these do you spend money on **but don't actually care about much?**",
            [
                "Travel",
                "Eating out",
                "Hobbies",
                "Home improvements",
                "Subscriptions",
                "Cooking",
                "Convenience services",
            ],
            key="budget_q4_dontcare",
        )
        if budget_q4_joy or budget_q4_dontcare:
            st.info(
                "Most people don't regret spending money on things they love.\n\n"
                "They regret spending money on things they barely notice."
            )

        st.divider()
        st.caption("Question 5 of 5")

        budget_q5 = st.radio(
            "Which category do many households underestimate or overspend on?",
            [
                "Utilities",
                "Insurance",
                "Dining out",
                "Taxes",
            ],
            index=None,
            key="budget_q5",
        )
        if budget_q5:
            st.info(
                "Dining out is one of the most common areas where spending grows quietly over time.\n\n"
                "The goal isn't to eliminate it — just make sure it's something you actually value."
            )

        st.divider()
        st.markdown(
            "If you're interested in rethinking your spending habits, these people write about this far more thoughtfully than I do:\n\n"
            "- [Ramit Sethi](https://www.iwillteachyoutoberich.com)\n"
            "- [Vicki Robin — Your Money or Your Life](https://yourmoneyoryourlife.com)\n"
            "- [Paula Pant — Afford Anything](https://affordanything.com)\n"
            "- [Morgan Housel — Psychology of Money](https://www.collaborativefund.com/blog/authors/morgan-housel/)"
        )

    # -----------------------------
    # Investing & TSP
    # -----------------------------
    with st.expander("📈 Investing & TSP"):
        st.markdown("**Time does most of the work.**")
        st.markdown("Consistency makes it matter.")
        st.caption("Question 1 of 5")

        invest_q1 = st.radio(
            "If you're in the **Blended Retirement System**, what is the minimum TSP contribution needed to maximize your government match?",
            [
                "3%",
                "4%",
                "5%",
                "10%",
            ],
            index=None,
            key="invest_q1",
        )
        if invest_q1:
            st.info(
                "Contributing **5% of your base pay** captures the full government match.\n\n"
                "Here's how the BRS match works:\n"
                "- DoD automatically contributes **1%** regardless of what you put in\n"
                "- They match **dollar-for-dollar on your first 3%**\n"
                "- They match **50 cents per dollar on your next 2%**\n\n"
                "At 5% from you, the government adds **5% more** — for a total of **10% of base pay** going into your TSP every month. "
                "Anything you contribute above 5% is still good — it just doesn't earn additional matching.\n\n"
                "Examples of annual government match at 5% contribution:\n"
                "- **E-3 with 2 years:** about **$1,600/year**\n"
                "- **E-6 with 7 years:** about **$2,600/year**\n"
                "- **O-2 with 2 years:** about **$3,400/year**\n"
                "- **O-3 with 6 years:** about **$4,400/year**\n\n"
                "If you're contributing less than **5%**, you're leaving free money on the table."
            )

        st.divider()
        st.caption("Question 2 of 5")

        invest_q2 = st.radio(
            "Which habit matters most for long-term investing success?",
            [
                "Picking the perfect stock",
                "Timing the market",
                "Investing consistently for many years",
                "Watching financial news",
            ],
            index=None,
            key="invest_q2",
        )
        if invest_q2:
            st.info(
                "Most investing success comes from **time and consistency**, not brilliance."
            )

        st.divider()
        st.caption("Question 3 of 5")

        invest_q3 = st.radio(
            "What is the difference between **Roth and Traditional TSP**?",
            [
                "Roth taxed later / Traditional taxed now",
                "Traditional taxed later / Roth taxed now",
                "Same taxes",
                "Roth grows faster",
            ],
            index=None,
            key="invest_q3",
        )
        if invest_q3:
            st.info(
                "Nobody knows future tax rates.\n\n"
                "The important thing is **investing consistently**.\n\n"
                "For many service members, **Roth TSP is often the better default early in a career**.\n\n"
                "Learn more: [Roth vs Traditional TSP](https://www.tsp.gov/making-contributions/traditional-and-roth-contributions/)"
            )

        st.divider()
        st.caption("Question 4 of 5")

        invest_q4 = st.radio(
            "What do **TSP Lifecycle (L) Funds** do?",
            [
                "Guarantee returns",
                "Automatically adjust investment risk over time",
                "Eliminate market losses",
                "Double contributions",
            ],
            index=None,
            key="invest_q4",
        )
        if invest_q4:
            st.info(
                "Lifecycle funds gradually shift from **growth investments early** to **more stability later**, simplifying long-term investing.\n\n"
                "Learn more: [TSP Lifecycle Funds](https://www.tsp.gov/funds-lifecycle/)"
            )

        st.divider()
        st.caption("Question 5 of 5")

        invest_q5 = st.radio(
            "If you've already contributed the maximum to your TSP ($24,500 in 2026), where would you typically invest additional long-term retirement savings?",
            [
                "529 college savings account",
                "Individual Retirement Account (IRA)",
                "Taxable brokerage account",
                "Mattress",
            ],
            index=None,
            key="invest_q5",
        )
        if invest_q5:
            st.info(
                "If you've already maxed your TSP, the next common place for retirement investing is an **Individual Retirement Account (IRA)**.\n\n"
                "IRAs provide additional tax advantages similar to the TSP.\n\n"
                "After maxing both **TSP and IRA**, additional investing usually goes into a **taxable brokerage account**.\n\n"
                "A common order looks like this:\n"
                "1. Capture full **TSP match**\n"
                "2. Max **TSP**\n"
                "3. Max **IRA**\n"
                "4. Invest additional savings in **taxable brokerage**\n\n"
                "Learn more: [IRA overview](https://www.investopedia.com/terms/i/ira.asp)"
            )

    # -----------------------------
    # GI Bill
    # -----------------------------
    with st.expander("🎓 GI Bill"):
        st.markdown("**A career launch pad. Or a wasted benefit.**")
        st.markdown("Your choice.")
        st.caption("Question 1 of 5")

        gi_q1 = st.radio(
            "What does the Post-9/11 GI Bill typically cover?",
            [
                "Tuition only",
                "Tuition, housing allowance, and books",
                "Housing only",
                "Student loans",
            ],
            index=None,
            key="gi_q1",
        )
        if gi_q1:
            st.info(
                "The Post-9/11 GI Bill generally provides three things:\n\n"
                "**1. Tuition and Fees**\n\n"
                "- Full **in-state tuition** at public schools\n"
                "- Up to **$28,937 per academic year (2026 cap)** at private schools\n\n"
                "**2. Monthly Housing Allowance**\n\n"
                "Based on **E-5 BAH with dependents** for the school's ZIP code.\n\n"
                "You can check BAH rates here: [BAH Calculator](https://www.travel.dod.mil/Allowances/Basic-Allowance-for-Housing/BAH-Rate-Lookup/)\n\n"
                "**3. Book Stipend**\n\n"
                "Up to **$1,000 per academic year**\n\n"
                "Depending on the school, the GI Bill can easily be worth **well over $100,000**.\n\n"
                "Learn more: [VA GI Bill Benefits](https://www.va.gov/education/about-gi-bill-benefits/)"
            )

        st.divider()
        st.caption("Question 2 of 5")

        gi_q2 = st.radio(
            "How is the GI Bill monthly housing allowance calculated?",
            [
                "Flat national amount",
                "Based on your previous military pay",
                "Based on E-5 BAH with dependents at the school's ZIP code",
                "Based on tuition cost",
            ],
            index=None,
            key="gi_q2",
        )
        if gi_q2:
            st.info(
                "The housing allowance is calculated using **E-5 BAH with dependents** for the location of the school.\n\n"
                "That means the housing benefit varies significantly depending on where you attend.\n\n"
                "Learn more: [BAH Calculator](https://www.travel.dod.mil/Allowances/Basic-Allowance-for-Housing/BAH-Rate-Lookup/)"
            )

        st.divider()
        st.caption("Question 3 of 5")

        gi_q3 = st.radio(
            "When can you transfer the GI Bill to a dependent?",
            [
                "Anytime before retirement",
                "After leaving the military",
                "After 6 years of service with a 4-year service commitment",
                "Only at 20 years",
            ],
            index=None,
            key="gi_q3",
        )
        if gi_q3:
            st.info(
                "To transfer GI Bill benefits you must:\n\n"
                "- have **6 years of service**\n"
                "- commit to **4 additional years**\n\n"
                "Many people wait too long and lose the opportunity.\n\n"
                "Learn more: [Transfer Your GI Bill Benefits](https://www.va.gov/education/transfer-post-9-11-gi-bill-benefits/)"
            )

        st.divider()
        st.caption("Question 4 of 5")

        gi_q4 = st.radio(
            "Why can't ROTC and service academy graduates always transfer their GI Bill at 6 years of service?",
            [
                "Officers are ineligible",
                "They can",
                "Their commissioning source and service obligation may affect when they reach full eligibility",
                "Congressional approval is required",
            ],
            index=None,
            key="gi_q4",
        )
        if gi_q4:
            st.info(
                "The 6-year transfer window is more complicated for ROTC and academy-commissioned officers. "
                "Service obligations, how entitlement is calculated, and whether prior service counts "
                "all affect the actual eligibility date — and the rules are nuanced enough that stating "
                "a specific year here would risk being wrong for your situation.\n\n"
                "**The right move:** Check [VA.gov's transfer page](https://www.va.gov/education/transfer-post-9-11-gi-bill-benefits/) "
                "or call a VA education counselor (1-888-442-4551) to get your exact eligibility date. "
                "Don't guess on this one — the 4-year service commitment you incur when you transfer is real."
            )

        st.divider()
        st.caption("Question 5 of 5")

        gi_q5 = st.radio(
            "You're at 18 years of service and decide to transfer your GI Bill to your child. What happens next?",
            [
                "Transfer is automatic",
                "You must commit to 4 more years of service",
                "Transfer is no longer allowed",
                "The benefit disappears",
            ],
            index=None,
            key="gi_q5",
        )
        if gi_q5:
            st.info(
                "GI Bill transfer requires a **4-year service commitment**.\n\n"
                "If you initiate the transfer at **18 years**, the obligation extends to **22 years of service**.\n\n"
                "Many people discover this rule too late.\n\n"
                "Learn more: [GI Bill Transfer Rules](https://www.va.gov/education/transfer-post-9-11-gi-bill-benefits/)"
            )

    # -----------------------------
    # VA Loan
    # -----------------------------
    with st.expander("🏠 VA Loan"):
        st.markdown("**A powerful opportunity. Or a serious risk.**")
        st.markdown("Understand the difference.")
        st.caption("Question 1 of 5")

        va_q1 = st.radio(
            "What is the main advantage of the VA Loan program?",
            [
                "Guaranteed approval",
                "Lower property taxes",
                "Ability to buy a home with little or no down payment and no PMI",
                "No closing costs",
            ],
            index=None,
            key="va_q1",
        )
        if va_q1:
            st.info(
                "VA Loans allow qualified service members to buy homes with **little or no down payment** and **no private mortgage insurance (PMI)**.\n\n"
                "This reduces the cash required to purchase a home compared with many conventional mortgages.\n\n"
                "Learn more: [VA Home Loans](https://www.va.gov/housing-assistance/home-loans/)"
            )

        st.divider()
        st.caption("Question 2 of 5")

        va_q2 = st.radio(
            "Which factor matters most when deciding whether buying with a VA Loan makes financial sense?",
            [
                "Your rank",
                "Your credit score",
                "How long you expect to stay in the home",
                "Your car payment",
            ],
            index=None,
            key="va_q2",
        )
        if va_q2:
            st.info(
                "Buying a home involves large transaction costs when you sell.\n\n"
                "Example using a **$420,000 home (roughly the U.S. median price):**\n\n"
                "- Realtor commission (~6%) → ~$25,000\n"
                "- Closing costs → ~$5,000–$10,000\n\n"
                "Total potential selling costs: **~$30,000+**\n\n"
                "If you move after only a few years, the home price may not have risen enough to offset those costs.\n\n"
                "Learn more: [Rent vs Buy Calculator](https://www.nytimes.com/interactive/2014/upshot/buy-rent-calculator.html)"
            )

        st.divider()
        st.caption("Question 3 of 5")

        va_q3 = st.radio(
            "What does the VA Funding Fee do?",
            [
                "Lowers interest rates",
                "Replaces property taxes",
                "Adds additional cost to the loan",
                "Eliminates closing costs",
            ],
            index=None,
            key="va_q3",
        )
        if va_q3:
            st.info(
                "The VA Funding Fee helps support the VA loan program.\n\n"
                "It typically ranges from about **2%–3.3% of the loan amount**.\n\n"
                "Example:\n\n"
                "$420,000 home\n"
                "Funding fee → **~$8,000–$13,000**\n\n"
                "Most borrowers roll this into the loan balance.\n\n"
                "Learn more: [VA Funding Fee and Closing Costs](https://www.va.gov/housing-assistance/home-loans/funding-fee-and-closing-costs/)"
            )

        st.divider()
        st.caption("Question 4 of 5")

        va_q4 = st.radio(
            "In the early years of a mortgage, where do most monthly payments go?",
            [
                "Principal",
                "Closing costs",
                "Interest",
                "Property taxes",
            ],
            index=None,
            key="va_q4",
        )
        if va_q4:
            st.info(
                "Mortgage payments early in a loan mostly go toward **interest**, not the loan balance.\n\n"
                "Example:\n\n"
                "$420,000 loan\n"
                "6.5% interest\n"
                "30-year mortgage\n\n"
                "Monthly payment ≈ **$2,650**\n\n"
                "First payment:\n"
                "- Interest ≈ ~$2,280\n"
                "- Principal ≈ ~$370\n\n"
                "After several years of payments, you may have paid tens of thousands of dollars while reducing the loan balance only modestly.\n\n"
                "Learn more:\n"
                "- [Mortgage Amortization Calculator](https://www.bankrate.com/mortgages/amortization-calculator/)\n"
                "- [Rent vs Buy Calculator](https://www.nytimes.com/interactive/2014/upshot/buy-rent-calculator.html)"
            )

        st.divider()
        st.caption("Question 5 of 5")

        va_q5 = st.radio(
            "How much should homeowners generally budget each year for maintenance and repairs?",
            [
                "$0",
                "$500",
                "1–2% of the home's value per year",
                "$1,000 total",
            ],
            index=None,
            key="va_q5",
        )
        if va_q5:
            st.info(
                "A common rule of thumb is **1–2% of the home's value per year** for maintenance.\n\n"
                "For a **$420,000 home**, that is roughly:\n\n"
                "**$4,000–$8,000 annually**\n\n"
                "This covers things like roof repairs, HVAC replacement, appliances, plumbing, and other ongoing maintenance.\n\n"
                "Learn more: [Home Maintenance Budget](https://www.nytimes.com/guides/realestate/home-maintenance-budget)"
            )
# --- TAB 5: ACTION PLAN ---
with tab5:
    if 5 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(5)
        log_event("tab_visited", 5)
    st.header("The Personal Finance Playbook")
    st.write(
        "Know where you are, decide what you want, and start building."
        " - Crawl, walk, run. You don't need to be perfect; you need to make progress."
        " - Plans without action are just dreams."
    )

    total_steps = 11
    steps_completed = sum([st.session_state.get(f"step_{i}", False) for i in range(1, total_steps + 1)])
    progress_pct = int((steps_completed / total_steps) * 100)

    col_pct, col_bar = st.columns([1, 4])
    with col_pct:
        st.metric("Progress", f"{progress_pct}%", f"{steps_completed}/{total_steps} steps")
    with col_bar:
        st.write("")
        st.write("")
        st.progress(steps_completed / total_steps)

    if steps_completed == total_steps:
        st.balloons()
        st.success("You've worked the whole list. The hard part is behind you — now you just let it run.")

    st.divider()

    # ── CRAWL ─────────────────────────────────────────────────────────────────
    st.subheader("🐛 Crawl — Do all four simultaneously")

    with st.expander("1. Get access to your money"):
        st.markdown(
            "Your CAC is your key to everything. Once you have it, get into "
            "[MyPay](https://mypay.dfas.mil) — that's where your pay, TSP contributions, "
            "and direct deposit all live. If you're in the BRS, set your TSP contribution "
            "to at least **5%** right now. That's all it takes to capture the full government match — "
            "1% automatic + dollar-for-dollar on your first 3% + 50 cents on the next 2% = 5% from them. "
            "Every paycheck you delay is money you don't get back.\n\n"
            "[How to change your TSP contribution](https://www.tsp.gov/making-contributions/start-change-stop-contributions/) · "
            "[MyPay](https://mypay.dfas.mil)"
        )
        st.checkbox("I have MyPay access and my TSP is set to at least 5%", key="step_1")

    with st.expander("2. Open a high-yield savings account and get to $1,000"):
        st.markdown(
            "Don't put this in your checking account — keep it separate enough that you won't spend it, "
            "and in an account that actually pays you interest. Just one-thousand. That's the goal right now. "
            "That's the buffer that keeps one bad week "
            "from going on a credit card.\n\n"
            "[Compare HYSA rates — NerdWallet](https://www.nerdwallet.com/best/banking/high-yield-online-savings-accounts)"
        )
        st.checkbox("I have an HYSA with at least $1,000 in it", key="step_2")

    with st.expander("3. Check your pre-service debt for SCRA protection"):
        st.markdown(
            "If you had loans or credit cards before you came on active duty, lenders are legally required "
            "to cap your interest at 6%. Most won't do it unless you ask. Call them, tell them you're active duty, "
            "and send a copy of your orders. If you've been overpaying, they owe you a refund.\n\n"
            "[SCRA overview — DOJ](https://www.justice.gov/servicemembers) · "
            "[File a complaint — CFPB](https://www.consumerfinance.gov/complaint/)"
        )
        st.checkbox("I have checked my pre-service debt for SCRA eligibility", key="step_3")

    with st.expander("4. Kill high-interest debt"):
        st.markdown(
            "No investment will beat a 20% APR debt. Every dollar you put toward it is a guaranteed return — "
            " Use the "
            "[Avalanche method](https://www.investopedia.com/terms/d/debt-avalanche.asp) "
            "(highest rate first, mathematically optimal) or the "
            "[Snowball method](https://www.investopedia.com/terms/d/debt-snowball.asp) "
            "(smallest balance first, psychological wins). Either works. Pick one and get rid of the debt.\n\n"
            "[See what minimum payments actually cost you — Bankrate](https://www.bankrate.com/calculators/credit-cards/minimum-payment-calculator.aspx)"
        )
        st.checkbox("I have a plan to eliminate all debt above 8% APR", key="step_4")

    st.divider()

    # ── WALK ──────────────────────────────────────────────────────────────────
    st.subheader("🚶 Walk — In order")

    with st.expander("5. Build the real emergency fund"):
        st.markdown(
            "Now bring your buffer up to 3–6 months of actual living expenses, in the same HYSA. "
            "This is what keeps a bad month from becoming a bad year — a job transition, a medical bill, "
            "a car that dies. Once it's funded, leave it alone.\n\n"
            "[Emergency fund guidance — Military OneSource](https://www.militaryonesource.mil/financial-legal/personal-finance/building-emergency-savings/)"
        )
        st.checkbox("My HYSA holds 3–6 months of living expenses", key="step_5")

    with st.expander("6. Check where your TSP money is actually invested"):
        st.markdown(
            "If you joined before 2018 your TSP defaulted into the G-Fund — it barely beats inflation. "
            "On [TSP.gov](https://www.tsp.gov) you need to do two separate things: change your "
            "**Contribution Allocation** (where new money goes) and submit an **Interfund Transfer** "
            "(where your existing balance sits). Most people only do one. Both matter.\n\n"
            "[How to change your TSP allocation](https://www.tsp.gov/fund-performance/interfund-transfers.html) · "
            "[TSP Fund information](https://www.tsp.gov/funds-individual/)"
        )
        st.checkbox("My TSP allocation is set intentionally — not defaulted", key="step_6")

    with st.expander("7. Set your savings rate and automate it"):
        st.markdown(
            "Tab 2 gave you a percentage. Put that number into [MyPay](https://mypay.dfas.mil) and don't touch it. "
            "If your required savings will exceed the TSP annual limit, Tab 2 showed you where the overflow goes — "
            "IRA first, then brokerage. The point is that it happens automatically. "
            "Not when you remember. Not when the market looks good. Every month, on repeat.\n\n"
            "[MyPay](https://mypay.dfas.mil) · "
            "[Roth IRA overview — Investopedia](https://www.investopedia.com/terms/r/rothira.asp)"
        )
        st.checkbox("My savings rate is set in MyPay and automated", key="step_7")

    st.divider()

    # ── RUN ───────────────────────────────────────────────────────────────────
    st.subheader("🏃 Run — Once the walk phase is solid")

    with st.expander("8. Get your paperwork right"):
        st.markdown(
            "JAG will do a will and power of attorney for free — use it. "
            "Update your SGLI beneficiary through [milConnect](https://milconnect.dmdc.osd.mil). "
            "Set your TSP beneficiary separately on [TSP.gov](https://www.tsp.gov/account-basics/designate-beneficiaries/) — "
            "it's a different form and most people never fill it out. "
            "These take less than an hour and protect everything else you're building."
        )
        st.checkbox("Will, POA, SGLI beneficiary, and TSP beneficiary are all current", key="step_8")

    with st.expander("9. Know your GI Bill transfer window"):
        st.markdown(
            "You can transfer the Post-9/11 GI Bill to a dependent at 6 years of service, "
            "but you have to commit to 4 more years from the transfer date. "
            "If you're ROTC- or academy-commissioned, your eligibility date may be later than year 6 "
            "depending on your service obligation and how entitlement is calculated for your commissioning source — "
            "don't assume the standard 6-year rule applies without checking. "
            "Prior enlisted service can also affect the date. "
            "If you wait until year 18 you'll owe until year 22. "
            "Know your number, decide whether you want to transfer it, and put a calendar reminder "
            "on the exact date you become eligible — don't rely on someone telling you.\n\n"
            "[Transfer your GI Bill — VA](https://www.va.gov/education/transfer-post-9-11-gi-bill-benefits/) · "
            "VA education counselors: 1-888-442-4551"
        )
        st.checkbox("I know my GI Bill transfer eligibility date and have made a decision", key="step_9")

    with st.expander("10. Understand your VA benefits"):
        st.markdown(
            "You earned these. Make sure you know what you're entitled to before you separate — "
            "healthcare, disability, home loan, education. The window to document and file doesn't stay open forever. "
            "A Benefits Delivery at Discharge (BDD) claim filed 180 days before separation gives you "
            "the best chance of a smooth transition.\n\n"
            "[VA benefits overview](https://www.va.gov/benefits/) · "
            "[BDD claim information](https://www.va.gov/disability/how-to-file-claim/when-to-file/pre-discharge-claim/)"
        )
        st.checkbox("I understand my VA benefits and have a plan for separation", key="step_10")

    with st.expander("11. Build beyond the plan"):
        st.markdown(
            "You've automated retirement, cleared the debt, funded the emergency account, "
            "and sorted the military-specific stuff. Now decide what's next.\n\n"
            "**Retire earlier or richer** — max your TSP and IRA fully, then keep going. "
            "The math compounds faster than most people expect once the foundation is solid. "
            "[r/financialindependence](https://www.reddit.com/r/financialindependence) · "
            "[r/fatFIRE](https://www.reddit.com/r/fatFIRE)\n\n"
            "**Real estate** — the VA loan gives you an entry point most civilians don't have, "
            "including the option to buy a small multi-family property and live in one unit. "
            "It's not passive, but it builds wealth. "
            "[BiggerPockets](https://www.biggerpockets.com)\n\n"
            "**Starting a business** — high risk, real upside. Free resources exist specifically for veterans. "
            "[SBA Boots to Business](https://sbavets.force.com/s/) · "
            "[VA Small Business Resources](https://www.sba.gov/business-guide/grow-your-business/veteran-owned-businesses)\n\n"
            "**Goal-based saving** — car, kids, college, whatever matters to you. "
            "Once the foundation is built, saving for specific things is just a matter of opening "
            "separate accounts and automating contributions. "
            "[r/personalfinance flowchart](https://www.reddit.com/r/personalfinance/wiki/commontopics)"
        )
        st.checkbox("I have thought about what comes next and have a direction", key="step_11")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 6: YOUR PLAN / PDF
# Page 1: Income snapshot, retirement targets, Monte Carlo chart (if run),
#          budget summary, budget bar chart.
# Page 2: Financial order of operations checklist (11 steps, crawl/walk/run).
# All data pulled from session_state. No way_forward paragraph.
# PDF generated in-memory with fpdf2 + matplotlib. No temp files written.
# ════════════════════════════════════════════════════════════════════════════════
# --- TAB 6: MY FINANCIAL PLAN (PDF) ---
with tab6:
    if 6 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(6)
        log_event("tab_visited", 6)
    st.header("📄 Your Plan")
    st.caption("Your numbers and your checklist — one PDF. Download it, share it, or just keep it somewhere you'll look at it.")

    # ── Check what data is available ─────────────────────────────────────────
    missing = []
    if st.session_state.get("base_pay", 0.0) == 0.0:
        missing.append("**Tab 1** — complete your rank, TIS, and zip code")
    if st.session_state.get("pmt_target", 0.0) == 0.0:
        missing.append("**Tab 2** — complete your career inputs and fund allocation")
    if st.session_state.get("tab3_take_home", 0.0) == 0.0:
        missing.append("**Tab 3** — enter your take-home pay and budget")

    if missing:
        st.warning("Complete the following before generating your plan:\n\n" +
                   "\n".join(f"- {m}" for m in missing))
    else:
        # ── Pull data from session state ──────────────────────────────────────
        base_pay      = st.session_state.get("base_pay", 0.0)
        bah_amt       = st.session_state.get("bah_amt", 0.0)
        bas_amt       = st.session_state.get("bas_amt", 0.0)
        special_pay   = st.session_state.get("special_pay", 0.0)
        gross_monthly = base_pay + bah_amt + bas_amt + special_pay

        savings_rate  = st.session_state.get("savings_rate_pct", 0.0)
        nest_egg      = st.session_state.get("nest_egg_target", 0.0)
        est_pension   = st.session_state.get("est_pension", 0.0)
        pmt_target    = st.session_state.get("pmt_target", 0.0)

        take_home     = st.session_state.get("tab3_take_home", 0.0)
        fixed_costs   = st.session_state.get("tab3_fixed", 0.0)
        invested      = st.session_state.get("tab3_invested", 0.0)
        guilt_free    = st.session_state.get("tab3_guilt_free", 0.0)
        surplus       = take_home - fixed_costs - invested - guilt_free

        mc_results    = st.session_state.get("sim_results", None)
        mc_age_start  = st.session_state.get("sim_current_age", 0)
        mc_age_end    = st.session_state.get("sim_age_at_retire", 0)
        mc_target     = st.session_state.get("sim_target", 0.0)
        mc_rate       = st.session_state.get("sim_savings_pct", 0.0)

        # ── On-screen preview ─────────────────────────────────────────────────
        st.subheader("Snapshot")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**Income**")
            st.metric("Monthly Gross",  f"${gross_monthly:,.0f}")
            st.metric("Base Pay",       f"${base_pay:,.0f}")
            st.metric("BAH",            f"${bah_amt:,.0f}")
            st.metric("BAS",            f"${bas_amt:,.0f}")
        with col_b:
            st.markdown("**Retirement**")
            st.metric("Est. Monthly Pension",   f"${est_pension:,.0f}")
            st.metric("Target Nest Egg",        f"${nest_egg:,.0f}")
            st.metric("Required Savings Rate",  f"{savings_rate*100:.1f}% of Base Pay" if savings_rate else "—")
            if mc_results is not None:
                mc_success = st.session_state.get("mc_success_rate", None)
                if mc_success is not None:
                    st.metric("Simulation Success Rate", f"{mc_success:.0f}%")
        with col_c:
            st.markdown("**Budget**")
            st.metric("Take-Home",  f"${take_home:,.0f}")
            st.metric("Fixed",      f"${fixed_costs:,.0f}")
            st.metric("Invested",   f"${invested:,.0f}")
            delta_color = "normal" if surplus >= 0 else "inverse"
            st.metric("Surplus / Deficit", f"${surplus:,.0f}",
                      delta="On track" if surplus >= 0 else "Needs attention",
                      delta_color=delta_color)

        st.divider()

        # ── PDF generation ────────────────────────────────────────────────────
        if st.button("📥 Generate & Download PDF", type="primary"):
            if not st.session_state.pdf_logged:
                st.session_state.pdf_logged = True
                log_event("pdf_downloaded")

            from fpdf import FPDF
            import datetime
            import io

            pdf = FPDF()
            pdf.set_margins(15, 15, 15)

            def safe(text):
                return (str(text)
                    .replace('\u2014', '-').replace('\u2013', '-')
                    .replace('\u2190', '<-').replace('\u2192', '->')
                    .replace('\u2019', "'").replace('\u2018', "'")
                    .replace('\u201c', '"').replace('\u201d', '"')
                    .replace('\u2026', '...')
                )

            def page_header():
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_fill_color(30, 60, 114)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(0, 10, safe("F.I.R.E. for Effect  —  Financial Plan"), fill=True, ln=True, align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(0, 5, safe(f"Generated {datetime.date.today().strftime('%B %d, %Y')}  |  For planning purposes only — not financial advice."), ln=True, align="C")
                pdf.ln(3)

            def section_header(title):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_fill_color(220, 230, 245)
                pdf.set_text_color(30, 60, 114)
                pdf.cell(0, 6, safe(f"  {title}"), fill=True, ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1)

            def row(label, value):
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(90, 5, safe(f"    {label}"), ln=False)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 5, safe(value), ln=True)

            # ── PAGE 1 ────────────────────────────────────────────────────────
            pdf.add_page()
            page_header()

            # Income
            section_header("INCOME SNAPSHOT")
            row("Monthly Gross Pay:", f"${gross_monthly:,.0f}")
            row("Base Pay:", f"${base_pay:,.0f}")
            row("BAH (Tax-Free):", f"${bah_amt:,.0f}")
            row("BAS (Tax-Free):", f"${bas_amt:,.0f}")
            row("Special Pays:", f"${special_pay:,.0f}")
            pdf.ln(3)

            # Retirement
            section_header("RETIREMENT TARGETS")
            row("Estimated Monthly Pension:", f"${est_pension:,.0f}  (High-3 Average)")
            row("Target Nest Egg:", f"${nest_egg:,.0f}")
            row("Required Savings Rate:",
                f"{savings_rate*100:.1f}% of base pay  —  set in MyPay (mypay.dfas.mil)" if savings_rate else "N/A")
            pdf.ln(3)

            # Monte Carlo chart — only if simulation was run
            if mc_results is not None and mc_age_end > mc_age_start:
                _time = np.linspace(mc_age_start, mc_age_end, mc_results.shape[1])
                _p10  = np.percentile(mc_results, 10, axis=0)
                _p50  = np.percentile(mc_results, 50, axis=0)
                _p90  = np.percentile(mc_results, 90, axis=0)

                _mc_fig, _mc_ax = plt.subplots(figsize=(7.2, 2.8))
                _mc_fig.patch.set_facecolor('white')
                _mc_ax.set_facecolor('white')
                _mc_ax.fill_between(_time, _p10, _p90, color='#00b4d8', alpha=0.15, label='10th–90th percentile')
                _mc_ax.plot(_time, _p50, color='#00b4d8', lw=2, label=f'Median  (saving {mc_rate*100:.1f}% of base pay)')
                _mc_ax.axhline(y=mc_target, color='#ef476f', linestyle='--', lw=1.5, label=f'Target: ${mc_target:,.0f}')
                _mc_ax.set_xlabel('Age', fontsize=8)
                _mc_ax.set_ylabel('Portfolio Value', fontsize=8)
                _mc_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1e6:.1f}M' if x >= 1e6 else f'${int(x):,}'))
                _mc_ax.tick_params(labelsize=7)
                _mc_ax.legend(fontsize=7, loc='upper left')
                _mc_ax.spines['top'].set_visible(False)
                _mc_ax.spines['right'].set_visible(False)
                _mc_ax.grid(True, linestyle='--', alpha=0.3)
                _mc_fig.tight_layout()

                _mc_buf = io.BytesIO()
                _mc_fig.savefig(_mc_buf, format='png', dpi=150, bbox_inches='tight')
                plt.close(_mc_fig)
                _mc_buf.seek(0)

                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 5, "Luck & Timing Roulette — 1,000 simulated market scenarios", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.image(_mc_buf, x=15, w=180)
                pdf.ln(2)

            # Budget summary
            section_header("MONTHLY BUDGET SUMMARY")
            row("Take-Home Pay:", f"${take_home:,.0f}")
            row("Fixed Costs:", f"${fixed_costs:,.0f}")
            row("Investments / Savings:", f"${invested:,.0f}")
            row("Guilt-Free Spending:", f"${guilt_free:,.0f}")
            _status = "SURPLUS" if surplus >= 0 else "DEFICIT"
            row(f"Budget {_status}:", f"${abs(surplus):,.0f} / month")
            pdf.ln(3)

            # Budget bar chart
            if take_home > 0:
                _surplus_plot = max(0.0, surplus)
                _vals   = [fixed_costs, invested, guilt_free, _surplus_plot]
                _labels = ['Fixed', 'Invested', 'Guilt-Free', 'Surplus']
                _colors = ['#ef476f', '#00b4d8', '#ffd166', '#06d6a0']
                _total  = sum(_vals) if sum(_vals) > 0 else 1

                _bar_fig, _bar_ax = plt.subplots(figsize=(7.2, 0.9))
                _bar_fig.patch.set_facecolor('white')
                _bar_ax.set_facecolor('white')
                _left = 0
                for _v, _lbl, _c in zip(_vals, _labels, _colors):
                    if _v > 0:
                        _bar_ax.barh(0, _v / _total, left=_left / _total,
                                     color=_c, height=0.5, label=f"{_lbl} ${_v:,.0f}")
                        _left += _v
                _bar_ax.set_xlim(0, 1)
                _bar_ax.axis('off')
                _bar_ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                               ncol=4, fontsize=7, frameon=False)
                if surplus < 0:
                    _bar_ax.set_title(f"Budget deficit: ${abs(surplus):,.0f}/month", fontsize=8, color='#ef476f')
                _bar_fig.tight_layout()

                _bar_buf = io.BytesIO()
                _bar_fig.savefig(_bar_buf, format='png', dpi=150, bbox_inches='tight')
                plt.close(_bar_fig)
                _bar_buf.seek(0)
                pdf.image(_bar_buf, x=15, w=180)
                pdf.ln(2)

            # Disclaimer bottom of page 1
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(140, 140, 140)
            pdf.multi_cell(180, 4, safe(
                "Projections use primary-zone promotion timelines, historical TSP fund return averages, "
                "and a 4% safe withdrawal rate. Actual results will vary. "
                "Consult a Certified Financial Planner for personalized advice."))
            pdf.set_text_color(0, 0, 0)

            # ── PAGE 2 — CHECKLIST ────────────────────────────────────────────
            pdf.add_page()
            page_header()

            section_header("YOUR FINANCIAL ORDER OF OPERATIONS")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5, "Crawl, walk, run. Work these in order.", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

            _BOX  = 4    # checkbox square size
            _LH   = 6    # line height
            _IND  = 22   # text indent from left margin

            def checklist_group(title):
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_fill_color(235, 240, 250)
                pdf.set_text_color(30, 60, 114)
                pdf.cell(0, 6, safe(f"  {title}"), fill=True, ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1)

            def checklist_item(text, link=None):
                # Draw checkbox
                _y = pdf.get_y()
                pdf.set_draw_color(100, 100, 100)
                pdf.rect(15, _y + 1, _BOX, _BOX)
                # Item text
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_xy(_IND, _y)
                if link:
                    full = f"{text}  {link}"
                else:
                    full = text
                pdf.multi_cell(180 - (_IND - 15), _LH, safe(full))
                pdf.ln(0.5)

            checklist_group("CRAWL — Do all four simultaneously")
            checklist_item("Get CAC access, log into MyPay, set TSP to at least 5% to capture full BRS match", "mypay.dfas.mil")
            checklist_item("Open a high-yield savings account and get to $1,000")
            checklist_item("Check pre-service debt for SCRA interest rate protection", "justice.gov/servicemembers")
            checklist_item("Kill high-interest debt — Avalanche or Snowball, pick one and commit")
            pdf.ln(2)

            checklist_group("WALK — In order")
            checklist_item("Build the full emergency fund — 3 to 6 months of expenses in your HYSA")
            checklist_item("Check TSP fund allocation — Contribution Allocation AND Interfund Transfer", "tsp.gov")
            checklist_item("Set your savings rate in MyPay and automate it", "mypay.dfas.mil")
            pdf.ln(2)

            checklist_group("RUN — Once the walk phase is solid")
            checklist_item("Get your paperwork right — JAG will, POA, SGLI beneficiary, TSP beneficiary", "milconnect.dmdc.osd.mil")
            checklist_item("Know your GI Bill transfer eligibility date — decide and set a calendar reminder", "va.gov/education/transfer-post-9-11-gi-bill-benefits")
            checklist_item("Understand your VA benefits before you separate", "va.gov/benefits")
            checklist_item("Build beyond the plan — max retirement accounts, real estate, goal-based saving", "reddit.com/r/financialindependence")
            pdf.ln(4)

            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(140, 140, 140)
            pdf.multi_cell(180, 4, safe(
                "This document is for educational purposes only and does not constitute financial advice. "
                "F.I.R.E. for Effect — fireforeffect.app"))

            # ── Output ────────────────────────────────────────────────────────
            pdf_bytes = pdf.output()
            st.download_button(
                label="⬇️ Download Your Financial Plan (PDF)",
                data=bytes(pdf_bytes),
                file_name=f"fire_for_effect_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )
            st.success("✅ PDF ready — click above to download.")

# --- TAB 7: FEEDBACK ---
with tab7:
    if 7 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(7)
        log_event("tab_visited", 7)
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

# --- TAB 8: RENT VS. BUY ---
with tab8:
    if 8 not in st.session_state.tabs_logged:
        st.session_state.tabs_logged.add(8)
        log_event("tab_visited", 8)

    st.header("🏠 Should You Rent or Buy?")
    st.caption("This calculator is built around your BAH. It tells you the true cost of buying vs. renting, "
               "what equity you actually build, and — if you plan to rent it out later — what your real return looks like.")

    # ── SECTION 1: BAH LOOKUP ──────────────────────────────────────────────────
    st.subheader("Step 1: Your BAH")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        rvb_rank = st.selectbox("Rank", CONFIG["ranks"],
                                index=CONFIG["ranks"].index(st.session_state.get("tab1_rank", CONFIG["ranks"][14])),
                                key="rvb_rank")
    with col_r2:
        rvb_zip = st.text_input("Duty Station ZIP", value=st.session_state.get("tab1_zip", ""), key="rvb_zip")
    with col_r3:
        rvb_dep = st.radio("Dependents", ["With", "Without"], horizontal=True, key="rvb_dep")
    with col_r4:
        rvb_tis = st.number_input("Years of Service", min_value=0, max_value=30, value=4, key="rvb_tis")

    rvb_has_dep = (rvb_dep == "With")
    _, _, rvb_bah_auto = get_military_pay(rvb_rank, rvb_tis, rvb_zip, rvb_has_dep)

    if rvb_bah_auto > 0:
        st.success(f"BAH for **{rvb_rank}** at ZIP **{rvb_zip}** ({'w/' if rvb_has_dep else 'w/o'} dependents): **\\${rvb_bah_auto:,.0f}/month**")
        rvb_bah = rvb_bah_auto
    else:
        st.warning(f"ZIP **{rvb_zip}** not found — enter BAH manually.")
        rvb_bah = st.number_input("Your Monthly BAH (\\$/month)", min_value=0.0, step=50.0, value=2000.0, key="rvb_bah_manual")

    st.divider()

    # ── SECTION 2: PROPERTY & LOAN INPUTS ─────────────────────────────────────
    st.subheader("Step 2: The Property & Loan")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        rvb_home_price   = st.number_input("Home Price (\\$)", min_value=50_000, max_value=2_000_000,
                                            value=350_000, step=5_000, key="rvb_price")
        rvb_market_rent  = st.number_input("Market Rent for Comparable Home (\\$/month)",
                                            min_value=500, max_value=10_000, value=int(rvb_bah * 0.95) if rvb_bah > 0 else 2000,
                                            step=50, key="rvb_mkt_rent")
        rvb_years_stay   = st.slider("How Long Do You Plan to Stay? (years)", 1, 15, 3, key="rvb_stay")

    with col_p2:
        rvb_va_loan = st.toggle("VA Loan (0% down, no PMI)", value=True, key="rvb_va")
        if rvb_va_loan:
            rvb_down_pct = 0.0
            st.caption("VA loan: no down payment, no PMI. A 2.15% funding fee is rolled into the loan (first use, not disabled).")
            rvb_funding_fee_pct = 0.0215
        else:
            rvb_down_pct = st.slider("Down Payment (%)", 3, 25, 10, key="rvb_down") / 100
            rvb_funding_fee_pct = 0.0

        rvb_rate = st.number_input("Interest Rate (%)", min_value=2.0, max_value=12.0,
                                    value=6.75, step=0.05, format="%.2f", key="rvb_rate") / 100

    st.divider()

    # ── SECTION 3: ADJUSTABLE ASSUMPTIONS ─────────────────────────────────────
    with st.expander("⚙️ Adjust Assumptions (click to customize — defaults are conservative baselines)"):
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            rvb_appreciation  = st.slider("Annual Home Appreciation (%)", 0.0, 8.0, 3.0, 0.25, key="rvb_appr") / 100
            rvb_prop_tax_rate = st.slider("Property Tax Rate (% of value/yr)", 0.5, 3.0, 1.1, 0.05, key="rvb_ptax") / 100
            rvb_maint_rate    = st.slider("Maintenance (% of value/yr)", 0.5, 2.0, 1.0, 0.1,  key="rvb_maint") / 100
        with col_a2:
            rvb_insurance_mo  = st.number_input("Home Insurance (\\$/month)", 50, 500, 120, 10, key="rvb_ins")
            rvb_hoa_mo        = st.number_input("HOA (\\$/month, 0 if none)", 0, 1000, 0, 25, key="rvb_hoa")
            rvb_pmi_rate      = 0.0 if rvb_va_loan else (
                st.slider("PMI Rate (% of loan/yr)", 0.2, 1.5, 0.5, 0.05, key="rvb_pmi") / 100
                if rvb_down_pct < 0.20 else 0.0
            )
        with col_a3:
            rvb_buy_closing   = st.slider("Buying Closing Costs (%)", 1.0, 5.0, 3.0, 0.25, key="rvb_bclose") / 100
            rvb_sell_closing  = st.slider("Selling Closing Costs (%)", 4.0, 8.0, 6.0, 0.25, key="rvb_sclose") / 100
            rvb_rent_increase = st.slider("Annual Rent Increase (%)", 0.0, 6.0, 3.0, 0.25, key="rvb_renti") / 100
            rvb_invest_return = st.slider("Investment Return on Down Payment if Renting (%)", 3.0, 10.0, 7.0, 0.25, key="rvb_inv") / 100

    # ── CALCULATIONS ───────────────────────────────────────────────────────────
    # Loan setup
    rvb_down_amt      = rvb_home_price * rvb_down_pct
    rvb_funding_fee   = (rvb_home_price * rvb_funding_fee_pct) if rvb_va_loan else 0.0
    rvb_loan_amt      = rvb_home_price - rvb_down_amt + rvb_funding_fee
    rvb_monthly_rate  = rvb_rate / 12
    rvb_n_payments    = 360  # 30-year

    if rvb_monthly_rate > 0:
        rvb_mortgage_pi = rvb_loan_amt * (rvb_monthly_rate * (1 + rvb_monthly_rate) ** rvb_n_payments) / \
                          ((1 + rvb_monthly_rate) ** rvb_n_payments - 1)
    else:
        rvb_mortgage_pi = rvb_loan_amt / rvb_n_payments

    rvb_prop_tax_mo   = (rvb_home_price * rvb_prop_tax_rate) / 12
    rvb_maint_mo      = (rvb_home_price * rvb_maint_rate) / 12
    rvb_pmi_mo        = (rvb_loan_amt * rvb_pmi_rate) / 12
    rvb_total_own_mo  = rvb_mortgage_pi + rvb_prop_tax_mo + rvb_insurance_mo + rvb_maint_mo + rvb_hoa_mo + rvb_pmi_mo
    rvb_buy_closing_cost = rvb_home_price * rvb_buy_closing

    # Month-by-month simulation over stay period
    n_months   = rvb_years_stay * 12
    balance    = rvb_loan_amt
    total_interest   = 0.0
    total_principal  = 0.0
    total_buy_costs  = rvb_buy_closing_cost + rvb_down_amt  # upfront cash out

    rent_mo    = float(rvb_market_rent)
    total_rent_paid  = 0.0
    invest_balance   = rvb_down_amt + rvb_buy_closing_cost  # opportunity cost invested

    monthly_costs_buy = []
    monthly_costs_rent = []

    for m in range(n_months):
        # Buy side
        interest_portion   = balance * rvb_monthly_rate
        principal_portion  = rvb_mortgage_pi - interest_portion
        balance           -= principal_portion
        total_interest    += interest_portion
        total_principal   += principal_portion

        # Rent side
        total_rent_paid   += rent_mo
        invest_balance    *= (1 + rvb_invest_return / 12)
        if m % 12 == 11:
            rent_mo *= (1 + rvb_rent_increase)

        monthly_costs_buy.append(rvb_total_own_mo)
        monthly_costs_rent.append(rent_mo)

    # End-of-stay values
    rvb_home_value_end  = rvb_home_price * (1 + rvb_appreciation) ** rvb_years_stay
    rvb_equity_end      = rvb_home_value_end - balance
    rvb_sell_cost       = rvb_home_value_end * rvb_sell_closing
    rvb_net_proceeds    = rvb_equity_end - rvb_sell_cost

    total_buy_out       = (rvb_total_own_mo * n_months) + rvb_buy_closing_cost + rvb_down_amt + rvb_funding_fee
    total_rent_out      = total_rent_paid
    buy_net_cost        = total_buy_out - rvb_net_proceeds  # true cost after selling
    rent_net_cost       = total_rent_out - (invest_balance - (rvb_down_amt + rvb_buy_closing_cost))  # rent minus investment gains

    net_delta           = rent_net_cost - buy_net_cost  # positive = buying wins

    bah_coverage_buy    = rvb_bah - rvb_total_own_mo
    bah_coverage_rent   = rvb_bah - rvb_market_rent

    # ── SECTION 4: OUTPUT ──────────────────────────────────────────────────────
    st.subheader("Step 3: The Numbers")

    # Monthly snapshot
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Monthly Mortgage (P&I)",    f"\\${rvb_mortgage_pi:,.0f}")
    mc2.metric("Total Monthly Own Cost",    f"\\${rvb_total_own_mo:,.0f}",
               delta=f"\\${rvb_total_own_mo - rvb_market_rent:+,.0f} vs renting",
               delta_color="inverse")
    mc3.metric("Market Rent",               f"\\${rvb_market_rent:,.0f}")
    mc4.metric("Your BAH",                  f"\\${rvb_bah:,.0f}")

    mc5, mc6, mc7, mc8 = st.columns(4)
    mc5.metric("BAH vs Own Cost",           f"\\${bah_coverage_buy:+,.0f}/mo",
               delta="surplus" if bah_coverage_buy >= 0 else "shortfall", delta_color="normal" if bah_coverage_buy >= 0 else "inverse")
    mc6.metric("BAH vs Rent",               f"\\${bah_coverage_rent:+,.0f}/mo",
               delta="surplus" if bah_coverage_rent >= 0 else "shortfall", delta_color="normal" if bah_coverage_rent >= 0 else "inverse")
    mc7.metric("Equity Built (Paydown)",     f"\\${total_principal:,.0f}")
    mc8.metric("Est. Home Value at Sale",    f"\\${rvb_home_value_end:,.0f}")

    st.divider()

    # Monthly cost breakdown table
    with st.expander("📋 Monthly Cost Breakdown — Buying"):
        rows = {
            "Principal & Interest":   rvb_mortgage_pi,
            "Property Tax":           rvb_prop_tax_mo,
            "Home Insurance":         float(rvb_insurance_mo),
            "Maintenance (est.)":     rvb_maint_mo,
            "HOA":                    float(rvb_hoa_mo),
            "PMI":                    rvb_pmi_mo,
        }
        if rvb_va_loan:
            rows[f"VA Funding Fee (rolled in, {rvb_funding_fee_pct*100:.2f}%)"] = rvb_funding_fee / 360
        df_breakdown = pd.DataFrame({"Monthly Cost": rows})
        df_breakdown["Monthly Cost"] = df_breakdown["Monthly Cost"].map(lambda x: f"${x:,.0f}")
        st.dataframe(df_breakdown, use_container_width=True)

    # True cost comparison over stay period
    st.subheader(f"Over {rvb_years_stay} Year{'s' if rvb_years_stay != 1 else ''}: True Cost After Selling")

    tc1, tc2, tc3 = st.columns(3)
    tc1.metric(f"Net Cost of Buying",   f"\\${buy_net_cost:,.0f}",
               help="All payments + closing costs + selling costs − net sale proceeds")
    tc2.metric(f"Net Cost of Renting",  f"\\${rent_net_cost:,.0f}",
               help="Total rent paid − investment gains on down payment opportunity cost")
    tc3.metric("Buying Advantage" if net_delta > 0 else "Renting Advantage",
               f"\\${abs(net_delta):,.0f}",
               delta="Buying wins" if net_delta > 0 else "Renting wins",
               delta_color="normal" if net_delta > 0 else "inverse")

    if net_delta > 0:
        st.success(f"Over {rvb_years_stay} years, **buying saves you approximately \\${net_delta:,.0f}** compared to renting — after accounting for selling costs and the investment return you'd earn on the down payment if you rented instead.")
    else:
        st.info(f"Over {rvb_years_stay} years, **renting saves you approximately \\${abs(net_delta):,.0f}** compared to buying at this price. "
                f"Try increasing the stay duration or adjusting appreciation — time in the home is usually the biggest lever.")

    # Cumulative cost chart
    cum_buy  = []
    cum_rent = []
    running_buy = rvb_buy_closing_cost + rvb_down_amt + rvb_funding_fee
    running_rent = 0.0
    invest_val = rvb_down_amt + rvb_buy_closing_cost
    bal_chart = rvb_loan_amt

    for m in range(n_months):
        running_buy  += rvb_total_own_mo
        running_rent += monthly_costs_rent[m]
        invest_val   *= (1 + rvb_invest_return / 12)
        i_p = bal_chart * rvb_monthly_rate
        p_p = rvb_mortgage_pi - i_p
        bal_chart -= p_p
        hv = rvb_home_price * (1 + rvb_appreciation) ** ((m + 1) / 12)
        equity = hv - bal_chart
        net_buy_cumulative  = running_buy  - (equity - hv * rvb_sell_closing)
        net_rent_cumulative = running_rent - (invest_val - (rvb_down_amt + rvb_buy_closing_cost))
        cum_buy.append(net_buy_cumulative)
        cum_rent.append(net_rent_cumulative)

    months_axis = list(range(1, n_months + 1))
    fig_rvb = go.Figure()
    fig_rvb.add_trace(go.Scatter(x=months_axis, y=cum_buy,  name="Buying (net true cost)", line=dict(color="#00aaff", width=2)))
    fig_rvb.add_trace(go.Scatter(x=months_axis, y=cum_rent, name="Renting (net true cost)", line=dict(color="#ff8844", width=2)))

    # Crossover point
    crossover = None
    for i in range(1, len(cum_buy)):
        if (cum_buy[i-1] > cum_rent[i-1]) != (cum_buy[i] > cum_rent[i]):
            crossover = i
            break
    if crossover:
        fig_rvb.add_vline(x=crossover, line_dash="dot", line_color="#00ff88",
                          annotation_text=f"Break-even: month {crossover} ({crossover//12}y {crossover%12}m)",
                          annotation_position="top right", annotation_font_color="#00ff88")

    fig_rvb.update_layout(
        title="Cumulative Net Cost: Buying vs. Renting",
        xaxis_title="Month",
        yaxis_title="Net True Cost ($)",
        yaxis_tickformat="$,.0f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        height=380,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_rvb, use_container_width=True)
    st.caption("Net true cost = total cash out − equity recovered (buy) or total rent − investment gains on down payment (rent). "
               "Lower is better. The crossover is your break-even point.")

    # ── SECTION 5: RENTAL SCENARIO ────────────────────────────────────────────
    st.divider()
    st.subheader("🏘️ What If I Rent It Out After I'm Done Living There?")
    st.caption("This section assumes you stop living in the home and convert it to a rental property. "
               "It calculates your return three ways — each adds one more layer of value.")

    with st.expander("⚙️ Rental Scenario Inputs & Assumptions", expanded=True):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            rvb_rental_income  = st.number_input("Expected Monthly Rent (\\$/month)", min_value=500, max_value=10_000,
                                                   value=int(rvb_market_rent * 1.05), step=50, key="rvb_rental_income")
            rvb_vacancy_rate   = st.slider("Vacancy Rate (%)", 0, 20, 8, 1, key="rvb_vacancy") / 100
            rvb_mgmt_rate      = st.slider("Property Management Fee (% of rent)", 0, 15, 8, 1, key="rvb_mgmt") / 100
        with rc2:
            rvb_capex_rate     = st.slider("CapEx / Major Repairs Reserve (% of rent)", 0, 15, 8, 1, key="rvb_capex") / 100
            rvb_rental_ins_mo  = st.number_input("Landlord Insurance (\\$/month)", 50, 400, 150, 10, key="rvb_rins")
            rvb_rental_prop_tax_same = st.checkbox("Use same property tax as above", value=True, key="rvb_rptax_same")
        with rc3:
            rvb_rental_years   = st.slider("How Long Do You Plan to Rent It Out? (years)", 1, 20, 5, key="rvb_ryears")
            rvb_rental_appr    = st.slider("Appreciation During Rental Period (%/yr)", 0.0, 8.0, 3.0, 0.25, key="rvb_rappr") / 100
            rvb_rental_income_growth = st.slider("Annual Rent Increase (%/yr)", 0.0, 6.0, 2.0, 0.25, key="rvb_rgrowth") / 100

    # Rental calculations
    # Starting point: end of stay period
    rvb_rental_start_balance    = balance          # remaining mortgage balance
    rvb_rental_start_home_val   = rvb_home_value_end

    rvb_rental_n_months = rvb_rental_years * 12
    rvb_rental_prop_tax_mo = rvb_prop_tax_mo  # same rate

    rent_income_mo   = float(rvb_rental_income)
    r_balance        = rvb_rental_start_balance
    r_home_val       = rvb_rental_start_home_val

    total_gross_rent       = 0.0
    total_mortgage_paid_r  = 0.0
    total_principal_r      = 0.0
    total_expenses_r       = 0.0

    for m in range(rvb_rental_n_months):
        # Income
        effective_rent = rent_income_mo * (1 - rvb_vacancy_rate)
        total_gross_rent += effective_rent

        # Mortgage
        i_r = r_balance * rvb_monthly_rate
        p_r = rvb_mortgage_pi - i_r
        r_balance -= p_r
        total_mortgage_paid_r  += rvb_mortgage_pi
        total_principal_r      += p_r

        # Operating expenses (excl. mortgage)
        mgmt     = effective_rent * rvb_mgmt_rate
        capex    = effective_rent * rvb_capex_rate
        vacancy_loss = rent_income_mo * rvb_vacancy_rate
        expenses = mgmt + capex + rvb_rental_ins_mo + rvb_rental_prop_tax_mo + rvb_maint_mo
        total_expenses_r += expenses

        if m % 12 == 11:
            rent_income_mo *= (1 + rvb_rental_income_growth)

    r_home_val_end   = rvb_rental_start_home_val * (1 + rvb_rental_appr) ** rvb_rental_years
    r_equity_end     = r_home_val_end - max(r_balance, 0)
    r_sell_cost      = r_home_val_end * rvb_sell_closing

    net_cash_flow    = total_gross_rent - total_expenses_r - total_mortgage_paid_r
    total_cash_invested = rvb_down_amt + rvb_buy_closing_cost + rvb_funding_fee  # original cash in

    # ROI 1: Cash flow only (passive income)
    if total_cash_invested > 0:
        roi_cashflow = (net_cash_flow / total_cash_invested) / rvb_rental_years * 100
    else:
        roi_cashflow = 0.0

    # ROI 2: Cash flow + mortgage paydown by tenants
    roi_paydown = ((net_cash_flow + total_principal_r) / total_cash_invested) / rvb_rental_years * 100 if total_cash_invested > 0 else 0.0

    # ROI 3: Cash flow + paydown + appreciation
    appreciation_gain = r_home_val_end - rvb_rental_start_home_val
    roi_total = ((net_cash_flow + total_principal_r + appreciation_gain) / total_cash_invested) / rvb_rental_years * 100 if total_cash_invested > 0 else 0.0

    annual_noi = (total_gross_rent - total_expenses_r) / rvb_rental_years
    cap_rate   = (annual_noi / rvb_rental_start_home_val) * 100 if rvb_rental_start_home_val > 0 else 0.0
    avg_monthly_cashflow = net_cash_flow / rvb_rental_n_months

    # Display rental results
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Avg Monthly Cash Flow",   f"\\${avg_monthly_cashflow:,.0f}/mo",
              delta="positive" if avg_monthly_cashflow >= 0 else "negative cash flow",
              delta_color="normal" if avg_monthly_cashflow >= 0 else "inverse")
    r2.metric("Cap Rate",                f"{cap_rate:.1f}%",
              help="Net Operating Income ÷ property value. 5–8% is typically considered healthy.")
    r3.metric("Est. Equity at Exit",     f"\\${r_equity_end - r_sell_cost:,.0f}",
              help="Home value minus remaining mortgage minus selling costs")
    r4.metric("Tenant Paydown (principal)", f"\\${total_principal_r:,.0f}",
              help="How much of your mortgage balance your tenants pay down")

    st.divider()
    st.subheader("Return on Investment — Three Ways to Look at It")
    st.caption("Each row adds one more source of return. The first row is the most conservative — only counting cash you actually receive.")

    roi_data = {
        "What's Included":        ["Cash flow only", "Cash flow + tenant mortgage paydown", "Cash flow + paydown + appreciation"],
        "Annual ROI":             [f"{roi_cashflow:.1f}%", f"{roi_paydown:.1f}%", f"{roi_total:.1f}%"],
        "Description":            [
            "Only passive income after all expenses & mortgage. The floor.",
            "Adds principal reduction by tenants — real wealth even if you break even on cash.",
            "Adds speculative appreciation. The ceiling — not guaranteed, but historically likely."
        ]
    }
    st.dataframe(pd.DataFrame(roi_data), use_container_width=True, hide_index=True)

    with st.expander("📋 Rental P&L Summary"):
        pnl_data = {
            "Item": [
                "Gross Rent Collected (adj. for vacancy)",
                "− Property Management",
                "− CapEx / Repairs Reserve",
                "− Landlord Insurance",
                "− Property Tax",
                "− Maintenance",
                "= Net Operating Income (NOI)",
                "− Mortgage Payments (P&I)",
                "= Net Cash Flow",
                "  + Tenant Principal Paydown",
                "  + Appreciation Gain (est.)",
                "= Total Wealth Created"
            ],
            "Total over Period": [
                f"${total_gross_rent:,.0f}",
                f"−${total_gross_rent * rvb_mgmt_rate:,.0f}",
                f"−${total_gross_rent * rvb_capex_rate:,.0f}",
                f"−${rvb_rental_ins_mo * rvb_rental_n_months:,.0f}",
                f"−${rvb_rental_prop_tax_mo * rvb_rental_n_months:,.0f}",
                f"−${rvb_maint_mo * rvb_rental_n_months:,.0f}",
                f"${annual_noi * rvb_rental_years:,.0f}",
                f"−${total_mortgage_paid_r:,.0f}",
                f"${net_cash_flow:,.0f}",
                f"+${total_principal_r:,.0f}",
                f"+${appreciation_gain:,.0f}",
                f"${net_cash_flow + total_principal_r + appreciation_gain:,.0f}",
            ]
        }
        st.dataframe(pd.DataFrame(pnl_data), use_container_width=True, hide_index=True)

    st.caption(
        "**Assumptions:** 30-year fixed mortgage. Appreciation compounds annually. "
        "Vacancy and CapEx are estimated percentages of gross rent. "
        "ROI is annualized over the rental hold period and uses original cash invested (down payment + closing costs + VA funding fee if applicable). "
        "Tax implications of rental income not modeled — consult a CPA."
    )

# --- GLOBAL FOOTER & DISCLAIMER ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; font-size: 0.85em; color: gray;'>
<b>Disclaimer:</b> This tool is for educational purposes only. I am not a financial advisor — but financial literacy isn't reserved for people with CFP after their name. Purposeful scrolling through r/personalfinance and r/MilitaryFinance, clicking some links, and reading for a weekend will get you further than you can possibly imagine. Where applicable, model assumptions are documented in the expandable sections throughout the app. Take charge of your money and own your future — the return on investment is 100%. Oh, and I'll take a smash burger with sautéed jalapeños and a cup that's 90% seltzer water with a splash of Coke.
</div>
""", unsafe_allow_html=True)
