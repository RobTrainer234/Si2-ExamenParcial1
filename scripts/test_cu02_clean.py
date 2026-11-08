import win32com.client
import os

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
TEST_PNG = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\test_cu02_perfect.png"

print("Connecting to EA...")
ea = win32com.client.Dispatch("EA.App")
repo = ea.Repository
repo.OpenFile(EAP_PATH)
project = repo.GetProjectInterface()

pkg = repo.GetPackageByID(193) # Segundo Parcial - Diagramas de Secuencia (Etapa 1)

# Eliminar CU-02 viejo
for i in range(pkg.Diagrams.Count):
    d = pkg.Diagrams.GetAt(i)
    if "CU-02" in d.Name:
        pkg.Diagrams.Delete(i)
        break
pkg.Diagrams.Refresh()

# Crear nuevo CU-02
diag = pkg.Diagrams.AddNew("sd CU-02 Gestionar Planes de Suscripción", "Sequence")
diag.Update()
pkg.Diagrams.Refresh()

created_elements = {}

# Lifelines
lifelines = [
    ("Superadmin SaaS", "Actor", 40, 110),
    ("V.PlanIndex", "Sequence", 160, 260),
    ("V.CrearPlan", "Sequence", 290, 390),
    ("V.EditarPlan", "Sequence", 420, 520),
    ("SubscriptionPlanController", "Sequence", 550, 670),
    ("E_SubscriptionPlan", "Sequence", 710, 830),
    ("E_Subscription", "Sequence", 860, 980),
    ("E_Tenant", "Sequence", 1010, 1130)
]

for name, typ, left, right in lifelines:
    el = pkg.Elements.AddNew(name, typ)
    el.Update()
    created_elements[name] = el
    do = diag.DiagramObjects.AddNew(f"l={left};r={right};t=-40;b=-720;", "")
    do.ElementID = el.ElementID
    do.left = left
    do.right = right
    do.top = -40
    do.bottom = -720
    do.Update()

# Fragmentos con separación limpia y sin solapamiento
# Tab sits cleanly; actor message sits in the gap above the fragment!
frags = [
    ("alt", "listar", 0, -90, -205, 150, 1140),
    ("alt", "crear", 0, -250, -365, 150, 1140),
    ("alt", "modificar", 0, -410, -525, 150, 1140),
    ("alt", "cambiarEstado", 0, -570, -685, 150, 1140)
]

for f_type, f_name, subtype_val, top, bot, left, right in frags:
    fel = pkg.Elements.AddNew(f_name, "InteractionFragment")
    fel.Subtype = subtype_val
    fel.Update()
    do = diag.DiagramObjects.AddNew(f"l={left};r={right};t={top};b={bot};", "")
    do.ElementID = fel.ElementID
    do.left = left
    do.right = right
    do.top = top
    do.bottom = bot
    do.Update()

# Mensajes en secuencia exacta
messages = [
    # Dentro de alt listar (y ≈ -110, -150, -190)
    ("Superadmin SaaS", "SubscriptionPlanController", "index()"),
    ("SubscriptionPlanController", "E_SubscriptionPlan", "get()"),
    ("E_SubscriptionPlan", "SubscriptionPlanController", "return()"),
    # En la brecha (y ≈ -230): actor invoca create
    ("Superadmin SaaS", "SubscriptionPlanController", "create()"),
    # Dentro de alt crear (y ≈ -270, -310, -350): interacciones internas
    ("SubscriptionPlanController", "V.CrearPlan", "view()"),
    ("V.CrearPlan", "SubscriptionPlanController", "store(datosPlan)"),
    ("SubscriptionPlanController", "E_SubscriptionPlan", "create(datosPlan)"),
    # En la brecha (y ≈ -390): actor invoca edit
    ("Superadmin SaaS", "SubscriptionPlanController", "edit(id)"),
    # Dentro de alt modificar (y ≈ -430, -470, -510)
    ("SubscriptionPlanController", "V.EditarPlan", "view()"),
    ("V.EditarPlan", "SubscriptionPlanController", "update(id, limites)"),
    ("SubscriptionPlanController", "E_SubscriptionPlan", "update(limites)"),
    # En la brecha (y ≈ -550): actor invoca patchEstado
    ("Superadmin SaaS", "SubscriptionPlanController", "patchEstado(id, nuevoEstado)"),
    # Dentro de alt cambiarEstado (y ≈ -590, -630, -670)
    ("SubscriptionPlanController", "E_Subscription", "get(plan_id)"),
    ("SubscriptionPlanController", "E_SubscriptionPlan", "updateEstado(id, nuevoEstado)"),
    ("SubscriptionPlanController", "V.PlanIndex", "notify(estadoActualizado)")
]

for idx, (src_name, dst_name, msg) in enumerate(messages, 1):
    src = created_elements[src_name]
    dst = created_elements[dst_name]
    con = src.Connectors.AddNew(msg, "Sequence")
    con.SupplierID = dst.ElementID
    con.SequenceNo = idx
    con.Direction = "Source -> Destination"
    con.Update()
    src.Connectors.Refresh()

    dl = diag.DiagramLinks.AddNew("", "")
    dl.ConnectorID = con.ConnectorID
    dl.Update()

diag.DiagramObjects.Refresh()
diag.DiagramLinks.Refresh()
diag.Update()
repo.SaveDiagram(diag.DiagramID)

project.PutDiagramImageToFile(diag.DiagramGUID, TEST_PNG, 1)
print(f"Exported test diagram: {TEST_PNG} ({os.path.getsize(TEST_PNG)} bytes)")

repo.CloseFile()
del repo
del ea
print("Test completed!")
