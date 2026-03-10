# F.I.R.E. for Effect — Executive Summary

## Problem Statement

Military compensation is among the most structurally complex pay systems in any profession. A single service member may draw base pay, Basic Allowance for Housing (BAH), Basic Allowance for Subsistence (BAS), special and incentive pays, and a defined-benefit pension — each governed by separate eligibility rules, pay tables, and tax treatment. Despite this complexity, no integrated tool existed that could tell a service member what they actually earn, what they need to save to retire, and where their money is going — in one place, without an account, and calibrated to military-specific compensation structures.

This project builds that tool. The computational challenge is not trivial: answering "what savings rate do I need?" requires modeling promotion-driven income growth, TSP fund allocations, inflation, a military pension, and a post-military civilian income phase — all integrated into a single solvable system.

---

## Data Sources and Curation

All compensation data lives in a single structured JSON file (`military_data.json`) with three top-level keys:

**`base_pay`**
Sourced from official DFAS military pay tables. Structured as a nested lookup: `rank → years-of-service bracket → monthly dollar amount`. The TIS brackets follow the actual pay table breakpoints (0, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20+ years), allowing the application to snap any fractional TIS value to the correct pay cell without interpolation.

**`bah_rates`**
BAH varies by Military Housing Area (MHA), rank, and dependent status. Sourced from the DoD BAH rate tables. Structured as: `MHA code → rank → with/without dependents → monthly dollar amount`. There are over 300 MHA codes covering the continental U.S., Hawaii, Alaska, and overseas locations.

**`zip_to_mha`**
The bridging layer between a user-entered ZIP code and the BAH table. Curated from DoD's ZIP-to-MHA mapping file, which is not exposed in a clean API format and required manual parsing and normalization. Each ZIP entry resolves to an MHA code, which the application then uses to look up the correct BAH rate. This is the most fragile part of the data pipeline — ZIP code boundaries shift, and new installations occasionally fall outside the published mapping.

**Curation decisions:**
- Pay tables are loaded once at startup via `@st.cache_data`, eliminating redundant file reads on every Streamlit rerun
- All lookups use floor-snapping (highest bracket not exceeding current TIS) rather than interpolation, which matches how DFAS actually calculates pay
- BAH fallback: when a ZIP is not found, the application warns the user and allows manual entry rather than silently defaulting to a wrong value

**TSP fund return parameters** are not stored in the JSON but are hardcoded as `FUND_STATS` — inception-to-date geometric mean CAGRs and annualized standard deviations sourced from tspfolio.com (through March 2026). These feed both the deterministic solver and the Monte Carlo simulation.

---

## Computational Engines

### 1. Savings Rate Solver

The core question — *what percentage of my base pay do I need to save?* — is solved via **binary search** over the savings percentage, running 60 iterations to converge to machine precision.

The solver operates on a month-by-month income schedule that concatenates two phases: a military phase using `build_monthly_base_pay_schedule()` (which walks the promotion timeline forward from current rank and TIS) and a civilian phase using a user-entered expected salary. At each month, the algorithm compounds the running balance by a real return rate derived from the user's TSP fund allocation, then adds the contribution for that month:

```
balance(m+1) = balance(m) × (1 + real_rate(m)) + savings_pct × income(m)
```

The return path uses a gliding allocation — if L-fund weight is non-zero, the sub-allocation shifts toward bonds and G-fund as retirement approaches, mirroring actual TSP Lifecycle fund behavior. The effective rate therefore changes every month of the projection rather than holding a static assumption.

The target nest egg is derived from the 4% safe withdrawal rule applied to the income gap not covered by the military pension: `(monthly_goal - pension) × 12 / 0.04`. The solver finds the savings percentage where the terminal balance equals this target exactly.

**Why binary search:** The balance function is monotonically increasing in savings percentage, guaranteeing a unique solution. A closed-form solution would require simplifying the income schedule to a constant, which would be materially wrong for users whose pay changes at promotions or career transitions.

### 2. Monte Carlo Simulation

The solver produces a deterministic rate. The Monte Carlo stress-tests it against 1,000 stochastic market scenarios to produce a probability of success — the fraction of trials where the portfolio reaches or exceeds the nest egg target by the user's planned stop-work age.

Each trial draws independent monthly returns from `Normal(μ, σ)` for each TSP fund, applies the user's allocation weights, deflates by inflation, and compounds forward. The key implementation decision was **parametric sampling** (drawing fresh returns each trial) rather than pool sampling (resampling a fixed historical window). Pool sampling with a fixed seed produced severe bias — the S-fund generated an 8.6% success rate against an expected ~55% — because the fixed pool's sequence dominated the outcome. Parametric sampling eliminates this by construction.

A second calibration decision: the monthly arithmetic mean used in sampling is derived as `geo_mean + σ²/2` (variance drag correction). Without this, the expected geometric return of the simulated paths falls below the target CAGR, causing the MC median to diverge from the solver projection over long horizons. With the correction, the simulation median converges to the deterministic solver output — meaning the success probability measures genuine market risk, not model miscalibration.

The simulation runs fully vectorized using NumPy, with pre-allocated result arrays and array-broadcasting for the fund return draws, keeping 1,000 trials fast enough to run interactively on each Streamlit rerun.

### 3. Sankey Diagram (Cash Flow Architecture)

The Sankey diagram visualizes the full monthly cash flow from gross income through taxes to each spending category, built using **Plotly's `go.Sankey`**.

Plotly was chosen over Altair (also imported) for two reasons: native Streamlit rendering without an intermediate transform step, and link-level color control that gives each flow a distinct visual identity. The diagram adapts to the user's data entry path — in LES mode, tax flows use actual deduction figures; in estimate mode, they use the computed federal bracket and FICA estimates. All node values are floored at `0.1` to prevent Plotly from collapsing zero-value links in ways that break the diagram layout.

The fixed seven-node topology (Gross Income → Taxes, Gross Income → Take-Home → Fixed Costs / Investments / Guilt-Free / Surplus) makes the spending decision visible as a proportion of total income rather than just a dollar amount — which is the behaviorally relevant framing for a budgeting tool.

---

## Visualizations

| Chart | Library | Rationale |
|---|---|---|
| Projected compensation (stacked bar) | Plotly | Interactive hover; annotation layer marks promotion milestones directly on bars |
| TSP fund growth explorer (line) | Plotly | Multi-trace with confidence bands; hover shows per-fund value at any age |
| Monte Carlo fan chart (line) | Plotly | Percentile bands (10th/50th/90th) show distribution of outcomes; vertical success marker |
| Savings rate explorer (line) | Plotly | Real-time slider interaction; shows how rate changes affect retirement age |
| Monthly cash flow (Sankey) | Plotly | Flow topology makes proportional allocation visible in a way pie or bar charts cannot |
| Budget bar chart (PDF only) | Matplotlib | Matplotlib writes to a `BytesIO` buffer that FPDF2 embeds as an image; Plotly cannot |

Plotly was selected as the primary visualization library for all on-screen charts because it renders natively in Streamlit, supports the dark theme used throughout, and handles interactivity without additional JavaScript. Matplotlib is retained exclusively for the PDF export pipeline where a buffer-compatible renderer is required — the only use case where it outperforms Plotly in this application.

---

## Key Findings and Results

- **A single solvable savings rate exists for most service members.** The binary search converges for any valid input combination. For a typical O-2 at 3 years TIS targeting $8,000/month in retirement, the solver returns rates in the 12–18% range depending on assumed civilian salary — significantly higher than the 5% minimum to capture the BRS match, which most service members treat as their savings ceiling.

- **Sequence-of-returns risk is the dominant source of outcome variance.** Monte Carlo results consistently show that the spread between the 10th and 90th percentile outcomes is driven primarily by early-career market conditions, not total return. This is the insight the simulation is designed to surface.

- **BAH frequently exceeds base pay for mid-career officers in high cost-of-living markets.** The compensation projection chart makes this visible in a way that MyPay does not — BAH at O-3/O-4 in markets like Monterey, San Diego, or Washington D.C. can account for more than half of total compensation, with meaningful implications for post-military financial planning.

---

## Recommendations and Limitations

- **TSP contribution limits require annual updates.** The $23,500 employee limit and $7,000 IRA limit are hardcoded. These change each fall via IRS guidance and should be parameterized or loaded from a config file rather than edited manually each year.

- **The 4% safe withdrawal rate was validated for 30-year retirements.** Military retirees who stop working in their early 40s face a 40+ year drawdown horizon. Literature increasingly supports 3–3.5% for these cases. The current model uses 4% uniformly and documents this in the assumptions expander but does not adjust based on horizon length.

- **The ZIP-to-MHA mapping is the most fragile data dependency.** DoD updates BAH rates and MHA boundaries annually. A production version should pull from a maintained API or at minimum version-stamp the JSON with the effective date so users know when the data was last current.

- **Multipage Streamlit refactor.** The single-file architecture causes all tab widgets to execute on every rerun, creating potential state interactions between tabs. Streamlit's native multipage format would isolate tab state and improve performance at scale.

-**Rent vs. buy calculator.** The VA Loan section explains the transaction costs and break-even logic of homeownership, but stops short of a personalized calculation. A dedicated rent vs. buy module — taking inputs for home price, expected tenure, interest rate, and local rent — would let service members run the numbers for their specific duty station rather than reasoning from a generic example. Given PCS frequency, this is one of the highest-stakes financial decisions in a military career.
-**Sequence-of-returns Monte Carlo during drawdown.** The current simulation models the accumulation phase only. A drawdown module would allow a user to input their nest egg at retirement, select a monthly withdrawal amount, and toggle portfolio allocation across standard presets (90/10, 80/20, 60/40, 40/60, 20/80 stocks-to-bonds) to see how allocation affects the probability of portfolio survival over a 30–40 year retirement. This would directly surface sequence-of-returns risk — the finding that early bear markets in retirement are far more damaging than late ones — and give users a concrete reason to consider glide-path adjustments as they approach and enter retirement.
