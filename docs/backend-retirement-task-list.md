# Backend Retirement Milestone Task List

Scope: finish the first retirement-backend milestone on `rebuild/web-api`.

Status key:

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete

## Tasks

- [x] Extract pension present value logic.
- [x] Add pension APV tests.
- [x] Extract TSP fund assumptions and lifecycle allocation.
- [x] Add fund allocation and blended-return tests.
- [x] Extract savings-rate solver.
- [x] Add solver tests.
- [x] Add retirement API request/response models.
- [x] Add retirement API endpoint.
- [x] Add retirement endpoint smoke tests.
- [x] Run full API test suite.
- [x] Update parity checklist.
- [x] Commit and push milestone.

## Checks

Run from `api/`:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Latest result:

- `39` tests passing.
- Existing income API tests still pass.
- Promotion and pension basics still pass.
- Pension APV tests pass.
- TSP fund/lifecycle tests pass.
- Savings-rate solver tests pass.
- Retirement API smoke tests pass.
