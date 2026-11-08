# -*- coding: utf-8 -*-
"""
Script para generar los diagramas individuales de cada Caso de Uso (CU) con sus actores,
siguiendo exactamente el formato de la imagen de referencia:
- Título exterior superior: "Diagrama de caso de uso"
- Caja límite de sistema (System Boundary) con título superior interior: "CU# Nombre del Caso de Uso"
- Actor(es) representados como figuras humanas UML clásicas con cabeza tono piel suave (#FDE2C8)
- Óvalo de caso de uso celeste (#D6E8FC) con borde azul/negro y texto centrado
- Línea sólida continua de asociación entre actor y óvalo
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Rectangle, Ellipse
import numpy as np

def draw_actor(ax, cx, cy, height=1.05, label="Actor"):
    """Dibuja la figura humana clásica UML (stick figure)."""
    head_r = height * 0.165
    head_cy = cy + height * 0.35
    
    # Cabeza piel suave
    head = Circle((cx, head_cy), head_r, facecolor="#FDE2C8", edgecolor="#111827", linewidth=1.5, zorder=10)
    ax.add_patch(head)
    
    # Tronco
    neck_y = head_cy - head_r
    waist_y = cy - height * 0.10
    ax.plot([cx, cx], [neck_y, waist_y], color="#111827", lw=1.8, zorder=9, solid_capstyle='round')
    
    # Brazos
    arms_y = cy + height * 0.12
    arm_w = height * 0.28
    ax.plot([cx - arm_w, cx + arm_w], [arms_y, arms_y], color="#111827", lw=1.8, zorder=9, solid_capstyle='round')
    
    # Piernas
    leg_y = cy - height * 0.46
    leg_w = height * 0.24
    ax.plot([cx, cx - leg_w], [waist_y, leg_y], color="#111827", lw=1.8, zorder=9, solid_capstyle='round')
    ax.plot([cx, cx + leg_w], [waist_y, leg_y], color="#111827", lw=1.8, zorder=9, solid_capstyle='round')
    
    # Etiqueta
    ax.text(cx, leg_y - 0.10, label, ha="center", va="top",
            fontsize=9.0, fontweight="bold", color="#111827",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none", alpha=0.9),
            zorder=12)

def draw_cu_oval(ax, cx, cy, rx, ry, cu_code, cu_title):
    """Dibuja el óvalo del caso de uso."""
    # Sombra sutil
    shadow = Ellipse((cx + 0.03, cy - 0.03), rx * 2, ry * 2,
                     facecolor="#CBD5E1", edgecolor="none", alpha=0.4, zorder=4)
    ax.add_patch(shadow)
    
    # Óvalo principal
    ellipse = Ellipse((cx, cy), rx * 2, ry * 2,
                      facecolor="#D6E8FC", edgecolor="#1E3A8A", linewidth=1.4, zorder=5)
    ax.add_patch(ellipse)
    
    # Texto
    full_text = f"{cu_code}\n{cu_title}"
    ax.text(cx, cy, full_text, ha="center", va="center",
            fontsize=8.5, fontweight="semibold", color="#0F172A",
            linespacing=1.15, zorder=6)

def generate_single_cu_diagram(cu_code, cu_title, actors, output_path):
    """
    Genera un diagrama individual de caso de uso con sus actores.
    Si hay 1 actor: Actor a la izquierda, Óvalo a la derecha.
    Si hay 2 actores: Actor 1 a la izquierda, Óvalo al centro, Actor 2 a la derecha.
    """
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    
    # Título superior exterior (estilo imagen: "Diagrama de caso de uso")
    fig.text(0.06, 0.95, "Diagrama de caso de uso",
             ha="left", va="top", fontsize=11.5, fontweight="bold", color="#000000")
    
    # Límite del sistema (rectángulo interior)
    # x: 0.6 a 9.4 (ancho 8.8), y: 0.4 a 4.4 (alto 4.0)
    boundary = Rectangle((0.6, 0.4), 8.8, 4.0,
                         facecolor="#FAFCFF", edgecolor="#000000", linewidth=1.4, zorder=2)
    ax.add_patch(boundary)
    
    # Título interior del límite del sistema centrado arriba
    inner_title = f"{cu_code} {cu_title.replace(chr(10), ' ')}"
    if len(inner_title) > 55:
        inner_title = inner_title[:52] + "..."
    ax.text(5.0, 4.18, inner_title,
            ha="center", va="top", fontsize=9.5, fontweight="bold", color="#1E293B", zorder=3)
    
    rx = 1.35
    ry = 0.58
    
    if len(actors) == 1:
        # 1 actor a la izquierda, óvalo en x=6.3
        actor_x = 2.4
        actor_y = 2.1
        draw_actor(ax, cx=actor_x, cy=actor_y, height=1.05, label=actors[0])
        
        oval_x = 6.4
        oval_y = 2.1
        draw_cu_oval(ax, oval_x, oval_y, rx, ry, cu_code, cu_title)
        
        # Línea de asociación
        ax.plot([actor_x + 0.3, oval_x - rx], [actor_y + 0.1, oval_y],
                color="#111827", lw=1.4, zorder=4)
        
    elif len(actors) == 2:
        # Actor 1 a la izquierda, Óvalo al centro, Actor 2 a la derecha
        actor1_x = 1.9
        actor1_y = 2.1
        draw_actor(ax, cx=actor1_x, cy=actor1_y, height=1.05, label=actors[0])
        
        oval_x = 5.0
        oval_y = 2.1
        draw_cu_oval(ax, oval_x, oval_y, rx, ry, cu_code, cu_title)
        
        actor2_x = 8.1
        actor2_y = 2.1
        draw_actor(ax, cx=actor2_x, cy=actor2_y, height=1.05, label=actors[1])
        
        # Líneas de asociación
        ax.plot([actor1_x + 0.3, oval_x - rx], [actor1_y + 0.1, oval_y],
                color="#111827", lw=1.4, zorder=4)
        ax.plot([actor2_x - 0.3, oval_x + rx], [actor2_y + 0.1, oval_y],
                color="#111827", lw=1.4, zorder=4)
        
    else:
        # 3 actores: 2 a la izquierda apilados, 1 a la derecha
        actor1_x = 1.8
        actor1_y = 2.9
        draw_actor(ax, cx=actor1_x, cy=actor1_y, height=0.9, label=actors[0])
        
        actor2_x = 1.8
        actor2_y = 1.3
        draw_actor(ax, cx=actor2_x, cy=actor2_y, height=0.9, label=actors[1])
        
        oval_x = 5.0
        oval_y = 2.1
        draw_cu_oval(ax, oval_x, oval_y, rx, ry, cu_code, cu_title)
        
        actor3_x = 8.1
        actor3_y = 2.1
        draw_actor(ax, cx=actor3_x, cy=actor3_y, height=1.0, label=actors[2])
        
        ax.plot([actor1_x + 0.3, oval_x - rx], [actor1_y, oval_y + 0.15], color="#111827", lw=1.4, zorder=4)
        ax.plot([actor2_x + 0.3, oval_x - rx], [actor2_y, oval_y - 0.15], color="#111827", lw=1.4, zorder=4)
        ax.plot([actor3_x - 0.3, oval_x + rx], [actor3_y + 0.1, oval_y], color="#111827", lw=1.4, zorder=4)
        
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, facecolor="#FFFFFF", edgecolor="none")
    plt.close()

def generate_all_cu_diagrams():
    out_dir = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\individual_cus"
    os.makedirs(out_dir, exist_ok=True)
    
    cus = [
        {
            "id": "CU-01",
            "title": "Registrar Empresa\nContratante (Tenant)",
            "actors": ["Superadmin SaaS"],
            "filename": "cu01_diagram.png"
        },
        {
            "id": "CU-02",
            "title": "Gestionar Planes\nde Suscripción",
            "actors": ["Superadmin SaaS"],
            "filename": "cu02_diagram.png"
        },
        {
            "id": "CU-03",
            "title": "Asignar y Renovar\nSuscripción de Empresa",
            "actors": ["Superadmin SaaS", "Tenant Admin"],
            "filename": "cu03_diagram.png"
        },
        {
            "id": "CU-04",
            "title": "Controlar Límites y\nRestricciones por Plan",
            "actors": ["Sistema Middleware", "Tenant Admin"],
            "filename": "cu04_diagram.png"
        },
        {
            "id": "CU-05",
            "title": "Gestionar Sucursales\ny Empleados por Tenant",
            "actors": ["Tenant Admin"],
            "filename": "cu05_diagram.png"
        },
        {
            "id": "CU-06",
            "title": "Descargar y Almacenar\nCatálogo Offline",
            "actors": ["Cajero / Vendedor", "Cliente"],
            "filename": "cu06_diagram.png"
        },
        {
            "id": "CU-07",
            "title": "Consultar Catálogo y\nExistencias Offline",
            "actors": ["Cajero / Vendedor", "Cliente"],
            "filename": "cu07_diagram.png"
        },
        {
            "id": "CU-08",
            "title": "Registrar Venta de\nContado Offline",
            "actors": ["Cajero / Vendedor"],
            "filename": "cu08_diagram.png"
        },
        {
            "id": "CU-09",
            "title": "Registrar Reserva\nde Prendas Offline",
            "actors": ["Cajero / Vendedor", "Cliente"],
            "filename": "cu09_diagram.png"
        },
        {
            "id": "CU-23",
            "title": "Notificar Conectividad\n(Semáforo Online/Offline)",
            "actors": ["Sistema Cliente", "Cajero / Vendedor"],
            "filename": "cu23_diagram.png"
        },
        {
            "id": "CU-24",
            "title": "Instalar y Registrar\nService Worker (PWA)",
            "actors": ["Usuario Web", "Navegador Web"],
            "filename": "cu24_diagram.png"
        },
        {
            "id": "CU-25",
            "title": "Configurar Persistencia\nSQLite Móvil",
            "actors": ["Motor Móvil", "Cajero / Vendedor"],
            "filename": "cu25_diagram.png"
        }
    ]
    
    for cu in cus:
        out_path = os.path.join(out_dir, cu["filename"])
        generate_single_cu_diagram(cu["id"], cu["title"], cu["actors"], out_path)
        print(f"Generado {cu['id']} -> {out_path}")

if __name__ == "__main__":
    generate_all_cu_diagrams()
