# -*- coding: utf-8 -*-
"""
Script maestro para completar el Diagrama Conceptual de la Base de Datos en Enterprise Architect.
Actualiza Diagrama 11 ('DISEÑO CONCEPTUAL DE LA BASE DE DATOS (FASHIONSTORE COMPLETO)')
y Diagrama 430 ('DISEÑO CONCEPTUAL DE LA BASE DE DATOS (SEGUNDO PARCIAL COMPLETO)')
integrando las 30 clases originales + las 7 nuevas entidades de cambios, cuarentena,
devoluciones, notas de crédito y envíos (Total: 37 entidades).
"""

import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

NEW_ENTITIES = {
    "DetalleCambioPrenda": {
        "attributes": [
            ("id", "int"),
            ("cambio_id", "int"),
            ("detalle_venta_id", "int"),
            ("variante_devuelta_id", "int"),
            ("cantidad_devuelta", "int"),
            ("nueva_variante_id", "int"),
            ("nueva_cantidad", "int")
        ],
        "pos": {"l": 1530, "r": 1760, "t": -740, "b": -920}
    },
    "EnvioVenta": {
        "attributes": [
            ("id", "int"),
            ("venta_id", "int"),
            ("destinatario_nombre", "string"),
            ("destinatario_ci", "string"),
            ("destinatario_telefono", "string"),
            ("departamento_ciudad", "string"),
            ("zona", "string"),
            ("calle", "string"),
            ("numero_casa", "string"),
            ("referencia", "string"),
            ("fecha_creacion", "datetime")
        ],
        "pos": {"l": 1530, "r": 1760, "t": -1760, "b": -1980}
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
        "pos": {"l": 1530, "r": 1760, "t": -200, "b": -420}
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
        "pos": {"l": 1530, "r": 1760, "t": -470, "b": -690}
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
        "pos": {"l": 1530, "r": 1760, "t": -970, "b": -1210}
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
        "pos": {"l": 1530, "r": 1760, "t": -1260, "b": -1480}
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
        "pos": {"l": 1530, "r": 1760, "t": -1530, "b": -1710}
    }
}

NEW_RELATIONS = [
    # Post-Venta: Cambios de Prendas (CU-13)
    ("Venta", "CambioPrenda", "origina", "1", "0..*"),
    ("CambioPrenda", "DetalleCambioPrenda", "desglosa", "1", "1..*"),
    ("DetalleVenta", "DetalleCambioPrenda", "cambia", "1", "0..1"),
    ("VarianteProducto", "DetalleCambioPrenda", "reemplaza", "1", "0..*"),
    ("DetalleCambioPrenda", "CuarentenaInventario", "aisla", "1", "1"),
    ("CuarentenaInventario", "Inventario", "inspecciona", "0..*", "1"),

    # Post-Venta: Devolución y Reposición (CU-26 / RF17)
    ("Venta", "Devolucion", "origina", "1", "0..*"),
    ("Devolucion", "DetalleDevolucion", "contiene", "1", "1..*"),
    ("DetalleVenta", "DetalleDevolucion", "devuelve", "1", "0..1"),
    ("VarianteProducto", "DetalleDevolucion", "reintegra", "1", "0..*"),
    ("Devolucion", "NotaCredito", "emite", "1", "0..1"),
    ("Devolucion", "MovimientoInventario", "restituye_kardex", "1", "1..*"),
    ("Usuario", "Devolucion", "autoriza", "1", "0..*"),
    ("Sucursal", "Devolucion", "recibe", "1", "0..*"),

    # Envíos / Despacho a domicilio
    ("Venta", "EnvioVenta", "despacha", "1", "0..1")
]

def main():
    print("Iniciando actualización completa del Diagrama Conceptual de la BD...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    pkg = rep.GetPackageByID(8)
    pkg_name = pkg.Name
    pkg_id = pkg.PackageID
    print(f"Paquete EA: '{pkg_name}' (ID: {pkg_id})")

    # 1. Crear / verificar elementos en Package 8
    elements_map = {pkg.Elements.GetAt(i).Name: pkg.Elements.GetAt(i) for i in range(pkg.Elements.Count)}
    
    for name, spec in NEW_ENTITIES.items():
        if name not in elements_map:
            el = pkg.Elements.AddNew(name, "Class")
            el.Update()
            print(f"  Clase nueva creada: {name}")
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

    # 2. Sincronizar conectores nuevos
    print("Sincronizando nuevos conectores de asociación...")
    for src_name, dst_name, verb, src_card, dst_card in NEW_RELATIONS:
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

    # 3. Actualizar Diagrama 11 ('DISEÑO CONCEPTUAL DE LA BASE DE DATOS (FASHIONSTORE COMPLETO)')
    d11 = None
    d430 = None
    for d in pkg.Diagrams:
        if d.DiagramID == 11:
            d11 = d
        elif d.DiagramID == 430:
            d430 = d

    if d11 is not None:
        print(f"Actualizando Diagrama 11: '{d11.Name}'...")
        d11_objs = {d11.DiagramObjects.GetAt(i).ElementID: d11.DiagramObjects.GetAt(i) for i in range(d11.DiagramObjects.Count)}
        for name, spec in NEW_ENTITIES.items():
            el = elements_map[name]
            pos = spec["pos"]
            if el.ElementID in d11_objs:
                d_obj = d11_objs[el.ElementID]
            else:
                d_obj = d11.DiagramObjects.AddNew(f"l={pos['l']};r={pos['r']};t={pos['t']};b={pos['b']};", "")
                d_obj.ElementID = el.ElementID
            d_obj.left = pos["l"]
            d_obj.right = pos["r"]
            d_obj.top = pos["t"]
            d_obj.bottom = pos["b"]
            d_obj.Update()
        d11.DiagramObjects.Refresh()
        d11.Update()
        rep.SaveDiagram(d11.DiagramID)
        rep.ReloadDiagram(d11.DiagramID)
        print(f"  Diagrama 11 actualizado. Total clases en diagrama: {d11.DiagramObjects.Count}")

    # 4. Actualizar Diagrama 430 ('DISEÑO CONCEPTUAL DE LA BASE DE DATOS (SEGUNDO PARCIAL COMPLETO)')
    if d430 is not None:
        print(f"Actualizando Diagrama 430: '{d430.Name}'...")
        # Asegurar que todas las 30 clases originales + 7 nuevas estén en 430 con la misma distribución
        d430_objs = {d430.DiagramObjects.GetAt(i).ElementID: d430.DiagramObjects.GetAt(i) for i in range(d430.DiagramObjects.Count)}
        # Copiar posiciones de d11 para que sea idéntico y ordenado
        if d11 is not None:
            for i in range(d11.DiagramObjects.Count):
                src_obj = d11.DiagramObjects.GetAt(i)
                eid = src_obj.ElementID
                if eid in d430_objs:
                    tgt_obj = d430_objs[eid]
                else:
                    tgt_obj = d430.DiagramObjects.AddNew(f"l={src_obj.left};r={src_obj.right};t={src_obj.top};b={src_obj.bottom};", "")
                    tgt_obj.ElementID = eid
                tgt_obj.left = src_obj.left
                tgt_obj.right = src_obj.right
                tgt_obj.top = src_obj.top
                tgt_obj.bottom = src_obj.bottom
                tgt_obj.Update()
        d430.DiagramObjects.Refresh()
        d430.Update()
        rep.SaveDiagram(d430.DiagramID)
        rep.ReloadDiagram(d430.DiagramID)
        print(f"  Diagrama 430 actualizado. Total clases en diagrama: {d430.DiagramObjects.Count}")

    pkg.Update()
    rep.CloseFile()
    rep.Exit()

    print("=" * 70)
    print("¡DIAGRAMAS CONCEPTUALES DE BASE DE DATOS ACTUALIZADOS CON ÉXITO!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name} (ID: {pkg_id})")
    print(f"Total entidades integradas: 37 clases (30 existentes + 7 nuevas)")
    print("=" * 70)

if __name__ == '__main__':
    main()
