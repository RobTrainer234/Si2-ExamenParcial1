import win32com.client
import os

def main():
    print("Creando Diagrama de Estructura en Capas UML 2.5 optimizado...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    try:
        if not repo.ConnectionString:
            repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

        root_model = repo.Models.GetAt(0)

        # Buscar o crear el paquete para la Arquitectura del Segundo Parcial
        target_pkg = None
        for p in root_model.Packages:
            if 'Arquitectura del Sistema (Capas UML 2.5)' in p.Name:
                target_pkg = p
                break

        if target_pkg is None:
            target_pkg = root_model.Packages.AddNew("Segundo Parcial - Arquitectura del Sistema (Capas UML 2.5)", "Package")
            target_pkg.Update()
            root_model.Packages.Refresh()

        # Limpiar elementos y diagramas previos del paquete
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()

        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()

        # Crear el diagrama de paquetes
        diag = target_pkg.Diagrams.AddNew("Diagrama de Estructura en Capas (UML 2.5) - Etapa 1", "Package")
        diag.Update()

        # Definición de paquetes por capas (UML 2.5)
        # 3 Columnas:
        # Col 1: 50 .. 330 (Ancho 280) -> Módulo SaaS & Suscripciones (CU-01 a CU-04)
        # Col 2: 380 .. 660 (Ancho 280) -> Módulo Sucursales & Usuarios (CU-05)
        # Col 3: 710 .. 990 (Ancho 280) -> Módulo Catálogo, Stock & Offline (CU-06, CU-07, CU-23..CU-25)
        #
        # 4 Filas (Capas):
        # Fila 1 (Presentación): Top -40, Bottom -160 (Alto 120)
        # Fila 2 (Controladores/Aplicación): Top -230, Bottom -350 (Alto 120)
        # Fila 3 (Dominio/Modelos): Top -420, Bottom -540 (Alto 120)
        # Fila 4 (Persistencia/BD): Top -610, Bottom -730 (Alto 120)

        packages_def = {
            # CAPA 1: PRESENTACIÓN (VISTAS)
            "Vista_SaaS": {
                "name": "Paquete Vistas Gestión SaaS y Planes",
                "stereotype": "layer",
                "coords": (50, 330, -40, -160),
                "notes": "Capa de Presentación: Vistas Angular Web para registro de empresas contratantes, administración de planes de suscripción y monitoreo de límites."
            },
            "Vista_Sucursales": {
                "name": "Paquete Vistas Sucursales y Personal",
                "stereotype": "layer",
                "coords": (380, 660, -40, -160),
                "notes": "Capa de Presentación: Vistas Angular Web para configuración de tiendas físicas y administración del personal de ventas."
            },
            "Vista_Offline": {
                "name": "Paquete Vistas Catálogo y Contingencia Offline",
                "stereotype": "layer",
                "coords": (710, 990, -40, -160),
                "notes": "Capa de Presentación: Interfaces PWA (Angular) y Móvil (Flutter) con semáforo de conectividad y consulta local de existencias."
            },

            # CAPA 2: APLICACIÓN (CONTROLADORES & SERVICIOS)
            "Ctrl_SaaS": {
                "name": "Paquete Controladores SaaS y Suscripciones",
                "stereotype": "layer",
                "coords": (50, 330, -230, -350),
                "notes": "Capa de Aplicación: Routers FastAPI y servicios TenantService y SubscriptionService con gobernanza de cuotas."
            },
            "Ctrl_Sucursales": {
                "name": "Paquete Controladores Sucursales y Empleados",
                "stereotype": "layer",
                "coords": (380, 660, -230, -350),
                "notes": "Capa de Aplicación: Routers FastAPI y servicios BranchService y UserService con aislamiento estricto por tenant."
            },
            "Ctrl_Offline": {
                "name": "Paquete Controladores Catálogo y Sincronización",
                "stereotype": "layer",
                "coords": (710, 990, -230, -350),
                "notes": "Capa de Aplicación: Servicios de sincronización diferencial (CatalogSyncService) y endpoints de exportación de catálogo."
            },

            # CAPA 3: DOMINIO (MODELOS DE NEGOCIO)
            "Model_SaaS": {
                "name": "Paquete Modelos SaaS y Contratos",
                "stereotype": "layer",
                "coords": (50, 330, -420, -540),
                "notes": "Capa de Dominio: Entidades conceptuales Tenant, SubscriptionPlan, Subscription y reglas de contrato."
            },
            "Model_Sucursales": {
                "name": "Paquete Modelos Organización y Personal",
                "stereotype": "layer",
                "coords": (380, 660, -420, -540),
                "notes": "Capa de Dominio: Entidades Sucursal, Usuario, Rol y Bitácora de auditoría transaccional."
            },
            "Model_Offline": {
                "name": "Paquete Modelos Catálogo e Inventario",
                "stereotype": "layer",
                "coords": (710, 990, -420, -540),
                "notes": "Capa de Dominio: Entidades Categoria, Producto, VarianteProducto, Inventario y SyncOperation."
            },

            # CAPA 4: INFRAESTRUCTURA Y PERSISTENCIA (SGBD)
            # Base Central abarca Columnas 1 y 2
            "DB_Postgres": {
                "name": "Base de Datos Central PostgreSQL 16",
                "stereotype": "layer",
                "coords": (180, 530, -610, -730),
                "notes": "Capa de Persistencia Nube: Esquema relacional multi-tenant con particionamiento por tenant_id e índices compuestos."
            },
            # Persistencia Desconectada se alinea con Columna 3
            "DB_Local": {
                "name": "Persistencia Local Desconectada\n(SQLite Móvil / IndexedDB Web)",
                "stereotype": "layer",
                "coords": (710, 990, -610, -730),
                "notes": "Capa de Persistencia Local: Motor SQLite embebido en Flutter y almacén transaccional IndexedDB en Angular PWA."
            }
        }

        element_map = {}
        for key, pdata in packages_def.items():
            el = target_pkg.Elements.AddNew(pdata["name"], "Package")
            el.Stereotype = pdata["stereotype"]
            el.Notes = pdata["notes"]
            el.Update()
            element_map[key] = el

            l, r, t, b = pdata["coords"]
            d_obj = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d_obj.ElementID = el.ElementID
            d_obj.left = l
            d_obj.right = r
            d_obj.top = t
            d_obj.bottom = b
            d_obj.Update()

        # Dependencias UML 2.5 (Strict Layering Rule: Top-down Client ..> Supplier)
        dependencies = [
            # Columna 1 (SaaS): Presentación -> Aplicación -> Dominio -> Persistencia
            ("Vista_SaaS", "Ctrl_SaaS", "«use»"),
            ("Ctrl_SaaS", "Model_SaaS", "«access»"),
            ("Model_SaaS", "DB_Postgres", "«persists»"),

            # Columna 2 (Sucursales & Personal): Presentación -> Aplicación -> Dominio -> Persistencia
            ("Vista_Sucursales", "Ctrl_Sucursales", "«use»"),
            ("Ctrl_Sucursales", "Model_Sucursales", "«access»"),
            ("Model_Sucursales", "DB_Postgres", "«persists»"),

            # Columna 3 (Catálogo, Stock & Offline): Presentación -> Aplicación -> Dominio -> Persistencia
            ("Vista_Offline", "Ctrl_Offline", "«use»"),
            ("Ctrl_Offline", "Model_Offline", "«access»"),
            ("Model_Offline", "DB_Postgres", "«persists»"),
            ("Model_Offline", "DB_Local", "«syncs_local»"),

            # Interacción horizontal entre controladores de negocio (Gobernanza de límites)
            ("Ctrl_SaaS", "Ctrl_Sucursales", "«limits»")
        ]

        for src_key, dst_key, stereotype in dependencies:
            src_el = element_map[src_key]
            dst_el = element_map[dst_key]

            conn = src_el.Connectors.AddNew("", "Dependency")
            conn.SupplierID = dst_el.ElementID
            conn.Direction = "Source -> Destination"
            conn.Stereotype = stereotype
            conn.Update()

        diag.Update()
        repo.SaveDiagram(diag.DiagramID)
        repo.ReloadDiagram(diag.DiagramID)

        out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6'
        img_path = os.path.join(out_dir, "diagrama_estructura_capas_uml25_clean.png")
        repo.GetProjectInterface().PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
        print(f"Diagrama de estructura en capas limpio exportado a: {img_path}")

    finally:
        try: repo.CloseFile()
        except: pass
        try: ea.Quit()
        except: pass

if __name__ == '__main__':
    main()
