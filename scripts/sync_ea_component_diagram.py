import win32com.client
import sys
import os

def main():
    print("Sincronizando Diagrama de Componentes en Enterprise Architect...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    try:
        if not repo.ConnectionString:
            repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

        root = repo.Models.GetAt(0)

        # Buscar o crear paquete
        target_pkg = None
        for p in root.Packages:
            if 'Diagrama de Componentes' in p.Name and 'Segundo Parcial' in p.Name:
                target_pkg = p
                break

        if not target_pkg:
            target_pkg = root.Packages.AddNew("Segundo Parcial - Diagrama de Componentes (Etapa 1)", "Package")
            target_pkg.Update()
            root.Packages.Refresh()

        # Limpiar previos
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()

        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()

        # Crear diagrama de tipo Component
        diag = target_pkg.Diagrams.AddNew("Diagrama de Componentes - Etapa 1", "Component")
        diag.Update()

        # Definición de componentes y posiciones
        # Coordenadas EA: (Left, Right, Top, Bottom) donde Top y Bottom son negativos
        components_def = {
            "API": {
                "name": "Servidor Backend API\n(FastAPI)",
                "type": "Component",
                "coords": (350, 570, -40, -130),
                "notes": "Servidor central FastAPI con enrutadores modulares, middleware de aislamiento tenant_id y control de cuotas por plan."
            },
            "DB": {
                "name": "Base de Datos Central\n(PostgreSQL Multi-tenant)",
                "type": "Component",
                "coords": (340, 580, -250, -360),
                "notes": "Base de datos relacional PostgreSQL con aislamiento por tenant_id e integridad referencial."
            },
            "Cliente": {
                "name": "Consola Cliente\n(Navegador Web)",
                "type": "Component",
                "coords": (50, 240, -180, -270),
                "notes": "Navegador web del usuario cliente para navegación en catálogo y consultas."
            },
            "Admin": {
                "name": "Consola Administrador\n(Superadmin & Tenant Admin)",
                "type": "Component",
                "coords": (700, 930, -180, -270),
                "notes": "Panel de administración web para gestión de empresas contratantes, suscripciones, sucursales y empleados."
            },
            "Movil": {
                "name": "Terminal Móvil Sucursal\n(App Flutter)",
                "type": "Component",
                "coords": (620, 840, -450, -540),
                "notes": "Aplicación móvil Flutter en dispositivo de vendedor con SQLite local y semáforo de conectividad."
            },
            "WebPWA": {
                "name": "Página Web / PWA\n(Angular + Service Worker)",
                "type": "Component",
                "coords": (350, 570, -450, -540),
                "notes": "Aplicación web progresiva Angular con Service Worker y almacenamiento IndexedDB para contingencia offline."
            },
            "OfflineStore": {
                "name": "Almacén Local Offline\n(SQLite / IndexedDB)",
                "type": "Component",
                "coords": (80, 290, -450, -540),
                "notes": "Motor de persistencia local desconectada en el cliente para disponibilidad del catálogo sin internet."
            }
        }

        created_elems = {}
        for k, v in components_def.items():
            elem = target_pkg.Elements.AddNew(v["name"], v["type"])
            elem.Notes = v["notes"]
            elem.Update()
            created_elems[k] = elem

            # Agregar al diagrama
            c = v["coords"]
            pos_str = f"l={c[0]};r={c[1]};t={c[2]};b={c[3]};"
            d_obj = diag.DiagramObjects.AddNew(pos_str, "")
            d_obj.ElementID = elem.ElementID
            d_obj.Update()

        # Interfaces Lollipop
        interfaces_def = {
            "I_API": {
                "name": "Servicio API REST",
                "coords": (610, 680, -70, -110),
                "parent": "API"
            },
            "I_DB": {
                "name": "Datos de Catálogo y Tenants",
                "coords": (620, 700, -280, -320),
                "parent": "DB"
            },
            "I_Admin": {
                "name": "Transacción Administrativa",
                "coords": (760, 870, -310, -350),
                "parent": "Admin"
            },
            "I_Movil": {
                "name": "Transacción Móvil Sucursal",
                "coords": (680, 780, -580, -620),
                "parent": "Movil"
            },
            "I_PWA": {
                "name": "Transacción Online / PWA",
                "coords": (410, 510, -580, -620),
                "parent": "WebPWA"
            },
            "I_Offline": {
                "name": "Consulta Catálogo Offline",
                "coords": (130, 240, -580, -620),
                "parent": "OfflineStore"
            }
        }

        created_ifaces = {}
        for k, v in interfaces_def.items():
            iface = target_pkg.Elements.AddNew(v["name"], "Interface")
            iface.Update()
            created_ifaces[k] = iface

            c = v["coords"]
            pos_str = f"l={c[0]};r={c[1]};t={c[2]};b={c[3]};"
            d_obj = diag.DiagramObjects.AddNew(pos_str, "")
            d_obj.ElementID = iface.ElementID
            d_obj.Update()

            # Conector Realization desde el componente a la interfaz
            parent_elem = created_elems[v["parent"]]
            con = parent_elem.Connectors.AddNew("", "Realization")
            con.SupplierID = iface.ElementID
            con.Update()

        # Dependencias (Dashed Arrows)
        dependencies = [
            ("Cliente", "API"),
            ("Cliente", "WebPWA"),
            ("API", "DB"),
            ("Admin", "DB"),
            ("Admin", "API"),
            ("WebPWA", "DB"),
            ("Movil", "DB"),
            ("Movil", "OfflineStore"),
            ("WebPWA", "OfflineStore")
        ]

        for src, dst in dependencies:
            src_elem = created_elems[src]
            dst_elem = created_elems[dst]
            con = src_elem.Connectors.AddNew("", "Dependency")
            con.SupplierID = dst_elem.ElementID
            con.Update()

        diag.Update()
        target_pkg.Update()
        repo.SaveDiagram(diag.DiagramID)
        print("Diagrama guardado exitosamente en Enterprise Architect!")

        # Exportar imagen desde EA
        ea_png_path = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\diagrama_componentes_etapa1_ea.png"
        project = repo.GetProjectInterface()
        project.SaveDiagramImageToFile(diag.DiagramGUID, ea_png_path, 1)
        print(f"Diagrama exportado desde EA a: {ea_png_path}")

    finally:
        del repo
        del ea
        print("Finalizado proceso EA.")

if __name__ == "__main__":
    main()
