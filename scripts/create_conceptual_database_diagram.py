"""Script para crear el Diagrama de Clases 'DISEÑO CONCEPTUAL DE LA BASE DE DATOS' en Enterprise Architect (UML 2.5).

Basado fielmente en la estructura, clases, atributos, multiplicidades y disposición del modelo de referencia.
"""

import os
import sys
from pathlib import Path
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\diseno-conceptual-base-de-datos.png"

def main():
    print("Conectando con Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"Error: No se pudo abrir {MODEL_PATH}")
        return 1

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)
    print(f"Modelo raíz: {root_model.Name}")

    # 1. Obtener o crear el paquete '02 - Diseño Conceptual de la Base de Datos'
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
        print(f"Paquete creado: '{pkg_name}'")
    else:
        print(f"Paquete existente encontrado: '{pkg_name}'")

    # 2. Definición exacta de las clases y sus atributos según el modelo de referencia
    classes_data = {
        "Administrador": {
            "attributes": [
                {"name": "ci", "type": "int", "visibility": "Private"},
                {"name": "eliminado", "type": "bool", "visibility": "Private"},
                {"name": "email", "type": "string", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "imagen", "type": "string", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "password", "type": "string", "visibility": "Private"},
            ],
            "pos": {"left": 350, "right": 520, "top": -60, "bottom": -240},
        },
        "Bitacora": {
            "attributes": [
                {"name": "accion", "type": "string", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
            ],
            "pos": {"left": 640, "right": 790, "top": -90, "bottom": -190},
        },
        "Categoria": {
            "attributes": [
                {"name": "activo", "type": "bool", "visibility": "Private"},
                {"name": "descripcion", "type": "string", "visibility": "Private"},
                {"name": "eliminado", "type": "bool", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
            ],
            "pos": {"left": 60, "right": 230, "top": -260, "bottom": -420},
        },
        "Producto": {
            "attributes": [
                {"name": "activo", "type": "bool", "visibility": "Private"},
                {"name": "descripcion", "type": "string", "visibility": "Private"},
                {"name": "eliminado", "type": "bool", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "imagen", "type": "string", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "precio", "type": "float", "visibility": "Private"},
                {"name": "rank", "type": "int", "visibility": "Private"},
                {"name": "stock", "type": "int", "visibility": "Private"},
            ],
            "pos": {"left": 60, "right": 230, "top": -530, "bottom": -770},
        },
        "Descuento": {
            "attributes": [
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "porcentaje", "type": "float", "visibility": "Private"},
            ],
            "pos": {"left": 60, "right": 230, "top": -860, "bottom": -980},
        },
        "Usuario": {
            "attributes": [
                {"name": "email", "type": "string", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "imagen", "type": "string", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "password", "type": "string", "visibility": "Private"},
            ],
            "pos": {"left": 700, "right": 870, "top": -300, "bottom": -470},
        },
        "Favorito": {
            "attributes": [
                {"name": "es_favorito", "type": "bool", "visibility": "Private"},
                {"name": "puntaje", "type": "int", "visibility": "Private"},
            ],
            "pos": {"left": 310, "right": 460, "top": -430, "bottom": -530},
        },
        "Venta": {
            "attributes": [
                {"name": "created_at", "type": "datetime", "visibility": "Private"},
                {"name": "direccion", "type": "string", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "total", "type": "float", "visibility": "Private"},
            ],
            "pos": {"left": 700, "right": 870, "top": -570, "bottom": -710},
        },
        "Detalle": {
            "attributes": [
                {"name": "cantidad", "type": "int", "visibility": "Private"},
                {"name": "created_at", "type": "datetime", "visibility": "Private"},
                {"name": "precio", "type": "float", "visibility": "Private"},
                {"name": "total", "type": "float", "visibility": "Private"},
            ],
            "pos": {"left": 380, "right": 530, "top": -690, "bottom": -830},
        },
        "Pago": {
            "attributes": [
                {"name": "apellido", "type": "string", "visibility": "Private"},
                {"name": "created_at", "type": "datetime", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "total", "type": "float", "visibility": "Private"},
                {"name": "transaction_id", "type": "string", "visibility": "Private"},
            ],
            "pos": {"left": 1000, "right": 1180, "top": -490, "bottom": -680},
        },
        "MetodoPago": {
            "attributes": [
                {"name": "activo", "type": "bool", "visibility": "Private"},
                {"name": "descripcion", "type": "string", "visibility": "Private"},
                {"name": "eliminado", "type": "bool", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
            ],
            "pos": {"left": 1000, "right": 1180, "top": -740, "bottom": -900},
        },
        "EmpresaEnvio": {
            "attributes": [
                {"name": "activo", "type": "bool", "visibility": "Private"},
                {"name": "eliminado", "type": "bool", "visibility": "Private"},
                {"name": "id", "type": "int", "visibility": "Private"},
                {"name": "nombre", "type": "string", "visibility": "Private"},
                {"name": "precio", "type": "float", "visibility": "Private"},
            ],
            "pos": {"left": 700, "right": 870, "top": -810, "bottom": -970},
        },
    }

    # 3. Crear o actualizar elementos en el paquete
    created_elements = {}
    for name, spec in classes_data.items():
        # Buscar si ya existe
        el = None
        for j in range(target_pkg.Elements.Count):
            item = target_pkg.Elements.GetAt(j)
            if item.Name == name and item.Type == "Class":
                el = item
                break
        if el is None:
            el = target_pkg.Elements.AddNew(name, "Class")
            el.Update()
            print(f"  Clase creada: {name}")

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

    # 4. Definición de Relaciones, Roles y Multiplicidades
    relationships_spec = [
        {
            "source": "Administrador", "target": "Bitacora",
            "name": "tiene", "type": "Association",
            "source_mult": "1", "target_mult": "1..*",
            "direction": "Unspecified"
        },
        {
            "source": "Categoria", "target": "Producto",
            "name": "pertenece", "type": "Association",
            "source_mult": "1..*", "target_mult": "1..*",
            "direction": "Unspecified"
        },
        {
            "source": "Producto", "target": "Descuento",
            "name": "tiene", "type": "Association",
            "source_mult": "1..*", "target_mult": "1",
            "direction": "Unspecified"
        },
        {
            "source": "Usuario", "target": "Producto",
            "name": "tiene", "type": "Association",
            "source_mult": "0..*", "target_mult": "0..*",
            "direction": "Unspecified"
        },
        {
            "source": "Favorito", "target": "Producto",
            "name": "", "type": "Dependency",
            "source_mult": "", "target_mult": "",
            "direction": "Unspecified"
        },
        {
            "source": "Usuario", "target": "Venta",
            "name": "realiza", "type": "Association",
            "source_mult": "1", "target_mult": "1..*",
            "direction": "Unspecified"
        },
        {
            "source": "Producto", "target": "Venta",
            "name": "genera", "type": "Association",
            "source_mult": "1..*", "target_mult": "1..*",
            "direction": "Unspecified"
        },
        {
            "source": "Detalle", "target": "Venta",
            "name": "", "type": "Dependency",
            "source_mult": "", "target_mult": "",
            "direction": "Unspecified"
        },
        {
            "source": "Venta", "target": "Pago",
            "name": "genera", "type": "Association",
            "source_mult": "1", "target_mult": "1",
            "direction": "Unspecified"
        },
        {
            "source": "Venta", "target": "MetodoPago",
            "name": "utiliza", "type": "Association",
            "source_mult": "1..*", "target_mult": "1",
            "direction": "Unspecified"
        },
        {
            "source": "Venta", "target": "EmpresaEnvio",
            "name": "utiliza", "type": "Association",
            "source_mult": "1..*", "target_mult": "1",
            "direction": "Unspecified"
        },
    ]

    for rel in relationships_spec:
        src = created_elements[rel["source"]]
        tgt = created_elements[rel["target"]]

        # Verificar si el conector ya existe
        conn = None
        for k in range(src.Connectors.Count):
            c = src.Connectors.GetAt(k)
            if c.SupplierID == tgt.ElementID and c.Type == rel["type"]:
                conn = c
                break

        if conn is None:
            conn = src.Connectors.AddNew(rel["name"], rel["type"])
            conn.SupplierID = tgt.ElementID

        conn.Name = rel["name"]
        conn.Direction = rel["direction"]
        if rel["source_mult"]:
            conn.ClientEnd.Cardinality = rel["source_mult"]
            conn.ClientEnd.Update()
        if rel["target_mult"]:
            conn.SupplierEnd.Cardinality = rel["target_mult"]
            conn.SupplierEnd.Update()
        conn.Update()
        src.Connectors.Refresh()

    # 5. Crear o actualizar el Diagrama de Clases
    diag_name = "DISEÑO CONCEPTUAL DE LA BASE DE DATOS"
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
        print(f"Diagrama creado: '{diag_name}'")
    else:
        print(f"Diagrama existente encontrado: '{diag_name}'")

    # Configuración UML 2.5: Activar Diagram Frame
    # En EA, StyleEx con ShowFrame=1 activa el marco pentagonal UML 2.5
    current_style = str(diag.StyleEx or "")
    if "ShowFrame=1;" not in current_style:
        diag.StyleEx = current_style + "ShowFrame=1;"
        diag.Update()

    # 6. Posicionar los objetos en el lienzo
    # Mapeo de IDs existentes en el diagrama
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

    # 7. Exportar imagen a PNG para visualización directa
    Path(EXPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    rep.OpenDiagram(diag.DiagramID)
    res = project.PutDiagramImageToFile(diag.DiagramGUID, EXPORT_PATH, 1)
    print(f"Diagrama exportado a PNG: {EXPORT_PATH} (Resultado: {res})")

    rep.CloseFile()
    rep.Exit()
    print("¡Proceso completado exitosamente!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
