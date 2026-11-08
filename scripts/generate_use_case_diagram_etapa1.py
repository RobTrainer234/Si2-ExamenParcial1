# -*- coding: utf-8 -*-
"""
Script optimizado para generar el Diagrama UML de Casos de Uso de la Etapa 1 (FashionStore SaaS)
siguiendo fielmente el diseño de la imagen de referencia (DIAGRAMA GENERAL DE CASOS DE USO):
- Título exterior: DIAGRAMA GENERAL DE CASOS DE USO
- Subtítulo interior del límite del sistema: "Diagrama general de casos de uso - Etapa 1"
- 4 Actores estilo UML clásico (muñecos con cabeza piel #FCE3C8 y cuerpo limpio)
- 10 Casos de Uso en óvalos celestes (#D2E7FD) con borde azul (#1E40AF)
- Asociaciones directas limpias
- Relaciones «include» y «extend» perfectamente trazadas sin colisiones
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle, Ellipse
import numpy as np

def draw_actor(ax, cx, cy, height=1.1, label="Actor"):
    """
    Dibuja la figura humana clásica (Actor UML) tal como en el modelo:
    cabeza circular rellena, tronco vertical, brazos horizontales, piernas en V invertida.
    """
    head_r = height * 0.165
    head_cy = cy + height * 0.36
    
    # Cabeza (color piel suave como en la imagen de referencia)
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
    
    # Nombre del actor debajo
    ax.text(cx, leg_y - 0.10, label, ha="center", va="top",
            fontsize=10.0, fontweight="bold", color="#111827",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none", alpha=0.85),
            zorder=12)

def draw_use_case(ax, cx, cy, rx, ry, cu_code, cu_title):
    """
    Dibuja un óvalo de caso de uso UML idéntico a la imagen de referencia:
    fondo celeste suave, contorno negro/azul marino definido y texto centrado.
    """
    # Sombra sutil elegante
    shadow = Ellipse((cx + 0.035, cy - 0.035), rx * 2, ry * 2,
                     facecolor="#CBD5E1", edgecolor="none", alpha=0.4, zorder=4)
    ax.add_patch(shadow)
    
    # Óvalo principal
    ellipse = Ellipse((cx, cy), rx * 2, ry * 2,
                      facecolor="#D6E8FC", edgecolor="#1E3A8A", linewidth=1.4, zorder=5)
    ax.add_patch(ellipse)
    
    # Texto centrado
    full_text = f"{cu_code} {cu_title}"
    ax.text(cx, cy, full_text, ha="center", va="center",
            fontsize=8.5, fontweight="semibold", color="#0F172A",
            linespacing=1.15, zorder=6)

def draw_assoc(ax, x1, y1, x2, y2):
    """Línea sólida continua de asociación UML."""
    ax.plot([x1, x2], [y1, y2], color="#1E293B", lw=1.3, zorder=3)

def draw_relation(ax, x1, y1, x2, y2, label="«include»", label_pos=0.5, rad=0.0):
    """
    Flecha discontinua estereotipada UML («include» o «extend»).
    """
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle="->,head_length=5,head_width=3.5",
                            linestyle=(0, (4, 3.5)), color="#0F172A",
                            lw=1.2, connectionstyle=f"arc3,rad={rad}", zorder=7)
    ax.add_patch(arrow)
    
    mx = x1 + (x2 - x1) * label_pos
    my = y1 + (y2 - y1) * label_pos
    if rad != 0.0:
        dx = x2 - x1
        dy = y2 - y1
        length = np.hypot(dx, dy)
        if length > 0:
            nx = -dy / length
            ny = dx / length
            mx += nx * rad * length * 0.38
            my += ny * rad * length * 0.38
            
    ax.text(mx, my, label, ha="center", va="center",
            fontsize=7.8, fontstyle="italic", fontweight="bold", color="#1E3A8A",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#93C5FD", lw=0.7, alpha=0.98),
            zorder=8)

def build_etapa1_diagram(output_path):
    fig, ax = plt.subplots(figsize=(15.0, 10.5), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")
    
    # Título superior idéntico a la imagen
    fig.text(0.12, 0.955, "DIAGRAMA GENERAL DE CASOS DE USO",
             ha="left", va="top", fontsize=15.0, fontweight="bold", color="#000000")
    
    # System boundary box
    # x: 1.8 a 14.2 (ancho 12.4), y: 0.6 a 9.2 (alto 8.6)
    boundary = Rectangle((2.3, 0.6), 11.4, 8.6,
                         facecolor="#FBFDFF", edgecolor="#000000", linewidth=1.5, zorder=2)
    ax.add_patch(boundary)
    
    # Subtítulo centrado en el límite superior
    ax.text(8.0, 8.95, "Diagrama general de casos de uso - Etapa 1 (Fundación Multitenant y Catálogo Offline)",
            ha="center", va="top", fontsize=9.5, fontstyle="normal", color="#333333", zorder=3)
    
    # ─────────────────────────────────────────────────────────────
    # ACTORES (2 a la izquierda, 2 a la derecha, en los bordes)
    # ─────────────────────────────────────────────────────────────
    # Lado Izquierdo
    draw_actor(ax, cx=1.2, cy=6.9, height=1.1, label="Superadmin\nSaaS")
    draw_actor(ax, cx=1.2, cy=2.7, height=1.1, label="Tenant\nAdmin")
    
    # Lado Derecho
    draw_actor(ax, cx=14.8, cy=6.9, height=1.1, label="Cajero /\nVendedor")
    draw_actor(ax, cx=14.8, cy=2.7, height=1.1, label="Cliente")
    
    # ─────────────────────────────────────────────────────────────
    # CASOS DE USO (10 CUs de la Etapa 1)
    # ─────────────────────────────────────────────────────────────
    rx = 1.25
    ry = 0.44
    
    # Coordenadas calculadas para distribución armónica:
    # Cluster Multitenant (Izquierda-Centro)
    cu01 = (4.3, 7.5)   # CU-01 Registrar Empresa
    cu02 = (7.5, 8.0)   # CU-02 Gestionar Planes
    cu03 = (7.3, 6.6)   # CU-03 Asignar Suscripción
    cu04 = (7.4, 5.2)   # CU-04 Controlar Límites
    cu05 = (4.3, 4.4)   # CU-05 Gestionar Sucursales y Empleados
    
    # Cluster Catálogo & Desconectado (Derecha-Centro)
    cu06 = (11.6, 6.7)  # CU-06 Descargar Catálogo Offline
    cu07 = (11.6, 4.5)  # CU-07 Consultar Catálogo Offline
    cu23 = (8.5, 3.4)   # CU-23 Notificar Semáforo Online/Offline
    cu24 = (5.3, 1.8)   # CU-24 Instalar Service Worker (PWA)
    cu25 = (11.0, 1.8)  # CU-25 Configurar Persistencia SQLite Móvil
    
    # Renderizar elipses
    draw_use_case(ax, cu01[0], cu01[1], rx, ry, "CU1", "Registrar Empresa\nContratante (Tenant)")
    draw_use_case(ax, cu02[0], cu02[1], rx, ry, "CU2", "Gestionar Planes\nde Suscripción")
    draw_use_case(ax, cu03[0], cu03[1], rx, ry, "CU3", "Asignar y Renovar\nSuscripción de Empresa")
    draw_use_case(ax, cu04[0], cu04[1], rx, ry, "CU4", "Controlar Límites\ny Restricciones por Plan")
    draw_use_case(ax, cu05[0], cu05[1], rx, ry, "CU5", "Gestionar Sucursales\ny Empleados por Tenant")
    
    draw_use_case(ax, cu06[0], cu06[1], rx, ry, "CU6", "Descargar y Almacenar\nCatálogo Offline")
    draw_use_case(ax, cu07[0], cu07[1], rx, ry, "CU7", "Consultar Catálogo y\nExistencias Offline")
    draw_use_case(ax, cu23[0], cu23[1], rx, ry, "CU23", "Notificar Estado de\nConectividad (Semáforo)")
    draw_use_case(ax, cu24[0], cu24[1], rx, ry, "CU24", "Instalar y Registrar\nService Worker (PWA)")
    draw_use_case(ax, cu25[0], cu25[1], rx, ry, "CU25", "Configurar Persistencia\nSQLite Móvil")
    
    # ─────────────────────────────────────────────────────────────
    # LÍNEAS DE ASOCIACIÓN (Actor a Casos de Uso)
    # ─────────────────────────────────────────────────────────────
    # Superadmin SaaS
    draw_assoc(ax, 1.6, 7.1, cu01[0] - rx, cu01[1])
    draw_assoc(ax, 1.6, 7.3, cu02[0] - rx * 0.95, cu02[1] + 0.1)
    draw_assoc(ax, 1.6, 6.8, cu03[0] - rx * 0.9, cu03[1] + 0.15)
    
    # Tenant Admin
    draw_assoc(ax, 1.6, 3.1, cu03[0] - rx * 0.85, cu03[1] - 0.25)
    draw_assoc(ax, 1.6, 2.9, cu05[0] - rx, cu05[1])
    
    # Cajero / Vendedor
    draw_assoc(ax, 14.4, 7.0, cu06[0] + rx, cu06[1])
    draw_assoc(ax, 14.4, 6.7, cu07[0] + rx, cu07[1] + 0.15)
    draw_assoc(ax, 14.4, 6.5, cu23[0] + rx * 0.9, cu23[1] + 0.2)
    
    # Cliente
    draw_assoc(ax, 14.4, 2.9, cu07[0] + rx, cu07[1] - 0.2)
    draw_assoc(ax, 14.4, 2.6, cu24[0] + rx * 0.9, cu24[1] - 0.1)
    
    # ─────────────────────────────────────────────────────────────
    # DEPENDENCIAS «include» y «extend»
    # ─────────────────────────────────────────────────────────────
    # CU1 -> CU3 («include»)
    draw_relation(ax, cu01[0] + rx * 0.8, cu01[1] - 0.2,
                  cu03[0] - rx * 0.6, cu03[1] + 0.3,
                  label="«include»", label_pos=0.5, rad=-0.1)
    
    # CU3 -> CU2 («include»)
    draw_relation(ax, cu03[0] + 0.1, cu03[1] + ry,
                  cu02[0] - 0.1, cu02[1] - ry,
                  label="«include»", label_pos=0.5, rad=0.0)
    
    # CU5 -> CU4 («include»)
    draw_relation(ax, cu05[0] + rx * 0.8, cu05[1] + 0.2,
                  cu04[0] - rx * 0.6, cu04[1] - 0.2,
                  label="«include»", label_pos=0.5, rad=0.08)
    
    # CU7 -> CU6 («include» / «extend»)
    draw_relation(ax, cu07[0], cu07[1] + ry,
                  cu06[0], cu06[1] - ry,
                  label="«include»", label_pos=0.5, rad=0.0)
    
    # CU23 -> CU6 («extend»)
    draw_relation(ax, cu23[0] + rx * 0.8, cu23[1] + 0.25,
                  cu06[0] - rx * 0.7, cu06[1] - 0.25,
                  label="«extend»", label_pos=0.5, rad=-0.12)
    
    # CU24 -> CU6 («extend»)
    draw_relation(ax, cu24[0] + rx * 0.7, cu24[1] + ry * 0.7,
                  cu06[0] - rx * 0.5, cu06[1] - ry * 0.9,
                  label="«extend»", label_pos=0.45, rad=0.18)
    
    # CU25 -> CU6 («extend»)
    draw_relation(ax, cu25[0] + 0.1, cu25[1] + ry,
                  cu06[0] - 0.2, cu06[1] - ry,
                  label="«extend»", label_pos=0.5, rad=-0.1)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, facecolor="#FFFFFF", edgecolor="none")
    plt.close()
    print(f"Diagrama generado con éxito en: {output_path}")

if __name__ == "__main__":
    out_file = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\diagrama_casos_uso_etapa1.png"
    build_etapa1_diagram(out_file)
