# Stage 1 implementation — FashionStore exam 2

## Objective
Implement the first delivery stage described in `docs/parcial-2-etapa-1.md`: shared-schema SaaS tenancy and subscriptions, tenant-scoped backend access, PWA and Flutter offline catalog persistence, and Stage 1 verification/documentation.

## Problem and rationale
The second-partial requirements require FashionStore to serve multiple independent clothing businesses, apply subscription limits, and retain catalog access during network outages in both Angular and Flutter. The existing project is a single-tenant application with a substantial pre-existing baseline; the implementation must preserve its behavior and existing uncommitted user changes.

## Scope
- Reconcile the stage document with actual model names, existing authentication, migrations, test conventions, and implementation status.
- Add tenant, plan, and subscription data and safely associate existing business records with a default/legacy tenant before enforcing non-null isolation.
- Enforce tenant ownership in backend authentication, query paths, and subscription-sensitive operations.
- Add an offline catalog download/read path for Angular and Flutter with durable local persistence and stale/offline indicators.
- Add focused isolation, quota, and offline catalog checks; update relevant ICONIX artifacts.

## Constraints
- Do not overwrite or revert pre-existing working-tree changes.
- Shared PostgreSQL database and shared schema with `tenant_id`; do not describe this as database-per-tenant.
- The Stage 1 plan has now been corrected to 36 ordered tasks, uses the actual `Inventory` ORM name, maps the stage to the official CU-01 through CU-07, CU-23, CU-24, and CU-25 list, and separates catalog offline from future offline transaction sync.
- The migration plan must backfill existing data into an explicit legacy tenant before applying non-null tenant constraints. Do not add required tenant IDs without a safe migration path.
- Existing global uniqueness constraints and shared/global catalog entities must be reviewed before deciding which records are tenant-owned or keys become tenant-scoped.
- Strict TDD was explicitly selected by the user. Run `python -m pytest backend/tests -q` from the repository root for backend tests; web checks are `npm test` and `npm run build` from `web`; mobile checks are `flutter test` and `flutter analyze` from `mobile`.

## Work checklist
- [x] S1. Reconcile the Stage 1 task document with discovered model/auth/test conventions. Evidence: the checklist contains 25 items while the heading says 22; `InventoryItem` does not exist (`Inventory` is the ORM class); the Stage 1 mapping was reconciled to CU-01 through CU-07, CU-23, CU-24, and CU-25, with CU-08 reserved for Stage 2; migration backfill and tenant ownership policy are missing.
- [ ] S2. Define tenant ownership and backward-compatible default-tenant migration strategy.
- [ ] S3. Add tenant, subscription-plan, and subscription models, migration, and seed data.
- [ ] S4. Add tenant identity resolution and tenant-scoped backend access.
- [ ] S5. Enforce subscription plan entitlements and branch quotas.
- [ ] S6. Add tenant-scoped offline catalog sync API.
- [ ] S7. Add Angular PWA shell, IndexedDB catalog persistence, refresh, and offline state.
- [ ] S8. Add Flutter SQLite catalog persistence, refresh, and offline state.
- [ ] S9. Add functional tests for tenant isolation, plan quotas, and local catalog availability.
- [ ] S10. Update Stage 1 ICONIX artifacts and reconcile completion evidence.

## Acceptance criteria
- At least two seeded tenants can operate without cross-tenant data access.
- Existing records are safely assigned to a tenant through a migration/backfill path.
- Subscription plans and branch limits are enforced by the backend.
- Both web and mobile can persist and consult a downloaded catalog after restart/offline, and identify potentially stale data.
- Tenant isolation, quota boundaries, and offline catalog behavior have observed automated or documented functional checks.
- No unrelated pre-existing changes are modified or reverted.
- ICONIX artifacts and stage status correspond to implemented behavior, not planned claims.

## Checks
- Strict TDD selected by the user: for every code task, create a focused test, observe RED, implement to GREEN, then refactor and rerun checks.
- Backend (repository root): `python -m pytest backend/tests -q`.
- Web (`web` directory): `npm test`; `npm run build`.
- Mobile (`mobile` directory): `flutter test`; `flutter analyze`.
- Use focused checks per work item; preserve and report any environmental blockers.

## Progress
- Status: corrected and reconciled `docs/parcial-2-etapa-1.md`; implementation remains blocked before the first source edit because both package subagent launches failed and no native Agent tool is available.
- Evidence: `backend/app/core/models.py` contains `Inventory` (not `InventoryItem`); `backend/app/modules/auth/dependencies.py` resolves `User` from JWT/session without tenant context; `backend/app/core/security.py` JWT has `sub`, `role`, `type`, `jti`, and `exp`, no tenant claim; `backend/app/core/seed.py` seeds one FashionStore dataset; Angular has no PWA dependency/configuration in `web/package.json`; Flutter `mobile/pubspec.yaml` has no SQLite dependency.
- Working tree was already dirty before this work, including source, docs, mobile, web, and untracked files. Preserve all existing changes.
- Delegation evidence: `gentle-ai-explore` and `gentle-ai-worker` both returned `assistant reported an error`; no source file was changed. The required native Agent fallback is not exposed in this session, so multi-file implementation must stop rather than proceed inline.
- Next: resume the strict-TDD-first tenant model slice when a working bounded writer or native Agent runtime is available; first execute T1.1.1 ownership classification, then the schema/migration tasks in dependency order.
