"""Script para crear el DIAGRAMA COMPLETO DE LA BASE DE DATOS DE FASHIONSTORE (Ciclos 1, 2 y 3).

Incluye todas las 26 entidades del sistema en español, con atributos tipados en privado (-),
multiplicidades explícitas en conectores, disposición espacial agrupada y marco UML 2.5.
"""

import os
import sys
from pathlib import Path
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\diseno-conceptual-base-de-datos-completo.png"

def main():
    print("Iniciando conexión con Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"Error: No se pudo abrir {MODEL_PATH}")
        return 1

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    # 1. Obtener o crear el paquete
    pkg_name = "02 - Diseño Conceptual de la Base de Datos"
    target_pkg = None
    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            target_pkg = p
            break

    if target_pkg is None:
        target_pkg = root_model.Packages.AddNew(pkg_name, "")
        target_pkg.Update()
        root_model.Packages.Refresh()

    # 2. Especificación de las 26 entidades de FashionStore (Ciclos 1, 2 y 3)
    classes_data = {
        # --- ZONA 1: SEGURIDAD, ACCESO Y AUDITORÍA ---
        "Rol": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "codigo", "type": "string", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 920, "right": 1100, "top": -40, "bottom": -160},
        },
        "Usuario": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "rol_id", "type": "int", "visibility": "Private"},
                {"name": "sucursal_id", "type": "int", "visibility": "Private"},
                {"name": "nombre_completo", "type": "string", "visibility": "Private"},
                {"name": "email", "type": "string", "visibility": "Private"},
                {"name": "password", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
                {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
            ],
            "pos": {"left": 920, "right": 1130, "top": -200, "bottom": -400},
        },
        "Bitacora": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
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
            "pos": {"left": 1220, "right": 1420, "top": -40, "bottom": -270},
        },

        # --- ZONA 2: UBICACIÓN Y SUCURSALES ---
        "Ciudad": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 50, "right": 230, "top": -40, "bottom": -150},
        },
        "Sucursal": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "ciudad_id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "direccion", "type": "string", "visibility": "Private"},
                {"name": "telefono", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 50, "right": 250, "top": -190, "bottom": -350},
        },

        # --- ZONA 3: CATÁLOGO MAESTRO Y PRODUCTOS ---
        "Categoria": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "descripcion", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 50, "right": 250, "top": -390, "bottom": -510},
        },
        "Temporada": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "fecha_inicio", "type": "date", "visibility": "Private"},
                {"name": "fecha_fin", "type": "date", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 50, "right": 250, "top": -550, "bottom": -690},
        },
        "Coleccion": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "temporada_id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "descripcion", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 50, "right": 250, "top": -730, "bottom": -870},
        },
        "Proveedor": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "razon_social", "type": "string", "visibility": "Private"},
                {"name": "nit", "type": "string", "visibility": "Private"},
                {"name": "email", "type": "string", "visibility": "Private"},
                {"name": "telefono", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 50, "right": 250, "top": -910, "bottom": -1070},
        },
        "Producto": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
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
            "pos": {"left": 340, "right": 550, "top": -390, "bottom": -650},
        },
        "ImagenProducto": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "producto_id", "type": "int", "visibility": "Private"},
                {"name": "url_imagen", "type": "string", "visibility": "Private"},
                {"name": "es_principal", "type": "bool", "visibility": "Private"},
                {"name": "orden", "type": "int", "visibility": "Private"},
            ],
            "pos": {"left": 340, "right": 530, "top": -190, "bottom": -330},
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
            "pos": {"left": 340, "right": 560, "top": -710, "bottom": -930},
        },
        "Talla": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "orden", "type": "int", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 250, "right": 410, "top": -990, "bottom": -1110},
        },
        "Color": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "codigo_hex", "type": "string", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 450, "right": 610, "top": -990, "bottom": -1110},
        },

        # --- ZONA 4: INVENTARIO Y MOVIMIENTOS ---
        "Inventario": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "sucursal_id", "type": "int", "visibility": "Private"},
                {"name": "variante_id", "type": "int", "visibility": "Private"},
                {"name": "stock_fisico", "type": "int", "visibility": "Private"},
                {"name": "stock_reservado", "type": "int", "visibility": "Private"},
            ],
            "pos": {"left": 630, "right": 830, "top": -600, "bottom": -750},
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
            "pos": {"left": 630, "right": 850, "top": -800, "bottom": -1030},
        },

        # --- ZONA 5: CARRITO, RESERVAS Y VENTAS ---
        "Carrito": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "usuario_id", "type": "int", "visibility": "Private"},
                {"name": "estado", "type": "string", "visibility": "Private"},
                {"name": "fecha_creacion", "type": "datetime", "visibility": "Private"},
            ],
            "pos": {"left": 920, "right": 1100, "top": -450, "bottom": -570},
        },
        "DetalleCarrito": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "carrito_id", "type": "int", "visibility": "Private"},
                {"name": "variante_id", "type": "int", "visibility": "Private"},
                {"name": "cantidad", "type": "int", "visibility": "Private"},
                {"name": "precio_unitario", "type": "decimal", "visibility": "Private"},
            ],
            "pos": {"left": 630, "right": 830, "top": -410, "bottom": -560},
        },
        "Reserva": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "usuario_id", "type": "int", "visibility": "Private"},
                {"name": "sucursal_id", "type": "int", "visibility": "Private"},
                {"name": "codigo_reserva", "type": "string", "visibility": "Private"},
                {"name": "fecha_programada", "type": "datetime", "visibility": "Private"},
                {"name": "estado", "type": "string", "visibility": "Private"},
                {"name": "notas", "type": "string", "visibility": "Private"},
                {"name": "expira_en", "type": "datetime", "visibility": "Private"},
            ],
            "pos": {"left": 920, "right": 1130, "top": -620, "bottom": -820},
        },
        "DetalleReserva": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "reserva_id", "type": "int", "visibility": "Private"},
                {"name": "variante_id", "type": "int", "visibility": "Private"},
                {"name": "cantidad", "type": "int", "visibility": "Private"},
                {"name": "precio_unitario", "type": "decimal", "visibility": "Private"},
            ],
            "pos": {"left": 920, "right": 1130, "top": -870, "bottom": -1010},
        },
        "Venta": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
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
            "pos": {"left": 1220, "right": 1430, "top": -340, "bottom": -600},
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
            "pos": {"left": 1220, "right": 1430, "top": -650, "bottom": -820},
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
            "pos": {"left": 1220, "right": 1430, "top": -870, "bottom": -1110},
        },

        # --- ZONA 6: INNOVACIÓN Y ANALÍTICA (CICLO 3) ---
        "Promocion": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "tipo_descuento", "type": "string", "visibility": "Private"},
                {"name": "valor_descuento", "type": "decimal", "visibility": "Private"},
                {"name": "fecha_inicio", "type": "datetime", "visibility": "Private"},
                {"name": "fecha_fin", "type": "datetime", "visibility": "Private"},
                {"name": "activo", "type": "bool", "visibility": "Private"},
            ],
            "pos": {"left": 340, "right": 540, "top": -1160, "bottom": -1340},
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
            "pos": {"left": 630, "right": 840, "top": -190, "bottom": -360},
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
            "pos": {"left": 1220, "right": 1430, "top": -1150, "bottom": -1330},
        },
    }

    # 3. Crear o actualizar elementos
    created_elements = {}
    for name, spec in classes_data.items():
        el = None
        for j in range(target_pkg.Elements.Count):
            item = target_pkg.Elements.GetAt(j)
            if item.Name == name and item.Type == "Class":
                el = item
                break
        if el is None:
            el = target_pkg.Elements.AddNew(name, "Class")
            el.Update()

        # Atributos
        existing_attrs = {el.Attributes.GetAt(k).Name: el.Attributes.GetAt(k) for k in range(el.Attributes.Count)}
        for attr in spec["attributes"]:
            attr_name = attr["name"]
            if attr_name in existing_attrs:
                a = existing_attrs[attr_name]
            else:
                a = el.Attributes.AddNew(attr_name, attr["type"])
            a.Type = attr["type"]
            a.Visibility = attr["visibility"]
            a.Update()
        el.Update()
        created_elements[name] = el

    target_pkg.Elements.Refresh()

    # 4. Relaciones completas del negocio
    relationships_spec = [
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

    for rel in relationships_spec:
        src = created_elements[rel["source"]]
        tgt = created_elements[rel["target"]]

        conn = None
        for k in range(src.Connectors.Count):
            c = src.Connectors.GetAt(k)
            if c.SupplierID == tgt.ElementID and c.Type == "Association":
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

    # 5. Crear o actualizar el Diagrama
    diag_name = "DISEÑO CONCEPTUAL DE LA BASE DE DATOS (FASHIONSTORE COMPLETO)"
    diag = None
    for i in range(target_pkg.Diagrams.Count):
        d = target_pkg.Diagrams.GetAt(i)
        if d.Name == diag_name:
            diag = d
            break

    if diag is None:
        diag = target_pkg.Diagrams.AddNew(diag_name, "Class")
        diag.Update()
        target_pkg.Diagrams.Refresh()

    # Marco UML 2.5
    current_style = str(diag.StyleEx or "")
    if "ShowFrame=1;" not in current_style:
        diag.StyleEx = current_style + "ShowFrame=1;"
        diag.Update()

    # 6. Posicionar las 26 clases en el lienzo
    existing_diag_objs = {diag.DiagramObjects.GetAt(idx).ElementID: diag.DiagramObjects.GetAt(idx) for idx in range(diag.DiagramObjects.Count)}

    for name, spec in classes_data.items():
        el = created_elements[name]
        pos = spec["pos"]
        if el.ElementID in existing_diag_objs:
            d_obj = existing_diag_objs[el.ElementID]
        else:
            d_obj = diag.DiagramObjects.AddNew("", "")
            d_obj.ElementID = el.ElementID

        d_obj.left = pos["left"]
        d_obj.right = pos["right"]
        d_obj.top = pos["top"]
        d_obj.bottom = pos["bottom"]
        d_obj.Update()

    diag.Update()
    rep.SaveDiagram(diag.DiagramID)
    print("Diagrama guardado en Enterprise Architect.")

    # 7. Exportar a PNG
    Path(EXPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    rep.OpenDiagram(diag.DiagramID)
    res = project.PutDiagramImageToFile(diag.DiagramGUID, EXPORT_PATH, 1)
    print(f"Diagrama exportado a PNG: {EXPORT_PATH} (Resultado: {res})")

    rep.CloseFile()
    rep.Exit()
    print("¡Modelo completo de la base de datos generado con éxito!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
