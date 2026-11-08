# -*- coding: utf-8 -*-
"""
Script maestro para generar el Diagrama de Clases - Modelo de Dominio General (Segundo Parcial Completo)
directamente en Sparx Enterprise Architect (CasosDeUso_SegundoParcial.eap).
Incluye las 3 etapas del segundo parcial con las 26 clases de dominio, incluyendo Devolución,
Nota de Crédito, Cambio de Prendas, Cuarentena, Kardex, IA y SaaS.
"""

import win32com.client
import os

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

def main():
    print("Iniciando creación del Modelo de Dominio General (Segundo Parcial Completo)...")
    rep = win32com.client.Dispatch('EA.Repository')
    print(f"Abriendo repositorio EA: {EAP_PATH}...")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    root_model = rep.Models.GetAt(0)

    pkg_name = "Segundo Parcial - Modelo de Dominio (General Completo)"
    target_pkg = None
    for p in root_model.Packages:
        if p.Name == pkg_name:
            target_pkg = p
            break

    if target_pkg is None:
        target_pkg = root_model.Packages.AddNew(pkg_name, "Package")
        target_pkg.Notes = "Modelo de Dominio General y Conceptual que abarca las 3 etapas del Segundo Parcial (SaaS, Catálogo Offline, Operaciones POS, Cuarentena, Cambios, Devoluciones e IA)."
        target_pkg.Update()
        root_model.Packages.Refresh()
        print(f"Paquete creado: {target_pkg.Name} (ID={target_pkg.PackageID})")
    else:
        print(f"Usando paquete existente: {target_pkg.Name} (ID={target_pkg.PackageID})")
        # Limpiar diagramas y elementos previos del paquete
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()

        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()

    diag_title = "Diagrama de Clases - Modelo de Dominio General (Segundo Parcial)"
    diag = target_pkg.Diagrams.AddNew(diag_title, "Logical")
    diag.Notes = "Diagrama de Clases y Modelo de Dominio General oficial que integra la totalidad de entidades del Segundo Parcial."
    diag.Update()
    print(f"Diagrama creado: {diag.Name} (ID={diag.DiagramID})")

    # -------------------------------------------------------------
    # 26 Entidades de Dominio organizadas por capas y cuadrantes
    # -------------------------------------------------------------
    entities_def = {
        # --- FILA 1: SaaS Multitenant, Auditoría y Analítica IA ---
        "SubscriptionPlan": {
            "attrs": [
                ("codigo_plan", "string"),
                ("nombre_plan", "string"),
                ("precio_mensual", "decimal"),
                ("max_sucursales", "int"),
                ("max_usuarios", "int"),
                ("permite_offline", "bool"),
                ("permite_ia", "bool"),
                ("activo", "bool")
            ],
            "coords": (50, 260, -40, -210)
        },
        "Subscription": {
            "attrs": [
                ("fecha_inicio", "date"),
                ("fecha_fin", "date"),
                ("estado", "string"),
                ("metodo_pago", "string"),
                ("auto_renovar", "bool")
            ],
            "coords": (310, 520, -40, -200)
        },
        "Tenant": {
            "attrs": [
                ("codigo_tenant", "string"),
                ("nombre_empresa", "string"),
                ("nit_ruc", "string"),
                ("subdominio", "string"),
                ("estado", "string"),
                ("fecha_registro", "datetime")
            ],
            "coords": (570, 790, -40, -210)
        },
        "Bitacora": {
            "attrs": [
                ("accion", "string"),
                ("tipo_entidad", "string"),
                ("descripcion", "string"),
                ("fecha_hora", "datetime"),
                ("ip_origen", "string")
            ],
            "coords": (840, 1050, -40, -200)
        },
        "ReporteAnaliticoIA": {
            "attrs": [
                ("prompt_consulta", "string"),
                ("consulta_sql_generada", "string"),
                ("narrativa", "string"),
                ("fecha_generacion", "datetime"),
                ("formato_exportacion", "string")
            ],
            "coords": (1100, 1330, -40, -200)
        },
        "ModeloPredictivoML": {
            "attrs": [
                ("nombre_modelo", "string"),
                ("tipo_algoritmo", "string"),
                ("metricas_rendimiento", "string"),
                ("fecha_entrenamiento", "datetime"),
                ("version", "string")
            ],
            "coords": (1380, 1610, -40, -200)
        },

        # --- FILA 2: Estructura Organizacional y Catálogo de Prendas ---
        "Rol": {
            "attrs": [
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ],
            "coords": (50, 260, -260, -400)
        },
        "Usuario": {
            "attrs": [
                ("nombre_completo", "string"),
                ("email", "string"),
                ("password_hash", "string"),
                ("activo", "bool"),
                ("fecha_creacion", "datetime")
            ],
            "coords": (310, 520, -260, -420)
        },
        "Sucursal": {
            "attrs": [
                ("nombre", "string"),
                ("direccion", "string"),
                ("telefono", "string"),
                ("ciudad", "string"),
                ("activo", "bool")
            ],
            "coords": (570, 790, -260, -420)
        },
        "Categoria": {
            "attrs": [
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ],
            "coords": (840, 1050, -260, -390)
        },
        "Producto": {
            "attrs": [
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("precio_base", "decimal"),
                ("activo", "bool")
            ],
            "coords": (1100, 1330, -260, -420)
        },
        "VarianteProducto": {
            "attrs": [
                ("codigo_barra", "string"),
                ("sku", "string"),
                ("talla", "string"),
                ("color", "string"),
                ("precio_adicional", "decimal"),
                ("activo", "bool")
            ],
            "coords": (1380, 1610, -260, -430)
        },

        # --- FILA 3: Gestión de Stock, Kardex, Cuarentena y Conectividad ---
        "SyncOperation": {
            "attrs": [
                ("client_operation_id", "string"),
                ("tipo_operacion", "string"),
                ("tabla_afectada", "string"),
                ("dispositivo_id", "string"),
                ("estado_sync", "string"),
                ("fecha_sincronizacion", "datetime")
            ],
            "coords": (50, 260, -480, -640)
        },
        "Cliente": {
            "attrs": [
                ("ci_nit", "string"),
                ("nombre_completo", "string"),
                ("telefono", "string"),
                ("email", "string"),
                ("registrado_offline", "bool")
            ],
            "coords": (310, 520, -480, -640)
        },
        "Inventario": {
            "attrs": [
                ("stock_fisico", "int"),
                ("stock_reservado", "int"),
                ("stock_disponible", "int")
            ],
            "coords": (570, 790, -480, -620)
        },
        "MovimientoInventario": {
            "attrs": [
                ("tipo_movimiento", "string"),
                ("cantidad", "int"),
                ("stock_anterior", "int"),
                ("stock_posterior", "int"),
                ("motivo", "string"),
                ("fecha_movimiento", "datetime")
            ],
            "coords": (840, 1070, -480, -650)
        },
        "CuarentenaInventario": {
            "attrs": [
                ("cantidad", "int"),
                ("estado", "string"),
                ("motivo_inspeccion", "string"),
                ("fecha_ingreso", "datetime"),
                ("fecha_inspeccion", "datetime")
            ],
            "coords": (1110, 1350, -480, -650)
        },

        # --- FILA 4: Transacciones Comerciales Offline / Online y Pagos ---
        "Reserva": {
            "attrs": [
                ("codigo_reserva", "string"),
                ("fecha_reserva", "datetime"),
                ("fecha_limite", "datetime"),
                ("estado", "string"),
                ("es_offline", "bool")
            ],
            "coords": (50, 260, -710, -870)
        },
        "DetalleReserva": {
            "attrs": [
                ("cantidad", "int")
            ],
            "coords": (310, 500, -710, -820)
        },
        "Venta": {
            "attrs": [
                ("codigo_orden", "string"),
                ("canal", "string"),
                ("subtotal", "decimal"),
                ("descuento", "decimal"),
                ("total", "decimal"),
                ("estado", "string"),
                ("fecha_venta", "datetime"),
                ("es_offline", "bool")
            ],
            "coords": (570, 790, -710, -910)
        },
        "DetalleVenta": {
            "attrs": [
                ("cantidad", "int"),
                ("precio_unitario", "decimal"),
                ("descuento_linea", "decimal"),
                ("subtotal_linea", "decimal")
            ],
            "coords": (840, 1070, -710, -870)
        },
        "Pago": {
            "attrs": [
                ("monto", "decimal"),
                ("metodo", "string"),
                ("referencia_transaccion", "string"),
                ("estado", "string"),
                ("fecha_pago", "datetime")
            ],
            "coords": (1110, 1350, -710, -870)
        },

        # --- FILA 5: Post-Venta: Cambios, Devoluciones y Reposición ---
        "CambioPrenda": {
            "attrs": [
                ("codigo_cambio", "string"),
                ("fecha_cambio", "datetime"),
                ("diferencia_precio", "decimal"),
                ("tipo_diferencia", "string"),
                ("estado", "string"),
                ("idempotency_key", "string")
            ],
            "coords": (50, 270, -960, -1130)
        },
        "DetalleCambio": {
            "attrs": [
                ("cantidad_devuelta", "int"),
                ("cantidad_entregada", "int"),
                ("valor_reconocido", "decimal"),
                ("valor_entregado", "decimal")
            ],
            "coords": (320, 530, -960, -1120)
        },
        "Devolucion": {
            "attrs": [
                ("codigo_devolucion", "string"),
                ("fecha_devolucion", "datetime"),
                ("motivo", "string"),
                ("estado", "string"),
                ("monto_reembolsado", "decimal"),
                ("tipo_reembolso", "string"),
                ("estado_prenda", "string")
            ],
            "coords": (580, 800, -960, -1140)
        },
        "NotaCredito": {
            "attrs": [
                ("codigo_nota", "string"),
                ("fecha_emision", "datetime"),
                ("monto_total", "decimal"),
                ("estado", "string"),
                ("motivo", "string")
            ],
            "coords": (850, 1070, -960, -1110)
        }
    }

    # Crear Clases y Atributos
    element_map = {}
    for ent_name, data in entities_def.items():
        el = target_pkg.Elements.AddNew(ent_name, "Class")
        el.Update()

        for attr_name, attr_type in data["attrs"]:
            attr = el.Attributes.AddNew(attr_name, attr_type)
            attr.Update()
        el.Attributes.Refresh()

        element_map[ent_name] = el

        l, r, t, b = data["coords"]
        d_obj = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
        d_obj.ElementID = el.ElementID
        d_obj.left = l
        d_obj.right = r
        d_obj.top = t
        d_obj.bottom = b
        d_obj.Update()

    # -------------------------------------------------------------
    # Relaciones y Asociaciones del Modelo de Dominio
    # (Source, Target, Verb/Name, Source_Card, Target_Card)
    # -------------------------------------------------------------
    relations_def = [
        # SaaS y Gobierno
        ("Tenant", "Subscription", "contrata", "1", "0..*"),
        ("SubscriptionPlan", "Subscription", "define", "1", "0..*"),
        ("Tenant", "Usuario", "aloja", "1", "0..*"),
        ("Tenant", "Sucursal", "posee", "1", "0..*"),
        ("Tenant", "Bitacora", "audita", "1", "0..*"),
        ("Tenant", "Categoria", "clasifica", "1", "0..*"),
        ("Tenant", "Producto", "administra", "1", "0..*"),
        ("Tenant", "ReporteAnaliticoIA", "consulta", "1", "0..*"),
        ("Tenant", "ModeloPredictivoML", "entrena", "1", "0..*"),

        # Roles y Usuarios
        ("Rol", "Usuario", "tiene", "1", "0..*"),
        ("Sucursal", "Usuario", "asignado_a", "0..1", "0..*"),
        ("Usuario", "SyncOperation", "ejecuta", "1", "0..*"),
        ("Usuario", "Bitacora", "registra", "1", "0..*"),

        # Catálogo e Inventario
        ("Categoria", "Producto", "clasifica", "1", "0..*"),
        ("Producto", "VarianteProducto", "compone", "1", "1..*"),
        ("Sucursal", "Inventario", "almacena", "1", "0..*"),
        ("VarianteProducto", "Inventario", "controla", "1", "0..*"),
        ("Inventario", "MovimientoInventario", "registra", "1", "0..*"),
        ("CuarentenaInventario", "Inventario", "inspecciona", "0..*", "1"),

        # Ventas, Reservas y Pagos
        ("Cliente", "Venta", "realiza", "1", "0..*"),
        ("Cliente", "Reserva", "solicita", "1", "0..*"),
        ("Sucursal", "Venta", "emite", "1", "0..*"),
        ("Sucursal", "Reserva", "recibe", "1", "0..*"),
        ("Venta", "DetalleVenta", "contiene", "1", "1..*"),
        ("VarianteProducto", "DetalleVenta", "referencia", "1", "0..*"),
        ("Venta", "Pago", "liquida", "1", "1..*"),
        ("Reserva", "DetalleReserva", "contiene", "1", "1..*"),
        ("VarianteProducto", "DetalleReserva", "reserva", "1", "0..*"),

        # Post-Venta: Cambios de Prendas (CU-13)
        ("Venta", "CambioPrenda", "origina", "1", "0..*"),
        ("CambioPrenda", "DetalleCambio", "contiene", "1", "1..*"),
        ("DetalleCambio", "CuarentenaInventario", "ingresa_a", "1", "1"),

        # Post-Venta: Devolución y Reposición (CU-26)
        ("Venta", "Devolucion", "origina", "1", "0..*"),
        ("Devolucion", "NotaCredito", "emite", "1", "0..1"),
        ("Devolucion", "MovimientoInventario", "restituye", "1", "1..*"),
        ("Usuario", "Devolucion", "autoriza", "1", "0..*"),
        ("Sucursal", "Devolucion", "recibe", "1", "0..*")
    ]

    for src_name, dst_name, verb, src_card, dst_card in relations_def:
        src_el = element_map[src_name]
        dst_el = element_map[dst_name]

        conn = src_el.Connectors.AddNew(verb, "Association")
        conn.SupplierID = dst_el.ElementID
        conn.Direction = "Source -> Destination"

        conn.ClientEnd.Cardinality = src_card
        conn.SupplierEnd.Cardinality = dst_card
        conn.Update()

    diag.StyleEx = "HideQuals=1;DocAll=0;"
    diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
    diag.DiagramObjects.Refresh()
    diag.Update()

    rep.SaveDiagram(diag.DiagramID)
    rep.ReloadDiagram(diag.DiagramID)

    target_pkg.Update()
    root_model.Packages.Refresh()

    rep.CloseFile()
    rep.Exit()

    print("=" * 70)
    print("MODELO DE DOMINIO GENERAL (SEGUNDO PARCIAL) GENERADO EXITOSAMENTE!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name}")
    print(f"Diagrama EA: {diag_title}")
    print(f"Total entidades creadas: {len(entities_def)}")
    print(f"Total relaciones asociadas: {len(relations_def)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
