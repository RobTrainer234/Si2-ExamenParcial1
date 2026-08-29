# Productos del Ciclo 1

Los productos se administran bajo `/api/v1/products` y requieren `ADMIN`.

Una creación puede incluir:

- categoría activa;
- precio positivo;
- proveedores activos;
- variantes con talla, color y SKU;
- imágenes registradas mediante URL.

La base de datos impide repetir códigos, slugs, SKU y combinaciones de
producto, talla y color. Las imágenes usan URL para permitir migrar después a
S3, Cloudinary u otro proveedor sin cambiar el dominio del producto.

Endpoints adicionales:

```text
POST /api/v1/products/{product_id}/variants
POST /api/v1/products/{product_id}/images
```
