# Plan de Implementación — Etapa 1 (Segundo Parcial)

> **Alcance:** fundación SaaS multitenant, suscripciones, aislamiento backend y consulta offline del catálogo en Angular PWA y Flutter/SQLite.
>
> **Fechas de seguimiento:** Presentación 1: 25/10/2026; Presentación 2: 01/11/2026; Presentación 3: 08/11/2026; defensa: 10/11/2026. El 25/10 es un hito de avance, no se declara completa toda la etapa si quedan criterios pendientes.
>
> **Casos de uso oficiales de la Etapa 1:** CU-01, CU-02, CU-03, CU-04, CU-05, CU-06, CU-07, CU-23, CU-24 y CU-25. La etapa incluye sólo descarga/consulta del catálogo y persistencia offline; CU-08 (venta de contado offline), junto con las demás operaciones comerciales offline, corresponde a la Etapa 2.
>
> **Estado actual (auditoría actualizada):** las 36 tareas listadas abajo corresponden al cierre histórico original; una auditoría posterior detectó y corrigió brechas en CU-03, CU-04 y CU-07. Se reejecutaron las suites completas de backend (111), Web (107), Flutter (60), análisis Dart y el E2E PWA de producción (1); todas pasaron. La migración CU-03 pasó upgrade/downgrade en SQLite `:memory:`; no se aplicó a una base persistente. Se considera cerrada la implementación y verificación automatizada de los 10 CU oficiales de Etapa 1, con esa limitación de despliegue explícita.

## Propósito y límites de esta etapa

Entregar una base comprobable sobre la cual se implementarán posteriormente ventas y reservas offline, sincronización de transacciones, reportes generativos y Machine Learning. En esta etapa no se implementa todavía la cola de ventas/reservas offline ni la resolución de conflictos comerciales.

La base central es PostgreSQL compartida con esquema compartido y aislamiento lógico por `tenant_id` (no es un diseño database-per-tenant). Los clientes web y móvil comparten API y reglas de negocio, pero usan mecanismos locales distintos: IndexedDB y SQLite.

## Supuestos y reglas que gobiernan la implementación

1. Cada usuario de empresa pertenece a un tenant. La reutilización de una misma cuenta de usuario en varios tenants queda fuera de esta etapa; si el grupo requiere cuentas multiempresa, hay que cambiar el modelo antes de crear la migración.
2. Los tenants de demostración se separan del tenant legado que recibirá los datos actualmente existentes. No se reasignan los datos productivos/de desarrollo existentes a una empresa de demostración.
3. La identidad del tenant se deriva de la sesión/usuario autenticado y de la pertenencia validada en backend. Un `tenant_id` enviado por el cliente nunca es, por sí solo, autorización. Las operaciones de administración SaaS usan un rol de plataforma explícito. Las migraciones se desarrollan y prueban primero contra una base descartable/de pruebas; no se aplican a una base compartida o productiva sin autorización explícita del responsable.
4. Antes de añadir columnas obligatorias se crea un tenant legado, se agrega `tenant_id` inicialmente nullable, se realiza el backfill, se verifican las relaciones y recién después se aplican `NOT NULL`, claves foráneas, índices y restricciones.
5. Se debe clasificar el modelo ORM real en datos propios del tenant y catálogos globales. No se agrega `tenant_id` a ciegas a tablas compartidas de referencia (por ejemplo, roles/permisos o referencias maestras); los registros comerciales y sus relaciones sí deben quedar dentro del tenant dueño.
6. Usar los nombres reales de las entidades existentes. En el ORM actual el inventario se llama `Inventory`, no `InventoryItem`. La lista definitiva de entidades se obtiene de `backend/app/core/models.py` antes de migrar.
7. Los planes son configurables en backend. Para esta etapa, Básico permite hasta 2 sucursales activas y no habilita reportes generativos; Profesional permite hasta 10 y los habilita. Las funciones no restringidas explícitamente se habilitan según la matriz acordada por el grupo y el enunciado.
8. La PWA y SQLite almacenan una copia identificada por tenant y sucursal. Al cerrar sesión o cambiar la identidad activa, no se pueden mostrar datos locales de otra empresa.
9. Strict TDD: para cada cambio de código, primero escribir una prueba focalizada y observar RED; implementar hasta GREEN; luego refactorizar y volver a ejecutar los checks. No inferir cumplimiento por existencia de tests.

## Fase 1.1 — Inventario del dominio, modelo SaaS y migración segura

- [x] **T1.1.1** Clasificar todas las entidades SQLAlchemy actuales como tenant-owned, globales o derivadas, documentando sus relaciones y las claves que deben ser únicas dentro o fuera del tenant.

### Resultado T1.1.1 — inventario del modelo ORM

Inventario realizado sobre `backend/app/core/models.py` (33 entidades persistentes; `Base` no es una tabla). La clasificación se basa en el dominio y las relaciones actuales; las decisiones marcadas **confirmar** deben cerrarse antes de generar la migración. Los IDs técnicos continúan siendo PK globales. Las reglas de unicidad indicadas abajo se refieren a claves de negocio y restricciones `UNIQUE`, no a las PK.

| Clasificación | Entidades | Relaciones y alcance de tenant | Unicidad/índices que deben revisarse |
|---|---|---|---|
| Globales / plataforma | `Role`, `Permission`, `RolePermission` | Catálogo de autorización de plataforma; `RolePermission` es la unión global rol-permiso. Los roles de plataforma no deben confundirse con roles de empresa. | `Role.code` y `Permission.code` globales; PK compuesta `(role_id, permission_id)` global. |
| Globales / referencia | `City`, `Size`, `Color` | Referencias compartidas por sucursales y variantes. No reciben `tenant_id` salvo decisión explícita de convertirlas en configurables por empresa. | `City.name`, `Size.name`, `Color.name` permanecen globales si se conserva el catálogo común. |
| Tenant-owned raíz | `User`, `Branch`, `Category`, `Supplier`, `Season`, `Promotion` | Cada registro pertenece a un tenant. `Branch` referencia `City`; `User` referencia un rol y opcionalmente un proveedor; `Category`, `Season`, `Supplier` y `Promotion` son propiedad de la empresa. `User` no se reutiliza entre tenants según el supuesto de la etapa. | `User.email` pasa a ser único dentro del tenant (confirmar si los usuarios de plataforma quedan en un espacio global separado); `Branch(city_id, name)` pasa a `(tenant_id, city_id, name)`; `Category.name`, `Supplier.tax_id` (si no es nulo), `Season.name`, `Product.code`, `Product.slug` y `ProductVariant.sku` deben ser únicos por tenant, no globalmente. `Promotion.name` no tiene unicidad actualmente; no inventar una sin requisito. |
| Tenant-owned dependiente | `Collection`, `Product`, `ProductVariant`, `ProductImage`, `ProductSupplier`, `SupplierSupplyOffer`, `Inventory`, `Reservation`, `ReservationItem`, `Cart`, `CartItem`, `Sale`, `SaleShippingSnapshot`, `SaleItem`, `Payment`, `InventoryMovement`, `PromotionProduct` | Pertenecen al tenant del agregado/padre: colección→temporada; producto→categoría/temporada/colección; variante e imagen→producto; inventario→sucursal+variante; reserva/venta→cliente y sucursal; detalles/pagos/envío→reserva/venta; promoción→producto; oferta→proveedor+variante+temporada/colección; movimientos→inventario. Las FKs entre entidades tenant-owned deben validar que ambos extremos sean del mismo tenant, no sólo que existan. | `Collection(season_id, name)` conserva la unicidad por temporada (la temporada es tenant-owned); `ProductVariant(product_id, size_id, color_id)` e `Inventory(branch_id, product_variant_id)` conservan su unicidad dentro del agregado/tenant; `ProductImage(product_id, sort_order)`, `ReservationItem(reservation_id, product_variant_id)`, `CartItem(cart_id, product_variant_id)` y `PromotionProduct(promotion_id, product_id)` son únicas por padre; `Cart.customer_id` es único dentro del tenant; `Sale.order_number` único por tenant; `Payment(provider, transaction_reference)` debe ser único por tenant/proveedor cuando ambos valores existan; `Payment.idempotency_key` único por tenant (confirmar alcance externo del proveedor). |
| Dependientes de identidad / sesión | `UserBranch`, `RefreshToken` | `UserBranch` hereda el tenant de usuario y sucursal y sólo permite asociaciones dentro del mismo tenant. `RefreshToken` hereda el tenant de `User`; no necesita `tenant_id` independiente si las consultas siempre se unen y filtran por usuario autenticado. | PK compuesta `(user_id, branch_id)`; `RefreshToken.session_id` y `token_hash` siguen globalmente únicos para impedir colisiones de credenciales. |
| Derivadas / transversales | `VirtualFittingSession`, `AIRecommendation`, `Bitacora` | `VirtualFittingSession` y `AIRecommendation` derivan tenant del cliente/producto; si cualquiera puede existir sin cliente, el producto sigue siendo ancla tenant. `Bitacora` es transversal: debe registrar tenant explícito cuando el evento pertenece a uno, conservar eventos de plataforma con tenant nulo y no usar sólo `user_id` para filtrar auditoría. | No introducir unicidad de negocio no existente. Los índices existentes de `Bitacora` (`tipo_entidad, entidad_id`; `fecha_creacion`) deben revisarse para consultas por tenant; mantener índices temporales y de referencia de las entidades derivadas. |

#### Decisiones de diseño antes de T1.1.3–T1.1.7

- La clasificación de `Category` como tenant-owned sigue el alcance explícito de la etapa; `Size`, `Color` y `City` se mantienen como referencias globales. Si el negocio necesita categorías compartidas y personalizadas, se debe modelar esa distinción expresamente en lugar de mezclar ambos alcances.
- En tablas hijas, evitar `tenant_id` redundante si se puede garantizar aislamiento con una FK compuesta hacia el padre; si se agrega para filtrar/particionar eficientemente, usar una restricción compuesta que impida discrepancias entre el tenant de la fila y el del padre.
- `UserBranch` es una tabla de asociación, no una entidad con tenant independiente. La consistencia tenant usuario-sucursal debe imponerse en base de datos o en servicio con prueba explícita.
- `Bitacora` no debe convertirse en un catálogo tenant-owned ordinario: requiere distinguir auditoría de tenant de operaciones de plataforma y definir retención/acceso.
- `SupplierSupplyOffer` vincula proveedor y productos/variantes. Confirmar si una oferta de un proveedor debe poder referenciar producto de otro tenant; por defecto, impedirlo.
- Las restricciones únicas nullable (por ejemplo, `Supplier.tax_id` y referencias de pago) dependen del comportamiento de NULL de PostgreSQL y del proveedor; deben definirse explícitamente al migrar.

**Evidencia:** clasificación y restricciones contrastadas con las declaraciones ORM vigentes en `backend/app/core/models.py`. No se modificó el modelo ni se ejecutó una migración: esas tareas pertenecen a los puntos siguientes.
- [x] **T1.1.2** Definir los casos de usuario de empresa, administrador de plataforma y usuario de sucursal, incluidos los límites de pertenencia de usuario a tenant.

### Resultado T1.1.2 — actores y límites de pertenencia

Estos casos describen el modelo de autorización objetivo de la etapa; no implican que ya esté implementado. El tenant se resuelve desde la identidad autenticada y la membresía validada en backend. Un ID de tenant enviado en el request nunca concede acceso.

| Actor | Identidad y pertenencia | Alcance permitido | Límites y controles |
|---|---|---|---|
| Administrador de plataforma (SaaS) | Identidad de plataforma con rol/permisos explícitos de plataforma; no es administrador de una empresa por el solo hecho de ser `ADMIN`. Puede no pertenecer a un tenant. | Operaciones SaaS expresamente autorizadas: alta de empresa, administración del catálogo de planes y gestión de suscripciones/estado. Acceso a datos operativos de tenants sólo mediante una operación de plataforma con permiso explícito y auditado. | No hereda acceso a sucursales ni a datos comerciales. No usar el rol actual `ADMIN` como bypass global para tenants. Cada operación cross-tenant debe validar permiso de plataforma, declarar el tenant objetivo y auditar actor, acción y objetivo. |
| Administrador de empresa (tenant) | Usuario interno asociado a exactamente un tenant en esta etapa. Su rol de administrador de empresa es distinto del administrador SaaS. | Administración de datos y usuarios de su empresa, sucursales y recursos tenant-owned; puede operar en cualquier sucursal del tenant según permisos. | No puede leer ni mutar otra empresa aunque conozca IDs válidos. No puede crear/asignar usuarios fuera de su tenant ni realizar operaciones de plataforma. El tenant objetivo se deriva de la sesión. |
| Usuario de sucursal | Usuario interno asociado a exactamente un tenant y a una o más sucursales de ese mismo tenant mediante membresía explícita. El conjunto de sucursales puede ser una sola sucursal o varias según asignación administrativa. | Sólo operaciones concedidas por sus permisos y dentro de sus sucursales asignadas. Cada recurso recibido por ID (por ejemplo, `branch_id`, inventario, venta o reserva) se valida simultáneamente contra tenant y sucursal. | No puede cambiar su tenant ni ampliar sus sucursales desde el cliente. Sucursal de otro tenant se rechaza sin revelar si el recurso existe. No alcanza con validar que el usuario tenga rol de empleado: se valida la membresía concreta. |

#### Reglas comunes de identidad y autorización

1. **Una identidad interna, un tenant:** en esta etapa un usuario de empresa pertenece a un solo tenant. No se admite reutilizar la misma cuenta como miembro de varias empresas; hacerlo requeriría modelar una entidad de membresía y seleccionar tenant activo de forma explícita antes de cambiar el esquema.
2. **Separación plataforma/empresa:** rol global y permisos de plataforma se distinguen de los roles funcionales de tenant. Un rol administrativo de empresa no otorga privilegios SaaS, y un usuario de plataforma no recibe acceso implícito al contenido empresarial.
3. **Tenant de confianza:** en endpoints autenticados, derivar tenant desde usuario/membresía validada en backend. Ignorar o rechazar `tenant_id` cliente como fuente de autorización; para tareas de plataforma, validar el permiso y el tenant objetivo explícito.
4. **Cierre de alcance por relación:** validar tenant en todas las relaciones y sucursal cuando la operación sea branch-scoped. No aceptar referencias cruzadas sólo porque sus IDs existen.
5. **Errores no enumerables:** recurso ajeno y recurso inexistente deben producir respuestas equivalentes donde corresponda, evitando filtrar datos entre tenants.
6. **Auditoría:** registrar actor, tenant (cuando aplique), tipo/ID de recurso, acción y motivo en operaciones privilegiadas; los eventos SaaS quedan identificados como operaciones de plataforma.

#### Brecha observada en la autenticación actual

`backend/app/modules/auth/dependencies.py` hoy trata `role.code == "ADMIN"` como bypass tanto para permisos (`require_permission`) como para acceso a sucursales (`require_branch_access`); `backend/app/modules/auth/router.py` expone el rol y sucursales, pero no una membresía tenant. Por eso, el diseño SaaS no debe reutilizar ese bypass sin acotarlo: en tareas posteriores se separará explícitamente la autorización de plataforma de la administración tenant y se agregará validación tenant+sucursal. No se cambió código de autenticación en T1.1.2.

**Evidencia:** casos objetivo definidos a partir del supuesto de un tenant por usuario y de los roles/permisos/membresías que existen hoy en `backend/app/core/models.py` y `backend/app/modules/auth/dependencies.py`. Pendiente de implementación en T1.1.3 y T1.2.
- [x] **T1.1.3** Crear los modelos ORM `Tenant`, `SubscriptionPlan` y `Subscription` siguiendo la convención central existente de `backend/app/core/models.py`.

### Resultado T1.1.3 — modelos ORM SaaS

Se añadieron `Tenant`, `SubscriptionPlan` y `Subscription` en `backend/app/core/models.py`, con relaciones y claves foráneas explícitas. `Tenant` conserva nombre visible (sin unicidad global), estado y timestamps; `SubscriptionPlan` define código único, límite positivo de sucursales activas, habilitación de reportes generativos y estado activo; `Subscription` enlaza empresa y plan, registra estado y período efectivo, y permite conservar el historial de planes. No se agregaron precio/cobros, migración, seeds, `tenant_id` a modelos existentes ni rutas API: corresponden a otros puntos.

Las pruebas focalizadas verifican las capacidades Básico/Profesional (límites 2/10, reportes generativos desactivados/activados), persistencia de historial, timestamps, nombres de empresa duplicados permitidos y rechazo de estado/intervalo inválidos.

**TDD y verificación:** RED observado antes del modelo: test collection falló porque `Subscription` aún no existía; al completar el modelo, las pruebas quedaron verdes. Una segunda RED detectó timestamps faltantes y unicidad global no requerida del nombre; ambas regresiones se resolvieron. Comando final: `python -m pytest backend/tests/test_saas_models.py -q` → **4 passed** (confirmado también por verificación independiente).
- [x] **T1.1.4** Añadir `tenant_id` nullable y sus relaciones a las entidades de negocio clasificadas como tenant-owned; incluir `Branch`, `User`, `Category`, `Product`, `ProductVariant`, `Inventory`, `Sale`, `Reservation` y las demás entidades dependientes identificadas en T1.1.1.

### Resultado T1.1.4 — tenant_id nullable y relaciones en modelos de negocio

Se añadió la columna `tenant_id` (inicialmente nullable, indexada, con clave foránea a `tenants.id` y `ondelete="CASCADE"`, salvo en `Bitacora` donde usa `ondelete="SET NULL"`) y las relaciones bidireccionales ORM correspondientes entre `Tenant` y las 19 entidades de negocio clasificadas en T1.1.1:
- **Tenant-owned raíz:** `User`, `Branch`, `Category`, `Supplier`, `Season`, `Promotion`.
- **Tenant-owned dependientes:** `Collection`, `Product`, `ProductVariant`, `Inventory`, `Reservation`, `Cart`, `Sale`, `Payment`, `InventoryMovement`, `SupplierSupplyOffer`.
- **Derivadas y transversales:** `VirtualFittingSession`, `AIRecommendation`, `Bitacora`.

Siguiendo la decisión de diseño de T1.1.1, se evitó la adición de columnas redundantes de `tenant_id` en tablas puramente hijas de detalle (`SaleItem`, `ReservationItem`, `CartItem`, `ProductImage`, `SaleShippingSnapshot`) y tablas de unión pura (`ProductSupplier`, `PromotionProduct`, `UserBranch`, `RolePermission`, `RefreshToken`), ya que su aislamiento de tenant queda garantizado mediante la relación con su entidad padre/agregado.

**TDD y verificación:**
1. **RED:** Se añadieron 3 nuevas pruebas unitarias en `backend/tests/test_saas_models.py` (`test_tenant_id_present_and_nullable_on_tenant_owned_entities`, `test_tenant_relationships_bidirectional_roundtrip`, `test_legacy_records_persist_with_null_tenant_id`). Se observó el fallo esperado (`AssertionError: User missing tenant_id column in table usuarios`, `TypeError: 'tenant' is an invalid keyword argument for User`, `TypeError: 'tenant_id' is an invalid keyword argument for User` → **3 failed, 4 passed**).
2. **GREEN:** Se definieron las columnas `tenant_id` y relaciones en `backend/app/core/models.py`. Al re-ejecutar, las pruebas pasaron: `python -m pytest backend/tests/test_saas_models.py` → **7 passed**.
3. **Regresión:** Se ejecutó la suite completa de pruebas del backend: `python -m pytest backend/tests -q` → **65 passed in 19.13s** (0 fallos). Los registros existentes y la compatibilidad con valores nulos quedaron completamente preservados.
- [x] **T1.1.5** Revisar y migrar las restricciones únicas/índices de datos tenant-owned para evitar colisiones entre empresas sin debilitar unicidad dentro de cada empresa.

### Resultado T1.1.5 — restricciones únicas e índices por tenant

Se actualizaron las restricciones de unicidad (`UniqueConstraint`) y los índices compuestos en `backend/app/core/models.py` de acuerdo con la matriz definida en T1.1.1:
- **Claves de negocio migradas a alcance por tenant (`(tenant_id, ...)`):**
  - `User`: `uq_users_tenant_email` (`(tenant_id, email)`) + `Index("ix_users_email", "email")`.
  - `Branch`: `uq_branches_tenant_city_name` (`(tenant_id, city_id, name)`).
  - `Category`: `uq_categories_tenant_name` (`(tenant_id, name)`).
  - `Supplier`: `uq_suppliers_tenant_tax_id` (`(tenant_id, tax_id)`).
  - `Season`: `uq_seasons_tenant_name` (`(tenant_id, name)`).
  - `Product`: `uq_products_tenant_code` (`(tenant_id, code)`), `uq_products_tenant_slug` (`(tenant_id, slug)`), más índices compuestos `ix_products_tenant_category_active`, `ix_products_tenant_audience_active`, `ix_products_tenant_season_active` e `ix_products_tenant_collection_active`.
  - `ProductVariant`: `uq_product_variants_tenant_sku` (`(tenant_id, sku)`) + `Index("ix_product_variants_sku", "sku")` (conservando `uq_product_variants_attributes` por `(product_id, size_id, color_id)`).
  - `Cart`: `uq_carts_tenant_customer` (`(tenant_id, customer_id)`) + `Index("ix_carts_customer_id", "customer_id")`.
  - `Sale`: `uq_sales_tenant_order_number` (`(tenant_id, order_number)`) + `Index("ix_sales_order_number", "order_number")` e `ix_sales_tenant_branch_created`.
  - `Payment`: `uq_payments_tenant_provider_reference` (`(tenant_id, provider, transaction_reference)`), `uq_payments_tenant_idempotency_key` (`(tenant_id, idempotency_key)`), más `Index("ix_payments_idempotency_key", "idempotency_key")`.
  - Índices operativos compuestos adicionales: `ix_inventory_tenant_branch` (`Inventory`), `ix_reservations_tenant_status_expires` (`Reservation`), `ix_bitacora_tenant_created_at` (`Bitacora`).
- **Catálogos globales y de sesión preservados con unicidad global:** `Role.code`, `Permission.code`, `City.name`, `Size.name`, `Color.name`, `RefreshToken.session_id` y `RefreshToken.token_hash`.
- **Validaciones de servicio compatibles con `tenant_id` nullable (transición antes de T1.2):** Dado que en SQL estándar/SQLite `UNIQUE(NULL, col)` permite duplicados cuando `tenant_id IS NULL`, se reforzaron las validaciones previas en `backend/app/modules/products/service.py`, `backend/app/modules/locations/service.py` y `backend/app/modules/seasons/service.py` para verificar unicidad en el ámbito del `tenant_id` (incluyendo `IS NULL`).

**TDD y verificación:**
1. **RED:** Se agregaron 3 pruebas en `backend/tests/test_saas_models.py` (`test_tenant_scoped_unique_constraints_and_indexes_metadata`, `test_two_tenants_can_share_business_keys_without_collision`, `test_same_tenant_rejects_duplicate_business_keys`). Se observó fallo esperado (`AssertionError: User.email must not be globally unique` e `IntegrityError: UNIQUE constraint failed: sucursales.ciudad_id, sucursales.nombre` → **2 failed, 8 passed**).
2. **GREEN:** Se actualizaron las restricciones e índices en `backend/app/core/models.py` y se ejecutó `python -m pytest backend/tests/test_saas_models.py` → **10 passed in 0.63s**.
3. **Regresión:** Se ejecutó la suite completa de pruebas `python -m pytest backend/tests -q`, se detectaron y corrigieron los chequeos de unicidad en servicios cuando `tenant_id` es `None`, obteniendo **68 passed in 24.51s** (0 fallos).
- [x] **T1.1.6** Crear migración Alembic aditiva y segura: crear tablas SaaS, columnas nullable/FKs e índices iniciales, y crear un tenant legado para los registros existentes.

### Resultado T1.1.6 — migración Alembic aditiva y tenant legado

Se creó la migración aditiva `backend/migrations/versions/p7l0m3n5q7r9_agregar_fundacion_saas_aditiva.py` (`down_revision = "o6k9l2m4n6p8"`), probada exclusivamente contra una base descartable en memoria y mediante generación de DDL PostgreSQL offline (respetando la Regla 3 de no aplicar migraciones a bases compartidas/productivas sin autorización):
- **Tablas SaaS creadas:** `tenants`, `subscription_plans` (`uq_subscription_plans_code`, `ck_subscription_plans_branch_limit_positive`) y `subscriptions` (`ck_subscriptions_status_valid`, `ck_subscriptions_valid_interval`, FKs a `tenants` y `subscription_plans`, e índices `ix_subscriptions_tenant_id`, `ix_subscriptions_plan_id`).
- **Columnas `tenant_id` nullable, FKs e índices iniciales en las 19 tablas:** se añadieron `tenant_id` (`nullable=True`), la FK `fk_<tabla>_tenant_id_tenants` (`ON DELETE CASCADE` en las 18 tablas de negocio y `ON DELETE SET NULL` en `bitacora`), el índice `ix_<tabla>_tenant_id` y los índices compuestos por tenant (`ix_products_tenant_category_active`, `ix_products_tenant_audience_active`, `ix_products_tenant_season_active`, `ix_products_tenant_collection_active`, `ix_inventory_tenant_branch`, `ix_reservations_tenant_status_expires`, `ix_sales_tenant_branch_created`, `ix_bitacora_tenant_created_at`).
- **Tenant legado creado idempotentemente:** se inserta el registro `Empresa Legado` (`status = 'ACTIVE'`) en `tenants` cuando no existe, dejando lista la entidad receptora para el backfill y cierre de restricciones de **T1.1.7** sin mezclar datos existentes con empresas de demostración.
- **Reversibilidad (`downgrade`):** revierte limpiamente los índices compuestos, columnas/FKs/índices `tenant_id` y las tablas `subscriptions`, `subscription_plans` y `tenants` preservando los datos legados existentes.

**TDD y verificación:**
1. **RED:** Se añadieron 3 pruebas en `backend/tests/test_saas_models.py` (`test_t1_1_6_additive_alembic_migration_exists_and_revises_previous_head`, `test_t1_1_6_additive_migration_upgrade_and_downgrade_on_disposable_db`, `test_t1_1_6_migration_generates_additive_postgresql_ddl`). Se observó fallo inicial (`ResolutionError: No such revision or branch 'p7l0m3n5q7r9'` y `ModuleNotFoundError` → **3 failed, 10 passed**), y durante la primera corrida de validación sobre base descartable se detectó y corrigió el nombre físico de la tabla `ofertas_abastecimiento` (`NoSuchTableError: ofertas_abastecimiento` → **1 failed, 12 passed**).
2. **GREEN:** Corregido el nombre de tabla, `python -m pytest backend/tests/test_saas_models.py -q` → **13 passed in 1.32s**.
3. **Regresión:** `python -m pytest backend/tests -q` → **71 passed in 23.23s** (0 fallos).
- [x] **T1.1.7** Completar el backfill del tenant legado, verificar conteos/relaciones y después aplicar `NOT NULL` y restricciones finales; preservar datos y posibilidad de actualización de una base existente.

### Resultado T1.1.7 — backfill del tenant legado, verificación de relaciones y restricciones finales

Se creó la migración `backend/migrations/versions/q8m1n4p6r8s0_backfill_tenant_legado_y_restricciones.py` (`down_revision = "p7l0m3n5q7r9"`), validada sobre una base descartable en memoria con datos legados preexistentes:
- **Backfill jerárquico hacia el tenant legado (`Empresa Legado`):**
  - Asegura idempotentemente la existencia de `Empresa Legado` en `tenants`.
  - Completa `tenant_id` en tablas raíz (`usuarios`, `sucursales`, `categorias`, `proveedores`, `temporadas`, `promociones`) cuando es nulo.
  - Completa `tenant_id` en tablas dependientes (`colecciones`, `productos`, `variantes_producto`, `ofertas_abastecimiento`, `inventario`, `reservas`, `carritos`, `ventas`, `pagos`, `movimientos_inventario`, `sesiones_vestidor_virtual`, `recomendaciones_ia`) derivando primero del registro padre/agregado con `COALESCE(..., legacy_tenant_id)`.
  - En `bitacora`, asigna `tenant_id` desde `usuarios.tenant_id` cuando `usuario_id IS NOT NULL`, preservando `tenant_id IS NULL` en eventos transversales/de plataforma sin usuario de empresa.
- **Verificación de conteos y consistencia relacional (`_verify_counts_and_relationships`):**
  - Verifica que las 17 tablas operativas estrictamente tenant-owned tengan `0` registros con `tenant_id IS NULL`.
  - Ejecuta 17 comprobaciones SQL de consistencia entre padres, hijos y tablas de asociación (`colecciones -> temporadas`, `productos -> categorias/temporadas/colecciones`, `variantes_producto -> productos`, `ofertas_abastecimiento -> proveedores/variantes/temporadas`, `inventario -> sucursales/variantes_producto`, `reservas -> sucursales/usuarios`, `carritos -> usuarios`, `ventas -> sucursales`, `pagos -> ventas`, `movimientos_inventario -> inventario`, `sesiones_vestidor_virtual -> productos`, `recomendaciones_ia -> productos`, `usuario_sucursales`, `producto_proveedores`, `productos_promocion`), abortando con `RuntimeError` si existe cualquier discrepancia cross-tenant antes de aplicar `NOT NULL` o restricciones.
- **Aplicación de `NOT NULL` y restricciones únicas finales por tenant:**
  - Aplica `ALTER COLUMN tenant_id SET NOT NULL` en las 17 tablas operativas estrictamente tenant-owned (manteniendo `usuarios.tenant_id` y `bitacora.tenant_id` nullables para identidades y auditoría de plataforma).
  - Reemplaza las restricciones e índices únicos globales legados (`uq_users_email`, `uq_branches_city_name`, `uq_categories_name`, `uq_suppliers_tax_id`, `seasons_name_key`, `uq_products_code`, `uq_products_slug`, `uq_product_variants_sku`, `carts_customer_id_key`, `ix_ventas_order_number`, `uq_payment_provider_reference`, `ix_pagos_idempotency_key`) por las restricciones compuestas por tenant (`uq_users_tenant_email` + `ix_users_email`, `uq_branches_tenant_city_name`, `uq_categories_tenant_name`, `uq_suppliers_tenant_tax_id`, `uq_seasons_tenant_name`, `uq_products_tenant_code`, `uq_products_tenant_slug`, `uq_product_variants_tenant_sku` + `ix_product_variants_sku`, `uq_carts_tenant_customer` + `ix_carts_customer_id`, `uq_sales_tenant_order_number` + `ix_sales_order_number`, `uq_payments_tenant_provider_reference`, `uq_payments_tenant_idempotency_key` + `ix_payments_idempotency_key`).
  - Incluye `downgrade()` completo para restaurar la nulabilidad y las restricciones previas si se revierte la revisión.

**TDD y verificación:**
1. **RED:** Se añadieron 3 pruebas en `backend/tests/test_saas_models.py` (`test_t1_1_7_backfill_and_constraints_migration_exists_and_revises_t1_1_6`, `test_t1_1_7_backfill_verifies_relations_and_applies_not_null_and_final_constraints`, `test_t1_1_7_rejects_cross_tenant_relationship_mismatch_before_applying_constraints`). Se observó fallo inicial (`ResolutionError: No such revision or branch 'q8m1n4p6r8s0'` y `ModuleNotFoundError` → **3 failed, 13 passed**).
2. **GREEN:** Implementada la migración `q8m1n4p6r8s0_backfill_tenant_legado_y_restricciones.py`, `python -m pytest backend/tests/test_saas_models.py -q` → **16 passed in 2.14s**.
3. **Regresión:** `python -m pytest backend/tests -q` → **74 passed in 42.30s** (0 fallos).
- [x] **T1.1.8** Añadir seeds idempotentes de planes Básico/Profesional y dos empresas de prueba independientes con administradores y sucursales propias, sin mezclar sus datos con el tenant legado.

### Resultado T1.1.8 — seeds idempotentes de planes y empresas de prueba SaaS

Se actualizó `backend/app/core/seed.py` añadiendo `seed_saas_plans_and_demo_tenants(db)` e integrándolo al final de `seed_development_data()`:
- **Catálogo de planes (`SubscriptionPlan`) idempotente:**
  - `BASIC` (`name="Básico"`, `max_active_branches=2`, `generative_reports_enabled=False`, `is_active=True`).
  - `PROFESSIONAL` (`name="Profesional"`, `max_active_branches=10`, `generative_reports_enabled=True`, `is_active=True`).
- **Dos empresas de prueba SaaS independientes:**
  - `Boutique Aurora`: suscripción activa a `BASIC`, sucursales propias (`Aurora Equipetrol` en Santa Cruz y `Aurora Prado` en Cochabamba), administrador propio (`admin@boutiqueaurora.com`) y encargado de sucursal (`encargado@boutiqueaurora.com`).
  - `Moda Boreal`: suscripción activa a `PROFESSIONAL`, sucursales propias (`Boreal Las Brisas` en Santa Cruz y `Boreal Recoleta` en Cochabamba), administrador propio (`admin@modaboreal.com`) y encargado de sucursal (`encargado@modaboreal.com`).
- **Aislamiento estricto respecto al tenant legado (`Empresa Legado`):**
  - Los datos existentes de `FashionStore` (`FashionStore Centro`, `FashionStore Norte`, productos `DEMO-*`, categorías, proveedor y usuarios demo originales) quedan vinculados exclusivamente a `Empresa Legado` y nunca se reasignan ni comparten con `Boutique Aurora` o `Moda Boreal`.

**TDD y verificación:**
1. **RED:** Se agregaron 2 pruebas en `backend/tests/test_saas_models.py` (`test_t1_1_8_seed_saas_plans_and_demo_tenants_is_idempotent_and_isolated_from_legacy_tenant`, `test_t1_1_8_full_seed_development_data_populates_legacy_and_two_demo_tenants_idempotently`). Se observó fallo inicial (`ImportError: cannot import name 'DEMO_TENANT_ONE_NAME' from 'backend.app.core.seed'` → **2 failed, 16 passed**).
2. **GREEN:** Implementados los seeds en `backend/app/core/seed.py`, `python -m pytest backend/tests/test_saas_models.py -q` → **18 passed in 3.82s**.
3. **Regresión:** `python -m pytest backend/tests -q` → **76 passed in 26.87s** (0 fallos).

## Fase 1.2 — Identidad, aislamiento backend y gobernanza de suscripciones

- [x] **T1.2.1** Incorporar la pertenencia tenant a la autenticación actual y resolver el tenant desde el usuario/sesión validada; no confiar en IDs de tenant arbitrarios del request.

### Resultado T1.2.1 — pertenencia tenant en autenticación y resolución desde sesión validada

Se integró el contexto de empresa (`tenant_id` y `tenant`) en el flujo de autenticación (`backend/app/core/security.py`, `backend/app/modules/auth/schemas.py`, `backend/app/modules/auth/service.py`, `backend/app/modules/auth/dependencies.py` y `backend/app/modules/auth/router.py`):
- **Claim `tenant_id` en JWT y respuestas de usuario (`UserResponse`):**
  - `create_access_token` incluye `"tenant_id": tenant_id` en el payload del access token.
  - `UserResponse` y `/api/v1/auth/me` exponen `tenant_id` y `tenant` (`{id, name, status}`) junto con las sucursales filtradas al propio tenant del usuario.
  - `login` soporta correos repetidos entre distintas empresas (`uq_users_tenant_email`) evaluando la credencial sobre los candidatos activos y resolviendo el `tenant` exclusivamente desde el registro `User` autenticado en base de datos.
- **Validación de membresía y estado del tenant en sesión (`get_current_user`, `get_current_tenant`, `get_current_tenant_id`):**
  - `get_current_user` carga `User.tenant` desde la sesión persistida, verifica que el claim `tenant_id` del token coincida con `user.tenant_id` en base de datos (`401 Unauthorized` ante discrepancia/adulteración) y bloquea usuarios cuya empresa no esté `ACTIVE` (`403 TENANT_INACTIVE` en `login`, `refresh` y `get_current_user`).
  - Rechaza cualquier intento de un usuario no plataforma de suplantar otro `tenant_id` mediante cabeceras (`X-Tenant-Id`) o query params (`?tenant_id=`) con `403 TENANT_SCOPE_FORBIDDEN`, asegurando que el tenant activo siempre se derive de la sesión validada en backend.

**TDD y verificación:**
1. **RED:** Se añadieron 3 pruebas en `backend/tests/test_saas_models.py` (`test_t1_2_1_login_and_me_include_validated_tenant_membership_and_jwt_claim`, `test_t1_2_1_auth_rejects_tampered_jwt_tenant_claim_and_spoofed_client_tenant_ids`, `test_t1_2_1_inactive_or_suspended_tenant_blocks_login_refresh_and_session`). Se observó fallo inicial (`KeyError: 'tenant_id'`, `TypeError: create_access_token() got an unexpected keyword argument 'tenant_id'`, `AssertionError: assert 200 == 403` → **3 failed, 18 deselected**).
2. **GREEN:** Implementados los cambios en `security.py` y `modules/auth/*`, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_1" -q` → **3 passed in 3.95s**.
3. **Regresión:** `python -m pytest backend/tests -q` → **79 passed in 34.43s** (0 fallos).
- [x] **T1.2.2** Definir el rol de administración SaaS separado del administrador de empresa y reservar operaciones cross-tenant sólo para rutas de plataforma explícitas y autorizadas.

### Resultado T1.2.2 — separación del rol de administración SaaS y reserva de operaciones cross-tenant

Se implementó la separación estricta entre el administrador de plataforma SaaS (`PLATFORM_ADMIN`) y el administrador de empresa (`ADMIN`) en `backend/app/core/seed.py`, `backend/app/modules/auth/dependencies.py` y `backend/app/modules/users/service.py`:
- **Separación de roles y permisos (`backend/app/core/seed.py`):**
  - Se definió el rol `PLATFORM_ADMIN` (`"Administrador de Plataforma SaaS"`) separado de `ADMIN` (`"Administrador"`).
  - Se dividió el catálogo de permisos en `TENANT_PERMISSIONS` (26 permisos operativos de empresa) y `PLATFORM_PERMISSIONS` (`saas.tenants.manage`, `saas.plans.manage`, `saas.subscriptions.manage`).
  - `ROLE_PERMISSIONS["ADMIN"]` conserva únicamente `TENANT_PERMISSIONS` (disjunto de `PLATFORM_PERMISSIONS`), mientras que `ROLE_PERMISSIONS["PLATFORM_ADMIN"]` posee exclusivamente `PLATFORM_PERMISSIONS` (disjunto de `TENANT_PERMISSIONS`).
  - `seed_saas_plans_and_demo_tenants` asegura de forma idempotente los permisos de plataforma y la cuenta `platform.admin@fashionstore.com` (`tenant_id=None`, `role="PLATFORM_ADMIN"`).
- **Dependencias de autorización y reserva cross-tenant (`backend/app/modules/auth/dependencies.py`):**
  - `require_platform_admin` y `require_platform_permission` exigen `role.code == "PLATFORM_ADMIN"`, `tenant_id is None` y el permiso de plataforma activo correspondiente (`403 PLATFORM_ADMIN_REQUIRED` / `403 PLATFORM_PERMISSION_REQUIRED`), rechazando a cualquier `ADMIN` de empresa.
  - `require_admin`, `require_permission` (para permisos de empresa) y `require_branch_access` rechazan explícitamente a `PLATFORM_ADMIN` (`403 ADMIN_ROLE_REQUIRED` / `403 TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN`), impidiendo que un operador de plataforma herede acceso implícito a datos comerciales o sucursales.
  - `resolve_platform_target_tenant(permission_code)` y `_reject_untrusted_client_tenant_override` reservan las operaciones cross-tenant exclusivamente para rutas explícitas bajo `/api/v1/platform` (`403 CROSS_TENANT_PLATFORM_ROUTE_REQUIRED` fuera de dicho prefijo), exigen declarar explícitamente el tenant objetivo (`400 TARGET_TENANT_REQUIRED`) y registran auditoría en `Bitacora` (`action="PLATFORM_TARGET_ACCESS"`, actor, permiso, ruta y `target_tenant_id`).
- **Protección contra escalación desde gestión de usuarios (`backend/app/modules/users/service.py`):**
  - Se bloquea la asignación del rol `PLATFORM_ADMIN` en alta/edición de usuarios de empresa (`403 PLATFORM_ROLE_ASSIGNMENT_FORBIDDEN`) y se excluyen las identidades `PLATFORM_ADMIN` de los listados y consultas de `/api/v1/users`.

**TDD y verificación:**
1. **RED:** Se añadieron 3 pruebas en `backend/tests/test_saas_models.py` (`test_t1_2_2_platform_admin_role_and_permissions_are_strictly_separated_from_tenant_admin`, `test_t1_2_2_company_admin_is_rejected_on_platform_routes_and_cannot_escalate_to_platform_admin`, `test_t1_2_2_platform_admin_cannot_access_tenant_operational_routes_and_cross_tenant_is_reserved_for_explicit_platform_routes`). Se observó fallo inicial (`ImportError: cannot import name 'PLATFORM_ADMIN_ROLE' / 'require_platform_admin' / 'resolve_platform_target_tenant'` → **3 failed, 21 deselected**).
2. **GREEN:** Implementada la separación de roles, dependencias y protecciones, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_2" -q` → **3 passed in 2.84s** (`24 passed in 11.38s` en `backend/tests/test_saas_models.py`).
3. **Regresión:** `python -m pytest backend/tests -q` → **82 passed in 43.95s** (0 fallos).
- [x] **T1.2.3** Aplicar el ámbito del tenant en los servicios y consultas de todas las rutas de datos tenant-owned; auditar endpoints existentes y relaciones para impedir lecturas, modificaciones, eliminaciones y enumeración cruzadas.

### Resultado T1.2.3 — ámbito por tenant en servicios, consultas y relaciones de rutas tenant-owned

Se aplicó el filtrado, sellado y aislamiento por tenant en la capa de sesión ORM, dependencias y servicios de todos los módulos tenant-owned (`users`, `locations`, `catalog_masters`, `suppliers`, `seasons`, `products`, `promotions`, `inventory`, `reservations`, `commerce`, `reports`, `audit`, `recommendations`, `virtual_fitting`, `catalog`, `ai_chat`):
- **Aislamiento en sesión SQLAlchemy (`backend/app/core/database.py`):**
  - Se definieron las 19 entidades `TENANT_SCOPED_MODELS` (`Branch`, `User`, `Category`, `Supplier`, `Season`, `Promotion`, `Collection`, `Product`, `ProductVariant`, `SupplierSupplyOffer`, `Inventory`, `Reservation`, `Cart`, `Sale`, `Payment`, `InventoryMovement`, `VirtualFittingSession`, `AIRecommendation`, `Bitacora`).
  - El listener `_apply_tenant_loader_criteria` (`do_orm_execute`) aplica `with_loader_criteria(..., include_aliases=True)` automáticamente sobre toda consulta (`SELECT`, `UPDATE`, `DELETE`) y carga de relaciones cuando el contexto de tenant está activo en la sesión (`session.info["tenant_context_active"] = True`).
  - El listener `_enforce_tenant_on_flush` (`before_flush`) asigna automáticamente `obj.tenant_id = tid` a las nuevas entidades creadas en la sesión y bloquea cualquier intento de persistir, modificar o eliminar instancias de otro tenant (`PermissionError`).
- **Vinculación del contexto tenant desde la autenticación (`backend/app/modules/auth/dependencies.py`, `backend/app/core/audit.py`):**
  - `bind_session_tenant_context(db, user)` enlaza el `tenant_id` validado del usuario autenticado al finalizar `get_current_user`.
  - `bind_optional_tenant_context(request, db)` vincula el contexto de tenant en routers públicos/híbridos (`catalog`, `catalogo` VTON y `ai_chat`) cuando la petición incluye un Bearer token válido.
  - `record_audit` (`backend/app/core/audit.py`) sella automáticamente `Bitacora.tenant_id` desde el usuario autenticado o el `tenant_id` activo de la sesión.
- **Auditoría y normalización de consultas/unicidad en servicios de módulos (`catalog_masters`, `seasons`, `products`, `locations`, `commerce`):**
  - Se reemplazaron accesos directos por clave primaria `db.get(...)` en `catalog_masters/service.py` (`get_master`), `seasons/service.py` (`get_season`) y `commerce/service.py` (`_line_promotion_discount`) por `db.scalar(select(...).where(...))` para garantizar que el filtro `with_loader_criteria` se aplique siempre y devuelva `404 Not Found` no enumerable ante IDs de otro tenant.
  - Se actualizaron `create_season`, `create_product` y `create_branch` para resolver `tenant_id = db.info.get("tenant_id")` en sus validaciones de unicidad y creación de entidades, impidiendo asociaciones cruzadas de categorías, temporadas, colecciones, proveedores, sucursales, variantes o productos en promociones (`400 Bad Request` / `404 Not Found`).

**TDD y verificación:**
1. **RED:** Se añadieron 2 pruebas integrales en `backend/tests/test_saas_models.py` (`test_t1_2_3_tenant_isolation_blocks_cross_tenant_reads_lists_and_enumeration_across_modules`, `test_t1_2_3_tenant_isolation_blocks_cross_tenant_mutations_deletions_and_foreign_relationships`). Se observó fallo inicial (`AssertionError: assert {1, 2, 3, 4} == {1, 2}` y `assert 200 == 404` → **2 failed, 24 deselected in 3.72s**).
2. **GREEN:** Implementados el ámbito de sesión, vinculación en dependencias/routers y ajustes de servicios, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_3" -q` → **2 passed in 5.06s** (`26 passed in 12.84s` en `backend/tests/test_saas_models.py`).
3. **Regresión:** `python -m pytest backend/tests -q` → **84 passed in 43.43s** (0 fallos).
- [x] **T1.2.4** Validar conjuntamente tenant y sucursal en las operaciones que reciben `branch_id`; devolver respuestas que no filtren datos sobre recursos de otro tenant.

### Resultado T1.2.4 — validación conjunta tenant y sucursal y respuestas no enumerables

Se implementó la validación conjunta de empresa y sucursal en todas las operaciones que reciben `branch_id` (`auth/dependencies.py`, `reports/service.py`, `inventory`, `reservations`, `commerce`):
- **Validación conjunta en `require_branch_access` (`backend/app/modules/auth/dependencies.py`):**
  - Se vinculó la verificación de pertenencia a sucursal con el `tenant_id` validado del usuario autenticado (`current_user.tenant_id`).
  - Ante una sucursal inexistente o perteneciente a otra empresa (`Branch.tenant_id != current_user.tenant_id`), se retorna inmediatamente `404 Not Found` (`{"code": "BRANCH_NOT_FOUND", "message": "Sucursal no encontrada."}`).
  - Se impide la enumeración o detección de existencia de sucursales entre empresas: una sucursal de otro tenant es indistinguible de un identificador no existente.
  - Para usuarios de empresa con rol no administrador (`CASHIER`, `BRANCH_MANAGER`), si la sucursal sí pertenece a su empresa pero no está entre sus sucursales asignadas (`user.branches`), se retorna `403 Forbidden` (`{"code": "BRANCH_ACCESS_REQUIRED", "message": "No tienes acceso a esta sucursal."}`).
  - El administrador de empresa (`ADMIN`) mantiene acceso a todas las sucursales de su propia empresa, pero queda estrictamente bloqueado de operar sobre sucursales de otra empresa (`404 Not Found`).
- **Validación de sucursal en filtros de reportes (`backend/app/modules/reports/service.py`):**
  - Se actualizó `validate_report_filters` para validar la existencia de `branch_id` en el tenant de la sesión sobre `dashboard`, `sales_by_branch`, `top_products`, `low_stock`, `reservations_summary`, `sales_by_channel`, `revenue_summary` y `assistant_report`, retornando `404 Not Found` (`BRANCH_NOT_FOUND`) si el parámetro `branch_id` corresponde a otra empresa o no existe.
- **Validación en creación de operaciones comerciales y reservas:**
  - `create_digital_purchase` (`commerce/service.py`) y `create_reservation` (`reservations/service.py`) validan `branch_id` mediante `select(Branch)` con ámbito de tenant, retornando `400 Bad Request` (`BRANCH_NOT_FOUND_OR_INACTIVE`) no enumerable ante IDs de sucursales ajenas.

**TDD y verificación:**
1. **RED:** Se añadió la prueba integral `test_t1_2_4_joint_tenant_and_branch_validation_blocks_cross_tenant_branch_id_operations_with_non_enumerable_responses` en `backend/tests/test_saas_models.py`. Se observó fallo inicial en la consulta de inventario por el administrador con `branch_id` de otra empresa (`AssertionError: Expected 404, got 200: {"items":[],"page":1,...}` → **1 failed, 26 deselected in 4.64s**).
2. **GREEN:** Implementada la validación conjunta en `require_branch_access` y `validate_report_filters`, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_4" -q` → **1 passed in 7.84s** (`27 passed in 29.24s` en `backend/tests/test_saas_models.py`).
3. **Regresión:** `python -m pytest backend/tests -q` → **85 passed in 80.45s** (0 fallos).
- [x] **T1.2.5** Implementar endpoints protegidos para registrar empresa, consultar planes, asignar/cambiar suscripción y consultar estado/vigencia; definir sus permisos y esquemas de respuesta.

### Resultado T1.2.5 — endpoints de empresas, planes y gestión de suscripciones SaaS

Se implementó el módulo [`backend/app/modules/subscriptions`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/modules/subscriptions) con rutas públicas, operativas de empresa y de administración de plataforma SaaS:
- **Catálogo de planes (`/api/v1/plans` y `/api/v1/platform/plans`):**
  - `GET /api/v1/plans`: endpoint accesible para consultar los planes activos disponibles (`BASIC`, `PROFESSIONAL`), exponiendo `code`, `name`, `max_active_branches`, `generative_reports_enabled` e `is_active`.
  - `GET /api/v1/platform/plans`: endpoint exclusivo de plataforma protegido con `require_platform_permission("saas.plans.manage")` para listar todos los planes configurados.
- **Registro y gestión de empresas (`/api/v1/platform/tenants`):**
  - `POST /api/v1/platform/tenants`: permite al administrador de plataforma registrar nuevas empresas (`TenantCreateRequest`) con su plan de suscripción inicial y, opcionalmente, la cuenta del administrador inicial (`ADMIN`), sellando auditoría en `Bitacora`.
  - `GET /api/v1/platform/tenants`: listado paginado de empresas para la plataforma.
  - `GET /api/v1/platform/tenants/{target_tenant_id}` y `PATCH /api/v1/platform/tenants/{target_tenant_id}/status`: consulta y actualización de estado (`ACTIVE`, `SUSPENDED`, `INACTIVE`) mediante `resolve_platform_target_tenant("saas.tenants.manage")`.
- **Asignación, cambio e historial de suscripción (`/api/v1/platform/tenants/{target_tenant_id}/subscriptions`):**
  - `POST /api/v1/platform/tenants/{target_tenant_id}/subscriptions`: protegido con `resolve_platform_target_tenant("saas.subscriptions.manage")`; cancela la suscripción activa previa (`status="CANCELLED"`, `valid_until=now`), crea la nueva suscripción activa vinculada al plan seleccionado y registra el cambio en `Bitacora`.
  - `GET /api/v1/platform/tenants/{target_tenant_id}/subscriptions`: historial completo de suscripciones de la empresa objetivo.
- **Consulta de vigencia y estado por la empresa (`GET /api/v1/subscriptions/current`):**
  - Endpoint accesible por el administrador de la empresa (`require_admin`); devuelve `tenant_id`, `tenant_name`, `tenant_status`, datos del plan actual, vigencia (`valid_from`, `valid_until`), `max_active_branches`, `generative_reports_enabled` y conteo de sucursales activas actuales (`active_branch_count`).
  - Bloquea al administrador de plataforma con `403 Forbidden` (`ADMIN_ROLE_REQUIRED`) e impide a los administradores de empresa acceder a endpoints de gestión de plataforma (`403 PLATFORM_ADMIN_REQUIRED`).

**TDD y verificación:**
1. **RED:** Se añadieron 2 pruebas en `backend/tests/test_saas_models.py` (`test_t1_2_5_platform_endpoints_register_tenant_consult_plans_change_subscription_and_audit` y `test_t1_2_5_tenant_consults_current_subscription_status_and_company_admin_is_blocked_from_platform_subscription_management`). Se observó fallo inicial (`assert 404 == 200` en `/api/v1/plans` y `/api/v1/subscriptions/current` → **2 failed, 27 deselected in 5.25s**).
2. **GREEN:** Implementados schemas, servicio y routers en `subscriptions/`, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_5" -q` → **2 passed in 6.45s** (`29 passed in 17.10s` en `backend/tests/test_saas_models.py`).
3. **Regresión:** `python -m pytest backend/tests -q` → **87 passed in 47.01s** (0 fallos).
- [x] **T1.2.6** Aplicar límites de sucursales activas y funcionalidades habilitadas desde backend en una operación transaccional para evitar superar cuotas concurrentemente.

### Resultado T1.2.6 — control transaccional de cuota de sucursales y feature flags por plan

Se implementó el control de límites y funcionalidades habilitadas en backend según el plan de suscripción activo de la empresa:
- **Control transaccional de cuota de sucursales activas (`_enforce_branch_limit` en `locations/service.py`):**
  - Aplicado en la creación (`POST /api/v1/branches`) y en la reactivación (`PATCH /api/v1/branches/{branch_id}/activate`).
  - Adquiere bloqueo a nivel de fila (`select(Tenant).where(...).with_for_update()` en PostgreSQL) para serializar la validación de cuotas concurrentes y evitar race conditions.
  - Comprueba la suscripción activa del tenant y su `plan.max_active_branches`. Si el conteo de sucursales activas alcanza o excede la cuota permitida, rechaza la solicitud con `409 Conflict` (`BRANCH_LIMIT_EXCEEDED`).
  - La desactivación de una sucursal (`PATCH /api/v1/branches/{branch_id}/deactivate`) reduce el conteo activo permitiendo registrar o activar otra sucursal dentro del límite.
  - La actualización de suscripción a un plan superior (ej. `BASIC` -> `PROFESSIONAL`) desbloquea inmediatamente la capacidad de agregar o reactivar más sucursales.
- **Control de feature flags por plan (`check_tenant_feature` y endpoint de reportes):**
  - Se implementó `check_tenant_feature(db, tenant_id, feature_name)` en `subscriptions/service.py`.
  - En `POST /api/v1/reports/assistant` (`reports/router.py`), se valida si el tenant tiene habilitada la funcionalidad `generative_reports_enabled`. Si el plan del tenant no incluye reportes con IA (ej. `BASIC`), la solicitud es rechazada con `403 Forbidden` (`FEATURE_NOT_IN_PLAN`).
  - Las consultas a reportes estándar (`GET /api/v1/reports/dashboard`, etc.) se mantienen accesibles en todos los planes.
  - Tras el upgrade a `PROFESSIONAL`, el endpoint de asistente de reportes queda disponible automáticamente.

**TDD y verificación:**
1. **RED:** Se añadieron 2 pruebas en `backend/tests/test_saas_models.py` (`test_t1_2_6_branch_quota_limit_enforced_transactionally_and_subscription_upgrade_unlocks_more_branches` y `test_t1_2_6_feature_flag_generative_reports_enforced_by_plan`). Se observó el fallo inicial esperado (`assert 201 == 409` en creación de sucursal 3 y `assert 200 == 403` en reporte IA con plan básico → **2 failed, 29 deselected in 7.31s**).
2. **GREEN:** Implementados los controles en `locations/service.py`, `subscriptions/service.py` y `reports/router.py`, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_6" -v` → **2 passed in 5.73s** (`31 passed in 23.01s` en `backend/tests/test_saas_models.py`).
3. **Regresión:** `python -m pytest backend/tests -q` → **89 passed in 41.17s** (0 fallos).
- [x] **T1.2.7** Implementar `GET /api/v1/sync/catalog` con tenant y sucursal derivados/validados en backend; retornar sólo catálogo autorizado, variantes, precios y disponibilidad local conocida, junto con fecha/versionado para identificar datos desactualizados.

### Resultado T1.2.7 — endpoint de sincronización de catálogo offline con derivación y validación de sucursal

Se implementó el módulo [`backend/app/modules/sync`](file:///c:/ProyectoSi2_TiendaRopa/backend/app/modules/sync) con schemas, servicio y router para la sincronización de catálogo con almacenamiento local (IndexedDB en PWA y SQLite en Flutter):
- **Endpoint `GET /api/v1/sync/catalog`:**
  - Protegido con `require_permission("catalog.read")`, accesible para cajeros, encargados de sucursal, administradores de empresa y clientes.
  - Bloquea al administrador de plataforma con `403 Forbidden` (`TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN`).
- **Derivación y validación conjunta de sucursal (`resolve_sync_branch`):**
  - **Derivación automática:** cuando no se envía `branch_id`, si el usuario tiene sucursales asignadas (como cajeros o encargados), el backend deriva automáticamente su primera sucursal autorizada; si es administrador, selecciona la primera sucursal activa de la empresa.
  - **Validación conjunta:** cuando se envía `?branch_id=...`, valida mediante `require_branch_access` que la sucursal pertenezca al `tenant_id` del usuario (retornando `404 Not Found` no enumerable ante sucursales ajenas) y que el usuario tenga asignación a ella si no es administrador (`403 Forbidden`).
- **Esquema estructurado de respuesta (`SyncCatalogResponse`):**
  - `metadata`: `tenant_id`, `tenant_name`, `branch_id`, `branch_name`, `sync_timestamp` (ISO UTC) y `catalog_version` (identificador para detectar desactualizaciones locales).
  - `categories`: lista de categorías activas pertenecientes a la empresa (`id`, `name`, `is_active`).
  - `products`: lista de productos activos de la empresa con `category_id`, `category_name`, `name`, `code`, `slug`, `price`, `image_url` principal e `is_active`.
  - `variants`: lista de variantes activas con `product_id`, `sku`, `size_id`/`size_name`, `color_id`/`color_name`, `price` e `is_active`.
  - `inventory`: disponibilidad local en la sucursal resuelta (`product_variant_id`, `stock_quantity`, `reserved_quantity`, `available_quantity`).
- **Aislamiento absoluto entre empresas:**
  - Las consultas aplican filtro estricto por `tenant_id` y por la sucursal autorizada, impidiendo que productos, variantes, categorías o inventario de otras empresas se incluyan en el payload.

**TDD y verificación:**
1. **RED:** Se añadió la prueba integral `test_t1_2_7_sync_catalog_derived_and_validated_with_offline_metadata_and_isolation` en `backend/tests/test_saas_models.py`. Se observó el fallo inicial esperado (`assert 404 == 200` en `GET /api/v1/sync/catalog` → **1 failed, 31 deselected in 3.99s**).
2. **GREEN:** Implementados schemas, servicio y router en `sync/`, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_7" -v` → **1 passed in 6.10s** (`32 passed in 19.33s` en `backend/tests/test_saas_models.py`).
3. **Regresión:** `python -m pytest backend/tests -q` → **90 passed in 41.08s** (0 fallos).
- [x] **T1.2.8** Agregar pruebas RED/GREEN de aislamiento entre dos tenants para lectura y mutación, acceso a sucursal ajena, permisos de administración SaaS y límites de plan.

### Resultado T1.2.8 — suite integral de aislamiento multi-tenant, sucursales ajenas y límites de plan

Se implementó en `backend/tests/test_saas_models.py` la prueba integral `test_t1_2_8_multi_tenant_isolation_reads_mutations_alien_branches_and_platform_perms`, validando con dos empresas independientes (`Empresa Alpha` y `Empresa Beta`) y un administrador de plataforma:
- **Aislamiento en lecturas y mutaciones:**
  - El listado de productos de Alpha sólo incluye los suyos; consultar un producto de Beta devuelve `404 Not Found` no enumerable.
  - Modificar un producto de Beta devuelve `404 Not Found`.
  - El listado de categorías de Alpha no expone categorías de Beta; consultar o mutar una categoría de Beta devuelve `404 Not Found`.
  - El listado de sucursales de Alpha sólo expone las suyas; consultar, mutar o desactivar una sucursal de Beta devuelve `404 Not Found`.
- **Acceso a sucursal ajena:**
  - Consultar inventario con `branch_id` de Beta devuelve `404 Not Found` (`BRANCH_NOT_FOUND`).
  - Sincronizar catálogo con `branch_id` de Beta devuelve `404 Not Found` (`BRANCH_NOT_FOUND`).
  - Intentar compra digital en comercio con `pickup_branch_id` de Beta devuelve `400 Bad Request` (`BRANCH_NOT_FOUND_OR_INACTIVE`).
  - Intentar reserva en sucursal de Beta devuelve `400 Bad Request` (`BRANCH_NOT_FOUND_OR_INACTIVE`).
- **Segregación de roles plataforma vs. empresa:**
  - Administrador de empresa no puede acceder a rutas `/api/v1/platform/*` (`403 Forbidden` `PLATFORM_ADMIN_REQUIRED`).
  - Administrador de plataforma no puede ejecutar operaciones operativas de empresa (`403 Forbidden` `TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN`).
- **Límites de plan y cuotas:**
  - En plan `BASIC` (máx. 2 sucursales activas), intentar crear una tercera sucursal es bloqueado con `409 Conflict` (`BRANCH_LIMIT_EXCEEDED`).
  - En plan `BASIC` sin IA, el asistente generativo devuelve `403 Forbidden` (`FEATURE_NOT_IN_PLAN`).
  - Tras el upgrade a `PROFESSIONAL` ejecutado por la plataforma, se desbloquean inmediatamente la creación de la tercera sucursal (201 Created) y el reporte con IA (200 OK).

**TDD y verificación:**
1. **RED:** Se observó fallo inicial en `test_t1_2_8` (`assert 422 in (400, 404)` por clave `items` en reserva) y `1 failed, 1 passed in 9.25s`.
2. **GREEN:** Ajustado el payload de prueba a la especificación de `ReservationCreateRequest`, `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_8" -v` → **1 passed in 4.70s**.

- [x] **T1.2.9** Agregar pruebas para el endpoint de catálogo que demuestren filtrado por tenant/sucursal y ausencia de información de otra empresa.

### Resultado T1.2.9 — pruebas de filtrado estricto en el endpoint de sincronización

Se implementó en `backend/tests/test_saas_models.py` la prueba `test_t1_2_9_sync_catalog_filtering_by_tenant_and_branch_and_absence_of_other_tenant_info`:
- Comprueba que `GET /api/v1/sync/catalog` para una empresa (`Empresa X`) devuelve únicamente sus categorías, productos, variantes y metadatos de sincronización.
- Comprueba que la disponibilidad local de inventario (`stock_quantity`, `reserved_quantity`, `available_quantity`) corresponde exclusivamente a la sucursal solicitada (probado en sucursal principal y secundaria con distintos niveles de stock).
- Verifica la ausencia total de productos, categorías, variantes o inventario de otra empresa (`Empresa Y`).
- Verifica que solicitar una sucursal de otra empresa devuelve `404 Not Found` no enumerable (`BRANCH_NOT_FOUND`).

**TDD y verificación:**
1. **GREEN:** `python -m pytest backend/tests/test_saas_models.py -k "test_t1_2_9" -v` → **1 passed in 4.50s** (`34 passed in 23.40s` en `backend/tests/test_saas_models.py`).
2. **Regresión:** `python -m pytest backend/tests -q` → **92 passed in 57.48s** (0 fallos).

## Fase 1.3 — Angular: PWA y catálogo offline con IndexedDB

- [x] **T1.3.1** Configurar la PWA para la versión Angular del proyecto: dependencia/paquete compatible, Service Worker, `manifest.webmanifest`, recursos estáticos y estrategia de caché del shell.
- [x] **T1.3.2** Verificar instalación en navegadores objetivo y que la navegación básica de la aplicación abre sin conexión después de la primera carga.
- [x] **T1.3.3** Implementar almacenamiento IndexedDB versionado para catálogo, variantes, inventario/disponibilidad y metadatos de tenant, sucursal, versión y fecha de descarga.
- [x] **T1.3.4** Implementar acción explícita para descargar/actualizar el catálogo mediante el endpoint de sincronización; mostrar éxito, error y última actualización.
- [x] **T1.3.5** Adaptar el catálogo para usar datos locales cuando no haya red y señalar claramente que precios/disponibilidad pueden estar desactualizados.
- [x] **T1.3.6** Aislar y limpiar el caché local ante logout, cambio de usuario o cambio de tenant; probar que no se presentan datos del tenant anterior.

### Resultado Fase 1.3 — PWA, Service Worker y catálogo offline con IndexedDB en Angular

Se implementó la arquitectura completa de PWA y catálogo offline para la aplicación web Angular:
- **PWA y Service Worker (`@angular/service-worker@21.0.0`):**
  - Configurado `web/ngsw-config.json` con dos grupos de activos: `app` (prefetch para `index.html`, `manifest.webmanifest`, `favicon.ico`, bundles CSS y JS) y `assets` (lazy prefetch para imágenes y tipografías).
  - Creado `web/src/manifest.webmanifest` con `display: "standalone"`, `theme_color: "#111827"`, orientación y el set completo de iconos responsivos PWA (desde 72x72 hasta 512x512 con purpose any y maskable).
  - Configurado `web/angular.json` con `"serviceWorker": "ngsw-config.json"` y copia de assets PWA en build de producción.
  - Configurado `web/src/main.ts` con `provideServiceWorker('ngsw-worker.js', { enabled: !isDevMode(), registrationStrategy: 'registerWhenStable:30000' })`.
  - Verificado que `npm run build` genera automáticamente `ngsw-worker.js` y el manifiesto compilado `ngsw.json` en `dist/fashionstore-web/browser/`.
- **Almacenamiento IndexedDB versionado (`OfflineCatalogService`):**
  - Creado [`web/src/app/core/offline/offline-catalog.service.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/offline-catalog.service.ts) con base de datos `fashionstore_offline_catalog` (v1) y object stores normalizados para `metadata` (clave `branch_id`), `categories` (`id`), `products` (`id`, índice `category_id`), `variants` (`id`, índices `product_id`, `sku`) e `inventory` (`product_variant_id`).
  - Provee consultas locales indexadas por categoría y búsqueda textual, así como consulta de disponibilidad en la sucursal.
- **Sincronización reactiva (`SyncCatalogService`):**
  - Creado [`web/src/app/core/offline/sync-catalog.service.ts`](file:///c:/ProyectoSi2_TiendaRopa/web/src/app/core/offline/sync-catalog.service.ts) que consume `GET /api/v1/sync/catalog`, almacena los datos de forma atómica en IndexedDB y expone señales reactivas (`isSyncing`, `syncError`, `lastSync`, `isOnline`) con listeners de eventos `online`/`offline`.
- **Integración en la interfaz de catálogo (`CatalogComponent`):**
  - Se añadió la barra de sincronización y estado de conectividad en el catálogo (`sync-status-bar`) con botón explícito "Descargar catálogo offline", indicador de estado ("En línea" / "Modo offline · Catálogo local"), advertencia visible de posibles datos desactualizados y fecha de última descarga.
  - Si no hay conexión o falla la red, el catálogo consulta automáticamente IndexedDB desplegando los productos locales.
- **Aislamiento y purga de caché entre usuarios y empresas:**
  - Integrada la limpieza automática de IndexedDB en `AuthService.clearSession()` y en `saveSession()` cuando cambia el usuario o el `tenant_id`, impidiendo la persistencia o visualización de datos de una empresa previa.

**Verificación:**
1. **Pruebas unitarias de servicios offline:** `web/src/app/core/offline/offline-catalog.service.spec.ts` (5 pruebas pasando).
2. **Pruebas unitarias de catálogo con modo offline:** `web/src/app/features/catalog/catalog.component.spec.ts` (7 pruebas pasando).
3. **Suite completa de pruebas web:** `cd web; npm test` → **19 suites pasadas, 77 pruebas pasadas (0 fallos)**.
4. **Compilación de producción:** `cd web; npm run build` → compila exitosamente en 10.7s generando `ngsw-worker.js` y `ngsw.json`.

## Fase 1.4 — Flutter: catálogo offline con SQLite

- [x] **T1.4.1** Seleccionar versiones compatibles de `sqflite` y `path` para el Flutter/Android/iOS objetivo y agregarlas al proyecto.
- [x] **T1.4.2** Crear una base SQLite versionada y migrable con tablas normalizadas para catálogo/variantes, inventario local conocido y metadatos de tenant, sucursal, versión y fecha.
- [x] **T1.4.3** Implementar la descarga/actualización desde el mismo endpoint `/api/v1/sync/catalog`, validando el tenant y las sucursales permitidas.
- [x] **T1.4.4** Adaptar el catálogo móvil para consultar SQLite sin conexión y conservar los datos después de reiniciar la aplicación.
- [x] **T1.4.5** Mostrar estado online/offline y advertencia de vigencia de los datos locales.
- [x] **T1.4.6** Separar/limpiar el almacenamiento local al cerrar sesión o cambiar identidad activa; probar el aislamiento local entre sesiones/tenants.

### Resultado Fase 1.4 — Catálogo offline con SQLite y sincronización en Flutter

Se implementó la arquitectura completa de catálogo offline con almacenamiento relacional SQLite en la aplicación móvil Flutter:
- **Dependencias y compatibilidad (`mobile/pubspec.yaml`):**
  - Incorporadas las dependencias compatibles `sqflite: ^2.4.5`, `path: ^1.9.1` y en entorno de desarrollo/pruebas `sqflite_common_ffi: ^2.4.5`, garantizando compatibilidad con Dart 3.12.1 y soporte para pruebas unitarias sobre SQLite in-memory / desktop.
- **Base de datos relacional SQLite versionada (`OfflineDatabase`):**
  - Creada en [`mobile/lib/core/offline/offline_database.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/core/offline/offline_database.dart) con archivo de base de datos `fashionstore_offline.db` (v1) y tablas normalizadas:
    - `metadata`: `branch_id`, `tenant_id`, `tenant_name`, `branch_name`, `sync_timestamp`, `catalog_version`.
    - `categories`: `id`, `name`, `is_active`.
    - `products`: `id`, `category_id`, `category_name`, `name`, `code`, `slug`, `price`, `image_url`, `is_active` con índices en `category_id` y `name`.
    - `variants`: `id`, `product_id`, `sku`, `size_id`, `size_name`, `color_id`, `color_name`, `price`, `is_active` con índices en `product_id` y `sku`.
    - `inventory`: `product_variant_id`, `stock_quantity`, `reserved_quantity`, `available_quantity`.
  - Operaciones atómicas bajo transacciones (`saveCatalogSync`, `clearAll`), consultas paginadas con soporte de filtros (`listProducts`), detalle estructurado (`getProductDetail`) y disponibilidad de stock local (`getVariantAvailability`).
- **Servicio de sincronización reactiva (`SyncCatalogService`):**
  - Implementado en [`mobile/lib/core/offline/sync_catalog_service.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/core/offline/sync_catalog_service.dart), consumiendo `GET /api/v1/sync/catalog` con soporte de sucursal específica (`branch_id`), persistencia atómica en SQLite y control de estado reactivo (`isSyncing`, `syncError`, `lastSync`, `lastMetadata`).
- **Consulta con fallback offline y persistencia entre reinicios:**
  - Actualizado [`mobile/lib/features/catalog/data/catalog_repository.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/features/catalog/data/catalog_repository.dart) para consultar la API en línea y, ante fallas de conectividad o red, recurrir de forma transparente a los datos de SQLite (`list`, `detail`, `availability`), asegurando que las prendas descargadas persistan y se consulten sin conexión tras reiniciar la app.
- **Interfaz visual de estado offline y advertencia de vigencia:**
  - Integrado en [`mobile/lib/features/catalog/presentation/catalog_screen.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/features/catalog/presentation/catalog_screen.dart) el widget de barra de estado `_syncStatusBar()` con:
    - Badge dinámico de conectividad ("En línea · Showroom activo" / "Modo offline · Catálogo local").
    - Banner de advertencia de vigencia visible cuando se consultan datos locales ("Precios y disponibilidad locales pueden estar desactualizados").
    - Fecha y hora de la última sincronización.
    - Botón de descarga/actualización "Descargar offline" con feedback visual de progreso.
- **Aislamiento local y purga de caché ante cambio de sesión o tenant:**
  - Actualizado [`mobile/lib/features/auth/application/auth_controller.dart`](file:///c:/ProyectoSi2_TiendaRopa/mobile/lib/features/auth/application/auth_controller.dart) para purgar automáticamente todas las tablas de SQLite en `logout()` y en `login()` cuando se detecta un cambio de usuario o `tenant_id`, evitando fuga de catálogos o inventario entre empresas.

**Verificación:**
1. **Pruebas de base de datos SQLite:** `mobile/test/offline_database_test.dart` (4 pruebas pasando).
2. **Pruebas de servicio de sincronización:** `mobile/test/sync_catalog_service_test.dart` (2 pruebas pasando).
3. **Pruebas de repositorio con fallback offline:** `mobile/test/catalog_repository_offline_test.dart` (1 prueba pasando).
4. **Pruebas visuales de estado offline en pantalla de catálogo:** `mobile/test/catalog_screen_offline_test.dart` (1 prueba pasando).
5. **Pruebas de aislamiento y purga entre usuarios/tenants:** `mobile/test/auth_controller_offline_isolation_test.dart` (2 pruebas pasando).
6. **Suite completa móvil:** `cd mobile; flutter test` → **41 pruebas pasadas (0 fallos)**.
7. **Análisis estático:** `cd mobile; dart analyze lib test` → **No issues found!**

## Fase 1.5 — Verificación, integración y artefactos ICONIX

- [x] **T1.5.1** Ejecutar migración de una base con datos previos y comprobar backfill, FKs, restricciones y preservación del tenant legado.
- [x] **T1.5.2** Ejecutar pruebas de API para dos empresas independientes y documentar resultados de acceso permitido/denegado.
- [x] **T1.5.3** Ejecutar pruebas funcionales web: primera carga, instalación, descarga de catálogo, desconexión, reinicio, consulta local y aviso de datos antiguos.
- [x] **T1.5.4** Ejecutar pruebas funcionales móvil: descarga, desconexión, cierre/reinicio, consulta SQLite y aviso de datos antiguos.
- [x] **T1.5.5** Ejecutar los checks focalizados backend, build/tests web y análisis/tests Flutter; registrar comandos exactos, resultados y bloqueos sin ocultarlos.
- [x] **T1.5.6** Actualizar ICONIX: casos oficiales CU-01, CU-02, CU-03, CU-04, CU-05, CU-06, CU-07, CU-23, CU-24 y CU-25 pertinentes, modelo de dominio, robustez y secuencia para alta/plan, autorización tenant y descarga/consulta offline; documentar correspondencia con lo implementado.
- [x] **T1.5.7** Actualizar este estado con conteo real de tareas terminadas, riesgos abiertos y evidencia; no marcar la etapa como completa si queda algún criterio de aceptación incumplido.

### Resultado Fase 1.5 — Verificación, Integración y Documentación ICONIX

> **Vigencia de la evidencia:** los totales detallados en el resultado histórico abajo son del cierre original. La revalidación posterior a CU-03/CU-04/CU-07 se documenta en `odd/tasks/landing-trial-saas.md` y en el estado actual al inicio de este documento.

1. **T1.5.1 (Migración E2E y Backfill de Datos Previos):**
   - Implementada y verificada la prueba `test_t1_5_1_end_to_end_legacy_migration_with_preexisting_data_and_isolation` en `backend/tests/test_saas_models.py`.
   - Comprobó la creación y preservación del tenant `Empresa Legado`, asignación de `tenant_id` sin nulos en las 17 tablas operativas, validación de integridad referencial padre-hijo/asociación y funcionamiento de las restricciones de unicidad compuestas `(tenant_id, ...)`.
   - Resultado: **1 passed in 1.15s**.

2. **T1.5.2 (Pruebas de Aislamiento de API entre Tenants Independientes):**
   - Ejecutadas las pruebas de aislamiento multi-tenant `test_t1_2_8` y `test_t1_2_9` en `backend/tests/test_saas_models.py`.
   - Verificó bloqueo de lectura/mutación cross-tenant con respuestas no enumerables `404 Not Found` en productos, categorías y sucursales; bloqueo de sucursales ajenas en inventario, ventas, reservas y sync; separación de roles SaaS (`PLATFORM_ADMIN` vs `ADMIN`); y cumplimiento de límites de plan y sincronización de catálogo.
   - Resultado: **2 passed in 9.51s**.

3. **T1.5.3 (Pruebas Funcionales Web PWA e IndexedDB):**
   - Comprobada la configuración PWA y la estrategia de Service Worker.
   - Ejecución del build de producción: `npm run build` en `web` completada con éxito en 17.8s, generando `ngsw-worker.js` y `ngsw.json` con precaché del shell y assets.
   - Suite completa de pruebas web: `npm test` → **77 pruebas pasadas en 19 suites (0 fallos)** en 64.74s.

4. **T1.5.4 (Pruebas Funcionales Móvil Flutter y SQLite):**
   - Ejecutadas las 10 pruebas focalizadas de persistencia local y sincronización offline en Flutter:
     - `mobile/test/offline_database_test.dart` (4 passed).
     - `mobile/test/sync_catalog_service_test.dart` (2 passed).
     - `mobile/test/catalog_repository_offline_test.dart` (1 passed).
     - `mobile/test/catalog_screen_offline_test.dart` (1 passed).
     - `mobile/test/auth_controller_offline_isolation_test.dart` (2 passed).
   - Resultado: **10 passed (0 fallos)**.

5. **T1.5.5 (Verificación de Regresión y Checks Globales):**
   - **Backend:** `python -m pytest backend/tests -q` → **93 passed** en 78.05s.
   - **Web:** `cd web; npm test` → **77 passed** en 64.74s; `npm run build` → **Succeeded** en 17.8s.
   - **Móvil:** `cd mobile; flutter test` → **41 passed** en 10 suites; `dart analyze lib test` → **No issues found!**

6. **T1.5.6 (Artefactos ICONIX):**
   - Documentado en [`docs/uml/diagramas_uml.md`](file:///c:/ProyectoSi2_TiendaRopa/docs/uml/diagramas_uml.md) la Sección 15 completa:
     - **Modelo de Dominio (15.2):** Diagrama de clases Mermaid con `Tenant`, `SubscriptionPlan`, `Subscription` y `OfflineCatalogStorage`.
     - **Diagramas de Robustez BCE (15.3):**
       - CU-01/CU-03: Alta de empresa SaaS y asignación de suscripción; CU-02 se aplica a la gestión de planes.
       - Alcance transversal, relacionado con CU-05: autenticación, derivación y autorización multi-tenant.
       - CU-04: Aplicación y control transaccional de cuota de sucursales por plan.
       - CU-06/CU-07/CU-23/CU-24/CU-25: Descarga, consulta y persistencia del catálogo offline, conectividad y capacidades PWA/SQLite.
     - **Diagramas de Secuencia (15.4):**
       - Secuencia de alta y asignación de plan.
       - Secuencia de aislamiento multi-tenant y bloqueo no enumerable cross-tenant (`404 Not Found`).
       - Secuencia de sincronización de catálogo, persistencia atómica local (IndexedDB/SQLite) y fallback offline con aviso de vigencia.
     - **Matriz de Correspondencia ICONIX–Código (15.5):** Relaciona los elementos de análisis con sus componentes implementados; las asociaciones a los CU oficiales se identifican en los encabezados de 15.3–15.4.

7. **T1.5.7 (Cierre de Auditoría de Criterios de Aceptación Etapa 1):**
   - El conteo **36/36** describe únicamente las tareas de la checklist histórica; la auditoría posterior agregó brechas CU-03, CU-04 y CU-07.
   - Esas brechas se corrigieron y verificaron. La regresión posterior completa pasó: backend **111 tests**, Web **107 tests / 24 archivos**, Flutter **60 tests**, `dart analyze lib test` sin issues, y Playwright PWA de producción **1 test**.
   - La migración CU-03 pasó un round-trip upgrade/downgrade contra SQLite `:memory:`. No se ejecutó contra una base persistente.
   - Resultado: **implementación de los 10 CU oficiales de Etapa 1 cerrada con evidencia automatizada**. La limitación de no desplegar/aplicar migración persistente se mantiene explícita.

## Hitos y secuencia de entrega

- **25/10 — Presentación 1:** mostrar modelo y migración tenant con datos existentes preservados, dos tenants de prueba y una prueba de aislamiento backend. Si algún elemento no está integrado, presentarlo como pendiente explícito.
- **01/11 — Presentación 2:** mostrar descarga/consulta offline persistente en al menos una plataforma y el avance verificable de la otra; completar ambas para cierre de Etapa 1.
- **08/11 — Presentación 3:** etapa integrada con pruebas web y móvil, aislamiento local/remoto y artefactos ICONIX actualizados.
- **10/11 — Defensa:** demostrar los criterios de aceptación y distinguir capacidades terminadas de extensiones o pendientes.

## Comandos de verificación

Ejecutar los comandos desde los directorios indicados; las pruebas de código siguen el protocolo RED → GREEN → refactor:

- Backend, desde la raíz: `python -m pytest backend/tests -q`.
- Angular, desde `web`: `npm test` y `npm run build`.
- Flutter, desde `mobile`: `flutter test` y `flutter analyze`.
- Para cada tarea, agregar primero su prueba focalizada y registrar el comando y resultado observados. Los comandos integrales anteriores se ejecutan en la verificación de etapa.

## Criterios de aceptación de la Etapa 1

- Dos tenants de prueba existen con administradores y sucursales separados; los datos previos permanecen en el tenant legado.
- Las consultas y mutaciones de recursos tenant-owned no permiten acceso cruzado, incluso manipulando IDs de empresa/sucursal en el request.
- Planes y límites configurados se aplican en backend, no sólo en las interfaces.
- El endpoint de catálogo devuelve sólo datos del tenant y sucursal autorizados.
- La PWA es instalable en navegador compatible, mantiene el shell y consulta un catálogo descargado sin conexión.
- Flutter conserva y consulta el catálogo descargado en SQLite después de reiniciar.
- Ambas aplicaciones muestran estado offline y posible desactualización; ninguna muestra caché de otro usuario/tenant.
- Migración desde el estado previo y pruebas automatizadas/funcionales tienen evidencia registrada.
- Los diagramas ICONIX describen el comportamiento realmente implementado.

## Fuera del alcance de esta etapa

Registro de ventas o reservas offline, cola de transacciones, reintentos de venta, idempotencia de transacciones comerciales, resolución de conflictos de stock, reportes generativos, modelos de Machine Learning y asesor de estilo con foto. Esos elementos permanecen en etapas posteriores y no deben marcarse como cubiertos por la descarga del catálogo.
