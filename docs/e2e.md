# Pruebas E2E

Las pruebas E2E usan Playwright y cubren un smoke test del catálogo público y
el acceso administrativo a la bitácora.

## Preparacion

Desde `web`:

```bash
npm install
npx playwright install chromium
```

Los servicios deben estar disponibles en `http://localhost:4200` y la API en
`http://localhost:8000`. Playwright reutiliza el frontend existente cuando no
se ejecuta en CI; si no está levantado, inicia `ng serve` automáticamente.

## Ejecucion

```bash
npm run e2e
npm run e2e:headed
npm run e2e:report
```

El flujo administrativo requiere credenciales fuera del repositorio:

```powershell
$env:E2E_ADMIN_EMAIL = "admin@fashionstore.local"
$env:E2E_ADMIN_PASSWORD = "<password-del-seed>"
npm run e2e
```

También se puede cambiar la URL con `E2E_BASE_URL`. Nunca se deben guardar
estas variables en archivos versionados.
