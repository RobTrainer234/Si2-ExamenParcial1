# CU-15 Secure Analytics Interpretation Plan

Authority: `docs/casos-de-uso-oficiales-parcial-2.md`, which requires the backend assistant to restrict analytical reads to the authenticated tenant. Provider output must never be executable SQL.

## Findings and approach
- Current provider output is a structured report intent, not SQL; kinds are allowlisted and filters are typed/validated.
- Normal HTTP queries rely on SQLAlchemy's implicit tenant session criteria. Strengthen the assistant boundary so it fails closed without tenant context and requires a matching tenant-bound session before interpretation/query work.
- Keep local SQLite/synthetic tests only; no live Gemini/OpenAI/provider or real tenant data.

## Tasks
- [x] **CU15-1 — Enforce tenant-bound assistant execution.** Assistant and assistant-export routes require tenant context before plan/provider work; `service.assistant_report` requires an explicit matching tenant-bound session; explicit and provider-derived branch filters require an active tenant-owned branch. Local suite: 24 tests + Ruff; independently verified and parent spot-checked.
- [x] **CU15-2 — Prove tenant and provider-output isolation.** Added deterministic tests for tenantless denial, mismatched/unbound sessions, foreign/inactive branches, and Gemini SQL/tenant extra-field rejection with local fallback. OpenAI schema allowlist is asserted. Two-tenant HTTP requests cover category revenue, top products, sales by branch, and dashboard with exact tenant-A aggregates and explicit tenant-B absence. Provider keys are disabled or HTTP clients mocked. Final focused backend suite: 27 passed; Ruff passed; independent verification passed.
- [x] **CU15-3 — Reconcile traceability and verify locally.** Updated `docs/parcial-2-etapa-3.md` with CU15 implementation, tests, and explicit reliance on SQLAlchemy's tenant-scoped session criteria. Final local verification: 27 tests passed, Ruff clean. No real provider calls, PostgreSQL validation, or deployed-service checks.
- [ ] **CU15-4 — Complete native review in an isolated candidate.** Native `inspect` found a mixed current-workspace candidate spanning many unrelated tracked changes and blocked on intended-untracked selection. `git worktree list` found only one existing candidate-view, and its status also contains many unrelated staged changes; it is not a CU15-isolated target. No START or capture was run. Resume only after the user supplies an exact suitable worktree root (and the candidate is present there) or explicitly chooses review of the entire mixed workspace.

## Constraints
- Strict TDD for code changes.
- Preserve unrelated worktree changes; no staging or commits.
- No schema migration, `.env`, credentials, real data, external provider calls, or deployed-service tests.
