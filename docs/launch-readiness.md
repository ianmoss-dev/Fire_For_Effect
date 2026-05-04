# Launch Readiness

Reviewed: 2026-05-04

Branch reviewed: `rebuild/web-api`

## Verdict

- Internal staging: `Go`
- Limited soft launch to friendly testers: `Conditional`
- Public launch: `No-go yet`

## What Passed

- API unit and endpoint tests pass locally: `49` tests.
- Web app lint passes.
- Web production build passes.
- Local runtime smoke passed for:
  - `GET /health`
  - `POST /income/calculate`
  - `POST /budget/summary`
  - `POST /retirement/solve-savings-rate`
  - `POST /retirement/monte-carlo`
- Render config exists in `render.yaml`.
- Cloudflare Pages setup is documented in `docs/deployment.md`.
- CI workflow exists for API tests and web lint/build.

## What Blocks Public Launch

- Responsive smoke testing is not complete for `390px`, `430px`, and desktop.
- Legacy parity is still incomplete in `docs/parity-checklist.md`.
- The MVP does not yet cover several legacy features:
  - special pays
  - COLA input
  - dual-military or spouse-service-member handling
  - LES-style budget entry
  - tax-estimate mode parity
  - PDF or downloadable plan
  - rent-vs-buy flow
  - analytics and feedback flow
- The launch checklist does not yet include a deployed staging URL verification step.

## Risk Notes

- This version is appropriate for a scoped MVP test if expectations are clear.
- It is not ready to claim full parity with the legacy Streamlit app.
- If launched publicly now, users may assume omitted military-specific cases are covered when they are not.

## Recommended Next Steps

1. Deploy backend to Render staging.
2. Deploy frontend to Cloudflare Pages staging with `VITE_API_BASE_URL` set.
3. Run manual viewport checks at `390px`, `430px`, and desktop.
4. Click through the full user flow on staging.
5. Decide whether to launch as:
   - a narrow MVP with explicit scope limits
   - or a parity-focused release after another feature pass

## Minimum Public Launch Checklist

- Responsive smoke pass completed.
- Staging URL verified end to end.
- Final custom domain added to `CORS_ORIGINS`.
- Scope disclaimer added to launch copy.
- At least one real-world sample scenario verified against the legacy app.
