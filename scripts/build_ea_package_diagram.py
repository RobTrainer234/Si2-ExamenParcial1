import win32com.client
import sys

def main():
    print("=== Generando Diagrama de Paquetes (Arquitectura en 4 Capas) en Enterprise Architect ===")
    
    rep = win32com.client.Dispatch('EA.Repository')
    eap_path = r'c:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
    rep.OpenFile(eap_path)
    
    try:
        root = rep.Models.GetAt(0)
        
        # Buscar o crear paquete dedicado
        pkg_name = "Segundo Parcial - Diagrama de Paquetes (Arquitectura en 4 Capas)"
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
        
        # Crear diagrama
        diag_title = "Diagrama de Paquetes – Plataforma Web/Móvil FashionStore SaaS"
        diag = target_pkg.Diagrams.AddNew(diag_title, "Package")
        diag.Notes = "Diagrama de Paquetes organizado en 4 capas horizontales (Específica, General, Interna, Software) con dependencias verticales y cruzadas conforme a UML 2.5."
        diag.Update()
        
        # ==========================================
        # 1. DEFINICIÓN DE CONTENEDORES HORIZONTALES
        # ==========================================
        # Ancho total: 1480 px (Left: 40, Right: 1520)
        c_especifica = target_pkg.Elements.AddNew("Capa Específica", "Package")
        c_especifica.Notes = "Capa superior que expone las interfaces de usuario y controladores específicos de la aplicación."
        c_especifica.Update()
        
        c_general = target_pkg.Elements.AddNew("Capa General", "Package")
        c_general.Notes = "Capa que contiene la lógica de negocio nuclear y servicios de dominio de la plataforma."
        c_general.Update()
        
        c_interna = target_pkg.Elements.AddNew("Capa Interna", "Package")
        c_interna.Notes = "Capa que agrupa los frameworks tecnológicos, motores de desarrollo y persistencia."
        c_interna.Update()
        
        c_software = target_pkg.Elements.AddNew("Capa Software", "Package")
        c_software.Notes = "Capa base de infraestructura de ejecución, plataformas cliente y nube AWS."
        c_software.Update()
        
        # ==========================================
        # 2. DEFINICIÓN DE SUBPAQUETES
        # ==========================================
        # 7 Paquetes en Capa Específica
        p_esp_names = [
            ("P1_esp", "P1: Gestión de Usuarios y Seguridad"),
            ("P2_esp", "P2: Gestión de Empresas y Suscripciones"),
            ("P3_esp", "P3: Gestión de Sucursales y Personal"),
            ("P4_esp", "P4: Catálogo Maestro y Variantes"),
            ("P5_esp", "P5: Inventario, Stock y Proveedores"),
            ("P6_esp", "P6: Ventas POS, Reservas y Postventa"),
            ("P7_esp", "P7: Sincronización Offline, IA y Analítica")
        ]
        sub_esp = {}
        for key, name in p_esp_names:
            el = target_pkg.Elements.AddNew(name, "Package")
            el.Notes = f"Módulo específico para {name} en frontend y controladores."
            el.Update()
            sub_esp[key] = el
            
        # 7 Paquetes en Capa General
        p_gen_names = [
            ("P1_gen", "P1: Gestión de Usuarios y Seguridad"),
            ("P2_gen", "P2: Gestión de Empresas y Suscripciones"),
            ("P3_gen", "P3: Gestión de Sucursales y Personal"),
            ("P4_gen", "P4: Catálogo Maestro y Variantes"),
            ("P5_gen", "P5: Inventario, Stock y Proveedores"),
            ("P6_gen", "P6: Ventas POS, Reservas y Postventa"),
            ("P7_gen", "P7: Sincronización Offline, IA y Analítica")
        ]
        sub_gen = {}
        for key, name in p_gen_names:
            el = target_pkg.Elements.AddNew(name, "Package")
            el.Notes = f"Reglas de negocio y entidades de dominio para {name}."
            el.Update()
            sub_gen[key] = el
            
        # 3 Paquetes en Capa Interna
        p_int_names = [
            ("P_int_frontend", "Angular (Web) /\nFlutter (Móvil)"),
            ("P_int_backend", "FastAPI\n(Backend)"),
            ("P_int_db", "PostgreSQL\n(Base de Datos)")
        ]
        sub_int = {}
        for key, name in p_int_names:
            el = target_pkg.Elements.AddNew(name, "Package")
            el.Notes = f"Framework y plataforma técnica: {name}."
            el.Update()
            sub_int[key] = el
            
        # 2 Paquetes en Capa Software
        p_soft_names = [
            ("P_soft_client", "Navegador Web /\nDispositivo Móvil"),
            ("P_soft_cloud", "AWS\n(Despliegue / Hosting)")
        ]
        sub_soft = {}
        for key, name in p_soft_names:
            el = target_pkg.Elements.AddNew(name, "Package")
            el.Notes = f"Infraestructura y runtime: {name}."
            el.Update()
            sub_soft[key] = el
            
        # ==========================================
        # 3. COLOCACIÓN DE ELEMENTOS EN DIAGRAMA
        # ==========================================
        # Sequence alto = AL FONDO (Contenedores)
        # Sequence bajo = AL FRENTE (Subpaquetes)
        
        # Contenedor 1: Capa Específica (L=40, R=1520, T=-40, B=-240)
        d = diag.DiagramObjects.AddNew("l=40;r=1520;t=-40;b=-240;", "")
        d.ElementID = c_especifica.ElementID
        d.left = 40; d.right = 1520; d.top = -40; d.bottom = -240
        d.Sequence = 100
        d.Update()
        
        # Subpaquetes Capa Específica (7 columnas de ancho 190, gap 18)
        col_coords = [
            (60, 250),
            (268, 458),
            (476, 666),
            (684, 874),
            (892, 1082),
            (1100, 1290),
            (1308, 1498)
        ]
        for idx, (l, r) in enumerate(col_coords):
            el = sub_esp[f"P{idx+1}_esp"]
            d_sub = diag.DiagramObjects.AddNew(f"l={l};r={r};t=-90;b=-215;", "")
            d_sub.ElementID = el.ElementID
            d_sub.left = l; d_sub.right = r; d_sub.top = -90; d_sub.bottom = -215
            d_sub.Sequence = idx + 1
            d_sub.Update()
            
        # Contenedor 2: Capa General (L=40, R=1520, T=-320, B=-520)
        d = diag.DiagramObjects.AddNew("l=40;r=1520;t=-320;b=-520;", "")
        d.ElementID = c_general.ElementID
        d.left = 40; d.right = 1520; d.top = -320; d.bottom = -520
        d.Sequence = 90
        d.Update()
        
        # Subpaquetes Capa General (7 columnas)
        for idx, (l, r) in enumerate(col_coords):
            el = sub_gen[f"P{idx+1}_gen"]
            d_sub = diag.DiagramObjects.AddNew(f"l={l};r={r};t=-370;b=-495;", "")
            d_sub.ElementID = el.ElementID
            d_sub.left = l; d_sub.right = r; d_sub.top = -370; d_sub.bottom = -495
            d_sub.Sequence = idx + 10
            d_sub.Update()
            
        # Contenedor 3: Capa Interna (L=40, R=1520, T=-600, B=-780)
        d = diag.DiagramObjects.AddNew("l=40;r=1520;t=-600;b=-780;", "")
        d.ElementID = c_interna.ElementID
        d.left = 40; d.right = 1520; d.top = -600; d.bottom = -780
        d.Sequence = 80
        d.Update()
        
        # 3 Subpaquetes Capa Interna
        int_coords = [
            (sub_int["P_int_frontend"], 160, 480, -640, -750),
            (sub_int["P_int_backend"], 620, 940, -640, -750),
            (sub_int["P_int_db"], 1080, 1400, -640, -750)
        ]
        for el, l, r, t, b in int_coords:
            d_sub = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d_sub.ElementID = el.ElementID
            d_sub.left = l; d_sub.right = r; d_sub.top = t; d_sub.bottom = b
            d_sub.Sequence = 20
            d_sub.Update()
            
        # Contenedor 4: Capa Software (L=40, R=1520, T=-860, B=-1030)
        d = diag.DiagramObjects.AddNew("l=40;r=1520;t=-860;b=-1030;", "")
        d.ElementID = c_software.ElementID
        d.left = 40; d.right = 1520; d.top = -860; d.bottom = -1030
        d.Sequence = 70
        d.Update()
        
        # 2 Subpaquetes Capa Software
        soft_coords = [
            (sub_soft["P_soft_client"], 190, 530, -895, -1005),
            (sub_soft["P_soft_cloud"], 840, 1180, -895, -1005)
        ]
        for el, l, r, t, b in soft_coords:
            d_sub = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d_sub.ElementID = el.ElementID
            d_sub.left = l; d_sub.right = r; d_sub.top = t; d_sub.bottom = b
            d_sub.Sequence = 30
            d_sub.Update()
            
        # ==========================================
        # 4. CONECTORES DE DEPENDENCIA (FLECHAS DISCONTINUAS ..>)
        # ==========================================
        # A. Capa Específica a Capa General (Verticales P1->P1, ..., P7->P7)
        for i in range(1, 8):
            src = sub_esp[f"P{i}_esp"]
            dst = sub_gen[f"P{i}_gen"]
            con = src.Connectors.AddNew("", "Dependency")
            con.SupplierID = dst.ElementID
            con.Direction = "Source -> Destination"
            con.Update()
            
        # B. Capa General a Capa Interna (Abanico hacia frameworks)
        # P1, P2 -> Angular/Flutter
        for p_key in ["P1_gen", "P2_gen"]:
            src = sub_gen[p_key]
            con = src.Connectors.AddNew("", "Dependency")
            con.SupplierID = sub_int["P_int_frontend"].ElementID
            con.Direction = "Source -> Destination"
            con.Update()
            
        # P2, P3, P4, P5, P6 -> FastAPI (Backend)
        for p_key in ["P2_gen", "P3_gen", "P4_gen", "P5_gen", "P6_gen"]:
            src = sub_gen[p_key]
            con = src.Connectors.AddNew("", "Dependency")
            con.SupplierID = sub_int["P_int_backend"].ElementID
            con.Direction = "Source -> Destination"
            con.Update()
            
        # P6, P7 -> PostgreSQL (Base de Datos)
        for p_key in ["P6_gen", "P7_gen"]:
            src = sub_gen[p_key]
            con = src.Connectors.AddNew("", "Dependency")
            con.SupplierID = sub_int["P_int_db"].ElementID
            con.Direction = "Source -> Destination"
            con.Update()
            
        # C. Capa Interna a Capa Software
        # Frontend -> Navegador / Móvil
        con = sub_int["P_int_frontend"].Connectors.AddNew("", "Dependency")
        con.SupplierID = sub_soft["P_soft_client"].ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # FastAPI -> AWS Cloud
        con = sub_int["P_int_backend"].Connectors.AddNew("", "Dependency")
        con.SupplierID = sub_soft["P_soft_cloud"].ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        # PostgreSQL -> AWS Cloud
        con = sub_int["P_int_db"].Connectors.AddNew("", "Dependency")
        con.SupplierID = sub_soft["P_soft_cloud"].ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        
        diag.Update()
        rep.SaveDiagram(diag.DiagramID)
        rep.ReloadDiagram(diag.DiagramID)
        
        diag_id = diag.DiagramID
        diag_name = diag.Name
        target_pkg_id = target_pkg.PackageID
        print(f"Diagrama de Paquetes creado con éxito!")
        print(f"Paquete ID: {target_pkg_id}, Diagrama ID: {diag_id}, Nombre: '{diag_name}'")
        print(f"Total elementos: {target_pkg.Elements.Count}, Total DiagramObjects: {diag.DiagramObjects.Count}")
        
    finally:
        try: rep.CloseFile()
        except: pass
        try: rep.Exit()
        except: pass

if __name__ == "__main__":
    main()
