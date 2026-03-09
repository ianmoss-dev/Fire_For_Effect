F.I.R.E. for Effect is a comprehensive, single-page Streamlit web application built specifically for U.S. military service members. It serves as an end-to-end financial planning tool that demystifies military compensation, calculates precise retirement savings rates, visualizes monthly cash flow, and generates a personalized, downloadable financial plan.

Technical Architecture
Framework: Python-based Streamlit application.

State Management: Utilizes a single-file architecture, relying heavily on st.session_state to persist data, mathematical outputs, and charts seamlessly across its 7-tab layout.

Key Libraries: pandas and numpy for data/math, plotly and matplotlib for interactive and static visualizations, fpdf2 for on-the-fly document generation, and gspread for backend analytics.

External Data Dependencies: Requires a local military_data.json file containing DOD base pay tables, BAH rates, and ZIP-to-MHA mappings.

Core Features & Engines
1. Military Income Calculator (Tab 1)
Accurately reconstructs a service member's gross and net pay. It takes Rank, Time in Service (TIS), and ZIP code, then calculates Base Pay, Basic Allowance for Housing (BAH), Basic Allowance for Subsistence (BAS), and applies toggles for various special and incentive pays (e.g., Jump, Flight, Dive, FLPB).

2. Retirement Solver & Monte Carlo Simulator (Tab 2)
The mathematical heart of the application. It goes beyond simple compounding:

Promotion Projections: Projects future income based on standard military promotion timelines.

Pension Valuation: Calculates High-3/BRS pension estimates and determines their Actuarial Present Value using SSA 2022 Period Life Tables.

Savings Rate Solver: Uses a binary search algorithm to calculate the exact percentage of base pay the user must contribute to their Thrift Savings Plan (TSP) to hit their retirement goals.

Parametric Monte Carlo: Runs 1,000 simulated market scenarios drawing on historical TSP fund metrics (C, S, I, F, G funds) to show the user the probability of success based on market volatility and timing risk.

3. Conscious Spending & Cash Flow Visualization (Tab 3)
Allows users to either precisely mirror their Leave and Earnings Statement (LES) line-by-line or use an algorithmic tax estimation. It deducts fixed costs and investments to reveal "Guilt-Free" spending limits. The output is visualized via an interactive Plotly Sankey diagram, giving users a clear map of their financial architecture.

4. Education & Execution Checklists (Tabs 4 & 5)
Features interactive Q&A modules addressing critical military-specific financial nuances—such as SCRA protections, VA Home Loans, GI Bill transferability, and TSP Lifecycle funds. It translates these concepts into an 11-step "Crawl, Walk, Run" actionable checklist.

5. Automated PDF Report Generation (Tab 6)
Aggregates all session state data—including the income snapshot, retirement targets, the customized Monte Carlo chart, and budget metrics—and compiles them into a structured PDF using fpdf2. The PDF is generated entirely in-memory and offered as a direct download.

Telemetry & Analytics
The app includes a custom, fire-and-forget logging function. Once a user passes a mandatory consent gate, it generates an anonymous SHA-256 hashed user ID and logs basic interactions (tab visits, simulation runs, PDF downloads) to a Google Sheet via a GCP service account. No personally identifiable financial data is captured
