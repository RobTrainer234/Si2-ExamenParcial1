# Proveedores y abastecimiento del Ciclo 1

Los proveedores se administran mediante `/api/v1/suppliers` y requieren el
permiso `suppliers.manage`. Los productos mantienen la asociación comercial con
sus proveedores mediante `supplier_ids`.

## Ofertas de abastecimiento

Una oferta registra la disponibilidad que un proveedor puede entregar para una
variante concreta, temporada y colección opcional:

```text
GET   /api/v1/suppliers/{supplier_id}/offers
POST  /api/v1/suppliers/{supplier_id}/offers
PATCH /api/v1/suppliers/{supplier_id}/offers/{offer_id}
GET   /api/v1/suppliers/me/offers
PATCH /api/v1/suppliers/me/offers/{offer_id}
```

Los estados disponibles son `AVAILABLE`, `LIMITED`, `OUT_OF_STOCK` y `UPCOMING`.
El administrador define las asociaciones de proveedor, variante, temporada y
colección. El proveedor asociado puede actualizar únicamente el estado,
cantidad, fecha estimada y observaciones de su propia oferta.

El sistema valida que el proveedor esté asociado al producto de la variante,
que la temporada y colección estén activas y que la colección pertenezca a la
temporada seleccionada. Las mutaciones se registran en `bitacora`.

Este alcance no incluye órdenes de compra, recepción física, pagos a
proveedores ni logística.
