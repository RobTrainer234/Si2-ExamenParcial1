"""Script para generar los 5 Diagramas de Análisis de Clases (Análisis de Robustez Orientado a Clases)
para los Casos de Uso del Ciclo 3 en Enterprise Architect (UML 2.5).

Basado exactamente en el modelo de referencia (media_1789871652355.jpg):
- Marco UML 2.5: 'class Analizar una clase CUxx'
- Actor -> «Formulario» (Form...) -> «Class» (...Controller) -> «Entidad» Principal (E_...)
- Desde la Entidad Principal se conectan las 3 Entidades Secundarias («Entidad») con multiplicidades
- Atributos y métodos públicos (+) con tipos y parámetros limpios
- Sin solapamientos espaciales, espaciado horizontal calibrado
- Exportación a PNG de alta resolución
"""

import os
import sys
from pathlib import Path
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

USE_CASES_ANALYSIS = [
    {
        "id": "CU12",
        "diagram_name": "Analizar una clase CU12",
        "filename": "analisis-clases-cu12-sesion-probador-virtual.png",
        "actor": "Cliente",
        "form": {
            "name": "FormVestidorVirtual",
            "stereotype": "Formulario",
            "attributes": [
                ("productoId", "integer"),
                ("imagenUsuarioBase64", "string"),
                ("puntosClavePose", "string"),
                ("sesionActivaId", "integer"),
                ("dispositivoInfo", "string"),
                ("estadoSesion", "string"),
            ],
            "methods": [
                ("IniciarSesion", "void", []),
                ("CargarImagen", "void", []),
                ("SeleccionarPrenda", "void", []),
                ("SolicitarAjusteVTON", "void", []),
                ("FinalizarSesion", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "VestidorVirtualController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("start_session", "JsonResponse", []),
                ("finish_session", "JsonResponse", []),
                ("list_mine", "JsonResponse", []),
                ("vton_try_on", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_SesionVestidorVirtual",
            "stereotype": "Entidad",
            "attributes": [
                ("id_sesion", "integer"),
                ("id_cliente", "integer"),
                ("id_producto", "integer"),
                ("estado", "string"),
                ("info_dispositivo", "string"),
                ("fecha_inicio", "datetime"),
                ("fecha_fin", "datetime"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("finish", "boolean", []),
                ("vincularPrenda", "void", [("id_producto", "integer")]),
                ("validarDispositivo", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("codigo_sku", "string"),
                    ("precio_base", "decimal"),
                    ("modelo_3d_url", "string"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("obtenerModelo3D", "string", []),
                    ("verificarDisponibilidad", "boolean", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "0..*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                    ("apellido", "string"),
                    ("estado", "string"),
                ],
                "methods": [
                    ("obtenerHistorialSesiones", "list", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("tipo_entidad", "string"),
                    ("detalle", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("registrarEventoVTON", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU20",
        "diagram_name": "Analizar una clase CU20",
        "filename": "analisis-clases-cu20-gestionar-promociones.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormPromocion",
            "stereotype": "Formulario",
            "attributes": [
                ("nombre", "string"),
                ("descripcion", "string"),
                ("tipoDescuento", "string"),
                ("valorDescuento", "decimal"),
                ("fechaInicio", "datetime"),
                ("fechaFin", "datetime"),
                ("productosSeleccionados", "string"),
                ("filtroBusqueda", "string"),
                ("estado", "string"),
            ],
            "methods": [
                ("NuevaPromocion", "void", []),
                ("Guardar", "void", []),
                ("Modificar", "void", []),
                ("ActivarDesactivar", "void", []),
                ("AsignarProductos", "void", []),
                ("Cancelar", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "PromocionController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_promotions", "JsonResponse", []),
                ("create_promotion", "JsonResponse", []),
                ("get_promotion", "JsonResponse", []),
                ("update_promotion", "JsonResponse", []),
                ("activate_promotion", "JsonResponse", []),
                ("deactivate_promotion", "JsonResponse", []),
                ("set_promotion_products", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Promocion",
            "stereotype": "Entidad",
            "attributes": [
                ("id_promocion", "integer"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("tipo_descuento", "string"),
                ("valor_descuento", "decimal"),
                ("fecha_inicio", "datetime"),
                ("fecha_fin", "datetime"),
                ("activo", "boolean"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("cambiarEstado", "void", [("estado", "boolean")]),
                ("agregarProducto", "void", [("id_producto", "integer")]),
                ("removerProducto", "void", [("id_producto", "integer")]),
                ("estaVigente", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_ProductoPromocion",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_promocion", "integer"),
                    ("id_producto", "integer"),
                ],
                "methods": [
                    ("asociarPrenda", "void", []),
                    ("desasociarPrenda", "void", []),
                ],
            },
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("precio_base", "decimal"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("calcularPrecioConDescuento", "decimal", [("descuento", "decimal")]),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("tipo_entidad", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("registrarAccion", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU21",
        "diagram_name": "Analizar una clase CU21",
        "filename": "analisis-clases-cu21-gestionar-reportes.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormReporte",
            "stereotype": "Formulario",
            "attributes": [
                ("fechaDesde", "datetime"),
                ("fechaHasta", "datetime"),
                ("sucursalSeleccionada", "integer"),
                ("formatoExportacion", "string"),
                ("promptAsistenteIA", "string"),
                ("tipoMetrica", "string"),
            ],
            "methods": [
                ("ConsultarDashboard", "void", []),
                ("FiltrarPorSucursal", "void", []),
                ("FiltrarTopProductos", "void", []),
                ("ExportarExcel", "void", []),
                ("ExportarPDF", "void", []),
                ("ConsultarAsistenteIA", "void", []),
                ("LimpiarFiltros", "void", []),
            ],
        },
        "controller": {
            "name": "ReporteController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("dashboard", "JsonResponse", []),
                ("report_assistant", "JsonResponse", []),
                ("sales_by_branch", "JsonResponse", []),
                ("top_products", "JsonResponse", []),
                ("low_stock", "JsonResponse", []),
                ("revenue_summary", "JsonResponse", []),
                ("export_report", "FileResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Reporte",
            "stereotype": "Entidad",
            "attributes": [
                ("id_reporte", "integer"),
                ("titulo", "string"),
                ("periodo_inicio", "datetime"),
                ("periodo_fin", "datetime"),
                ("total_ingresos", "decimal"),
                ("total_ventas", "integer"),
                ("total_reservas", "integer"),
                ("fecha_generacion", "datetime"),
            ],
            "methods": [
                ("consolidarMetricas", "boolean", []),
                ("exportarDataset", "binary", [("formato", "string")]),
                ("consultarTopPrendas", "list", []),
                ("calcularKPIs", "dict", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Venta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_venta", "integer"),
                    ("id_sucursal", "integer"),
                    ("id_cliente", "integer"),
                    ("total", "decimal"),
                    ("estado", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("obtenerSubtotal", "decimal", []),
                ],
            },
            {
                "name": "E_Sucursal",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string"),
                    ("id_ciudad", "integer"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("consolidarPorSucursal", "dict", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("detalle", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("registrarExportacion", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU22",
        "diagram_name": "Analizar una clase CU22",
        "filename": "analisis-clases-cu22-obtener-recomendaciones-ia.png",
        "actor": "Cliente",
        "form": {
            "name": "FormRecomendacion",
            "stereotype": "Formulario",
            "attributes": [
                ("clienteId", "integer"),
                ("categoriaFiltro", "string"),
                ("temporadaFiltro", "string"),
                ("limiteProductos", "integer"),
                ("feedbackSeleccionado", "string"),
            ],
            "methods": [
                ("SolicitarRecomendaciones", "void", []),
                ("FiltrarPorTemporada", "void", []),
                ("VerDetallePrenda", "void", []),
                ("CalificarRecomendacion", "void", []),
                ("ActualizarPrendas", "void", []),
            ],
        },
        "controller": {
            "name": "RecomendacionController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("mine", "JsonResponse", []),
                ("get_recommendations_by_user", "JsonResponse", []),
                ("record_feedback", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_RecomendacionIA",
            "stereotype": "Entidad",
            "attributes": [
                ("id_recomendacion", "integer"),
                ("id_cliente", "integer"),
                ("id_producto", "integer"),
                ("origen", "string"),
                ("justificacion", "string"),
                ("puntaje_score", "decimal"),
                ("fecha_creacion", "datetime"),
                ("fecha_expiracion", "datetime"),
            ],
            "methods": [
                ("calcularScoreAfinidad", "decimal", []),
                ("verificarExpiracion", "boolean", []),
                ("registrarPuntaje", "void", [("score", "decimal")]),
                ("save", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("id_categoria", "integer"),
                    ("precio_base", "decimal"),
                    ("calificacion_promedio", "decimal"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("verificarStock", "boolean", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                    ("apellido", "string"),
                ],
                "methods": [
                    ("obtenerPreferenciasEstilo", "dict", []),
                ],
            },
            {
                "name": "E_Temporada",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_temporada", "integer"),
                    ("nombre", "string"),
                    ("fecha_inicio", "date"),
                    ("fecha_fin", "date"),
                    ("activa", "boolean"),
                ],
                "methods": [
                    ("estaVigente", "boolean", []),
                ],
            },
        ],
    },
    {
        "id": "CU23",
        "diagram_name": "Analizar una clase CU23",
        "filename": "analisis-clases-cu23-consultar-historial-compras.png",
        "actor": "Cliente",
        "form": {
            "name": "FormHistorialCompras",
            "stereotype": "Formulario",
            "attributes": [
                ("clienteId", "integer"),
                ("filtroEstado", "string"),
                ("fechaDesde", "date"),
                ("fechaHasta", "date"),
                ("paginaActual", "integer"),
                ("ventaSeleccionadaId", "integer"),
            ],
            "methods": [
                ("ConsultarCompras", "void", []),
                ("VerDetalleCompra", "void", []),
                ("DescargarComprobante", "void", []),
                ("FiltrarPorEstado", "void", []),
                ("CambiarPagina", "void", []),
            ],
        },
        "controller": {
            "name": "HistorialComprasController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("purchase_history", "JsonResponse", []),
                ("purchase_detail", "JsonResponse", []),
                ("get_sale", "JsonResponse", []),
                ("return_sale", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Venta",
            "stereotype": "Entidad",
            "attributes": [
                ("id_venta", "integer"),
                ("id_cliente", "integer"),
                ("id_sucursal", "integer"),
                ("tipo_venta", "string"),
                ("estado", "string"),
                ("subtotal", "decimal"),
                ("descuento", "decimal"),
                ("total", "decimal"),
                ("fecha_creacion", "datetime"),
            ],
            "methods": [
                ("calcularTotal", "decimal", []),
                ("obtenerDetalles", "list", []),
                ("cambiarEstado", "void", [("nuevo_estado", "string")]),
                ("solicitarDevolucion", "boolean", [("motivo", "string")]),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_DetalleVenta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_detalle", "integer"),
                    ("id_venta", "integer"),
                    ("id_variante_producto", "integer"),
                    ("cantidad", "integer"),
                    ("precio_unitario", "decimal"),
                    ("descuento", "decimal"),
                    ("subtotal_linea", "decimal"),
                ],
                "methods": [
                    ("calcularSubtotal", "decimal", []),
                ],
            },
            {
                "name": "E_Pago",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_pago", "integer"),
                    ("id_venta", "integer"),
                    ("metodo", "string"),
                    ("proveedor", "string"),
                    ("referencia_transaccion", "string"),
                    ("estado", "string"),
                    ("monto", "decimal"),
                    ("fecha_pago", "datetime"),
                ],
                "methods": [
                    ("verificarTransaccion", "boolean", []),
                    ("generarRecibo", "string", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "0..*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                    ("apellido", "string"),
                    ("telefono", "string"),
                ],
                "methods": [
                    ("obtenerDireccionEnvio", "string", []),
                ],
            },
        ],
    },
]

def main():
    print("=" * 70)
    print("GENERADOR DE DIAGRAMAS DE ANÁLISIS DE CLASES (CICLO 3) - UML 2.5")
    print("=" * 70)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir {MODEL_PATH}")
        return 1

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    pkg_name = "04 - Diagramas de Analisis de Clases (Ciclo 3)"
    target_pkg = None
    target_pkg_idx = -1

    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            target_pkg = p
            target_pkg_idx = i
            break

    # Si ya existe, lo eliminamos y volvemos a crear para total limpieza
    if target_pkg is not None:
        print(f"Limpiando paquete previo '{pkg_name}'...")
        root_model.Packages.Delete(target_pkg_idx)
        root_model.Packages.Refresh()

    target_pkg = root_model.Packages.AddNew(pkg_name, "")
    target_pkg.Update()
    root_model.Packages.Refresh()

    os.makedirs(EXPORT_DIR, exist_ok=True)

    def create_class(pkg, name, stereotype, attrs, methods):
        el = pkg.Elements.AddNew(name, "Class")
        if stereotype:
            el.Stereotype = stereotype
        el.Update()

        for a_name, a_type in attrs:
            att = el.Attributes.AddNew(a_name, a_type)
            att.Visibility = "Public"
            att.Update()
        el.Attributes.Refresh()

        for m in methods:
            m_name = m[0]
            m_ret = m[1]
            params = m[2] if len(m) > 2 else []
            meth = el.Methods.AddNew(m_name, m_ret)
            meth.ReturnType = m_ret
            meth.Visibility = "Public"
            meth.Update()
            if params:
                for p_name, p_type in params:
                    p = meth.Parameters.AddNew(p_name, p_type)
                    p.Type = p_type
                    p.Update()
                meth.Parameters.Refresh()
        el.Methods.Refresh()
        return el

    def connect_elements(diag, src, dst, card_src="", card_dst=""):
        c = src.Connectors.AddNew("", "Association")
        c.SupplierID = dst.ElementID
        c.Direction = "Unspecified"
        if card_src:
            c.ClientEnd.Cardinality = card_src
        if card_dst:
            c.SupplierEnd.Cardinality = card_dst
        c.Update()
        lnk = diag.DiagramLinks.AddNew("", "")
        lnk.ConnectorID = c.ConnectorID
        lnk.Update()
        return c

    for uc in USE_CASES_ANALYSIS:
        print(f"\nGenerando: {uc['diagram_name']}...")

        # Subpaquete para mantener limpio el namespace
        cu_pkg = target_pkg.Packages.AddNew(uc["id"], "")
        cu_pkg.Update()
        target_pkg.Packages.Refresh()

        # 1. Crear diagrama de clases
        diag = cu_pkg.Diagrams.AddNew(uc["diagram_name"], "Class")
        diag.Update()
        cu_pkg.Diagrams.Refresh()

        # Marco UML 2.5
        diag.StyleEx = "ShowFrame=1;"
        diag.Update()

        # 2. Crear elementos
        # Actor
        actor = cu_pkg.Elements.AddNew(uc["actor"], "Actor")
        actor.Update()

        # Formulario
        f_data = uc["form"]
        form = create_class(cu_pkg, f_data["name"], f_data["stereotype"], f_data["attributes"], f_data["methods"])

        # Controller
        c_data = uc["controller"]
        ctrl = create_class(cu_pkg, c_data["name"], c_data["stereotype"], c_data["attributes"], c_data["methods"])

        # Entidad Principal
        p_data = uc["primary_entity"]
        ent_p = create_class(cu_pkg, p_data["name"], p_data["stereotype"], p_data["attributes"], p_data["methods"])

        # Entidades Secundarias
        sec_elements = []
        for s_data in uc["secondary_entities"]:
            s_el = create_class(cu_pkg, s_data["name"], s_data["stereotype"], s_data["attributes"], s_data["methods"])
            sec_elements.append((s_el, s_data["card_primary"], s_data["card_secondary"]))

        # 3. Disposición horizontal calibrada con amplio espaciado para evitar todo solapamiento
        layout_positions = [
            (actor, 40, 110, -220, -300),
            (form, 150, 320, -110, -410),
            (ctrl, 380, 570, -150, -380),
            (ent_p, 640, 850, -110, -430),
            (sec_elements[0][0], 930, 1140, -40, -190),
            (sec_elements[1][0], 930, 1140, -220, -370),
            (sec_elements[2][0], 930, 1140, -400, -560),
        ]

        for el, l, r, t, b in layout_positions:
            obj = diag.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.left = l
            obj.right = r
            obj.top = t
            obj.bottom = b
            obj.Update()

        # 4. Conectores
        # Actor -> Formulario
        connect_elements(diag, actor, form)
        # Formulario -> Controller
        connect_elements(diag, form, ctrl)
        # Controller -> Entidad Principal
        connect_elements(diag, ctrl, ent_p)

        # Entidad Principal -> Secundarias
        for s_el, card_p, card_s in sec_elements:
            connect_elements(diag, ent_p, s_el, card_p, card_s)

        diag.Update()
        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()

        # 5. Exportar imagen PNG
        export_path = os.path.join(EXPORT_DIR, uc["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, export_path, 1)
        print(f"  -> Exportado: {export_path}")

    rep.CloseFile()
    print("\n" + "=" * 70)
    print("TODOS LOS DIAGRAMAS DE ANÁLISIS DE CLASES FUERON GENERADOS EXITOSAMENTE")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
