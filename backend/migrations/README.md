# Migraciones Alembic

Las migraciones versionan el esquema completo de los tres ciclos. La primera
revision crea la base del Ciclo 1, la segunda agrega sesiones de actualizacion,
la tercera incorpora las operaciones comerciales, innovacion, analitica y la
tabla `bitacora`; las revisiones siguientes traducen tablas, indices y columnas
de la bitacora.

Ejecutar con:

```bash
alembic upgrade head
```
