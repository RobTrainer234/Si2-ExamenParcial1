"""
Diseño Lógico de la Arquitectura — FashionStore SI2
Genera el canvas y sincroniza Enterprise Architect correctamente:
1. Elimina el Root Model huérfano '09 - Diseño Lógico de la Arquitectura' si existe en rep.Models.
2. Crea el paquete '09 - Diseño Lógico de la Arquitectura' dentro de 'Model' (rep.Models.GetAt(0)).
3. Crea el Diagrama 'Diseño Lógico de la Arquitectura' directamente en ese paquete para apertura con doble clic.
4. Crea los 10 paquetes y las dependencias UML 2.5 correspondientes a todo el proyecto.
5. Exporta el diagrama tanto nativo de EA como en canvas vectorial de alta fidelidad.
"""

import os
import sys
import subprocess
import time
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
OUT_DIR    = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"
CANVAS_PNG = os.path.join(OUT_DIR, "logical-architecture-diagram.png")
EA_PNG     = os.path.join(OUT_DIR, "ea-logical-architecture-diagram.png")

os.makedirs(OUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# 1. CANVAS MATPLOTLIB
# ─────────────────────────────────────────────────────────────

def draw_uml_package(ax, x, y, width, height, title,
                     fill="#ffecd2", edge="#222222",
                     tab_w_ratio=0.45, tab_h_ratio=0.22,
                     fontsize=9.0):
    tab_w = width * tab_w_ratio
    tab_h = height * tab_h_ratio

    # Pestaña
    tab = mpatches.Rectangle(
        (x, y + height), tab_w, tab_h,
        facecolor=fill, edgecolor=edge, linewidth=1.1,
        zorder=3
    )
    ax.add_patch(tab)

    # Cuerpo
    body = mpatches.Rectangle(
        (x, y), width, height,
        facecolor=fill, edgecolor=edge, linewidth=1.1,
        zorder=3
    )
    ax.add_patch(body)

    # Encabezado
    header_h = height * 0.28
    header_line = mpatches.Rectangle(
        (x, y + height - header_h), width, header_h,
        facecolor="#fce2c2", edgecolor=edge, linewidth=0.8,
        zorder=4
    )
    ax.add_patch(header_line)

    ax.text(
        x + width / 2.0, y + height - header_h / 2.0,
        title,
        ha="center", va="center",
        fontsize=fontsize, color="#111111", zorder=5
    )


def draw_dashed_arrow(ax, x1, y1, x2, y2, color="#111111", lw=1.2, arrowstyle="->"):
    arrow = FancyArrowPatch(
        posA=(x1, y1), posB=(x2, y2),
        arrowstyle=arrowstyle,
        mutation_scale=14,
        color=color,
        linewidth=lw,
        linestyle="--",
        zorder=6
    )
    ax.add_patch(arrow)


def generate_canvas():
    fig, ax = plt.subplots(figsize=(15, 12), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    # Título superior izquierdo
    ax.text(
        0.05, 0.965,
        "Diseño lógico de la arquitectura",
        ha="left", va="center",
        fontsize=22, fontweight="bold",
        family="serif", color="#000000"
    )

    frame_x = 0.05
    frame_y = 0.03
    frame_w = 0.90
    frame_h = 0.90

    outer_box = mpatches.Rectangle(
        (frame_x, frame_y), frame_w, frame_h,
        facecolor="#ebf1f6", edgecolor="#222222", linewidth=1.5,
        zorder=1
    )
    ax.add_patch(outer_box)

    y_div1 = 0.64   # Separa Vista de controlador
    y_div2 = 0.41   # Separa controlador de Modelo

    ax.plot([frame_x, frame_x + frame_w], [y_div1, y_div1],
            color="#222222", linewidth=1.3, zorder=2)
    ax.plot([frame_x, frame_x + frame_w], [y_div2, y_div2],
            color="#222222", linewidth=1.3, zorder=2)

    label_bbox = dict(facecolor="#ebf1f6", edgecolor="none", pad=3.0)

    ax.text(0.50, 0.910, "Vista",
            ha="center", va="center",
            fontsize=12, color="#111111", zorder=8,
            bbox=label_bbox)

    ax.text(0.50, 0.620, "controlador",
            ha="center", va="center",
            fontsize=12, color="#111111", zorder=8,
            bbox=label_bbox)

    ax.text(0.50, 0.395, "Modelo",
            ha="center", va="center",
            fontsize=12, color="#111111", zorder=8,
            bbox=label_bbox)

    pkg_w = 0.23
    pkg_h = 0.12

    col1_x = 0.10
    col2_x = 0.385
    col3_x = 0.67

    row_vista_y = 0.73
    row_ctrl_y  = 0.46
    row_model_y = 0.22

    # Vista
    draw_uml_package(ax, col1_x, row_vista_y, pkg_w, pkg_h,
                     "Paquete Vista actividades de usuario")
    draw_uml_package(ax, col2_x, row_vista_y, pkg_w, pkg_h,
                     "Paquete Vista Venta de productos")
    draw_uml_package(ax, col3_x, row_vista_y, pkg_w, pkg_h,
                     "Paquete vista Reportes")

    # Controlador
    draw_uml_package(ax, col1_x, row_ctrl_y, pkg_w, pkg_h,
                     "Paquete actividades de usuario Controllers", fontsize=8.5)
    draw_uml_package(ax, col2_x, row_ctrl_y, pkg_w, pkg_h,
                     "Paquete Venta de productos Controllers", fontsize=8.5)
    draw_uml_package(ax, col3_x, row_ctrl_y, pkg_w, pkg_h,
                     "Paquete Reportes Controller")

    # Modelo
    draw_uml_package(ax, col1_x, row_model_y, pkg_w, pkg_h,
                     "Paquete modelos actividades de usuario", fontsize=8.5)
    draw_uml_package(ax, col2_x, row_model_y, pkg_w, pkg_h,
                     "Paquete modelos Venta de productos", fontsize=8.5)
    draw_uml_package(ax, col3_x, row_model_y, pkg_w, pkg_h,
                     "Paquete modelos Reportes")

    # Base de Datos
    db_w = 0.20
    db_h = 0.10
    db_x = 0.40
    db_y = 0.05
    draw_uml_package(ax, db_x, db_y, db_w, db_h,
                     "Base de datos postgresql", tab_w_ratio=0.55)

    c1_cx = col1_x + pkg_w / 2.0
    c2_cx = col2_x + pkg_w / 2.0
    c3_cx = col3_x + pkg_w / 2.0

    # Controlador -> Vista (^)
    draw_dashed_arrow(ax, c1_cx, row_ctrl_y + pkg_h + 0.02, c1_cx, row_vista_y - 0.005)
    draw_dashed_arrow(ax, c2_cx, row_ctrl_y + pkg_h + 0.02, c2_cx, row_vista_y - 0.005)
    draw_dashed_arrow(ax, c3_cx, row_ctrl_y + pkg_h + 0.02, c3_cx, row_vista_y - 0.005)

    # Controlador Venta -> Controlador Usuario (<-)
    mid_ctrl_y = row_ctrl_y + pkg_h * 0.55
    draw_dashed_arrow(ax, col2_x, mid_ctrl_y, col1_x + pkg_w, mid_ctrl_y)

    # Controlador -> Modelo (v)
    draw_dashed_arrow(ax, c1_cx, row_ctrl_y - 0.005, c1_cx, row_model_y + pkg_h + 0.02)
    draw_dashed_arrow(ax, c2_cx, row_ctrl_y - 0.005, c2_cx, row_model_y + pkg_h + 0.02)
    draw_dashed_arrow(ax, c3_cx, row_ctrl_y - 0.005, c3_cx, row_model_y + pkg_h + 0.02)

    # Controlador Usuario -> Modelo Venta (diagonal)
    draw_dashed_arrow(ax, col1_x + pkg_w * 0.75, row_ctrl_y - 0.005,
                          col2_x + pkg_w * 0.20, row_model_y + pkg_h + 0.02)

    # Modelos -> Base de Datos
    db_top_y = db_y + db_h + 0.02
    db_cx = db_x + db_w / 2.0
    draw_dashed_arrow(ax, c1_cx + pkg_w * 0.25, row_model_y - 0.005, db_x + db_w * 0.10, db_top_y)
    draw_dashed_arrow(ax, c2_cx, row_model_y - 0.005, db_cx, db_top_y)
    draw_dashed_arrow(ax, c3_cx - pkg_w * 0.25, row_model_y - 0.005, db_x + db_w * 0.90, db_top_y)

    plt.tight_layout()
    fig.savefig(CANVAS_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Canvas generado: {CANVAS_PNG}")


# ─────────────────────────────────────────────────────────────
# 2. SINCRONIZACIÓN CON ENTERPRISE ARCHITECT
# ─────────────────────────────────────────────────────────────

def sync_with_ea():
    import win32com.client

    rep = None
    try:
        rep = win32com.client.Dispatch("EA.Repository")
        rep.OpenFile(MODEL_PATH)
        time.sleep(1)

        # 1. Limpiar root model huérfano si existe fuera de 'Model'
        for i in range(rep.Models.Count - 1, -1, -1):
            m = rep.Models.GetAt(i)
            if m.Name == "09 - Diseño Lógico de la Arquitectura":
                print(f"Eliminando Root Model huérfano: {m.Name}")
                rep.Models.Delete(i)
                rep.Models.Refresh()

        # 2. Acceder al modelo principal 'Model' (PackageID = 1)
        root_model = rep.Models.GetAt(0)
        print(f"Modelo raíz principal: {root_model.Name} (ID: {root_model.PackageID})")

        pkg_name = "09 - Diseño Lógico de la Arquitectura"

        # Si ya existía dentro de 'Model', eliminarlo para recrearlo limpio
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if p.Name == pkg_name:
                print(f"Limpiando paquete previo dentro de Model: {p.Name}")
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                break

        # Crear el paquete 09 dentro de Model
        pkg_main = root_model.Packages.AddNew(pkg_name, "")
        pkg_main.Notes = (
            "Diseño Lógico de la Arquitectura (UML 2.5) del sistema FashionStore. "
            "Estructura MVC de 3 capas (Vista, Controlador, Modelo) y Base de Datos PostgreSQL."
        )
        pkg_main.Update()
        root_model.Packages.Refresh()
        print(f"Paquete creado exitosamente: {pkg_name} (ID: {pkg_main.PackageID})")

        # Crear el Diagrama directamente en el paquete
        diag_name = "Diseño Lógico de la Arquitectura"
        diag = pkg_main.Diagrams.AddNew(diag_name, "Package")
        diag.Notes = "Diagrama de Paquetes — Diseño Lógico de la Arquitectura de FashionStore"
        diag.Update()
        pkg_main.Diagrams.Refresh()
        print(f"Diagrama creado: {diag_name} (ID: {diag.DiagramID})")

        # Función para coordenadas en EA (left, right, top, bottom negativos)
        def to_ea_coords(cx, cy, w, h):
            ea_cx = 80 + (cx / 100.0) * 1100
            ea_cy = - (80 + (cy / 100.0) * 850)
            ea_w = (w / 100.0) * 1100
            ea_h = (h / 100.0) * 850
            left = int(ea_cx - ea_w / 2.0)
            right = int(ea_cx + ea_w / 2.0)
            top = int(ea_cy + ea_h / 2.0)
            bottom = int(ea_cy - ea_h / 2.0)
            return left, right, top, bottom

        # Definición de los 10 paquetes
        packages_def = [
            # Capa Vista (y = 15%)
            {"name": "Paquete Vista actividades de usuario", "x": 18, "y": 15, "w": 25, "h": 12},
            {"name": "Paquete Vista Venta de productos",     "x": 50, "y": 15, "w": 25, "h": 12},
            {"name": "Paquete vista Reportes",               "x": 82, "y": 15, "w": 25, "h": 12},

            # Capa Controlador (y = 42%)
            {"name": "Paquete actividades de usuario Controllers", "x": 18, "y": 42, "w": 25, "h": 12},
            {"name": "Paquete Venta de productos Controllers",     "x": 50, "y": 42, "w": 25, "h": 12},
            {"name": "Paquete Reportes Controller",               "x": 82, "y": 42, "w": 25, "h": 12},

            # Capa Modelo (y = 70%)
            {"name": "Paquete modelos actividades de usuario", "x": 18, "y": 70, "w": 25, "h": 12},
            {"name": "Paquete modelos Venta de productos",     "x": 50, "y": 70, "w": 25, "h": 12},
            {"name": "Paquete modelos Reportes",               "x": 82, "y": 70, "w": 25, "h": 12},

            # Base de Datos (y = 92%)
            {"name": "Base de datos postgresql", "x": 50, "y": 92, "w": 22, "h": 10},
        ]

        created_elements = {}
        for pdef in packages_def:
            p_name = pdef["name"]
            el = pkg_main.Elements.AddNew(p_name, "Package")
            el.Update()
            pkg_main.Elements.Refresh()
            created_elements[p_name] = el

            l, r, t, b = to_ea_coords(pdef["x"], pdef["y"], pdef["w"], pdef["h"])
            d_obj = diag.DiagramObjects.AddNew("", "")
            d_obj.ElementID = el.ElementID
            d_obj.left = l
            d_obj.right = r
            d_obj.top = t
            d_obj.bottom = b
            d_obj.Update()

        diag.DiagramObjects.Refresh()

        # Dependencias UML 2.5
        dependencies = [
            # Controlador -> Vista (^)
            ("Paquete actividades de usuario Controllers", "Paquete Vista actividades de usuario"),
            ("Paquete Venta de productos Controllers",     "Paquete Vista Venta de productos"),
            ("Paquete Reportes Controller",               "Paquete vista Reportes"),

            # Controlador Venta -> Controlador Usuario (<-)
            ("Paquete Venta de productos Controllers",     "Paquete actividades de usuario Controllers"),

            # Controlador -> Modelo (v)
            ("Paquete actividades de usuario Controllers", "Paquete modelos actividades de usuario"),
            ("Paquete Venta de productos Controllers",     "Paquete modelos Venta de productos"),
            ("Paquete Reportes Controller",               "Paquete modelos Reportes"),

            # Controlador Usuario -> Modelo Venta (diagonal)
            ("Paquete actividades de usuario Controllers", "Paquete modelos Venta de productos"),

            # Modelos -> Base de Datos
            ("Paquete modelos actividades de usuario", "Base de datos postgresql"),
            ("Paquete modelos Venta de productos",     "Base de datos postgresql"),
            ("Paquete modelos Reportes",               "Base de datos postgresql"),
        ]

        for src_name, tgt_name in dependencies:
            src_el = created_elements[src_name]
            tgt_el = created_elements[tgt_name]
            conn = src_el.Connectors.AddNew("", "Dependency")
            conn.SupplierID = tgt_el.ElementID
            conn.Update()
            src_el.Connectors.Refresh()

        diag.Update()
        rep.SaveDiagram(diag.DiagramID)

        # Exportar imagen nativa de EA
        proj = rep.GetProjectInterface()
        proj.PutDiagramImageToFile(diag.DiagramGUID, EA_PNG, 1)
        print(f"Exportación nativa de EA guardada: {EA_PNG}")

        return True

    except Exception as e:
        print(f"Error sincronizando con EA: {e}")
        traceback.print_exc()
        return False
    finally:
        if rep:
            try:
                rep.CloseFile()
                del rep
            except Exception:
                pass


if __name__ == "__main__":
    subprocess.run(["taskkill", "/F", "/IM", "EA.exe"], capture_output=True)
    time.sleep(1)

    print("\n--- Generando Canvas ---")
    generate_canvas()

    print("\n--- Sincronizando con Enterprise Architect ---")
    sync_with_ea()

    print("\n¡Proceso finalizado con éxito!")
