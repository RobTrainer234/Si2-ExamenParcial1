# Mobile UI redesign

## Objective

Create a cohesive, premium FashionStore mobile experience without changing backend contracts or web behavior. Improve the visual hierarchy, navigation, feedback states, touch ergonomics, and consistency across authentication, catalog, product detail, cart, reservations, purchases, recommendations, and virtual fitting.

## Visual direction

- Editorial fashion aesthetic with warm ivory surfaces, charcoal text, and restrained gold accent.
- Material 3 tokens centralized in a reusable theme.
- Consistent spacing, radii, elevation, typography, status pills, buttons, cards, loading, error, and empty states.
- Persistent authenticated bottom navigation with Catalog, Reservations, Recommendations, and Purchases.
- Product-first cards and detail surfaces with clear primary actions.

## Scope

- `mobile/lib/main.dart` and new shared theme/widget files.
- Auth screens.
- Catalog and product detail.
- Cart and checkout presentation.
- Reservations and purchase history.
- Recommendations.
- Virtual fitting states and controls.
- Mobile-only tests/build configuration as needed.

## Non-goals

- No changes to backend, API contracts, database, web, or desktop UI.
- No new Flutter dependency unless already present or strictly necessary.
- No change to payment, reservation, inventory, or authentication business logic.

## Acceptance criteria

- All mobile screens share one visual system and navigation pattern.
- Touch targets are at least 48dp where practical and accessible labels are present.
- Loading, error, empty, and success states are visually consistent.
- Catalog/detail/cart/reservations/purchases/recommendations/fitting use polished hierarchy and Spanish copy.
- Existing CU10 mobile flow remains functional.
- Camera permission, fallback simulator, and session states remain usable.
- `flutter analyze`, `flutter test`, and `flutter build apk --debug` pass.
