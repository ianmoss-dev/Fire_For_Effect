# FIRE for Effect Migration Plan

## Decision

Keep this project in the current `Fire_For_Effect` repo, but build the new product beside the legacy Streamlit app instead of editing the monolith in place.

This gives us the best balance:

- We preserve the current working version for reference.
- We keep git history, source data, docs, and presentation assets together.
- We can compare new outputs against the old Streamlit calculations before replacing anything.
- We avoid creating a second repo that drifts away from the original feature set.

Do not delete `app.py` during the migration. Treat it as the legacy reference implementation until the new app reaches parity.

Recommended git setup:

- Tag the current app as `legacy-streamlit-v1`.
- Create a long-running branch named `rebuild/web-api`.
- Keep `main` deployable until the replacement is ready.
- Merge the rebuild only after parity checks pass.

## Product Goal

Rebuild FIRE for Effect as a stable, mobile-first financial planning app for military users.

The new version should:

- Support multiple users without Streamlit session-state instability.
- Preserve the existing calculation engines and financial functionality.
- Make state explicit and predictable across screens.
- Improve mobile visualization and interaction quality.
- Share a recognizable visual family with Napkin Math.
- Be easier to test, host, monitor, and extend.

## Non-Goals

Avoid these until the foundation is stable:

- New financial features that are not already in the current app.
- Login, user accounts, or saved cloud profiles.
- Rebuilding every visualization at once.
- Rewriting validated math without parity tests.
- Expanding analytics beyond basic privacy-safe events.

## Recommended Architecture

Use a small web app with a Python calculation API.

Frontend:

- `Vite + React`
- Mobile-first screens
- Shared visual style with Napkin Math
- Client-side state for the active planning session
- Local storage for optional draft persistence

Backend:

- `FastAPI`
- Stateless calculation endpoints
- Pydantic request and response models
- Pure Python domain modules extracted from the Streamlit app

Hosting:

- Frontend: Cloudflare Pages, Netlify, or Vercel
- Backend: Render, Fly.io, Railway, Azure App Service, or AWS App Runner
- Static data: bundled in the API or served as versioned JSON

A single Python web host can also serve both API and built frontend later, but separate frontend/backend hosting is cleaner for mobile UI iteration.

## Target Repo Structure

```text
Fire_For_Effect/
  legacy/
    streamlit_app.py
  data/
    military_data.json
  api/
    app/
      main.py
      models/
        income.py
        retirement.py
        budget.py
        rent_vs_buy.py
        report.py
      domain/
        military_pay.py
        oha.py
        promotion.py
        pension.py
        retirement_solver.py
        monte_carlo.py
        budget.py
        rent_vs_buy.py
        recommendations.py
      services/
        pdf.py
        analytics.py
      data/
        loaders.py
    tests/
      test_income_parity.py
      test_retirement_parity.py
      test_budget_parity.py
      test_rent_vs_buy_parity.py
    pyproject.toml
  web/
    src/
      app/
      components/
      screens/
      state/
      charts/
      styles/
      api/
    package.json
  docs/
    parity-checklist.md
    visual-system.md
    deployment.md
```

## State Model

State should be explicit, typed, and grouped by product area.

Initial state groups:

- `profile`: rank, time in service, age, household, dependents, ZIP, OCONUS status
- `income`: base pay, BAH/OHA, BAS, COLA, special pays, spouse/dual-military pay
- `retirement`: current TSP, savings rate, fund allocation, retirement age, target income
- `budget`: take-home pay, fixed expenses, investments, flexible spending, surplus
- `simulation`: Monte Carlo inputs and outputs
- `checklist`: crawl/walk/run completion state
- `report`: generated plan inputs and metadata
- `analytics`: consent, anonymous session ID, event flags

Frontend state rule:

- The browser owns the active planning session.
- The API receives complete inputs and returns calculated outputs.
- The backend should not depend on server-side session state for MVP.

This avoids the Streamlit rerun/session-state problem and makes multi-user hosting much simpler.

## Visual System

Mirror Napkin Math enough that the apps feel related, while letting FIRE feel more technical and planning-focused.

Shared family traits:

- Fonts: `DM Sans` for interface text, `Playfair Display` for major headings and large numeric moments
- Palette:
  - Navy: `#1B3A6B`
  - Blue: `#2E75B6`
  - Gold: `#C9A84C`
  - Light blue: `#D5E8F0`
  - Light gold: `#FEF9EE`
  - Gray: `#595959`
  - App background: `#F8F9FA`
  - Green: `#2E7D32`
  - Red: `#C62828`
- Mobile shell: start with a 430px-friendly layout, then expand deliberately for desktop.
- Tone: direct, useful, plain English.

FIRE-specific design direction:

- More dashboard-like than Napkin Math.
- Use compact sections, clear metrics, and progressive detail.
- Charts must work first on mobile, then scale up.
- Avoid giant Streamlit-style walls of controls.
- Prioritize one job per screen.

## Functionality Parity Checklist

Current Streamlit features that must be preserved or intentionally deferred:

- Income calculator
- Base pay lookup by rank and time in service
- BAH lookup by ZIP, rank, and dependency status
- OCONUS/OHA flow
- BAS calculation
- COLA and special pay handling
- Dual-military/spouse pay handling
- Tax estimate or LES-style take-home modeling
- Retirement savings-rate solver
- Promotion timeline projection
- High-3/BRS pension calculation
- Pension present value calculation
- TSP fund allocation assumptions
- Monte Carlo simulation
- Fund comparison
- Budget and cash-flow breakdown
- Sankey or replacement cash-flow visualization
- Education modules
- Crawl/walk/run checklist
- PDF or downloadable plan
- Feedback capture
- Rent vs. buy calculator
- Rental property scenario
- Anonymous analytics consent and event logging

Each feature should be marked as one of:

- `Keep in MVP`
- `Keep but redesign`
- `Defer to v2`
- `Remove intentionally`

Nothing should disappear silently.

## Migration Phases

### Phase 0: Preserve and Baseline

Tasks:

- Create `legacy/streamlit_app.py` as a copy of current `app.py`.
- Tag the repo as `legacy-streamlit-v1`.
- Capture screenshots of the current tabs.
- Record sample inputs for income, retirement, budget, and rent-vs-buy.
- Save expected outputs from the legacy app for parity tests.
- Add `docs/parity-checklist.md`.

Exit criteria:

- We can run or inspect the old app at any point.
- We have sample cases for the core financial engines.

### Phase 1: Extract Data and Domain Logic

Tasks:

- Move `military_data.json` into `data/`.
- Extract data loading into `api/app/data/loaders.py`.
- Extract military pay calculations into `api/app/domain/military_pay.py`.
- Extract OHA logic into `api/app/domain/oha.py`.
- Extract promotion logic into `api/app/domain/promotion.py`.
- Extract pension logic into `api/app/domain/pension.py`.
- Extract savings-rate solver into `api/app/domain/retirement_solver.py`.
- Extract Monte Carlo logic into `api/app/domain/monte_carlo.py`.
- Extract budget logic into `api/app/domain/budget.py`.
- Extract rent-vs-buy logic into `api/app/domain/rent_vs_buy.py`.

Exit criteria:

- Extracted functions can run without importing Streamlit.
- No domain module depends on `st.session_state`.
- Basic unit tests pass for each extracted module.

### Phase 2: Create Typed API Contract

Tasks:

- Add FastAPI app shell.
- Add Pydantic models for each calculator.
- Add endpoints:
  - `POST /income/calculate`
  - `POST /retirement/solve`
  - `POST /retirement/monte-carlo`
  - `POST /budget/summary`
  - `POST /rent-vs-buy/compare`
  - `POST /report/generate`
- Add API-level validation and error messages.
- Add parity tests comparing API outputs to legacy sample outputs.

Exit criteria:

- API runs locally.
- Swagger/OpenAPI docs are generated.
- Core endpoints match legacy calculations within agreed tolerances.

### Phase 3: Build Mobile-First Frontend

Tasks:

- Scaffold Vite + React app in `web/`.
- Add Napkin Math family tokens and typography.
- Build app shell, screen navigation, and state store.
- Build screens:
  - Start/consent
  - Profile and pay inputs
  - Income result
  - Retirement inputs
  - Retirement result
  - Budget inputs
  - Cash-flow result
  - Checklist
  - Plan summary
  - Rent vs. buy
- Connect screens to API endpoints.
- Persist draft state locally.

Exit criteria:

- User can complete the core flow on mobile.
- Refreshing the page does not wipe the current draft unless the user starts over.
- UI does not depend on hidden tab execution.

### Phase 4: Rebuild Visualizations

Tasks:

- Replace Streamlit charts with responsive React charts.
- Prioritize mobile charts:
  - Income composition
  - Monthly cash-flow breakdown
  - Retirement projection
  - Monte Carlo range
  - Rent-vs-buy comparison
- Avoid dense desktop-first charts on small screens.
- Add summary-first chart views with expandable detail.

Exit criteria:

- Charts are readable at 390px mobile width.
- Every chart has a clear takeaway metric.
- Desktop layout enhances the mobile design instead of replacing it.

### Phase 5: Report, Analytics, and Deployment

Tasks:

- Rebuild downloadable plan generation.
- Decide whether PDF is generated by backend or frontend.
- Replace Google Sheets logging with a safer analytics path.
- Keep analytics consent explicit.
- Add deployment docs for frontend and backend.
- Add environment variable documentation.
- Deploy staging.

Exit criteria:

- Staging app works end to end.
- API health check is live.
- No secrets are committed.
- Analytics failures cannot break the user experience.

### Phase 6: Cutover

Tasks:

- Complete parity checklist.
- Run mobile and desktop smoke tests.
- Run build/test commands.
- Review financial disclaimers.
- Decide what legacy features remain deferred.
- Update README.
- Merge rebuild branch into `main`.
- Deploy production.

Exit criteria:

- New app covers the agreed MVP.
- Legacy app remains available for comparison.
- Production deployment has a rollback path.

## Testing Strategy

Test the math before polishing the interface.

Minimum tests:

- Base pay lookup returns expected values.
- BAH lookup handles ZIP to MHA mapping correctly.
- OHA fallback behavior is explicit.
- Savings-rate solver returns stable values for sample cases.
- Pension calculations match legacy outputs.
- Monte Carlo returns deterministic results when seeded.
- Budget summary matches legacy sample inputs.
- Rent-vs-buy comparison matches legacy sample inputs.
- API validation rejects incomplete or invalid payloads.

Use fixtures based on real app scenarios:

- Single enlisted member CONUS
- Officer with dependents CONUS
- OCONUS service member
- Dual-military household
- Member with special pays
- Member close to retirement
- Rent-vs-buy with VA loan

## Hosting Recommendation

For MVP:

- Frontend on Cloudflare Pages or Vercel.
- Backend on Render or Fly.io.
- API remains stateless.
- No login required.
- Local browser storage preserves drafts.

For later:

- Add Postgres if users need saved plans across devices.
- Add user accounts only after the anonymous MVP is stable.
- Move analytics to a proper event store or privacy-first analytics service.

## First Implementation Tasks

Start here:

- Add `legacy/streamlit_app.py`.
- Add `docs/parity-checklist.md`.
- Add `api/app/domain/` and `api/app/models/`.
- Extract data loading and base pay lookup first.
- Add the first parity test against known base pay values.
- Scaffold the FastAPI app after the first extracted module passes.

This keeps the migration honest: preserve, extract, test, then rebuild the interface.

