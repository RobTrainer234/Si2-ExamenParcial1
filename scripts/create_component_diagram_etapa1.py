import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle

OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\237defdf-2954-4086-96f9-23d868845b7e"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

PNG_PATH = os.path.join(OUT_DIR, "diagrama_componentes_etapa1.png")
ARTIFACT_PNG = os.path.join(ARTIFACT_DIR, "diagrama_componentes_etapa1.png")

def draw_component_box(ax, x, y, w, h, name, subtitle=None):
    # Main rectangle with subtle drop shadow for depth
    shadow = mpatches.Rectangle((x + 2, y - 2), w, h, facecolor="#E2E8F0", edgecolor="none", zorder=2)
    ax.add_patch(shadow)
    
    rect = mpatches.Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor="#1E293B", linewidth=1.3, zorder=3)
    ax.add_patch(rect)
    
    # UML 2.0 Component Icon on upper-left
    icon_w = 26
    icon_h = 24
    icon_x = x + 8
    icon_y = y + h - icon_h - 8
    
    icon_box = mpatches.Rectangle((icon_x, icon_y), icon_w, icon_h, facecolor="#FFFFFF", edgecolor="#1E293B", linewidth=1.0, zorder=4)
    ax.add_patch(icon_box)
    
    # 2 tiny tabs on the left of the icon
    tab_w = 9
    tab_h = 6
    tab1_y = icon_y + icon_h - tab_h - 3
    tab2_y = icon_y + 3
    
    tab1 = mpatches.Rectangle((icon_x - 5, tab1_y), tab_w, tab_h, facecolor="#FFFFFF", edgecolor="#1E293B", linewidth=1.0, zorder=5)
    tab2 = mpatches.Rectangle((icon_x - 5, tab2_y), tab_w, tab_h, facecolor="#FFFFFF", edgecolor="#1E293B", linewidth=1.0, zorder=5)
    ax.add_patch(tab1)
    ax.add_patch(tab2)
    
    # Component text
    if subtitle:
        ax.text(x + w * 0.53, y + h * 0.58, name, ha="center", va="center", fontsize=10.0, fontweight="bold", color="#0F172A", zorder=6)
        ax.text(x + w * 0.53, y + h * 0.28, subtitle, ha="center", va="center", fontsize=8.0, color="#475569", zorder=6)
    else:
        ax.text(x + w * 0.53, y + h * 0.50, name, ha="center", va="center", fontsize=10.0, fontweight="bold", color="#0F172A", zorder=6)

def draw_lollipop(ax, start_pt, end_pt, label, label_pos="bottom"):
    # Solid line from component border to lollipop
    ax.plot([start_pt[0], end_pt[0]], [start_pt[1], end_pt[1]], color="#1E293B", linewidth=1.2, zorder=3)
    # Circle at end_pt
    circle = Circle((end_pt[0], end_pt[1]), radius=7.5, facecolor="#FFFFFF", edgecolor="#1E293B", linewidth=1.3, zorder=5)
    ax.add_patch(circle)
    # Label
    lx, ly = end_pt
    ha = "center"
    va = "center"
    if label_pos == "bottom":
        ly -= 15
        va = "top"
    elif label_pos == "top":
        ly += 15
        va = "bottom"
    elif label_pos == "right":
        lx += 12
        ha = "left"
    elif label_pos == "left":
        lx -= 12
        ha = "right"
    ax.text(lx, ly, label, ha=ha, va=va, fontsize=8.5, fontweight="semibold", color="#1E293B", zorder=6)

def draw_dependency(ax, start_pt, end_pt):
    # Dashed arrow
    ax.annotate(
        "", xy=end_pt, xytext=start_pt,
        arrowprops=dict(
            arrowstyle="->",
            linestyle=(0, (4, 3)),
            color="#334155",
            linewidth=1.1,
            mutation_scale=12,
            shrinkA=3,
            shrinkB=3
        ),
        zorder=2
    )

def main():
    fig, ax = plt.subplots(figsize=(13, 10.5), dpi=300)
    
    # Coordinate space
    ax.set_xlim(0, 1050)
    ax.set_ylim(0, 880)
    ax.set_aspect("equal")
    
    # Grid paper styling (subtle grid like draw.io / StarUML)
    ax.set_facecolor("#FFFFFF")
    for gx in range(0, 1050, 25):
        ax.axvline(gx, color="#F1F5F9", linewidth=0.6, zorder=1)
    for gy in range(0, 880, 25):
        ax.axhline(gy, color="#F1F5F9", linewidth=0.6, zorder=1)
        
    ax.axis("off")
    
    # Header Title
    ax.text(525, 845, "DIAGRAMA DE COMPONENTES UML 2.5 — ETAPA 1", ha="center", va="center", fontsize=15, fontweight="bold", color="#1B365D")
    ax.text(525, 822, "Proyecto FashionStore: SaaS Multi-tenant, PWA & Catálogo Offline (Sistemas de Información II - UAGRM)", ha="center", va="center", fontsize=9.5, color="#64748B")

    # -------------------------------------------------------------
    # 1. TOP: Servidor Backend API (FastAPI) [Equivalente a Cajero]
    # -------------------------------------------------------------
    c_api = (400, 680, 240, 75)
    draw_component_box(ax, c_api[0], c_api[1], c_api[2], c_api[3], "Servidor Backend API", "(FastAPI + Controladores)")
    draw_lollipop(ax, (c_api[0] + c_api[2], c_api[1] + c_api[3]/2), (c_api[0] + c_api[2] + 85, c_api[1] + c_api[3]/2), "Servicio API REST", label_pos="bottom")

    # -------------------------------------------------------------
    # 2. CENTER: Base de Datos Central PostgreSQL [Equivalente a BD Banco]
    # -------------------------------------------------------------
    c_db = (390, 420, 260, 85)
    draw_component_box(ax, c_db[0], c_db[1], c_db[2], c_db[3], "Base de Datos Central", "(PostgreSQL Multi-tenant)")
    draw_lollipop(ax, (c_db[0] + c_db[2], c_db[1] + c_db[3] * 0.8), (c_db[0] + c_db[2] + 75, c_db[1] + c_db[3] * 0.8 + 45), "Datos de Catálogo y Tenants", label_pos="top")

    # -------------------------------------------------------------
    # 3. LEFT: Consola Cliente [Equivalente a Consola cliente]
    # -------------------------------------------------------------
    c_cli = (50, 490, 210, 75)
    draw_component_box(ax, c_cli[0], c_cli[1], c_cli[2], c_cli[3], "Consola Cliente", "(Navegador Web)")

    # -------------------------------------------------------------
    # 4. RIGHT: Consola Administrador [Equivalente a Consola de empleado]
    # -------------------------------------------------------------
    c_emp = (780, 490, 220, 75)
    draw_component_box(ax, c_emp[0], c_emp[1], c_emp[2], c_emp[3], "Consola Administrador", "(Superadmin & Tenant Admin)")
    draw_lollipop(ax, (c_emp[0] + c_emp[2]/2, c_emp[1]), (c_emp[0] + c_emp[2]/2, c_emp[1] - 80), "Transacción Administrativa", label_pos="bottom")

    # -------------------------------------------------------------
    # 5. BOTTOM-RIGHT: Terminal Móvil Sucursal [Equivalente a Lector de tarjetas]
    # -------------------------------------------------------------
    c_mov = (670, 230, 220, 75)
    draw_component_box(ax, c_mov[0], c_mov[1], c_mov[2], c_mov[3], "Terminal Móvil Sucursal", "(Flutter + Vendedor)")
    draw_lollipop(ax, (c_mov[0] + c_mov[2]/2, c_mov[1]), (c_mov[0] + c_mov[2]/2, c_mov[1] - 80), "Transacción Móvil Sucursal", label_pos="bottom")

    # -------------------------------------------------------------
    # 6. BOTTOM: Página Web / PWA [Equivalente a Página web]
    # -------------------------------------------------------------
    c_web = (380, 100, 230, 75)
    draw_component_box(ax, c_web[0], c_web[1], c_web[2], c_web[3], "Página Web / PWA", "(Angular + Service Worker)")
    draw_lollipop(ax, (c_web[0] + c_web[2]/2, c_web[1]), (c_web[0] + c_web[2]/2, c_web[1] - 65), "Transacción Online / PWA", label_pos="bottom")

    # -------------------------------------------------------------
    # 7. BOTTOM-LEFT: Almacén Local Offline [Núcleo Offline-First Etapa 1]
    # -------------------------------------------------------------
    c_off = (90, 230, 220, 75)
    draw_component_box(ax, c_off[0], c_off[1], c_off[2], c_off[3], "Almacén Local Offline", "(SQLite / IndexedDB)")
    draw_lollipop(ax, (c_off[0] + c_off[2]/2, c_off[1]), (c_off[0] + c_off[2]/2, c_off[1] - 80), "Consulta Catálogo Offline", label_pos="bottom")

    # -------------------------------------------------------------
    # DEPENDENCIAS (FLECHAS DISCONTINUAS -->)
    # -------------------------------------------------------------
    # Consola Cliente --> Servidor Backend API
    draw_dependency(ax, (c_cli[0] + c_cli[2] * 0.8, c_cli[1] + c_cli[3]), (c_api[0] + 15, c_api[1] + 15))
    
    # Consola Cliente --> Página Web / PWA
    draw_dependency(ax, (c_cli[0] + c_cli[2] * 0.5, c_cli[1]), (c_web[0] + 15, c_web[1] + c_web[3] * 0.75))

    # Servidor Backend API --> Base de Datos Central
    draw_dependency(ax, (c_api[0] + c_api[2]/2, c_api[1]), (c_db[0] + c_db[2]/2, c_db[1] + c_db[3]))

    # Consola Administrador --> Base de Datos Central
    draw_dependency(ax, (c_emp[0], c_emp[1] + c_emp[3] * 0.4), (c_db[0] + c_db[2], c_db[1] + c_db[3] * 0.6))
    
    # Consola Administrador --> Servidor Backend API
    draw_dependency(ax, (c_emp[0] + 40, c_emp[1] + c_emp[3]), (c_api[0] + c_api[2] - 15, c_api[1] + 15))

    # Página Web / PWA --> Base de Datos Central (Online)
    draw_dependency(ax, (c_web[0] + c_web[2]/2, c_web[1] + c_web[3]), (c_db[0] + c_db[2] * 0.45, c_db[1]))

    # Terminal Móvil Sucursal --> Base de Datos Central (Online)
    draw_dependency(ax, (c_mov[0] + 25, c_mov[1] + c_mov[3] * 0.8), (c_db[0] + c_db[2] * 0.85, c_db[1]))

    # Terminal Móvil Sucursal --> Almacén Local Offline (Desconectado SQLite)
    draw_dependency(ax, (c_mov[0], c_mov[1] + c_mov[3]/2), (c_off[0] + c_off[2], c_off[1] + c_off[3]/2))

    # Página Web / PWA --> Almacén Local Offline (Desconectado IndexedDB)
    draw_dependency(ax, (c_web[0], c_web[1] + c_web[3] * 0.65), (c_off[0] + c_off[2] * 0.75, c_off[1]))

    plt.tight_layout()
    plt.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.savefig(ARTIFACT_PNG, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Refined diagram saved to {PNG_PATH} and {ARTIFACT_PNG}")

if __name__ == "__main__":
    main()
