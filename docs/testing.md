# Estrategia de pruebas

## Backend

Ejecutar desde `backend/`:

```bash
pytest -q
ruff check app migrations tests
```

Las pruebas cubren autenticación, autorización ADMIN, usuarios, ciudades,
sucursales, maestros, proveedores, productos, variantes, inventario,

## Angular

Ejecutar desde `web/`:

```bash
npm test
npm run build
```

Se prueban `AuthService`, el guard ADMIN y `CatalogService` mediante el cliente
HTTP de pruebas. Los flujos web del Ciclo 2 requieren pruebas E2E específicas
para carrito, checkout, POS, reservas y operaciones de inventario.

## Flutter

Ejecutar desde `mobile/`:

```bash
flutter analyze
flutter test
flutter build apk --debug
```

Se prueban el arranque, parsing de catálogo y disponibilidad, autenticación y
errores estructurados del cliente HTTP.

## Criterio de validación del Ciclo 2

La validación debe cubrir el flujo exitoso, autorización por rol, acceso por
sucursal, validaciones de entrada, rollback transaccional, concurrencia,
idempotencia y auditoría. La matriz de criterios de aceptación está en
`docs/cycle-2-contracts.md`.

La expiración puede ejecutarse como tarea programada con:

```bash
python -m app.modules.reservations.expiration
```

## Línea base registrada

La ejecución inicial de la Fase 0 produjo estos resultados:

| Suite | Resultado |
| --- | --- |
| Backend `pytest -q` | 20 pruebas aprobadas |
| Backend `ruff check app migrations tests` | Aprobado |
| Web `npm test` | 6 pruebas aprobadas |
| Web `npm run build` | Aprobado |
| Móvil `flutter analyze` | Sin problemas |
| Móvil `flutter test` | Todas las pruebas aprobadas |

Estos resultados validan la línea base técnica, pero no certifican todavía los
criterios completos del Ciclo 2. Los casos faltantes se incorporarán durante
las fases de implementación de cada CU.
## Datos demo locales

Al ejecutar `docker compose up -d --build`, el servicio `seed` crea datos demo
idempotentes para probar catálogo, reservas, inventario, ventas y permisos. Usa
estas cuentas en la web:

| Rol | Correo | Contraseña |
| --- | --- | --- |
| CLIENT | `client.demo@fashionstore.com` | `Client123!` |
| BRANCH_MANAGER | `manager.demo@fashionstore.com` | `Manager123!` |
| CASHIER | `cashier.demo@fashionstore.com` | `Cashier123!` |

El administrador usa `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD` definidos en
`.env`.
