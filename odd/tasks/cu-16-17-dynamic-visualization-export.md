# CU-16 / CU-17 — Dynamic Visualization and Excel/PDF Export

## Goal
Align the current Web and Flutter report views with official CU-16 (adaptive tables and interactive charts on desktop/mobile), and make CU-17 (Web Excel/PDF exports) function end-to-end from the current assistant UI. Keep tenant authorization and subscription controls intact.

## Authority
- Official definitions: `docs/casos-de-uso-oficiales-parcial-2.md` — CU-16 is both Web and Mobile; CU-17 is Web.
- `docs/parcial-2-etapa-3.md` is a roadmap and contains historical status claims; official matrix IDs and criteria are authoritative.
- User requests source-level functional/traceability review and says not to spend time on tests requiring real-user hardware/provider actions (for example, real microphone use). Automated unit/route tests with fakes remain allowed where useful.
- CU-14 native review is explicitly deferred while the user directs work on following CUs; do not run hardware/provider tests.

## TDD and verification policy
- Use strict TDD for code changes, using deterministic test doubles and local test databases only.
- Do not test with a physical microphone, real browser speech provider, real Gemini/API keys, real tenant data, or live downloads from a deployed service.
- Focus verification on behavior and official traceability; report any integration property that cannot be established locally.

## Current read-only findings
- Web and Flutter assistant visualizations currently use constant bar values (`80%` Web; `0.75` Flutter) rather than scaling to the returned data.
- The clients/renderer do not cover all declared chart types (`bar`, `line`, `pie`, `table`, `kpi`) consistently; Flutter collapses most non-pie types into fixed progress bars.
- Web `AdminService.exportAssistantReport` sends POST JSON to `/reports/assistant/export/{format}`, while backend `export_assistant_report` is declared GET with query parameters. No existing test was found for this assistant-export route; current export tests exercise the builder directly.
- User-controlled prompt text can enter an XLSX cell in the generic export path. Formula interpretation is a risk to test and mitigate, not yet a confirmed exploit.
- CU-17 is Web-only; mobile export is out of scope. Flutter reporting contributes to CU-16 only.

## Acceptance criteria
- For supported report payloads, Web and Flutter render values proportional to returned data rather than hard-coded placeholder values.
- The chart recommendation is honored for declared chart kinds, with a useful tabular fallback for unsupported/malformed/empty chart data; interaction and responsive behavior work with keyboard/touch and have accessible labels.
- Web assistant export request, route method, body, filters, authorization, and feature gate agree; XLSX and PDF are generated for each supported report type with meaningful labels and data.
- Untrusted string cells are safely represented in XLSX; normal negative numeric values remain numeric.
- Add deterministic component/service/route/export-builder tests. Do not perform real-user or live-provider tests.
- Update `docs/parcial-2-etapa-3.md` so CU-16 and CU-17 trace to official IDs and distinguish tested code behavior from untested runtime integration.

## Tasks
- [x] **CU16/17-1 — Map official criteria to existing code and tests.** CodeGraph/read-only source audit found the placeholder chart values and POST-vs-GET export mismatch; no files changed during this audit.
- [x] **CU16-2 — Implement Web data-driven visualizations.** Added data-driven bar, pie, connected SVG line, KPI and table/fallback rendering, with visible responsive geometry, accessible labels/focus, and deterministic coverage. RED observed before implementation; independent and parent checks passed (`npm test`: 28 files/155 tests; `npm run build`: passed).
- [x] **CU16-3 — Implement Flutter data-driven chart/table rendering.** Replaced fixed bars with dependency-free data-driven bar, line, pie, table and KPI renderers; added semantics, touch details, temporal sorting and accessible fallback. RED/GREEN observed; focused widget tests passed (5 CU16 tests) and `flutter analyze` passed.
- [x] **CU17-4 — Align assistant export contract and coverage.** Backend now accepts the existing Web POST JSON contract, preserves permission/feature gates, and restricts formats to XLSX/PDF. Deterministic backend and Web tests cover body/filters, both formats, unsupported PPTX, binary headers, auth/plan denial, and Blob response; backend 10 tests + Ruff and Web 28 files/156 tests passed.
- [x] **CU17-5 — Harden and complete exported report content.** Exports now include actual data for all service-produced report shapes (including dashboard sections, reservations and channels); formula-like XLSX strings are neutralized while numeric values stay numeric; PDF titles are escaped. Route and builder tests passed (26 backend tests) and Ruff passed.
- [x] **CU16/17-6 — Reconcile traceability and run allowed checks.** Updated `docs/parcial-2-etapa-3.md` with official CU-16/CU-17 status, current evidence, the old traceability items still open, and the no-live-service boundary. CU16 Web: 28 files/156 tests + build; Flutter: 5 focused chart tests + analyze; CU17 backend: 26 tests + Ruff. No physical device, browser provider, Gemini, or deployed-service tests were run.

## Allowed edit surfaces
- `backend/app/modules/reports/router.py`
- `backend/app/modules/reports/export_service.py`
- `backend/tests/test_report_assistant.py`
- `backend/tests/test_generative_reports_ml.py`
- `web/src/app/core/admin/admin.service.ts`
- `web/src/app/core/admin/admin.service.spec.ts`
- `web/src/app/features/admin/cycle3-admin.component.ts`
- `web/src/app/features/admin/cycle3-admin.component.spec.ts`
- `mobile/lib/features/reports/presentation/reports_screen.dart`
- `mobile/test/reports_screen_test.dart`
- `docs/parcial-2-etapa-3.md`

## Out of scope
- Real microphone or browser provider trials, Gemini calls, production database, deployed service, or real user/customer data.
- CU-15 query-engine redesign, CU-18–CU-21 modeling work, mobile export, and unrelated Stage 2/CU-13 changes.
