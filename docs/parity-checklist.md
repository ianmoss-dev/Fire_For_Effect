# FIRE for Effect Parity Checklist

Use this checklist to make sure the rebuild does not lose functionality from the current Streamlit app.

Status key:

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete
- `[d]` Deferred intentionally
- `[r]` Removed intentionally

## Baseline

- [x] Legacy Streamlit app copied to `legacy/streamlit_app.py`
- [x] Legacy repo state tagged as `legacy-streamlit-v1`
- [x] Sample input cases captured
- [ ] Expected legacy outputs captured
- [ ] Screenshots captured for current tabs
- [ ] Parity tolerances defined for each calculator

## Income

- [ ] Rank and time-in-service input
- [x] Base pay lookup
- [x] BAH lookup by ZIP/MHA
- [x] Dependency-status handling
- [x] BAS calculation
- [x] OCONUS/OHA flow
- [x] OHA location lookup
- [ ] COLA input
- [ ] Special pay inputs
- [ ] Dual-military household handling
- [ ] Spouse service-member pay handling
- [x] Gross monthly compensation output
- [ ] Monthly/annual pay breakdown
- [x] Taxable vs non-taxable compensation distinction

## Retirement

- [ ] Current TSP balance input
- [ ] Current age input
- [ ] Retirement age input
- [ ] Retirement income target input
- [x] Promotion timeline projection
- [x] Future base-pay schedule
- [x] High-3 pension calculation
- [x] BRS pension calculation
- [x] Pension present-value calculation
- [x] Required savings-rate solver
- [ ] TSP fund allocation input
- [x] TSP fund assumptions
- [ ] Fund comparison
- [x] Monte Carlo simulation
- [x] Monte Carlo success rate
- [ ] Monte Carlo chart
- [ ] Scenario output summary

## Budget

- [ ] LES-style income entry
- [ ] Estimated tax mode
- [ ] Extra income streams
- [x] Take-home pay output
- [x] Fixed expenses
- [x] Investments
- [x] Flexible spending
- [x] Surplus calculation
- [~] Cash-flow visualization
- [x] Mobile-friendly cash-flow replacement for Sankey chart
- [x] Budget summary for report

## Education and Checklist

- [ ] Know-the-game education modules
- [ ] SCRA content
- [ ] VA loan content
- [ ] GI Bill transferability content
- [ ] TSP Lifecycle content
- [ ] Crawl/walk/run checklist
- [ ] Checklist progress state
- [ ] Recommendation or next-step summary

## Report

- [ ] On-screen plan preview
- [ ] PDF or downloadable plan generation
- [ ] Income snapshot in plan
- [ ] Retirement target in plan
- [ ] Monte Carlo result in plan
- [ ] Budget summary in plan
- [ ] Checklist in plan
- [ ] Disclaimer in plan

## Rent vs. Buy

- [ ] Duty station ZIP input
- [ ] BAH prefill
- [ ] Rent input
- [ ] Home price input
- [ ] VA loan option
- [ ] Down payment input
- [ ] Interest-rate input
- [ ] Property tax input
- [ ] Insurance input
- [ ] Maintenance estimate
- [ ] HOA and PMI handling
- [ ] Buying vs renting cost comparison
- [ ] Break-even timeline
- [ ] Rental conversion scenario
- [ ] Rental income input
- [ ] Vacancy, management, and CapEx assumptions
- [ ] Rental cash-flow output
- [ ] ROI summary

## Analytics and Feedback

- [ ] Consent gate
- [ ] Anonymous session identifier
- [ ] Device type detection
- [ ] Event logging
- [ ] Feedback capture
- [ ] Analytics failures do not affect app flow
- [ ] No personal financial data logged

## Mobile UX

- [ ] 390px viewport smoke test
- [ ] 430px viewport smoke test
- [ ] Desktop viewport smoke test
- [ ] Inputs fit without horizontal scrolling
- [ ] Charts have mobile summary states
- [ ] Navigation is one-screen-at-a-time
- [ ] No dense tab wall on mobile
