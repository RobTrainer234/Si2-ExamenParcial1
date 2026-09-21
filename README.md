# FashionStore

Plataforma de comercio electrónico para una cadena de tiendas de ropa.
Este repositorio contiene la implementación incremental de los Ciclos 1, 2 y 3.

## Stack fijado

- Python `3.13.15`, FastAPI `0.116.1`, SQLAlchemy `2.0.43`, Alembic `1.16.4`
- Angular `21.0.0`, TypeScript `5.9.2`, Node.js `22`
- Flutter `3.44.1`, Dart `3.12.1`
- PostgreSQL `17.11-alpine`
- Docker Compose `v5`

## Inicio local con Docker

1. Copiar `.env.example` a `.env` y cambiar los valores sensibles.
2. Ejecutar `docker compose up --build`.
3. API: `http://localhost:8000/docs`.
4. Healthcheck: `http://localhost:8000/health`.
5. Web: `http://localhost:4200`.

El primer arranque puede tardar mientras el servicio web ejecuta `npm install`.
Los servicios `migrate` y `seed` aplican las migraciones y crean el usuario
administrador de desarrollo antes de iniciar el backend.

## Comandos útiles

```bash
docker compose build
docker compose up
docker compose down
docker compose logs -f backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.core.seed
docker compose ps
```

Compose ejecuta `alembic upgrade head` mediante el servicio `migrate` antes de
iniciar el backend. Para producción se dispone de `docker-compose.prod.yml`,
que usa el build multi-stage de Angular con Nginx y no habilita hot reload.

## Produccion

1. Crear `.env` con valores reales. No usar las contrasenas de `.env.example`.
2. Definir una clave `JWT_SECRET` larga y aleatoria.
3. Construir y levantar el stack:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

La aplicacion queda disponible en el puerto definido por `WEB_PORT` (80 por
defecto). Nginx sirve Angular y redirige `/api/` al backend. Para detenerla:

```bash
docker compose -f docker-compose.prod.yml down
```

El volumen `postgres_data` conserva los datos al ejecutar `docker compose down`.
Para eliminarlo explícitamente: `docker compose down -v`.

El seed crea los roles base y el administrador definido por
`SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD`. Solo se puede ejecutar con
`APP_ENV=development`.

El seed es idempotente: no duplica roles, usuarios ni registros demo existentes.

En el entorno Docker de desarrollo también carga escenarios demo para el Ciclo
2: sucursales, usuarios `CLIENT`, `BRANCH_MANAGER` y `CASHIER`, temporadas,
colecciones, productos, variantes e inventario. Las credenciales demo son:

```text
client.demo@fashionstore.com / Client123!
manager.demo@fashionstore.com / Manager123!
cashier.demo@fashionstore.com / Cashier123!
```

El seed demo solo se ejecuta con `APP_ENV=development` y no reemplaza registros
existentes.

La implementación del Ciclo 2 se documenta en `docs/cycle-2.md`. Sus contratos,
roles y criterios de aceptación están definidos en
`docs/cycle-2-contracts.md`.

La implementación ampliada del Ciclo 3 se documenta en `docs/cycle-3.md` y
`docs/cycle-3-academic-report.md`. Incluye dashboard administrativo, reportes
exportables en Excel/PDF/PowerPoint y un asistente de reportes basado en
OpenAI Responses API con fallback local.

La configuración del bridge MCP para Enterprise Architect y la guía para crear
el modelo UML se encuentran en `antigravity.jsonc` y
`docs/enterprise-architect-mcp.md`. El modelo previsto es
`docs/uml/FashionStore.qea`.

## Desarrollo fuera de Docker

Backend:

```bash
cd backend
python -m venv .venv
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```

Web:

```bash
cd web
npm install
npm start
npm test
npm run build
npm run e2e
```

Las pruebas E2E requieren Chromium de Playwright y credenciales de
administrador definidas mediante `E2E_ADMIN_EMAIL` y `E2E_ADMIN_PASSWORD`.
Consultar `docs/e2e.md`.

Mobile:

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000/api/v1
flutter test
```

En el emulador Android, `10.0.2.2` apunta al host local. En un dispositivo
fisico se debe usar la IP accesible del equipo que ejecuta el backend.

## Verificacion completa

```bash
cd backend && pytest -q && ruff check app migrations tests
cd ../web && npm test && npm run build
cd ../mobile && flutter analyze && flutter test && flutter build apk --debug
```

Para comprobar Docker despues del arranque:

```bash
curl http://localhost:8000/health
curl http://localhost:4200/
```

Las funcionalidades de reservas, carrito, pagos, inventario completo, IA y
realidad aumentada quedan fuera del Ciclo 1.
