import win32com.client
import sys

def main():
    print("=== Generando Diagrama de Componentes en Enterprise Architect ===")
    
    rep = win32com.client.Dispatch('EA.Repository')
    eap_path = r'c:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
    rep.OpenFile(eap_path)
    
    try:
        root = rep.Models.GetAt(0)
        
        # Buscar o crear paquete dedicado
        pkg_name = "Segundo Parcial - Diagrama de Componentes"
        target_pkg = None
        for p in root.Packages:
            if p.Name == pkg_name:
                target_pkg = p
                break
                
        if not target_pkg:
            target_pkg = root.Packages.AddNew(pkg_name, "Package")
            target_pkg.Update()
            root.Packages.Refresh()
            print(f"Paquete creado: {pkg_name} (ID: {target_pkg.PackageID})")
        else:
            print(f"Paquete existente encontrado: {pkg_name} (ID: {target_pkg.PackageID})")
            
        # Limpiar diagramas y elementos previos dentro de este paquete para idempotencia
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()
        
        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()
        
        # Crear diagrama de tipo Component
        diag_title = "Diagrama de Componentes"
        diag = target_pkg.Diagrams.AddNew(diag_title, "Component")
        diag.Notes = "Diagrama de Componentes que ilustra la arquitectura de software: Componentes UI/DTO/Servicios, Capa Nuclear (Routers, Models, Settings), Paquetes de Dominio y Persistencia Multi-Tenant."
        diag.Update()
        
        # ==========================================
        # 1. ELEMENTOS DE LA COLUMNA IZQUIERDA (Frontend & Servicios)
        # ==========================================
        c_ui = target_pkg.Elements.AddNew("Componentes UI", "Component")
        c_ui.Notes = "Vistas y componentes visuales en Angular PWA y Flutter para interacción de usuarios, cajeros y administradores."
        c_ui.Update()
        
        c_dto = target_pkg.Elements.AddNew("Interfaces / DTOs", "Component")
        c_dto.Notes = "Esquemas Pydantic y modelos TypeScript para validación y transferencia de datos entre capas."
        c_dto.Update()
        
        c_app_serv = target_pkg.Elements.AddNew("Servicios de Aplicación", "Component")
        c_app_serv.Notes = "Casos de uso y orquestación de lógica transaccional de negocio independiente del transporte."
        c_app_serv.Update()
        
        c_config_left = target_pkg.Elements.AddNew("Configuración", "Component")
        c_config_left.Notes = "Variables de entorno de cliente, constantes de conexión y configuración de tema/i18n."
        c_config_left.Update()
        
        # ==========================================
        # 2. ELEMENTOS DE LA COLUMNA CENTRAL (Core Backend)
        # ==========================================
        c_routers = target_pkg.Elements.AddNew("Routers / Controllers", "Component")
        c_routers.Notes = "Enrutadores FastAPI con inyección de dependencias, validación OpenAPI y middleware tenant."
        c_routers.Update()
        
        c_models = target_pkg.Elements.AddNew("Models / Entidades", "Component")
        c_models.Notes = "Entidades de dominio y modelos SQLAlchemy 2.0 que definen el esquema relacional y reglas de integridad."
        c_models.Update()
        
        c_settings = target_pkg.Elements.AddNew("Settings / Config", "Component")
        c_settings.Notes = "Configuración global de backend (pydantic-settings), pool de conexiones asyncpg y claves JWT."
        c_settings.Update()
        
        # ==========================================
        # 3. ELEMENTOS DE LA COLUMNA DERECHA (Paquetes de Dominio)
        # ==========================================
        domain_packages_def = [
            ("pkg1", "Paquete 1: Seguridad y Control de Acceso", "Auth JWT, Roles, Permisos, tenant_id", -50, -160, -95, -145),
            ("pkg2", "Paquete 2: Gestión de Usuarios y Sucursales", "Usuarios, Sucursales, Suscripción", -190, -300, -235, -285),
            ("pkg3", "Paquete 3: Catálogo, Inventario y Proveedores", "Prendas, Variantes, Guía de Medidas, Inventario", -330, -440, -375, -425),
            ("pkg4", "Paquete 4: Ventas, Reservas y Postventa", "Ventas, Reservas, Nota de Devolución", -470, -580, -515, -565),
            ("pkg5", "Paquete 5: Sincronización Offline, IA y Analítica", "Sync Engine, Reportes IA, ML Dashboard", -610, -720, -655, -705)
        ]
        
        domain_pkgs = {}
        domain_texts = {}
        for key, name, content, p_top, p_bot, t_top, t_bot in domain_packages_def:
            pkg_el = target_pkg.Elements.AddNew(name, "Package")
            pkg_el.Notes = content
            pkg_el.Update()
            domain_pkgs[key] = (pkg_el, p_top, p_bot)
            
            # Texto visible dentro del cuerpo del paquete
            txt_el = target_pkg.Elements.AddNew(content, "Text")
            txt_el.Notes = content
            txt_el.Update()
            domain_texts[key] = (txt_el, t_top, t_bot)
            
        # ==========================================
        # 4. PAQUETE Y COMPONENTES DE BASE DE DATOS (Inferior)
        # ==========================================
        pkg_db = target_pkg.Elements.AddNew("Base de Datos", "Package")
        pkg_db.Notes = "Contenedor de persistencia relacional PostgreSQL 16 y versionado de esquema Alembic."
        pkg_db.Update()
        
        c_alembic = target_pkg.Elements.AddNew("<<scripts>>\nMigraciones Alembic", "Component")
        c_alembic.Notes = "Scripts de migración DDL versionados para mantenimiento evolutivo del esquema de datos."
        c_alembic.Update()
        
        c_pg = target_pkg.Elements.AddNew("PostgreSQL 16", "Component")
        c_pg.Notes = "Motor de base de datos relacional PostgreSQL 16 con particionamiento y aislamiento multitenant."
        c_pg.Update()
        
        c_audit = target_pkg.Elements.AddNew("Auditoría / Logs", "Component")
        c_audit.Notes = "Bitácora inmutable de transacciones, accesos y cambios para trazabilidad regulatoria."
        c_audit.Update()
        
        c_tablas = target_pkg.Elements.AddNew("Tablas Tenantizadas", "Component")
        c_tablas.Notes = "Esquema relacional con discriminador tenant_id para segregación estricta de datos por empresa."
        c_tablas.Update()
        
        # ==========================================
        # 5. POSICIONAMIENTO EN EL DIAGRAMA
        # ==========================================
        # Fondo: Contenedor Base de Datos (L=160, R=900, T=-680, B=-980)
        d_db = diag.DiagramObjects.AddNew("l=160;r=900;t=-680;b=-980;", "")
        d_db.ElementID = pkg_db.ElementID
        d_db.left = 160; d_db.right = 900; d_db.top = -680; d_db.bottom = -980
        d_db.Sequence = 100
        d_db.Update()
        
        # Columna Izquierda (L=60, R=260)
        left_components = [
            (c_ui, -120, -200),
            (c_dto, -240, -320),
            (c_app_serv, -360, -440),
            (c_config_left, -480, -560)
        ]
        for idx, (el, top, bot) in enumerate(left_components):
            d = diag.DiagramObjects.AddNew(f"l=60;r=260;t={top};b={bot};", "")
            d.ElementID = el.ElementID
            d.left = 60; d.right = 260; d.top = top; d.bottom = bot
            d.Sequence = idx + 1
            d.Update()
            
        # Columna Central
        # Routers / Controllers (L=400, R=640, T=-120, B=-200)
        d = diag.DiagramObjects.AddNew("l=400;r=640;t=-120;b=-200;", "")
        d.ElementID = c_routers.ElementID
        d.left = 400; d.right = 640; d.top = -120; d.bottom = -200
        d.Sequence = 10
        d.Update()
        
        # Models / Entidades (L=380, R=660, T=-270, B=-390)
        d = diag.DiagramObjects.AddNew("l=380;r=660;t=-270;b=-390;", "")
        d.ElementID = c_models.ElementID
        d.left = 380; d.right = 660; d.top = -270; d.bottom = -390
        d.Sequence = 11
        d.Update()
        
        # Settings / Config (L=400, R=640, T=-480, B=-560)
        d = diag.DiagramObjects.AddNew("l=400;r=640;t=-480;b=-560;", "")
        d.ElementID = c_settings.ElementID
        d.left = 400; d.right = 640; d.top = -480; d.bottom = -560
        d.Sequence = 12
        d.Update()
        
        # Columna Derecha (Paquetes L=800, R=1140)
        for key in domain_pkgs:
            pkg_el, p_top, p_bot = domain_pkgs[key]
            d_p = diag.DiagramObjects.AddNew(f"l=800;r=1140;t={p_top};b={p_bot};", "")
            d_p.ElementID = pkg_el.ElementID
            d_p.left = 800; d_p.right = 1140; d_p.top = p_top; d_p.bottom = p_bot
            d_p.Sequence = 50
            d_p.Update()
            
            txt_el, t_top, t_bot = domain_texts[key]
            d_t = diag.DiagramObjects.AddNew(f"l=820;r=1120;t={t_top};b={t_bot};", "")
            d_t.ElementID = txt_el.ElementID
            d_t.left = 820; d_t.right = 1120; d_t.top = t_top; d_t.bottom = t_bot
            d_t.Sequence = 5
            d_t.Update()
            
        # Componentes dentro de Base de Datos
        # Top-left: Alembic
        d = diag.DiagramObjects.AddNew("l=200;r=470;t=-740;b=-820;", "")
        d.ElementID = c_alembic.ElementID
        d.left = 200; d.right = 470; d.top = -740; d.bottom = -820
        d.Sequence = 20
        d.Update()
        
        # Top-right: PostgreSQL 16
        d = diag.DiagramObjects.AddNew("l=590;r=860;t=-740;b=-820;", "")
        d.ElementID = c_pg.ElementID
        d.left = 590; d.right = 860; d.top = -740; d.bottom = -820
        d.Sequence = 21
        d.Update()
        
        # Bottom-left: Auditoria / Logs
        d = diag.DiagramObjects.AddNew("l=200;r=470;t=-870;b=-950;", "")
        d.ElementID = c_audit.ElementID
        d.left = 200; d.right = 470; d.top = -870; d.bottom = -950
        d.Sequence = 22
        d.Update()
        
        # Bottom-right: Tablas Tenantizadas
        d = diag.DiagramObjects.AddNew("l=590;r=860;t=-870;b=-950;", "")
        d.ElementID = c_tablas.ElementID
        d.left = 590; d.right = 860; d.top = -870; d.bottom = -950
        d.Sequence = 23
        d.Update()
        
        # ==========================================
        # 6. CONECTORES DE DEPENDENCIA
        # ==========================================
        # A. Routers -> Models
        con = c_routers.Connectors.AddNew("", "Dependency")
        con.SupplierID = c_models.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # B. Columna Izquierda -> Models
        for el in [c_ui, c_dto, c_app_serv, c_config_left]:
            con = el.Connectors.AddNew("", "Dependency")
            con.SupplierID = c_models.ElementID
            con.Direction = "Source -> Destination"
            con.Update()
            
        # C. Models -> Settings
        con = c_models.Connectors.AddNew("", "Dependency")
        con.SupplierID = c_settings.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # D. Models -> Paquetes de Dominio (1 a 5)
        for key in domain_pkgs:
            pkg_el, _, _ = domain_pkgs[key]
            con = c_models.Connectors.AddNew("", "Dependency")
            con.SupplierID = pkg_el.ElementID
            con.Direction = "Source -> Destination"
            con.Update()
            
        # E. Settings -> Base de Datos
        con = c_settings.Connectors.AddNew("", "Dependency")
        con.SupplierID = pkg_db.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # F. Dependencias internas dentro de Base de Datos
        # PostgreSQL 16 -> Alembic
        con = c_pg.Connectors.AddNew("", "Dependency")
        con.SupplierID = c_alembic.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # PostgreSQL 16 -> Tablas Tenantizadas
        con = c_pg.Connectors.AddNew("", "Dependency")
        con.SupplierID = c_tablas.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # Tablas Tenantizadas -> Auditoria / Logs
        con = c_tablas.Connectors.AddNew("", "Dependency")
        con.SupplierID = c_audit.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        diag.Update()
        rep.SaveDiagram(diag.DiagramID)
        rep.ReloadDiagram(diag.DiagramID)
        
        diag_id = diag.DiagramID
        diag_name = diag.Name
        target_pkg_id = target_pkg.PackageID
        print(f"Diagrama de Componentes creado con éxito!")
        print(f"Paquete ID: {target_pkg_id}, Diagrama ID: {diag_id}, Nombre: '{diag_name}'")
        print(f"Total DiagramObjects: {diag.DiagramObjects.Count}")
        
    finally:
        try: rep.CloseFile()
        except: pass
        try: rep.Exit()
        except: pass

if __name__ == "__main__":
    main()
