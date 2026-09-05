# Trazabilidad del Ciclo 1

## Incluido

| Area | Estado | Implementacion principal |
| --- | --- | --- |
| Usuarios y autenticacion | Completo | Registro, login, logout, refresh, Argon2id, JWT y roles |
| Administracion | Completo | Usuarios, ciudades, sucursales, categorias, tallas, colores y proveedores |
| Catalogo | Completo | Productos, variantes, imagenes, filtros, detalle y disponibilidad |
| Inventario inicial | Completo | Existencias por variante y sucursal, ajustes y movimientos auditados |
| Web | Completo | Angular, guards, interceptor JWT, catalogo y panel admin |
| Mobile | Completo | Flutter, Riverpod, sesion, catalogo y disponibilidad |
| Persistencia | Completo | PostgreSQL, SQLAlchemy y migraciones Alembic |
| Operacion | Completo | Docker Compose, healthchecks, migracion one-shot y Nginx productivo |

La separación funcional entre registro y autenticación se documenta en
`docs/cycle-1-cu1-cu2.md`.

## Verificacion realizada

- Backend: 11 pruebas exitosas.
- Angular: 6 pruebas exitosas y build de produccion exitoso.
- Flutter: 5 pruebas exitosas, analisis estatico sin issues y APK debug generado.
- Docker: configuraciones de desarrollo/produccion validas; migraciones aplicadas;
  backend saludable y web respondiendo HTTP 200.

## Fuera de alcance

No forman parte del Ciclo 1: carrito, reservas, checkout, pagos, ventas,
movimientos completos de inventario, IA, realidad aumentada y reportes
avanzados.

## Riesgos pendientes

- Antes de desplegar, sustituir todos los valores sensibles de `.env.example`.
- El seed actual solo prepara roles y administrador; los datos de catalogo deben
  cargarse mediante la API administrativa.
- Deben añadirse pruebas E2E de navegador y dispositivo si el siguiente ciclo
  requiere validacion visual o de hardware real.
- El abastecimiento del Ciclo 1 registra ofertas por proveedor y variante; las
  órdenes de compra y recepción física pertenecen a un alcance posterior.
