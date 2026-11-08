# -*- coding: utf-8 -*-
"""
Script maestro para generar los 7 Diagramas de Caso de Uso individuales (Actor + CU) de la ETAPA 2 en Enterprise Architect.
Paquete: 'Segundo Parcial - Casos de Uso (Etapa 2)'
Casos de Uso incluidos:
  - CU-08: Registrar Venta de Contado Offline
  - CU-09: Registrar Reserva de Prendas Offline
  - CU-10: Consultar Operaciones Locales Pendientes (Outbox)
  - CU-11: Sincronizar Operaciones con el Servidor
  - CU-12: Gestionar Conflictos de Sincronización
  - CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)
  - CU-22: Gestionar Datos Mínimos de Clientes Offline
"""

import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

UC_SPECS = [
    {
        "code": "CU-08",
        "title": "CU-08: Registrar Venta de Contado Offline",
        "actors": [("Cajero / Vendedor", 80, -70, 160, -190)],
        "uc_pos": (300, -90, 560, -170)
    },
    {
        "code": "CU-09",
        "title": "CU-09: Registrar Reserva de Prendas Offline",
        "actors": [
            ("Cajero / Vendedor", 80, -40, 160, -140),
            ("Cliente", 80, -180, 160, -280)
        ],
        "uc_pos": (300, -110, 560, -190)
    },
    {
        "code": "CU-10",
        "title": "CU-10: Consultar Operaciones Locales Pendientes (Outbox)",
        "actors": [("Cajero / Vendedor", 80, -70, 160, -190)],
        "uc_pos": (300, -90, 580, -170)
    },
    {
        "code": "CU-11",
        "title": "CU-11: Sincronizar Operaciones con el Servidor",
        "actors": [
            ("Cajero / Vendedor", 80, -40, 160, -140),
            ("Actores de Sistema (Motor de Sync)", 80, -180, 160, -280)
        ],
        "uc_pos": (300, -110, 560, -190)
    },
    {
        "code": "CU-12",
        "title": "CU-12: Gestionar Conflictos de Sincronización",
        "actors": [
            ("Tenant Admin", 80, -40, 160, -140),
            ("Cajero / Vendedor", 80, -180, 160, -280)
        ],
        "uc_pos": (300, -110, 560, -190)
    },
    {
        "code": "CU-13",
        "title": "CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)",
        "actors": [("Cajero / Vendedor", 80, -70, 160, -190)],
        "uc_pos": (300, -90, 580, -170)
    },
    {
        "code": "CU-22",
        "title": "CU-22: Gestionar Datos Mínimos de Clientes Offline",
        "actors": [("Cajero / Vendedor", 80, -70, 160, -190)],
        "uc_pos": (300, -90, 580, -170)
    }
]

def main():
    print("Iniciando creación de los Diagramas de Casos de Uso (Etapa 2) en Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    model = rep.Models.GetAt(0)
    pkg_name = "Segundo Parcial - Casos de Uso (Etapa 2)"
    pkg = None
    for p in model.Packages:
        if p.Name == pkg_name:
            pkg = p
            break

    if pkg is None:
        pkg = model.Packages.AddNew(pkg_name, "")
        pkg.Update()
        model.Packages.Refresh()
        print(f"Paquete creado: '{pkg_name}' (ID: {pkg.PackageID})")
    else:
        print(f"Paquete existente: '{pkg_name}' (ID: {pkg.PackageID})")

    def get_or_create_element(name, elem_type):
        for i in range(pkg.Elements.Count):
            el = pkg.Elements.GetAt(i)
            if el.Name == name and el.Type == elem_type:
                return el
        el = pkg.Elements.AddNew(name, elem_type)
        el.Update()
        pkg.Elements.Refresh()
        return el

    for spec in UC_SPECS:
        diag_name = spec["title"]
        print(f"\n--- Creando Diagrama de Caso de Uso: {diag_name} ---")

        diag = None
        for d in pkg.Diagrams:
            if d.Name == diag_name:
                diag = d
                break

        if diag is None:
            diag = pkg.Diagrams.AddNew(diag_name, "Use Case")
            diag.Update()
            pkg.Diagrams.Refresh()

        # Crear UseCase element
        uc_el = get_or_create_element(spec["title"], "UseCase")
        l, t, r, b = spec["uc_pos"]
        dobj_uc = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
        dobj_uc.ElementID = uc_el.ElementID
        dobj_uc.left = l
        dobj_uc.right = r
        dobj_uc.top = t
        dobj_uc.bottom = b
        dobj_uc.Update()

        # Crear y asociar actores
        for a_name, al, at, ar, ab in spec["actors"]:
            a_el = get_or_create_element(a_name, "Actor")
            dobj_a = diag.DiagramObjects.AddNew(f"l={al};r={ar};t={at};b={ab};", "")
            dobj_a.ElementID = a_el.ElementID
            dobj_a.left = al
            dobj_a.right = ar
            dobj_a.top = at
            dobj_a.bottom = ab
            dobj_a.Update()

            # Conector de asociación
            conn_exists = False
            for c in a_el.Connectors:
                if c.SupplierID == uc_el.ElementID and c.Type == "Association":
                    conn_exists = True
                    break
            if not conn_exists:
                conn = a_el.Connectors.AddNew("", "Association")
                conn.SupplierID = uc_el.ElementID
                conn.Direction = "Unspecified"
                conn.Update()
                a_el.Connectors.Refresh()

        # Estilo con marco UML 2.5
        current_style = str(diag.StyleEx or "")
        if "ShowFrame=1;" not in current_style:
            diag.StyleEx = current_style + "ShowFrame=1;"
        diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
        diag.DiagramObjects.Refresh()
        diag.Update()

        rep.SaveDiagram(diag.DiagramID)
        rep.ReloadDiagram(diag.DiagramID)
        print(f"  Diagrama guardado con éxito: {diag_name} (ID: {diag.DiagramID})")

    pkg_id = pkg.PackageID
    pkg.Update()
    rep.CloseFile()
    rep.Exit()

    print("\n" + "=" * 70)
    print("¡LOS 7 DIAGRAMAS DE CASO DE USO DE LA ETAPA 2 FUERON GENERADOS CON ÉXITO!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name} (ID: {pkg_id})")
    print("=" * 70)

if __name__ == '__main__':
    main()
