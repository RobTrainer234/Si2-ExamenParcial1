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
HTTP de pruebas.

## Flutter

Ejecutar desde `mobile/`:

```bash
flutter analyze
flutter test
flutter build apk --debug
```

Se prueban el arranque, parsing de catálogo y disponibilidad, autenticación y
errores estructurados del cliente HTTP.
