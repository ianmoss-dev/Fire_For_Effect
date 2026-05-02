# FIRE for Effect Analytics Plan

## Goal

Track product adoption, feature use, geographic spread, reliability, and launch-channel performance without collecting personal financial inputs.

Do not track:

- Debt amounts
- Budget amounts
- Income amounts
- Retirement balances
- TSP allocations
- Names, emails, phone numbers, DoD IDs, or account identifiers
- Full street addresses
- Free-text financial details

## Current Streamlit Issue

The current Google Sheets tracker can fail silently.

Known risks in `app.py`:

- `get_gsheet()` returns `None` on any exception.
- `log_event()` ignores all append failures.
- The app depends on `st.secrets["gcp_service_account"]`.
- The Google Sheet must be shared with the service account email.
- Events only write after the consent gate is accepted.
- ZIP is pulled from `tab1_zip`, so early session events may not include ZIP yet.

Before relying on the existing tracker, add visible debug logging in development and a small health check event.

## Privacy Position

Use privacy-by-design rules:

- Collect only data needed for product decisions.
- Keep event records short and structured.
- Keep a clear consent screen.
- Make ZIP collection explicit.
- Avoid combining ZIP with financial details.
- Avoid raw IP collection.
- Avoid precise location collection.
- Set a retention window.

Recommended retention:

- Raw events: 12 months
- Aggregated geography/adoption reports: indefinite
- Error logs: 90 days unless needed for active debugging

## Session Model

Use one anonymous session ID per browser session.

Recommended fields:

- `event_id`: random UUID
- `session_id`: random UUID stored locally
- `visitor_id`: optional anonymous ID stored locally
- `timestamp_utc`
- `event_name`
- `screen`
- `feature`
- `source`
- `campaign`
- `referrer`
- `device_type`
- `viewport_width`
- `viewport_height`
- `zip_code`
- `geo_type`: `duty_station_zip`, `user_entered_zip`, `unknown`
- `app_version`
- `api_version`
- `duration_ms`
- `success`
- `error_code`
- `metadata`: structured, non-financial values only

Avoid user-agent fingerprinting as a durable identity method. A random local anonymous ID is simpler and easier to explain.

## Launch Tracking

Use campaign parameters so Reddit and local launch efforts can be compared.

Example links:

- `?utm_source=reddit&utm_medium=post&utm_campaign=launch`
- `?utm_source=reddit&utm_medium=comment&utm_campaign=launch`
- `?utm_source=yodel&utm_medium=local&utm_campaign=fort_liberty`
- `?utm_source=yodel&utm_medium=local&utm_campaign=fort_cavazos`
- `?utm_source=direct&utm_medium=qr&utm_campaign=briefing`

Store campaign fields on the first session event and include them on later events.

## Core Events

Session events:

- `session_started`
- `consent_accepted`
- `session_ended`
- `heartbeat`

Navigation events:

- `screen_viewed`
- `screen_completed`
- `screen_abandoned`
- `back_clicked`
- `start_over_clicked`

Feature events:

- `income_calculated`
- `retirement_solver_run`
- `monte_carlo_run`
- `fund_comparison_viewed`
- `budget_started`
- `budget_completed`
- `cash_flow_viewed`
- `checklist_started`
- `checklist_completed`
- `plan_generated`
- `plan_downloaded`
- `rent_vs_buy_started`
- `rent_vs_buy_completed`
- `rental_scenario_run`
- `feedback_opened`
- `feedback_submitted`

Reliability events:

- `api_request_failed`
- `api_request_slow`
- `calculation_failed`
- `chart_render_failed`
- `pdf_generation_failed`
- `frontend_error`
- `backend_error`

Performance events:

- `app_loaded`
- `api_latency_measured`
- `chart_render_time_measured`
- `pdf_generation_time_measured`

## Session Duration

Track duration in two ways:

- `session_started` timestamp
- periodic `heartbeat` events every 30 to 60 seconds while active

End-of-session events are unreliable because browsers often close tabs before sending final requests. Heartbeats produce better usage-duration estimates.

Useful metrics:

- active sessions
- median session duration
- sessions over 30 seconds
- sessions over 3 minutes
- completion rate by screen
- drop-off screen
- feature adoption rate
- return visitor rate

## Geographic Spread

Use entered ZIP code as the geographic unit only after the user explicitly provides it.

Track:

- first ZIP seen per session
- ZIP of income calculation
- launch campaign tied to ZIP
- timestamp of first event from ZIP
- number of sessions per ZIP over time
- number of completed plans per ZIP over time

Map outputs:

- sessions by ZIP
- first-seen date by ZIP
- cumulative ZIP spread over time
- week-over-week new ZIP count
- velocity: new ZIPs per day/week
- acceleration: change in new ZIPs per day/week

Be careful with low-count ZIPs. For public maps, aggregate or suppress ZIPs with very small counts.

## Product Learning Questions

The analytics should answer:

- Do people accept the consent screen?
- Where do users drop off?
- Which calculators are actually used?
- Are users running simulations or only viewing income?
- Are users downloading plans?
- Are mobile users completing the flow?
- Which launch channels create engaged sessions?
- Which ZIPs/locations are adopting fastest?
- Which screens or API endpoints break most often?
- Which features are ignored and can be simplified?

## Suggested Storage Path

Early prototype:

- Google Sheets is acceptable for low-volume manual review.

Better MVP:

- PostHog, Plausible, or a simple Postgres events table.

Best later path:

- API endpoint: `POST /analytics/event`
- Store events in Postgres.
- Build dashboard/map from aggregated event data.

Google Sheets is easy to start, but it will get awkward for maps, velocity calculations, and reliability analysis once traffic grows.

## Minimum MVP Dashboard

Start with these views:

- Daily sessions
- Median active duration
- Feature usage count
- Funnel completion by screen
- Drop-off by screen
- Sessions by source/campaign
- Sessions by ZIP
- First-seen ZIP timeline
- Error count by event type
- Slow API calls by endpoint

## Consent Copy Requirements

Consent should plainly say:

- what is collected
- what is not collected
- why ZIP code is collected
- that financial inputs are not tracked
- that anonymous usage data helps improve the app

Avoid saying "no personal information" if ZIP code is collected. Say something more precise:

`We do not collect names, emails, account numbers, income amounts, budget amounts, debt amounts, or retirement balances. We do collect anonymous usage events and the duty-station ZIP code you enter so we can understand where the tool is being used.`

