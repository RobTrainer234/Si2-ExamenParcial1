# -*- coding: utf-8 -*-
"""
Script para actualizar y enriquecer las secciones:
- 4.3. Implementación de la base de datos
- 4.4. Desarrollo de los módulos del sistema (4.4.1 a 4.4.7)
- 4.5. Integración de componentes (4.5.1 a 4.5.7)
en 'docsegundoparcialSI2.docx' tomando como guía técnica y arquitectónica
el documento 'Grupo #6 -2daPresentación.docx'.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

DOC_PATH = r"C:\ProyectoSi2_TiendaRopa\docsegundoparcialSI2.docx"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
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

class Cap4Builder:
    def __init__(self, doc, insert_before_elem):
        self.doc = doc
        self.target = insert_before_elem

    def _insert(self, elem):
        self.target.addprevious(elem)

    def add_heading_2(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(13)
        run.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)
        self._insert(p._p)
        return p

    def add_heading_3(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(11)
        run.bold = True
        run.font.color.rgb = RGBColor(30, 30, 30)
        self._insert(p._p)
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
            
        self._insert(p._p)
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
        
        self._insert(p._p)
        return p

    def add_callout(self, title, text, bg="F0F4F8", border="003366"):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, bg)
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        
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
        p.paragraph_format.space_after = Pt(3)
        r_title = p.add_run(title)
        r_title.font.name = 'Arial'
        r_title.font.size = Pt(9.5)
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(0, 51, 102)
        
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        r_text = p2.add_run(text)
        r_text.font.name = 'Arial'
        r_text.font.size = Pt(9)
        r_text.font.color.rgb = RGBColor(40, 40, 40)
        
        self._insert(table._tbl)
        
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)
        self._insert(sp._p)

    def add_code_block(self, title, code_lines, language=""):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, "F6F8FA")
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        
        tblPr = table._tbl.tblPr
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            f'<w:left w:val="single" w:sz="12" w:space="0" w:color="003366"/>'
            f'<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            f'<w:insideH w:val="none"/>'
            f'<w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(borders)
        
        p_hdr = cell.paragraphs[0]
        p_hdr.paragraph_format.space_before = Pt(0)
        p_hdr.paragraph_format.space_after = Pt(4)
        r_h = p_hdr.add_run(title)
        r_h.font.name = 'Arial'
        r_h.font.size = Pt(8.5)
        r_h.bold = True
        r_h.font.color.rgb = RGBColor(0, 51, 102)
        
        p_code = cell.add_paragraph()
        p_code.paragraph_format.space_before = Pt(0)
        p_code.paragraph_format.space_after = Pt(0)
        p_code.paragraph_format.line_spacing = 1.0
        r_code = p_code.add_run("\n".join(code_lines))
        r_code.font.name = 'Consolas'
        r_code.font.size = Pt(8)
        r_code.font.color.rgb = RGBColor(36, 41, 47)
        
        self._insert(table._tbl)
        
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)
        self._insert(sp._p)

print("Cap4Builder definido correctamente.")
