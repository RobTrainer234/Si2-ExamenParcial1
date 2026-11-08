# -*- coding: utf-8 -*-
"""
Script maestro para generar el Diagrama de Clases - Modelo de Dominio General Completo (Segundo Parcial)
en Enterprise Architect (CasosDeUso_SegundoParcial.eap).
Paquete: 'Segundo Parcial - Modelo de Dominio (General Completo)' (ID: 199)
Diagrama: 'Diagrama de Clases - Modelo de Dominio General (Segundo Parcial)' (ID: 429)
Total: 40 clases organizadas en 6 columnas conceptuales completas.
"""

import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

CLASSES_DATA = {
    # --- COLUMNA 1: SAAS, GOBIERNO & INFRAESTRUCTURA (L: 50, R: 270) ---
    "Tenant": {
        "attributes": [
            ("id", "int"),
            ("codigo_tenant", "string"),
            ("nombre_empresa", "string"),
            ("nit_ruc", "string"),
            ("subdominio", "string"),
            ("estado", "string"),
            ("fecha_registro", "datetime")
        ],
        "pos": {"l": 50, "r": 270, "t": -40, "b": -220}
    },
    "SubscriptionPlan": {
        "attributes": [
            ("id", "int"),
            ("codigo_plan", "string"),
            ("nombre_plan", "string"),
            ("precio_mensual", "decimal"),
            ("max_usuarios", "int"),
            ("max_sucursales", "int"),
            ("permite_offline", "bool"),
            ("permite_ia", "bool"),
            ("activo", "bool")
        ],
        "pos": {"l": 50, "r": 270, "t": -260, "b": -430}
    },
    "Subscription": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("plan_id", "int"),
            ("fecha_inicio", "date"),
            ("fecha_fin", "date"),
            ("estado", "string"),
            ("metodo_pago", "string"),
            ("auto_renovar", "bool")
        ],
        "pos": {"l": 50, "r": 270, "t": -470, "b": -640}
    },
    "SyncOperation": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("dispositivo_id", "string"),
            ("tipo_operacion", "string"),
            ("tabla_afectada", "string"),
            ("estado_sync", "string"),
            ("fecha_sincronizacion", "datetime")
        ],
        "pos": {"l": 50, "r": 270, "t": -680, "b": -850}
    },
    "Ciudad": {
        "attributes": [
            ("id", "int"),
            ("nombre", "string"),
            ("departamento", "string")
        ],
        "pos": {"l": 50, "r": 270, "t": -890, "b": -1000}
    },
    "Sucursal": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("ciudad_id", "int"),
            ("nombre", "string"),
            ("direccion", "string"),
            ("telefono", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 50, "r": 270, "t": -1040, "b": -1220}
    },
    "Proveedor": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("nombre_empresa", "string"),
            ("nit", "string"),
            ("telefono", "string"),
            ("email", "string"),
            ("direccion", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 50, "r": 270, "t": -1260, "b": -1440}
    },

    # --- COLUMNA 2: USUARIOS, CLIENTES & CLASIFICACIÓN (L: 320, R: 540) ---
    "Rol": {
        "attributes": [
            ("id", "int"),
            ("codigo", "string"),
            ("nombre", "string"),
            ("descripcion", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 320, "r": 540, "t": -40, "b": -170}
    },
    "Usuario": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("rol_id", "int"),
            ("sucursal_id", "int"),
            ("nombre_completo", "string"),
            ("email", "string"),
            ("password_hash", "string"),
            ("telefono", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 320, "r": 540, "t": -210, "b": -410}
    },
    "Cliente": {
        "attributes": [
            ("id", "int"),
            ("usuario_id", "int"),
            ("nit_ci", "string"),
            ("razon_social", "string"),
            ("telefono", "string"),
            ("direccion", "string"),
            ("puntos_fidelidad", "int")
        ],
        "pos": {"l": 320, "r": 540, "t": -450, "b": -610}
    },
    "Categoria": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("nombre", "string"),
            ("descripcion", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 320, "r": 540, "t": -650, "b": -790}
    },
    "Temporada": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("nombre", "string"),
            ("fecha_inicio", "date"),
            ("fecha_fin", "date"),
            ("activo", "bool")
        ],
        "pos": {"l": 320, "r": 540, "t": -830, "b": -970}
    },
    "Coleccion": {
        "attributes": [
            ("id", "int"),
            ("temporada_id", "int"),
            ("nombre", "string"),
            ("descripcion", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 320, "r": 540, "t": -1010, "b": -1150}
    },
    "Promocion": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("nombre", "string"),
            ("codigo_promo", "string"),
            ("tipo_descuento", "string"),
            ("valor_descuento", "decimal"),
            ("fecha_inicio", "datetime"),
            ("fecha_fin", "datetime"),
            ("activo", "bool")
        ],
        "pos": {"l": 320, "r": 540, "t": -1190, "b": -1390}
    },

    # --- COLUMNA 3: CATÁLOGO, PRENDAS & VARIANTES (L: 590, R: 810) ---
    "Bitacora": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("usuario_id", "int"),
            ("accion", "string"),
            ("tipo_entidad", "string"),
            ("descripcion", "string"),
            ("fecha_hora", "datetime"),
            ("ip_origen", "string")
        ],
        "pos": {"l": 590, "r": 810, "t": -40, "b": -220}
    },
    "Producto": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("categoria_id", "int"),
            ("coleccion_id", "int"),
            ("codigo", "string"),
            ("nombre", "string"),
            ("descripcion", "string"),
            ("precio_base", "decimal"),
            ("activo", "bool")
        ],
        "pos": {"l": 590, "r": 810, "t": -260, "b": -480}
    },
    "ImagenProducto": {
        "attributes": [
            ("id", "int"),
            ("producto_id", "int"),
            ("url_imagen", "string"),
            ("orden", "int"),
            ("es_principal", "bool")
        ],
        "pos": {"l": 590, "r": 810, "t": -520, "b": -660}
    },
    "VarianteProducto": {
        "attributes": [
            ("id", "int"),
            ("producto_id", "int"),
            ("sku", "string"),
            ("talla", "string"),
            ("color", "string"),
            ("precio_adicional", "decimal"),
            ("activo", "bool")
        ],
        "pos": {"l": 590, "r": 810, "t": -700, "b": -920}
    },
    "Talla": {
        "attributes": [
            ("id", "int"),
            ("codigo", "string"),
            ("nombre", "string"),
            ("orden", "int"),
            ("activo", "bool")
        ],
        "pos": {"l": 590, "r": 690, "t": -960, "b": -1090}
    },
    "Color": {
        "attributes": [
            ("id", "int"),
            ("codigo_hex", "string"),
            ("nombre", "string"),
            ("activo", "bool")
        ],
        "pos": {"l": 710, "r": 810, "t": -960, "b": -1090}
    },
    "SesionVestidorVirtual": {
        "attributes": [
            ("id", "int"),
            ("usuario_id", "int"),
            ("producto_id", "int"),
            ("imagen_usuario_url", "string"),
            ("resultado_url", "string"),
            ("fecha_sesion", "datetime")
        ],
        "pos": {"l": 590, "r": 810, "t": -1130, "b": -1300}
    },

    # --- COLUMNA 4: INVENTARIO, CARRITO & RESERVAS (L: 860, R: 1080) ---
    "Inventario": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("variante_id", "int"),
            ("stock_fisico", "int"),
            ("stock_reservado", "int"),
            ("stock_disponible", "int")
        ],
        "pos": {"l": 860, "r": 1080, "t": -40, "b": -200}
    },
    "MovimientoInventario": {
        "attributes": [
            ("id", "int"),
            ("inventario_id", "int"),
            ("tipo_movimiento", "string"),
            ("cantidad", "int"),
            ("stock_anterior", "int"),
            ("stock_posterior", "int"),
            ("motivo", "string"),
            ("fecha_movimiento", "datetime")
        ],
        "pos": {"l": 860, "r": 1080, "t": -240, "b": -460}
    },
    "Carrito": {
        "attributes": [
            ("id", "int"),
            ("usuario_id", "int"),
            ("fecha_creacion", "datetime"),
            ("estado", "string")
        ],
        "pos": {"l": 860, "r": 1080, "t": -500, "b": -630}
    },
    "DetalleCarrito": {
        "attributes": [
            ("id", "int"),
            ("carrito_id", "int"),
            ("variante_id", "int"),
            ("cantidad", "int"),
            ("precio_unitario", "decimal")
        ],
        "pos": {"l": 860, "r": 1080, "t": -670, "b": -820}
    },
    "Reserva": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("cliente_id", "int"),
            ("codigo_reserva", "string"),
            ("fecha_reserva", "datetime"),
            ("fecha_limite", "datetime"),
            ("estado", "string"),
            ("es_offline", "bool")
        ],
        "pos": {"l": 860, "r": 1080, "t": -860, "b": -1060}
    },
    "DetalleReserva": {
        "attributes": [
            ("id", "int"),
            ("reserva_id", "int"),
            ("variante_id", "int"),
            ("cantidad", "int"),
            ("precio_unitario", "decimal")
        ],
        "pos": {"l": 860, "r": 1080, "t": -1100, "b": -1250}
    },

    # --- COLUMNA 5: VENTAS POS, PAGOS, ENVÍOS & ANALÍTICA IA (L: 1130, R: 1350) ---
    "Venta": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("cajero_id", "int"),
            ("cliente_id", "int"),
            ("codigo_orden", "string"),
            ("canal", "string"),
            ("subtotal", "decimal"),
            ("descuento", "decimal"),
            ("total", "decimal"),
            ("estado", "string"),
            ("es_offline", "bool"),
            ("fecha_venta", "datetime")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -40, "b": -280}
    },
    "DetalleVenta": {
        "attributes": [
            ("id", "int"),
            ("venta_id", "int"),
            ("variante_id", "int"),
            ("cantidad", "int"),
            ("precio_unitario", "decimal"),
            ("subtotal", "decimal")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -320, "b": -500}
    },
    "Pago": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("venta_id", "int"),
            ("monto", "decimal"),
            ("metodo", "string"),
            ("referencia", "string"),
            ("estado", "string"),
            ("fecha_pago", "datetime")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -540, "b": -730}
    },
    "EnvioVenta": {
        "attributes": [
            ("id", "int"),
            ("venta_id", "int"),
            ("destinatario_nombre", "string"),
            ("destinatario_ci", "string"),
            ("destinatario_telefono", "string"),
            ("direccion", "string"),
            ("ciudad", "string"),
            ("referencia", "string"),
            ("fecha_creacion", "datetime")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -770, "b": -980}
    },
    "RecomendacionIA": {
        "attributes": [
            ("id", "int"),
            ("usuario_id", "int"),
            ("producto_id", "int"),
            ("score", "decimal"),
            ("tipo_recomendacion", "string"),
            ("fecha_generacion", "datetime")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -1020, "b": -1200}
    },
    "ReporteAnaliticoIA": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("tipo_reporte", "string"),
            ("resumen_ejecutivo", "string"),
            ("metricas_clave", "string"),
            ("fecha_generacion", "datetime")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -1240, "b": -1420}
    },
    "ModeloPredictivoML": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("nombre_modelo", "string"),
            ("tipo_algoritmo", "string"),
            ("precision", "decimal"),
            ("version", "string"),
            ("fecha_entrenamiento", "datetime")
        ],
        "pos": {"l": 1130, "r": 1350, "t": -1460, "b": -1650}
    },

    # --- COLUMNA 6: LOGÍSTICA INVERSA, CAMBIOS, CUARENTENA & DEVOLUCIONES (L: 1400, R: 1630) ---
    "CuarentenaInventario": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("inventario_id", "int"),
            ("variante_id", "int"),
            ("cantidad", "int"),
            ("estado", "string"),
            ("inspeccionado_por", "int"),
            ("motivo_inspeccion", "string"),
            ("fecha_ingreso", "datetime")
        ],
        "pos": {"l": 1400, "r": 1630, "t": -40, "b": -240}
    },
    "CambioPrenda": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("venta_id", "int"),
            ("cajero_id", "int"),
            ("valor_reconocido", "decimal"),
            ("valor_entregado", "decimal"),
            ("diferencia", "decimal"),
            ("reembolso_efectivo", "decimal"),
            ("estado", "string"),
            ("fecha_cambio", "datetime")
        ],
        "pos": {"l": 1400, "r": 1630, "t": -280, "b": -490}
    },
    "DetalleCambio": {
        "attributes": [
            ("id", "int"),
            ("cambio_id", "int"),
            ("detalle_venta_id", "int"),
            ("variante_devuelta_id", "int"),
            ("cantidad_devuelta", "int"),
            ("nueva_variante_id", "int"),
            ("nueva_cantidad", "int")
        ],
        "pos": {"l": 1400, "r": 1630, "t": -530, "b": -710}
    },
    "Devolucion": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("venta_id", "int"),
            ("cajero_id", "int"),
            ("autorizado_por", "int"),
            ("numero_devolucion", "string"),
            ("total_devuelto", "decimal"),
            ("tipo_reembolso", "string"),
            ("codigo_nota_credito", "string"),
            ("motivo", "string"),
            ("estado", "string"),
            ("fecha_creacion", "datetime")
        ],
        "pos": {"l": 1400, "r": 1630, "t": -750, "b": -980}
    },
    "DetalleDevolucion": {
        "attributes": [
            ("id", "int"),
            ("devolucion_id", "int"),
            ("detalle_venta_id", "int"),
            ("variante_id", "int"),
            ("cantidad", "int"),
            ("precio_unitario", "decimal"),
            ("subtotal", "decimal"),
            ("estado_prenda", "string"),
            ("reintegrado_inventario", "bool")
        ],
        "pos": {"l": 1400, "r": 1630, "t": -1020, "b": -1230}
    },
    "NotaCredito": {
        "attributes": [
            ("id", "int"),
            ("tenant_id", "int"),
            ("sucursal_id", "int"),
            ("devolucion_id", "int"),
            ("codigo_nota", "string"),
            ("monto_total", "decimal"),
            ("estado", "string"),
            ("fecha_emision", "datetime")
        ],
        "pos": {"l": 1400, "r": 1630, "t": -1270, "b": -1460}
    }
}

RELATIONS_DEF = [
    # SaaS, Gobierno & Estructura
    ("Tenant", "Subscription", "contrata", "1", "0..*"),
    ("SubscriptionPlan", "Subscription", "define", "1", "0..*"),
    ("Tenant", "Usuario", "aloja", "1", "0..*"),
    ("Tenant", "Sucursal", "posee", "1", "0..*"),
    ("Tenant", "Bitacora", "audita", "1", "0..*"),
    ("Tenant", "Categoria", "clasifica", "1", "0..*"),
    ("Tenant", "Producto", "administra", "1", "0..*"),
    ("Tenant", "Proveedor", "registra", "1", "0..*"),
    ("Tenant", "Promocion", "configura", "1", "0..*"),
    ("Tenant", "ReporteAnaliticoIA", "consulta", "1", "0..*"),
    ("Tenant", "ModeloPredictivoML", "entrena", "1", "0..*"),
    ("Rol", "Usuario", "tiene", "1", "0..*"),
    ("Sucursal", "Usuario", "asignado_a", "0..1", "0..*"),
    ("Ciudad", "Sucursal", "ubica", "1", "1..*"),
    ("Usuario", "Cliente", "perfila", "1", "0..1"),
    ("Usuario", "Bitacora", "registra", "1", "0..*"),
    ("Usuario", "SyncOperation", "ejecuta", "1", "0..*"),
    ("Usuario", "Carrito", "posee", "1", "0..1"),
    ("Usuario", "SesionVestidorVirtual", "inicia", "1", "0..*"),
    ("Usuario", "RecomendacionIA", "recibe", "1", "0..*"),

    # Catálogo, Prendas & Clasificación
    ("Categoria", "Producto", "clasifica", "1", "0..*"),
    ("Temporada", "Coleccion", "agrupa", "1", "0..*"),
    ("Temporada", "Producto", "aplica_a", "0..1", "0..*"),
    ("Coleccion", "Producto", "contiene", "0..1", "0..*"),
    ("Proveedor", "Producto", "suministra", "0..*", "0..*"),
    ("Promocion", "Producto", "aplica_a", "0..*", "0..*"),
    ("Producto", "ImagenProducto", "posee", "1", "0..*"),
    ("Producto", "VarianteProducto", "compone", "1", "1..*"),
    ("Talla", "VarianteProducto", "especifica", "1", "0..*"),
    ("Color", "VarianteProducto", "especifica", "1", "0..*"),
    ("Producto", "SesionVestidorVirtual", "prueba", "1", "0..*"),
    ("Producto", "RecomendacionIA", "sugiere", "1", "0..*"),

    # Inventario & Kardex
    ("Sucursal", "Inventario", "almacena", "1", "0..*"),
    ("VarianteProducto", "Inventario", "controla", "1", "0..*"),
    ("Inventario", "MovimientoInventario", "registra", "1", "0..*"),
    ("CuarentenaInventario", "Inventario", "inspecciona", "0..*", "1"),

    # Carrito Web & Reservas
    ("Carrito", "DetalleCarrito", "contiene", "1", "0..*"),
    ("VarianteProducto", "DetalleCarrito", "referencia", "1", "0..*"),
    ("Cliente", "Reserva", "solicita", "1", "0..*"),
    ("Sucursal", "Reserva", "recibe", "1", "0..*"),
    ("Reserva", "DetalleReserva", "contiene", "1", "1..*"),
    ("VarianteProducto", "DetalleReserva", "reserva", "1", "0..*"),

    # Ventas POS, Pagos & Despacho
    ("Cliente", "Venta", "realiza", "1", "0..*"),
    ("Sucursal", "Venta", "emite", "1", "0..*"),
    ("Venta", "DetalleVenta", "contiene", "1", "1..*"),
    ("VarianteProducto", "DetalleVenta", "referencia", "1", "0..*"),
    ("Venta", "Pago", "liquida", "1", "1..*"),
    ("Venta", "EnvioVenta", "despacha", "1", "0..1"),

    # Post-Venta: Cambios de Prenda (CU-13)
    ("Venta", "CambioPrenda", "origina", "1", "0..*"),
    ("CambioPrenda", "DetalleCambio", "contiene", "1", "1..*"),
    ("DetalleVenta", "DetalleCambio", "cambia", "1", "0..1"),
    ("VarianteProducto", "DetalleCambio", "entrega", "1", "0..*"),
    ("DetalleCambio", "CuarentenaInventario", "ingresa_a", "1", "1"),

    # Post-Venta: Devolución y Reposición (CU-26 / RF17)
    ("Venta", "Devolucion", "origina", "1", "0..*"),
    ("Devolucion", "DetalleDevolucion", "contiene", "1", "1..*"),
    ("DetalleVenta", "DetalleDevolucion", "devuelve", "1", "0..1"),
    ("VarianteProducto", "DetalleDevolucion", "reintegra", "1", "0..*"),
    ("Devolucion", "NotaCredito", "emite", "1", "0..1"),
    ("Devolucion", "MovimientoInventario", "restituye", "1", "1..*"),
    ("Usuario", "Devolucion", "autoriza", "1", "0..*"),
    ("Sucursal", "Devolucion", "recibe", "1", "0..*")
]

def main():
    print("Iniciando generación del Modelo de Dominio General Completo en Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    pkg = rep.GetPackageByID(199) # 'Segundo Parcial - Modelo de Dominio (General Completo)'
    pkg_name = pkg.Name
    pkg_id = pkg.PackageID
    print(f"Paquete EA: '{pkg_name}' (ID: {pkg_id})")

    # 1. Crear / verificar elementos en Package 199
    print("Sincronizando clases y atributos...")
    elements_map = {pkg.Elements.GetAt(i).Name: pkg.Elements.GetAt(i) for i in range(pkg.Elements.Count)}

    for name, spec in CLASSES_DATA.items():
        if name not in elements_map:
            el = pkg.Elements.AddNew(name, "Class")
            el.Update()
            print(f"  Clase creada en Paquete 199: {name}")
            elements_map[name] = el
        else:
            el = elements_map[name]

        # Sincronizar atributos
        existing_attrs = {el.Attributes.GetAt(k).Name: el.Attributes.GetAt(k) for k in range(el.Attributes.Count)}
        for attr_name, attr_type in spec["attributes"]:
            if attr_name not in existing_attrs:
                a = el.Attributes.AddNew(attr_name, attr_type)
                a.Update()
        el.Attributes.Refresh()
        el.Update()

    pkg.Elements.Refresh()

    # 2. Sincronizar conectores de asociación
    print("Sincronizando conectores de asociación del modelo de dominio...")
    for src_name, dst_name, verb, src_card, dst_card in RELATIONS_DEF:
        if src_name not in elements_map or dst_name not in elements_map:
            print(f"  [AVISO] No se encontró {src_name} o {dst_name}")
            continue
        src_el = elements_map[src_name]
        dst_el = elements_map[dst_name]

        conn_exists = False
        for c in src_el.Connectors:
            if c.SupplierID == dst_el.ElementID and (c.Name == verb or c.Type == "Association"):
                conn_exists = True
                break

        if not conn_exists:
            conn = src_el.Connectors.AddNew(verb, "Association")
            conn.SupplierID = dst_el.ElementID
            conn.Direction = "Source -> Destination"
            conn.ClientEnd.Cardinality = src_card
            conn.SupplierEnd.Cardinality = dst_card
            conn.Update()
            src_el.Connectors.Refresh()

    # 3. Diagrama 429: 'Diagrama de Clases - Modelo de Dominio General (Segundo Parcial)'
    diag = None
    for d in pkg.Diagrams:
        if d.DiagramID == 429:
            diag = d
            break

    if diag is None:
        diag = pkg.Diagrams.AddNew("Diagrama de Clases - Modelo de Dominio General (Segundo Parcial)", "Logical")
        diag.Update()
        pkg.Diagrams.Refresh()

    diag_title = diag.Name
    print(f"Actualizando objetos en el lienzo del diagrama: '{diag_title}'...")

    existing_objs = {diag.DiagramObjects.GetAt(i).ElementID: diag.DiagramObjects.GetAt(i) for i in range(diag.DiagramObjects.Count)}

    for name, spec in CLASSES_DATA.items():
        el = elements_map[name]
        pos = spec["pos"]
        if el.ElementID in existing_objs:
            d_obj = existing_objs[el.ElementID]
        else:
            d_obj = diag.DiagramObjects.AddNew(f"l={pos['l']};r={pos['r']};t={pos['t']};b={pos['b']};", "")
            d_obj.ElementID = el.ElementID
        d_obj.left = pos["l"]
        d_obj.right = pos["r"]
        d_obj.top = pos["t"]
        d_obj.bottom = pos["b"]
        d_obj.Update()

    diag.DiagramObjects.Refresh()

    # Estilo UML 2.5 Frame
    current_style = str(diag.StyleEx or "")
    if "ShowFrame=1;" not in current_style:
        diag.StyleEx = current_style + "ShowFrame=1;"
    diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
    diag.Update()

    rep.SaveDiagram(diag.DiagramID)
    rep.ReloadDiagram(diag.DiagramID)
    pkg.Update()

    rep.CloseFile()
    rep.Exit()

    print("=" * 70)
    print("¡MODELO DE DOMINIO GENERAL COMPLETO GENERADO CON ÉXITO!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name} (ID: {pkg_id})")
    print(f"Diagrama EA: {diag_title} (ID: 429)")
    print(f"Total entidades integradas: {len(CLASSES_DATA)} clases")
    print(f"Total relaciones asociadas: {len(RELATIONS_DEF)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
