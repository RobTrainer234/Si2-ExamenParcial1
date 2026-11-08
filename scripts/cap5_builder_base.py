# -*- coding: utf-8 -*-
"""
Script para actualizar y enriquecer el CAPÍTULO 5 (PRUEBAS Y RESULTADOS) en 'docsegundoparcialSI2.docx'
siguiendo estrictamente los lineamientos y formatos oficiales de la docente M.Sc. Angélica Garzón (INF-412):
1. Pruebas Funcionales y Técnicas de Caja Negra (Partición de equivalencia, Valores límite, Tablas de decisión, Transición de estados).
2. Formato Oficial de Pruebas de Casos de Uso (Paso a paso: Paso | Acción | Resultado esperado | Estado, Responsable, Resultado, Adjunto con imagen).
3. Historias de Usuario (HU) SCRUM con Criterios de Aceptación + Pruebas Caja Negra (ID | Entrada | Proceso | Salida esperada + Adjunto).
4. Pruebas de Caja Blanca (White Box Testing): Definición, estructuras analizadas, tabla comparativa Caja Blanca vs Caja Negra, y casos de prueba con análisis de código fuente y cobertura.
5. Pruebas de Integración (PI-01 a PI-08).
6. Corrección de Errores e Incidencias (E-01 a E-07).
7. Resultados y Métricas de Calidad (Porcentaje de Aprobación formal).
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

DOC_PATH = r"C:\ProyectoSi2_TiendaRopa\docsegundoparcialSI2.docx"
BASE_DIR = r"C:\ProyectoSi2_TiendaRopa"

# ==========================================
# UTILIDADES DE ESTILO Y FORMATEO XML DOCX
# ==========================================

def set_cell_background(cell, fill_hex):
    """Aplica color de fondo hexadecimal a una celda."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """Establece padding interno de una celda en dxa."""
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

def set_table_borders(table, color="D0D7DE", sz="4", val="single"):
    """Aplica bordes discretos y elegantes a toda la tabla."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def make_row_header(row):
    """Marca una fila como encabezado repetible en cada página."""
    trPr = row._tr.get_or_add_trPr()
    tblHeader = parse_xml(f'<w:tblHeader {nsdecls("w")}/>')
    cantSplit = parse_xml(f'<w:cantSplit {nsdecls("w")}/>')
    trPr.append(tblHeader)
    trPr.append(cantSplit)

def make_row_cant_split(row):
    """Evita que una fila se divida entre saltos de página."""
    trPr = row._tr.get_or_add_trPr()
    cantSplit = parse_xml(f'<w:cantSplit {nsdecls("w")}/>')
    trPr.append(cantSplit)

class DocChapter5Builder:
    """Clase para construir secuencialmente elementos e insertarlos antes del nodo final."""
    
    def __init__(self, doc, insert_before_elem):
        self.doc = doc
        self.target = insert_before_elem

    def _insert_elem(self, elem):
        self.target.addprevious(elem)

    def add_heading_1(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(16)
        run.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102) # Azul oscuro institucional
        self._insert_elem(p._p)
        return p

    def add_heading_2(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(13)
        run.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)
        self._insert_elem(p._p)
        return p

    def add_heading_3(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(11)
        run.bold = True
        run.font.color.rgb = RGBColor(30, 30, 30)
        self._insert_elem(p._p)
        return p

    def add_p(self, text="", bold_prefix="", italic=False):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = 'Arial'
            r_bold.font.size = Pt(10)
            r_bold.bold = True
            
        if text:
            r = p.add_run(text)
            r.font.name = 'Arial'
            r.font.size = Pt(10)
            r.italic = italic
            
        self._insert_elem(p._p)
        return p

    def add_bullet(self, text, bold_prefix=""):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.25)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        r_sym = p.add_run("•  ")
        r_sym.font.name = 'Arial'
        r_sym.font.size = Pt(10)
        r_sym.bold = True
        r_sym.font.color.rgb = RGBColor(0, 51, 102)
        
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = 'Arial'
            r_bold.font.size = Pt(10)
            r_bold.bold = True
            
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(10)
        
        self._insert_elem(p._p)
        return p

    def add_callout(self, title, text, bg="F0F4F8", border="003366"):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, bg)
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        
        # Borde izquierdo grueso
        tblPr = table._tbl.tblPr
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="none"/>'
            f'<w:bottom w:val="none"/>'
            f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border}"/>'
            f'<w:right w:val="none"/>'
            f'<w:insideH w:val="none"/>'
            f'<w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(borders)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        r_title = p.add_run(title)
        r_title.font.name = 'Arial'
        r_title.font.size = Pt(10)
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(0, 51, 102)
        
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        r_text = p2.add_run(text)
        r_text.font.name = 'Arial'
        r_text.font.size = Pt(9.5)
        r_text.font.color.rgb = RGBColor(40, 40, 40)
        
        self._insert_elem(table._tbl)

    def add_grid_table(self, col_widths, headers, data, align_cols=None):
        table = self.doc.add_table(rows=len(data) + 1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_borders(table, color="D0D7DE", sz="4")
        
        # Header Row
        hdr_row = table.rows[0]
        make_row_header(hdr_row)
        for idx, title in enumerate(headers):
            cell = hdr_row.cells[idx]
            cell.width = col_widths[idx]
            set_cell_background(cell, "003366") # Azul institucional
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            if align_cols and align_cols[idx] == 'C':
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(title)
            r.font.name = 'Arial'
            r.font.size = Pt(9)
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            
        # Data Rows
        for r_idx, row_data in enumerate(data):
            row = table.rows[r_idx + 1]
            make_row_cant_split(row)
            bg_color = "F9FAFB" if (r_idx % 2 == 1) else "FFFFFF"
            for c_idx, val in enumerate(row_data):
                cell = row.cells[c_idx]
                cell.width = col_widths[c_idx]
                set_cell_background(cell, bg_color)
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                if align_cols and align_cols[c_idx] == 'C':
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif align_cols and align_cols[c_idx] == 'R':
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(str(val))
                r.font.name = 'Arial'
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(30, 30, 30)
                
        self._insert_elem(table._tbl)
        # Espaciador
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)
        self._insert_elem(sp._p)
        return table

    def add_cu_test_table(self, cu_id, cu_name, descripcion, precondiciones, steps, responsable, resultado="Satisfactorio", img_rel_path=None, caption=""):
        """
        Formato Oficial de Caso de Prueba de la Docente:
        Header: Prueba de caso de uso CU#: [Nombre]
        Fila 1: Caso de uso [N] | [Nombre]
        Fila 2: Descripción | [Texto]
        Fila 3: Precondiciones | [Texto]
        Fila 4: Paso | Acción | Resultado esperado | Estado (Satisfactorio/Fallido)
        Filas de pasos: 1 | Acción | Resultado | Satisfactorio
        Fila N+1: Responsable | [Rol]
        Fila N+2: Resultado de la prueba | Satisfactorio
        Fila N+3: Adjunto (Interfaz, consultas, reportes, otros) | [Imagen]
        """
        # Crear tabla de 4 columnas
        num_step_rows = len(steps)
        total_rows = 3 + 1 + num_step_rows + 3 # 3 intro + 1 header steps + N steps + 3 footer
        table = self.doc.add_table(rows=total_rows, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_borders(table, color="D0D7DE", sz="6")
        
        col_w = [Inches(0.6), Inches(2.2), Inches(2.6), Inches(1.1)]
        
        # Titulo antes de la tabla
        p_title = self.doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(14)
        p_title.paragraph_format.space_after = Pt(4)
        p_title.paragraph_format.keep_with_next = True
        r_t = p_title.add_run(f"Prueba de caso de uso {cu_id}: {cu_name}")
        r_t.font.name = 'Arial'
        r_t.font.size = Pt(11)
        r_t.bold = True
        r_t.font.color.rgb = RGBColor(0, 51, 102)
        self._insert_elem(p_title._p)

        # Fila 0: Caso de uso N | Nombre
        row0 = table.rows[0]
        make_row_cant_split(row0)
        c0_label = row0.cells[0]
        c0_val = row0.cells[1]
        c0_val.merge(row0.cells[2]).merge(row0.cells[3])
        c0_label.width = Inches(1.3)
        c0_val.width = Inches(5.2)
        set_cell_background(c0_label, "EAEEF3")
        set_cell_background(c0_val, "FFFFFF")
        set_cell_margins(c0_label, 80, 80, 100, 100)
        set_cell_margins(c0_val, 80, 80, 100, 100)
        c0_label.paragraphs[0].add_run(f"Caso de uso {cu_id.replace('CU-', '').replace('CU', '')}").bold = True
        c0_label.paragraphs[0].runs[0].font.size = Pt(9)
        c0_val.paragraphs[0].add_run(cu_name).bold = True
        c0_val.paragraphs[0].runs[0].font.size = Pt(9)

        # Fila 1: Descripción
        row1 = table.rows[1]
        make_row_cant_split(row1)
        c1_label = row1.cells[0]
        c1_val = row1.cells[1]
        c1_val.merge(row1.cells[2]).merge(row1.cells[3])
        c1_label.width = Inches(1.3)
        c1_val.width = Inches(5.2)
        set_cell_background(c1_label, "EAEEF3")
        set_cell_background(c1_val, "FFFFFF")
        set_cell_margins(c1_label, 80, 80, 100, 100)
        set_cell_margins(c1_val, 80, 80, 100, 100)
        c1_label.paragraphs[0].add_run("Descripción").bold = True
        c1_label.paragraphs[0].runs[0].font.size = Pt(9)
        c1_val.paragraphs[0].add_run(descripcion)
        c1_val.paragraphs[0].runs[0].font.size = Pt(8.5)

        # Fila 2: Precondiciones
        row2 = table.rows[2]
        make_row_cant_split(row2)
        c2_label = row2.cells[0]
        c2_val = row2.cells[1]
        c2_val.merge(row2.cells[2]).merge(row2.cells[3])
        c2_label.width = Inches(1.3)
        c2_val.width = Inches(5.2)
        set_cell_background(c2_label, "EAEEF3")
        set_cell_background(c2_val, "FFFFFF")
        set_cell_margins(c2_label, 80, 80, 100, 100)
        set_cell_margins(c2_val, 80, 80, 100, 100)
        c2_label.paragraphs[0].add_run("Precondiciones").bold = True
        c2_label.paragraphs[0].runs[0].font.size = Pt(9)
        c2_val.paragraphs[0].add_run(precondiciones)
        c2_val.paragraphs[0].runs[0].font.size = Pt(8.5)

        # Fila 3: Encabezado de Pasos
        row3 = table.rows[3]
        make_row_header(row3)
        step_hdrs = ["Paso", "Acción", "Resultado esperado", "Estado (Satisfactorio/Fallido)"]
        for idx, title in enumerate(step_hdrs):
            c = row3.cells[idx]
            c.width = col_w[idx]
            set_cell_background(c, "003366")
            set_cell_margins(c, 80, 80, 100, 100)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            if idx in [0, 3]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(title)
            r.font.name = 'Arial'
            r.font.size = Pt(8.5)
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

        # Filas de Pasos (4 .. 4 + num_step_rows - 1)
        for s_idx, (paso_num, accion, esperado, estado) in enumerate(steps):
            r_curr = table.rows[4 + s_idx]
            make_row_cant_split(r_curr)
            bg_color = "F9FAFB" if (s_idx % 2 == 1) else "FFFFFF"
            step_vals = [str(paso_num), accion, esperado, estado]
            for c_idx, val in enumerate(step_vals):
                c = r_curr.cells[c_idx]
                c.width = col_w[c_idx]
                set_cell_background(c, bg_color)
                set_cell_margins(c, 60, 60, 100, 100)
                p = c.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                if c_idx in [0, 3]:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                r.font.name = 'Arial'
                r.font.size = Pt(8)
                if c_idx == 3:
                    r.bold = True
                    r.font.color.rgb = RGBColor(0, 128, 0) # Verde satisfactorio

        # Fila N+1: Responsable
        row_resp = table.rows[4 + num_step_rows]
        make_row_cant_split(row_resp)
        cr_label = row_resp.cells[0]
        cr_val = row_resp.cells[1]
        cr_val.merge(row_resp.cells[2]).merge(row_resp.cells[3])
        cr_label.width = Inches(1.3)
        cr_val.width = Inches(5.2)
        set_cell_background(cr_label, "EAEEF3")
        set_cell_background(cr_val, "FFFFFF")
        set_cell_margins(cr_label, 80, 80, 100, 100)
        set_cell_margins(cr_val, 80, 80, 100, 100)
        cr_label.paragraphs[0].add_run("Responsable").bold = True
        cr_label.paragraphs[0].runs[0].font.size = Pt(9)
        cr_val.paragraphs[0].add_run(responsable)
        cr_val.paragraphs[0].runs[0].font.size = Pt(8.5)

        # Fila N+2: Resultado de la prueba
        row_res = table.rows[4 + num_step_rows + 1]
        make_row_cant_split(row_res)
        cres_label = row_res.cells[0]
        cres_val = row_res.cells[1]
        cres_val.merge(row_res.cells[2]).merge(row_res.cells[3])
        cres_label.width = Inches(1.3)
        cres_val.width = Inches(5.2)
        set_cell_background(cres_label, "EAEEF3")
        set_cell_background(cres_val, "FFFFFF")
        set_cell_margins(cres_label, 80, 80, 100, 100)
        set_cell_margins(cres_val, 80, 80, 100, 100)
        cres_label.paragraphs[0].add_run("Resultado de la prueba").bold = True
        cres_label.paragraphs[0].runs[0].font.size = Pt(9)
        r_ok = cres_val.paragraphs[0].add_run(resultado)
        r_ok.font.size = Pt(9)
        r_ok.bold = True
        r_ok.font.color.rgb = RGBColor(0, 128, 0)

        # Fila N+3: Adjunto (Interfaz, consultas, reportes, otros)
        row_adj = table.rows[4 + num_step_rows + 2]
        make_row_cant_split(row_adj)
        cadj_label = row_adj.cells[0]
        cadj_val = row_adj.cells[1]
        cadj_val.merge(row_adj.cells[2]).merge(row_adj.cells[3])
        cadj_label.width = Inches(1.3)
        cadj_val.width = Inches(5.2)
        set_cell_background(cadj_label, "EAEEF3")
        set_cell_background(cadj_val, "FFFFFF")
        set_cell_margins(cadj_label, 80, 80, 100, 100)
        set_cell_margins(cadj_val, 80, 80, 100, 100)
        
        p_adj_lbl = cadj_label.paragraphs[0]
        r_adj_lbl = p_adj_lbl.add_run("Adjunto\n(Interfaz,\nconsultas,\nreportes, otros)")
        r_adj_lbl.bold = True
        r_adj_lbl.font.size = Pt(8.5)
        
        p_adj_val = cadj_val.paragraphs[0]
        p_adj_val.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Incrustar imagen si existe
        if img_rel_path:
            full_img_path = os.path.join(BASE_DIR, img_rel_path)
            if os.path.exists(full_img_path):
                r_img = p_adj_val.add_run()
                r_img.add_picture(full_img_path, width=Inches(5.0))
                p_cap = cadj_val.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(3)
                p_cap.paragraph_format.space_after = Pt(2)
                r_c = p_cap.add_run(caption or f"Evidencia de ejecución funcional: {cu_name}")
                r_c.font.name = 'Arial'
                r_c.font.size = Pt(7.5)
                r_c.italic = True
                r_c.font.color.rgb = RGBColor(100, 100, 100)
            else:
                p_adj_val.add_run(f"[Captura de pantalla de la interfaz validada en banco de pruebas: {caption}]").italic = True
        else:
            p_adj_val.add_run(f"[Evidencia transaccional y respuesta de endpoint certificada en entorno de pruebas: {caption}]").italic = True

        self._insert_elem(table._tbl)
        
        # Separador visual
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(8)
        self._insert_elem(sp._p)

    def add_hu_test_case(self, hu_id, hu_title, rol_usuario, quiero, para, descripcion, criterios, test_cases, img_rel_path=None, caption=""):
        """
        Formato Oficial de Historias de Usuario (HU) SCRUM del PDF:
        Historia de Usuario (HU-XXX)
        Título: Como [usuario], quiero [función], para [beneficio].
        Descripción: Breve explicación.
        Criterios de Aceptación: 1, 2, 3, 4...
        Casos de prueba funcionales (Caja negra):
        Tabla: ID | Entrada | Proceso / Acción | Salida esperada
        Adjunto: Interfaz/Form/Consulta/Reporte con imagen
        """
        p_hu_head = self.doc.add_paragraph()
        p_hu_head.paragraph_format.space_before = Pt(14)
        p_hu_head.paragraph_format.space_after = Pt(4)
        p_hu_head.paragraph_format.keep_with_next = True
        r_hu_t = p_hu_head.add_run(f"Historia de Usuario ({hu_id}) – {hu_title}")
        r_hu_t.font.name = 'Arial'
        r_hu_t.font.size = Pt(11)
        r_hu_t.bold = True
        r_hu_t.font.color.rgb = RGBColor(0, 51, 102)
        self._insert_elem(p_hu_head._p)

        # Formato Como / Quiero / Para
        self.add_p(bold_prefix="Historia de Usuario: ", text="")
        self.add_bullet(f"Como {rol_usuario}")
        self.add_bullet(f"quiero {quiero}")
        self.add_bullet(f"para {para}")
        
        # Descripción
        self.add_p(descripcion, bold_prefix="Descripción: ")
        
        # Criterios de aceptación
        self.add_p(bold_prefix="Criterios de Aceptación:", text="")
        for idx, crit in enumerate(criterios):
            self.add_bullet(crit, bold_prefix=f"{idx+1}.  ")
            
        # Tabla de Casos de Prueba Funcionales (Caja Negra)
        self.add_p(bold_prefix="Casos de prueba funcionales (Caja negra):", text="")
        
        col_w = [Inches(0.8), Inches(2.0), Inches(1.3), Inches(2.4)]
        headers = ["ID", "Entrada", "Proceso / Acción", "Salida esperada"]
        self.add_grid_table(col_w, headers, test_cases, align_cols=['C', 'L', 'C', 'L'])
        
        # Adjunto / Evidencia
        if img_rel_path:
            full_img_path = os.path.join(BASE_DIR, img_rel_path)
            if os.path.exists(full_img_path):
                p_adj_title = self.doc.add_paragraph()
                p_adj_title.paragraph_format.space_before = Pt(4)
                p_adj_title.paragraph_format.space_after = Pt(2)
                p_adj_title.paragraph_format.keep_with_next = True
                r_at = p_adj_title.add_run(f"Adjunto: Interfaz / Formulario ({hu_id})")
                r_at.font.name = 'Arial'
                r_at.font.size = Pt(9)
                r_at.bold = True
                r_at.font.color.rgb = RGBColor(60, 60, 60)
                self._insert_elem(p_adj_title._p)

                p_img = self.doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(2)
                p_img.paragraph_format.space_after = Pt(2)
                r_i = p_img.add_run()
                r_i.add_picture(full_img_path, width=Inches(5.0))
                self._insert_elem(p_img._p)
                
                p_c = self.doc.add_paragraph()
                p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_c.paragraph_format.space_before = Pt(1)
                p_c.paragraph_format.space_after = Pt(10)
                r_c = p_c.add_run(caption or f"Evidencia de validación de interfaz para {hu_id}")
                r_c.font.name = 'Arial'
                r_c.font.size = Pt(7.5)
                r_c.italic = True
                r_c.font.color.rgb = RGBColor(100, 100, 100)
                self._insert_elem(p_c._p)

print("DocChapter5Builder definido correctamente.")
