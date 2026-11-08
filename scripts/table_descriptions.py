# Diccionario de descripciones funcionales y de negocio para las 38 tablas de FashionStore

TABLE_MODULES = {
    # 1. Multi-tenancy SaaS
    "tenants": {
        "module": "1. Multi-tenancy SaaS",
        "description": "Entidad fundamental del modelo SaaS. Representa a cada empresa, marca de ropa o franquicia cliente que contrata la plataforma. Garantiza el aislamiento lógico multi-inquilino de los datos.",
        "columns": {
            "id": "Identificador único correlativo del tenant (empresa cliente).",
            "name": "Nombre comercial o razón social de la empresa cliente.",
            "status": "Estado operativo del tenant: ACTIVE (activo), SUSPENDED (suspendido por pago), INACTIVE (inactivo).",
            "created_at": "Marca de tiempo de registro de la empresa en la plataforma.",
            "updated_at": "Marca de tiempo de la última modificación de los datos de la empresa."
        }
    },
    "subscription_plans": {
        "module": "1. Multi-tenancy SaaS",
        "description": "Catálogo de planes de suscripción comercializables (Básico, Profesional, Enterprise) que definen precios y cuotas de uso de recursos.",
        "columns": {
            "id": "Identificador único correlativo del plan de suscripción.",
            "code": "Código nemotécnico único del plan (ej. BASIC, PRO, ENTERPRISE).",
            "name": "Nombre descriptivo comercial del plan.",
            "price_monthly": "Tarifa mensual en la moneda especificada.",
            "price_annual": "Tarifa anual con descuento comercial por prepago.",
            "currency": "Código de moneda según ISO 4217 (ej. BOB, USD).",
            "max_active_branches": "Cuota máxima de sucursales u almacenes físicos que el tenant puede mantener activos simultáneamente.",
            "generative_reports_enabled": "Habilita o restringe el acceso al motor de IA Generativa para reportes ejecutivos por texto y voz.",
            "is_active": "Indicador lógico de disponibilidad del plan para nuevas contrataciones."
        }
    },
    "subscriptions": {
        "module": "1. Multi-tenancy SaaS",
        "description": "Registro de contratos de suscripción formalizados por cada tenant, controlando su ciclo de vida, vigencia temporal, estados y pausas operativas.",
        "columns": {
            "id": "Identificador único de la suscripción contratada.",
            "tenant_id": "Empresa cliente titular del contrato de suscripción.",
            "plan_id": "Plan de suscripción contratado y asociado.",
            "status": "Estado del ciclo de suscripción: ACTIVE, CANCELLED, EXPIRED, SUSPENDED, PAUSED.",
            "valid_from": "Fecha y hora de inicio de vigencia de la suscripción.",
            "valid_until": "Fecha y hora límite de expiración o renovación del servicio.",
            "paused_at": "Fecha y hora en que se activó la pausa temporal de la suscripción (si aplica)."
        }
    },

    # 2. Seguridad y RBAC
    "roles": {
        "module": "2. Seguridad y Control de Acceso (RBAC)",
        "description": "Catálogo de roles de usuario para el modelo de control de acceso RBAC (Role-Based Access Control).",
        "columns": {
            "id": "Identificador único correlativo del rol.",
            "code": "Código único en mayúsculas del rol (SUPER_ADMIN, TENANT_ADMIN, STORE_MANAGER, CASHIER, SELLER, CUSTOMER, SUPPLIER).",
            "name": "Nombre descriptivo y formal del rol.",
            "is_active": "Indica si el rol está activo en el sistema."
        }
    },
    "permisos": {
        "module": "2. Seguridad y Control de Acceso (RBAC)",
        "description": "Catálogo maestro de permisos atómicos y privilegios del sistema para autorización granular en backend.",
        "columns": {
            "id": "Identificador único correlativo del permiso.",
            "code": "Clave única del permiso (ej. sales:create, inventory:adjust, reports:generative).",
            "name": "Descripción legible de la operación o privilegio concedido.",
            "is_active": "Indica si el permiso se encuentra habilitado."
        }
    },
    "rol_permisos": {
        "module": "2. Seguridad y Control de Acceso (RBAC)",
        "description": "Tabla asociativa N:M que mapea la matriz de privilegios y permisos asignados a cada rol del sistema.",
        "columns": {
            "role_id": "Rol al que se le confiere el permiso.",
            "permission_id": "Permiso atómico otorgado al rol."
        }
    },
    "usuarios": {
        "module": "2. Seguridad y Control de Acceso (RBAC)",
        "description": "Cuentas de usuario de la plataforma: administradores globales, administradores de empresa, personal de sucursal, clientes y proveedores.",
        "columns": {
            "id": "Identificador único correlativo del usuario.",
            "tenant_id": "Empresa cliente a la que pertenece el usuario (NULL para superadministradores SaaS globales).",
            "role_id": "Rol de seguridad asignado para control de acceso RBAC.",
            "supplier_id": "Vínculo al perfil de proveedor en caso de tratarse de un usuario externo del portal B2B.",
            "first_name": "Nombres del usuario.",
            "last_name": "Apellidos del usuario.",
            "email": "Correo electrónico corporativo o personal, utilizado como identificador de login (único por tenant).",
            "phone": "Teléfono de contacto o celular.",
            "password_hash": "Hash criptográfico seguro de la contraseña (generado mediante algoritmo bcrypt/argon2).",
            "is_active": "Indicador lógico de cuenta activa o bloqueada.",
            "created_at": "Fecha y hora de creación de la cuenta.",
            "updated_at": "Fecha y hora de la última modificación del perfil."
        }
    },
    "usuario_sucursales": {
        "module": "2. Seguridad y Control de Acceso (RBAC)",
        "description": "Tabla asociativa N:M que asigna a los empleados (cajeros, encargados, vendedores) a una o más sucursales físicas donde tienen autorización de operar.",
        "columns": {
            "user_id": "Identificador del usuario empleado.",
            "branch_id": "Identificador de la sucursal física habilitada para el empleado."
        }
    },
    "sesiones_actualizacion": {
        "module": "2. Seguridad y Autenticación",
        "description": "Gestión de sesiones persistentes y Refresh Tokens para la renovación periódica de tokens JWT de corta duración.",
        "columns": {
            "id": "Identificador único de la sesión o token.",
            "user_id": "Usuario titular de la sesión de autenticación.",
            "session_id": "Identificador unívoco de la sesión cliente (UUID / dispositivo).",
            "token_hash": "Hash criptográfico SHA-256 del Refresh Token persistido.",
            "expires_at": "Fecha y hora límite de expiración del token de refresco.",
            "revoked_at": "Fecha y hora de revocación explícita (cierre de sesión o invalidación preventiva).",
            "created_at": "Fecha y hora de emisión del token."
        }
    },

    # 3. Ubicaciones Geográficas y Sucursales
    "ciudades": {
        "module": "3. Ubicaciones y Red Física",
        "description": "Catálogo general de ciudades y regiones geográficas donde operan los puntos de venta.",
        "columns": {
            "id": "Identificador único correlativo de la ciudad.",
            "name": "Nombre de la ciudad (ej. Santa Cruz de la Sierra, La Paz, Cochabamba).",
            "is_active": "Indica si la ciudad está activa para operaciones logísticas."
        }
    },
    "sucursales": {
        "module": "3. Ubicaciones y Red Física",
        "description": "Puntos de venta físicos, tiendas y almacenes operados por cada tenant, con control de cuotas por plan de suscripción.",
        "columns": {
            "id": "Identificador único correlativo de la sucursal.",
            "tenant_id": "Empresa tenant propietaria del establecimiento comercial.",
            "city_id": "Ciudad geográfica donde radica el establecimiento.",
            "name": "Nombre o denominación comercial de la sucursal (ej. Sucursal Equipetrol, Central Almacén).",
            "address": "Dirección física exacta de la tienda.",
            "phone": "Teléfono fijo o celular de la sucursal.",
            "latitude": "Coordenada geográfica de latitud para geolocalización y mapas.",
            "longitude": "Coordenada geográfica de longitud para geolocalización y mapas.",
            "is_active": "Indica si la sucursal se encuentra operativa."
        }
    },

    # 4. Catálogo de Prendas y Moda
    "categorias": {
        "module": "4. Catálogo y Taxonomía de Prendas",
        "description": "Clasificación taxonómica de las prendas de vestir comercializadas (ej. Camisas, Pantalones, Vestidos, Chaquetas).",
        "columns": {
            "id": "Identificador único correlativo de la categoría.",
            "tenant_id": "Empresa cliente a la que pertenece esta categoría de productos.",
            "name": "Nombre de la categoría textil.",
            "description": "Descripción opcional o detalles del tipo de prendas incluidas.",
            "is_active": "Estado de activación en el catálogo."
        }
    },
    "tallas": {
        "module": "4. Catálogo y Taxonomía de Prendas",
        "description": "Sistema maestro paramétrico de tallas para prendas de vestir y calzado, organizado por escalas alfanuméricas, numéricas y calzado.",
        "columns": {
            "id": "Identificador único correlativo de la talla.",
            "name": "Etiqueta visible de la talla (ej. XS, S, M, L, XL, 38, 40, 42).",
            "size_type": "Tipo de escala de talla: ALPHA (alfanumérica), NUMERIC (numérica textil), SHOE (calzado).",
            "sort_order": "Secuencia numérico de ordenamiento para visualización ordenada en tiendas y reportes.",
            "is_active": "Indica si la talla está disponible para selección."
        }
    },
    "colores": {
        "module": "4. Catálogo y Taxonomía de Prendas",
        "description": "Catálogo general de colores disponibles para las prendas, con su respectivo código hexadecimal para renderizado en UI.",
        "columns": {
            "id": "Identificador único correlativo del color.",
            "name": "Nombre del color (ej. Negro, Blanco, Azul Marino, Rojo Borgoña).",
            "hex_code": "Código hexadecimal del color web (ej. #FFFFFF, #1B365D) para muestras visuales.",
            "is_active": "Indica si el color está activo."
        }
    },
    "temporadas": {
        "module": "4. Catálogo y Moda Estacional",
        "description": "Temporadas comerciales de moda (ej. Verano 2026, Otoño-Invierno 2026) que marcan la rotación del catálogo.",
        "columns": {
            "id": "Identificador único de la temporada comercial.",
            "tenant_id": "Empresa cliente titular de la temporada.",
            "name": "Nombre de la temporada (ej. Primavera - Verano 2026).",
            "starts_on": "Fecha de inicio del ciclo estacional comercial.",
            "ends_on": "Fecha de culminación del ciclo comercial.",
            "is_active": "Indica si la temporada está activa para promociones y catálogos."
        }
    },
    "colecciones": {
        "module": "4. Catálogo y Moda Estacional",
        "description": "Líneas o colecciones temáticas de diseño textil asociadas a una temporada estacional específica.",
        "columns": {
            "id": "Identificador único correlativo de la colección.",
            "tenant_id": "Empresa cliente titular de la colección.",
            "season_id": "Temporada a la que pertenece la colección.",
            "name": "Nombre de la colección (ej. Urban Chic, Casual Friday, Gala Nocturna).",
            "description": "Descripción conceptual o estética de la línea de prendas.",
            "is_active": "Indica si la colección está disponible en vitrina."
        }
    },
    "productos": {
        "module": "4. Catálogo y Ficha Maestra de Prendas",
        "description": "Ficha maestra de prendas de vestir. Centraliza la información base del diseño, categoría, precio de lista y características generales.",
        "columns": {
            "id": "Identificador único correlativo del producto.",
            "tenant_id": "Empresa cliente titular del producto.",
            "category_id": "Categoría a la que pertenece la prenda.",
            "season_id": "Temporada de moda asociada (opcional).",
            "collection_id": "Colección estilística asociada (opcional).",
            "audience": "Segmento de público objetivo: UNISEX, MEN, WOMEN, KIDS.",
            "size_system": "Sistema de tallaje aplicable: ALPHA, NUMERIC, SHOE.",
            "code": "Código interno o referencia de diseño del producto.",
            "name": "Nombre comercial de la prenda de vestir.",
            "slug": "Identificador amigable para URLs amigables en e-Commerce.",
            "description": "Descripción detallada del material, corte, cuidado y composición textil.",
            "price": "Precio base de venta al público en moneda local.",
            "is_active": "Indica si la prenda se encuentra visible y disponible para venta.",
            "created_at": "Fecha y hora de alta del producto en el catálogo.",
            "updated_at": "Fecha y hora de la última actualización de la ficha del producto."
        }
    },
    "producto_proveedores": {
        "module": "4. Catálogo y Suministros",
        "description": "Tabla asociativa N:M que vincula cada producto del catálogo con los proveedores certificados para su confección o suministro.",
        "columns": {
            "product_id": "Prenda de vestir del catálogo.",
            "supplier_id": "Proveedor calificado para suministrar dicha prenda."
        }
    },
    "variantes_producto": {
        "module": "4. Catálogo y SKUs Comercializables",
        "description": "Matriz de variantes físicas comercializables que combina Producto + Talla + Color. Cada variante posee un SKU único para control de inventario.",
        "columns": {
            "id": "Identificador único correlativo de la variante.",
            "tenant_id": "Empresa cliente titular de la variante.",
            "product_id": "Prenda maestra a la que pertenece esta variante.",
            "size_id": "Talla física específica de la variante.",
            "color_id": "Color físico específico de la variante.",
            "sku": "Stock Keeping Unit: Código unívoco de barras o identificación para inventario y ventas.",
            "is_active": "Indica si esta variante física específica está activa para comercialización."
        }
    },
    "imagenes_producto": {
        "module": "4. Catálogo y Galería Multimedia",
        "description": "Galería fotográfica de las prendas de vestir, controlando la imagen principal para vitrinas y el orden de visualización.",
        "columns": {
            "id": "Identificador único de la fotografía.",
            "product_id": "Prenda a la que pertenece la imagen.",
            "image_url": "Ruta de almacenamiento relativo o URL pública de la imagen de alta resolución.",
            "is_primary": "Marca booleana que designa si esta imagen es la portada principal en el catálogo.",
            "sort_order": "Secuencia numérica de ordenamiento en la galería de fotos."
        }
    },

    # 5. Proveedores y Abastecimiento B2B
    "proveedores": {
        "module": "5. Proveedores y Abastecimiento B2B",
        "description": "Registro maestro de proveedores, talleres de confección y maquiladores textiles que abastecen a las marcas cliente.",
        "columns": {
            "id": "Identificador único correlativo del proveedor.",
            "tenant_id": "Empresa cliente con la que mantiene relación comercial el proveedor.",
            "trade_name": "Nombre de fantasía o denominación comercial del proveedor.",
            "legal_name": "Razón social jurídica legalmente registrada.",
            "tax_id": "Número de Identificación Tributaria (NIT / RUC / NIF).",
            "email": "Correo electrónico de contacto comercial.",
            "phone": "Teléfono de contacto o atención a pedidos.",
            "address": "Dirección física de oficinas o talleres de confección.",
            "is_active": "Indica si el proveedor está habilitado para emitir ofertas y suministros."
        }
    },
    "ofertas_abastecimiento": {
        "module": "5. Proveedores y Abastecimiento B2B",
        "description": "Ofertas de aprovisionamiento de stock emitidas por proveedores externos para variantes de prendas específicas en una temporada.",
        "columns": {
            "id": "Identificador único de la oferta de abastecimiento.",
            "tenant_id": "Empresa cliente receptora de la oferta de stock.",
            "supplier_id": "Proveedor que publica la oferta de suministro.",
            "product_variant_id": "Variante SKU de producto ofertada.",
            "season_id": "Temporada de moda a la que corresponde el lote textil.",
            "collection_id": "Colección temática a la que pertenece el lote (opcional).",
            "status": "Estado de disponibilidad del lote: AVAILABLE, LIMITED, OUT_OF_STOCK, UPCOMING.",
            "available_quantity": "Volumen de piezas textiles disponibles para suministro inmediato.",
            "expected_date": "Fecha proyectada de entrega o arribo del lote.",
            "notes": "Observaciones técnicas sobre telas, empaque o condiciones de entrega.",
            "is_active": "Indica si la oferta está vigente para compra institucional.",
            "created_at": "Fecha y hora de publicación de la oferta.",
            "updated_at": "Fecha y hora de actualización del stock ofertado."
        }
    },

    # 6. Inventario y Kardex
    "inventario": {
        "module": "6. Inventario y Control de Stock",
        "description": "Existencias físicas y cantidades reservadas de cada variante SKU en cada sucursal o almacén físico de la empresa.",
        "columns": {
            "id": "Identificador único del registro de inventario.",
            "tenant_id": "Empresa cliente titular del stock.",
            "branch_id": "Sucursal o almacén físico donde se encuentran físicamente las prendas.",
            "product_variant_id": "Variante SKU de la prenda en existencia.",
            "stock_quantity": "Cantidad física total de unidades en existencias.",
            "reserved_quantity": "Cantidad de unidades temporalmente apartadas por reservas activas de clientes."
        }
    },
    "movimientos_inventario": {
        "module": "6. Inventario y Control de Stock (Kardex)",
        "description": "Kardex transaccional e inmutable que registra cada variación física de existencias con saldo previo y posterior.",
        "columns": {
            "id": "Identificador único del movimiento de inventario.",
            "tenant_id": "Empresa cliente donde ocurrió la alteración de stock.",
            "inventory_id": "Registro de stock afectado por el movimiento.",
            "movement_type": "Naturaleza del movimiento: IN (ingreso), OUT (salida), RETURN (devolución), RESERVE (apartado), RELEASE (liberación de reserva), SALE (descuento por venta).",
            "quantity": "Cantidad absoluta de unidades modificadas.",
            "stock_before": "Balance de existencias antes de aplicar la operación.",
            "stock_after": "Balance de existencias resultante tras la operación.",
            "reason": "Motivo justificado del ajuste de inventario.",
            "reference_type": "Entidad de origen relacionada (ej. SALE, RESERVATION, PURCHASE_ORDER, MANUAL).",
            "reference_id": "Identificador de la transacción de origen.",
            "created_by": "Usuario que ejecutó o autorizó el movimiento.",
            "created_at": "Fecha y hora exacta del registro del movimiento en Kardex."
        }
    },

    # 7. Reservas y Carritos
    "reservas": {
        "module": "7. Comercio, Reservas y Carrito",
        "description": "Gestión de reservas de prendas realizadas por clientes para retiro y pago presencial en sucursales físicas, con control de expiración.",
        "columns": {
            "id": "Identificador único correlativo de la reserva.",
            "tenant_id": "Empresa cliente titular de la reserva.",
            "customer_id": "Cliente titular que efectúa el apartado de prendas.",
            "branch_id": "Sucursal física donde el cliente retirará las prendas reservadas.",
            "scheduled_for": "Fecha y hora pactada para la visita del cliente.",
            "status": "Estado de la reserva: PENDING, CONFIRMED, COMPLETED, CANCELLED, EXPIRED.",
            "notes": "Instrucciones especiales o comentarios del cliente.",
            "expires_at": "Fecha y hora límite de caducidad automática de la reserva (normalmente 24 horas).",
            "created_at": "Fecha y hora de generación de la reserva.",
            "updated_at": "Fecha y hora de última modificación del estado."
        }
    },
    "detalles_reserva": {
        "module": "7. Comercio, Reservas y Carrito",
        "description": "Líneas de detalle de una reserva, especificando variantes de producto, unidades apartadas y precio unitario pactado.",
        "columns": {
            "id": "Identificador único de la línea de reserva.",
            "reservation_id": "Reserva a la que corresponde este ítem.",
            "product_variant_id": "Variante SKU de la prenda apartada.",
            "quantity": "Cantidad de unidades reservadas.",
            "unit_price": "Precio unitario fijado al momento de formalizar la reserva."
        }
    },
    "carritos": {
        "module": "7. Comercio, Reservas y Carrito",
        "description": "Carrito de compras persistente por usuario cliente y empresa tenant para compras en línea en la tienda web.",
        "columns": {
            "id": "Identificador único del carrito de compra.",
            "tenant_id": "Empresa cliente dueña de la tienda online.",
            "customer_id": "Usuario cliente propietario del carrito.",
            "status": "Estado operativo del carrito: ACTIVE (en curso), ABANDONED (abandonado), CONVERTED (convertido en venta).",
            "created_at": "Fecha y hora de creación del carrito.",
            "updated_at": "Fecha y hora de última adición o edición de ítems."
        }
    },
    "detalles_carrito": {
        "module": "7. Comercio, Reservas y Carrito",
        "description": "Ítems y prendas agregadas al carrito de compra con cantidades y precio de lista vigente.",
        "columns": {
            "id": "Identificador único del detalle de carrito.",
            "cart_id": "Carrito de compras al que pertenece este ítem.",
            "product_variant_id": "Variante física de prenda seleccionada.",
            "quantity": "Cantidad de unidades elegidas por el cliente.",
            "unit_price": "Precio unitario de lista al momento de agregarlo al carrito."
        }
    },

    # 8. Ventas, Envíos y Pagos
    "ventas": {
        "module": "8. Ventas, Logística y Pasarela de Pagos",
        "description": "Encabezado maestro de transacciones de venta comercial formalizadas en caja física (POS) o a través de la tienda web (e-Commerce).",
        "columns": {
            "id": "Identificador único correlativo de la venta.",
            "tenant_id": "Empresa cliente titular de la venta.",
            "order_number": "Número de orden o folio fiscal único por empresa (ej. ORD-2026-0001).",
            "customer_id": "Usuario cliente comprador (opcional para ventas directas en mostrador a consumidor final).",
            "branch_id": "Sucursal física donde se formalizó o despachó la venta.",
            "cashier_id": "Empleado/cajero responsable del cobro de la venta.",
            "reservation_id": "Vínculo a la reserva previa que originó esta venta (si aplica).",
            "channel": "Canal de comercialización: POS (punto de venta presencial), ONLINE (comercio web/móvil).",
            "status": "Estado de la transacción: PENDING, COMPLETED, CANCELLED, REFUNDED.",
            "fulfillment_type": "Modalidad de entrega: PICKUP (retiro presencial en tienda), DELIVERY (envío a domicilio).",
            "subtotal": "Monto acumulado antes de descuentos e impuestos en moneda local.",
            "discount": "Monto total de rebajas comerciales o promociones aplicadas.",
            "total": "Monto líquido neto a cobrar y liquidar.",
            "created_at": "Fecha y hora de formalización de la venta.",
            "updated_at": "Fecha y hora de actualización del registro."
        }
    },
    "envios_venta": {
        "module": "8. Ventas, Logística y Pasarela de Pagos",
        "description": "Datos de despacho, mensajería y entrega a domicilio para órdenes de venta con modalidad DELIVERY.",
        "columns": {
            "id": "Identificador único del registro de envío.",
            "sale_id": "Venta comercial asociada a este despacho.",
            "recipient_name": "Nombre completo de la persona que recibirá el paquete.",
            "recipient_ci": "Cédula de Identidad o documento del receptor.",
            "recipient_phone": "Teléfono de contacto para el transportista/courier.",
            "department_or_city": "Departamento o ciudad de destino.",
            "zone": "Barrio, zona o distrito municipal.",
            "street": "Avenida o calle principal.",
            "house_number": "Número de inmueble, edificio o departamento.",
            "reference": "Puntos de referencia para facilitar la ubicación al repartidor.",
            "created_at": "Fecha y hora de captura de los datos de envío.",
            "updated_at": "Fecha y hora de actualización del despacho."
        }
    },
    "detalles_venta": {
        "module": "8. Ventas, Logística y Pasarela de Pagos",
        "description": "Líneas de detalle de las prendas vendidas, con registro inalterable de precio histórico, descuento unitario y subtotal de línea.",
        "columns": {
            "id": "Identificador único de la línea de venta.",
            "sale_id": "Venta comercial a la que pertenece esta línea.",
            "product_variant_id": "Variante SKU de la prenda vendida.",
            "quantity": "Cantidad de unidades adquiridas.",
            "unit_price": "Precio unitario pactado y congelado al momento de la transacción.",
            "discount": "Descuento total aplicado a esta línea.",
            "line_total": "Total líquido de la línea (cantidad * unit_price - discount)."
        }
    },
    "pagos": {
        "module": "8. Ventas, Logística y Pasarela de Pagos",
        "description": "Transacciones de pago y cobro financiero con soporte de idempotencia, arqueo de caja (recibido/cambio) y pasarelas de pago (Stripe, QR).",
        "columns": {
            "id": "Identificador único del comprobante o transacción de pago.",
            "tenant_id": "Empresa cliente titular del cobro.",
            "idempotency_key": "Clave única de idempotencia para evitar cobros dobles en pasarelas digitales y sincronización offline.",
            "sale_id": "Venta comercial cancelada con este pago.",
            "method": "Método de pago: CASH (efectivo), STRIPE (tarjeta online), QR (pago simple QR), CARD (terminal POS bancario).",
            "provider": "Entidad procesadora o pasarela externa (ej. Stripe, Red Enlace, Banco BCP).",
            "transaction_reference": "Número de autorización, código de rastreo o referencia bancaria externa.",
            "status": "Estado de la transacción financiera: PENDING, APPROVED, REJECTED, REFUNDED.",
            "amount": "Monto total debitado o cobrado efectivamente.",
            "received_amount": "Monto recibido en efectivo entregado por el cliente en caja.",
            "change_amount": "Monto de vuelto o cambio devuelto al cliente.",
            "metadata_json": "Carga útil JSON con respuesta técnica de la pasarela de pagos.",
            "paid_at": "Fecha y hora de confirmación y liquidación del pago.",
            "created_at": "Fecha y hora de iniciación del cobro."
        }
    },

    # 9. Promociones y Descuentos
    "promociones": {
        "module": "9. Marketing y Promociones",
        "description": "Campañas de descuento promocional (porcentaje o monto fijo) con vigencia temporal acotada.",
        "columns": {
            "id": "Identificador único correlativo de la promoción.",
            "tenant_id": "Empresa cliente titular de la campaña de descuentos.",
            "name": "Nombre comercial de la campaña (ej. Black Friday 20%, Liquidación de Verano).",
            "description": "Términos, condiciones y alcance de la promoción.",
            "discount_type": "Tipo de beneficio: PERCENTAGE (porcentaje sobre precio), FIXED_AMOUNT (monto fijo de descuento).",
            "discount_value": "Valor numérico del descuento (ej. 20.00 para 20% o 50.00 para Bs 50).",
            "starts_at": "Fecha y hora de inicio de vigencia de la campaña.",
            "ends_at": "Fecha y hora de vencimiento de la campaña.",
            "is_active": "Indica si la promoción está activa en el sistema."
        }
    },
    "productos_promocion": {
        "module": "9. Marketing y Promociones",
        "description": "Tabla asociativa N:M que define cuáles prendas específicas del catálogo quedan sujetas a una promoción activa.",
        "columns": {
            "promotion_id": "Campaña promocional de descuento.",
            "product_id": "Prenda de vestir incluida en la promoción."
        }
    },

    # 10. Inteligencia Artificial y VTON
    "sesiones_vestidor_virtual": {
        "module": "10. Inteligencia Artificial y Vestidor Virtual (VTON)",
        "description": "Sesiones de prueba de ropa virtual (Virtual Try-On) impulsadas por modelos generativos de IA multimodal.",
        "columns": {
            "id": "Identificador único de la sesión de probador virtual.",
            "tenant_id": "Empresa cliente titular de la sesión.",
            "customer_id": "Usuario cliente que utiliza el vestidor virtual (si está autenticado).",
            "product_id": "Prenda de vestir seleccionada para la prueba virtual.",
            "status": "Estado del proceso: STARTED, PROCESSING, COMPLETED, FAILED.",
            "device_info": "Metadatos del navegador, resolución y dispositivo del usuario.",
            "started_at": "Fecha y hora de inicio de la sesión.",
            "ended_at": "Fecha y hora de culminación o entrega de la imagen generada."
        }
    },
    "recomendaciones_ia": {
        "module": "10. Inteligencia Artificial y Recomendaciones ML",
        "description": "Recomendaciones personalizadas de prendas sugeridas a clientes mediante algoritmos de Machine Learning y similitud estilística.",
        "columns": {
            "id": "Identificador único de la recomendación de producto.",
            "tenant_id": "Empresa cliente titular.",
            "customer_id": "Cliente al que se le formula la recomendación personalizada.",
            "product_id": "Prenda de vestir recomendada.",
            "source": "Algoritmo o fuente generadora: COLLABORATIVE_FILTERING, CONTENT_BASED, LLM_ASSISTANT.",
            "reason": "Explicación explicable de por qué se recomienda la prenda (ej. 'Combina perfectamente con tu última compra').",
            "score": "Puntuación de confianza o similitud (entre 0.0000 y 1.0000).",
            "context": "Contexto JSON de la inferencia (temporada, ocasión, preferencias de color).",
            "created_at": "Fecha y hora de cálculo de la recomendación.",
            "expires_at": "Fecha y hora de caducidad de la sugerencia."
        }
    },

    # 11. Auditoría y Sincronización Offline
    "bitacora": {
        "module": "11. Auditoría Transversal y Seguridad",
        "description": "Auditoría exhaustiva e inmutable de operaciones críticas. Almacena deltas de datos (valores anteriores y nuevos en JSON), IP y User-Agent.",
        "columns": {
            "id": "Identificador único del registro de auditoría.",
            "tenant_id": "Empresa cliente donde ocurrió el evento de auditoría.",
            "usuario_id": "Usuario responsable que ejecutó la acción.",
            "accion": "Operación efectuada: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, SYNC_CONFLICT.",
            "tipo_entidad": "Nombre de la entidad o tabla afectada (ej. Product, Sale, Inventory, Subscription).",
            "entidad_id": "Clave primaria del registro alterado.",
            "descripcion": "Descripción textual legible del cambio ejecutado.",
            "valores_anteriores": "Fotografía JSON de los valores previos a la modificación.",
            "valores_nuevos": "Fotografía JSON de los valores resultantes tras la modificación.",
            "direccion_ip": "Dirección IP de origen del cliente (IPv4 / IPv6).",
            "agente_usuario": "Cadena User-Agent del navegador o cliente móvil emisor.",
            "fecha_creacion": "Marca de tiempo exacta del registro en auditoría."
        }
    },
    "sync_operations": {
        "module": "11. Arquitectura Offline-First y Patrón Outbox",
        "description": "Registro de operaciones transaccionales fuera de línea procesadas bajo el patrón Outbox. Garantiza idempotencia, orden y resolución de conflictos.",
        "columns": {
            "id": "Identificador único correlativo de la operación de sincronización.",
            "tenant_id": "Empresa cliente titular de los datos sincronizados.",
            "client_operation_id": "UUID universal v4 emitido por el cliente desconectado para control estricto de idempotencia.",
            "branch_id": "Sucursal física donde se originó la transacción fuera de línea.",
            "user_id": "Operador o cajero que efectuó la operación desconectada.",
            "operation_type": "Naturaleza de la operación: SALE (venta de contado), RESERVATION (reserva de prendas).",
            "status": "Resultado del procesamiento: CONFIRMED (procesada con éxito), CONFLICT (conflicto de stock), REJECTED (rechazada).",
            "payload": "Contenido transaccional completo en formato JSON originado en el dispositivo móvil/PWA.",
            "conflict_detail": "Detalle técnico de discrepancias en caso de conflicto por insuficiencia de stock.",
            "sale_id": "Venta central creada en la base de datos tras la sincronización exitosa.",
            "reservation_id": "Reserva central creada en la base de datos tras la sincronización exitosa.",
            "processed_at": "Fecha y hora de procesamiento en el servidor central.",
            "created_at": "Fecha y hora de recepción del paquete de sincronización."
        }
    }
}
