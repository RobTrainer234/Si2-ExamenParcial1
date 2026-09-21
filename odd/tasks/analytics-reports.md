# Analytics dashboards and intelligent reports

## Goal
Deliver an intuitive administrator analytics experience aligned with RF24/RF25: visual dashboard, deterministic report exports, and an AI-assisted report request flow grounded in PostgreSQL results.

## Scope
- Improve the existing Cycle 3 dashboard with visual charts, KPIs, filters, empty/loading/error states, and export controls.
- Add backend-generated Excel, PDF, and PowerPoint exports from the same filtered report snapshot.
- Add an OpenAI Responses API adapter for interpreting report requests and drafting conclusions; keep numeric facts sourced from deterministic backend queries and provide a local fallback when no key/provider is available.
- Preserve existing routes and report endpoints where possible.

## Non-goals
- Do not expose the OpenAI key to Angular or mobile clients.
- Do not allow AI-generated values to replace database values.
- Do not change commerce, inventory, reservation, or payment business rules.
- Do not add Stripe production integration.

## Work units
1. Visual dashboard and report controls.
2. Deterministic export service and download endpoints.
3. AI report assistant with structured intent and grounded narrative fallback.
4. Automated tests and frontend/backend verification.

## Acceptance criteria
- Admin can filter dashboard by date and branch and see KPIs, charts, tables, and clear states.
- Excel, PDF, and PowerPoint downloads use the exact selected filters and include report metadata.
- AI requests such as “prendas más vendidas del último mes” resolve to validated report intent and real report data.
- Missing/invalid OpenAI configuration does not break deterministic reports or exports.
- OpenAI credentials remain backend-only and are never returned to clients.
- Existing report endpoints and tests remain compatible.
