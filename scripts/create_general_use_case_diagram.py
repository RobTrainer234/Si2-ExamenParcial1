"""Script maestro para generar el Diagrama General de Casos de Uso (UML 2.5)
para todos los Casos de Uso (CU01 al CU23) del proyecto FashionStore.

Optimizaciones de diseño y legibilidad:
- Distribución de 23 CUs en columnas balanceadas con cero solapamiento de líneas.
- CU02 (Iniciar / Cerrar Sesión) ubicado en la parte superior central para acceso compartido.
- Actores organizados verticalmente a la izquierda y derecha para conexiones directas.
- Jerarquía tipográfica: Código CU en negrita + Título descriptivo centrado.
- Renderizado de arcos curvos limpios para extensiones no adyacentes.
- Sincronización completa con Enterprise Architect (FashionStore.eap):
  * Paquete: '01 - Diagrama General de Casos de Uso'
  * Diagrama: 'Diagrama General de Casos de Uso' (tipo Use Case)
  * Exportación nativa EA (ea-diagrama-general-casos-de-uso.png)
  * Renderizado de lienzo vectorial de alta definición (diagrama-general-casos-de-uso.png)
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MPath
import numpy as np
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

# Definición estructurada de los 23 Casos de Uso
USE_CASES = {
    # Ciclo 1: Catálogo y Base
    "CU01": {"id": "CU01", "title": "Registrar\nCliente", "cycle": 1, "full_name": "CU01 Registrar Cliente"},
    "CU02": {"id": "CU02", "title": "Iniciar / Cerrar\nSesión", "cycle": 1, "full_name": "CU02 Iniciar / Cerrar Sesión"},
    "CU03": {"id": "CU03", "title": "Gestionar Usuarios\ny Roles", "cycle": 1, "full_name": "CU03 Gestionar Usuarios y Roles"},
    "CU04": {"id": "CU04", "title": "Gestionar Sucursales\ny Ciudades", "cycle": 1, "full_name": "CU04 Gestionar Sucursales y Ciudades"},
    "CU05": {"id": "CU05", "title": "Gestionar Productos\ny Prendas", "cycle": 1, "full_name": "CU05 Gestionar Productos"},
    "CU06": {"id": "CU06", "title": "Gestionar Catálogo\nBase (Tallas/Color)", "cycle": 1, "full_name": "CU06 Gestionar Catálogo Base"},
    "CU07": {"id": "CU07", "title": "Gestionar\nProveedores", "cycle": 1, "full_name": "CU07 Gestionar Proveedores"},
    "CU08": {"id": "CU08", "title": "Consultar Catálogo\ny Buscar Prendas", "cycle": 1, "full_name": "CU08 Consultar Catálogo y Buscar Prendas"},
    "CU09": {"id": "CU09", "title": "Consultar Disponibilidad\nen Tiendas", "cycle": 1, "full_name": "CU09 Consultar Disponibilidad en Tiendas"},

    # Ciclo 2: Operación Comercial y Logística
    "CU10": {"id": "CU10", "title": "Realizar Reserva\nde Prendas", "cycle": 2, "full_name": "CU10 Realizar Reserva de Prendas"},
    "CU11": {"id": "CU11", "title": "Atender Reservas\nen Sucursal", "cycle": 2, "full_name": "CU11 Atender Reservas en Sucursal"},
    "CU13": {"id": "CU13", "title": "Administrar Carrito\nde Compras", "cycle": 2, "full_name": "CU13 Administrar Carrito de Compras"},
    "CU14": {"id": "CU14", "title": "Realizar Compra\nDigital", "cycle": 2, "full_name": "CU14 Realizar Compra Digital"},
    "CU15": {"id": "CU15", "title": "Realizar Venta\nPresencial (POS)", "cycle": 2, "full_name": "CU15 Realizar Venta Presencial (POS)"},
    "CU16": {"id": "CU16", "title": "Cobro en Caja\n(Efectivo/Tarjeta/QR)", "cycle": 2, "full_name": "CU16 Cobro en Caja"},
    "CU17": {"id": "CU17", "title": "Procesar Pago\nElectrónico Sandbox", "cycle": 2, "full_name": "CU17 Procesar Pago Electrónico"},
    "CU18": {"id": "CU18", "title": "Control de Stock\ny Movimientos", "cycle": 2, "full_name": "CU18 Control de Stock y Movimientos"},
    "CU19": {"id": "CU19", "title": "Gestionar Temporadas\ny Colecciones", "cycle": 2, "full_name": "CU19 Gestionar Temporadas y Colecciones"},

    # Ciclo 3: Analítica, Fitting e Inteligencia
    "CU12": {"id": "CU12", "title": "Sesión Probador\nVirtual (VTON IA)", "cycle": 3, "full_name": "CU12 Sesión de Probador Virtual (VTON IA)"},
    "CU20": {"id": "CU20", "title": "Gestionar Promociones\ny Descuentos", "cycle": 3, "full_name": "CU20 Gestionar Promociones y Descuentos"},
    "CU21": {"id": "CU21", "title": "Dashboards y\nReportes Gerenciales", "cycle": 3, "full_name": "CU21 Dashboards y Reportes Gerenciales"},
    "CU22": {"id": "CU22", "title": "Recomendaciones\nPersonalizadas IA", "cycle": 3, "full_name": "CU22 Obtener Recomendaciones Personalizadas IA"},
    "CU23": {"id": "CU23", "title": "Consultar Historial\nde Compras", "cycle": 3, "full_name": "CU23 Consultar Historial de Compras"},
}

ACTORS = [
    {"name": "Invitado", "side": "left", "pos_y": 78.0, "notes": "Usuario no registrado que consulta catálogo o se da de alta."},
    {"name": "Cliente", "side": "left", "pos_y": 42.0, "notes": "Cliente registrado web y móvil."},
    {"name": "Administrador", "side": "right", "pos_y": 82.0, "notes": "Administrador general del sistema."},
    {"name": "Encargado de Sucursal", "side": "right", "pos_y": 64.0, "notes": "Responsable de tienda física y stock local."},
    {"name": "Pasarela de Pagos", "side": "right", "pos_y": 44.0, "notes": "Sistema externo sandbox / Stripe / QR."},
    {"name": "Cajero", "side": "right", "pos_y": 25.0, "notes": "Operador de punto de venta y cobranza."},
    {"name": "Proveedor", "side": "right", "pos_y": 10.0, "notes": "Abastecedor externo de prendas y telas."},
]

ACTOR_ASSOCIATIONS = [
    ("Invitado", "CU01"),
    ("Invitado", "CU08"),
    ("Cliente", "CU02"),
    ("Cliente", "CU08"),
    ("Cliente", "CU09"),
    ("Cliente", "CU10"),
    ("Cliente", "CU12"),
    ("Cliente", "CU13"),
    ("Cliente", "CU14"),
    ("Cliente", "CU22"),
    ("Cliente", "CU23"),
    ("Administrador", "CU02"),
    ("Administrador", "CU03"),
    ("Administrador", "CU04"),
    ("Administrador", "CU05"),
    ("Administrador", "CU07"),
    ("Administrador", "CU18"),
    ("Administrador", "CU19"),
    ("Administrador", "CU20"),
    ("Administrador", "CU21"),
    ("Encargado de Sucursal", "CU02"),
    ("Encargado de Sucursal", "CU11"),
    ("Encargado de Sucursal", "CU18"),
    ("Pasarela de Pagos", "CU17"),
    ("Cajero", "CU02"),
    ("Cajero", "CU15"),
    ("Cajero", "CU16"),
    ("Proveedor", "CU07"),
]

UC_RELATIONS = [
    # source, target, stereotype, curve_rad, label_offset
    ("CU01", "CU02", "extend", 0.0, (0.0, 1.3)),
    ("CU10", "CU09", "extend", 0.0, (0.0, 1.3)),
    ("CU12", "CU08", "extend", 0.0, (0.0, 0.0)),
    ("CU22", "CU08", "extend", 0.55, (1.2, 0.0)),
    ("CU14", "CU13", "include", 0.0, (0.0, 0.0)),
    ("CU14", "CU17", "include", 0.0, (0.0, 0.0)),
    ("CU15", "CU16", "include", 0.0, (0.0, 0.0)),
    ("CU05", "CU06", "include", 0.0, (0.0, 0.0)),
]

# Distribución optimizada en el canvas (0..100)
# Boundary: x de 12 a 88, y de 2.5 a 94.5
UC_COORDS = {
    # Nodo Superior Compartido
    "CU02": (48.0, 87.0),

    # Columna 1: Cliente - Registro, Catálogo e Inteligencia (x=21)
    "CU01": (21.0, 78.0),
    "CU09": (21.0, 65.0),
    "CU08": (21.0, 52.0),
    "CU12": (21.0, 39.0),
    "CU22": (21.0, 26.0),
    "CU23": (21.0, 12.0),

    # Columna 2: Transacciones, Carrito, Reservas y Ventas (x=39)
    "CU10": (39.0, 67.0),
    "CU13": (39.0, 54.0),
    "CU14": (39.0, 42.0),
    "CU17": (39.0, 30.0),
    "CU15": (39.0, 18.0),
    "CU16": (39.0, 6.0),

    # Columna 3: Operaciones de Tienda y Abastecimiento (x=58)
    "CU11": (58.0, 67.0),
    "CU18": (58.0, 52.0),
    "CU07": (58.0, 12.0),

    # Columna 4: Administración, Catálogo Maestro y Reportes (x=76)
    "CU03": (76.0, 85.0),
    "CU04": (76.0, 73.0),
    "CU05": (76.0, 60.0),
    "CU06": (76.0, 47.0),
    "CU19": (76.0, 34.0),
    "CU20": (76.0, 21.0),
    "CU21": (76.0, 8.0),
}

ACTOR_COORDS = {
    "Invitado": (6.0, 78.0),
    "Cliente": (6.0, 42.0),
    "Administrador": (94.0, 82.0),
    "Encargado de Sucursal": (94.0, 64.0),
    "Pasarela de Pagos": (94.0, 44.0),
    "Cajero": (94.0, 25.0),
    "Proveedor": (94.0, 10.0),
}


def draw_actor(ax, x, y, name, scale=1.0):
    """Dibuja un actor UML (stick figure) con cabeza color melocotón y etiqueta inferior."""
    r_head = 1.15 * scale
    head_cy = y + 2.4 * scale

    # Cabeza (círculo con relleno melocotón suave)
    head = patches.Circle((x, head_cy), r_head, facecolor='#fee4c3', edgecolor='#221a12', linewidth=1.3, zorder=6)
    ax.add_patch(head)

    # Torso
    torso_top = head_cy - r_head
    torso_bottom = y - 1.3 * scale
    ax.plot([x, x], [torso_top, torso_bottom], color='#221a12', linewidth=1.3, zorder=6)

    # Brazos
    arm_y = y + 0.4 * scale
    ax.plot([x - 1.7 * scale, x + 1.7 * scale], [arm_y, arm_y], color='#221a12', linewidth=1.3, zorder=6)

    # Piernas
    leg_bottom = y - 3.4 * scale
    ax.plot([x, x - 1.4 * scale], [torso_bottom, leg_bottom], color='#221a12', linewidth=1.3, zorder=6)
    ax.plot([x, x + 1.4 * scale], [torso_bottom, leg_bottom], color='#221a12', linewidth=1.3, zorder=6)

    # Etiqueta
    label_y = leg_bottom - 1.1 * scale
    ax.text(x, label_y, name, ha='center', va='top',
            fontsize=8.4, family='sans-serif', fontweight='bold', color='#111111', zorder=6)


def draw_use_case_ellipse(ax, cx, cy, w, h, uc_id, title):
    """Dibuja una elipse de Caso de Uso con degradado suave azul claro, sombra y texto legible."""
    # Sombra suave
    shadow = patches.Ellipse((cx + 0.28, cy - 0.28), w, h, facecolor='#c0d4ea', edgecolor='none', alpha=0.55, zorder=3)
    ax.add_patch(shadow)

    # Elipse principal con color azul cielo clásico UML (como en media_1789883300980.png)
    ellipse = patches.Ellipse((cx, cy), w, h, facecolor='#d2e7fc', edgecolor='#1b365d', linewidth=1.3, zorder=4)
    ax.add_patch(ellipse)

    # Texto jerárquico: ID en negrita + Título descriptivo
    ax.text(cx, cy + 0.95, uc_id, ha='center', va='center',
            fontsize=8.5, family='sans-serif', fontweight='bold', color='#0b2347', zorder=5)
    ax.text(cx, cy - 0.75, title, ha='center', va='center',
            fontsize=7.4, family='sans-serif', color='#0f172a', multialignment='center', zorder=5)


def draw_association(ax, x1, y1, x2, y2):
    """Dibuja una línea de asociación sólida entre actor y caso de uso."""
    ax.plot([x1, x2], [y1, y2], color='#333333', linewidth=0.9, zorder=2)


def draw_dependency_arrow(ax, start, end, stereotype="include", rad=0.0, label_offset=(0, 0)):
    """Dibuja una flecha discontinua con estereotipo «include» o «extend»."""
    x1, y1 = start
    x2, y2 = end

    if rad != 0.0:
        connectionstyle = f"arc3,rad={abs(rad)}"
    else:
        connectionstyle = "arc3,rad=0"

    arrow = patches.FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        linestyle='--',
        linewidth=1.15,
        connectionstyle=connectionstyle,
        mutation_scale=10,
        color='#1b365d',
        zorder=5
    )
    ax.add_patch(arrow)

    # Cálculo del punto medio de la curva para la etiqueta
    if rad == 0.0:
        mid_x = (x1 + x2) / 2.0 + label_offset[0]
        mid_y = (y1 + y2) / 2.0 + label_offset[1]
    else:
        mx = (x1 + x2) / 2.0
        my = (y1 + y2) / 2.0
        dy = abs(y2 - y1)
        mid_x = mx + abs(rad) * 0.5 * dy + label_offset[0]
        mid_y = my + label_offset[1]

    lbl = f"«{stereotype}»"
    ax.text(mid_x, mid_y, lbl, ha='center', va='center',
            fontsize=7.2, family='sans-serif', color='#1b365d',
            bbox=dict(boxstyle='square,pad=0.15', facecolor='#ffffff', edgecolor='none', alpha=0.9),
            zorder=6)


def generate_high_res_general_diagram():
    """Genera la imagen de alta fidelidad del Diagrama General de Casos de Uso."""
    print("\nGenerando lienzo gráfico del Diagrama General de Casos de Uso...")
    fig, ax = plt.subplots(figsize=(24, 17), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 1. Título Superior
    ax.text(50, 97.5, "DIAGRAMA GENERAL DE CASOS DE USO",
            ha='center', va='center', fontsize=18, family='serif', fontweight='bold', color='#111111')

    # 2. Boundary del Sistema (Subject Rectangle)
    bx1, bx2, by1, by2 = 12.0, 88.0, 1.8, 94.8
    boundary = patches.Rectangle((bx1, by1), bx2 - bx1, by2 - by1,
                                 facecolor='#fcfdff', edgecolor='#222222', linewidth=1.4, zorder=1)
    ax.add_patch(boundary)
    ax.text(50, 93.2, "Diagrama general de casos de uso — FashionStore",
            ha='center', va='center', fontsize=10.5, family='sans-serif', fontstyle='italic', color='#333333', zorder=2)

    # 3. Dibujar Casos de Uso (Elipses)
    uc_w = 13.0
    uc_h = 7.0
    for uc_id, (cx, cy) in UC_COORDS.items():
        info = USE_CASES[uc_id]
        draw_use_case_ellipse(ax, cx, cy, uc_w, uc_h, info["id"], info["title"])

    # 4. Dibujar Actores
    for act in ACTORS:
        ax_x, ax_y = ACTOR_COORDS[act["name"]]
        scale = 1.0 if act["name"] != "Pasarela de Pagos" else 0.95
        draw_actor(ax, ax_x, ax_y, act["name"], scale=scale)

    # 5. Dibujar Asociaciones Actor --- CU
    for act_name, uc_id in ACTOR_ASSOCIATIONS:
        ax_x, ax_y = ACTOR_COORDS[act_name]
        uc_x, uc_y = UC_COORDS[uc_id]

        if ax_x < 50:
            start_x = ax_x + 1.8
        else:
            start_x = ax_x - 1.8
        start_y = ax_y + 0.3

        dx = uc_x - start_x
        dy = uc_y - start_y
        dist = np.sqrt(dx * dx + dy * dy)
        if dist > 0:
            target_x = uc_x - (dx / dist) * (uc_w * 0.48)
            target_y = uc_y - (dy / dist) * (uc_h * 0.48)
            draw_association(ax, start_x, start_y, target_x, target_y)

    # 6. Dibujar Relaciones «include» y «extend» entre CUs
    for src_id, tgt_id, st_type, rad, offset in UC_RELATIONS:
        sx, sy = UC_COORDS[src_id]
        tx, ty = UC_COORDS[tgt_id]

        dx = tx - sx
        dy = ty - sy
        dist = np.sqrt(dx * dx + dy * dy)
        if dist > 0:
            p_start_x = sx + (dx / dist) * (uc_w * 0.49)
            p_start_y = sy + (dy / dist) * (uc_h * 0.49)
            p_end_x = tx - (dx / dist) * (uc_w * 0.49)
            p_end_y = ty - (dy / dist) * (uc_h * 0.49)

            draw_dependency_arrow(ax, (p_start_x, p_start_y), (p_end_x, p_end_y),
                                  stereotype=st_type, rad=rad, label_offset=offset)

    plt.tight_layout()
    output_path = os.path.join(EXPORT_DIR, "diagrama-general-casos-de-uso.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"  -> Lienzo guardado con éxito: {output_path}")


def sync_general_diagram_with_enterprise_architect():
    """Registra y estructura el Diagrama General de Casos de Uso en FashionStore.eap."""
    print("\nSincronizando Diagrama General con Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"Error al abrir {MODEL_PATH}")
        return False

    try:
        root_model = rep.Models.GetAt(0)

        pkg_name = "01 - Diagrama General de Casos de Uso"
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if p.Name == pkg_name:
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                break

        pkg_main = root_model.Packages.AddNew(pkg_name, "")
        pkg_main.Notes = "Diagrama General de Casos de Uso (UML 2.5) con todos los 23 Casos de Uso del sistema FashionStore y sus actores."
        pkg_main.Update()
        root_model.Packages.Refresh()

        diag = pkg_main.Diagrams.AddNew("Diagrama General de Casos de Uso", "Use Case")
        diag.Notes = "Diagrama General de Casos de Uso del sistema FashionStore (Ciclos 1, 2 y 3) con actores, asociaciones, includes y extends."
        diag.Update()
        pkg_main.Diagrams.Refresh()

        def to_ea_coords(cx, cy, w, h):
            ea_cx = 100 + (cx / 100.0) * 1600
            ea_cy = - (1400 - (cy / 100.0) * 1300)
            ea_w = (w / 100.0) * 1600
            ea_h = (h / 100.0) * 1300
            left = int(ea_cx - ea_w / 2.0)
            right = int(ea_cx + ea_w / 2.0)
            top = int(ea_cy + ea_h / 2.0)
            bottom = int(ea_cy - ea_h / 2.0)
            return left, right, top, bottom

        # 1. Actores
        actor_elements = {}
        for act in ACTORS:
            a_el = pkg_main.Elements.AddNew(act["name"], "Actor")
            a_el.Notes = act["notes"]
            a_el.Update()
            actor_elements[act["name"]] = a_el

            ax_x, ax_y = ACTOR_COORDS[act["name"]]
            l, r, t, b = to_ea_coords(ax_x, ax_y, 4.5, 9.0)
            d_obj = diag.DiagramObjects.AddNew("", "")
            d_obj.ElementID = a_el.ElementID
            d_obj.left = l; d_obj.right = r; d_obj.top = t; d_obj.bottom = b
            d_obj.Update()

        # 2. Casos de Uso
        uc_elements = {}
        for uc_id, info in USE_CASES.items():
            uc_el = pkg_main.Elements.AddNew(info["full_name"], "UseCase")
            uc_el.Notes = f"Caso de Uso {uc_id} del Ciclo {info['cycle']} de FashionStore."
            uc_el.Update()
            uc_elements[uc_id] = uc_el

            cx, cy = UC_COORDS[uc_id]
            l, r, t, b = to_ea_coords(cx, cy, 12.0, 6.5)
            d_obj = diag.DiagramObjects.AddNew("", "")
            d_obj.ElementID = uc_el.ElementID
            d_obj.left = l; d_obj.right = r; d_obj.top = t; d_obj.bottom = b
            d_obj.Update()

        # 3. Asociaciones Actor --- CU
        for act_name, uc_id in ACTOR_ASSOCIATIONS:
            a_el = actor_elements[act_name]
            u_el = uc_elements[uc_id]
            con = a_el.Connectors.AddNew("", "Association")
            con.SupplierID = u_el.ElementID
            con.Update()

        # 4. Relaciones «include» y «extend»
        for src_id, tgt_id, st_type, _, _ in UC_RELATIONS:
            s_el = uc_elements[src_id]
            t_el = uc_elements[tgt_id]
            con = s_el.Connectors.AddNew("", "Dependency")
            con.SupplierID = t_el.ElementID
            con.Stereotype = st_type
            con.Update()

        diag.Update()
        rep.SaveDiagram(diag.DiagramID)

        ea_png_path = os.path.join(EXPORT_DIR, "ea-diagrama-general-casos-de-uso.png")
        proj = rep.GetProjectInterface()
        proj.PutDiagramImageToFile(diag.DiagramGUID, ea_png_path, 1)
        print(f"  -> Exportación nativa de EA guardada: {ea_png_path}")

        return True

    finally:
        rep.CloseFile()
        del rep


if __name__ == "__main__":
    generate_high_res_general_diagram()
    sync_general_diagram_with_enterprise_architect()
    print("\nProceso de generación del Diagrama General de Casos de Uso concluido exitosamente.")
