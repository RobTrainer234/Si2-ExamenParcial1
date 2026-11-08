# -*- coding: utf-8 -*-
"""
Script maestro para generar el Diagrama de Clases 'DISEÑO CONCEPTUAL DE LA BASE DE DATOS (SEGUNDO PARCIAL)'
en Enterprise Architect (CasosDeUso_SegundoParcial.eap).
Incluye todas las tablas del Segundo Parcial en español, incorporando Devolucion, DetalleDevolucion,
NotaCredito, MovimientoInventario, CambioPrenda, CuarentenaInventario y todas las entidades de Venta y SaaS.
"""

import win32com.client
import os

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

def main():
    print("Iniciando creación del Diagrama Conceptual de la Base de Datos en Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    print(f"Abriendo repositorio EA: {EAP_PATH}...")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    # 1. Obtener el Paquete 02 (ID: 8)
    pkg = rep.GetPackageByID(8) # '02 - Diseño Conceptual de la Base de Datos'
    print(f"Paquete encontrado: '{pkg.Name}' (ID: {pkg.PackageID})")

    # 2. Definición exhaustiva de entidades con nombres en español y atributos formales
    classes_data = {
        # --- ZONA SAAS Y GOBIERNO ---
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
            "pos": {"l": 50, "r": 260, "t": -40, "b": -230}
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
            "pos": {"l": 310, "r": 520, "t": -40, "b": -230}
        },
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
            "pos": {"l": 570, "r": 780, "t": -40, "b": -240}
        },
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
            "pos": {"l": 830, "r": 1040, "t": -40, "b": -220}
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
            "pos": {"l": 1090, "r": 1300, "t": -40, "b": -250}
        },
        "Rol": {
            "attributes": [
                ("id", "int"),
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ],
            "pos": {"l": 1350, "r": 1540, "t": -40, "b": -190}
        },

        # --- ZONA CATÁLOGO, SUCURSALES Y STOCK ---
        "Ciudad": {
            "attributes": [
                ("id", "int"),
                ("nombre", "string")
            ],
            "pos": {"l": 50, "r": 230, "t": -300, "b": -410}
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
            "pos": {"l": 310, "r": 520, "t": -300, "b": -480}
        },
        "Categoria": {
            "attributes": [
                ("id", "int"),
                ("tenant_id", "int"),
                ("nombre", "string"),
                ("descripcion", "string")
            ],
            "pos": {"l": 570, "r": 760, "t": -300, "b": -430}
        },
        "Producto": {
            "attributes": [
                ("id", "int"),
                ("tenant_id", "int"),
                ("categoria_id", "int"),
                ("codigo", "string"),
                ("nombre", "string"),
                ("precio_base", "decimal"),
                ("activo", "bool")
            ],
            "pos": {"l": 830, "r": 1040, "t": -300, "b": -480}
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
            "pos": {"l": 1090, "r": 1300, "t": -300, "b": -490}
        },
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
            "pos": {"l": 1350, "r": 1560, "t": -300, "b": -480}
        },

        # --- ZONA OPERACIONES COMERCIALES POS & OFFLINE ---
        "SyncOperation": {
            "attributes": [
                ("id", "int"),
                ("tenant_id", "int"),
                ("client_operation_id", "string"),
                ("tipo_operacion", "string"),
                ("tabla_afectada", "string"),
                ("dispositivo_id", "string"),
                ("estado_sync", "string"),
                ("fecha_sincronizacion", "datetime")
            ],
            "pos": {"l": 50, "r": 270, "t": -560, "b": -740}
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
            "pos": {"l": 310, "r": 510, "t": -560, "b": -740}
        },
        "DetalleReserva": {
            "attributes": [
                ("id", "int"),
                ("reserva_id", "int"),
                ("variante_id", "int"),
                ("cantidad", "int")
            ],
            "pos": {"l": 570, "r": 760, "t": -560, "b": -690}
        },
        "Venta": {
            "attributes": [
                ("id", "int"),
                ("tenant_id", "int"),
                ("sucursal_id", "int"),
                ("cajero_id", "int"),
                ("cliente_id", "int"),
                ("codigo_orden", "string"),
                ("channel", "string"),
                ("subtotal", "decimal"),
                ("descuento", "decimal"),
                ("total", "decimal"),
                ("estado", "string"),
                ("es_offline", "bool"),
                ("fecha_venta", "datetime")
            ],
            "pos": {"l": 830, "r": 1050, "t": -560, "b": -820}
        },
        "DetalleVenta": {
            "attributes": [
                ("id", "int"),
                ("venta_id", "int"),
                ("variante_id", "int"),
                ("cantidad", "int"),
                ("precio_unitario", "decimal"),
                ("descuento", "decimal"),
                ("subtotal", "decimal")
            ],
            "pos": {"l": 1100, "r": 1300, "t": -560, "b": -730}
        },
        "Pago": {
            "attributes": [
                ("id", "int"),
                ("tenant_id", "int"),
                ("venta_id", "int"),
                ("monto", "decimal"),
                ("metodo", "string"),
                ("referencia_transaccion", "string"),
                ("estado", "string"),
                ("fecha_pago", "datetime")
            ],
            "pos": {"l": 1350, "r": 1560, "t": -560, "b": -740}
        },

        # --- ZONA POST-VENTA: DEVOLUCIONES, REPOSICIÓN Y CAMBIOS (CU-13, CU-26, RF17) ---
        "MovimientoInventario": {
            "attributes": [
                ("id", "int"),
                ("inventario_id", "int"),
                ("tipo_movimiento", "string"),
                ("cantidad", "int"),
                ("stock_anterior", "int"),
                ("stock_posterior", "int"),
                ("motivo", "string"),
                ("reference_type", "string"),
                ("reference_id", "int"),
                ("fecha_movimiento", "datetime")
            ],
            "pos": {"l": 50, "r": 270, "t": -880, "b": -1100}
        },
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
            "pos": {"l": 310, "r": 520, "t": -880, "b": -1100}
        },
        "CambioPrenda": {
            "attributes": [
                ("id", "int"),
                ("tenant_id", "int"),
                ("sucursal_id", "int"),
                ("venta_id", "int"),
                ("cajero_id", "int"),
                ("idempotency_key", "string"),
                ("valor_reconocido", "decimal"),
                ("valor_entregado", "decimal"),
                ("diferencia", "decimal"),
                ("reembolso_efectivo", "decimal"),
                ("estado", "string"),
                ("fecha_cambio", "datetime")
            ],
            "pos": {"l": 570, "r": 780, "t": -880, "b": -1120}
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
            "pos": {"l": 830, "r": 1060, "t": -880, "b": -1140}
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
            "pos": {"l": 1100, "r": 1310, "t": -880, "b": -1100}
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
            "pos": {"l": 1350, "r": 1560, "t": -880, "b": -1060}
        }
    }

    # 3. Crear o actualizar elementos en Package 8
    print("Creando / actualizando clases en el paquete...")
    elements_map = {}
    for name, spec in classes_data.items():
        found = None
        for j in range(pkg.Elements.Count):
            item = pkg.Elements.GetAt(j)
            if item.Name == name and item.Type == "Class":
                found = item
                break
        if not found:
            found = pkg.Elements.AddNew(name, "Class")
            found.Update()
            print(f"  Clase creada: {name}")

        # Sincronizar atributos
        existing_attrs = {found.Attributes.GetAt(k).Name: found.Attributes.GetAt(k) for k in range(found.Attributes.Count)}
        for attr_name, attr_type in spec["attributes"]:
            if attr_name not in existing_attrs:
                a = found.Attributes.AddNew(attr_name, attr_type)
                a.Update()
        found.Attributes.Refresh()
        found.Update()
        elements_map[name] = found
    pkg.Elements.Refresh()

    # 4. Crear o actualizar el Diagrama
    diag_title = "DISEÑO CONCEPTUAL DE LA BASE DE DATOS (SEGUNDO PARCIAL COMPLETO)"
    diag = None
    for d in pkg.Diagrams:
        if d.Name == diag_title:
            diag = d
            break
            
    if diag is None:
        diag = pkg.Diagrams.AddNew(diag_title, "Class")
        diag.Update()
        pkg.Diagrams.Refresh()
        print(f"Diagrama nuevo creado: '{diag_title}'")
    else:
        print(f"Diagrama existente encontrado: '{diag_title}'")

    # Posicionar en el lienzo (idempotente)
    existing_objs = {diag.DiagramObjects.GetAt(i).ElementID: diag.DiagramObjects.GetAt(i) for i in range(diag.DiagramObjects.Count)}

    for name, spec in classes_data.items():
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

    # 5. Relaciones entre entidades (Asociaciones con Cardinalidad y Verbo)
    relations_def = [
        # SaaS & Estructura
        ("SubscriptionPlan", "Subscription", "define", "1", "0..*"),
        ("Tenant", "Subscription", "contrata", "1", "0..*"),
        ("Tenant", "Usuario", "aloja", "1", "0..*"),
        ("Tenant", "Sucursal", "posee", "1", "0..*"),
        ("Tenant", "Bitacora", "audita", "1", "0..*"),
        ("Tenant", "Categoria", "clasifica", "1", "0..*"),
        ("Tenant", "Producto", "administra", "1", "0..*"),
        ("Rol", "Usuario", "tiene", "1", "0..*"),
        ("Sucursal", "Usuario", "asignado_a", "0..1", "0..*"),
        ("Ciudad", "Sucursal", "ubica", "1", "0..*"),

        # Catálogo e Inventario
        ("Categoria", "Producto", "agrupa", "1", "0..*"),
        ("Producto", "VarianteProducto", "compone", "1", "1..*"),
        ("Sucursal", "Inventario", "almacena", "1", "0..*"),
        ("VarianteProducto", "Inventario", "controla", "1", "0..*"),
        ("Inventario", "MovimientoInventario", "registra", "1", "0..*"),
        ("CuarentenaInventario", "Inventario", "inspecciona", "0..*", "1"),

        # Operaciones Comerciales
        ("Usuario", "SyncOperation", "ejecuta", "1", "0..*"),
        ("Sucursal", "Reserva", "recibe", "1", "0..*"),
        ("Reserva", "DetalleReserva", "contiene", "1", "1..*"),
        ("VarianteProducto", "DetalleReserva", "reserva", "1", "0..*"),
        ("Sucursal", "Venta", "emite", "1", "0..*"),
        ("Venta", "DetalleVenta", "contiene", "1", "1..*"),
        ("VarianteProducto", "DetalleVenta", "referencia", "1", "0..*"),
        ("Venta", "Pago", "liquida", "1", "1..*"),

        # Post-Venta: Cambios de Prendas (CU-13)
        ("Venta", "CambioPrenda", "origina", "1", "0..*"),
        ("CambioPrenda", "CuarentenaInventario", "aisla", "1", "1"),

        # Post-Venta: Devolución y Reposición (CU-26 / RF17)
        ("Venta", "Devolucion", "origina", "1", "0..*"),
        ("Devolucion", "DetalleDevolucion", "contiene", "1", "1..*"),
        ("DetalleVenta", "DetalleDevolucion", "devuelve", "1", "0..1"),
        ("VarianteProducto", "DetalleDevolucion", "reintegra", "1", "0..*"),
        ("Devolucion", "NotaCredito", "emite", "1", "0..1"),
        ("Devolucion", "MovimientoInventario", "restituye_kardex", "1", "1..*"),
        ("Usuario", "Devolucion", "autoriza", "1", "0..*"),
        ("Sucursal", "Devolucion", "recibe", "1", "0..*")
    ]

    print("Sincronizando conectores de asociación...")
    for src_name, dst_name, verb, src_card, dst_card in relations_def:
        src_el = elements_map[src_name]
        dst_el = elements_map[dst_name]

        # Verificar si el conector ya existe
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

    # Configuración de estilo UML 2.5
    current_style = str(diag.StyleEx or "")
    if "ShowFrame=1;" not in current_style:
        diag.StyleEx = current_style + "ShowFrame=1;"
    diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
    diag.DiagramObjects.Refresh()
    diag.Update()

    rep.SaveDiagram(diag.DiagramID)
    rep.ReloadDiagram(diag.DiagramID)
    pkg.Update()

    pkg_name = pkg.Name
    pkg_id = pkg.PackageID

    rep.CloseFile()
    rep.Exit()

    print("=" * 70)
    print("DISEÑO CONCEPTUAL DE LA BASE DE DATOS (SEGUNDO PARCIAL) GENERADO EXITOSAMENTE!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name} (ID: {pkg_id})")
    print(f"Diagrama EA: {diag_title}")
    print(f"Total entidades en el diagrama: {len(classes_data)}")
    print(f"Total relaciones asociadas: {len(relations_def)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
