# CU-18–CU-21 Analytics Completion Plan

Authority: `docs/casos-de-uso-oficiales-parcial-2.md`. The user-suggested surfaces (`demand_forecast`, `customer_segments`, `train_ml_models`, `ml_service.py`) are leads, not proof of completeness.

## Decisions
- CU-18 synthetic generation may remain an in-memory internal pipeline; no dedicated Tenant Admin UI/API to generate or inspect datasets is required. Verify its deterministic generation/fallback use and expose trustworthy provenance where appropriate.
- CU-20 requires explicit anomaly detection in addition to K-Means customer clustering.
- Do not run tests requiring real users, hardware, live providers/APIs, or deployed services. Use deterministic local data and fakes.

## Tasks
- [x] **CU18-1 — Verify and label the synthetic-data pipeline.** Synthetic sales timestamps are UTC-day normalized and tenant-seeded; ML metrics now report total, real, and synthetic sample counts for forecast/segmentation. Deterministic tests cover both sparse fallbacks and real-day overwrite accounting; 11 backend tests and Ruff passed.
- [x] **CU19-2 — Make supervised forecast tenant-safe and honestly evaluated.** All ML routes fail closed without tenant context; branch ownership/activity and query bounds are enforced; branch labels are tenant-scoped; forecasts use chronological holdouts and preserve negative/null R² without fabricated metrics. Backend suite: 18 passed; Ruff clean; independent verification and parent spot-check passed.
- [x] **CU20-3 — Add explicit RFM anomaly detection.** Added typed `CustomerAnomalyItem` and deterministic `IsolationForest(random_state=42, contamination="auto")`; responses include real/synthetic source, score-sorted top-10 ID-free details, and total anomaly count. Empty/degenerate inputs are safe; K-Means and metrics counts remain intact. TDD RED: two expected failures for absent anomaly fields/empty-data crash; GREEN: 20 tests passed; Ruff passed within allowed surfaces.
- [x] **CU21-4 — Align the Web dashboard to actual backend contracts.** Angular DTOs/templates now match backend forecast, segment, anomaly, provenance, and training payloads; component fixtures use backend-shaped JSON and assert period/revenue/confidence/anomaly source/training metrics. Also, with user approval, fixed Platform Admin action labels and decorative icon semantics to clear the pre-existing full-suite failure. Web suite: 28 files/156 tests passed; production build passed.
- [x] **CU18–21-5 — Reconcile traceability and verify locally.** Updated `docs/parcial-2-etapa-3.md` with official CU18–CU21 status, decisions, evidence, limitations, and outstanding full ICONIX/stage-closeout work. Backend focused suite: 20 tests + Ruff; Web full suite: 28 files/156 tests; build passed. No live integrations or real data.

## Constraints
- Strict TDD: demonstrate failing tests before implementation.
- Preserve unrelated worktree changes; do not stage or commit.
- No migrations, real tenant data, `.env`, external providers, or deployed-service calls.
- Scope writes task-by-task and keep reviewer workload bounded.
