import win32com.client
import os

def main():
    print("Optimizando layout del Modelo de Dominio (Etapa 1)...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    root_model = repo.Models.GetAt(0)
    target_pkg = None
    for p in root_model.Packages:
        if 'Modelo de Dominio (Etapa 1)' in p.Name:
            target_pkg = p
            break

    if target_pkg is None:
        target_pkg = root_model.Packages.AddNew("Segundo Parcial - Modelo de Dominio (Etapa 1)", "Package")
        target_pkg.Update()
        root_model.Packages.Refresh()

    # Clear previous elements and diagrams
    for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
        target_pkg.Diagrams.Delete(i)
    target_pkg.Diagrams.Refresh()

    for i in range(target_pkg.Elements.Count - 1, -1, -1):
        target_pkg.Elements.Delete(i)
    target_pkg.Elements.Refresh()

    diag = target_pkg.Diagrams.AddNew("Diagrama de Clases - Modelo de Dominio (Etapa 1)", "Logical")
    diag.Update()

    # Grid parameters
    # Col 1: 50..250
    # Col 2: 300..500
    # Col 3: 550..750
    # Col 4: 800..1000
    # Row 1: -40..-200
    # Row 2: -270..-430
    # Row 3: -500..-660

    entities_layout = {
        # ROW 1 (SaaS y Suscripciones)
        "SubscriptionPlan": {
            "coords": (50, 250, -40, -210),
            "attrs": [
                ("codigo_plan", "string"),
                ("nombre_plan", "string"),
                ("precio_mensual", "decimal"),
                ("max_sucursales", "int"),
                ("max_usuarios", "int"),
                ("permite_offline", "bool"),
                ("activo", "bool")
            ]
        },
        "Subscription": {
            "coords": (300, 500, -40, -190),
            "attrs": [
                ("fecha_inicio", "date"),
                ("fecha_fin", "date"),
                ("estado", "string"),
                ("metodo_pago", "string"),
                ("auto_renovar", "bool")
            ]
        },
        "Tenant": {
            "coords": (550, 750, -40, -210),
            "attrs": [
                ("codigo_tenant", "string"),
                ("nombre_empresa", "string"),
                ("nit_ruc", "string"),
                ("subdominio", "string"),
                ("estado", "string"),
                ("fecha_registro", "datetime")
            ]
        },
        "Bitacora": {
            "coords": (800, 1000, -40, -190),
            "attrs": [
                ("accion", "string"),
                ("tipo_entidad", "string"),
                ("descripcion", "string"),
                ("fecha_hora", "datetime"),
                ("ip_origen", "string")
            ]
        },

        # ROW 2 (Organización, Personal y Logística)
        "Rol": {
            "coords": (50, 250, -270, -410),
            "attrs": [
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ]
        },
        "Usuario": {
            "coords": (300, 500, -270, -430),
            "attrs": [
                ("nombre_completo", "string"),
                ("email", "string"),
                ("password_hash", "string"),
                ("activo", "bool"),
                ("fecha_creacion", "datetime")
            ]
        },
        "Sucursal": {
            "coords": (550, 750, -270, -430),
            "attrs": [
                ("nombre", "string"),
                ("direccion", "string"),
                ("telefono", "string"),
                ("ciudad", "string"),
                ("activo", "bool")
            ]
        },
        "Inventario": {
            "coords": (800, 1000, -270, -410),
            "attrs": [
                ("stock_fisico", "int"),
                ("stock_reservado", "int"),
                ("stock_disponible", "int")
            ]
        },

        # ROW 3 (Catálogo, Producto y Offline)
        "SyncOperation": {
            "coords": (50, 250, -500, -650),
            "attrs": [
                ("tipo_operacion", "string"),
                ("tabla_afectada", "string"),
                ("dispositivo_id", "string"),
                ("estado_sync", "string"),
                ("fecha_sincronizacion", "datetime")
            ]
        },
        "Categoria": {
            "coords": (300, 500, -500, -640),
            "attrs": [
                ("nombre", "string"),
                ("descripcion", "string"),
                ("activo", "bool")
            ]
        },
        "Producto": {
            "coords": (550, 750, -500, -660),
            "attrs": [
                ("codigo", "string"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("precio_base", "decimal"),
                ("activo", "bool")
            ]
        },
        "VarianteProducto": {
            "coords": (800, 1000, -500, -660),
            "attrs": [
                ("codigo_barra", "string"),
                ("sku", "string"),
                ("talla", "string"),
                ("color", "string"),
                ("precio_adicional", "decimal"),
                ("activo", "bool")
            ]
        }
    }

    element_map = {}
    for name, data in entities_layout.items():
        el = target_pkg.Elements.AddNew(name, "Class")
        el.Update()

        for a_name, a_type in data["attrs"]:
            attr = el.Attributes.AddNew(a_name, a_type)
            attr.Update()
        el.Attributes.Refresh()

        element_map[name] = el

        l, r, t, b = data["coords"]
        d_obj = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
        d_obj.ElementID = el.ElementID
        d_obj.left = l
        d_obj.right = r
        d_obj.top = t
        d_obj.bottom = b
        d_obj.Update()

    # Define clean domain associations
    associations = [
        # SaaS Row 1
        ("SubscriptionPlan", "Subscription", "define", "1", "0..*"),
        ("Tenant", "Subscription", "contrata", "1", "0..*"),
        ("Tenant", "Bitacora", "audita", "1", "0..*"),

        # Row 1 to Row 2
        ("Tenant", "Sucursal", "posee", "1", "0..*"),
        ("Tenant", "Usuario", "aloja", "1", "0..*"),

        # Row 2 (Organization & Staff)
        ("Rol", "Usuario", "tiene", "1", "0..*"),
        ("Sucursal", "Usuario", "asignado_a", "0..1", "0..*"),
        ("Sucursal", "Inventario", "almacena", "1", "0..*"),
        ("Usuario", "Bitacora", "registra", "1", "0..*"),
        ("Usuario", "SyncOperation", "ejecuta", "1", "0..*"),

        # Catalog Row 3 & Inventory link
        ("Categoria", "Producto", "clasifica", "1", "0..*"),
        ("Producto", "VarianteProducto", "compone", "1", "1..*"),
        ("VarianteProducto", "Inventario", "controla", "1", "0..*")
    ]

    for src_name, dst_name, verb, src_card, dst_card in associations:
        src_el = element_map[src_name]
        dst_el = element_map[dst_name]

        conn = src_el.Connectors.AddNew(verb, "Association")
        conn.SupplierID = dst_el.ElementID
        conn.Direction = "Source -> Destination"
        conn.ClientEnd.Cardinality = src_card
        conn.SupplierEnd.Cardinality = dst_card
        conn.Update()

    diag.Update()
    repo.SaveDiagram(diag.DiagramID)
    repo.ReloadDiagram(diag.DiagramID)

    out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6'
    img_path = os.path.join(out_dir, "modelo_dominio_etapa1_clean.png")
    repo.GetProjectInterface().PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
    print(f"Diagrama de Modelo de Dominio limpio exportado a: {img_path}")

if __name__ == '__main__':
    main()
