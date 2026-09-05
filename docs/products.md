# Productos del Ciclo 1

Los productos se administran bajo `/api/v1/products` y requieren `ADMIN`.

Una creación puede incluir:

- categoría activa;
- temporada y colección activas, con la colección perteneciente a la temporada;
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

Las imágenes se registran mediante URLs HTTPS públicas. La primera imagen puede
marcarse como principal y cada imagen debe utilizar un `sort_order` diferente:

```json
{
  "image_url": "https://images.example.com/camisa-frontal.jpg",
  "is_primary": true,
  "sort_order": 0
}
```

Las temporadas y colecciones se administran mediante `/api/v1/seasons` y
`/api/v1/collections`. Ambas operaciones requieren `ADMIN`.
