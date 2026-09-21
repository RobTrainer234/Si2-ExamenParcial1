# Cycle 3 — Innovation, analytics, and customer insight

Cycle 3 completes the remaining customer-facing and administrative capabilities of FashionStore. It adds virtual fitting, promotions, operational reports, explainable recommendations, and purchase history on top of the catalog, inventory, reservations, commerce, and payment capabilities delivered in Cycles 1 and 2.

## Purpose and scope

The cycle has two complementary goals:

1. Improve the customer's decision-making experience through virtual fitting, recommendations, and purchase history.
2. Improve administrative decision-making through promotions, dashboards, and operational summaries.

The cycle does not replace the reservation, cart, sales, inventory, or payment flows. It consumes their persisted data and preserves their authorization, audit, and stock-consistency rules.

## Roles and responsibilities

| Role | Cycle 3 responsibility |
| --- | --- |
| ADMIN | Creates and manages promotions; reads dashboards and reports for the full business. |
| CLIENT | Reads their own purchase history, receives recommendations, and starts/finishes/lists their own virtual fitting sessions. |
| BRANCH_MANAGER | No new Cycle 3 administration scope; branch-scoped operational access remains governed by Cycle 2 permissions. |
| CASHIER | No new Cycle 3 administration scope. |
| SUPPLIER | No direct Cycle 3 scope. |

## Criteria by use case

| CU | Use case | Acceptance criteria |
| --- | --- | --- |
| CU12 | Virtual fitting | A client can start, finish, and list virtual fitting sessions for active products. Mobile uses local camera and pose detection when available, with a documented simulator fallback. |
| CU20 | Promotions | An administrator can create, update, activate/deactivate promotions, assign products, and apply valid discounts to cart and sale totals without producing negative totals. |
| CU21 | Reports and dashboards | An administrator can read sales, stock, reservations, channels, and revenue summaries with date and branch filters. Calculations match persisted commerce and inventory data. |
| CU22 | AI recommendations | A client receives explainable ranked product recommendations based on purchase history, category affinity, season, popularity, and available stock. Unavailable products are excluded; cold-start clients receive popular available products. |
| CU23 | Purchase history | A client can list and inspect only their own confirmed, pending, or failed purchases, including items and payments. A client cannot read another customer's history. |

## Status

| Use case | Status | Implemented scope |
| --- | --- | --- |
| CU12 Virtual fitting | Complete academic prototype | Backend sessions, web simulator action, and mobile camera/overlay prototype using local pose detection with a documented fallback simulator. |
| CU20 Promotions | Complete | Administrative promotion CRUD, product assignment, activation/deactivation, and server-side discount application in cart and sales. |
| CU21 Reports and dashboards | Complete | Administrative dashboard with sales, products, stock, reservations, channels, and revenue sections, including branch/date filters. |
| CU22 AI recommendations | Complete academic scoring engine | Explainable ranking from purchase history, category affinity, popularity, active season, catalog state, and stock availability. |
| CU23 Purchase history | Complete | Client-owned purchase listing and detail endpoints, web history screen, mobile history screen, item/payment detail, and ownership validation. |

## Functional details

### CU12 — Virtual fitting

Virtual fitting provides an academic prototype for previewing how a selected garment may be positioned on the user's body.

- The web product detail can start a simulator session.
- Mobile can use the device camera and local pose detection.
- Shoulder landmarks are used to estimate garment placement.
- Camera frames are not uploaded to an external AI service.
- No API key is required.
- When a camera or pose detector is unavailable, the simulator/fallback remains available.
- Sessions can be started, finished, and listed for the authenticated client.

This is an assisted visual prototype, not photorealistic cloth simulation or a production sizing guarantee.

### CU20 — Promotions

Promotions allow the administrator to manage commercial discounts without putting pricing rules in the client.

- Create and edit promotion name, dates, and discount values.
- Activate or deactivate a promotion.
- Assign products to a promotion.
- Apply valid discounts to cart and sale totals on the server.
- Reject invalid or expired promotions.
- Prevent totals from becoming negative.
- Preserve the original price and the calculated discount in the commerce response where applicable.

### CU21 — Reports and dashboards

Reports aggregate persisted business data for administrative decision-making.

The dashboard includes:

- Sales totals and trends.
- Sales by branch.
- Top products.
- Low-stock products.
- Reservation summaries.
- Sales by channel.
- Revenue summaries.
- Date and branch filters.

The report layer is read-only. It does not modify inventory, reservations, sales, payments, or promotions.

### CU22 — AI recommendations

Recommendations use an explainable academic scoring engine rather than a trained custom model.

Signals include:

- Purchase history.
- Category affinity.
- Product popularity.
- Active season and collection.
- Product activity and catalog visibility.
- Available inventory.

The response explains the recommendation reason and excludes products with no available stock. For a client without purchase history, the system uses available popular products as the cold-start strategy.

### CU23 — Purchase history

Purchase history gives the client a read-only view of their own commerce activity.

- List the client's purchases.
- Inspect a single purchase.
- Show purchase status.
- Show line items, quantities, prices, discounts, and totals.
- Show associated payment information where available.
- Include pending, confirmed, and failed purchases.
- Reject access to another customer's purchase identifiers.

## Backend endpoints

```text
# Purchase history — CU23
GET   /api/v1/purchases/mine
GET   /api/v1/purchases/mine/{sale_id}

# Promotions — CU20
GET   /api/v1/promotions
POST  /api/v1/promotions
GET   /api/v1/promotions/{promotion_id}
PATCH /api/v1/promotions/{promotion_id}
PATCH /api/v1/promotions/{promotion_id}/activate
PATCH /api/v1/promotions/{promotion_id}/deactivate
POST  /api/v1/promotions/{promotion_id}/products

# Reports — CU21
GET   /api/v1/reports/dashboard
GET   /api/v1/reports/sales-by-branch
GET   /api/v1/reports/top-products
GET   /api/v1/reports/low-stock
GET   /api/v1/reports/reservations-summary
GET   /api/v1/reports/sales-by-channel
GET   /api/v1/reports/revenue-summary

# Recommendations — CU22
GET   /api/v1/recommendations/mine

# Virtual fitting — CU12
POST  /api/v1/virtual-fitting/sessions
PATCH /api/v1/virtual-fitting/sessions/{session_id}/finish
GET   /api/v1/virtual-fitting/sessions/mine
```

## UI surfaces

### Web

- `/purchase-history`: client purchase list and selectable purchase detail.
- `/recommendations`: explainable recommendation list.
- `/cycle-3-admin`: promotion administration and reporting dashboard.
- Product detail: virtual fitting action and simulator feedback.

### Mobile

- Purchase history screen.
- Recommendations screen.
- Virtual fitting screen with local camera/overlay prototype and fallback simulator.
- Existing catalog navigation exposes recommendations, purchases, and virtual fitting.

## Authorization and data protection

- Only `ADMIN` can manage promotions.
- Only `ADMIN` can read the complete administrative dashboard and reports.
- A `CLIENT` can read only their own purchases and virtual fitting sessions.
- Recommendation results are scoped to the authenticated client.
- Report filters cannot bypass administrative authorization.
- Existing branch permissions remain enforced for operational roles.
- Read-only reporting and recommendation queries do not mutate commercial state.

## Rules and academic limitations

- Recommendation ranking is an explainable scoring engine, not a trained custom ML model.
- Virtual fitting uses local mobile pose detection and transparent overlays.
- Camera frames are not sent to an external AI API.
- The virtual fitting prototype does not guarantee garment fit, size, or photorealistic appearance.
- Promotions are validated server-side and cannot create negative totals.
- Purchase history always enforces ownership at the API boundary.
- Stripe production integration is outside this cycle; sandbox payment remains the accepted academic payment path.

## Verification evidence

The Cycle 3 baseline was verified with:

- Backend: `cd backend && python -m pytest -q` — 24 tests passed.
- Web unit tests: `cd web && npm test -- --watch=false` — 13 tests passed.
- Web production build: `cd web && npm run build` — successful.
- Mobile analysis: `cd mobile && flutter analyze` — no issues found.
- Mobile tests: `cd mobile && flutter test` — 8 tests passed.
- Android debug build: `cd mobile && flutter build apk --debug` — successful.

The backend suite covers authentication, authorization, promotions, reports, recommendations, purchase history, virtual fitting, commerce integration, and relevant ownership/error cases.

## Definition of done

Cycle 3 is considered complete when:

- Each CU has an implemented backend contract.
- Authorization is enforced for every role and ownership boundary.
- Planned web and mobile surfaces compile and support the intended flow.
- Main success and error paths have automated coverage.
- Recommendations and virtual fitting limitations are documented.
- Report values are derived from persisted business data.
- The cycle document records endpoints, surfaces, evidence, and limitations.

## Closure and next steps

The functional academic scope of Cycle 3 is complete. Remaining work is optional hardening or production preparation:

1. Consolidate final screenshots and demonstration evidence.
2. Run a final cross-cycle regression and deployment check.
3. Validate the virtual fitting experience on a physical Android device.
4. Replace sandbox payments with a real provider integration if production payments are required.
5. Run PostgreSQL concurrency and browser E2E checks against the final deployment environment.

## Actualización posterior — analítica, exportaciones e IA de reportes

La implementación posterior amplió CU21 para cubrir el dashboard exigido por el enunciado y la generación de reportes administrativos.

### Dashboard visual

La ruta web `/cycle-3-admin` incluye ahora:

- KPIs de ventas, ingresos, descuentos y bajo stock.
- Visualización de ingresos netos y descuentos.
- Ventas por sucursal.
- Productos más vendidos.
- Ventas por canal.
- Reservas por estado.
- Alertas de inventario bajo.
- Filtros por fechas y sucursal.
- Estados de carga, error y ausencia de datos.

La interfaz usa componentes SVG/CSS y mantiene las dependencias del frontend ligeras.

### Exportación de reportes

Los reportes se generan en FastAPI a partir de un snapshot determinístico de PostgreSQL:

```text
GET /api/v1/reports/export/xlsx
GET /api/v1/reports/export/pdf
GET /api/v1/reports/export/pptx
```

Cada exportación respeta `date_from`, `date_to` y `branch_id`, incluye metadatos y está protegida por `reports.read`.

- Excel: resumen, productos, sucursales, canales, reservas y bajo stock.
- PDF: resumen, tablas y visualización de ventas por sucursal.
- PowerPoint: resumen, ventas por sucursal y productos principales.

### Reporte inteligente

Se agregó el endpoint protegido:

```text
POST /api/v1/reports/assistant
```

El administrador puede escribir solicitudes como:

```text
¿Cuáles fueron las prendas más vendidas del último mes?
```

El flujo es:

1. OpenAI Responses API interpreta la intención cuando `OPENAI_API_KEY` está configurada.
2. FastAPI valida la intención y ejecuta consultas propias sobre PostgreSQL.
3. Los números del reporte provienen únicamente de datos persistidos.
4. OpenAI puede redactar una explicación usando esos datos.
5. Si OpenAI no está disponible, se utiliza un parser y una narrativa local determinística.

La clave OpenAI permanece exclusivamente en el backend mediante `OPENAI_API_KEY`; nunca se envía a Angular.

### Verificación actualizada

- Backend: `35` pruebas aprobadas.
- Web: `55` pruebas aprobadas.
- Ruff y compilación Python: aprobadas.
- Build productivo Angular: aprobado.
- Docker: PostgreSQL, backend y web levantados como saludables.

### UML mediante MCP

La configuración `antigravity.jsonc` registra un bridge MCP para Enterprise Architect. La documentación operativa está en `docs/enterprise-architect-mcp.md`.

El bridge permite inspeccionar paquetes y elementos, crear diagramas nativos de clases y secuencia, y exportarlos como imágenes. El modelo se configurará en:

```text
C:\ProyectoSi2_TiendaRopa\docs\uml\FashionStore.qea
```

El modelo debe ser creado y guardado previamente desde Enterprise Architect; el bridge no crea ni abre archivos desconocidos automáticamente.
