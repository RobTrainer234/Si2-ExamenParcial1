"""Script para poblar y exportar todos los diagramas UML en Enterprise Architect (FashionStore.eap)."""

import os
import sys
from pathlib import Path
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

def get_or_create_package(parent_pkg, name):
    for i in range(parent_pkg.Packages.Count):
        p = parent_pkg.Packages.GetAt(i)
        if p.Name == name:
            return p
    new_pkg = parent_pkg.Packages.AddNew(name, "")
    new_pkg.Update()
    parent_pkg.Packages.Refresh()
    return new_pkg

def get_or_create_element(pkg, name, elem_type, stereotype=""):
    for i in range(pkg.Elements.Count):
        el = pkg.Elements.GetAt(i)
        if el.Name == name and el.Type == elem_type:
            return el
    el = pkg.Elements.AddNew(name, elem_type)
    if stereotype:
        el.Stereotype = stereotype
    el.Update()
    pkg.Elements.Refresh()
    return el

def create_connector(source, target, conn_type, name="", stereotype="", direction="Unspecified"):
    # Check if connector already exists
    for i in range(source.Connectors.Count):
        c = source.Connectors.GetAt(i)
        if c.SupplierID == target.ElementID and c.Type == conn_type and c.Name == name:
            return c
    c = source.Connectors.AddNew(name, conn_type)
    c.SupplierID = target.ElementID
    if stereotype:
        c.Stereotype = stereotype
    c.Direction = direction
    c.Update()
    source.Connectors.Refresh()
    return c

def create_use_case_diagram(pkg, diag_name, actors_spec, ucs_spec, rels_spec):
    # Check if diagram exists
    diag = None
    for i in range(pkg.Diagrams.Count):
        d = pkg.Diagrams.GetAt(i)
        if d.Name == diag_name:
            diag = d
            break
    if diag is None:
        diag = pkg.Diagrams.AddNew(diag_name, "Use Case")
        diag.Update()
        pkg.Diagrams.Refresh()

    actor_elems = {}
    for a in actors_spec:
        el = get_or_create_element(pkg, a["name"], "Actor", a.get("stereotype", ""))
        actor_elems[a["name"]] = el

    uc_elems = {}
    for uc in ucs_spec:
        el = get_or_create_element(pkg, uc["name"], "UseCase", uc.get("stereotype", ""))
        uc_elems[uc["name"]] = el

    all_elems = {**actor_elems, **uc_elems}

    for rel in rels_spec:
        src = all_elems.get(rel["source"])
        tgt = all_elems.get(rel["target"])
        if src and tgt:
            create_connector(src, tgt, rel.get("type", "Association"), rel.get("name", ""), rel.get("stereotype", ""))

    # Position on diagram
    # Actors on the left
    for idx, (name, el) in enumerate(actor_elems.items()):
        left = 40
        top = -(40 + idx * 120)
        obj = diag.DiagramObjects.AddNew("", "")
        obj.ElementID = el.ElementID
        obj.left = left
        obj.right = left + 80
        obj.top = top
        obj.bottom = top - 80
        obj.Update()

    # UCs in columns
    for idx, (name, el) in enumerate(uc_elems.items()):
        col = idx // 5
        row = idx % 5
        left = 220 + col * 260
        top = -(40 + row * 110)
        obj = diag.DiagramObjects.AddNew("", "")
        obj.ElementID = el.ElementID
        obj.left = left
        obj.right = left + 200
        obj.top = top
        obj.bottom = top - 70
        obj.Update()

    diag.Update()
    return diag

def create_class_diagram(pkg, diag_name, classes_spec, rels_spec):
    diag = None
    for i in range(pkg.Diagrams.Count):
        d = pkg.Diagrams.GetAt(i)
        if d.Name == diag_name:
            diag = d
            break
    if diag is None:
        diag = pkg.Diagrams.AddNew(diag_name, "Class")
        diag.Update()
        pkg.Diagrams.Refresh()

    class_elems = {}
    for spec in classes_spec:
        el = get_or_create_element(pkg, spec["name"], "Class")
        # Add attributes
        existing_attrs = {el.Attributes.GetAt(i).Name for i in range(el.Attributes.Count)}
        for attr in spec.get("attributes", []):
            if attr["name"] not in existing_attrs:
                a = el.Attributes.AddNew(attr["name"], attr.get("type", "string"))
                a.Visibility = attr.get("visibility", "Public")
                a.Update()
        # Add methods
        existing_methods = {el.Methods.GetAt(i).Name for i in range(el.Methods.Count)}
        for meth in spec.get("methods", []):
            if meth["name"] not in existing_methods:
                m = el.Methods.AddNew(meth["name"], meth.get("return_type", "void"))
                m.Visibility = meth.get("visibility", "Public")
                m.Update()
        el.Update()
        class_elems[spec["name"]] = el

    for rel in rels_spec:
        src = class_elems.get(rel["source"])
        tgt = class_elems.get(rel["target"])
        if src and tgt:
            create_connector(src, tgt, rel.get("type", "Association"), rel.get("name", ""))

    # Position in grid 4 columns
    for idx, (name, el) in enumerate(class_elems.items()):
        col = idx % 4
        row = idx // 4
        left = 40 + col * 260
        top = -(40 + row * 220)
        obj = diag.DiagramObjects.AddNew("", "")
        obj.ElementID = el.ElementID
        obj.left = left
        obj.right = left + 220
        obj.top = top
        obj.bottom = top - 180
        obj.Update()

    diag.Update()
    return diag

def create_sequence_diagram(pkg, diag_name, participants_spec, messages_spec):
    diag = None
    for i in range(pkg.Diagrams.Count):
        d = pkg.Diagrams.GetAt(i)
        if d.Name == diag_name:
            diag = d
            break
    if diag is None:
        diag = pkg.Diagrams.AddNew(diag_name, "Sequence")
        diag.Update()
        pkg.Diagrams.Refresh()

    part_elems = {}
    for p in participants_spec:
        el = get_or_create_element(pkg, p["name"], "Object", p.get("stereotype", ""))
        part_elems[p["name"]] = el

    for idx, msg in enumerate(messages_spec, start=1):
        src = part_elems.get(msg["source"])
        tgt = part_elems.get(msg["target"])
        if src and tgt:
            c = src.Connectors.AddNew(msg["message"], "Sequence")
            c.SupplierID = tgt.ElementID
            c.SequenceNo = str(idx)
            c.Direction = "Source -> Destination"
            c.Update()

    # Position lifelines horizontally
    for idx, (name, el) in enumerate(part_elems.items()):
        left = 40 + idx * 180
        top = -40
        obj = diag.DiagramObjects.AddNew("", "")
        obj.ElementID = el.ElementID
        obj.left = left
        obj.right = left + 140
        obj.top = top
        obj.bottom = top - 80
        obj.Update()

    diag.Update()
    return diag

def create_component_or_deployment_diagram(pkg, diag_name, diag_type, nodes_spec, rels_spec, default_type):
    diag = None
    for i in range(pkg.Diagrams.Count):
        d = pkg.Diagrams.GetAt(i)
        if d.Name == diag_name:
            diag = d
            break
    if diag is None:
        diag = pkg.Diagrams.AddNew(diag_name, diag_type)
        diag.Update()
        pkg.Diagrams.Refresh()

    elems = {}
    for n in nodes_spec:
        el = get_or_create_element(pkg, n["name"], n.get("type", default_type), n.get("stereotype", ""))
        elems[n["name"]] = el

    for rel in rels_spec:
        src = elems.get(rel["source"])
        tgt = elems.get(rel["target"])
        if src and tgt:
            create_connector(src, tgt, rel.get("type", "Dependency"), rel.get("name", ""))

    for idx, (name, el) in enumerate(elems.items()):
        col = idx % 3
        row = idx // 3
        left = 40 + col * 260
        top = -(40 + row * 160)
        obj = diag.DiagramObjects.AddNew("", "")
        obj.ElementID = el.ElementID
        obj.left = left
        obj.right = left + 210
        obj.top = top
        obj.bottom = top - 110
        obj.Update()

    diag.Update()
    return diag

def export_all_diagrams(rep, project, root_pkg):
    exported = []
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    
    def process_package(pkg):
        for i in range(pkg.Diagrams.Count):
            diag = pkg.Diagrams.GetAt(i)
            safe_name = diag.Name.lower().replace(" ", "-").replace("—", "-").replace(":", "").replace("/", "-")
            out_file = os.path.join(EXPORT_DIR, f"{safe_name}.png")
            rep.OpenDiagram(diag.DiagramID)
            rep.SaveDiagram(diag.DiagramID)
            res = project.PutDiagramImageToFile(diag.DiagramGUID, out_file, 1)
            exported.append((diag.Name, out_file, res))
        for j in range(pkg.Packages.Count):
            process_package(pkg.Packages.GetAt(j))

    process_package(root_pkg)
    return exported

def main():
    print("Iniciando conexión con Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print("ERROR: No se pudo abrir el archivo .eap.")
        return 1

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)
    print(f"Modelo raíz abierto: {root_model.Name}")

    # 1. Ciclo 2 - Casos de Uso
    pkg_c2 = get_or_create_package(root_model, "Ciclo 2 - Operación Comercial")
    actors_c2 = [
        {"name": "Cliente"},
        {"name": "Cajero"},
        {"name": "Encargado de Sucursal"},
        {"name": "Pasarela de Pagos", "stereotype": "External"}
    ]
    ucs_c2 = [
        {"name": "CU10 Realizar Reserva de Prendas"},
        {"name": "CU11 Atender Reserva en Tienda"},
        {"name": "CU13 Gestionar Carrito"},
        {"name": "CU14 Realizar Compra Digital"},
        {"name": "CU15 Realizar Venta Presencial POS"},
        {"name": "CU16 Cobro en Caja"},
        {"name": "CU17 Procesar Pago Electrónico"},
        {"name": "CU18 Control de Stock y Movimientos"},
        {"name": "CU19 Gestionar Temporadas y Colecciones"}
    ]
    rels_c2 = [
        {"source": "Cliente", "target": "CU10 Realizar Reserva de Prendas"},
        {"source": "Cliente", "target": "CU13 Gestionar Carrito"},
        {"source": "Cliente", "target": "CU14 Realizar Compra Digital"},
        {"source": "Encargado de Sucursal", "target": "CU11 Atender Reserva en Tienda"},
        {"source": "Encargado de Sucursal", "target": "CU18 Control de Stock y Movimientos"},
        {"source": "Cajero", "target": "CU15 Realizar Venta Presencial POS"},
        {"source": "Cajero", "target": "CU16 Cobro en Caja"},
        {"source": "CU14 Realizar Compra Digital", "target": "CU17 Procesar Pago Electrónico", "type": "Dependency", "name": "<<include>>"},
        {"source": "CU15 Realizar Venta Presencial POS", "target": "CU16 Cobro en Caja", "type": "Dependency", "name": "<<include>>"},
        {"source": "Pasarela de Pagos", "target": "CU17 Procesar Pago Electrónico"}
    ]
    create_use_case_diagram(pkg_c2, "Ciclo 2 - Casos de Uso", actors_c2, ucs_c2, rels_c2)
    print("Ciclo 2 - Casos de Uso creado.")

    # 2. Ciclo 3 - Casos de Uso
    pkg_c3 = get_or_create_package(root_model, "Ciclo 3 - Innovación y Analítica")
    actors_c3 = [
        {"name": "Cliente"},
        {"name": "Administrador"},
        {"name": "Motor IA", "stereotype": "External"}
    ]
    ucs_c3 = [
        {"name": "CU12 Sesión Probador Virtual"},
        {"name": "CU20 Gestionar Promociones"},
        {"name": "CU21 Dashboards y Reportes"},
        {"name": "CU22 Obtener Recomendaciones IA"},
        {"name": "CU23 Consultar Historial Compras"}
    ]
    rels_c3 = [
        {"source": "Cliente", "target": "CU12 Sesión Probador Virtual"},
        {"source": "Cliente", "target": "CU22 Obtener Recomendaciones IA"},
        {"source": "Cliente", "target": "CU23 Consultar Historial Compras"},
        {"source": "Motor IA", "target": "CU22 Obtener Recomendaciones IA"},
        {"source": "Administrador", "target": "CU20 Gestionar Promociones"},
        {"source": "Administrador", "target": "CU21 Dashboards y Reportes"}
    ]
    create_use_case_diagram(pkg_c3, "Ciclo 3 - Casos de Uso", actors_c3, ucs_c3, rels_c3)
    print("Ciclo 3 - Casos de Uso creado.")

    # 3. Modelo de Dominio - Clases
    pkg_dom = get_or_create_package(root_model, "Modelo de Dominio")
    classes_spec = [
        {"name": "User", "attributes": [{"name": "id", "type": "int"}, {"name": "email", "type": "string"}, {"name": "role_id", "type": "int"}], "methods": [{"name": "verify_password", "return_type": "bool"}]},
        {"name": "Role", "attributes": [{"name": "id", "type": "int"}, {"name": "code", "type": "string"}, {"name": "name", "type": "string"}]},
        {"name": "City", "attributes": [{"name": "id", "type": "int"}, {"name": "name", "type": "string"}]},
        {"name": "Branch", "attributes": [{"name": "id", "type": "int"}, {"name": "name", "type": "string"}, {"name": "city_id", "type": "int"}]},
        {"name": "Category", "attributes": [{"name": "id", "type": "int"}, {"name": "name", "type": "string"}]},
        {"name": "Product", "attributes": [{"name": "id", "type": "int"}, {"name": "code", "type": "string"}, {"name": "price", "type": "decimal"}]},
        {"name": "ProductVariant", "attributes": [{"name": "id", "type": "int"}, {"name": "sku", "type": "string"}, {"name": "product_id", "type": "int"}]},
        {"name": "Inventory", "attributes": [{"name": "id", "type": "int"}, {"name": "stock_quantity", "type": "int"}, {"name": "reserved_quantity", "type": "int"}], "methods": [{"name": "get_available_stock", "return_type": "int"}]},
        {"name": "InventoryMovement", "attributes": [{"name": "id", "type": "int"}, {"name": "movement_type", "type": "string"}, {"name": "quantity", "type": "int"}]},
        {"name": "Cart", "attributes": [{"name": "id", "type": "int"}, {"name": "customer_id", "type": "int"}]},
        {"name": "CartItem", "attributes": [{"name": "id", "type": "int"}, {"name": "quantity", "type": "int"}, {"name": "unit_price", "type": "decimal"}]},
        {"name": "Reservation", "attributes": [{"name": "id", "type": "int"}, {"name": "reservation_code", "type": "string"}, {"name": "status", "type": "string"}], "methods": [{"name": "confirm", "return_type": "void"}, {"name": "cancel", "return_type": "void"}]},
        {"name": "ReservationItem", "attributes": [{"name": "id", "type": "int"}, {"name": "quantity", "type": "int"}, {"name": "unit_price", "type": "decimal"}]},
        {"name": "Sale", "attributes": [{"name": "id", "type": "int"}, {"name": "channel", "type": "string"}, {"name": "total", "type": "decimal"}, {"name": "status", "type": "string"}]},
        {"name": "SaleItem", "attributes": [{"name": "id", "type": "int"}, {"name": "quantity", "type": "int"}, {"name": "line_total", "type": "decimal"}]},
        {"name": "Payment", "attributes": [{"name": "id", "type": "int"}, {"name": "method", "type": "string"}, {"name": "amount", "type": "decimal"}, {"name": "status", "type": "string"}]},
        {"name": "Bitacora", "attributes": [{"name": "id", "type": "int"}, {"name": "accion", "type": "string"}, {"name": "tipo_entidad", "type": "string"}]}
    ]
    rels_dom = [
        {"source": "User", "target": "Role"},
        {"source": "City", "target": "Branch"},
        {"source": "Category", "target": "Product"},
        {"source": "Product", "target": "ProductVariant"},
        {"source": "Branch", "target": "Inventory"},
        {"source": "ProductVariant", "target": "Inventory"},
        {"source": "Inventory", "target": "InventoryMovement"},
        {"source": "Cart", "target": "CartItem"},
        {"source": "ProductVariant", "target": "CartItem"},
        {"source": "Reservation", "target": "ReservationItem"},
        {"source": "ProductVariant", "target": "ReservationItem"},
        {"source": "Sale", "target": "SaleItem"},
        {"source": "ProductVariant", "target": "SaleItem"},
        {"source": "Sale", "target": "Payment"},
        {"source": "User", "target": "Reservation"},
        {"source": "User", "target": "Sale"}
    ]
    create_class_diagram(pkg_dom, "Diagrama de Clases - Modelo de Dominio", classes_spec, rels_dom)
    print("Modelo de Dominio creado.")

    # 4. Diagramas de Secuencia
    pkg_seq = get_or_create_package(root_model, "Diagramas de Secuencia")
    
    # Secuencia CU10
    parts_cu10 = [
        {"name": "Cliente", "stereotype": "actor"},
        {"name": "Web/Mobile UI"},
        {"name": "ReservationRouter"},
        {"name": "ReservationService"},
        {"name": "InventoryService"},
        {"name": "PostgreSQL"}
    ]
    msgs_cu10 = [
        {"source": "Cliente", "target": "Web/Mobile UI", "message": "1: Seleccionar prendas y sucursal"},
        {"source": "Web/Mobile UI", "target": "ReservationRouter", "message": "2: POST /api/v1/reservations"},
        {"source": "ReservationRouter", "target": "ReservationService", "message": "3: create_reservation()"},
        {"source": "ReservationService", "target": "InventoryService", "message": "4: validate_and_lock_stock()"},
        {"source": "InventoryService", "target": "PostgreSQL", "message": "5: UPDATE reserved_quantity"},
        {"source": "ReservationService", "target": "PostgreSQL", "message": "6: INSERT INTO reservas"},
        {"source": "ReservationService", "target": "ReservationRouter", "message": "7: 201 Created"},
        {"source": "ReservationRouter", "target": "Web/Mobile UI", "message": "8: Mostrar Código FS-XXXX"},
        {"source": "Web/Mobile UI", "target": "Cliente", "message": "9: Confirmación en pantalla"}
    ]
    create_sequence_diagram(pkg_seq, "Secuencia CU10 - Reserva de Prendas", parts_cu10, msgs_cu10)
    print("Secuencia CU10 creada.")

    # Secuencia CU14/17
    parts_cu14 = [
        {"name": "Cliente", "stereotype": "actor"},
        {"name": "Web/Mobile App"},
        {"name": "CommerceRouter"},
        {"name": "CommerceService"},
        {"name": "PaymentGateway"},
        {"name": "InventoryService"},
        {"name": "PostgreSQL"}
    ]
    msgs_cu14 = [
        {"source": "Cliente", "target": "Web/Mobile App", "message": "1: Checkout digital"},
        {"source": "Web/Mobile App", "target": "CommerceRouter", "message": "2: POST /purchases/digital"},
        {"source": "CommerceRouter", "target": "CommerceService", "message": "3: create_digital_purchase()"},
        {"source": "CommerceService", "target": "PostgreSQL", "message": "4: INSERT venta (PENDING)"},
        {"source": "Web/Mobile App", "target": "CommerceRouter", "message": "5: POST /payments/electronic"},
        {"source": "CommerceRouter", "target": "CommerceService", "message": "6: process_payment()"},
        {"source": "CommerceService", "target": "PaymentGateway", "message": "7: Authorize charge"},
        {"source": "PaymentGateway", "target": "CommerceService", "message": "8: 200 Approved"},
        {"source": "CommerceService", "target": "InventoryService", "message": "9: deduct_inventory()"},
        {"source": "InventoryService", "target": "PostgreSQL", "message": "10: UPDATE stock_quantity"},
        {"source": "CommerceService", "target": "PostgreSQL", "message": "11: UPDATE venta (COMPLETED)"}
    ]
    create_sequence_diagram(pkg_seq, "Secuencia CU14 - Compra Digital con Pago Sandbox", parts_cu14, msgs_cu14)
    print("Secuencia CU14 creada.")

    # 5. Componentes y Despliegue
    pkg_arch = get_or_create_package(root_model, "Arquitectura del Sistema")
    comp_nodes = [
        {"name": "Angular Web SPA", "type": "Component"},
        {"name": "Flutter Mobile App", "type": "Component"},
        {"name": "FastAPI Modular Backend", "type": "Component"},
        {"name": "PostgreSQL 17 Database", "type": "Component"},
        {"name": "AI Recommendation Engine", "type": "Component"},
        {"name": "Sandbox Payment Gateway", "type": "Component"}
    ]
    comp_rels = [
        {"source": "Angular Web SPA", "target": "FastAPI Modular Backend", "type": "Dependency"},
        {"source": "Flutter Mobile App", "target": "FastAPI Modular Backend", "type": "Dependency"},
        {"source": "FastAPI Modular Backend", "target": "PostgreSQL 17 Database", "type": "Dependency"},
        {"source": "FastAPI Modular Backend", "target": "AI Recommendation Engine", "type": "Dependency"},
        {"source": "FastAPI Modular Backend", "target": "Sandbox Payment Gateway", "type": "Dependency"}
    ]
    create_component_or_deployment_diagram(pkg_arch, "Diagrama de Componentes", "Component", comp_nodes, comp_rels, "Component")
    print("Diagrama de Componentes creado.")

    deploy_nodes = [
        {"name": "Servidor Docker Host", "type": "Node"},
        {"name": "Contenedor Web (Nginx)", "type": "Node"},
        {"name": "Contenedor Backend (FastAPI)", "type": "Node"},
        {"name": "Contenedor DB (Postgres 17)", "type": "Node"},
        {"name": "Dispositivo Android (Flutter)", "type": "Node"},
        {"name": "Navegador Web (PC)", "type": "Node"}
    ]
    deploy_rels = [
        {"source": "Navegador Web (PC)", "target": "Contenedor Web (Nginx)", "type": "Dependency"},
        {"source": "Contenedor Web (Nginx)", "target": "Contenedor Backend (FastAPI)", "type": "Dependency"},
        {"source": "Dispositivo Android (Flutter)", "target": "Contenedor Backend (FastAPI)", "type": "Dependency"},
        {"source": "Contenedor Backend (FastAPI)", "target": "Contenedor DB (Postgres 17)", "type": "Dependency"}
    ]
    create_component_or_deployment_diagram(pkg_arch, "Diagrama de Despliegue", "Deployment", deploy_nodes, deploy_rels, "Node")
    print("Diagrama de Despliegue creado.")

    # Guardar cambios y exportar todo
    print("Exportando diagramas a PNG...")
    exported = export_all_diagrams(rep, project, root_model)
    for name, path, ok in exported:
        print(f"  [OK: {ok}] {name} -> {path}")

    rep.CloseFile()
    rep.Exit()
    print("Finalizado con éxito.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
