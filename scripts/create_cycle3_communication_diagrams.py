"""Script para generar los 5 Diagramas de Comunicación / Colaboración (Análisis de Robustez BCE)
para los Casos de Uso del Ciclo 3 en Enterprise Architect (UML 2.5).

Formato idéntico a la plantilla de referencia (media_1789870013037.jpg):
- Marco UML 2.5 con etiqueta pentagonal 'sd CUxx [Nombre]'
- 4 elementos horizontales: Actor -> Boundary (|O) -> Control (@->) -> Entity (O_)
- Un solo conector directo con flecha hacia la derecha entre cada elemento
- Bloque de texto multilínea formateado sobre cada conector con firmas y parámetros realistas
- Sin cajas de borde en los mensajes
- Exportación directa a PNG de alta resolución
"""

import os
import sys
from pathlib import Path
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

USE_CASES = [
    {
        "id": "CU12",
        "name": "CU12 Sesion de Probador Virtual",
        "filename": "comunicacion-cu12-sesion-probador-virtual.png",
        "actor": "Cliente",
        "boundary": "UI_VestidorVirtual",
        "control": "VestidorVirtualController",
        "entity": "SesionVestidorVirtual",
        "msg_link1": (
            "1: iniciarSesionProbador(cliente_id, dispositivo)\n"
            "2: seleccionarPrenda(prenda_id, talla)\n"
            "3: procesarAjusteVirtual(pose_data)\n"
            "4: finalizarSesionProbador(sesion_id)"
        ),
        "msg_link2": (
            "1.1: iniciarSesion(cliente_id, dispositivo)\n"
            "2.1: cargarModeloPrenda(prenda_id, talla)\n"
            "3.1: calcularAjuste(pose_data)\n"
            "4.1: cerrarSesion(sesion_id)"
        ),
        "msg_link3": (
            "1.2: createSession(cliente_id, dispositivo)\n"
            "1.3: save(sesion)\n"
            "2.2: findByPrendaId(prenda_id)\n"
            "3.2: updatePuntosClave(pose_data)\n"
            "4.2: findById(sesion_id)\n"
            "4.3: setEstado(\"FINALIZADA\")"
        ),
    },
    {
        "id": "CU20",
        "name": "CU20 Gestionar Promociones",
        "filename": "comunicacion-cu20-gestionar-promociones.png",
        "actor": "Administrador",
        "boundary": "UI_Promocion",
        "control": "PromocionController",
        "entity": "Promocion",
        "msg_link1": (
            "1: consultarPromociones(filtro)\n"
            "2: registrarPromocion(solicitud)\n"
            "3: modificarPromocion(id, solicitud)\n"
            "4: cambiarEstadoPromocion(id, estado)"
        ),
        "msg_link2": (
            "1.1: listarPromociones(filtro)\n"
            "2.1: crearPromocion(solicitud)\n"
            "3.1: actualizarPromocion(id, solicitud)\n"
            "4.1: modificarEstado(id, estado)"
        ),
        "msg_link3": (
            "1.2: buscarConFiltros(filtro)\n"
            "2.2: validarVigencia(fechas)\n"
            "2.3: save(promocion)\n"
            "3.2: findById(id)\n"
            "3.3: update(promocion)\n"
            "4.2: findById(id)\n"
            "4.3: setEstado(estado)"
        ),
    },
    {
        "id": "CU21",
        "name": "CU21 Gestionar Reportes y Dashboards",
        "filename": "comunicacion-cu21-gestionar-reportes.png",
        "actor": "Administrador",
        "boundary": "UI_Reporte",
        "control": "ReporteController",
        "entity": "Reporte",
        "msg_link1": (
            "1: consultarDashboard(periodo, sucursal_id)\n"
            "2: filtrarPorCategoria(categoria_id)\n"
            "3: exportarReporteExcel(tipo, periodo)\n"
            "4: exportarReportePDF(tipo, periodo)"
        ),
        "msg_link2": (
            "1.1: resumenDashboard(periodo, sucursal_id)\n"
            "2.1: filtrarMetricas(categoria_id)\n"
            "3.1: generarExcel(tipo, periodo)\n"
            "4.1: generarPdf(tipo, periodo)"
        ),
        "msg_link3": (
            "1.2: calcularMetricasVentas(periodo)\n"
            "1.3: queryVentasPorSucursal(sucursal_id)\n"
            "2.2: queryProductosMasVendidos(categoria_id)\n"
            "3.2: buildExcelWorkbook(datos)\n"
            "4.2: renderPdfDocument(datos)"
        ),
    },
    {
        "id": "CU22",
        "name": "CU22 Obtener Recomendaciones con IA",
        "filename": "comunicacion-cu22-obtener-recomendaciones-ia.png",
        "actor": "Cliente",
        "boundary": "UI_Recomendacion",
        "control": "RecomendacionController",
        "entity": "RecomendacionIA",
        "msg_link1": (
            "1: solicitarRecomendaciones(cliente_id)\n"
            "2: filtrarPorTemporada(temporada_id)\n"
            "3: verDetalleRecomendado(producto_id)\n"
            "4: registrarInteraccion(feedback_data)"
        ),
        "msg_link2": (
            "1.1: obtenerRecomendaciones(cliente_id)\n"
            "2.1: filtrarCatalogoRecomendado(temporada_id)\n"
            "3.1: consultarDetalleProducto(producto_id)\n"
            "4.1: registrarFeedback(feedback_data)"
        ),
        "msg_link3": (
            "1.2: calcularAfinidades(cliente_id)\n"
            "1.3: rankCatalogByStock()\n"
            "2.2: filterByTemporada(temporada_id)\n"
            "3.2: findById(producto_id)\n"
            "4.2: save(interaccion)\n"
            "4.3: updateScoreModel(feedback_data)"
        ),
    },
    {
        "id": "CU23",
        "name": "CU23 Consultar Historial de Compras",
        "filename": "comunicacion-cu23-consultar-historial-compras.png",
        "actor": "Cliente",
        "boundary": "UI_HistorialCompras",
        "control": "HistorialComprasController",
        "entity": "Venta",
        "msg_link1": (
            "1: consultarCompras(cliente_id, filtro)\n"
            "2: verDetalleCompra(venta_id)\n"
            "3: descargarComprobante(pago_id)\n"
            "4: filtrarPorEstado(estado)"
        ),
        "msg_link2": (
            "1.1: listarComprasCliente(cliente_id, filtro)\n"
            "2.1: obtenerDetalleVenta(venta_id)\n"
            "3.1: generarComprobante(pago_id)\n"
            "4.1: filtrarVentas(estado)"
        ),
        "msg_link3": (
            "1.2: findByClienteId(cliente_id)\n"
            "1.3: buscarConFiltros(filtro)\n"
            "2.2: findById(venta_id)\n"
            "2.3: getDetallesVenta(venta_id)\n"
            "3.2: getPaymentDetails(pago_id)\n"
            "4.2: filterByEstado(estado)"
        ),
    },
]

def main():
    print("=" * 70)
    print("GENERADOR DE DIAGRAMAS DE COMUNICACIÓN UML 2.5 (CICLO 3)")
    print("=" * 70)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir el modelo {MODEL_PATH}")
        return 1

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    pkg_name = "03 - Diagramas de Comunicación (Ciclo 3)"
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

    # Element cache para reutilizar Actor si corresponde
    elements_cache = {}

    def get_or_create_element(name, elem_type, stereotype=""):
        key = f"{name}_{elem_type}_{stereotype}"
        if key in elements_cache:
            return elements_cache[key]
        
        el = target_pkg.Elements.AddNew(name, elem_type)
        if stereotype:
            el.Stereotype = stereotype
        el.Update()
        elements_cache[key] = el
        return el

    for uc in USE_CASES:
        print(f"\nGenerando: {uc['name']}...")

        # 1. Crear diagrama de comunicación
        diag = target_pkg.Diagrams.AddNew(uc["name"], "Communication")
        diag.Update()
        target_pkg.Diagrams.Refresh()

        # Marco UML 2.5
        diag.StyleEx = "ShowFrame=1;"
        diag.Update()

        # 2. Crear elementos BCE
        actor = get_or_create_element(uc["actor"], "Actor")
        boundary = get_or_create_element(uc["boundary"], "Class", "boundary")
        control = get_or_create_element(uc["control"], "Class", "control")
        entity = get_or_create_element(uc["entity"], "Class", "entity")

        # 3. Disposición horizontal alineada
        elements_layout = [
            (actor, 50, 130, -100, -180),
            (boundary, 380, 470, -100, -180),
            (control, 720, 810, -100, -180),
            (entity, 1060, 1150, -100, -180),
        ]

        for el, l, r, t, b in elements_layout:
            obj = diag.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.left = l
            obj.right = r
            obj.top = t
            obj.bottom = b
            obj.Update()

        # 4. Conectores simples dirigidos de izquierda a derecha (Source -> Destination)
        def add_directed_connector(src, dst):
            conn = src.Connectors.AddNew("", "Association")
            conn.SupplierID = dst.ElementID
            conn.Direction = "Source -> Destination"
            conn.Update()

            lnk = diag.DiagramLinks.AddNew("", "")
            lnk.ConnectorID = conn.ConnectorID
            lnk.Update()
            return conn

        add_directed_connector(actor, boundary)
        add_directed_connector(boundary, control)
        add_directed_connector(control, entity)

        # 5. Textos multilínea sobre cada conector (sin bordes)
        # Texto 1: Actor -> Boundary
        t1 = target_pkg.Elements.AddNew(uc["msg_link1"], "Text")
        t1.Notes = uc["msg_link1"]
        t1.Update()
        obj_t1 = diag.DiagramObjects.AddNew("", "")
        obj_t1.ElementID = t1.ElementID
        obj_t1.left = 140
        obj_t1.right = 375
        obj_t1.top = -30
        obj_t1.bottom = -115
        obj_t1.Update()

        # Texto 2: Boundary -> Control
        t2 = target_pkg.Elements.AddNew(uc["msg_link2"], "Text")
        t2.Notes = uc["msg_link2"]
        t2.Update()
        obj_t2 = diag.DiagramObjects.AddNew("", "")
        obj_t2.ElementID = t2.ElementID
        obj_t2.left = 480
        obj_t2.right = 715
        obj_t2.top = -30
        obj_t2.bottom = -115
        obj_t2.Update()

        # Texto 3: Control -> Entity
        t3 = target_pkg.Elements.AddNew(uc["msg_link3"], "Text")
        t3.Notes = uc["msg_link3"]
        t3.Update()
        obj_t3 = diag.DiagramObjects.AddNew("", "")
        obj_t3.ElementID = t3.ElementID
        obj_t3.left = 820
        obj_t3.right = 1055
        obj_t3.top = -15
        obj_t3.bottom = -115
        obj_t3.Update()

        diag.Update()
        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()

        # 6. Exportar imagen PNG
        export_path = os.path.join(EXPORT_DIR, uc["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, export_path, 1)
        print(f"  -> Exportado: {export_path}")

    rep.CloseFile()
    print("\n" + "=" * 70)
    print("TODOS LOS DIAGRAMAS DE COMUNICACIÓN FUERON GENERADOS EXITOSAMENTE")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
