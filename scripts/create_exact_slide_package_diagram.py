import win32com.client
import os

def main():
    print("Iniciando creación del Diagrama de Paquetes (idéntico a las diapositivas)...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    try:
        if not repo.ConnectionString:
            repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

        root_model = repo.Models.GetAt(0)

        # Buscar o crear paquete
        target_pkg = None
        for p in root_model.Packages:
            if 'Arquitectura del Sistema (Capas UML 2.5)' in p.Name:
                target_pkg = p
                break

        if target_pkg is None:
            target_pkg = root_model.Packages.AddNew("Segundo Parcial - Arquitectura del Sistema (Capas UML 2.5)", "Package")
            target_pkg.Update()
            root_model.Packages.Refresh()

        # Limpiar
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()

        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()

        diag = target_pkg.Diagrams.AddNew("Diagrama de Paquetes - Arquitectura en Capas (UML 2.5)", "Package")
        diag.Update()

        # 1. Contenedores Principales (Grandes)
        # Capa de presentación (Top)
        pkg_pres = target_pkg.Elements.AddNew("Capa de presentación", "Package")
        pkg_pres.Update()

        # Capa de Lógica de Negocio (Middle)
        pkg_negocio = target_pkg.Elements.AddNew("Capa de Lógica de Negocio", "Package")
        pkg_negocio.Update()

        # Subpaquetes de Presentación (Fila Superior)
        sub_web = target_pkg.Elements.AddNew("Interfaz web PWA", "Package")
        sub_web.Update()
        sub_movil = target_pkg.Elements.AddNew("Interfaz móvil", "Package")
        sub_movil.Update()
        sub_admin = target_pkg.Elements.AddNew("Interfaz admin", "Package")
        sub_admin.Update()

        # Subpaquetes de Lógica de Negocio (6 subpaquetes en 2 filas x 3 columnas)
        sub_saas = target_pkg.Elements.AddNew("Subsistema de gestión SaaS y empresas", "Package")
        sub_saas.Update()
        sub_planes = target_pkg.Elements.AddNew("Subsistema de planes y suscripciones", "Package")
        sub_planes.Update()
        sub_limites = target_pkg.Elements.AddNew("Subsistema de control de límites de plan", "Package")
        sub_limites.Update()
        sub_sucursales = target_pkg.Elements.AddNew("Subsistema de gestión de sucursales", "Package")
        sub_sucursales.Update()
        sub_catalogo = target_pkg.Elements.AddNew("Subsistema de catálogo y existencias", "Package")
        sub_catalogo.Update()
        sub_offline = target_pkg.Elements.AddNew("Subsistema de sincronización offline", "Package")
        sub_offline.Update()

        # Paquetes de Base de Datos y Persistencia (Columna Derecha)
        db_postgres = target_pkg.Elements.AddNew("Base de datos central PostgreSQL", "Package")
        db_postgres.Update()
        db_sqlite = target_pkg.Elements.AddNew("Base de datos embebida SQLite móvil", "Package")
        db_sqlite.Update()
        db_idb = target_pkg.Elements.AddNew("Almacén local IndexedDB PWA", "Package")
        db_idb.Update()

        # Posicionamiento en el Diagrama
        # En Enterprise Architect: Sequence más ALTO = dibujado primero = al FONDO (Background)
        # Sequence más BAJO = dibujado después = al FRENTE (Foreground)
        
        # Capa Presentación: L=40, R=760, T=-40, B=-170
        d_pres = diag.DiagramObjects.AddNew("l=40;r=760;t=-40;b=-170;", "")
        d_pres.ElementID = pkg_pres.ElementID
        d_pres.left = 40; d_pres.right = 760; d_pres.top = -40; d_pres.bottom = -170
        d_pres.Sequence = 100 # AL FONDO
        d_pres.Update()

        # Subpaquetes en Capa Presentación (AL FRENTE)
        coords_pres = [
            (sub_web, 60, 260, -75, -155),
            (sub_movil, 290, 500, -75, -155),
            (sub_admin, 530, 740, -75, -155)
        ]
        seq = 1
        for el, l, r, t, b in coords_pres:
            d = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d.ElementID = el.ElementID
            d.left = l; d.right = r; d.top = t; d.bottom = b
            d.Sequence = seq
            seq += 1
            d.Update()

        # Capa Lógica de Negocio: L=40, R=760, T=-240, B=-530
        d_neg = diag.DiagramObjects.AddNew("l=40;r=760;t=-240;b=-530;", "")
        d_neg.ElementID = pkg_negocio.ElementID
        d_neg.left = 40; d_neg.right = 760; d_neg.top = -240; d_neg.bottom = -530
        d_neg.Sequence = 90 # AL FONDO
        d_neg.Update()

        # Subpaquetes en Capa Lógica de Negocio (AL FRENTE)
        coords_neg = [
            (sub_saas, 60, 260, -280, -385),
            (sub_planes, 290, 500, -280, -385),
            (sub_limites, 530, 740, -280, -385),
            (sub_sucursales, 60, 260, -415, -515),
            (sub_catalogo, 290, 500, -415, -515),
            (sub_offline, 530, 740, -415, -515)
        ]
        seq = 10
        for el, l, r, t, b in coords_neg:
            d = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d.ElementID = el.ElementID
            d.left = l; d.right = r; d.top = t; d.bottom = b
            d.Sequence = seq
            seq += 1
            d.Update()

        # Paquetes de Base de Datos y Persistencia (Columna Derecha: L=820, R=1040)
        coords_db = [
            (db_postgres, 820, 1040, -260, -340),
            (db_sqlite, 820, 1040, -365, -445),
            (db_idb, 820, 1040, -470, -550)
        ]
        for el, l, r, t, b in coords_db:
            d = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d.ElementID = el.ElementID
            d.left = l; d.right = r; d.top = t; d.bottom = b
            d.Update()

        # Relaciones de Dependencia (Flechas discontinuas ..>)
        # 1. Capa de presentación -> Capa de Lógica de Negocio (Hacia abajo)
        conn_pres = pkg_pres.Connectors.AddNew("", "Dependency")
        conn_pres.SupplierID = pkg_negocio.ElementID
        conn_pres.Direction = "Source -> Destination"
        conn_pres.Update()

        # 2. Bases de datos -> Capa de Lógica de Negocio (Hacia la izquierda, exactamente como en el Slide 4 y 5)
        for db_el in [db_postgres, db_sqlite, db_idb]:
            conn_db = db_el.Connectors.AddNew("", "Dependency")
            conn_db.SupplierID = pkg_negocio.ElementID
            conn_db.Direction = "Source -> Destination"
            conn_db.Update()

        diag.Update()
        repo.SaveDiagram(diag.DiagramID)
        repo.ReloadDiagram(diag.DiagramID)

        out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6'
        img_path = os.path.join(out_dir, "diagrama_paquetes_diapositivas_exacto.png")
        repo.GetProjectInterface().PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
        print(f"Diagrama exacto a las diapositivas exportado a: {img_path}")

    finally:
        try: repo.CloseFile()
        except: pass
        try: ea.Quit()
        except: pass

if __name__ == '__main__':
    main()
