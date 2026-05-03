# FIRE for Effect Rebuild Execution Checklist

Status key:

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete
- `[d]` Deferred intentionally

## Backend

- [x] Preserve legacy Streamlit app.
- [x] Extract military data loading.
- [x] Extract base pay, BAS, and BAH.
- [x] Extract OHA.
- [x] Add income API endpoint.
- [x] Add income API smoke tests.
- [x] Extract promotion and pension basics.
- [x] Extract pension present value.
- [x] Extract TSP fund assumptions.
- [x] Extract savings-rate solver.
- [x] Add savings-rate API endpoint.
- [x] Extract Monte Carlo simulation.
- [x] Add Monte Carlo API endpoint.
- [x] Extract budget/cash-flow summary.
- [x] Add budget API endpoint.
- [x] Add deployment configuration.

## Frontend

- [ ] Scaffold React/Vite app.
- [ ] Add Napkin Math family visual tokens.
- [ ] Add mobile-first app shell.
- [ ] Wire income calculator screen to API.
- [ ] Wire retirement solver screen to API.
- [ ] Add Monte Carlo result view.
- [ ] Add budget/cash-flow screen.
- [ ] Add plan summary screen.
- [ ] Run mobile and desktop build checks.

## Checks

- [x] Backend tests: `39` passing before Monte Carlo extraction.
- [x] Backend tests after Monte Carlo.
- [x] Backend tests after budget.
- [ ] Frontend build.
- [ ] Frontend responsive smoke check.
