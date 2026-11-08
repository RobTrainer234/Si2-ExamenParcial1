import win32com.client
import os

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
art_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\0c84ba0d-3a55-4d70-91ad-2a76b3c98f87'
out_dir = r'C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\db_conceptual'

print("Iniciando conexión con Enterprise Architect...")
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)
project = repo.GetProjectInterface()

# 1. Obtener paquete 02
pkg = repo.GetPackageByID(8) # '02 - Diseño Conceptual de la Base de Datos'
print(f"Paquete encontrado: {pkg.Name}")

# Verificar si el diagrama ya existe
diag_name = "DISEÑO CONCEPTUAL DE LA BASE DE DATOS (SEGUNDO PARCIAL - SAAS Y OFFLINE)"
target_diag = None
for d in pkg.Diagrams:
    if d.Name == diag_name:
        target_diag = d
        break

if target_diag is None:
    target_diag = pkg.Diagrams.AddNew(diag_name, "Class")
    target_diag.Update()
    pkg.Diagrams.Refresh()
    print("Diagrama nuevo creado.")
else:
    print("Diagrama existente encontrado.")

# 2. Definir entidades nuevas de Segundo Parcial
saas_classes = {
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
        "pos": {"left": 50, "right": 250, "top": -30, "bottom": -260}
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
        "pos": {"left": 320, "right": 520, "top": -30, "bottom": -220}
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
        "pos": {"left": 180, "right": 380, "top": -290, "bottom": -470}
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
        "pos": {"left": 50, "right": 270, "top": -530, "bottom": -770}
    }
}

elements_dict = {}

# Obtener o crear clases saas
for name, spec in saas_classes.items():
    el = None
    for item in pkg.Elements:
        if item.Name == name and item.Type == "Class":
            el = item
            break
    if el is None:
        el = pkg.Elements.AddNew(name, "Class")
        el.Update()
    
    # Atributos
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
    elements_dict[name] = el

pkg.Elements.Refresh()

# Obtener las clases existentes clave para colocarlas en el diagrama de Segundo Parcial
core_names = ["Usuario", "Rol", "Sucursal", "Ciudad", "Producto", "VarianteProducto", "Inventario", "Venta", "DetalleVenta", "Reserva", "DetalleReserva", "Pago"]
for item in pkg.Elements:
    if item.Name in core_names and item.Type == "Class":
        elements_dict[item.Name] = item

# 3. Limpiar objetos viejos del diagrama si existían
while target_diag.DiagramObjects.Count > 0:
    target_diag.DiagramObjects.Delete(0)
target_diag.DiagramObjects.Refresh()

# Disposición espacial para el diagrama de Segundo Parcial
layout = {
    # SaaS Zone (Top)
    "Tenant": (50, -40, 260, -260),
    "SubscriptionPlan": (320, -40, 520, -220),
    "Subscription": (180, -290, 390, -460),
    "SyncOperation": (50, -510, 270, -740),
    
    # Core Domain (Connected to Tenant)
    "Usuario": (480, -280, 690, -480),
    "Rol": (760, -280, 940, -400),
    "Sucursal": (480, -530, 680, -690),
    "Ciudad": (760, -530, 940, -640),
    
    "Producto": (480, -740, 690, -1000),
    "VarianteProducto": (760, -740, 980, -960),
    "Inventario": (1030, -740, 1230, -890),
    
    "Venta": (480, -1050, 690, -1310),
    "DetalleVenta": (760, -1050, 970, -1220),
    "Pago": (1030, -1050, 1240, -1290),
    "Reserva": (180, -800, 390, -1000),
    "DetalleReserva": (180, -1050, 390, -1190),
}

for name, coords in layout.items():
    if name in elements_dict:
        el = elements_dict[name]
        left, top, right, bottom = coords
        do = target_diag.DiagramObjects.AddNew(f"l={left};r={right};t={top};b={bottom};", "")
        do.ElementID = el.ElementID
        do.left = left
        do.top = top
        do.right = right
        do.bottom = bottom
        do.Update()

target_diag.DiagramObjects.Refresh()

# 4. Conectores específicos de SaaS
saas_relationships = [
    {"source": "Tenant", "target": "Subscription", "name": "contrata", "source_mult": "1", "target_mult": "1..*"},
    {"source": "SubscriptionPlan", "target": "Subscription", "name": "define", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Usuario", "name": "aloja", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Sucursal", "name": "posee", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Producto", "name": "administra", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Venta", "name": "consolida", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "Reserva", "name": "gestiona", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Tenant", "target": "SyncOperation", "name": "registra", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Usuario", "target": "SyncOperation", "name": "ejecuta", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Usuario", "target": "Rol", "name": "tiene", "source_mult": "0..*", "target_mult": "1"},
    {"source": "Usuario", "target": "Sucursal", "name": "asignado_a", "source_mult": "0..*", "target_mult": "0..1"},
    {"source": "Ciudad", "target": "Sucursal", "name": "contiene", "source_mult": "1", "target_mult": "1..*"},
    {"source": "Sucursal", "target": "Inventario", "name": "almacena", "source_mult": "1", "target_mult": "0..*"},
    {"source": "VarianteProducto", "target": "Inventario", "name": "controla", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Producto", "target": "VarianteProducto", "name": "compone", "source_mult": "1", "target_mult": "1..*"},
    {"source": "Usuario", "target": "Venta", "name": "realiza", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Sucursal", "target": "Venta", "name": "origina", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Venta", "target": "DetalleVenta", "name": "desglosa", "source_mult": "1", "target_mult": "1..*"},
    {"source": "VarianteProducto", "target": "DetalleVenta", "name": "incluye", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Venta", "target": "Pago", "name": "cancela_con", "source_mult": "1", "target_mult": "1..*"},
    {"source": "Usuario", "target": "Reserva", "name": "solicita", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Sucursal", "target": "Reserva", "name": "atiende", "source_mult": "1", "target_mult": "0..*"},
    {"source": "Reserva", "target": "DetalleReserva", "name": "contiene", "source_mult": "1", "target_mult": "1..*"},
    {"source": "VarianteProducto", "target": "DetalleReserva", "name": "aparta", "source_mult": "1", "target_mult": "0..*"},
]

for rel in saas_relationships:
    if rel["source"] in elements_dict and rel["target"] in elements_dict:
        src = elements_dict[rel["source"]]
        tgt = elements_dict[rel["target"]]
        
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

target_diag.Update()
repo.SaveDiagram(target_diag.DiagramID)
repo.ReloadDiagram(target_diag.DiagramID)

# 5. Exportar imagen del nuevo diagrama
file_sp = os.path.join(out_dir, 'diagrama_clases_bd_segundo_parcial.png')
file_sp_art = os.path.join(art_dir, 'diagrama_clases_bd_segundo_parcial.png')

project.PutDiagramImageToFile(target_diag.DiagramGUID, file_sp, 1)
project.PutDiagramImageToFile(target_diag.DiagramGUID, file_sp_art, 1)
print(f"Exportado Diagrama Segundo Parcial: {file_sp} ({os.path.getsize(file_sp)} bytes)")

repo.CloseFile()
del repo
del ea
print("¡Proceso completado con éxito!")
