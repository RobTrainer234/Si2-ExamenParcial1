# Tenant-specific Storefront Entry and Branding

## Goal
Allow a customer to enter the shared FashionStore Web/mobile experience in the context of a specific subscribing store (for example, Auro), recognize that store before logging in, and keep catalog, cart, branch, and purchase operations isolated to that tenant.

## Status
Product decision resolved; implementation is blocked before the first source edit because the required bounded writer skill path is unavailable. No source changes have started.

## Accepted direction
- One shared FashionStore mobile app and Web application, not a separately published app per tenant.
- A tenant-specific public link or QR establishes the storefront context before login.
- The store's public name is prominent; FashionStore remains the platform brand.
- A store-level QR may leave branch selection open; a branch-level QR may preselect that branch after backend validation.
- Path-based store links are the initial recommendation; custom domains and per-tenant app-store packages are out of initial scope.

## Decision gate
**Resolved by the user:** use tenant-scoped customer accounts. The same email may have a separate account per tenant; the store slug selects which account/login context is used; cart, history, reservations, and offline state stay separate. A global FashionStore identity with cross-tenant memberships is out of scope for this first release.

Current database uniqueness is already `(tenant_id, email)`, while public registration currently creates a global `CLIENT` with `tenant_id = NULL` and login selects by email without a tenant selector.

## Tasks
- [x] 1. Confirm customer identity scope and storefront-entry contract (user selected tenant-scoped customer accounts; store/branch QR behavior accepted as planned).
- [ ] 2. Add a unique public tenant slug and minimal public store identity/branding fields; create a migration and tests, but do not apply the migration.
- [ ] 3. Add public tenant/branch resolution, tenant-scoped anonymous catalog access, and tenant-aware customer registration/login. Validate all branch/product/cart/checkout operations against the resolved tenant; invalid or inactive stores must fail closed rather than fall back to a global catalog.
- [ ] 4. Add Web store routes that preserve the tenant slug, resolve public identity before rendering, show the store name prominently for anonymous and authenticated visitors, and preserve context through login, catalog, cart, and checkout.
- [ ] 5. Add Flutter cold-start/warm-start deep-link handling for tenant/optional branch links, persist the active store context safely, show store identity on login and throughout the shared app, and preserve tenant context through catalog and checkout.
- [ ] 6. Add backend/Web/Flutter tests for valid, missing, inactive, and cross-tenant store/branch contexts; verify login with duplicate email across tenants according to the selected model; run focused checks and update implementation/traceability documentation.

## Acceptance criteria
- A store link/QR opens the correct tenant in Web and the shared Flutter app, including cold and warm app launches.
- Before authentication, the customer can clearly see which store is active.
- Authentication, catalog, cart, reservations, checkout, and offline cache cannot silently switch to another tenant.
- A branch encoded in a link is accepted only if active and owned by the resolved tenant; without a branch link, selection is tenant-scoped.
- Unknown, inactive, or malformed store context yields an explicit unavailable/not-found experience; never show the global catalog or another tenant as fallback.
- No production migration is applied, no real provider/deployed service is called, no `.env` is inspected, and no commit is created.

## Known current gaps / evidence
- `backend/app/core/models.py`: `Tenant` currently has name/status only.
- `backend/app/modules/auth/service.py`: public customer registration creates a tenantless user; login does not accept tenant context.
- `backend/app/modules/catalog/router.py` and `service.py`: public catalog routes do not resolve a tenant slug.
- `web/src/app/app.routes.ts`, `web/src/app/app.component.ts`: routes and primary brand are global; tenant name appears only after authentication.
- `mobile/lib/features/auth/presentation/login_screen.dart`: email/password only; no active-store context.
- `mobile/lib/main.dart`, `mobile/pubspec.yaml`, Android manifest, and iOS plist: shared FashionStore shell; no deep-link setup.

## Constraints
- Preserve all existing uncommitted work; do not stage or commit.
- Use TDD with synthetic fixtures/mocks; never inspect or print `.env` credentials.
- Create a migration artifact only; do not apply it.
- Implement one task at a time and keep writes single-threaded. Each bounded writer task must receive narrow repository-relative allowed edit surfaces.
- Before source implementation, resolve the product decision above and verify the worker role/skill path is usable; do not use an unauthorized inline fallback for multi-file implementation.
