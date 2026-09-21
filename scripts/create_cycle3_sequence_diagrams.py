"""Script para generar los 5 Diagramas de Secuencia del Ciclo 3 en Enterprise Architect (UML 2.5).

Basado exactamente en el modelo de referencia (media_1789874263660.jpg):
- Marco UML 2.5 con etiqueta pentagonal 'sd CUxx [Nombre]'
- Participantes: Actor -> Vistas (V.xxx) -> Controller (xxxController) -> Modelos (M.xxx)
- Fragmentos combinados ('alt') que dividen los flujos principales del CU
- Mensajes de llamada síncronos (línea continua con flecha cerrada)
- Mensajes de retorno 'return()' (línea discontinua con flecha abierta)
- Llamadas 'view()' a las vistas correspondientes
- Exportación a PNG de alta resolución
"""

import os
import sys
from pathlib import Path
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

USE_CASES_SEQUENCE = [
    {
        "id": "CU12",
        "diagram_name": "CU12 Sesion de Probador Virtual",
        "filename": "secuencia-cu12-sesion-probador-virtual.png",
        "actor": "Cliente",
        "views": ["V.index", "V.CapturaPose", "V.ResultadoVTON"],
        "controller": "VestidorVirtualController",
        "models": ["M.SesionVestidorVirtual", "M.Prenda", "M.Bitacora"],
        "fragments": [
            {
                "name": "iniciar",
                "top": -100,
                "bottom": -220,
                "messages": [
                    ("actor", "controller", "start_session()", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "seleccionarPrenda",
                "top": -230,
                "bottom": -370,
                "messages": [
                    ("actor", "controller", "selectPrenda()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "procesarAjusteVTON",
                "top": -380,
                "bottom": -620,
                "messages": [
                    ("actor", "controller", "vton_try_on()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "finalizar",
                "top": -630,
                "bottom": -770,
                "messages": [
                    ("actor", "controller", "finish_session()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU20",
        "diagram_name": "CU20 Gestionar Promociones y Descuentos",
        "filename": "secuencia-cu20-gestionar-promociones.png",
        "actor": "Administrador",
        "views": ["V.index", "V.CrearPromocion", "V.DetallePromocion"],
        "controller": "PromocionController",
        "models": ["M.Promocion", "M.ProductoPromocion", "M.Bitacora"],
        "fragments": [
            {
                "name": "listar",
                "top": -100,
                "bottom": -220,
                "messages": [
                    ("actor", "controller", "index()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "registrar",
                "top": -230,
                "bottom": -470,
                "messages": [
                    ("actor", "controller", "store()", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m2", "create()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "modificar",
                "top": -480,
                "bottom": -670,
                "messages": [
                    ("actor", "controller", "update()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cambiarEstado",
                "top": -680,
                "bottom": -800,
                "messages": [
                    ("actor", "controller", "set_status()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU21",
        "diagram_name": "CU21 Gestionar Reportes y Dashboards",
        "filename": "secuencia-cu21-gestionar-reportes.png",
        "actor": "Administrador",
        "views": ["V.Dashboard", "V.FiltrosReporte", "V.AsistenteIA"],
        "controller": "ReporteController",
        "models": ["M.Reporte", "M.Venta", "M.Bitacora"],
        "fragments": [
            {
                "name": "consultarDashboard",
                "top": -100,
                "bottom": -270,
                "messages": [
                    ("actor", "controller", "dashboard()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "filtrarPorSucursal",
                "top": -280,
                "bottom": -420,
                "messages": [
                    ("actor", "controller", "sales_by_branch()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "asistenteIA",
                "top": -430,
                "bottom": -570,
                "messages": [
                    ("actor", "controller", "report_assistant()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "exportar",
                "top": -580,
                "bottom": -770,
                "messages": [
                    ("actor", "controller", "export_report()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                ],
            },
        ],
    },
    {
        "id": "CU22",
        "diagram_name": "CU22 Obtener Recomendaciones con IA",
        "filename": "secuencia-cu22-obtener-recomendaciones-ia.png",
        "actor": "Cliente",
        "views": ["V.CatalogoRecomendado", "V.DetalleRecomendacion", "V.FeedbackModal"],
        "controller": "RecomendacionController",
        "models": ["M.RecomendacionIA", "M.Prenda", "M.HistorialCliente"],
        "fragments": [
            {
                "name": "solicitarRecomendaciones",
                "top": -100,
                "bottom": -320,
                "messages": [
                    ("actor", "controller", "mine()", False),
                    ("controller", "m3", "get()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "filtrarPorTemporada",
                "top": -330,
                "bottom": -470,
                "messages": [
                    ("actor", "controller", "filterBySeason()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "verDetalle",
                "top": -480,
                "bottom": -620,
                "messages": [
                    ("actor", "controller", "selectProduct()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "registrarFeedback",
                "top": -630,
                "bottom": -770,
                "messages": [
                    ("actor", "controller", "record_feedback()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU23",
        "diagram_name": "CU23 Consultar Historial de Compras",
        "filename": "secuencia-cu23-consultar-historial-compras.png",
        "actor": "Cliente",
        "views": ["V.HistorialCompras", "V.DetalleCompra", "V.ComprobanteDigital"],
        "controller": "HistorialComprasController",
        "models": ["M.Venta", "M.DetalleVenta", "M.Pago"],
        "fragments": [
            {
                "name": "listarCompras",
                "top": -100,
                "bottom": -240,
                "messages": [
                    ("actor", "controller", "purchase_history()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "verDetalleCompra",
                "top": -250,
                "bottom": -450,
                "messages": [
                    ("actor", "controller", "purchase_detail()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "descargarComprobante",
                "top": -460,
                "bottom": -600,
                "messages": [
                    ("actor", "controller", "download_receipt()", False),
                    ("controller", "m3", "get()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "solicitarDevolucion",
                "top": -610,
                "bottom": -750,
                "messages": [
                    ("actor", "controller", "return_sale()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
        ],
    },
]

def main():
    print("=" * 70)
    print("GENERADOR DE DIAGRAMAS DE SECUENCIA (CICLO 3) - UML 2.5")
    print("=" * 70)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir {MODEL_PATH}")
        return 1

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    pkg_name = "05 - Diagramas de Secuencia (Ciclo 3)"
    target_pkg = None
    target_pkg_idx = -1

    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            target_pkg = p
            target_pkg_idx = i
            break

    # Si ya existe, lo eliminamos y volvemos a crear para garantizar limpieza total
    if target_pkg is not None:
        print(f"Limpiando paquete previo '{pkg_name}'...")
        root_model.Packages.Delete(target_pkg_idx)
        root_model.Packages.Refresh()

    target_pkg = root_model.Packages.AddNew(pkg_name, "")
    target_pkg.Update()
    root_model.Packages.Refresh()

    os.makedirs(EXPORT_DIR, exist_ok=True)

    for uc in USE_CASES_SEQUENCE:
        print(f"\nGenerando: {uc['diagram_name']}...")

        # Subpaquete por Caso de Uso
        cu_pkg = target_pkg.Packages.AddNew(uc["id"], "")
        cu_pkg.Update()
        target_pkg.Packages.Refresh()

        # 1. Crear diagrama de secuencia
        diag = cu_pkg.Diagrams.AddNew(uc["diagram_name"], "Sequence")
        diag.Update()
        cu_pkg.Diagrams.Refresh()

        # Marco UML 2.5
        diag.StyleEx = "ShowFrame=1;"
        diag.Update()

        # 2. Crear elementos participantes
        # Actor
        actor = cu_pkg.Elements.AddNew(uc["actor"], "Actor")
        actor.Update()

        # Vistas
        v1 = cu_pkg.Elements.AddNew(uc["views"][0], "Sequence")
        v1.Update()
        v2 = cu_pkg.Elements.AddNew(uc["views"][1], "Sequence")
        v2.Update()
        v3 = cu_pkg.Elements.AddNew(uc["views"][2], "Sequence")
        v3.Update()

        # Controller
        ctrl = cu_pkg.Elements.AddNew(uc["controller"], "Sequence")
        ctrl.Update()

        # Modelos
        m1 = cu_pkg.Elements.AddNew(uc["models"][0], "Sequence")
        m1.Update()
        m2 = cu_pkg.Elements.AddNew(uc["models"][1], "Sequence")
        m2.Update()
        m3 = cu_pkg.Elements.AddNew(uc["models"][2], "Sequence")
        m3.Update()

        participant_map = {
            "actor": actor,
            "v1": v1,
            "v2": v2,
            "v3": v3,
            "controller": ctrl,
            "m1": m1,
            "m2": m2,
            "m3": m3,
        }

        # 3. Disposición horizontal de las líneas de vida (Lifelines)
        # Idéntica a la referencia: Actor (40), V1 (140), V2 (250), V3 (370), Controller (500), M1 (645), M2 (775), M3 (905)
        lifeline_positions = [
            (actor, 40, 130),
            (v1, 140, 230),
            (v2, 250, 355),
            (v3, 370, 480),
            (ctrl, 500, 625),
            (m1, 645, 755),
            (m2, 775, 885),
            (m3, 905, 1010),
        ]

        # Calcular altura máxima según último fragmento
        max_bottom = min(f["bottom"] for f in uc["fragments"]) - 40

        for el, left, right in lifeline_positions:
            obj = diag.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.left = left
            obj.right = right
            obj.top = -40
            obj.bottom = max_bottom
            obj.Update()

        # 4. Fragmentos combinados ('alt') y Mensajes
        seq_counter = 1

        for frag in uc["fragments"]:
            # Crear fragmento alt
            frag_el = cu_pkg.Elements.AddNew(frag["name"], "InteractionFragment")
            frag_el.Subtype = 0  # 0 = alt
            frag_el.Update()

            obj_frag = diag.DiagramObjects.AddNew("", "")
            obj_frag.ElementID = frag_el.ElementID
            obj_frag.left = 20
            obj_frag.right = 1030
            obj_frag.top = frag["top"]
            obj_frag.bottom = frag["bottom"]
            obj_frag.Update()

            # Crear mensajes dentro del fragmento
            for src_key, dst_key, msg_text, is_return in frag["messages"]:
                src = participant_map[src_key]
                dst = participant_map[dst_key]

                c = src.Connectors.AddNew(msg_text, "Sequence")
                c.SupplierID = dst.ElementID
                c.SequenceNo = seq_counter
                c.Direction = "Source -> Destination"

                if is_return:
                    # Mensaje de retorno: línea discontinua con IsReturn=1
                    c.StyleEx = "IsReturn=1;"
                c.Update()

                lnk = diag.DiagramLinks.AddNew("", "")
                lnk.ConnectorID = c.ConnectorID
                lnk.Update()

                seq_counter += 1

        diag.Update()
        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()

        # 5. Exportar imagen PNG de alta resolución
        export_path = os.path.join(EXPORT_DIR, uc["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, export_path, 1)
        print(f"  -> Exportado: {export_path}")

    rep.CloseFile()
    print("\n" + "=" * 70)
    print("TODOS LOS DIAGRAMAS DE SECUENCIA FUERON GENERADOS EXITOSAMENTE")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
