# -*- coding: utf-8 -*-
"""
Script para generar el Diagrama General de Casos de Uso (Segundo Parcial Completo - 26 CUs)
directamente en Sparx Enterprise Architect (CasosDeUso_SegundoParcial.eap).
"""

import os
import shutil
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
BACKUP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.backup.eap"
OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"
os.makedirs(OUT_DIR, exist_ok=True)

# Lista Oficial de los 26 Casos de Uso del Segundo Parcial
CUS_P2 = [
    # --- ETAPA 1 ---
    {
        "code": "CU-01",
        "name": "CU-01: Registrar Empresa Contratante (Tenant)",
        "etapa": 1,
        "actors": ["Superadmin SaaS"],
        "pos": "l=260;r=470;t=-100;b=-180;"
    },
    {
        "code": "CU-03",
        "name": "CU-03: Asignar y Renovar Suscripción de Empresa",
        "etapa": 1,
        "actors": ["Superadmin SaaS", "Tenant Admin"],
        "pos": "l=510;r=720;t=-100;b=-180;"
    },
    {
        "code": "CU-02",
        "name": "CU-02: Gestionar Planes de Suscripción",
        "etapa": 1,
        "actors": ["Superadmin SaaS"],
        "pos": "l=510;r=720;t=-210;b=-290;"
    },
    {
        "code": "CU-05",
        "name": "CU-05: Gestionar Sucursales y Empleados por Tenant",
        "etapa": 1,
        "actors": ["Tenant Admin"],
        "pos": "l=260;r=470;t=-250;b=-330;"
    },
    {
        "code": "CU-04",
        "name": "CU-04: Controlar Límites y Restricciones por Plan",
        "etapa": 1,
        "actors": ["Tenant Admin", "Actores de Sistema"],
        "pos": "l=510;r=720;t=-340;b=-420;"
    },
    {
        "code": "CU-07",
        "name": "CU-07: Consultar Catálogo y Existencias Offline",
        "etapa": 1,
        "actors": ["Cajero / Vendedor", "Cliente"],
        "pos": "l=260;r=470;t=-460;b=-540;"
    },
    {
        "code": "CU-06",
        "name": "CU-06: Descargar y Almacenar Catálogo Offline",
        "etapa": 1,
        "actors": ["Cajero / Vendedor", "Cliente"],
        "pos": "l=510;r=720;t=-460;b=-540;"
    },
    {
        "code": "CU-23",
        "name": "CU-23: Notificar Estado de Conectividad (Semáforo)",
        "etapa": 1,
        "actors": ["Cajero / Vendedor", "Actores de Sistema"],
        "pos": "l=510;r=720;t=-580;b=-660;"
    },
    {
        "code": "CU-24",
        "name": "CU-24: Instalar y Registrar Service Worker (PWA)",
        "etapa": 1,
        "actors": ["Cliente"],
        "pos": "l=260;r=470;t=-670;b=-750;"
    },
    {
        "code": "CU-25",
        "name": "CU-25: Configurar y Migrar Persistencia SQLite Móvil",
        "etapa": 1,
        "actors": ["Cajero / Vendedor", "Actores de Sistema"],
        "pos": "l=510;r=720;t=-720;b=-800;"
    },

    # --- ETAPA 2 ---
    {
        "code": "CU-22",
        "name": "CU-22: Gestionar Datos Mínimos de Clientes Offline",
        "etapa": 2,
        "actors": ["Cajero / Vendedor"],
        "pos": "l=800;r=1010;t=-100;b=-180;"
    },
    {
        "code": "CU-08",
        "name": "CU-08: Registrar Venta de Contado Offline",
        "etapa": 2,
        "actors": ["Cajero / Vendedor"],
        "pos": "l=1060;r=1270;t=-100;b=-180;"
    },
    {
        "code": "CU-09",
        "name": "CU-09: Registrar Reserva de Prendas Offline",
        "etapa": 2,
        "actors": ["Cajero / Vendedor", "Cliente"],
        "pos": "l=1060;r=1270;t=-220;b=-300;"
    },
    {
        "code": "CU-10",
        "name": "CU-10: Consultar Operaciones Locales Pendientes (Outbox)",
        "etapa": 2,
        "actors": ["Cajero / Vendedor"],
        "pos": "l=800;r=1010;t=-310;b=-390;"
    },
    {
        "code": "CU-11",
        "name": "CU-11: Sincronizar Operaciones con el Servidor",
        "etapa": 2,
        "actors": ["Cajero / Vendedor", "Actores de Sistema"],
        "pos": "l=1060;r=1270;t=-430;b=-510;"
    },
    {
        "code": "CU-12",
        "name": "CU-12: Gestionar Conflictos de Sincronización",
        "etapa": 2,
        "actors": ["Cajero / Vendedor", "Tenant Admin", "Administrador de Sucursal"],
        "pos": "l=800;r=1010;t=-530;b=-610;"
    },
    {
        "code": "CU-13",
        "name": "CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)",
        "etapa": 2,
        "actors": ["Cajero / Vendedor", "Administrador de Sucursal", "Cliente"],
        "pos": "l=930;r=1150;t=-670;b=-750;"
    },

    # --- ETAPA 3 ---
    {
        "code": "CU-14",
        "name": "CU-14: Solicitar Reporte por Lenguaje Natural (Texto/Voz)",
        "etapa": 3,
        "actors": ["Tenant Admin"],
        "pos": "l=1350;r=1560;t=-100;b=-180;"
    },
    {
        "code": "CU-15",
        "name": "CU-15: Interpretar Consulta Analítica (Text-to-SQL)",
        "etapa": 3,
        "actors": ["Tenant Admin", "Actores de Sistema"],
        "pos": "l=1610;r=1820;t=-100;b=-180;"
    },
    {
        "code": "CU-16",
        "name": "CU-16: Visualizar Reporte Dinámico (Tablas y Gráficos)",
        "etapa": 3,
        "actors": ["Tenant Admin"],
        "pos": "l=1610;r=1820;t=-220;b=-300;"
    },
    {
        "code": "CU-17",
        "name": "CU-17: Exportar Reporte a Excel y PDF",
        "etapa": 3,
        "actors": ["Tenant Admin"],
        "pos": "l=1610;r=1820;t=-340;b=-420;"
    },
    {
        "code": "CU-18",
        "name": "CU-18: Generar Dataset Sintético de Entrenamiento",
        "etapa": 3,
        "actors": ["Tenant Admin", "Actores de Sistema"],
        "pos": "l=1350;r=1560;t=-460;b=-540;"
    },
    {
        "code": "CU-19",
        "name": "CU-19: Entrenar y Evaluar Modelo Supervisado (Demanda)",
        "etapa": 3,
        "actors": ["Tenant Admin"],
        "pos": "l=1610;r=1820;t=-460;b=-540;"
    },
    {
        "code": "CU-20",
        "name": "CU-20: Entrenar Modelo No Supervisado (Clustering RFM)",
        "etapa": 3,
        "actors": ["Tenant Admin"],
        "pos": "l=1610;r=1820;t=-570;b=-650;"
    },
    {
        "code": "CU-21",
        "name": "CU-21: Visualizar Dashboard Analítico Inteligente",
        "etapa": 3,
        "actors": ["Tenant Admin"],
        "pos": "l=1350;r=1560;t=-670;b=-750;"
    },
    {
        "code": "CU-26",
        "name": "CU-26: Gestionar Devolución y Reposición de Prendas",
        "etapa": 3,
        "actors": ["Cajero / Vendedor", "Administrador de Sucursal", "Cliente"],
        "pos": "l=1480;r=1700;t=-780;b=-860;"
    }
]

ACTORS_LIST = [
    {"name": "Superadmin SaaS", "pos": "l=80;r=160;t=-120;b=-240;"},
    {"name": "Tenant Admin", "pos": "l=80;r=160;t=-440;b=-560;"},
    {"name": "Administrador de Sucursal", "pos": "l=80;r=160;t=-740;b=-860;"},
    {"name": "Cajero / Vendedor", "pos": "l=1940;r=2020;t=-120;b=-240;"},
    {"name": "Cliente", "pos": "l=1940;r=2020;t=-440;b=-560;"},
    {"name": "Actores de Sistema", "pos": "l=1940;r=2020;t=-740;b=-860;"},
]

INCLUDES = [
    ("CU-01", "CU-03"),
    ("CU-03", "CU-02"),
    ("CU-05", "CU-04"),
    ("CU-07", "CU-06"),
    ("CU-08", "CU-07"),
    ("CU-08", "CU-22"),
    ("CU-09", "CU-22"),
    ("CU-08", "CU-10"),
    ("CU-09", "CU-10"),
    ("CU-11", "CU-10"),
    ("CU-14", "CU-15"),
    ("CU-14", "CU-04"),
    ("CU-15", "CU-16"),
    ("CU-19", "CU-18"),
    ("CU-20", "CU-18"),
    ("CU-21", "CU-19"),
    ("CU-21", "CU-20"),
]

EXTENDS = [
    ("CU-23", "CU-06"),
    ("CU-24", "CU-06"),
    ("CU-25", "CU-06"),
    ("CU-12", "CU-11"),
    ("CU-23", "CU-11"),
    ("CU-17", "CU-16"),
]

def build_diagram():
    print(f"Copia de seguridad del modelo EA: {BACKUP_PATH}...")
    shutil.copy2(EAP_PATH, BACKUP_PATH)

    rep = win32com.client.Dispatch("EA.Repository")
    print(f"Abriendo repositorio EA: {EAP_PATH}...")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    pkg_name = "01 - Diagrama General de Casos de Uso (26 CUs - Segundo Parcial)"
    
    # Buscar si ya existe el paquete
    target_pkg = None
    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            target_pkg = p
            break
            
    if target_pkg is None:
        print(f"Creando nuevo paquete en EA: '{pkg_name}'...")
        target_pkg = root_model.Packages.AddNew(pkg_name, "")
        target_pkg.Notes = "Diagrama General de Casos de Uso del Segundo Parcial (26 CUs oficiales, 6 actores y relaciones ICONIX)."
        target_pkg.Update()
        root_model.Packages.Refresh()

    # 1. Crear o recuperar Actores
    print("Creando / recuperando actores en el paquete...")
    actors_dict = {}
    for act_info in ACTORS_LIST:
        act_name = act_info["name"]
        found = None
        for el in target_pkg.Elements:
            if el.Name == act_name and el.Type == "Actor":
                found = el
                break
        if not found:
            found = target_pkg.Elements.AddNew(act_name, "Actor")
            found.Notes = f"Actor: {act_name}"
            found.Update()
        actors_dict[act_name] = found
    target_pkg.Elements.Refresh()

    # 2. Crear o recuperar Casos de Uso
    print("Creando / recuperando los 26 Casos de Uso en el paquete...")
    cus_dict = {}
    for cu in CUS_P2:
        cu_code = cu["code"]
        cu_name = cu["name"]
        found = None
        for el in target_pkg.Elements:
            if el.Type == "UseCase" and (el.Name == cu_name or el.Name.startswith(cu_code)):
                found = el
                break
        if not found:
            found = target_pkg.Elements.AddNew(cu_name, "UseCase")
            found.Notes = f"Caso de uso {cu_code} correspondiente a la Etapa {cu['etapa']} del Segundo Parcial."
            found.Update()
        cus_dict[cu_code] = found
    target_pkg.Elements.Refresh()

    # 3. Crear o actualizar el Diagrama General
    diag_title = "Diagrama General de Casos de Uso - Segundo Parcial (Completo)"
    print(f"Configurando diagrama de casos de uso: '{diag_title}'...")
    diag = None
    for d in target_pkg.Diagrams:
        if d.Name == diag_title:
            diag = d
            break
            
    if diag is None:
        diag = target_pkg.Diagrams.AddNew(diag_title, "Use Case")
        diag.Notes = "Diagrama general oficial del Segundo Parcial con los 26 casos de uso y 6 actores formalizados."
        diag.Update()
        target_pkg.Diagrams.Refresh()

    # Limpiar objetos previos del diagrama para asegurar disposición impecable
    while diag.DiagramObjects.Count > 0:
        diag.DiagramObjects.Delete(0)
    diag.DiagramObjects.Refresh()

    # 4. Crear Elemento Boundary (Límite del Sistema)
    bound_name = "FashionStore SaaS — Segundo Parcial (Multitenant, Offline y Analítica IA)"
    boundary_el = None
    for el in target_pkg.Elements:
        if el.Type == "Boundary" and el.Name == bound_name:
            boundary_el = el
            break
    if not boundary_el:
        boundary_el = target_pkg.Elements.AddNew(bound_name, "Boundary")
        boundary_el.Update()
        target_pkg.Elements.Refresh()

    # Colocar Boundary en el diagrama
    bo = diag.DiagramObjects.AddNew("l=220;r=1870;t=-40;b=-940;", "")
    bo.ElementID = boundary_el.ElementID
    bo.Update()

    # 5. Colocar Actores en el diagrama
    for act_info in ACTORS_LIST:
        ao = diag.DiagramObjects.AddNew(act_info["pos"], "")
        ao.ElementID = actors_dict[act_info["name"]].ElementID
        ao.Update()

    # 6. Colocar Casos de Uso en el diagrama
    for cu in CUS_P2:
        co = diag.DiagramObjects.AddNew(cu["pos"], "")
        co.ElementID = cus_dict[cu["code"]].ElementID
        co.Update()

    # 7. Crear Conectores de Asociación entre Actores y Casos de Uso
    print("Creando asociaciones entre actores y casos de uso...")
    def add_assoc(actor_el, cu_el):
        for c in actor_el.Connectors:
            if c.SupplierID == cu_el.ElementID and c.Type == "Association":
                return
        con = actor_el.Connectors.AddNew("", "Association")
        con.SupplierID = cu_el.ElementID
        con.Update()
        actor_el.Connectors.Refresh()

    def add_dep(src_el, tgt_el, st_type):
        for c in src_el.Connectors:
            if c.SupplierID == tgt_el.ElementID and c.Stereotype == st_type:
                return
        con = src_el.Connectors.AddNew("", "UseCase")
        con.Stereotype = st_type
        con.SupplierID = tgt_el.ElementID
        con.Update()
        src_el.Connectors.Refresh()

    for cu in CUS_P2:
        cu_el = cus_dict[cu["code"]]
        for act_name in cu["actors"]:
            act_el = actors_dict[act_name]
            add_assoc(act_el, cu_el)

    # 8. Crear Dependencias include y extend
    print("Creando relaciones <<include>> y <<extend>>...")
    for src, tgt in INCLUDES:
        add_dep(cus_dict[src], cus_dict[tgt], "include")

    for src, tgt in EXTENDS:
        add_dep(cus_dict[src], cus_dict[tgt], "extend")

    diag.StyleEx = "HideQuals=1;DocAll=0;"
    diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
    diag.DiagramObjects.Refresh()
    diag.Update()
    target_pkg.Update()

    # 9. Exportar la imagen PNG nativa desde Enterprise Architect
    out_png = os.path.join(OUT_DIR, "ea_diagrama_general_casos_uso_segundo_parcial.png")
    exported = project.PutDiagramImageToFile(diag.DiagramGUID, out_png, 1)
    print(f"Exportación de imagen desde EA: {out_png} -> Resultado: {exported}")

    rep.CloseFile()
    rep.Exit()
    print("=" * 70)
    print("DIAGRAMA EN ENTERPRISE ARCHITECT CREADO EXITOSAMENTE!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name}")
    print(f"Diagrama EA: {diag_title}")
    print(f"Imagen exportada (para tu uso): {out_png}")
    print("=" * 70)

if __name__ == "__main__":
    build_diagram()
