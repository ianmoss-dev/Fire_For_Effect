# FIRE for Effect Baseline Cases

These cases are used to compare the rebuild against the legacy Streamlit app.

Status key:

- `captured`: input and expected legacy output recorded
- `needs legacy run`: input selected, output still needs to be captured from the Streamlit app

## Income Cases

### Case I-001: Enlisted CONUS With Dependents

Status: `captured`

Inputs:

- Rank: `E-5`
- Time in service: `6`
- ZIP: `28310`
- MHA: `NC182`
- Location name: `FORT BRAGG/POPE, NC`
- Dependents: `yes`
- OCONUS: `no`
- Dual military: `no`
- Special pays: none

Expected baseline outputs:

- Base pay: `$4,110.00/mo`
- BAH with dependents: `$1,806.00/mo`
- BAH without dependents: `$1,527.00/mo`
- BAS: `$515.00/mo`
- Housing label: `BAH`

### Case I-002: Officer CONUS With Dependents

Status: `captured`

Inputs:

- Rank: `O-3`
- Time in service: `8`
- ZIP: `92135`
- MHA: `CA038`
- Location name: `SAN DIEGO, CA`
- Dependents: `yes`
- OCONUS: `no`
- Dual military: `no`
- Special pays: none

Expected baseline outputs:

- Base pay: `$8,125.50/mo`
- BAH with dependents: `$4,518.00/mo`
- BAH without dependents: `$4,248.00/mo`
- BAS: `$360.00/mo`
- Housing label: `BAH`

### Case I-003: Enlisted CONUS Without Dependents

Status: `captured`

Inputs:

- Rank: `E-7`
- Time in service: `14`
- ZIP: `98433`
- MHA: `WA311`
- Location name: `TACOMA, WA`
- Dependents: `no`
- OCONUS: `no`
- Dual military: `no`
- Special pays: none

Expected baseline outputs:

- Base pay: `$5,657.40/mo`
- BAH with dependents: `$2,994.00/mo`
- BAH without dependents: `$2,376.00/mo`
- BAS: `$515.00/mo`
- Housing label: `BAH`

### Case I-004: Officer DC Metro With Dependents

Status: `captured`

Inputs:

- Rank: `O-4`
- Time in service: `12`
- ZIP: `22060`
- MHA: `DC053`
- Location name: `WASHINGTON, DC METRO AREA`
- Dependents: `yes`
- OCONUS: `no`
- Dual military: `no`
- Special pays: none

Expected baseline outputs:

- Base pay: `$9,888.30/mo`
- BAH with dependents: `$4,410.00/mo`
- BAH without dependents: `$3,855.00/mo`
- BAS: `$360.00/mo`
- Housing label: `BAH`

## OCONUS Cases

### Case O-001: OCONUS Germany

Status: `needs legacy run`

Inputs:

- Rank: `E-5`
- Time in service: `6`
- OCONUS: `yes`
- OHA location: `Germany - Grafenwohr / Vilseck`
- Dependents: `yes`
- Dual military: `no`
- COLA: `$0`
- Special pays: none

Expected baseline outputs:

- Capture from legacy app before extracting OHA logic.

## Retirement Cases

### Case R-001: Mid-Career Enlisted Retirement Solver

Status: `needs legacy run`

Inputs:

- Rank: `E-5`
- Time in service: `6`
- Current age: `26`
- Retirement age: `60`
- Current TSP balance: `$10,000`
- Target retirement spending: `$60,000/yr`
- TSP allocation: lifecycle/default app assumption
- Pension system: legacy app default

Expected baseline outputs:

- Required savings rate
- Monthly contribution target
- Pension estimate
- Nest egg target
- Monte Carlo success rate if run

## Budget Cases

### Case B-001: Manual Budget Summary

Status: `needs legacy run`

Inputs:

- Pay mode: manual estimate
- Take-home pay: `$6,000/mo`
- Fixed expenses: `$3,200/mo`
- Investments: `$600/mo`
- Guilt-free/flexible spending: `$1,200/mo`

Expected baseline outputs:

- Surplus
- Cash-flow chart values
- Report budget summary values

## Rent vs. Buy Cases

### Case H-001: VA Loan, Fort Liberty

Status: `needs legacy run`

Inputs:

- ZIP: `28310`
- BAH source: prefilled from app
- Market rent: `$1,900/mo`
- Home price: `$325,000`
- VA loan: `yes`
- Down payment: `0%`
- Interest rate: `6.5%`
- Years staying: `3`
- Appreciation: `3%`
- Maintenance: legacy app default
- Selling costs: legacy app default

Expected baseline outputs:

- Net cost of buying
- Net cost of renting
- Buying/renting advantage
- Break-even month, if any

