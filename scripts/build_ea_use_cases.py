# -*- coding: utf-8 -*-
"""
Script maestro para automatizar Enterprise Architect (EA) y generar:
1. Nuevo archivo de repositorio EA: 'docs/uml/FashioStore/CasosDeUso_SegundoParcial.eap'
2. Diagrama General de Casos de Uso - Etapa 1 (con los 10 CUs, 4 actores, boundary y relaciones include/extend)
3. Diagramas Individuales de cada Caso de Uso (con su límite de sistema, actores asociados y óvalo de CU)
4. Exportación nativa en alta resolución (PNG) desde Enterprise Architect usando PutDiagramImageToFile.
"""

import os
import shutil
import win32com.client

BASE_EAP = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
NEW_EAP = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"
INDIV_DIR = os.path.join(OUT_DIR, "individual_cus")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(INDIV_DIR, exist_ok=True)

# -------------------------------------------------------------
# Definición de Casos de Uso y Actores de la Etapa 1
# -------------------------------------------------------------
CUS_ETAPA1 = [
    {
        "code": "CU-01",
        "name": "CU-01: Registrar Empresa Contratante (Tenant)",
        "short_name": "CU-01: Registrar Empresa (Tenant)",
        "actors": ["Superadmin SaaS"],
        "filename": "cu01_diagram.png"
    },
    {
        "code": "CU-02",
        "name": "CU-02: Gestionar Planes de Suscripción",
        "short_name": "CU-02: Gestionar Planes Suscripción",
        "actors": ["Superadmin SaaS"],
        "filename": "cu02_diagram.png"
    },
    {
        "code": "CU-03",
        "name": "CU-03: Asignar y Renovar Suscripción de Empresa",
        "short_name": "CU-03: Asignar y Renovar Suscripción",
        "actors": ["Superadmin SaaS"],
        "filename": "cu03_diagram.png"
    },
    {
        "code": "CU-04",
        "name": "CU-04: Controlar Límites y Restricciones por Plan",
        "short_name": "CU-04: Controlar Límites por Plan",
        "actors": ["Tenant Admin"],
        "filename": "cu04_diagram.png"
    },
    {
        "code": "CU-05",
        "name": "CU-05: Gestionar Sucursales y Empleados por Tenant",
        "short_name": "CU-05: Gestionar Sucursales y Empleados",
        "actors": ["Tenant Admin"],
        "filename": "cu05_diagram.png"
    },
    {
        "code": "CU-06",
        "name": "CU-06: Descargar y Almacenar Catálogo Offline",
        "short_name": "CU-06: Descargar Catálogo Offline",
        "actors": ["Cajero / Vendedor"],
        "filename": "cu06_diagram.png"
    },
    {
        "code": "CU-07",
        "name": "CU-07: Consultar Catálogo y Existencias Offline",
        "short_name": "CU-07: Consultar Catálogo y Existencias",
        "actors": ["Cajero / Vendedor"],
        "filename": "cu07_diagram.png"
    },
    {
        "code": "CU-08",
        "name": "CU-08: Registrar Venta de Contado Offline",
        "short_name": "CU-08: Registrar Venta Contado Offline",
        "actors": ["Cajero / Vendedor"],
        "filename": "cu08_diagram.png"
    },
    {
        "code": "CU-09",
        "name": "CU-09: Registrar Reserva de Prendas Offline",
        "short_name": "CU-09: Registrar Reserva Prendas Offline",
        "actors": ["Cajero / Vendedor"],
        "filename": "cu09_diagram.png"
    },
    {
        "code": "CU-23",
        "name": "CU-23: Notificar Estado de Conectividad (Semáforo)",
        "short_name": "CU-23: Notificar Estado Conectividad",
        "actors": ["Cajero / Vendedor"],
        "filename": "cu23_diagram.png"
    },
    {
        "code": "CU-24",
        "name": "CU-24: Instalar y Registrar Service Worker (PWA)",
        "short_name": "CU-24: Instalar Service Worker (PWA)",
        "actors": ["Cliente"],
        "filename": "cu24_diagram.png"
    },
    {
        "code": "CU-25",
        "name": "CU-25: Configurar y Migrar Persistencia SQLite Móvil",
        "short_name": "CU-25: Configurar SQLite Móvil",
        "actors": ["Cajero / Vendedor"],
        "filename": "cu25_diagram.png"
    }
]

def build_enterprise_architect_project():
    print(f"1. Creando nuevo archivo EA: {NEW_EAP} ...")
    shutil.copy2(BASE_EAP, NEW_EAP)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(NEW_EAP):
        raise RuntimeError(f"No se pudo abrir el archivo EA: {NEW_EAP}")

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    # Eliminar paquetes existentes que no correspondan para dejar el proyecto limpio
    print("2. Limpiando paquetes previos para dejar el archivo enfocado en el Segundo Parcial...")
    for i in range(root_model.Packages.Count - 1, -1, -1):
        p = root_model.Packages.GetAt(i)
        if "Segundo Parcial" in p.Name or "Etapa 1" in p.Name:
            root_model.Packages.Delete(i)
            root_model.Packages.Refresh()

    # Crear Paquete Principal
    main_pkg = root_model.Packages.AddNew("Segundo Parcial - Casos de Uso (Etapa 1)", "")
    main_pkg.Notes = "Modelado formal de Casos de Uso para el Segundo Examen Parcial de Sistemas de Información II (UAGRM - FICCT)."
    main_pkg.Update()
    root_model.Packages.Refresh()

    # ---------------------------------------------------------
    # 3. Crear Actores Principales de la Etapa 1
    # ---------------------------------------------------------
    actors_dict = {}
    actor_names = [
        "Superadmin SaaS", "Tenant Admin", "Cajero / Vendedor", "Cliente",
        "Actores de Sistema (Middleware)", "Actores de Sistema (Motor de Sync)", "Actores de Sistema (IA)"
    ]
    for a_name in actor_names:
        el_act = main_pkg.Elements.AddNew(a_name, "Actor")
        el_act.Notes = f"Actor participante en el ecosistema FashionStore SaaS ({a_name})."
        el_act.Update()
        actors_dict[a_name] = el_act
    main_pkg.Elements.Refresh()

    # ---------------------------------------------------------
    # 4. Crear Casos de Uso
    # ---------------------------------------------------------
    cus_dict = {}
    for cu in CUS_ETAPA1:
        el_cu = main_pkg.Elements.AddNew(cu["name"], "UseCase")
        el_cu.Notes = f"Caso de uso {cu['code']}: {cu['name']}."
        el_cu.Update()
        cus_dict[cu["code"]] = el_cu
    main_pkg.Elements.Refresh()

    # ---------------------------------------------------------
    # 5. DIAGRAMA TIPO 1: Diagrama General de Casos de Uso - Etapa 1
    # ---------------------------------------------------------
    print("3. Generando Diagrama General de Casos de Uso (Tipo 1) en Enterprise Architect...")
    diag_gen = main_pkg.Diagrams.AddNew("Diagrama General de Casos de Uso - Etapa 1", "Use Case")
    diag_gen.Notes = "Diagrama general que consolida todos los casos de uso, actores y dependencias de la Etapa 1."
    diag_gen.Update()
    main_pkg.Diagrams.Refresh()

    # Boundary general
    bound_gen = main_pkg.Elements.AddNew("FashionStore SaaS — Etapa 1: Fundación Multitenant y Catálogo Offline", "Boundary")
    bound_gen.Update()
    main_pkg.Elements.Refresh()

    # Colocar Boundary en el diagrama
    bo_gen = diag_gen.DiagramObjects.AddNew("l=280;r=1280;t=-40;b=-920;", "")
    bo_gen.ElementID = bound_gen.ElementID
    bo_gen.Update()

    # Colocar Actores Principales
    # Superadmin SaaS (arriba izq)
    ao_super = diag_gen.DiagramObjects.AddNew("l=140;r=210;t=-120;b=-240;", "")
    ao_super.ElementID = actors_dict["Superadmin SaaS"].ElementID
    ao_super.Update()

    # Tenant Admin (abajo izq)
    ao_tenant = diag_gen.DiagramObjects.AddNew("l=140;r=210;t=-460;b=-580;", "")
    ao_tenant.ElementID = actors_dict["Tenant Admin"].ElementID
    ao_tenant.Update()

    # Cajero / Vendedor (arriba der)
    ao_cajero = diag_gen.DiagramObjects.AddNew("l=1330;r=1400;t=-140;b=-260;", "")
    ao_cajero.ElementID = actors_dict["Cajero / Vendedor"].ElementID
    ao_cajero.Update()

    # Cliente (abajo der)
    ao_cliente = diag_gen.DiagramObjects.AddNew("l=1330;r=1400;t=-480;b=-600;", "")
    ao_cliente.ElementID = actors_dict["Cliente"].ElementID
    ao_cliente.Update()

    # Coordenadas de los 10 Casos de Uso en el Diagrama General
    gen_coords = {
        "CU-01": "l=330;r=530;t=-90;b=-170;",
        "CU-02": "l=640;r=840;t=-80;b=-160;",
        "CU-03": "l=620;r=820;t=-220;b=-300;",
        "CU-04": "l=630;r=830;t=-360;b=-440;",
        "CU-05": "l=330;r=530;t=-420;b=-500;",
        "CU-06": "l=1010;r=1210;t=-140;b=-220;",
        "CU-07": "l=1010;r=1210;t=-350;b=-430;",
        "CU-23": "l=740;r=940;t=-520;b=-600;",
        "CU-24": "l=420;r=620;t=-700;b=-780;",
        "CU-25": "l=960;r=1160;t=-700;b=-780;"
    }

    for cu_code, pos_str in gen_coords.items():
        co = diag_gen.DiagramObjects.AddNew(pos_str, "")
        co.ElementID = cus_dict[cu_code].ElementID
        co.Update()

    # Crear Asociaciones en Diagrama General
    def add_assoc(actor_el, cu_el):
        con = actor_el.Connectors.AddNew("", "Association")
        con.SupplierID = cu_el.ElementID
        con.Update()
        actor_el.Connectors.Refresh()

    def add_dependency(cu_src, cu_tgt, stereotype="include"):
        con = cu_src.Connectors.AddNew("", "UseCase")
        con.Stereotype = stereotype
        con.SupplierID = cu_tgt.ElementID
        con.Update()
        cu_src.Connectors.Refresh()

    # Asociaciones
    add_assoc(actors_dict["Superadmin SaaS"], cus_dict["CU-01"])
    add_assoc(actors_dict["Superadmin SaaS"], cus_dict["CU-02"])
    add_assoc(actors_dict["Superadmin SaaS"], cus_dict["CU-03"])

    add_assoc(actors_dict["Tenant Admin"], cus_dict["CU-04"])
    add_assoc(actors_dict["Tenant Admin"], cus_dict["CU-05"])

    add_assoc(actors_dict["Cajero / Vendedor"], cus_dict["CU-06"])
    add_assoc(actors_dict["Cajero / Vendedor"], cus_dict["CU-07"])
    add_assoc(actors_dict["Cajero / Vendedor"], cus_dict["CU-23"])
    add_assoc(actors_dict["Cajero / Vendedor"], cus_dict["CU-25"])

    add_assoc(actors_dict["Cliente"], cus_dict["CU-24"])

    # Dependencias include / extend
    add_dependency(cus_dict["CU-01"], cus_dict["CU-03"], "include")
    add_dependency(cus_dict["CU-03"], cus_dict["CU-02"], "include")
    add_dependency(cus_dict["CU-05"], cus_dict["CU-04"], "include")
    add_dependency(cus_dict["CU-07"], cus_dict["CU-06"], "include")

    add_dependency(cus_dict["CU-23"], cus_dict["CU-06"], "extend")
    add_dependency(cus_dict["CU-24"], cus_dict["CU-06"], "extend")
    add_dependency(cus_dict["CU-25"], cus_dict["CU-06"], "extend")

    diag_gen.StyleEx = "HideQuals=1;DocAll=0;"
    diag_gen.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
    diag_gen.DiagramObjects.Refresh()
    diag_gen.Update()

    # Exportar Diagrama General desde Enterprise Architect
    ea_gen_png = os.path.join(OUT_DIR, "ea_diagrama_casos_uso_etapa1.png")
    gen_exported = project.PutDiagramImageToFile(diag_gen.DiagramGUID, ea_gen_png, 1)
    print(f"   -> Diagrama General exportado ({ea_gen_png}): {gen_exported}")

    # ---------------------------------------------------------
    # 6. DIAGRAMAS TIPO 2: Diagramas Individuales por Caso de Uso
    # ---------------------------------------------------------
    print("4. Generando Diagramas Individuales por Caso de Uso (Tipo 2) en Enterprise Architect...")

    for cu_info in CUS_ETAPA1:
        cu_code = cu_info["code"]
        cu_el = cus_dict[cu_code]
        # Título limpio para el marco del diagrama (sin prefijo redundante)
        diag_name = f"{cu_code} {cu_info['name'].split(': ')[-1]}"

        # Se crean en main_pkg para que compartan el mismo paquete y no aparezca '(from ...)'
        diag_ind = main_pkg.Diagrams.AddNew(diag_name, "Use Case")
        diag_ind.StyleEx = "HideQuals=1;DocAll=0;"
        diag_ind.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
        diag_ind.Update()
        main_pkg.Diagrams.Refresh()

        # NOTA CLAVE: NO se agrega un elemento 'Boundary' interno.
        # Al omitir el Boundary interno, el diagrama contiene únicamente los actores y el caso de uso.
        # De esta manera, cuando Enterprise Architect exporta o el usuario copia el diagrama,
        # se genera un ÚNICO marco formal de diagrama UML (con pestaña 'uc [Nombre]') sin ningún doble encuadro.

        num_actors = len(cu_info["actors"])
        if num_actors == 1:
            # Actor a la izquierda
            act_name = cu_info["actors"][0]
            act_el = actors_dict[act_name]
            a_obj = diag_ind.DiagramObjects.AddNew("l=80;r=160;t=-70;b=-190;", "")
            a_obj.ElementID = act_el.ElementID
            a_obj.Update()

            # Caso de Uso a la derecha
            cu_obj = diag_ind.DiagramObjects.AddNew("l=300;r=550;t=-90;b=-170;", "")
            cu_obj.ElementID = cu_el.ElementID
            cu_obj.Update()

            # Asegurar conector de asociación
            con_ind = act_el.Connectors.AddNew("", "Association")
            con_ind.SupplierID = cu_el.ElementID
            con_ind.Update()

        elif num_actors == 2:
            # Actor 1 a la izquierda
            act1_name = cu_info["actors"][0]
            act1_el = actors_dict[act1_name]
            a1_obj = diag_ind.DiagramObjects.AddNew("l=80;r=160;t=-70;b=-190;", "")
            a1_obj.ElementID = act1_el.ElementID
            a1_obj.Update()

            # Caso de Uso al centro
            cu_obj = diag_ind.DiagramObjects.AddNew("l=280;r=530;t=-90;b=-170;", "")
            cu_obj.ElementID = cu_el.ElementID
            cu_obj.Update()

            # Actor 2 a la derecha
            act2_name = cu_info["actors"][1]
            act2_el = actors_dict[act2_name]
            a2_obj = diag_ind.DiagramObjects.AddNew("l=650;r=730;t=-70;b=-190;", "")
            a2_obj.ElementID = act2_el.ElementID
            a2_obj.Update()

            # Asegurar conectores de asociación
            con1 = act1_el.Connectors.AddNew("", "Association")
            con1.SupplierID = cu_el.ElementID
            con1.Update()

            con2 = act2_el.Connectors.AddNew("", "Association")
            con2.SupplierID = cu_el.ElementID
            con2.Update()

        diag_ind.DiagramObjects.Refresh()
        diag_ind.Update()

        # Exportar imagen individual nativa desde Enterprise Architect
        ea_ind_png = os.path.join(INDIV_DIR, f"ea_{cu_info['filename']}")
        # También sobreescribir el archivo estándar para sincronización directa
        std_ind_png = os.path.join(INDIV_DIR, cu_info["filename"])

        ind_exported = project.PutDiagramImageToFile(diag_ind.DiagramGUID, ea_ind_png, 1)
        shutil.copy2(ea_ind_png, std_ind_png)
        print(f"   -> {cu_code}: exportado {ea_ind_png} ({ind_exported})")

    # Copiar también el diagrama general exportado a la ruta estándar
    shutil.copy2(ea_gen_png, os.path.join(OUT_DIR, "diagrama_casos_uso_etapa1.png"))

    rep.CloseFile()
    rep.Exit()
    print("=" * 70)
    print("PROYECTO ENTERPRISE ARCHITECT CREADO Y SINCRONIZADO EXITOSAMENTE!")
    print(f"Archivo EA: {NEW_EAP}")
    print("=" * 70)

if __name__ == "__main__":
    build_enterprise_architect_project()
