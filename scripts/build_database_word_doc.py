import os
import sys
import json
from collections import defaultdict, deque

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('scripts'))

from app.core.models import Base
from table_descriptions import TABLE_MODULES

# Load raw metadata
with open("scripts/metadata_tables.json", "r", encoding="utf-8") as f:
    raw_metadata = json.load(f)

# Topological order of tables
adj = defaultdict(set)
in_degree = defaultdict(int)
tables = list(Base.metadata.tables.keys())

for tname in tables:
    in_degree[tname] = 0

for tname, table in Base.metadata.tables.items():
    for col in table.columns:
        for fk in col.foreign_keys:
            target = fk.column.table.name
            if target != tname:
                adj[target].add(tname)

for u in tables:
    for v in adj[u]:
        in_degree[v] += 1

q = deque([t for t in tables if in_degree[t] == 0])
sorted_tables = []
while q:
    u = q.popleft()
    sorted_tables.append(u)
    for v in adj[u]:
        in_degree[v] -= 1
        if in_degree[v] == 0:
            q.append(v)

print(f"Topological sorting ready: {len(sorted_tables)} tables.")

# Create Word Document
doc = docx.Document()

# Page Setup: Letter, 0.75 in margins (fits 7.0 in tables perfectly)
sections = doc.sections
for s in sections:
    s.page_width = Inches(8.5)
    s.page_height = Inches(11.0)
    s.top_margin = Inches(0.75)
    s.bottom_margin = Inches(0.75)
    s.left_margin = Inches(0.75)
    s.right_margin = Inches(0.75)

# Styling helpers
def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    borders_elm = OxmlElement('w:tcBorders')
    borders = {'top': top, 'bottom': bottom, 'left': left, 'right': right}
    for b_name, b_style in borders.items():
        if b_style:
            b_elm = parse_xml(
                f'<w:{b_name} {nsdecls("w")} '
                f'w:val="{b_style.get("val", "single")}" '
                f'w:sz="{b_style.get("sz", "4")}" '
                f'w:space="0" '
                f'w:color="{b_style.get("color", "CBD5E1")}"/>'
            )
            borders_elm.append(b_elm)
        else:
            b_elm = parse_xml(f'<w:{b_name} {nsdecls("w")} w:val="none"/>')
            borders_elm.append(b_elm)
    tcPr.append(borders_elm)

def prevent_row_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

# -----------------------------------------------------------------------------
# 1. PORTADA FORMAL ACADÉMICA
# -----------------------------------------------------------------------------
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_p.paragraph_format.space_before = Pt(20)
title_p.paragraph_format.space_after = Pt(4)

r = title_p.add_run("UNIVERSIDAD AUTÓNOMA GABRIEL RENÉ MORENO\n")
r.font.name = "Calibri"
r.font.size = Pt(16)
r.font.bold = True
r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

r2 = title_p.add_run("FACULTAD DE INGENIERÍA EN CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES\n")
r2.font.name = "Calibri"
r2.font.size = Pt(12)
r2.font.bold = True
r2.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

r3 = title_p.add_run("CARRERA DE INGENIERÍA INFORMÁTICA / SISTEMAS\n")
r3.font.name = "Calibri"
r3.font.size = Pt(11)
r3.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

doc.add_paragraph().paragraph_format.space_after = Pt(20)

# Banner Title Box
banner_tbl = doc.add_table(rows=1, cols=1)
banner_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
cell_banner = banner_tbl.cell(0, 0)
cell_banner.width = Inches(7.0)
set_cell_shading(cell_banner, "1B365D")
set_cell_margins(cell_banner, top=240, bottom=240, left=200, right=200)
set_cell_borders(cell_banner, top={"color": "1B365D", "sz": "12"}, bottom={"color": "1B365D", "sz": "12"}, left={"color": "1B365D", "sz": "12"}, right={"color": "1B365D", "sz": "12"})

p_box = cell_banner.paragraphs[0]
p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_box = p_box.add_run("DICCIONARIO DE DATOS Y ESQUEMA RELACIONAL FÍSICO\n")
r_box.font.name = "Calibri"
r_box.font.size = Pt(18)
r_box.font.bold = True
r_box.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

r_sub = p_box.add_run("ESPECIFICACIÓN COMPLETA DE TABLAS EN CAJAS DE ATRIBUTOS (PK / FK)\nSISTEMA DE COMERCIO ELECTRÓNICO & SAAS MULTI-TENANT 'FASHIONSTORE'")
r_sub.font.name = "Calibri"
r_sub.font.size = Pt(11)
r_sub.font.color.rgb = RGBColor(0x93, 0xC5, 0xFD)

doc.add_paragraph().paragraph_format.space_after = Pt(20)

# Metadata Box
meta_p = doc.add_paragraph()
meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta_p.paragraph_format.line_spacing = 1.3

m1 = meta_p.add_run("Materia: ")
m1.font.bold = True
m1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
meta_p.add_run("Sistemas de Información II (SI2) — INF412\n")

m2 = meta_p.add_run("Motor de Persistencia: ")
m2.font.bold = True
m2.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
meta_p.add_run("PostgreSQL 15+ / 16+ (Esquema Compartido SaaS con tenant_id)\n")

m3 = meta_p.add_run("Total de Tablas Físicas: ")
m3.font.bold = True
m3.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
meta_p.add_run("38 Tablas normalizadas en 3FN con integridad referencial declarativa\n")

m4 = meta_p.add_run("Arquitectura Resiliente: ")
m4.font.bold = True
m4.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
meta_p.add_run("Offline-First con sincronización transaccional Outbox (sync_operations)\n")

m5 = meta_p.add_run("Fecha de Generación: ")
m5.font.bold = True
m5.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
meta_p.add_run("Segundo Parcial - Periodo Académico II-2026\n")

m6 = meta_p.add_run("Santa Cruz de la Sierra — Bolivia")
m6.font.italic = True
m6.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

doc.add_page_break()

# -----------------------------------------------------------------------------
# 2. INTRODUCCIÓN Y ARQUITECTURA DE PERSISTENCIA
# -----------------------------------------------------------------------------
h1 = doc.add_paragraph()
r_h1 = h1.add_run("1. Arquitectura de Base de Datos y Modelo de Datos")
r_h1.font.name = "Calibri"
r_h1.font.size = Pt(16)
r_h1.font.bold = True
r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
h1.paragraph_format.space_after = Pt(8)

p_intro = doc.add_paragraph()
p_intro.paragraph_format.line_spacing = 1.15
p_intro.paragraph_format.space_after = Pt(8)
p_intro.add_run(
    "La base de datos relacional de la plataforma FashionStore ha sido diseñada bajo estándares rigurosos de "
    "ingeniería de software y modelado relacional en Tercera Forma Normal (3FN), garantizando la máxima integridad, "
    "escalabilidad transaccional y rendimiento en consultas analíticas. La persistencia centralizada opera sobre el motor "
    "PostgreSQL 15+ / 16+, complementado por persistencia distribuida y desconectada mediante SQLite en clientes móviles (Flutter) "
    "e IndexedDB en la Progressive Web App (Angular)."
)

# Callout box for SaaS Architecture
callout_tbl = doc.add_table(rows=1, cols=1)
callout_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
c_cell = callout_tbl.cell(0, 0)
c_cell.width = Inches(7.0)
set_cell_shading(c_cell, "F8FAFC")
set_cell_margins(c_cell, top=140, bottom=140, left=160, right=160)
set_cell_borders(c_cell, left={"color": "2563EB", "sz": "18"}, top={"color": "E2E8F0", "sz": "4"}, bottom={"color": "E2E8F0", "sz": "4"}, right={"color": "E2E8F0", "sz": "4"})

cp = c_cell.paragraphs[0]
cp.paragraph_format.line_spacing = 1.15
r_ct = cp.add_run("Pilares Fundamentales del Diseño Relacional:\n")
r_ct.font.bold = True
r_ct.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

cp.add_run(
    "• Modelo SaaS Multi-tenant con Discriminador Lógico (tenant_id): Todas las entidades del dominio de negocio incorporan "
    "la columna tenant_id con índices B-tree dedicados e integridad referencial (ON DELETE CASCADE), posibilitando que múltiples "
    "empresas coexistan en una base de datos física única con aislamiento absoluto.\n"
    "• Resiliencia Offline-First y Patrón Outbox: Las transacciones formalizadas en contingencias sin conectividad a Internet "
    "(ventas de contado y reservas de prendas) se enrutan mediante UUIDs universales y la tabla sync_operations, aplicando "
    "descuento atómico de existencias y resolución de conflictos por sobreventa.\n"
    "• Auditoría Transversal Inmutable (Bitácora): Registro exhaustivo en la tabla bitacora de todas las mutaciones críticas "
    "(valores anteriores y nuevos serializados en JSON), IP de origen y agente de usuario.\n"
    "• Integridad Categórica y Restricciones Formales: 100% de tipos PostgreSQL definidos, restricciones CHECK para validar cantidades "
    "positivas y coherencia temporal, y claves foráneas tipadas."
)

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# -----------------------------------------------------------------------------
# 3. MATRIZ RESUMEN DE LAS 38 TABLAS
# -----------------------------------------------------------------------------
h2 = doc.add_paragraph()
r_h2 = h2.add_run("2. Matriz Resumen de las 38 Tablas del Sistema")
r_h2.font.name = "Calibri"
r_h2.font.size = Pt(14)
r_h2.font.bold = True
r_h2.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
h2.paragraph_format.space_after = Pt(6)

summary_tbl = doc.add_table(rows=len(sorted_tables) + 1, cols=5)
summary_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
summary_col_widths = [Inches(0.4), Inches(2.1), Inches(2.2), Inches(0.8), Inches(1.5)]

# Header
s_headers = ["N°", "Nombre de Tabla", "Módulo Funcional", "Campos", "Claves"]
for ci, text in enumerate(s_headers):
    c = summary_tbl.cell(0, ci)
    c.width = summary_col_widths[ci]
    set_cell_shading(c, "1B365D")
    set_cell_margins(c, top=80, bottom=80, left=80, right=80)
    set_cell_borders(c, top={"color": "1B365D", "sz": "6"}, bottom={"color": "1B365D", "sz": "6"})
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in [0, 3] else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(8.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Populate rows
for idx, tname in enumerate(sorted_tables, 1):
    row = summary_tbl.rows[idx]
    prevent_row_split(row)
    tdata = raw_metadata[tname]
    tinfo = TABLE_MODULES.get(tname, {"module": "General", "description": ""})
    
    col_count = len(tdata["columns"])
    pk_count = sum(1 for c in tdata["columns"] if "PK" in c["key"])
    fk_count = sum(1 for c in tdata["columns"] if "FK" in c["key"])
    
    bg = "FFFFFF" if idx % 2 != 0 else "F8FAFC"
    
    vals = [
        str(idx),
        tname,
        tinfo["module"],
        str(col_count),
        f"PK: {pk_count} | FK: {fk_count}"
    ]
    
    for ci, val in enumerate(vals):
        c = row.cells[ci]
        c.width = summary_col_widths[ci]
        set_cell_shading(c, bg)
        set_cell_margins(c, top=50, bottom=50, left=80, right=80)
        set_cell_borders(c, bottom={"color": "E2E8F0", "sz": "4"})
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in [0, 3] else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.name = "Calibri"
        r.font.size = Pt(8)
        if ci == 1:
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        elif ci == 4:
            r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
        else:
            r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

doc.add_page_break()

# -----------------------------------------------------------------------------
# 4. ESPECIFICACIÓN DETALLADA DE CADA TABLA EN "CAJITA"
# -----------------------------------------------------------------------------
h3 = doc.add_paragraph()
r_h3 = h3.add_run("3. Diccionario Físico de Datos: Especificación de Tablas en Cajas")
r_h3.font.name = "Calibri"
r_h3.font.size = Pt(16)
r_h3.font.bold = True
r_h3.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
h3.paragraph_format.space_after = Pt(4)

p_box_intro = doc.add_paragraph()
p_box_intro.paragraph_format.line_spacing = 1.15
p_box_intro.paragraph_format.space_after = Pt(14)
p_box_intro.add_run(
    "A continuación se presenta cada una de las 38 tablas de la base de datos contenida dentro de su respectiva "
    "cajita estructurada. En cada caja se detallan todos sus atributos físicos, su tipo de dato exacto en PostgreSQL, "
    "su condición de obligatoriedad (NOT NULL / NULL), su tipificación de clave (PK = Primary Key, FK = Foreign Key, "
    "o PK / FK para claves primarias compuestas), las referencias relacionales con reglas ON DELETE, su descripción funcional "
    "y el desglose de restricciones UNIQUE, CHECK e índices de optimización."
)

# Group tables by module for clean visual division
current_module = None

# Column widths for the 6-column inner table
col_widths = [
    Inches(1.25),  # Atributo
    Inches(1.25),  # Tipo de Dato
    Inches(0.80),  # Clave (PK/FK)
    Inches(0.65),  # Nulo
    Inches(1.35),  # Referencia FK
    Inches(1.70),  # Descripción
]
TOTAL_WIDTH = Inches(7.0)

for idx, tname in enumerate(sorted_tables, 1):
    tdata = raw_metadata[tname]
    tinfo = TABLE_MODULES.get(tname, {"module": "General", "description": "Tabla del sistema."})
    
    # Check if new module header is needed
    if tinfo["module"] != current_module:
        current_module = tinfo["module"]
        mod_h = doc.add_paragraph()
        mod_h.paragraph_format.space_before = Pt(14)
        mod_h.paragraph_format.space_after = Pt(6)
        r_mod = mod_h.add_run(f"■ {current_module.upper()}")
        r_mod.font.name = "Calibri"
        r_mod.font.size = Pt(13)
        r_mod.font.bold = True
        r_mod.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
        
    cols = tdata["columns"]
    ucs = tdata["unique_constraints"]
    cks = tdata["check_constraints"]
    idxs = tdata["indexes"]
    
    has_constraints = bool(ucs or cks or idxs)
    extra_rows = 1 if has_constraints else 0
    
    # Total rows in the unified Box Table:
    # Row 0: Box Header Banner (Merged 6 cols)
    # Row 1: Box Description Sub-banner (Merged 6 cols)
    # Row 2: Attributes Table Header (6 cols)
    # Rows 3 .. 3 + len(cols) - 1: Attribute Rows (6 cols)
    # Row 3 + len(cols) (optional): Constraints Footer (Merged 6 cols)
    total_table_rows = 3 + len(cols) + extra_rows
    
    box_tbl = doc.add_table(rows=total_table_rows, cols=6)
    box_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # ROW 0: BANNER HEADER
    row_0 = box_tbl.rows[0]
    prevent_row_split(row_0)
    # Merge cells across all 6 columns
    cell_0 = row_0.cells[0]
    for c in row_0.cells[1:]:
        cell_0.merge(c)
    cell_0.width = TOTAL_WIDTH
    set_cell_shading(cell_0, "1B365D")
    set_cell_margins(cell_0, top=100, bottom=100, left=140, right=140)
    set_cell_borders(cell_0, 
                     top={"color": "1B365D", "sz": "12"}, 
                     left={"color": "1B365D", "sz": "12"}, 
                     right={"color": "1B365D", "sz": "12"}, 
                     bottom={"color": "2563EB", "sz": "6"})
    
    p0 = cell_0.paragraphs[0]
    p0.paragraph_format.space_after = Pt(0)
    p0.paragraph_format.line_spacing = 1.15
    
    r0_num = p0.add_run(f"TABLA [{idx:02d}/38]: ")
    r0_num.font.name = "Calibri"
    r0_num.font.size = Pt(9.5)
    r0_num.font.bold = True
    r0_num.font.color.rgb = RGBColor(0x93, 0xC5, 0xFD)
    
    r0_name = p0.add_run(f"{tname.upper()}\n")
    r0_name.font.name = "Calibri"
    r0_name.font.size = Pt(12)
    r0_name.font.bold = True
    r0_name.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    r0_mod = p0.add_run(f"Módulo: {tinfo['module']}")
    r0_mod.font.name = "Calibri"
    r0_mod.font.size = Pt(8.5)
    r0_mod.font.italic = True
    r0_mod.font.color.rgb = RGBColor(0xBF, 0xDB, 0xFE)
    
    # ROW 1: DESCRIPTION SUB-BANNER
    row_1 = box_tbl.rows[1]
    prevent_row_split(row_1)
    cell_1 = row_1.cells[0]
    for c in row_1.cells[1:]:
        cell_1.merge(c)
    cell_1.width = TOTAL_WIDTH
    set_cell_shading(cell_1, "F1F5F9")
    set_cell_margins(cell_1, top=70, bottom=70, left=140, right=140)
    set_cell_borders(cell_1, 
                     left={"color": "1B365D", "sz": "12"}, 
                     right={"color": "1B365D", "sz": "12"}, 
                     bottom={"color": "CBD5E1", "sz": "6"})
    
    p1 = cell_1.paragraphs[0]
    p1.paragraph_format.space_after = Pt(0)
    p1.paragraph_format.line_spacing = 1.1
    r1_tag = p1.add_run("Propósito de la Entidad: ")
    r1_tag.font.name = "Calibri"
    r1_tag.font.size = Pt(8.5)
    r1_tag.font.bold = True
    r1_tag.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    
    r1_txt = p1.add_run(tinfo["description"])
    r1_txt.font.name = "Calibri"
    r1_txt.font.size = Pt(8.5)
    r1_txt.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    
    # ROW 2: ATTRIBUTE COLUMN HEADERS
    row_2 = box_tbl.rows[2]
    prevent_row_split(row_2)
    header_titles = ["Atributo", "Tipo de Dato", "Clave", "Nulo", "Referencia (FK)", "Descripción / Propósito"]
    for ci, h_title in enumerate(header_titles):
        c = row_2.cells[ci]
        c.width = col_widths[ci]
        set_cell_shading(c, "2563EB")
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        
        # Border
        b_left = {"color": "1B365D", "sz": "12"} if ci == 0 else {"color": "3B82F6", "sz": "4"}
        b_right = {"color": "1B365D", "sz": "12"} if ci == 5 else {"color": "3B82F6", "sz": "4"}
        set_cell_borders(c, top={"color": "CBD5E1", "sz": "4"}, bottom={"color": "1E40AF", "sz": "8"}, left=b_left, right=b_right)
        
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in [2, 3] else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(h_title)
        r.font.name = "Calibri"
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    # ROWS 3 .. 3 + len(cols) - 1: ATTRIBUTE ROWS
    for ci_idx, col in enumerate(cols):
        r_idx = 3 + ci_idx
        row_attr = box_tbl.rows[r_idx]
        prevent_row_split(row_attr)
        bg = "FFFFFF" if ci_idx % 2 == 0 else "F8FAFC"
        
        # Determine column description from dictionary
        col_desc = tinfo.get("columns", {}).get(col["name"], "Atributo operativo del registro.")
        fk_str = ", ".join(col["fks"]) if col["fks"] else "-"
        
        # Cells
        vals = [
            col["name"],
            col["type"],
            col["key"],
            "NULL" if col["nullable"] else "NOT NULL",
            fk_str,
            col_desc
        ]
        
        for ci, val in enumerate(vals):
            c = row_attr.cells[ci]
            c.width = col_widths[ci]
            set_cell_shading(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=70, right=70)
            
            b_left = {"color": "1B365D", "sz": "12"} if ci == 0 else {"color": "E2E8F0", "sz": "4"}
            b_right = {"color": "1B365D", "sz": "12"} if ci == 5 else {"color": "E2E8F0", "sz": "4"}
            
            # If last row and no constraints, bottom border closes the box
            if r_idx == total_table_rows - 1:
                b_bottom = {"color": "1B365D", "sz": "12"}
            else:
                b_bottom = {"color": "E2E8F0", "sz": "4"}
                
            set_cell_borders(c, bottom=b_bottom, left=b_left, right=b_right)
            
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.05
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in [2, 3] else WD_ALIGN_PARAGRAPH.LEFT
            
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(8)
            
            # Key styling
            if ci == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
            elif ci == 1:
                r.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            elif ci == 2:
                r.font.bold = True
                if val == "PK":
                    r.font.color.rgb = RGBColor(0xDC, 0x26, 0x26)  # Red
                elif val == "FK":
                    r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)  # Blue
                elif val == "PK / FK":
                    r.font.color.rgb = RGBColor(0x7C, 0x3A, 0xED)  # Purple
                else:
                    r.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)  # Gray
            elif ci == 3:
                if val == "NOT NULL":
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
                else:
                    r.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
            elif ci == 4:
                if val != "-":
                    r.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
                else:
                    r.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
            else:
                r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
                
    # OPTIONAL ROW: CONSTRAINTS & INDEXES FOOTER
    if has_constraints:
        row_foot = box_tbl.rows[total_table_rows - 1]
        prevent_row_split(row_foot)
        cell_foot = row_foot.cells[0]
        for c in row_foot.cells[1:]:
            cell_foot.merge(c)
        cell_foot.width = TOTAL_WIDTH
        set_cell_shading(cell_foot, "F8FAFC")
        set_cell_margins(cell_foot, top=60, bottom=70, left=140, right=140)
        set_cell_borders(cell_foot, 
                         top={"color": "CBD5E1", "sz": "6"}, 
                         bottom={"color": "1B365D", "sz": "12"}, 
                         left={"color": "1B365D", "sz": "12"}, 
                         right={"color": "1B365D", "sz": "12"})
        
        pf = cell_foot.paragraphs[0]
        pf.paragraph_format.line_spacing = 1.05
        rf_title = pf.add_run("Restricciones e Índices del Motor (PostgreSQL):\n")
        rf_title.font.name = "Calibri"
        rf_title.font.size = Pt(8)
        rf_title.font.bold = True
        rf_title.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        
        c_lines = []
        for uc in ucs:
            c_lines.append(f"• UNIQUE [{uc['name']}]: ({', '.join(uc['columns'])})")
        for ck in cks:
            c_lines.append(f"• CHECK [{ck['name']}]: {ck['sql']}")
        for ix in idxs:
            u_tag = " [UNIQUE]" if ix['unique'] else ""
            c_lines.append(f"• INDEX [{ix['name']}]{u_tag}: ({', '.join(ix['columns'])})")
            
        rf_body = pf.add_run("\n".join(c_lines))
        rf_body.font.name = "Calibri"
        rf_body.font.size = Pt(7.5)
        rf_body.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
        
    # Spacer paragraph after each box
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

# -----------------------------------------------------------------------------
# 5. APÉNDICE: GUÍA DE DESPLIEGUE DEL SCRIPT SQL
# -----------------------------------------------------------------------------
doc.add_page_break()
h_ap = doc.add_paragraph()
r_ap = h_ap.add_run("4. Apéndice: Guía de Despliegue y Ejecución del Script SQL")
r_ap.font.name = "Calibri"
r_ap.font.size = Pt(16)
r_ap.font.bold = True
r_ap.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
h_ap.paragraph_format.space_after = Pt(8)

p_ap = doc.add_paragraph()
p_ap.paragraph_format.line_spacing = 1.15
p_ap.paragraph_format.space_after = Pt(8)
p_ap.add_run(
    "El script DDL generado en el archivo database/fashionstore_complete_schema.sql contiene la totalidad de las instrucciones "
    "DDL ordenadas de forma topológicamente acíclica, lo que permite su ejecución limpia y sin errores de dependencias cruzadas "
    "sobre cualquier instancia de PostgreSQL (versiones 14, 15, 16 o superior). A continuación se especifican las modalidades "
    "de ejecución recomendadas:"
)

tbl_steps = doc.add_table(rows=4, cols=2)
tbl_steps.alignment = WD_TABLE_ALIGNMENT.CENTER
col_w_steps = [Inches(2.0), Inches(5.0)]

step_data = [
    ("1. Vía Terminal / psql (PostgreSQL Nativo)", "psql -U fashionstore -d fashionstore -h localhost -p 5432 -f database/fashionstore_complete_schema.sql\nPermite la reconstrucción inmediata y limpia del catálogo completo."),
    ("2. Vía Docker Compose (Contenedor PostgreSQL)", "docker compose exec -T postgres psql -U fashionstore -d fashionstore < database/fashionstore_complete_schema.sql\nAplica los esquemas directamente en el contenedor sin requerir clientes locales."),
    ("3. Vía Gestor Gráfico (DBeaver / pgAdmin / Navicat)", "Abrir el archivo .sql en el editor de consultas SQL, seleccionar la base de datos de destino y ejecutar con 'Execute SQL Script' (Alt + X)."),
    ("4. Vía Alembic / FastAPI (Backend)", "El backend ejecuta automáticamente las migraciones declarativas mediante el comando:\nalembic upgrade head\nEl cual sincroniza los modelos SQLAlchemy con el estado del esquema.")
]

for si, (stitle, sbody) in enumerate(step_data):
    row = tbl_steps.rows[si]
    prevent_row_split(row)
    c0 = row.cells[0]
    c1 = row.cells[1]
    c0.width = col_w_steps[0]
    c1.width = col_w_steps[1]
    
    set_cell_shading(c0, "1B365D")
    set_cell_margins(c0, top=80, bottom=80, left=100, right=100)
    set_cell_borders(c0, bottom={"color": "E2E8F0", "sz": "4"})
    p0 = c0.paragraphs[0]
    r0 = p0.add_run(stitle)
    r0.font.name = "Calibri"
    r0.font.size = Pt(8.5)
    r0.font.bold = True
    r0.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    set_cell_shading(c1, "F8FAFC" if si % 2 == 0 else "FFFFFF")
    set_cell_margins(c1, top=80, bottom=80, left=100, right=100)
    set_cell_borders(c1, bottom={"color": "E2E8F0", "sz": "4"})
    p1 = c1.paragraphs[0]
    r1 = p1.add_run(sbody)
    r1.font.name = "Calibri"
    r1.font.size = Pt(8.5)
    r1.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

doc.add_paragraph().paragraph_format.space_after = Pt(20)

output_path = "Diccionario_Base_de_Datos_FashionStore.docx"
doc.save(output_path)
print(f"Document successfully created at: {output_path} ({os.path.getsize(output_path)} bytes)")
