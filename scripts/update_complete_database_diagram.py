import win32com.client
import os
import shutil

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\db_conceptual"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\0c84ba0d-3a55-4d70-91ad-2a76b3c98f87"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# 30 Clases Completas del Sistema FashionStore SaaS (Ciclos 1, 2, 3 y Segundo Parcial)
CLASSES_SPEC = {
    # --- ZONA SAAS (SEGUNDO PARCIAL) ---
    "Tenant": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "codigo_tenant", "type": "string", "visibility": "Private"},
            {"name": "razon_social", "type": "string", "visibility": "Private"},
            {"name": "nit", "type": "string", "visibility": "Private"},
            {"name": "subdominio", "type": "string", "visibility": "Private"},
            {"name": "schema_name", "type": "string", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "max_usuarios", "type": "int", "visibility": "Private"},
            {"name": "max_sucursales", "type": "int", "visibility": "Private"},
            {"name": "fecha_registro", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (50, -40, 280, -280)
    },
    "SubscriptionPlan": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "codigo_plan", "type": "string", "visibility": "Private"},
            {"name": "nombre_plan", "type": "string", "visibility": "Private"},
            {"name": "precio_mensual", "type": "decimal", "visibility": "Private"},
            {"name": "max_usuarios", "type": "int", "visibility": "Private"},
            {"name": "max_sucursales", "type": "int", "visibility": "Private"},
            {"name": "permite_offline", "type": "bool", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (340, -40, 560, -220)
    },
    "Subscription": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "plan_id", "type": "int", "visibility": "Private"},
            {"name": "fecha_inicio", "type": "datetime", "visibility": "Private"},
            {"name": "fecha_fin", "type": "datetime", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "auto_renovar", "type": "bool", "visibility": "Private"},
            {"name": "metodo_pago", "type": "string", "visibility": "Private"},
        ],
        "pos": (340, -260, 560, -440)
    },
    "SyncOperation": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "dispositivo_id", "type": "string", "visibility": "Private"},
            {"name": "tipo_operacion", "type": "string", "visibility": "Private"},
            {"name": "tabla_afectada", "type": "string", "visibility": "Private"},
            {"name": "registro_id", "type": "int", "visibility": "Private"},
            {"name": "payload_json", "type": "json", "visibility": "Private"},
            {"name": "version", "type": "int", "visibility": "Private"},
            {"name": "estado_sync", "type": "string", "visibility": "Private"},
            {"name": "fecha_sincronizacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (50, -320, 280, -560)
    },

    # --- SEGURIDAD Y AUDITORÍA ---
    "Rol": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "codigo", "type": "string", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (1230, -40, 1420, -160)
    },
    "Usuario": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "rol_id", "type": "int", "visibility": "Private"},
            {"name": "sucursal_id", "type": "int", "visibility": "Private"},
            {"name": "nombre_completo", "type": "string", "visibility": "Private"},
            {"name": "email", "type": "string", "visibility": "Private"},
            {"name": "password", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
            {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (1230, -200, 1460, -430)
    },
    "Bitacora": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "accion", "type": "string", "visibility": "Private"},
            {"name": "tipo_entidad", "type": "string", "visibility": "Private"},
            {"name": "entidad_id", "type": "int", "visibility": "Private"},
            {"name": "descripcion", "type": "string", "visibility": "Private"},
            {"name": "valores_anteriores", "type": "json", "visibility": "Private"},
            {"name": "valores_nuevos", "type": "json", "visibility": "Private"},
            {"name": "ip_origen", "type": "string", "visibility": "Private"},
            {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (1230, -470, 1460, -730)
    },

    # --- SUCURSALES Y UBICACIÓN ---
    "Ciudad": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (50, -600, 250, -710)
    },
    "Sucursal": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "ciudad_id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "direccion", "type": "string", "visibility": "Private"},
            {"name": "telefono", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (50, -750, 260, -940)
    },

    # --- CATÁLOGO MAESTRO ---
    "Categoria": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "descripcion", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (340, -480, 560, -620)
    },
    "Temporada": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "fecha_inicio", "type": "date", "visibility": "Private"},
            {"name": "fecha_fin", "type": "date", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (340, -660, 560, -810)
    },
    "Coleccion": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "temporada_id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "descripcion", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (340, -850, 560, -990)
    },
    "Proveedor": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "razon_social", "type": "string", "visibility": "Private"},
            {"name": "nit", "type": "string", "visibility": "Private"},
            {"name": "email", "type": "string", "visibility": "Private"},
            {"name": "telefono", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (50, -980, 260, -1160)
    },
    "Producto": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "categoria_id", "type": "int", "visibility": "Private"},
            {"name": "temporada_id", "type": "int", "visibility": "Private"},
            {"name": "coleccion_id", "type": "int", "visibility": "Private"},
            {"name": "codigo", "type": "string", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "descripcion", "type": "string", "visibility": "Private"},
            {"name": "precio", "type": "decimal", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
            {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (630, -40, 860, -320)
    },
    "ImagenProducto": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "producto_id", "type": "int", "visibility": "Private"},
            {"name": "url_imagen", "type": "string", "visibility": "Private"},
            {"name": "es_principal", "type": "bool", "visibility": "Private"},
            {"name": "orden", "type": "int", "visibility": "Private"},
        ],
        "pos": (630, -360, 840, -500)
    },
    "VarianteProducto": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "producto_id", "type": "int", "visibility": "Private"},
            {"name": "talla_id", "type": "int", "visibility": "Private"},
            {"name": "color_id", "type": "int", "visibility": "Private"},
            {"name": "sku", "type": "string", "visibility": "Private"},
            {"name": "codigo_barra", "type": "string", "visibility": "Private"},
            {"name": "precio_adicional", "type": "decimal", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (630, -540, 860, -760)
    },
    "Talla": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "orden", "type": "int", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (630, -800, 740, -920)
    },
    "Color": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "codigo_hex", "type": "string", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (760, -800, 870, -920)
    },

    # --- INVENTARIO ---
    "Inventario": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "sucursal_id", "type": "int", "visibility": "Private"},
            {"name": "variante_id", "type": "int", "visibility": "Private"},
            {"name": "stock_fisico", "type": "int", "visibility": "Private"},
            {"name": "stock_reservado", "type": "int", "visibility": "Private"},
        ],
        "pos": (930, -40, 1150, -190)
    },
    "MovimientoInventario": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "inventario_id", "type": "int", "visibility": "Private"},
            {"name": "tipo_movimiento", "type": "string", "visibility": "Private"},
            {"name": "cantidad", "type": "int", "visibility": "Private"},
            {"name": "stock_anterior", "type": "int", "visibility": "Private"},
            {"name": "stock_posterior", "type": "int", "visibility": "Private"},
            {"name": "motivo", "type": "string", "visibility": "Private"},
            {"name": "creado_por", "type": "int", "visibility": "Private"},
            {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (930, -230, 1160, -460)
    },

    # --- TRANSACCIONAL: CARRITO, RESERVAS, VENTAS Y PAGOS ---
    "Carrito": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (930, -500, 1130, -620)
    },
    "DetalleCarrito": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "carrito_id", "type": "int", "visibility": "Private"},
            {"name": "variante_id", "type": "int", "visibility": "Private"},
            {"name": "cantidad", "type": "int", "visibility": "Private"},
            {"name": "precio_unitario", "type": "decimal", "visibility": "Private"},
        ],
        "pos": (930, -660, 1150, -810)
    },
    "Reserva": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "sucursal_id", "type": "int", "visibility": "Private"},
            {"name": "codigo_reserva", "type": "string", "visibility": "Private"},
            {"name": "fecha_programada", "type": "datetime", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "notas", "type": "string", "visibility": "Private"},
            {"name": "expira_en", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (930, -850, 1160, -1070)
    },
    "DetalleReserva": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "reserva_id", "type": "int", "visibility": "Private"},
            {"name": "variante_id", "type": "int", "visibility": "Private"},
            {"name": "cantidad", "type": "int", "visibility": "Private"},
            {"name": "precio_unitario", "type": "decimal", "visibility": "Private"},
        ],
        "pos": (930, -1110, 1160, -1260)
    },
    "Venta": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "cajero_id", "type": "int", "visibility": "Private"},
            {"name": "sucursal_id", "type": "int", "visibility": "Private"},
            {"name": "canal", "type": "string", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "subtotal", "type": "decimal", "visibility": "Private"},
            {"name": "descuento", "type": "decimal", "visibility": "Private"},
            {"name": "total", "type": "decimal", "visibility": "Private"},
            {"name": "fecha_venta", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (1230, -770, 1460, -1040)
    },
    "DetalleVenta": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "venta_id", "type": "int", "visibility": "Private"},
            {"name": "variante_id", "type": "int", "visibility": "Private"},
            {"name": "cantidad", "type": "int", "visibility": "Private"},
            {"name": "precio_unitario", "type": "decimal", "visibility": "Private"},
            {"name": "descuento", "type": "decimal", "visibility": "Private"},
            {"name": "total_linea", "type": "decimal", "visibility": "Private"},
        ],
        "pos": (1230, -1080, 1460, -1270)
    },
    "Pago": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "venta_id", "type": "int", "visibility": "Private"},
            {"name": "metodo", "type": "string", "visibility": "Private"},
            {"name": "proveedor", "type": "string", "visibility": "Private"},
            {"name": "referencia", "type": "string", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "total", "type": "decimal", "visibility": "Private"},
            {"name": "monto_recibido", "type": "decimal", "visibility": "Private"},
            {"name": "cambio", "type": "decimal", "visibility": "Private"},
            {"name": "fecha_pago", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (1230, -1310, 1460, -1550)
    },

    # --- PROMOCIONES, FITTING E IA ---
    "Promocion": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "tenant_id", "type": "int", "visibility": "Private"},
            {"name": "nombre", "type": "string", "visibility": "Private"},
            {"name": "tipo_descuento", "type": "string", "visibility": "Private"},
            {"name": "valor_descuento", "type": "decimal", "visibility": "Private"},
            {"name": "fecha_inicio", "type": "datetime", "visibility": "Private"},
            {"name": "fecha_fin", "type": "datetime", "visibility": "Private"},
            {"name": "activo", "type": "bool", "visibility": "Private"},
        ],
        "pos": (340, -1030, 560, -1230)
    },
    "SesionVestidorVirtual": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "producto_id", "type": "int", "visibility": "Private"},
            {"name": "estado", "type": "string", "visibility": "Private"},
            {"name": "dispositivo", "type": "string", "visibility": "Private"},
            {"name": "fecha_inicio", "type": "datetime", "visibility": "Private"},
            {"name": "fecha_fin", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (630, -960, 860, -1140)
    },
    "RecomendacionIA": {
        "attributes": [
            {"name": "id", "type": "int", "visibility": "Private"},
            {"name": "usuario_id", "type": "int", "visibility": "Private"},
            {"name": "producto_id", "type": "int", "visibility": "Private"},
            {"name": "fuente", "type": "string", "visibility": "Private"},
            {"name": "motivo", "type": "string", "visibility": "Private"},
            {"name": "puntuacion", "type": "decimal", "visibility": "Private"},
            {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
        ],
        "pos": (1230, -1590, 1460, -1770)
    }
}

# 45 Asociaciones del Negocio Completo
RELATIONSHIPS_SPEC = [
    # SaaS Multi-tenant
    {"source": "Tenant", "target": "Subscription", "name": "contrata", "source_mult": "1", "target_mult": "1..*"},
    {"source": "SubscriptionPlan", "target": "Subscription", "name": "define", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Usuario", "name": "aloja", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Sucursal", "name": "posee", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Categoria", "name": "clasifica", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Producto", "name": "administra", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Venta", "name": "consolida", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Reserva", "name": "gestiona", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Bitacora", "name": "audita", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "SyncOperation", "name": "registra", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Usuario", "target": "SyncOperation", "name": "ejecuta", "source_mult": "1", "target_mult": "0..*"},

    # Seguridad y Ubicación
    {"source": "Usuario", "target": "Rol", "name": "tiene", "source_mult": "0..*", "target_mult": "1"},
    {"source": "Usuario", "target": "Sucursal", "name": "asignado_a", "source_mult": "0..*", "target_mult": "0..1"},
    {"source": "Usuario", "target": "Bitacora", "name": "registra", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Ciudad", "target": "Sucursal", "name": "contiene", "source_mult": "1", "target_mult": "1..*"},

    # Catálogo
    {"source": "Categoria", "target": "Producto", "name": "clasifica", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Temporada", "target": "Coleccion", "name": "agrupa", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Temporada", "target": "Producto", "name": "aplica_a", "source_mult": "0..1", "target_mult": "0..*"},
    {"source": "Coleccion", "target": "Producto", "name": "contiene", "source_mult": "0..1", "target_mult": "0..*"},
    {"source": "Producto", "target": "ImagenProducto", "name": "posee", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Producto", "target": "Proveedor", "name": "suministrado_por", "source_mult": "0..*", "target_mult": "0..*"},
    {"source": "Producto", "target": "VarianteProducto", "name": "compone", "source_mult": "1", "target_mult": "1..*"},
    {"source": "Talla", "target": "VarianteProducto", "name": "especifica", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Color", "target": "VarianteProducto", "name": "especifica", "source_mult": "1", "target_mult": "0..*"},

    # Inventario
    {"source": "Sucursal", "target": "Inventario", "name": "almacena", "source_mult": "1", "target_mult": "0..*"},
    {"source": "VarianteProducto", "target": "Inventario", "name": "controla", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Inventario", "target": "MovimientoInventario", "name": "registra", "source_mult": "1", "target_mult": "0..*"},

    # Carrito
    {"source": "Usuario", "target": "Carrito", "name": "posee", "source_mult": "1", "target_mult": "0..1"},
    {"source": "Carrito", "target": "DetalleCarrito", "name": "contiene", "source_mult": "1", "target_mult": "0..*"},
    {"source": "VarianteProducto", "target": "DetalleCarrito", "name": "referencia", "source_mult": "1", "target_mult": "0..*"},

    # Reservas
    {"source": "Usuario", "target": "Reserva", "name": "solicita", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Sucursal", "target": "Reserva", "name": "atiende", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Reserva", "target": "DetalleReserva", "name": "contiene", "source_mult": "1", "target_mult": "1..*"},
    {"source": "VarianteProducto", "target": "DetalleReserva", "name": "aparta", "source_mult": "1", "target_mult": "0..*"},

    # Ventas y Pagos
    {"source": "Usuario", "target": "Venta", "name": "realiza", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Sucursal", "target": "Venta", "name": "origina", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Venta", "target": "DetalleVenta", "name": "desglosa", "source_mult": "1", "target_mult": "1..*"},
    {"source": "VarianteProducto", "target": "DetalleVenta", "name": "incluye", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Venta", "target": "Pago", "name": "cancela_con", "source_mult": "1", "target_mult": "1..*"},

    # Ciclo 3 (Promociones, Fitting e IA)
    {"source": "Promocion", "target": "Producto", "name": "aplica_a", "source_mult": "0..*", "target_mult": "0..*"},
    {"source": "Usuario", "target": "SesionVestidorVirtual", "name": "participa", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Producto", "target": "SesionVestidorVirtual", "name": "prueba", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Usuario", "target": "RecomendacionIA", "name": "sugerida_a", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Producto", "target": "RecomendacionIA", "name": "recomienda", "source_mult": "1", "target_mult": "0..*"},
]

def main():
    print("Iniciando conexión con Enterprise Architect...")
    ea = win32com.client.Dispatch("EA.App")
    repo = ea.Repository
    if not repo.OpenFile(EAP_PATH):
        print(f"Error abriendo {EAP_PATH}")
        return

    project = repo.GetProjectInterface()
    root_model = repo.Models.GetAt(0)

    # Buscar paquete '02 - Diseño Conceptual de la Base de Datos' (Package ID: 8)
    pkg = repo.GetPackageByID(8)
    print(f"Paquete encontrado: {pkg.Name} (ID: {pkg.PackageID})")

    # 1. Crear o Actualizar las 30 entidades en el paquete
    created_elements = {}
    for name, spec in CLASSES_SPEC.items():
        el = None
        for j in range(pkg.Elements.Count):
            item = pkg.Elements.GetAt(j)
            if item.Name == name and item.Type == "Class":
                el = item
                break
        if el is None:
            el = pkg.Elements.AddNew(name, "Class")
            el.Update()

        # Atributos tipados y privados (-)
        existing_attrs = {el.Attributes.GetAt(k).Name: el.Attributes.GetAt(k) for k in range(el.Attributes.Count)}
        for attr in spec["attributes"]:
            a_name = attr["name"]
            if a_name in existing_attrs:
                a = existing_attrs[a_name]
            else:
                a = el.Attributes.AddNew(a_name, attr["type"])
            a.Type = attr["type"]
            a.Visibility = attr["visibility"]
            a.Update()
        el.Update()
        created_elements[name] = el

    pkg.Elements.Refresh()
    print(f"Total entidades registradas en paquete: {pkg.Elements.Count}")

    # 2. Conectar relaciones
    for rel in RELATIONSHIPS_SPEC:
        src = created_elements[rel["source"]]
        tgt = created_elements[rel["target"]]

        conn = None
        for k in range(src.Connectors.Count):
            c = src.Connectors.GetAt(k)
            if c.SupplierID == tgt.ElementID and c.Type == "Association" and c.Name == rel["name"]:
                conn = c
                break
        if conn is None:
            conn = src.Connectors.AddNew(rel["name"], "Association")
            conn.SupplierID = tgt.ElementID

        conn.Name = rel["name"]
        conn.Direction = "Unspecified"
        if rel["source_mult"]:
            conn.ClientEnd.Cardinality = rel["source_mult"]
            conn.ClientEnd.Update()
        if rel["target_mult"]:
            conn.SupplierEnd.Cardinality = rel["target_mult"]
            conn.SupplierEnd.Update()
        conn.Update()
        src.Connectors.Refresh()

    # 3. Actualizar Diagrama 11: DISEÑO CONCEPTUAL DE LA BASE DE DATOS (FASHIONSTORE COMPLETO)
    diag11 = repo.GetDiagramByID(11)
    print(f"Actualizando diagrama principal: {diag11.Name} (ID: {diag11.DiagramID})...")

    # Mapear objetos existentes por ElementID
    existing_objs = {}
    for i in range(diag11.DiagramObjects.Count):
        obj = diag11.DiagramObjects.GetAt(i)
        existing_objs[obj.ElementID] = obj

    for name, spec in CLASSES_SPEC.items():
        el = created_elements[name]
        left, top, right, bottom = spec["pos"]
        if el.ElementID in existing_objs:
            do = existing_objs[el.ElementID]
        else:
            do = diag11.DiagramObjects.AddNew(f"l={left};r={right};t={top};b={bottom};", "")
            do.ElementID = el.ElementID
        do.left = left
        do.top = top
        do.right = right
        do.bottom = bottom
        do.Update()

    diag11.DiagramObjects.Refresh()
    diag11.DiagramLinks.Refresh()
    diag11.Update()
    repo.SaveDiagram(diag11.DiagramID)
    repo.ReloadDiagram(diag11.DiagramID)

    # 4. Exportar imagen a docs y artefactos
    png11_out = os.path.join(OUT_DIR, "diagrama_clases_bd_completo.png")
    png11_art = os.path.join(ARTIFACT_DIR, "diagrama_clases_bd_completo.png")
    project.PutDiagramImageToFile(diag11.DiagramGUID, png11_out, 1)
    shutil.copy2(png11_out, png11_art)
    print(f"Exportado Diagrama 11 Completo: {png11_out} ({os.path.getsize(png11_out)} bytes)")

    repo.CloseFile()
    del repo
    del ea
    print("¡Diagrama General de la Base de Datos unificado con las 30 clases completado exitosamente!")

if __name__ == "__main__":
    main()
