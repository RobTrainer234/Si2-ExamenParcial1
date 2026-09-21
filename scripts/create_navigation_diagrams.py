"""Script maestro para generar los 6 Diagramas de Navegación UML 2.5 en Enterprise Architect y exportar imágenes de alta resolución.

Basado exactamente en el modelo de referencia (media_1789881256885.png):
- Marco de clase con encabezado 'class navegacion [rol/contexto]'
- Actor UML (stick figure) a la izquierda
- Clases de presentación/vistas (Views) con atributos (inputs/tablas) y operaciones (acciones de usuario)
- Clases de controlador (Controllers) con operaciones de despacho
- Conector <<submit>> desde vista hacia controlador principal
- Composición (rombo negro) desde vista principal hacia sub-vista/componente index
- Conectores 'build' desde controladores hacia vistas generadas
- Conectores 'submit' desde vista tabla hacia controladores de acción
- Bucle de retorno 'build' desde controlador de acción hacia controlador principal
- Sincronización completa con Enterprise Architect (paquete '08 - Diagramas de Navegación')
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MPath
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

NAV_DIAGRAMS_CONFIG = [
    {
        "id": "CU08",
        "title": "class navegacion cliente (CU08 Consultar Catalogo)",
        "actor": "Cliente",
        "name_ea": "CU08 Consultar Catalogo y Buscar Prendas",
        "filename": "navegacion-cu08-catalogo-prendas.png",
        "description": "Diagrama de navegacion web/movil para busqueda de prendas, aplicacion de filtros dinamicos y visualizacion de ficha de producto.",
        "nodes": {
            "initial": {
                "name": "catalogo",
                "attrs": ["- query_busqueda: String", "- categoria_id: int"],
                "ops": [],
            },
            "subview": {
                "name": "catalogo.filtros",
                "attrs": ["- rango_precio: decimal", "- talla: String", "- color: String"],
                "ops": [],
            },
            "main_ctrl": {
                "name": "catalogoController",
                "attrs": [],
                "ops": ["+ menu(): void", "+ index(): void"],
            },
            "table": {
                "name": "grilla prendas",
                "attrs": ["- total_items: int"],
                "ops": ["+ verDetalle(): void", "+ verStock(): void"],
            },
            "act_ctrl1": {
                "name": "detallePrendaController",
                "attrs": [],
                "ops": ["+ verFicha(): void"],
            },
            "detail": {
                "name": "fichaDetallePrenda",
                "attrs": ["- sku_base: String", "- precio: decimal"],
                "ops": ["+ agregarCarrito(): void"],
            },
            "act_ctrl2": {
                "name": "stockSucursalController",
                "attrs": [],
                "ops": ["+ consultarStock(): void"],
            },
        },
    },
    {
        "id": "CU05",
        "title": "class navegacion administrador (CU05 Gestion Prendas)",
        "actor": "Administrador",
        "name_ea": "CU05 Gestionar Productos y Prendas",
        "filename": "navegacion-cu05-gestion-productos.png",
        "description": "Diagrama de navegacion backoffice para administracion de catalogo maestro, tabla de stock y configuracion de variantes.",
        "nodes": {
            "initial": {
                "name": "gestionPrendas",
                "attrs": ["- search_sku: String", "- filtro_estado: String"],
                "ops": [],
            },
            "subview": {
                "name": "prenda.filtros",
                "attrs": ["- categoria_id: int", "- temporada_id: int"],
                "ops": [],
            },
            "main_ctrl": {
                "name": "prendaController",
                "attrs": [],
                "ops": ["+ menu(): void", "+ listar(): void"],
            },
            "table": {
                "name": "tabla prendas",
                "attrs": ["- prendas_count: int"],
                "ops": ["+ configurarVariantes(): void", "+ cambiarEstado(): void"],
            },
            "act_ctrl1": {
                "name": "variantesController",
                "attrs": [],
                "ops": ["+ editarVariantes(): void"],
            },
            "detail": {
                "name": "modalVariantesTallas",
                "attrs": ["- table: variantes: int", "- stock_sucursal: int"],
                "ops": ["+ guardarStock(): void"],
            },
            "act_ctrl2": {
                "name": "estadoPrendaController",
                "attrs": [],
                "ops": ["+ actualizarEstado(): void"],
            },
        },
    },
    {
        "id": "CU10",
        "title": "class navegacion cliente (CU10 Reserva Prendas)",
        "actor": "Cliente",
        "name_ea": "CU10 Realizar Reserva de Prendas en Tienda",
        "filename": "navegacion-cu10-reserva-prendas.png",
        "description": "Diagrama de navegacion omnicanal para reserva de prendas, verificacion de stock en sucursal y generacion de comprobante QR.",
        "nodes": {
            "initial": {
                "name": "reservaPrenda",
                "attrs": ["- prenda_id: int", "- talla_id: int"],
                "ops": [],
            },
            "subview": {
                "name": "reserva.selectorSede",
                "attrs": ["- sucursal_id: int", "- ciudad: String"],
                "ops": [],
            },
            "main_ctrl": {
                "name": "reservaController",
                "attrs": [],
                "ops": ["+ menu(): void", "+ iniciarReserva(): void"],
            },
            "table": {
                "name": "tabla disponibilidadSede",
                "attrs": ["- stock_disponible: int"],
                "ops": ["+ emitirQR(): void", "+ cambiarSede(): void"],
            },
            "act_ctrl1": {
                "name": "comprobanteQRController",
                "attrs": [],
                "ops": ["+ generarQR(): void"],
            },
            "detail": {
                "name": "comprobanteReservaQR",
                "attrs": ["- codigo_qr: String", "- expira_en: datetime"],
                "ops": ["+ descargarQR(): void"],
            },
            "act_ctrl2": {
                "name": "cambioSedeController",
                "attrs": [],
                "ops": ["+ actualizarSede(): void"],
            },
        },
    },
    {
        "id": "CU14_CU17",
        "title": "class navegacion cliente (CU14/CU17 Checkout y Pago)",
        "actor": "Cliente",
        "name_ea": "CU14/CU17 Compra Digital y Pago Electronico",
        "filename": "navegacion-cu14-pago-digital.png",
        "description": "Diagrama de navegacion para checkout de compra digital, seleccion de metodo de pago (Stripe/QR BCP) y confirmacion de orden.",
        "nodes": {
            "initial": {
                "name": "carritoCompras",
                "attrs": ["- items_count: int", "- subtotal: decimal"],
                "ops": [],
            },
            "subview": {
                "name": "checkout.resumenCostos",
                "attrs": ["- costo_envio: decimal", "- total_pagar: decimal"],
                "ops": [],
            },
            "main_ctrl": {
                "name": "checkoutController",
                "attrs": [],
                "ops": ["+ menu(): void", "+ iniciarPago(): void"],
            },
            "table": {
                "name": "seleccionMetodoPago",
                "attrs": ["- orden_id: int"],
                "ops": ["+ pagarTarjeta(): void", "+ pagarQR(): void"],
            },
            "act_ctrl1": {
                "name": "pagoStripeController",
                "attrs": [],
                "ops": ["+ procesarTarjeta(): void"],
            },
            "detail": {
                "name": "formularioStripeSecure",
                "attrs": ["- token_tarjeta: String", "- client_secret: String"],
                "ops": ["+ confirmarCargo(): void"],
            },
            "act_ctrl2": {
                "name": "pagoQRBCPController",
                "attrs": [],
                "ops": ["+ emitirQR(): void"],
            },
        },
    },
    {
        "id": "CU12",
        "title": "class navegacion cliente (CU12 Probador Virtual VTON)",
        "actor": "Cliente",
        "name_ea": "CU12 Sesion de Probador Virtual (VTON IA)",
        "filename": "navegacion-cu12-probador-virtual.png",
        "description": "Diagrama de navegacion para sesion de probador virtual con IA generativa, captura de silueta y visualizador renderizado.",
        "nodes": {
            "initial": {
                "name": "probadorVirtual",
                "attrs": ["- sesion_id: int", "- usuario_id: int"],
                "ops": [],
            },
            "subview": {
                "name": "probador.camaraPose",
                "attrs": ["- resolucion: String", "- score_silueta: float"],
                "ops": [],
            },
            "main_ctrl": {
                "name": "probadorController",
                "attrs": [],
                "ops": ["+ menu(): void", "+ calibrar(): void"],
            },
            "table": {
                "name": "selectorPrendasVTON",
                "attrs": ["- prendas_compatibles: int"],
                "ops": ["+ ajustarPrenda(): void", "+ limpiarCache(): void"],
            },
            "act_ctrl1": {
                "name": "inferenciaVTONController",
                "attrs": [],
                "ops": ["+ ejecutarInferencia(): void"],
            },
            "detail": {
                "name": "canvasRenderVTON",
                "attrs": ["- render_texture: Image", "- ajuste_score: decimal"],
                "ops": ["+ comprarPrenda(): void"],
            },
            "act_ctrl2": {
                "name": "descarteSesionController",
                "attrs": [],
                "ops": ["+ purgarMemoria(): void"],
            },
        },
    },
    {
        "id": "CU20",
        "title": "class navegacion administrador (CU20 Gestion Promociones)",
        "actor": "Administrador",
        "name_ea": "CU20 Gestionar Promociones y Descuentos",
        "filename": "navegacion-cu20-gestion-promociones.png",
        "description": "Diagrama de navegacion backoffice para administracion de campanas promocionales, wizard de reglas y asignacion de prendas.",
        "nodes": {
            "initial": {
                "name": "campanasPromocion",
                "attrs": ["- filtro_vigencia: String", "- search_nombre: String"],
                "ops": [],
            },
            "subview": {
                "name": "promocion.fechas",
                "attrs": ["- fecha_inicio: date", "- fecha_fin: date"],
                "ops": [],
            },
            "main_ctrl": {
                "name": "promocionController",
                "attrs": [],
                "ops": ["+ menu(): void", "+ listar(): void"],
            },
            "table": {
                "name": "tabla promociones",
                "attrs": ["- campanas_count: int"],
                "ops": ["+ configurarReglas(): void", "+ pausarCampana(): void"],
            },
            "act_ctrl1": {
                "name": "wizardReglasController",
                "attrs": [],
                "ops": ["+ abrirWizard(): void"],
            },
            "detail": {
                "name": "asignacionPrendasWizard",
                "attrs": ["- table: prendas_asignadas: int", "- descuento_pct: decimal"],
                "ops": ["+ guardarCampana(): void"],
            },
            "act_ctrl2": {
                "name": "pausarPromocionController",
                "attrs": [],
                "ops": ["+ alternarEstado(): void"],
            },
        },
    },
]

def draw_actor(ax, center_x, center_y, label="Cliente"):
    """Dibuja un muñeco de actor UML (stick figure)."""
    # Cabeza
    head_r = 1.3
    head = patches.Circle((center_x, center_y + 3.0), radius=head_r,
                          facecolor='#fee2af', edgecolor='#3d2c1e', linewidth=1.3, zorder=6)
    ax.add_patch(head)

    # Cuerpo
    ax.plot([center_x, center_x], [center_y + 1.7, center_y - 1.5], color='#3d2c1e', linewidth=1.5, zorder=6)

    # Brazos
    ax.plot([center_x - 2.0, center_x + 2.0], [center_y + 0.6, center_y + 0.6], color='#3d2c1e', linewidth=1.5, zorder=6)

    # Piernas
    ax.plot([center_x, center_x - 1.8], [center_y - 1.5, center_y - 4.5], color='#3d2c1e', linewidth=1.5, zorder=6)
    ax.plot([center_x, center_x + 1.8], [center_y - 1.5, center_y - 4.5], color='#3d2c1e', linewidth=1.5, zorder=6)

    # Etiqueta
    ax.text(center_x, center_y - 6.2, label, va='top', ha='center',
            fontsize=8.8, fontweight='bold', family='sans-serif', color='#221a12', zorder=6)

def draw_class_box(ax, center_x, center_y, width, height, title, attrs, ops):
    """Dibuja una caja de clase UML con 3 compartimentos estilo WAE / Enterprise Architect."""
    x = center_x - width / 2.0
    y = center_y - height / 2.0

    # Sombra suave 3D
    shadow = patches.FancyBboxPatch(
        (x + 0.35, y - 0.35), width, height,
        boxstyle="round,pad=0,rounding_size=0.6",
        linewidth=0, facecolor='#e6c898', zorder=3
    )
    ax.add_patch(shadow)

    # Caja principal
    box = patches.FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0,rounding_size=0.6",
        linewidth=1.2, edgecolor='#3d2c1e', facecolor='#fee2af', zorder=4
    )
    ax.add_patch(box)

    # Altura del header
    header_h = 3.6
    header_y = y + height - header_h

    # Título
    ax.text(center_x, header_y + header_h / 2.0, title, va='center', ha='center',
            fontsize=8.5, fontweight='bold', family='sans-serif', color='#221a12', zorder=5)

    # Línea divisoria de título
    ax.plot([x, x + width], [header_y, header_y], color='#3d2c1e', linewidth=1.0, zorder=5)

    # Compartimentos de atributos y operaciones
    content_top = header_y
    if attrs and ops:
        # Repartir espacio
        mid_split = y + (height - header_h) * 0.45
        ax.plot([x, x + width], [mid_split, mid_split], color='#3d2c1e', linewidth=0.9, zorder=5)

        # Escribir atributos
        attr_text = "\n".join(attrs)
        ax.text(x + 0.8, (content_top + mid_split) / 2.0, attr_text, va='center', ha='left',
                fontsize=7.3, family='sans-serif', color='#221a12', zorder=5)

        # Escribir operaciones
        ops_text = "\n".join(ops)
        ax.text(x + 0.8, (mid_split + y) / 2.0, ops_text, va='center', ha='left',
                fontsize=7.3, family='sans-serif', color='#221a12', zorder=5)

    elif attrs:
        attr_text = "\n".join(attrs)
        ax.text(x + 0.8, (content_top + y) / 2.0, attr_text, va='center', ha='left',
                fontsize=7.3, family='sans-serif', color='#221a12', zorder=5)

    elif ops:
        ops_text = "\n".join(ops)
        ax.text(x + 0.8, (content_top + y) / 2.0, ops_text, va='center', ha='left',
                fontsize=7.3, family='sans-serif', color='#221a12', zorder=5)

def draw_arrow(ax, start, end, label=None, label_offset=(0, 0), ha='center', va='center'):
    """Dibuja una flecha direccionada con etiqueta."""
    x1, y1 = start
    x2, y2 = end
    arrow = patches.FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        mutation_scale=11,
        linewidth=1.1,
        color='#221a12',
        zorder=5
    )
    ax.add_patch(arrow)

    if label:
        mid_x = (x1 + x2) / 2.0 + label_offset[0]
        mid_y = (y1 + y2) / 2.0 + label_offset[1]
        ax.text(mid_x, mid_y, label, va=va, ha=ha,
                fontsize=8.0, family='sans-serif', color='#221a12',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='#fbe6c3', edgecolor='none'),
                zorder=6)

def draw_composite_line(ax, start, end):
    """Dibuja una línea de composición UML con rombo negro en el destino (borde izquierdo de subview)."""
    x1, y1 = start
    x2, y2 = end

    # Línea en ángulo (ortogonal) desde start hacia arriba y luego derecha
    corner_x = x1
    corner_y = y2
    ax.plot([x1, corner_x, x2], [y1, corner_y, y2], color='#221a12', linewidth=1.1, zorder=5)

    # Rombo negro horizontal en (x2, y2)
    d_size = 0.9
    diamond = patches.Polygon([
        (x2, y2),
        (x2 - d_size, y2 + d_size * 0.55),
        (x2 - 2 * d_size, y2),
        (x2 - d_size, y2 - d_size * 0.55)
    ], facecolor='#221a12', edgecolor='#221a12', zorder=6)
    ax.add_patch(diamond)

def draw_loopback_arrow(ax, start, end, label="build"):
    """Dibuja una flecha ortogonal que baja y retorna hacia la izquierda."""
    x1, y1 = start
    x2, y2 = end
    down_y = y1 - 6.5

    # Camino: (x1, y1) -> (x1, down_y) -> (x2, down_y) -> (x2, y2)
    path_data = [
        (MPath.MOVETO, (x1, y1)),
        (MPath.LINETO, (x1, down_y)),
        (MPath.LINETO, (x2, down_y)),
        (MPath.LINETO, (x2, y2))
    ]
    codes, verts = zip(*path_data)
    path = MPath(verts, codes)
    patch = patches.PathPatch(path, facecolor='none', edgecolor='#221a12', linewidth=1.1, zorder=5)
    ax.add_patch(patch)

    # Punta de flecha hacia arriba en (x2, y2)
    arrow = patches.FancyArrowPatch(
        (x2, y2 - 0.1), (x2, y2),
        arrowstyle="-|>",
        mutation_scale=11,
        linewidth=1.1,
        color='#221a12',
        zorder=5
    )
    ax.add_patch(arrow)

    if label:
        ax.text(x2, down_y + 1.2, label, va='bottom', ha='center',
                fontsize=8.0, family='sans-serif', color='#221a12',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='#fbe6c3', edgecolor='none'),
                zorder=6)

def render_navigation_diagram(cfg, output_path):
    """Renderiza el diagrama de navegación en imagen de alta resolución réplica exacta del modelo."""
    fig_width = 13.5
    fig_height = 8.5
    dpi = 150
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Contenedor exterior rectangular
    outer_box = patches.FancyBboxPatch(
        (2, 2), 96, 96,
        boxstyle="round,pad=0,rounding_size=0.5",
        linewidth=1.3, edgecolor='#221a12', facecolor='#ffffff', zorder=1
    )
    ax.add_patch(outer_box)

    # Tab superior estilo Enterprise Architect / UML 2.5
    tab_w = 32
    tab_h = 4.2
    tab_path = patches.Polygon([
        (2, 98),
        (2 + tab_w, 98),
        (2 + tab_w + 2.0, 98 - tab_h),
        (2, 98 - tab_h)
    ], facecolor='#ffffff', edgecolor='#221a12', linewidth=1.1, zorder=2)
    ax.add_patch(tab_path)
    ax.text(4, 98 - tab_h / 2.0, cfg["title"], va='center', ha='left',
            fontsize=8.2, fontweight='bold', family='sans-serif', color='#221a12', zorder=3)

    nodes = cfg["nodes"]

    # Posiciones de los nodos en coordenadas relativas (0..100)
    # 1. Actor
    actor_x, actor_y = 7.5, 48
    draw_actor(ax, actor_x, actor_y, cfg["actor"])

    # 2. Vista Inicial (ej. seguimiento)
    n_init = nodes["initial"]
    init_cx, init_cy, init_w, init_h = 22.0, 48.0, 14.0, 12.0
    draw_class_box(ax, init_cx, init_cy, init_w, init_h, n_init["name"], n_init["attrs"], n_init["ops"])

    # Línea Actor -> Initial View
    ax.plot([actor_x + 2.5, init_cx - init_w / 2.0], [actor_y + 0.5, init_cy], color='#221a12', linewidth=1.1, zorder=5)

    # 3. Sub-vista Compuesta (ej. seguimiento.index)
    n_sub = nodes["subview"]
    sub_cx, sub_cy, sub_w, sub_h = 38.5, 78.0, 14.5, 12.0
    draw_class_box(ax, sub_cx, sub_cy, sub_w, sub_h, n_sub["name"], n_sub["attrs"], n_sub["ops"])

    # Composición Initial View -> Subview (rombo negro)
    draw_composite_line(ax, (init_cx, init_cy + init_h / 2.0), (sub_cx - sub_w / 2.0, sub_cy))

    # 4. Controlador Principal (ej. seguimientoController)
    n_ctrl = nodes["main_ctrl"]
    ctrl_cx, ctrl_cy, ctrl_w, ctrl_h = 38.5, 48.0, 14.5, 12.0
    draw_class_box(ax, ctrl_cx, ctrl_cy, ctrl_w, ctrl_h, n_ctrl["name"], n_ctrl["attrs"], n_ctrl["ops"])

    # Initial View -> Main Controller <<submit>>
    draw_arrow(ax, (init_cx + init_w / 2.0, init_cy), (ctrl_cx - ctrl_w / 2.0, ctrl_cy),
               label="<<submit>>", label_offset=(0, 0))

    # Main Controller -> Subview (build)
    draw_arrow(ax, (ctrl_cx, ctrl_cy + ctrl_h / 2.0), (sub_cx, sub_cy - sub_h / 2.0),
               label="build", label_offset=(0, 0))

    # 5. Vista Tabla / Grilla (ej. tabla seguimiento)
    n_tab = nodes["table"]
    tab_cx, tab_cy, tab_w, tab_h = 56.5, 48.0, 14.5, 12.5
    draw_class_box(ax, tab_cx, tab_cy, tab_w, tab_h, n_tab["name"], n_tab["attrs"], n_tab["ops"])

    # Main Controller -> Table View (build)
    draw_arrow(ax, (ctrl_cx + ctrl_w / 2.0, ctrl_cy), (tab_cx - tab_w / 2.0, tab_cy),
               label="build", label_offset=(0, 0.8))

    # 6. Controlador de Acción 1 (ej. seguimientoController: ubicacion)
    n_act1 = nodes["act_ctrl1"]
    act1_cx, act1_cy, act1_w, act1_h = 73.5, 74.0, 14.5, 11.5
    draw_class_box(ax, act1_cx, act1_cy, act1_w, act1_h, n_act1["name"], n_act1["attrs"], n_act1["ops"])

    # Table View -> Act Ctrl 1 (submit)
    draw_arrow(ax, (tab_cx + tab_w / 2.0, tab_cy + 3.0), (act1_cx - act1_w / 2.0, act1_cy - 3.0),
               label="submit", label_offset=(-1.2, 0.5))

    # 7. Vista Detalle / Resultado (ej. seguimientoUbicacion)
    n_det = nodes["detail"]
    det_cx, det_cy, det_w, det_h = 90.0, 74.0, 14.5, 11.5
    draw_class_box(ax, det_cx, det_cy, det_w, det_h, n_det["name"], n_det["attrs"], n_det["ops"])

    # Act Ctrl 1 -> Detail View (build)
    draw_arrow(ax, (act1_cx + act1_w / 2.0, act1_cy), (det_cx - det_w / 2.0, det_cy),
               label="build", label_offset=(0, 0.8))

    # 8. Controlador de Acción 2 (ej. seguimientoController: estado)
    n_act2 = nodes["act_ctrl2"]
    act2_cx, act2_cy, act2_w, act2_h = 74.5, 23.0, 14.5, 11.5
    draw_class_box(ax, act2_cx, act2_cy, act2_w, act2_h, n_act2["name"], n_act2["attrs"], n_act2["ops"])

    # Table View -> Act Ctrl 2 (submit)
    draw_arrow(ax, (tab_cx + tab_w / 2.0, tab_cy - 3.0), (act2_cx - act2_w / 2.0, act2_cy + 3.0),
               label="submit", label_offset=(-1.2, -0.5))

    # Act Ctrl 2 -> Loopback a Main Controller (build)
    draw_loopback_arrow(ax, (act2_cx - 4.0, act2_cy - act2_h / 2.0), (ctrl_cx, ctrl_cy - ctrl_h / 2.0), label="build")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"  -> PNG guardado: {output_path}")

def sync_navigation_with_enterprise_architect():
    """Registra y estructura los diagramas de navegación en el modelo FashionStore.eap."""
    print("\nSincronizando con repositorio Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"Error al abrir {MODEL_PATH}")
        return False

    root_model = rep.Models.GetAt(0)

    # Eliminar paquete previo si existe
    pkg_name = "08 - Diagramas de Navegación"
    for i in range(root_model.Packages.Count - 1, -1, -1):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            root_model.Packages.Delete(i)
            root_model.Packages.Refresh()
            break

    # Crear paquete principal
    pkg_main = root_model.Packages.AddNew(pkg_name, "")
    pkg_main.Notes = "Diagramas de Navegación Web/Móvil (UML 2.5) bajo arquitectura MVC para los casos de uso seleccionados."
    pkg_main.Update()
    root_model.Packages.Refresh()

    # Layout de coordenadas para Enterprise Architect (escala estándar)
    # EA: 0 es arriba, negativo es abajo.
    ea_layout = {
        "actor":     (50, 110, -200, -300),
        "initial":   (160, 310, -180, -300),
        "subview":   (360, 520, -40, -160),
        "main_ctrl": (360, 520, -200, -300),
        "table":     (570, 730, -190, -310),
        "act_ctrl1": (780, 940, -40, -150),
        "detail":    (990, 1150, -40, -150),
        "act_ctrl2": (780, 940, -340, -440),
    }

    for cfg in NAV_DIAGRAMS_CONFIG:
        sub_pkg = pkg_main.Packages.AddNew(f"{cfg['id']} - {cfg['name_ea']}", "")
        sub_pkg.Notes = cfg["description"]
        sub_pkg.Update()
        pkg_main.Packages.Refresh()

        # Crear diagrama Logical / Class con título limpio
        diag_title = f"navegacion {cfg['actor'].lower()} ({cfg['id']})"
        diag = sub_pkg.Diagrams.AddNew(diag_title, "Logical")
        diag.Notes = f"Diagrama de navegación UML 2.5 para {cfg['name_ea']}.\n{cfg['description']}"
        diag.Update()
        sub_pkg.Diagrams.Refresh()

        # 1. Crear Actor
        actor_el = sub_pkg.Elements.AddNew(cfg["actor"], "Actor")
        actor_el.Update()

        d_act = diag.DiagramObjects.AddNew("", "")
        d_act.ElementID = actor_el.ElementID
        l, r, t, b = ea_layout["actor"]
        d_act.left = l; d_act.right = r; d_act.top = t; d_act.bottom = b
        d_act.Update()

        # 2. Crear Clases (Vistas y Controladores sin estereotipos circulares para mantener estilo de clase rectangular)
        created_elements = {}
        for key, n_info in cfg["nodes"].items():
            c_el = sub_pkg.Elements.AddNew(n_info["name"], "Class")
            c_el.Update()

            # Agregar atributos
            for a_str in n_info["attrs"]:
                # Formato "- nombre: tipo"
                clean_a = a_str.lstrip("- + ").strip()
                parts = clean_a.split(":")
                a_name = parts[0].strip()
                a_type = parts[1].strip() if len(parts) > 1 else "String"
                attr = c_el.Attributes.AddNew(a_name, a_type)
                attr.Visibility = "Private"
                attr.Update()

            # Agregar operaciones
            for o_str in n_info["ops"]:
                # Formato "+ nombre(): tipo"
                clean_o = o_str.lstrip("- + ").strip()
                op_name = clean_o.split("(")[0].strip()
                op = c_el.Methods.AddNew(op_name, "void")
                op.Visibility = "Public"
                op.Update()

            c_el.Update()
            created_elements[key] = c_el

            # Posicionar en diagrama
            l, r, t, b = ea_layout[key]
            d_obj = diag.DiagramObjects.AddNew("", "")
            d_obj.ElementID = c_el.ElementID
            d_obj.left = l; d_obj.right = r; d_obj.top = t; d_obj.bottom = b
            d_obj.Update()

        # 3. Crear Conectores
        # Actor -> Initial View
        c_act = actor_el.Connectors.AddNew("", "Association")
        c_act.SupplierID = created_elements["initial"].ElementID
        c_act.Update()

        # Initial View -> Composite Subview (rombo negro)
        c_comp = created_elements["initial"].Connectors.AddNew("", "Aggregation")
        c_comp.SupplierID = created_elements["subview"].ElementID
        c_comp.Subtype = "Composite"
        c_comp.Update()

        # Initial View -> Main Controller (<<submit>>)
        c_sub = created_elements["initial"].Connectors.AddNew("<<submit>>", "Association")
        c_sub.SupplierID = created_elements["main_ctrl"].ElementID
        c_sub.Direction = "Source -> Destination"
        c_sub.Update()

        # Main Controller -> Subview (build)
        c_b1 = created_elements["main_ctrl"].Connectors.AddNew("build", "Dependency")
        c_b1.SupplierID = created_elements["subview"].ElementID
        c_b1.Direction = "Source -> Destination"
        c_b1.Update()

        # Main Controller -> Table View (build)
        c_b2 = created_elements["main_ctrl"].Connectors.AddNew("build", "Dependency")
        c_b2.SupplierID = created_elements["table"].ElementID
        c_b2.Direction = "Source -> Destination"
        c_b2.Update()

        # Table View -> Act Ctrl 1 (submit)
        c_s1 = created_elements["table"].Connectors.AddNew("submit", "Association")
        c_s1.SupplierID = created_elements["act_ctrl1"].ElementID
        c_s1.Direction = "Source -> Destination"
        c_s1.Update()

        # Act Ctrl 1 -> Detail View (build)
        c_b3 = created_elements["act_ctrl1"].Connectors.AddNew("build", "Dependency")
        c_b3.SupplierID = created_elements["detail"].ElementID
        c_b3.Direction = "Source -> Destination"
        c_b3.Update()

        # Table View -> Act Ctrl 2 (submit)
        c_s2 = created_elements["table"].Connectors.AddNew("submit", "Association")
        c_s2.SupplierID = created_elements["act_ctrl2"].ElementID
        c_s2.Direction = "Source -> Destination"
        c_s2.Update()

        # Act Ctrl 2 -> Main Controller (build loopback)
        c_loop = created_elements["act_ctrl2"].Connectors.AddNew("build", "Dependency")
        c_loop.SupplierID = created_elements["main_ctrl"].ElementID
        c_loop.Direction = "Source -> Destination"
        c_loop.Update()

        diag.Update()

        # Exportar imagen nativa oficial desde Enterprise Architect
        proj = rep.GetProjectInterface()
        ea_png = os.path.join(EXPORT_DIR, f"ea-{cfg['filename']}")
        proj.PutDiagramImageToFile(diag.DiagramGUID, ea_png, 1)
        print(f"  [EA] Diagrama de navegacion modelado y exportado para {cfg['id']}")

    rep.CloseFile()
    rep.Exit()
    print("Sincronización de Navegación con EA completada exitosamente.")
    return True

def main():
    print("=" * 75)
    print("GENERADOR DE DIAGRAMAS DE NAVEGACIÓN UML 2.5 (CICLOS 1, 2 Y 3)")
    print("FashionStore - Enterprise Architect & Visual Artifacts")
    print("=" * 75)

    print("\n1. Renderizando imágenes en alta resolución...")
    for cfg in NAV_DIAGRAMS_CONFIG:
        out_png = os.path.join(EXPORT_DIR, cfg["filename"])
        render_navigation_diagram(cfg, out_png)

    print("\n2. Registrando modelos de Navegación en FashionStore.eap...")
    try:
        sync_navigation_with_enterprise_architect()
    except Exception as e:
        print(f"Aviso durante sincronización EA: {e}")

    print("\n" + "=" * 75)
    print("TODOS LOS DIAGRAMAS DE NAVEGACIÓN FUERON GENERADOS Y REGISTRADOS EXITOSAMENTE")
    print("=" * 75)

if __name__ == "__main__":
    main()
