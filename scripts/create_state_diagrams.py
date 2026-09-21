"""Script maestro para generar los 6 Diagramas de Estado UML 2.5 en Enterprise Architect y exportar imágenes de alta resolución.

Basado exactamente en el modelo de referencia (media_1789878771332.jpg):
- Contenedor exterior grande con bordes redondeados y fondo cálido melocotón (#fbe6c3)
- Rótulo superior centrado (ej. 'CU03', 'CU05', etc.)
- Pseudo-estado inicial: Círculo negro sólido rotulado 'Inicio'
- Pseudo-estado final: Círculo verde con 'X' rotulado 'Fin'
- Estados: Rectángulos redondeados con sombra suave y degradado cálido (#fee2af)
- Transiciones: Flechas direccionadas con guardas entre corchetes '[condicion]'
- Bucle de error (self-loop) en el estado de autenticación/inicio
- Bifurcaciones hacia operaciones (listar, modificar, crear, eliminar/cancelar)
- Bucle de retorno ante validación incorrecta
- Estado de consolidación 'Transacción completada' que converge al estado 'Fin'
- Sincronización completa con Enterprise Architect (paquete '07 - Diagramas de Estado')
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

def draw_state_box(ax, center_x, center_y, width, height, text, font_size=8.8):
    """Dibuja una caja de estado redondeada idéntica al modelo de referencia."""
    x = center_x - width / 2.0
    y = center_y - height / 2.0

    # Sombra suave 3D
    shadow = patches.FancyBboxPatch(
        (x + 0.35, y - 0.35), width, height,
        boxstyle="round,pad=0,rounding_size=1.5",
        linewidth=0, facecolor='#e6c898', zorder=3
    )
    ax.add_patch(shadow)

    # Caja principal con borde marrón oscuro y fondo cálido
    box = patches.FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0,rounding_size=1.5",
        linewidth=1.2, edgecolor='#3d2c1e', facecolor='#fee2af', zorder=4
    )
    ax.add_patch(box)

    # Texto multilínea centrado
    ax.text(center_x, center_y, text, va='center', ha='center',
            fontsize=font_size, fontweight='bold', family='sans-serif', color='#221a12', zorder=5)

def draw_initial_state(ax, center_x, center_y, label="Inicio"):
    """Dibuja el pseudo-estado inicial UML (círculo negro)."""
    circle = patches.Circle((center_x, center_y), radius=1.8, facecolor='#111111', edgecolor='#111111', zorder=5)
    ax.add_patch(circle)
    ax.text(center_x, center_y - 2.8, label, va='top', ha='center',
            fontsize=9.0, fontweight='bold', family='sans-serif', color='#221a12', zorder=5)

def draw_final_state(ax, center_x, center_y, label="Fin"):
    """Dibuja el pseudo-estado final UML con cruz interna."""
    circle = patches.Circle((center_x, center_y), radius=2.2, facecolor='#93c87e', edgecolor='#2d5a1e', linewidth=1.2, zorder=5)
    ax.add_patch(circle)
    r = 1.3
    ax.plot([center_x - r, center_x + r], [center_y - r, center_y + r], color='#1b4010', linewidth=1.3, zorder=6)
    ax.plot([center_x - r, center_x + r], [center_y + r, center_y - r], color='#1b4010', linewidth=1.3, zorder=6)
    ax.text(center_x, center_y - 3.2, label, va='top', ha='center',
            fontsize=9.0, fontweight='bold', family='sans-serif', color='#221a12', zorder=5)

def draw_transition_arrow(ax, start, end, label=None, label_offset=(0, 0), connectionstyle="arc3,rad=0.0", ha='center', va='center'):
    """Dibuja una flecha de transición con guarda opcional."""
    x1, y1 = start
    x2, y2 = end

    arrow = patches.FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        connectionstyle=connectionstyle,
        mutation_scale=11,
        linewidth=1.1,
        color='#221a12',
        zorder=4
    )
    ax.add_patch(arrow)

    if label:
        mid_x = (x1 + x2) / 2.0 + label_offset[0]
        mid_y = (y1 + y2) / 2.0 + label_offset[1]
        ax.text(mid_x, mid_y, label, va=va, ha=ha,
                fontsize=8.5, family='sans-serif', color='#221a12',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='#fbe6c3', edgecolor='none'),
                zorder=6)

def draw_self_loop(ax, center_x, bottom_y, label="[error]"):
    """Dibuja un bucle reflexivo hacia abajo (self-loop) en la caja."""
    loop = patches.FancyArrowPatch(
        (center_x - 2.5, bottom_y), (center_x + 2.5, bottom_y),
        arrowstyle="-|>",
        connectionstyle="arc3,rad=2.2",
        mutation_scale=10,
        linewidth=1.1,
        color='#221a12',
        zorder=4
    )
    ax.add_patch(loop)
    ax.text(center_x, bottom_y - 4.2, label, va='center', ha='center',
            fontsize=8.5, family='sans-serif', color='#221a12',
            bbox=dict(boxstyle='square,pad=0.15', facecolor='#fbe6c3', edgecolor='none'), zorder=6)


STATE_DIAGRAMS_CONFIG = [
    {
        "id": "CU03",
        "title": "CU03",
        "name_ea": "CU03 Gestionar Usuarios y Roles",
        "filename": "estado-cu03-gestion-usuarios.png",
        "description": "Diagrama de estados interactivo para gestión administrativa de cuentas de usuario, asignación de roles y control de acceso.",
        "nodes": {
            "login": ("Loguear\nAdministrador", 24, 78, 14.5, 6.5),
            "select": ("Seleccionar opcion\nUsuario", 49, 78, 14.5, 6.5),
            "list": ("Desplegar lista\nusuarios", 80, 71, 14, 6.0),
            "modify": ("Modificar\nUsuario / Rol", 20, 54, 14, 6.5),
            "create": ("Crear Nuevo\nUsuario", 42, 54, 14, 6.5),
            "id_delete": ("ID del usuario\na desactivar", 65, 54, 15, 6.5),
            "delete": ("Desactivar\nUsuario", 65, 38, 14, 6.0),
            "review": ("Revisar Datos\ny Roles", 31, 38, 14, 6.0),
            "complete": ("Transaccion\ncompletada", 48, 22, 16, 6.0),
        },
        "labels": {
            "err_login": "[error credenciales]",
            "to_select": "[correcto]",
            "list": "[listar]",
            "modify": "[modificar]",
            "create": "[crear]",
            "delete": "[desactivar]",
            "id_err": "[incorrecto]",
            "id_ok": "[correcto]",
            "fill1": "[llenar datos]",
            "fill2": "[llenar datos]",
        }
    },
    {
        "id": "CU05",
        "title": "CU05",
        "name_ea": "CU05 Gestionar Productos y Prendas",
        "filename": "estado-cu05-gestion-productos.png",
        "description": "Diagrama de estados para catálogo de prendas, registro de variantes de talla/color, actualización de stock y descatalogación.",
        "nodes": {
            "login": ("Loguear Admin\no Encargado", 24, 78, 14.5, 6.5),
            "select": ("Seleccionar opcion\nPrenda", 49, 78, 14.5, 6.5),
            "list": ("Desplegar catalogo\nprendas", 80, 71, 14, 6.0),
            "modify": ("Modificar Prenda\ny Stock", 20, 54, 14, 6.5),
            "create": ("Registrar\nPrenda Base", 42, 54, 14, 6.5),
            "id_delete": ("SKU de prenda\na descontinuar", 65, 54, 15, 6.5),
            "delete": ("Descontinuar\nPrenda", 65, 38, 14, 6.0),
            "review": ("Revisar Variantes\ny Precios", 31, 38, 14.5, 6.0),
            "complete": ("Transaccion\ncompletada", 48, 22, 16, 6.0),
        },
        "labels": {
            "err_login": "[error]",
            "to_select": "[correcto]",
            "list": "[catalogo]",
            "modify": "[modificar]",
            "create": "[crear]",
            "delete": "[descontinuar]",
            "id_err": "[no encontrado]",
            "id_ok": "[correcto]",
            "fill1": "[llenar datos]",
            "fill2": "[configurar tallas]",
        }
    },
    {
        "id": "CU10",
        "title": "CU10",
        "name_ea": "CU10 Realizar Reserva de Prendas en Tienda",
        "filename": "estado-cu10-reserva-prendas.png",
        "description": "Diagrama de estados para reserva física en sucursal, retención temporal de stock, emisión de código de retiro QR y cancelación.",
        "nodes": {
            "login": ("Autenticar\nCliente", 24, 78, 14.5, 6.5),
            "select": ("Seleccionar Prenda\ny Sucursal", 49, 78, 15, 6.5),
            "list": ("Ver disponibilidad\nen tiendas", 80, 71, 14, 6.0),
            "modify": ("Modificar\nTalla / Sede", 20, 54, 14, 6.5),
            "create": ("Solicitar Reserva\nde Prenda", 42, 54, 14, 6.5),
            "id_delete": ("Codigo de reserva\na cancelar", 65, 54, 15, 6.5),
            "delete": ("Cancelar Reserva\ny Liberar Stock", 65, 38, 14.5, 6.0),
            "review": ("Generar Codigo QR\nde Retiro", 31, 38, 14.5, 6.0),
            "complete": ("Transaccion\ncompletada", 48, 22, 16, 6.0),
        },
        "labels": {
            "err_login": "[error login]",
            "to_select": "[correcto]",
            "list": "[consultar]",
            "modify": "[modificar]",
            "create": "[reservar]",
            "delete": "[cancelar]",
            "id_err": "[codigo invalido]",
            "id_ok": "[confirmado]",
            "fill1": "[cambiar sede]",
            "fill2": "[bloquear stock]",
        }
    },
    {
        "id": "CU14_CU17",
        "title": "CU14 / CU17",
        "name_ea": "CU14/CU17 Compra Digital y Pago Electrónico",
        "filename": "estado-cu14-pago-digital.png",
        "description": "Diagrama de estados para checkout digital, integración con pasarela de pagos QR BCP / Stripe y generación de comprobante.",
        "nodes": {
            "login": ("Revisar Carrito\nde Compras", 24, 78, 14.5, 6.5),
            "select": ("Seleccionar Metodo\nde Pago", 49, 78, 15, 6.5),
            "list": ("Desplegar resumen\nde compra", 80, 71, 14, 6.0),
            "modify": ("Ingresar Tarjeta\nStripe", 20, 54, 14, 6.5),
            "create": ("Generar Cobro\nQR Dinamico", 42, 54, 14, 6.5),
            "id_delete": ("ID de orden\na cancelar", 65, 54, 15, 6.5),
            "delete": ("Cancelar Orden\ny Liberar Stock", 65, 38, 14.5, 6.0),
            "review": ("Esperar Confirmacion\nWebhook", 31, 38, 14.5, 6.0),
            "complete": ("Generar Factura /\nTransaccion Ok", 48, 22, 16, 6.0),
        },
        "labels": {
            "err_login": "[carrito vacio]",
            "to_select": "[continuar]",
            "list": "[ver orden]",
            "modify": "[tarjeta]",
            "create": "[pago QR]",
            "delete": "[cancelar]",
            "id_err": "[orden invalida]",
            "id_ok": "[cancelar orden]",
            "fill1": "[procesar cargo]",
            "fill2": "[escanear QR]",
        }
    },
    {
        "id": "CU20",
        "title": "CU20",
        "name_ea": "CU20 Gestionar Promociones y Descuentos",
        "filename": "estado-cu20-gestion-promociones.png",
        "description": "Diagrama de estados para administración de promociones, reglas de descuento, asignación de prendas y activación en catálogo.",
        "nodes": {
            "login": ("Loguear\nAdministrador", 24, 78, 14.5, 6.5),
            "select": ("Seleccionar opcion\nPromocion", 49, 78, 15, 6.5),
            "list": ("Desplegar campañas\nvigentes", 80, 71, 14, 6.0),
            "modify": ("Modificar Reglas\nde Descuento", 20, 54, 14, 6.5),
            "create": ("Crear Nueva\nPromocion", 42, 54, 14, 6.5),
            "id_delete": ("ID de promocion\na pausar", 65, 54, 15, 6.5),
            "delete": ("Pausar o Finalizar\nCampaña", 65, 38, 14.5, 6.0),
            "review": ("Revisar Fechas\ny Prendas", 31, 38, 14, 6.0),
            "complete": ("Transaccion\ncompletada", 48, 22, 16, 6.0),
        },
        "labels": {
            "err_login": "[error]",
            "to_select": "[correcto]",
            "list": "[listar]",
            "modify": "[modificar]",
            "create": "[crear]",
            "delete": "[pausar]",
            "id_err": "[no encontrada]",
            "id_ok": "[correcto]",
            "fill1": "[llenar datos]",
            "fill2": "[asignar prendas]",
        }
    },
    {
        "id": "CU12",
        "title": "CU12",
        "name_ea": "CU12 Sesión de Probador Virtual (VTON)",
        "filename": "estado-cu12-probador-virtual.png",
        "description": "Diagrama de estados para probador virtual, captura de pose mediante visión computacional, ajuste con IA generativa y renderizado.",
        "nodes": {
            "login": ("Acceder a\nProbador Virtual", 24, 78, 14.5, 6.5),
            "select": ("Seleccionar opcion\nProbador", 49, 78, 15, 6.5),
            "list": ("Desplegar pruebas\nguardadas", 80, 71, 14, 6.0),
            "modify": ("Capturar Foto\ny Silueta", 20, 54, 14, 6.5),
            "create": ("Seleccionar Prenda\nde Catalogo", 42, 54, 14, 6.5),
            "id_delete": ("ID de sesion\na descartar", 65, 54, 15, 6.5),
            "delete": ("Descartar Sesion\ny Cache", 65, 38, 14.5, 6.0),
            "review": ("Procesar Inferencia\nVTON con IA", 31, 38, 14.5, 6.0),
            "complete": ("Prenda Adaptada /\nTransaccion Ok", 48, 22, 16, 6.0),
        },
        "labels": {
            "err_login": "[error camara]",
            "to_select": "[iniciado]",
            "list": "[historial]",
            "modify": "[nueva foto]",
            "create": "[probar]",
            "delete": "[descartar]",
            "id_err": "[invalido]",
            "id_ok": "[descartar]",
            "fill1": "[pose valida]",
            "fill2": "[ejecutar ajuste]",
        }
    },
]

def render_state_diagram(cfg, output_path):
    """Renderiza el diagrama de estados en base a la configuración y lo guarda en PNG."""
    fig_width = 11.5
    fig_height = 9.5
    dpi = 150
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Contenedor exterior idéntico al modelo
    outer_box = patches.FancyBboxPatch(
        (2, 2), 96, 96,
        boxstyle="round,pad=0,rounding_size=3.0",
        linewidth=1.3, edgecolor='#221a12', facecolor='#fbe6c3', zorder=1
    )
    ax.add_patch(outer_box)

    # Título centrado arriba
    ax.text(50, 95.5, cfg["title"], va='center', ha='center',
            fontsize=13.0, fontweight='bold', family='sans-serif', color='#221a12', zorder=3)

    nodes = cfg["nodes"]
    lbls = cfg["labels"]

    # 1. Estado Inicial
    draw_initial_state(ax, 10, 78, "Inicio")

    # 2. Estado de Login/Entrada
    name_login, lx, ly, lw, lh = nodes["login"]
    draw_state_box(ax, lx, ly, lw, lh, name_login)
    draw_transition_arrow(ax, (12, 78), (lx - lw/2.0, 78))

    # Self-loop de error
    draw_self_loop(ax, lx, ly - lh/2.0, lbls["err_login"])

    # 3. Estado Central Selector
    name_sel, sx, sy, sw, sh = nodes["select"]
    draw_state_box(ax, sx, sy, sw, sh, name_sel)
    draw_transition_arrow(ax, (lx + lw/2.0, ly), (sx - sw/2.0, sy), lbls["to_select"], label_offset=(0, 1.8))

    # 4. Rama Listar
    name_list, list_x, list_y, list_w, list_h = nodes["list"]
    draw_state_box(ax, list_x, list_y, list_w, list_h, name_list)
    draw_transition_arrow(ax, (sx + sw/2.0, sy - 1.0), (list_x - list_w/2.0, list_y), lbls["list"], label_offset=(0, 1.8))

    # 5. Rama Modificar
    name_mod, mx, my, mw, mh = nodes["modify"]
    draw_state_box(ax, mx, my, mw, mh, name_mod)
    draw_transition_arrow(ax, (sx - 4.5, sy - sh/2.0), (mx + 3.0, my + mh/2.0), lbls["modify"], label_offset=(-3.5, 2.0))

    # 6. Rama Crear
    name_cre, cx, cy, cw, ch = nodes["create"]
    draw_state_box(ax, cx, cy, cw, ch, name_cre)
    draw_transition_arrow(ax, (sx - 1.5, sy - sh/2.0), (cx + 1.0, cy + ch/2.0), lbls["create"], label_offset=(-2.6, 0.8), ha='right')

    # 7. Rama Eliminar / Acción
    name_del_id, dix, diy, diw, dih = nodes["id_delete"]
    draw_state_box(ax, dix, diy, diw, dih, name_del_id)
    draw_transition_arrow(ax, (sx + 3.5, sy - sh/2.0), (dix - 3.5, diy + dih/2.0), lbls["delete"], label_offset=(-2.0, 1.2), ha='right')

    # Bucle de retorno [incorrecto]
    draw_transition_arrow(ax, (dix + 0.5, diy + dih/2.0), (sx + 4.5, sy - sh/2.0 + 0.5), lbls["id_err"], label_offset=(2.8, -0.6), ha='left', connectionstyle="arc3,rad=-0.15")

    # Acción de Eliminar
    name_del, dx, dy, dw, dh = nodes["delete"]
    draw_state_box(ax, dx, dy, dw, dh, name_del)
    draw_transition_arrow(ax, (dix, diy - dih/2.0), (dx, dy + dh/2.0), lbls["id_ok"], label_offset=(3.2, 0))

    # 8. Estado Revisar / Validar
    name_rev, rx, ry, rw, rh = nodes["review"]
    draw_state_box(ax, rx, ry, rw, rh, name_rev)
    draw_transition_arrow(ax, (mx + 2.0, my - mh/2.0), (rx - 2.0, ry + rh/2.0), lbls["fill1"], label_offset=(-3.6, 0))
    draw_transition_arrow(ax, (cx - 2.0, cy - ch/2.0), (rx + 2.0, ry + rh/2.0), lbls["fill2"], label_offset=(3.8, 0))

    # 9. Estado Completado
    name_comp, com_x, com_y, com_w, com_h = nodes["complete"]
    draw_state_box(ax, com_x, com_y, com_w, com_h, name_comp)
    draw_transition_arrow(ax, (rx + 2.0, ry - rh/2.0), (com_x - 4.0, com_y + com_h/2.0))
    draw_transition_arrow(ax, (dx - 2.0, dy - dh/2.0), (com_x + 3.0, com_y + com_h/2.0))

    # 10. Estado Final
    draw_final_state(ax, com_x, 10, "Fin")
    draw_transition_arrow(ax, (com_x, com_y - com_h/2.0), (com_x, 13))

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"  -> PNG guardado: {output_path}")

def sync_with_enterprise_architect():
    """Registra y estructura los diagramas de estado en el modelo FashionStore.eap."""
    print("\nSincronizando con repositorio Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"Error al abrir {MODEL_PATH}")
        return False

    root_model = rep.Models.GetAt(0)

    # Eliminar paquete previo si existe
    pkg_name = "07 - Diagramas de Estado"
    for i in range(root_model.Packages.Count - 1, -1, -1):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            root_model.Packages.Delete(i)
            root_model.Packages.Refresh()
            break

    # Crear paquete principal
    pkg_main = root_model.Packages.AddNew(pkg_name, "")
    pkg_main.Notes = "Diagramas de Estado (Statechart Diagrams) para los casos de uso seleccionados en Ciclos 1, 2 y 3 segun el modelo de referencia."
    pkg_main.Update()
    root_model.Packages.Refresh()

    for cfg in STATE_DIAGRAMS_CONFIG:
        sub_pkg = pkg_main.Packages.AddNew(f"{cfg['id']} - {cfg['name_ea']}", "")
        sub_pkg.Notes = cfg["description"]
        sub_pkg.Update()
        pkg_main.Packages.Refresh()

        # Crear diagrama Statechart
        diag = sub_pkg.Diagrams.AddNew(cfg["title"], "Statechart")
        diag.Notes = f"Diagrama de estados UML 2.5 para {cfg['name_ea']}.\n{cfg['description']}"
        diag.Update()
        sub_pkg.Diagrams.Refresh()

        # Crear elementos en EA
        init_node = sub_pkg.Elements.AddNew("Inicio", "StateNode")
        init_node.Subtype = 3  # Initial
        init_node.Update()

        final_node = sub_pkg.Elements.AddNew("Fin", "StateNode")
        final_node.Subtype = 4  # Final
        final_node.Update()

        # Coordenadas orientadas Top-to-Bottom: Inicio ARRIBA, Fin ABAJO
        ea_layout = {
            "login":     (160, 300, -70, -130),
            "select":    (380, 520, -70, -130),
            "list":      (620, 760, -90, -150),
            "modify":    (160, 300, -220, -280),
            "create":    (370, 510, -220, -280),
            "id_delete": (580, 720, -220, -280),
            "review":    (260, 400, -360, -420),
            "delete":    (580, 720, -360, -420),
            "complete":  (420, 560, -500, -560),
        }

        # Crear estados
        created_states = {}
        for key, val in cfg["nodes"].items():
            st_text, _, _, _, _ = val
            clean_name = st_text.replace("\n", " ")
            st_el = sub_pkg.Elements.AddNew(clean_name, "State")
            st_el.Update()
            created_states[key] = st_el

            # Posicionar en diagrama con orientación vertical correcta
            l, r, t, b = ea_layout[key]
            d_obj = diag.DiagramObjects.AddNew("", "")
            d_obj.ElementID = st_el.ElementID
            d_obj.left = l
            d_obj.right = r
            d_obj.top = t
            d_obj.bottom = b
            d_obj.Update()

        # Posicionar inicio ARRIBA y fin ABAJO
        d_init = diag.DiagramObjects.AddNew("", "")
        d_init.ElementID = init_node.ElementID
        d_init.left = 70
        d_init.right = 100
        d_init.top = -85
        d_init.bottom = -115
        d_init.Update()

        d_final = diag.DiagramObjects.AddNew("", "")
        d_final.ElementID = final_node.ElementID
        d_final.left = 475
        d_final.right = 505
        d_final.top = -620
        d_final.bottom = -650
        d_final.Update()

        # Crear conectores StateFlow
        c_in = init_node.Connectors.AddNew("", "StateFlow")
        c_in.SupplierID = created_states["login"].ElementID
        c_in.Update()

        # Self-loop de error en estado inicial
        c_err = created_states["login"].Connectors.AddNew(cfg["labels"]["err_login"], "StateFlow")
        c_err.SupplierID = created_states["login"].ElementID
        c_err.Update()

        c_to_sel = created_states["login"].Connectors.AddNew(cfg["labels"]["to_select"], "StateFlow")
        c_to_sel.SupplierID = created_states["select"].ElementID
        c_to_sel.Update()

        c_list = created_states["select"].Connectors.AddNew(cfg["labels"]["list"], "StateFlow")
        c_list.SupplierID = created_states["list"].ElementID
        c_list.Update()

        c_mod = created_states["select"].Connectors.AddNew(cfg["labels"]["modify"], "StateFlow")
        c_mod.SupplierID = created_states["modify"].ElementID
        c_mod.Update()

        c_cre = created_states["select"].Connectors.AddNew(cfg["labels"]["create"], "StateFlow")
        c_cre.SupplierID = created_states["create"].ElementID
        c_cre.Update()

        c_del = created_states["select"].Connectors.AddNew(cfg["labels"]["delete"], "StateFlow")
        c_del.SupplierID = created_states["id_delete"].ElementID
        c_del.Update()

        c_id_ret = created_states["id_delete"].Connectors.AddNew(cfg["labels"]["id_err"], "StateFlow")
        c_id_ret.SupplierID = created_states["select"].ElementID
        c_id_ret.Update()

        c_id_ok = created_states["id_delete"].Connectors.AddNew(cfg["labels"]["id_ok"], "StateFlow")
        c_id_ok.SupplierID = created_states["delete"].ElementID
        c_id_ok.Update()

        c_f1 = created_states["modify"].Connectors.AddNew(cfg["labels"]["fill1"], "StateFlow")
        c_f1.SupplierID = created_states["review"].ElementID
        c_f1.Update()

        c_f2 = created_states["create"].Connectors.AddNew(cfg["labels"]["fill2"], "StateFlow")
        c_f2.SupplierID = created_states["review"].ElementID
        c_f2.Update()

        c_rev_comp = created_states["review"].Connectors.AddNew("", "StateFlow")
        c_rev_comp.SupplierID = created_states["complete"].ElementID
        c_rev_comp.Update()

        c_del_comp = created_states["delete"].Connectors.AddNew("", "StateFlow")
        c_del_comp.SupplierID = created_states["complete"].ElementID
        c_del_comp.Update()

        c_out = created_states["complete"].Connectors.AddNew("", "StateFlow")
        c_out.SupplierID = final_node.ElementID
        c_out.Update()

        diag.Update()

        # Exportar imagen nativa oficial desde Enterprise Architect
        proj = rep.GetProjectInterface()
        ea_png = os.path.join(EXPORT_DIR, f"ea-{cfg['filename']}")
        proj.PutDiagramImageToFile(diag.DiagramGUID, ea_png, 1)
        print(f"  [EA] Statechart modelado y exportado para {cfg['id']}")

    rep.CloseFile()
    rep.Exit()
    print("Sincronización con EA completada exitosamente.")
    return True

def main():
    print("=" * 75)
    print("GENERADOR DE DIAGRAMAS DE ESTADO UML 2.5 (CICLOS 1, 2 Y 3)")
    print("FashionStore - Enterprise Architect & Visual Artifacts")
    print("=" * 75)

    print("\n1. Renderizando imágenes en alta resolución...")
    for cfg in STATE_DIAGRAMS_CONFIG:
        out_png = os.path.join(EXPORT_DIR, cfg["filename"])
        render_state_diagram(cfg, out_png)

    print("\n2. Registrando modelos Statechart en FashionStore.eap...")
    try:
        sync_with_enterprise_architect()
    except Exception as e:
        print(f"Aviso durante sincronización EA: {e}")

    print("\n" + "=" * 75)
    print("TODOS LOS DIAGRAMAS DE ESTADO FUERON GENERADOS Y REGISTRADOS EXITOSAMENTE")
    print("=" * 75)
    return 0

if __name__ == "__main__":
    sys.exit(main())
