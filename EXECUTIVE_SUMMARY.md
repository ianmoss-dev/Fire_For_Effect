# F.I.R.E. for Effect — Executive Summary

## Motivation

Military compensation is arguably the most complex pay structure in any profession. A single service member may receive base pay, Basic Allowance for Housing (BAH), Basic Allowance for Subsistence (BAS), special and incentive pays, tax exclusions for combat zones, and a defined-benefit pension — all governed by separate rules, tables, and eligibility conditions. Despite this complexity, most service members cannot answer three foundational questions about their own finances:

> **What do I actually make? What do I need to save? Where is my money going?**

Existing tools address these questions in isolation, if at all. Paycheck calculators ignore savings targets. Retirement planners ignore military-specific compensation. Budgeting apps have no concept of BAH or the Blended Retirement System. No single tool integrates compensation, savings planning, and spending in a way that reflects the realities of military life.

F.I.R.E. for Effect was built to close that gap — a single, self-contained financial planning tool designed specifically for U.S. service members, requiring no account, no financial data upload, and no prior financial literacy.

---

## Approach

The application is built as a single-file Streamlit app with seven functional tabs, each addressing a distinct layer of financial understanding:

**Tab 1 — What You Make**
Calculates total military compensation (base pay, BAH, BAS, special pays) using live pay tables loaded from a structured JSON data file. BAH is resolved by duty station ZIP code. A projection chart extends compensation forward through 20 years of service, annotating promotion milestones drawn from primary-zone promotion timelines.

**Tab 2 — Retirement Savings Rate Solver**
The methodological core of the application. A binary search algorithm solves for the single constant savings rate — expressed as a percentage of base pay — that grows a user's current TSP balance to a target nest egg by their planned stop-work age. The solver runs against a month-by-month income schedule that incorporates projected promotions and a post-military civilian salary phase. A 1,000-trial parametric Monte Carlo simulation then stress-tests that rate against stochastic market returns drawn from calibrated Normal distributions for each TSP fund, deflated by user-selected inflation. The simulation reports a probability of success rather than a point estimate, explicitly accounting for sequence-of-returns risk. All model assumptions — promotion timelines, fund return parameters, the 4% safe withdrawal rule, pension calculation methodology, and actuarial pension present value inputs — are documented in an expandable section at the bottom of the tab.

**Tab 3 — Conscious Spending**
Users either enter their LES directly (capturing actual deductions) or use an estimate mode that applies 2025 federal tax brackets, standard deduction, and FICA to compute take-home pay. A structured budget framework allocates take-home across fixed costs, investments, and guilt-free spending. A Sankey diagram visualizes the full monthly cash flow from gross income through taxes to each spending category.

**Tab 4 — Know the Game**
An interactive financial literacy quiz covering five topic areas: debt and interest, emergency funds, budgeting, TSP and investing, the GI Bill, and the VA home loan. Each question includes a sourced explanation regardless of which answer is selected. Designed to be informative for any answer choice, not just the correct one.

**Tab 5 — The Way Ahead**
An eleven-step financial order of operations organized into Crawl / Walk / Run phases, each with an expandable action item, relevant links, and a checkbox. Progress is tracked and displayed.

**Tab 6 — Financial Plan PDF**
Generates a two-page downloadable PDF summarizing the user's compensation, budget allocation, savings rate, and a prioritized financial checklist. Built with FPDF2; budget chart rendered with matplotlib for BytesIO-compatible PDF embedding.

**Tab 7 — Feedback**
A form-submit feedback form routed to the developer.

Anonymous session analytics are logged to Google Sheets via the gspread API with user consent, capturing tab navigation and feature usage events without collecting any personal or financial data.

---

## Key Findings and Design Decisions

**The savings rate problem is solvable — but only with assumptions.** Most financial tools avoid projecting a specific savings rate because doing so requires making explicit assumptions about promotion timelines, fund returns, inflation, and post-military income. This application makes those assumptions explicit and transparent rather than avoiding the calculation. All assumptions are documented and intentionally conservative.

**Military compensation requires military-specific modeling.** BAH varies by ZIP code and dependent status. BAS changes at community boundaries, not by rank. Pension multipliers differ between BRS (2.0%) and Legacy High-3 (2.5%). Promotion timelines differ across officer, warrant, and enlisted communities. Generic financial tools that ignore these distinctions produce materially wrong outputs for service members.

**The Monte Carlo simulation is calibrated to the deterministic solver.** A known failure mode in parametric Monte Carlo is variance drag — the gap between arithmetic and geometric mean returns causes the median simulated outcome to diverge from the deterministic projection over long horizons. This application corrects for variance drag by deriving monthly arithmetic means from geometric targets, ensuring the simulation median converges to the solver output by construction. This makes the success probability a meaningful stress-test rather than an arbitrary number.

**Privacy by design.** No user data is stored. No account is required. BAH lookup, tax estimation, and savings rate calculations all run client-side within the Streamlit session. The only external write is an anonymous, consent-gated event log that records which features were used — not what numbers were entered.

---

## Recommendations

- **Verify contribution limit figures annually.** TSP employee contribution limits ($23,500 in 2025) and IRA limits ($7,000) are set by IRS guidance each fall. These figures are hardcoded and should be updated each year.
- **GI Bill transfer eligibility for ROTC and academy-commissioned officers** is nuanced and depends on commissioning source, service obligation, and prior service. The application intentionally does not assert specific year thresholds for these populations and directs users to VA.gov and the VA education counselor line (1-888-442-4551).
- **The 4% safe withdrawal rule** was originally validated for 30-year retirements. Military retirees who stop working in their 40s may face a 40+ year drawdown horizon, for which a lower withdrawal rate (3–3.5%) is increasingly supported in the literature. This is noted in the model assumptions but not enforced in the calculator.
- **Multipage refactor.** The current single-file architecture causes all tab widgets to execute on every Streamlit rerun, which can produce unexpected state interactions between tabs. Refactoring to Streamlit's multipage format would resolve session state sync issues and improve performance.

---

*F.I.R.E. for Effect is intended for educational purposes only and does not constitute financial advice. Model assumptions are documented throughout the application. Users are encouraged to consult a Certified Financial Planner for personalized guidance.*
