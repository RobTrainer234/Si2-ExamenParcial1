import win32com.client
import os

def main():
    print("Iniciando creación del Modelo de Dominio (Etapa 1)...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    root_model = repo.Models.GetAt(0)

    # 1. Check or create package: Segundo Parcial - Modelo de Dominio (Etapa 1)
    target_pkg = None
    for p in root_model.Packages:
        if 'Modelo de Dominio (Etapa 1)' in p.Name:
            target_pkg = p
            break

    if target_pkg is None:
        target_pkg = root_model.Packages.AddNew("Segundo Parcial - Modelo de Dominio (Etapa 1)", "Package")
        target_pkg.Update()
        root_model.Packages.Refresh()
        print(f"Paquete creado: {target_pkg.Name} (ID={target_pkg.PackageID})")
    else:
        print(f"Usando paquete existente: {target_pkg.Name} (ID={target_pkg.PackageID})")
        # Clean previous elements and diagrams
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()

        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()

    # 2. Create Diagram: Diagrama de Clases - Modelo de Dominio (Etapa 1)
    diag = target_pkg.Diagrams.AddNew("Diagrama de Clases - Modelo de Dominio (Etapa 1)", "Logical")
    diag.Update()
    print(f"Diagrama creado: {diag.Name} (ID={diag.DiagramID})")

    # 3. Define Domain Entities and their pure Domain Attributes (No methods)
    entities_def = {
        "SubscriptionPlan": {
            "attrs": [
                ("codigo_plan", "string"),
                ("nombre_plan", "string"),
                ("precio_mensual", "decimal"),
                ("max_sucursales", "int"),
                ("max_usuarios", "int"),
                ("permite_offline", "bool"),
                ("activo", "bool")
            ],
            "coords": (50, 240, -40, -190) # Col 1, Row 1
        },
        "Subscription": {
            "attrs": [
                ("fecha_inicio", "date"),
                ("fecha_fin", "date"),
                ("estado", "string"),
                ("metodo_pago", "string"),
                ("auto_renovar", "bool")
            ],
            "coords": (290, 480, -40, -190) # Col 2, Row 1
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
            "coords": (530, 730, -40, -200) # Col 3, Row 1
        },
        "Rol": {
            "attrs": [
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ],
            "coords": (770, 950, -40, -180) # Col 4, Row 1
        },
        "Bitacora": {
            "attrs": [
                ("accion", "string"),
                ("tipo_entidad", "string"),
                ("descripcion", "string"),
                ("fecha_hora", "datetime"),
                ("ip_origen", "string")
            ],
            "coords": (290, 480, -240, -390) # Col 2, Row 2
        },
        "Usuario": {
            "attrs": [
                ("nombre_completo", "string"),
                ("email", "string"),
                ("password_hash", "string"),
                ("activo", "bool"),
                ("fecha_creacion", "datetime")
            ],
            "coords": (530, 730, -240, -400) # Col 3, Row 2
        },
        "Sucursal": {
            "attrs": [
                ("nombre", "string"),
                ("direccion", "string"),
                ("telefono", "string"),
                ("ciudad", "string"),
                ("activo", "bool")
            ],
            "coords": (770, 960, -240, -390) # Col 4, Row 2
        },
        "Categoria": {
            "attrs": [
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ],
            "coords": (50, 240, -440, -580) # Col 1, Row 3
        },
        "Producto": {
            "attrs": [
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("precio_base", "decimal"),
                ("activo", "bool")
            ],
            "coords": (290, 480, -440, -600) # Col 2, Row 3
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
            "coords": (530, 730, -440, -600) # Col 3, Row 3
        },
        "Inventario": {
            "attrs": [
                ("stock_fisico", "int"),
                ("stock_reservado", "int")
            ],
            "coords": (770, 960, -440, -580) # Col 4, Row 3
        },
        "SyncOperation": {
            "attrs": [
                ("tipo_operacion", "string"),
                ("tabla_afectada", "string"),
                ("dispositivo_id", "string"),
                ("estado_sync", "string"),
                ("fecha_sincronizacion", "datetime")
            ],
            "coords": (530, 730, -650, -800) # Col 3, Row 4
        }
    }

    # 4. Create Class Elements and add Attributes
    element_map = {}
    for ent_name, data in entities_def.items():
        el = target_pkg.Elements.AddNew(ent_name, "Class")
        el.Update()

        # Add pure domain attributes
        for attr_name, attr_type in data["attrs"]:
            attr = el.Attributes.AddNew(attr_name, attr_type)
            attr.Update()
        el.Attributes.Refresh()

        element_map[ent_name] = el

        # Add to Diagram
        l, r, t, b = data["coords"]
        d_obj = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
        d_obj.ElementID = el.ElementID
        d_obj.left = l
        d_obj.right = r
        d_obj.top = t
        d_obj.bottom = b
        d_obj.Update()

    # 5. Define Relationships (from Diagram 11 Database Model)
    # Format: (Source, Target, Name/Verb, Source_Card, Target_Card)
    relations_def = [
        ("Tenant", "Subscription", "contrata", "1", "0..*"),
        ("SubscriptionPlan", "Subscription", "define", "1", "0..*"),
        ("Tenant", "Usuario", "aloja", "1", "0..*"),
        ("Tenant", "Sucursal", "posee", "1", "0..*"),
        ("Tenant", "Categoria", "clasifica", "1", "0..*"),
        ("Tenant", "Producto", "administra", "1", "0..*"),
        ("Tenant", "SyncOperation", "registra", "1", "0..*"),
        ("Tenant", "Bitacora", "audita", "1", "0..*"),
        ("Rol", "Usuario", "tiene", "1", "0..*"),
        ("Sucursal", "Usuario", "asignado_a", "0..1", "0..*"),
        ("Usuario", "Bitacora", "registra", "1", "0..*"),
        ("Usuario", "SyncOperation", "ejecuta", "1", "0..*"),
        ("Categoria", "Producto", "clasifica", "1", "0..*"),
        ("Producto", "VarianteProducto", "compone", "1", "1..*"),
        ("VarianteProducto", "Inventario", "controla", "1", "0..*"),
        ("Sucursal", "Inventario", "almacena", "1", "0..*")
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

    # 6. Save and reload diagram
    diag.Update()
    repo.SaveDiagram(diag.DiagramID)
    repo.ReloadDiagram(diag.DiagramID)

    # Export to PNG for visual inspection
    out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6'
    img_path = os.path.join(out_dir, "modelo_dominio_etapa1.png")
    repo.GetProjectInterface().PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
    print(f"Modelo de Dominio exportado exitosamente a: {img_path}")

if __name__ == '__main__':
    main()
