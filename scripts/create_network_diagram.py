"""
Diagrama de Red — Topología AWS FashionStore (UML 2.5)
Genera el diagrama de red formal basado en la arquitectura segmentada:
1. Internet & Usuario
2. Routers de Borde (Internet Gateway / Route 53)
3. Firewall Perimetral (AWS WAF / Security Group)
4. DMZ: Servidor Web (Angular/CloudFront), DNS Server (Route 53), Servidor de Correo (Amazon SES)
5. Firewall Interno (Network ACLs / Security Groups)
6. VLAN Usuarios: Equipo Administrador / Consola POS
7. VLAN Aplicación: Servidor de Aplicaciones (FastAPI en ECS Fargate)
8. VLAN Datos: Base de Datos (AWS RDS PostgreSQL 17)

Sincroniza con Enterprise Architect en el paquete '10 - Diagrama de Red (Topología AWS)'
y genera el renderizado de alta fidelidad matching el modelo de referencia.
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
from matplotlib.patches import FancyArrowPatch, Circle, Polygon, Rectangle
from matplotlib.path import Path

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
OUT_DIR    = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"
CANVAS_PNG = os.path.join(OUT_DIR, "diagrama-red-aws.png")
EA_PNG     = os.path.join(OUT_DIR, "ea-diagrama-red-aws.png")

os.makedirs(OUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# 1. RENDERIZADO VECTORIAL DE ALTA FIDELIDAD (ESTILO MODELO)
# ─────────────────────────────────────────────────────────────

def draw_cloud(ax, cx, cy, width, height, label="Internet"):
    """Dibuja una nube estilizada con contorno bezier suave sin intersecciones internas."""
    verts = [
        (cx - width * 0.35, cy - height * 0.20),
        (cx - width * 0.52, cy - height * 0.10), (cx - width * 0.52, cy + height * 0.25), (cx - width * 0.30, cy + height * 0.35),
        (cx - width * 0.25, cy + height * 0.55), (cx - width * 0.05, cy + height * 0.55), (cx + width * 0.05, cy + height * 0.35),
        (cx + width * 0.15, cy + height * 0.50), (cx + width * 0.38, cy + height * 0.45), (cx + width * 0.40, cy + height * 0.20),
        (cx + width * 0.52, cy + height * 0.12), (cx + width * 0.52, cy - height * 0.18), (cx + width * 0.30, cy - height * 0.28),
        (cx + width * 0.15, cy - height * 0.38), (cx - width * 0.15, cy - height * 0.38), (cx - width * 0.35, cy - height * 0.20)
    ]
    codes = [Path.MOVETO] + [Path.CURVE4] * (len(verts) - 1)
    path = Path(verts, codes)
    patch = mpatches.PathPatch(path, facecolor='#ffffff', edgecolor='#222222', lw=1.4, zorder=3)
    ax.add_patch(patch)
    ax.text(cx, cy, label, ha="center", va="center", fontsize=11.5, color="#222222", zorder=5)


def draw_actor(ax, cx, cy, height, label="Usuario"):
    """Dibuja una figura humana (Actor UML) estilizada."""
    head_r = height * 0.16
    head_cy = cy + height * 0.38
    head = Circle((cx, head_cy), head_r, facecolor="#ffffff", edgecolor="#222222", linewidth=1.4, zorder=5)
    ax.add_patch(head)

    # Cuerpo
    neck_y = head_cy - head_r
    waist_y = cy - height * 0.08
    ax.plot([cx, cx], [neck_y, waist_y], color="#222222", lw=1.5, zorder=5)

    # Brazos
    arms_y = cy + height * 0.12
    arm_w = height * 0.28
    ax.plot([cx - arm_w, cx + arm_w], [arms_y, arms_y], color="#222222", lw=1.5, zorder=5)

    # Piernas
    leg_y = cy - height * 0.45
    leg_w = height * 0.25
    ax.plot([cx, cx - leg_w], [waist_y, leg_y], color="#222222", lw=1.5, zorder=5)
    ax.plot([cx, cx + leg_w], [waist_y, leg_y], color="#222222", lw=1.5, zorder=5)

    ax.text(cx, leg_y - 0.022, label, ha="center", va="top", fontsize=10.5, color="#111111", zorder=5)


def draw_router(ax, cx, cy, rx, ry):
    """Dibuja un router de red cilíndrico."""
    h = ry * 1.5
    # Parte inferior
    body = mpatches.Rectangle((cx - rx, cy - h), rx * 2, h, facecolor="#8a9ba8", edgecolor="#2f3640", lw=1.2, zorder=3)
    ax.add_patch(body)

    ellipse_bot = mpatches.Ellipse((cx, cy - h), rx * 2, ry, facecolor="#718093", edgecolor="#2f3640", lw=1.2, zorder=4)
    ax.add_patch(ellipse_bot)

    # Tapa superior
    ellipse_top = mpatches.Ellipse((cx, cy), rx * 2, ry, facecolor="#a4b0be", edgecolor="#2f3640", lw=1.2, zorder=5)
    ax.add_patch(ellipse_top)

    # Flechas cruzadas en la tapa superior
    arr_len = rx * 0.55
    arr_w = ry * 0.45
    ax.annotate("", xy=(cx - arr_len, cy - arr_w), xytext=(cx + arr_len, cy + arr_w),
                arrowprops=dict(arrowstyle="<->", color="#ffffff", lw=1.4), zorder=6)
    ax.annotate("", xy=(cx - arr_len, cy + arr_w), xytext=(cx + arr_len, cy - arr_w),
                arrowprops=dict(arrowstyle="<->", color="#ffffff", lw=1.4), zorder=6)


def draw_firewall(ax, cx, cy, w, h):
    """Dibuja el icono de muro de ladrillos (Firewall de red)."""
    wall = mpatches.Rectangle((cx - w / 2.0, cy - h / 2.0), w, h,
                              facecolor="#d63031", edgecolor="#2d3436", lw=1.3, zorder=5)
    ax.add_patch(wall)

    rows = 4
    row_h = h / rows
    for r in range(1, rows):
        ly = cy - h / 2.0 + r * row_h
        ax.plot([cx - w / 2.0, cx + w / 2.0], [ly, ly], color="#ffffff", lw=1.2, zorder=6)

    for r in range(rows):
        ly_bot = cy - h / 2.0 + r * row_h
        ly_top = ly_bot + row_h
        if r % 2 == 0:
            ax.plot([cx - w * 0.22, cx - w * 0.22], [ly_bot, ly_top], color="#ffffff", lw=1.0, zorder=6)
            ax.plot([cx + w * 0.22, cx + w * 0.22], [ly_bot, ly_top], color="#ffffff", lw=1.0, zorder=6)
        else:
            ax.plot([cx, cx], [ly_bot, ly_top], color="#ffffff", lw=1.0, zorder=6)


def draw_server(ax, cx, cy, w, h, label="", badge=None, label_pos="bottom"):
    """Dibuja una torre de servidor 3D."""
    depth_x = w * 0.22
    depth_y = h * 0.18

    # Cara frontal
    front = mpatches.Rectangle((cx - w / 2.0, cy - h / 2.0), w, h,
                               facecolor="#b2bec3", edgecolor="#2d3436", lw=1.2, zorder=4)
    ax.add_patch(front)

    # Tapa superior (perspectiva)
    top_poly = Polygon([
        (cx - w / 2.0, cy + h / 2.0),
        (cx - w / 2.0 + depth_x, cy + h / 2.0 + depth_y),
        (cx + w / 2.0 + depth_x, cy + h / 2.0 + depth_y),
        (cx + w / 2.0, cy + h / 2.0),
    ], facecolor="#dfe6e9", edgecolor="#2d3436", lw=1.2, zorder=4)
    ax.add_patch(top_poly)

    # Cara lateral derecha
    side_poly = Polygon([
        (cx + w / 2.0, cy - h / 2.0),
        (cx + w / 2.0 + depth_x, cy - h / 2.0 + depth_y),
        (cx + w / 2.0 + depth_x, cy + h / 2.0 + depth_y),
        (cx + w / 2.0, cy + h / 2.0),
    ], facecolor="#636e72", edgecolor="#2d3436", lw=1.2, zorder=4)
    ax.add_patch(side_poly)

    # Ranuras de discos en el frente
    slot_w = w * 0.70
    for s_idx in range(3):
        sy = cy + h * 0.18 - s_idx * (h * 0.20)
        slot = mpatches.Rectangle((cx - slot_w / 2.0, sy), slot_w, h * 0.09,
                                  facecolor="#2d3436", edgecolor="none", zorder=5)
        ax.add_patch(slot)
        led = Circle((cx + slot_w / 2.0 - 0.005, sy + h * 0.045), 0.0025,
                     facecolor="#00b894", edgecolor="none", zorder=6)
        ax.add_patch(led)

    if badge == "web":
        badge_r = w * 0.26
        bx = cx + w * 0.38
        by = cy - h * 0.28
        globe = Circle((bx, by), badge_r, facecolor="#0984e3", edgecolor="#ffffff", lw=1.5, zorder=7)
        ax.add_patch(globe)
        ax.plot([bx - badge_r, bx + badge_r], [by, by], color="#ffffff", lw=0.9, zorder=8)
        globe_ell = mpatches.Ellipse((bx, by), badge_r * 1.1, badge_r * 1.8,
                                     facecolor="none", edgecolor="#ffffff", lw=0.9, zorder=8)
        ax.add_patch(globe_ell)

    elif badge == "dns":
        bx = cx + w * 0.38
        by = cy - h * 0.28
        doc_w = w * 0.40
        doc_h = h * 0.38
        doc = mpatches.Rectangle((bx - doc_w / 2.0, by - doc_h / 2.0), doc_w, doc_h,
                                 facecolor="#74b9ff", edgecolor="#ffffff", lw=1.2, zorder=7)
        ax.add_patch(doc)
        for d_line in range(3):
            dly = by + doc_h * 0.2 - d_line * (doc_h * 0.2)
            ax.plot([bx - doc_w * 0.3, bx + doc_w * 0.3], [dly, dly], color="#ffffff", lw=1.0, zorder=8)

    elif badge == "db":
        bx = cx + w * 0.38
        by = cy - h * 0.30
        cyl_w = w * 0.45
        cyl_h = h * 0.38
        cyl_body = mpatches.Rectangle((bx - cyl_w / 2.0, by - cyl_h / 2.0), cyl_w, cyl_h,
                                      facecolor="#dfe6e9", edgecolor="#2d3436", lw=1.0, zorder=7)
        ax.add_patch(cyl_body)
        cyl_top = mpatches.Ellipse((bx, by + cyl_h / 2.0), cyl_w, cyl_h * 0.35,
                                   facecolor="#b2bec3", edgecolor="#2d3436", lw=1.0, zorder=8)
        ax.add_patch(cyl_top)
        cyl_bot = mpatches.Ellipse((bx, by - cyl_h / 2.0), cyl_w, cyl_h * 0.35,
                                   facecolor="#b2bec3", edgecolor="#2d3436", lw=1.0, zorder=8)
        ax.add_patch(cyl_bot)

    if label:
        if label_pos == "bottom":
            ax.text(cx, cy - h / 2.0 - 0.025, label, ha="center", va="top", fontsize=9.5, color="#111111", zorder=7)
        elif label_pos == "below_close":
            ax.text(cx, cy - h / 2.0 - 0.015, label, ha="center", va="top", fontsize=9.5, color="#111111", zorder=7)


def draw_workstation(ax, cx, cy, w, h, label="Equipo administrador"):
    """Dibuja una estación de trabajo (PC monitor + torre + teclado)."""
    mon_w = w * 0.65
    mon_h = h * 0.60
    mon_x = cx - w * 0.15
    mon_y = cy
    screen = mpatches.Rectangle((mon_x - mon_w / 2.0, mon_y - mon_h / 2.0), mon_w, mon_h,
                                facecolor="#dfe6e9", edgecolor="#2d3436", lw=1.2, zorder=5)
    ax.add_patch(screen)
    inner_screen = mpatches.Rectangle((mon_x - mon_w * 0.42, mon_y - mon_h * 0.40), mon_w * 0.84, mon_h * 0.76,
                                      facecolor="#74b9ff", edgecolor="none", zorder=6)
    ax.add_patch(inner_screen)

    # Base monitor
    ax.plot([mon_x, mon_x], [mon_y - mon_h / 2.0, mon_y - mon_h / 2.0 - h * 0.12], color="#2d3436", lw=2, zorder=5)
    stand = mpatches.Rectangle((mon_x - mon_w * 0.25, mon_y - mon_h / 2.0 - h * 0.16), mon_w * 0.50, h * 0.04,
                               facecolor="#636e72", edgecolor="#2d3436", lw=1.0, zorder=5)
    ax.add_patch(stand)

    # Torre CPU al lado izquierdo
    tower_w = w * 0.25
    tower_h = h * 0.70
    tower_x = cx - w * 0.45
    tower = mpatches.Rectangle((tower_x - tower_w / 2.0, cy - tower_h / 2.0), tower_w, tower_h,
                               facecolor="#b2bec3", edgecolor="#2d3436", lw=1.2, zorder=5)
    ax.add_patch(tower)

    # Teclado en la base
    kb_w = mon_w * 0.85
    kb_h = h * 0.08
    kb = mpatches.Rectangle((mon_x - kb_w / 2.0, mon_y - mon_h / 2.0 - h * 0.26), kb_w, kb_h,
                            facecolor="#b2bec3", edgecolor="#2d3436", lw=1.0, zorder=5)
    ax.add_patch(kb)

    ax.text(cx, cy - h * 0.52 - 0.015, label, ha="center", va="top", fontsize=9.5, color="#111111", zorder=7)


def generate_high_res_canvas():
    """Genera la imagen completa de topología de red con el estilo exacto de la referencia."""
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    # 1. TOP LEVEL: Internet y Usuario
    draw_cloud(ax, cx=0.45, cy=0.89, width=0.22, height=0.10, label="Internet")
    draw_actor(ax, cx=0.67, cy=0.88, height=0.08, label="Usuario")

    # Línea entre Usuario e Internet
    ax.plot([0.55, 0.63], [0.89, 0.89], color="#222222", lw=1.3, zorder=2)

    # 2. ROUTERS DE BORDE
    draw_router(ax, cx=0.38, cy=0.74, rx=0.045, ry=0.018)
    draw_router(ax, cx=0.52, cy=0.74, rx=0.045, ry=0.018)

    # Conexiones de Internet a los Routers
    ax.plot([0.43, 0.38], [0.84, 0.76], color="#222222", lw=1.3, zorder=2)
    ax.plot([0.47, 0.52], [0.84, 0.76], color="#222222", lw=1.3, zorder=2)

    # 3. PRIMER FIREWALL (Perimetral)
    fw1_cx = 0.45
    fw1_cy = 0.62
    draw_firewall(ax, cx=fw1_cx, cy=fw1_cy, w=0.06, h=0.05)

    # Conexiones de los Routers al Firewall 1
    ax.plot([0.38, fw1_cx], [0.715, fw1_cy + 0.025], color="#222222", lw=1.3, zorder=2)
    ax.plot([0.52, fw1_cx], [0.715, fw1_cy + 0.025], color="#222222", lw=1.3, zorder=2)

    # 4. TRONCAL DMZ Y SERVIDORES DMZ
    dmz_bus_y = 0.565
    # Troncal vertical desde Firewall 1
    ax.plot([fw1_cx, fw1_cx], [fw1_cy - 0.025, dmz_bus_y], color="#222222", lw=1.5, zorder=2)

    # Bus horizontal DMZ
    ax.plot([fw1_cx, 0.88], [dmz_bus_y, dmz_bus_y], color="#222222", lw=1.8, zorder=2)
    ax.text(0.81, dmz_bus_y - 0.025, "DMZ", ha="left", va="top", fontsize=15, fontweight="bold", color="#111111", zorder=5)

    # Servidor de correo (arriba de la línea DMZ)
    s_mail_x = 0.62
    s_mail_y = 0.66
    draw_server(ax, cx=s_mail_x, cy=s_mail_y, w=0.055, h=0.065, label="Servidor de correo", label_pos="below_close")
    ax.plot([s_mail_x, s_mail_x], [s_mail_y - 0.033, dmz_bus_y], color="#222222", lw=1.3, zorder=2)

    # Servidor web (debajo de la línea DMZ)
    s_web_x = 0.55
    s_web_y = 0.475
    draw_server(ax, cx=s_web_x, cy=s_web_y, w=0.055, h=0.065, label="Servidor web", badge="web")
    ax.plot([s_web_x, s_web_x], [dmz_bus_y, s_web_y + 0.033], color="#222222", lw=1.3, zorder=2)

    # DNS Server (debajo de la línea DMZ)
    s_dns_x = 0.73
    s_dns_y = 0.475
    draw_server(ax, cx=s_dns_x, cy=s_dns_y, w=0.055, h=0.065, label="DNS Server", badge="dns")
    ax.plot([s_dns_x, s_dns_x], [dmz_bus_y, s_dns_y + 0.033], color="#222222", lw=1.3, zorder=2)

    # 5. SEGUNDO FIREWALL (Interno)
    fw2_cx = fw1_cx
    fw2_cy = 0.36
    # Troncal vertical desde DMZ hacia Firewall 2
    ax.plot([fw1_cx, fw2_cx], [dmz_bus_y, fw2_cy + 0.025], color="#222222", lw=1.5, zorder=2)
    draw_firewall(ax, cx=fw2_cx, cy=fw2_cy, w=0.06, h=0.05)

    # 6. BUS VLAN USUARIOS Y VLAN APLICACIÓN
    vlan_app_y = 0.36
    # Línea horizontal que cruza a ambos lados de Firewall 2
    ax.plot([0.16, fw2_cx - 0.03], [vlan_app_y, vlan_app_y], color="#222222", lw=1.8, zorder=2)
    ax.plot([fw2_cx + 0.03, 0.88], [vlan_app_y, vlan_app_y], color="#222222", lw=1.8, zorder=2)

    # Etiquetas de VLAN
    ax.text(0.18, vlan_app_y - 0.035, "VLAN Usuarios", ha="center", va="top", fontsize=15, fontweight="bold", color="#111111", zorder=5)
    ax.text(0.83, vlan_app_y - 0.035, "VLAN Aplicación", ha="center", va="top", fontsize=15, fontweight="bold", color="#111111", zorder=5)

    # Equipo administrador (colgando de VLAN Usuarios)
    admin_x = 0.34
    admin_y = 0.28
    draw_workstation(ax, cx=admin_x, cy=admin_y, w=0.075, h=0.065, label="Equipo administrador")
    ax.plot([admin_x, admin_x], [vlan_app_y, admin_y + 0.033], color="#222222", lw=1.3, zorder=2)

    # Servidor de aplicaciones (colgando de VLAN Aplicación)
    s_app_x = 0.57
    s_app_y = 0.265
    draw_server(ax, cx=s_app_x, cy=s_app_y, w=0.058, h=0.070, label="Servidor de aplicaciones")
    ax.plot([s_app_x, s_app_x], [vlan_app_y, s_app_y + 0.035], color="#222222", lw=1.3, zorder=2)

    # 7. TRONCAL HACIA VLAN DATOS
    vlan_data_y = 0.15
    # Troncal vertical desde Firewall 2 bajando hacia el bus de datos
    ax.plot([fw2_cx, fw2_cx], [fw2_cy - 0.025, vlan_data_y], color="#222222", lw=1.5, zorder=2)
    # Bus horizontal de VLAN Datos
    ax.plot([fw2_cx, 0.84], [vlan_data_y, vlan_data_y], color="#222222", lw=1.8, zorder=2)
    ax.text(0.83, vlan_data_y - 0.035, "VLAN Datos", ha="center", va="top", fontsize=15, fontweight="bold", color="#111111", zorder=5)

    # Base de datos (colgando de VLAN Datos)
    s_db_x = 0.54
    s_db_y = 0.05
    draw_server(ax, cx=s_db_x, cy=s_db_y, w=0.058, h=0.070, label="Base de datos", badge="db")
    ax.plot([s_db_x, s_db_x], [vlan_data_y, s_db_y + 0.035], color="#222222", lw=1.3, zorder=2)

    # Pie de página descriptivo
    ax.text(0.07, 0.025, "Ejemplo de diagrama de red — Topología AWS FashionStore",
            ha="left", va="bottom", fontsize=11, color="#333333", zorder=5)

    plt.tight_layout()
    plt.savefig(CANVAS_PNG, dpi=300, facecolor="#ffffff", bbox_inches="tight")
    plt.close(fig)
    print(f"Canvas de alta fidelidad generado: {CANVAS_PNG}")


# ─────────────────────────────────────────────────────────────
# 2. SINCRONIZACIÓN CON ENTERPRISE ARCHITECT (UML 2.5)
# ─────────────────────────────────────────────────────────────

def sync_enterprise_architect():
    """Crea el paquete, diagrama y elementos formales de red en FashionStore.eap."""
    print("=" * 75)
    print("SINCRONIZANDO DIAGRAMA DE RED CON ENTERPRISE ARCHITECT — UML 2.5")
    print("=" * 75)

    import win32com.client
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir {MODEL_PATH}")
        return 1

    try:
        project = rep.GetProjectInterface()
        root_model = rep.Models.GetAt(0)

        pkg_name = "10 - Diagrama de Red (Topologia AWS)"

        # Buscar si ya existe para recrearlo limpio
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if "Diagrama de Red" in p.Name:
                print(f"Limpiando paquete previo: {p.Name}")
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                break

        net_pkg = root_model.Packages.AddNew(pkg_name, "")
        net_pkg.Notes = (
            "Diagrama de Red y Topología de Despliegue en AWS (UML 2.5). "
            "Modela la segmentación perimetral con DMZ, VLAN Usuarios, VLAN Aplicación y VLAN Datos."
        )
        net_pkg.Update()
        root_model.Packages.Refresh()
        print(f"Paquete contenedor creado: '{net_pkg.Name}' (ID: {net_pkg.PackageID})")

        # Crear diagrama de despliegue/red
        diag = net_pkg.Diagrams.AddNew("Diagrama de Red - Topologia AWS", "Deployment")
        diag.Notes = "Topología de red segmentada en AWS con DMZ, VLAN Usuarios, VLAN Aplicación y VLAN Datos."
        diag.Update()
        net_pkg.Diagrams.Refresh()

        diag.StyleEx = "ShowFrame=1;"
        diag.Update()

        # 1. Crear Nodos / Componentes
        el_internet = net_pkg.Elements.AddNew("Internet (WAN)", "Node")
        el_internet.Stereotype = "Cloud"
        el_internet.Notes = "Red pública WAN e infraestructura global de conectividad."
        el_internet.Update()

        el_user = net_pkg.Elements.AddNew("Usuario / Cliente", "Actor")
        el_user.Notes = "Clientes web y móviles que acceden a través de Internet."
        el_user.Update()

        el_r1 = net_pkg.Elements.AddNew("Router de Borde (AWS IGW)", "Node")
        el_r1.Stereotype = "Router"
        el_r1.Notes = "Internet Gateway perimetral de Amazon VPC."
        el_r1.Update()

        el_r2 = net_pkg.Elements.AddNew("Router de Borde (Route 53)", "Node")
        el_r2.Stereotype = "Router"
        el_r2.Notes = "Enrutador DNS autoritativo Anycast y Latency-based routing."
        el_r2.Update()

        el_fw1 = net_pkg.Elements.AddNew("Firewall Perimetral (AWS WAF)", "Node")
        el_fw1.Stereotype = "Firewall"
        el_fw1.Notes = "AWS WAF + Security Groups perimetrales (Anti-DDoS, filtrado HTTP/HTTPS)."
        el_fw1.Update()

        el_s_web = net_pkg.Elements.AddNew("Servidor web (Frontend Angular)", "Node")
        el_s_web.Stereotype = "Server"
        el_s_web.Notes = "Host Nginx / CloudFront S3 sirviendo la SPA Angular 20 (Puerto 80/443)."
        el_s_web.Update()

        el_s_dns = net_pkg.Elements.AddNew("DNS Server (Route 53)", "Node")
        el_s_dns.Stereotype = "Server"
        el_s_dns.Notes = "Servidor DNS para resolución interna y externa (Puerto 53)."
        el_s_dns.Update()

        el_s_mail = net_pkg.Elements.AddNew("Servidor de correo (Amazon SES)", "Node")
        el_s_mail.Stereotype = "Server"
        el_s_mail.Notes = "Gateway SMTP/API para confirmaciones de compra y reservas (Puerto 587)."
        el_s_mail.Update()

        el_fw2 = net_pkg.Elements.AddNew("Firewall Interno (Network ACL)", "Node")
        el_fw2.Stereotype = "Firewall"
        el_fw2.Notes = "Control de tráfico este-oeste entre DMZ y redes internas."
        el_fw2.Update()

        el_admin = net_pkg.Elements.AddNew("Equipo administrador", "Device")
        el_admin.Stereotype = "Workstation"
        el_admin.Notes = "Estación de trabajo administrativa y terminal POS en caja."
        el_admin.Update()

        el_app = net_pkg.Elements.AddNew("Servidor de aplicaciones (FastAPI)", "Node")
        el_app.Stereotype = "Server"
        el_app.Notes = "Backend modular FastAPI + Uvicorn en contenedor ECS Fargate (Puerto 8000)."
        el_app.Update()

        el_db = net_pkg.Elements.AddNew("Base de datos (PostgreSQL 17)", "Node")
        el_db.Stereotype = "Database"
        el_db.Notes = "Instancia RDS PostgreSQL 17 Multi-AZ cifrada con AWS KMS (Puerto 5432)."
        el_db.Update()

        # 2. Posicionamiento en el Diagrama EA sin solapamiento
        # Layout con ancho y espaciado optimizado
        elements_layout = [
            (el_internet, 360, 500, -50, -110),
            (el_user,     640, 740, -50, -120),
            (el_r1,       260, 400, -150, -210),
            (el_r2,       480, 620, -150, -210),
            (el_fw1,      370, 510, -260, -320),
            (el_s_mail,   650, 790, -260, -320),
            (el_s_web,    180, 320, -370, -440),
            (el_s_dns,    580, 720, -370, -440),
            (el_fw2,      370, 510, -470, -530),
            (el_admin,    120, 260, -580, -650),
            (el_app,      560, 720, -580, -650),
            (el_db,       560, 720, -700, -770),
        ]

        for el, left, right, top, bottom in elements_layout:
            obj = diag.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.left = left
            obj.right = right
            obj.top = top
            obj.bottom = bottom
            obj.Update()

        # 3. Conexiones / Enlaces de Comunicación (CommunicationPath)
        connections = [
            (el_user, el_internet, "Acceso WAN / HTTPS"),
            (el_internet, el_r1, "Tráfico Inbound"),
            (el_internet, el_r2, "Consultas DNS:53"),
            (el_r1, el_fw1, "WAN -> Perímetro"),
            (el_r2, el_fw1, "DNS -> Perímetro"),
            (el_fw1, el_s_web, "HTTPS:443 (DMZ)"),
            (el_fw1, el_s_dns, "DNS:53 (DMZ)"),
            (el_fw1, el_s_mail, "SMTP:587 (DMZ)"),
            (el_fw1, el_fw2, "Trunk DMZ -> Interno"),
            (el_fw2, el_admin, "VLAN Usuarios (SSH/Admin)"),
            (el_fw2, el_app, "VLAN Aplicación (HTTP:8000)"),
            (el_app, el_db, "VLAN Datos (TCP:5432)"),
        ]

        for src, dst, label in connections:
            conn = src.Connectors.AddNew(label, "CommunicationPath")
            conn.SupplierID = dst.ElementID
            conn.Direction = "Unspecified"
            conn.Update()

            link = diag.DiagramLinks.AddNew("", "")
            link.ConnectorID = conn.ConnectorID
            link.Update()

        diag.Update()
        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()

        # 4. Exportar imagen nativa EA
        project.PutDiagramImageToFile(diag.DiagramGUID, EA_PNG, 1)
        print(f"Diagrama exportado desde EA: {EA_PNG}")

        rep.SaveAllDiagrams()
        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return 1
    finally:
        rep.CloseFile()
        del rep


def main():
    print("Iniciando generación de Diagrama de Red (Topología AWS)...")
    generate_high_res_canvas()
    res = sync_enterprise_architect()
    if res == 0:
        print("\n¡DIAGRAMA DE RED GENERADO Y EXPORTADO CON ÉXITO!")
    return res


if __name__ == "__main__":
    sys.exit(main())
