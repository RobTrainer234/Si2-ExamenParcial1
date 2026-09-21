from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import html
from io import BytesIO
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.modules.reports.schemas import ReportSnapshot

FIXED_TIMESTAMP = datetime(2024, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class ExportFile:
    content: bytes
    media_type: str
    filename: str


def safe_export_filename(format_name: str, snapshot: ReportSnapshot) -> str:
    date_from = snapshot.filters.date_from.date().isoformat() if snapshot.filters.date_from else "all"
    date_to = snapshot.filters.date_to.date().isoformat() if snapshot.filters.date_to else "all"
    branch = f"branch-{snapshot.filters.branch_id}" if snapshot.filters.branch_id is not None else "all-branches"
    return f"fashionstore-report-{date_from}-to-{date_to}-{branch}.{format_name}"


def export_snapshot(snapshot: ReportSnapshot, format_name: str) -> ExportFile:
    if format_name == "xlsx":
        return ExportFile(
            content=build_excel(snapshot),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=safe_export_filename("xlsx", snapshot),
        )
    if format_name == "pdf":
        return ExportFile(
            content=build_pdf(snapshot),
            media_type="application/pdf",
            filename=safe_export_filename("pdf", snapshot),
        )
    if format_name == "pptx":
        return ExportFile(
            content=build_pptx(snapshot),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=safe_export_filename("pptx", snapshot),
        )
    raise ValueError("Unsupported export format")


def _decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _money(value: object) -> str:
    return f"{_decimal(value):.2f}"


def _normalize_zip_timestamps(content: bytes) -> bytes:
    source = BytesIO(content)
    target = BytesIO()
    ns_uri = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ET.register_namespace("", ns_uri)
    with ZipFile(source) as input_zip, ZipFile(target, "w") as output_zip:
        for name in input_zip.namelist():
            data = input_zip.read(name)
            if name == "xl/styles.xml":
                try:
                    root = ET.fromstring(data)
                    for xf in root.findall(f".//{{{ns_uri}}}cellXfs/{{{ns_uri}}}xf"):
                        fill_id = int(xf.get("fillId", 0))
                        font_id = int(xf.get("fontId", 0))
                        border_id = int(xf.get("borderId", 0))
                        num_fmt_id = int(xf.get("numFmtId", 0))
                        if fill_id > 0:
                            xf.set("applyFill", "1")
                        if font_id > 0:
                            xf.set("applyFont", "1")
                        if border_id > 0:
                            xf.set("applyBorder", "1")
                        if num_fmt_id > 0:
                            xf.set("applyNumberFormat", "1")
                    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                except Exception:
                    pass
            info = ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            output_zip.writestr(info, data)
    return target.getvalue()


# ==============================================================================
# MOTOR EXCEL PROFESIONAL (OPENPYXL)
# ==============================================================================

def build_excel(snapshot: ReportSnapshot) -> bytes:
    workbook = Workbook()
    workbook.properties.creator = "FashionStore Atelier & Boutique"
    workbook.properties.title = "Consolidado Ejecutivo de Rendimiento Comercial"
    workbook.properties.subject = "Reporte Ejecutivo Ciclo 3"
    workbook.properties.created = FIXED_TIMESTAMP
    workbook.properties.modified = FIXED_TIMESTAMP

    # --------------------------------------------------------------------------
    # ESTILOS CORPORATIVOS "EXECUTIVE NAVY & GOLD" (100% Compatibles con Excel)
    # --------------------------------------------------------------------------
    header_fill = PatternFill(fill_type="solid", start_color="FF1F4E78", end_color="FF1F4E78")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFFFF")
    header_border = Border(
        left=Side(style="thin", color="FFCBD5E1"),
        right=Side(style="thin", color="FFCBD5E1"),
        top=Side(style="medium", color="FF16365C"),
        bottom=Side(style="medium", color="FF0F243E"),
    )

    section_fill = PatternFill(fill_type="solid", start_color="FF2F5597", end_color="FF2F5597")
    section_font = Font(name="Calibri", size=10, bold=True, color="FFFFFFFF")

    font_data = Font(name="Calibri", size=10, color="FF1F2937")
    font_bold = Font(name="Calibri", size=10, bold=True, color="FF111827")
    font_total = Font(name="Calibri", size=10, bold=True, color="FF0F172A")

    zebra_even = PatternFill(fill_type="solid", start_color="FFFFFFFF", end_color="FFFFFFFF")
    zebra_odd = PatternFill(fill_type="solid", start_color="FFF8FAFC", end_color="FFF8FAFC")
    total_fill = PatternFill(fill_type="solid", start_color="FFFEF3C7", end_color="FFFEF3C7")

    thin_border = Border(
        left=Side(style="thin", color="FFE2E8F0"),
        right=Side(style="thin", color="FFE2E8F0"),
        top=Side(style="thin", color="FFE2E8F0"),
        bottom=Side(style="thin", color="FFE2E8F0"),
    )
    total_border = Border(
        left=Side(style="thin", color="FFCBD5E1"),
        right=Side(style="thin", color="FFCBD5E1"),
        top=Side(style="thin", color="FF1F4E78"),
        bottom=Side(style="double", color="FF0F172A"),
    )

    # --------------------------------------------------------------------------
    # 1. HOJA: Summary (Tablero de Control Financiero y Resumen Consolidado)
    # --------------------------------------------------------------------------
    summary = workbook.active
    summary.title = "Summary"
    summary.sheet_properties.tabColor = "FF1F4E78"
    summary.views.sheetView[0].showGridLines = True
    summary.freeze_panes = "A2"

    # Fila 1: Cabeceras de Columnas Explícitas
    summary_headers = ["Métrica / Indicador", "Valor Registrado", "Unidad", "Descripción del Indicador"]
    summary.append(summary_headers)
    summary.row_dimensions[1].height = 28
    for cell in summary[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(vertical="center", horizontal="left" if cell.column <= 2 else "center")
        cell.border = header_border

    # Datos base del resumen financiero (Filas 2 a 9)
    sales_cnt = snapshot.revenue.sales_count
    total_val = _decimal(snapshot.revenue.total)
    subtotal_val = _decimal(snapshot.revenue.subtotal)
    discount_val = _decimal(snapshot.revenue.discount)
    avg_ticket = (total_val / Decimal(sales_cnt)) if sales_cnt > 0 else Decimal("0.00")

    date_from_str = snapshot.filters.date_from.isoformat() if snapshot.filters.date_from else "Todas (Todo el historial)"
    date_to_str = snapshot.filters.date_to.isoformat() if snapshot.filters.date_to else "Todas (Todo el historial)"
    branch_val = snapshot.filters.branch_id if snapshot.filters.branch_id is not None else "Todas las sucursales"

    summary_rows = [
        ["Total de Ventas (Órdenes)", sales_cnt, "Órdenes", "Total de compras confirmadas en el período auditado"],
        ["Subtotal Facturado Bruto", subtotal_val, "BOB", "Facturación comercial bruta antes de promociones y descuentos"],
        ["Descuentos Promocionales", discount_val, "BOB", "Ahorro total otorgado a clientes mediante promociones (CU20)"],
        ["Total Ingresos Netos", total_val, "BOB", "Ingresos netos consolidados efectivamente liquidados"],
        ["Ticket Promedio por Venta", avg_ticket, "BOB", "Monto promedio facturado por transacción"],
        ["Fecha Desde (Filtro)", date_from_str, "Filtro", "Límite inferior del rango de fechas evaluado"],
        ["Fecha Hasta (Filtro)", date_to_str, "Filtro", "Límite superior del rango de fechas evaluado"],
        ["Sucursal Auditada", branch_val, "Filtro", "Alcance de sucursales físicas y digitales evaluadas"],
    ]

    for r_idx, row in enumerate(summary_rows, start=2):
        summary.append(row)
        summary.row_dimensions[r_idx].height = 24
        is_odd = (r_idx % 2 == 1)
        for cell in summary[r_idx]:
            cell.border = thin_border
            cell.font = font_bold if cell.column == 1 or (cell.column == 2 and r_idx == 5) else font_data
            cell.fill = zebra_odd if is_odd else zebra_even

            if cell.column == 2:
                if r_idx in [3, 4, 5, 6]:
                    cell.number_format = '"Bs" #,##0.00'
                    cell.alignment = Alignment(vertical="center", horizontal="right")
                    if r_idx == 5:
                        cell.fill = total_fill
                        cell.font = Font(name="Calibri", size=10, bold=True, color="FF8F6D2D")
                elif r_idx == 2:
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(vertical="center", horizontal="right")
                else:
                    cell.alignment = Alignment(vertical="center", horizontal="left")
            elif cell.column == 3:
                cell.alignment = Alignment(vertical="center", horizontal="center")
            else:
                cell.alignment = Alignment(vertical="center", horizontal="left")

    # --------------------------------------------------------------------------
    # BLOQUE CONSOLIDADO EN HOJA SUMMARY (A partir de fila 11)
    # --------------------------------------------------------------------------
    summary.cell(row=11, column=1, value="")
    summary.merge_cells("A12:D12")
    sec_title = summary["A12"]
    sec_title.value = "RESUMEN EJECUTIVO DE MÓDULOS Y OPERACIONES COMERCIALES (CICLO 3)"
    sec_title.fill = section_fill
    sec_title.font = section_font
    sec_title.alignment = Alignment(vertical="center", horizontal="left")
    summary.row_dimensions[12].height = 24

    summary.append(["Módulo / Área", "Total Registros", "Indicador Clave", "Estado Operativo"])
    summary.row_dimensions[13].height = 26
    for cell in summary[13]:
        cell.fill = PatternFill(fill_type="solid", start_color="FF333F48", end_color="FF333F48")
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFFFF")
        cell.alignment = Alignment(vertical="center", horizontal="left" if cell.column in [1, 4] else "center")
        cell.border = header_border

    tot_units_sold = sum(p.units_sold for p in snapshot.top_products) if snapshot.top_products else 0
    tot_reservations = sum(r.count for r in snapshot.reservations) if snapshot.reservations else 0
    critical_stock_cnt = sum(1 for item in snapshot.low_stock if item.available_quantity <= 2)

    overview_rows = [
        ["Productos Estrella (Top)", len(snapshot.top_products), f"{tot_units_sold} prendas vendidas", "Consulte la hoja 'Top Products' para el ranking completo"],
        ["Rendimiento por Sucursal", len(snapshot.sales_by_branch), f"{len(snapshot.sales_by_branch)} sucursales activas", "Consulte la hoja 'Branches' para facturación por sede"],
        ["Canales de Venta", len(snapshot.sales_by_channel), "Físico y Digital", "Consulte la hoja 'Channels' para distribución omnicanal"],
        ["Flujo de Reservas", len(snapshot.reservations), f"{tot_reservations} reservas registradas", "Consulte la hoja 'Reservations' para estados de entrega"],
        ["Alertas de Inventario", len(snapshot.low_stock), f"{critical_stock_cnt} ítems en nivel crítico", "Consulte la hoja 'Low Stock' para reposición inmediata"],
    ]

    for r_idx, row in enumerate(overview_rows, start=14):
        summary.append(row)
        summary.row_dimensions[r_idx].height = 22
        is_odd = (r_idx % 2 == 1)
        for cell in summary[r_idx]:
            cell.border = thin_border
            cell.font = font_bold if cell.column == 1 else font_data
            cell.fill = zebra_odd if is_odd else zebra_even
            if cell.column in [2, 3]:
                cell.alignment = Alignment(vertical="center", horizontal="center")
            else:
                cell.alignment = Alignment(vertical="center", horizontal="left")

    for col in summary.columns:
        col_letter = col[0].column_letter
        max_len = max(len(str(c.value or "")) for c in col[:10])
        summary.column_dimensions[col_letter].width = max(max_len + 6, 22)
    summary.column_dimensions["D"].width = 58

    # --------------------------------------------------------------------------
    # 2. HOJAS DE DATOS CONTRACTUALES DETALLADAS
    # --------------------------------------------------------------------------
    sheets_def = [
        (
            "Top Products",
            "FF1F4E78",
            ["ID Producto", "Producto / Prenda", "Unidades Vendidas", "Ingresos Netos (BOB)", "% Participación"],
            [
                [
                    item.product_id,
                    item.product_name,
                    item.units_sold,
                    _decimal(item.revenue),
                    f"=D{idx+2}/D${len(snapshot.top_products)+2}" if total_val > 0 else "0.0%",
                ]
                for idx, item in enumerate(snapshot.top_products)
            ],
            {"id_cols": ["A"], "text_cols": ["B"], "qty_cols": ["C"], "money_cols": ["D"], "pct_cols": ["E"]},
            {"total_label_col": "B", "sum_cols": ["C", "D"], "pct_col": "E"},
        ),
        (
            "Branches",
            "FF2F5597",
            ["ID Sucursal", "Sucursal", "Total Ventas (Órdenes)", "Facturación (BOB)", "% Participación"],
            [
                [
                    item.branch_id if item.branch_id is not None else 0,
                    item.branch_name,
                    item.sales_count,
                    _decimal(item.total),
                    f"=D{idx+2}/D${len(snapshot.sales_by_branch)+2}" if total_val > 0 else "0.0%",
                ]
                for idx, item in enumerate(snapshot.sales_by_branch)
            ],
            {"id_cols": ["A"], "text_cols": ["B"], "qty_cols": ["C"], "money_cols": ["D"], "pct_cols": ["E"]},
            {"total_label_col": "B", "sum_cols": ["C", "D"], "pct_col": "E"},
        ),
        (
            "Channels",
            "FF107C41",
            ["Canal de Venta", "Total Ventas (Órdenes)", "Facturación (BOB)", "% Participación"],
            [
                [
                    item.channel,
                    item.sales_count,
                    _decimal(item.total),
                    f"=C{idx+2}/C${len(snapshot.sales_by_channel)+2}" if total_val > 0 else "0.0%",
                ]
                for idx, item in enumerate(snapshot.sales_by_channel)
            ],
            {"id_cols": [], "text_cols": ["A"], "qty_cols": ["B"], "money_cols": ["C"], "pct_cols": ["D"]},
            {"total_label_col": "A", "sum_cols": ["B", "C"], "pct_col": "D"},
        ),
        (
            "Reservations",
            "FF7030A0",
            ["Estado de Reserva", "Cantidad de Reservas", "% Participación"],
            [
                [
                    item.status,
                    item.count,
                    f"=B{idx+2}/B${len(snapshot.reservations)+2}" if tot_reservations > 0 else "0.0%",
                ]
                for idx, item in enumerate(snapshot.reservations)
            ],
            {"id_cols": [], "text_cols": ["A"], "qty_cols": ["B"], "money_cols": [], "pct_cols": ["C"]},
            {"total_label_col": "A", "sum_cols": ["B"], "pct_col": "C"},
        ),
        (
            "Low Stock",
            "FFC00000",
            ["ID Inventario", "ID Sucursal", "Sucursal", "ID Producto", "Producto / Prenda", "Código SKU", "Stock Disponible", "Nivel de Alerta"],
            [
                [
                    item.inventory_id,
                    item.branch_id,
                    item.branch_name,
                    item.product_id,
                    item.product_name,
                    item.sku,
                    item.available_quantity,
                    "CRÍTICO (≤ 2)" if item.available_quantity <= 2 else ("BAJO (≤ 5)" if item.available_quantity <= 5 else "PREVENTIVO"),
                ]
                for item in snapshot.low_stock
            ],
            {"id_cols": ["A", "B", "D"], "text_cols": ["C", "E", "F", "H"], "qty_cols": ["G"], "money_cols": []},
            None,
        ),
    ]

    for title, tab_color, headers, rows, col_types, total_spec in sheets_def:
        sheet = workbook.create_sheet(title)
        sheet.sheet_properties.tabColor = tab_color
        sheet.views.sheetView[0].showGridLines = True
        sheet.freeze_panes = "A2"

        sheet.append(headers)
        sheet.row_dimensions[1].height = 28
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center", horizontal="center")
            cell.border = header_border

        for row_idx, row in enumerate(rows, start=2):
            sheet.append(row)
            sheet.row_dimensions[row_idx].height = 24
            is_odd = (row_idx % 2 == 1)
            row_cells = sheet[row_idx]
            for cell in row_cells:
                col_letter = cell.column_letter
                cell.font = font_data
                cell.border = thin_border
                cell.fill = zebra_odd if is_odd else zebra_even

                if col_letter in col_types.get("money_cols", []):
                    cell.number_format = '"Bs" #,##0.00'
                    cell.alignment = Alignment(vertical="center", horizontal="right")
                elif col_letter in col_types.get("qty_cols", []):
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(vertical="center", horizontal="right")
                    if title == "Low Stock" and isinstance(cell.value, (int, float)):
                        if cell.value <= 2:
                            cell.fill = PatternFill(fill_type="solid", start_color="FFFEE2E2", end_color="FFFEE2E2")
                            cell.font = Font(name="Calibri", size=10, bold=True, color="FF991B1B")
                        elif cell.value <= 5:
                            cell.fill = PatternFill(fill_type="solid", start_color="FFFEF3C7", end_color="FFFEF3C7")
                            cell.font = Font(name="Calibri", size=10, bold=True, color="FF92400E")
                elif col_letter in col_types.get("pct_cols", []):
                    cell.number_format = '0.0%'
                    cell.alignment = Alignment(vertical="center", horizontal="right")
                elif col_letter in col_types.get("id_cols", []):
                    cell.alignment = Alignment(vertical="center", horizontal="center")
                elif col_letter == "H" and title == "Low Stock":
                    cell.alignment = Alignment(vertical="center", horizontal="center")
                    if "CRÍTICO" in str(cell.value):
                        cell.fill = PatternFill(fill_type="solid", start_color="FFFEE2E2", end_color="FFFEE2E2")
                        cell.font = Font(name="Calibri", size=10, bold=True, color="FF991B1B")
                    elif "BAJO" in str(cell.value):
                        cell.fill = PatternFill(fill_type="solid", start_color="FFFEF3C7", end_color="FFFEF3C7")
                        cell.font = Font(name="Calibri", size=10, bold=True, color="FF92400E")
                else:
                    cell.alignment = Alignment(vertical="center", horizontal="left")

        # Fila de Totales Contables con fórmulas dinámicas
        if total_spec and rows:
            last_data_row = len(rows) + 1
            tot_row_idx = last_data_row + 1
            sheet.row_dimensions[tot_row_idx].height = 26

            label_col = total_spec.get("total_label_col", "A")
            sheet[f"{label_col}{tot_row_idx}"] = "TOTAL CONSOLIDADO"
            sheet[f"{label_col}{tot_row_idx}"].font = font_total
            sheet[f"{label_col}{tot_row_idx}"].alignment = Alignment(vertical="center", horizontal="left" if label_col != "A" else "center")

            for sum_col in total_spec.get("sum_cols", []):
                tot_cell = sheet[f"{sum_col}{tot_row_idx}"]
                tot_cell.value = f"=SUM({sum_col}2:{sum_col}{last_data_row})"
                tot_cell.font = font_total
                tot_cell.alignment = Alignment(vertical="center", horizontal="right")
                if sum_col in col_types.get("money_cols", []):
                    tot_cell.number_format = '"Bs" #,##0.00'
                else:
                    tot_cell.number_format = '#,##0'

            pct_col = total_spec.get("pct_col")
            if pct_col:
                pct_cell = sheet[f"{pct_col}{tot_row_idx}"]
                pct_cell.value = 1.0
                pct_cell.number_format = '100.0%'
                pct_cell.font = font_total
                pct_cell.alignment = Alignment(vertical="center", horizontal="right")

            for cell in sheet[tot_row_idx]:
                cell.fill = total_fill
                cell.border = total_border

        for col in sheet.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            col_letter = col[0].column_letter
            sheet.column_dimensions[col_letter].width = max(max_len + 6, 18)

    output = BytesIO()
    workbook.save(output)
    return _normalize_zip_timestamps(output.getvalue())


# ==============================================================================
# MOTOR PDF DE ALTA FIDELIDAD (REPORTLAB)
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self._doc._pdfVersion = (1, 4)

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#737373"))
        # Línea dorada superior al pie
        self.setStrokeColor(colors.HexColor("#B8924A"))
        self.setLineWidth(0.75)
        self.line(36, 34, 576, 34)
        self.drawString(36, 22, "FashionStore Atelier & Boutique · Documento de Control Confidencial")
        self.drawRightString(576, 22, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def build_pdf(snapshot: ReportSnapshot) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Tipografías y estilos boutique
    brand_title_style = ParagraphStyle(
        "BrandTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#FFFFFF"),
    )
    brand_sub_style = ParagraphStyle(
        "BrandSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#D4AF37"),
        spaceBefore=2,
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#F8F6F0"),
    )
    section_h_style = ParagraphStyle(
        "SectionH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#1B1C1A"),
        spaceBefore=8,
        spaceAfter=4,
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#D4AF37"),
        alignment=TA_LEFT,
    )
    th_right_style = ParagraphStyle(
        "THRight",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#D4AF37"),
        alignment=TA_RIGHT,
    )
    th_center_style = ParagraphStyle(
        "THCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#D4AF37"),
        alignment=TA_CENTER,
    )
    kpi_title_style = ParagraphStyle(
        "KpiTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#8F6D2D"),
        alignment=TA_CENTER,
    )
    kpi_val_style = ParagraphStyle(
        "KpiVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#1B1C1A"),
        alignment=TA_CENTER,
    )
    kpi_sub_style = ParagraphStyle(
        "KpiSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
    )
    cell_text_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1B1C1A"),
    )
    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1B1C1A"),
        alignment=TA_CENTER,
    )
    cell_right_style = ParagraphStyle(
        "CellRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1B1C1A"),
        alignment=TA_RIGHT,
    )
    cell_badge_crit = ParagraphStyle(
        "CellBadgeCrit",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#DC2626"),
        alignment=TA_CENTER,
    )
    cell_badge_opt = ParagraphStyle(
        "CellBadgeOpt",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#10B981"),
        alignment=TA_CENTER,
    )

    story = []

    # Cálculos ejecutivos
    total_rev = _decimal(snapshot.revenue.total)
    subtotal_rev = _decimal(snapshot.revenue.subtotal)
    discount_rev = _decimal(snapshot.revenue.discount)
    sales_count = snapshot.revenue.sales_count
    avg_ticket = (total_rev / sales_count) if sales_count > 0 else Decimal("0.00")
    discount_rate = (discount_rev / subtotal_rev * 100) if subtotal_rev > 0 else Decimal("0.0")
    net_margin = max(Decimal("0.0"), Decimal("100.0") - discount_rate)

    date_from_str = snapshot.filters.date_from.strftime("%d/%m/%Y") if snapshot.filters.date_from else "Todo el histórico"
    date_to_str = snapshot.filters.date_to.strftime("%d/%m/%Y") if snapshot.filters.date_to else "Fecha actual"
    branch_str = f"Sucursal #{snapshot.filters.branch_id}" if snapshot.filters.branch_id is not None else "Todas las sucursales"

    # 1. Cabecera Institucional
    header_left = [
        Paragraph("FASHIONSTORE ATELIER &amp; BOUTIQUE", brand_title_style),
        Paragraph("INFORME EJECUTIVO DE RENDIMIENTO COMERCIAL &middot; CICLO 3", brand_sub_style),
    ]
    header_right = [
        Paragraph(f"<b>PERIODO:</b> {date_from_str} &rarr; {date_to_str}", meta_val_style),
        Paragraph(f"<b>SUCURSAL:</b> {branch_str}", meta_val_style),
        Paragraph("<b>MONEDA:</b> Bolivianos (BOB)", meta_val_style),
        Paragraph(f"<b>EMISIÓN:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", meta_val_style),
    ]
    header_table = Table([[header_left, header_right]], colWidths=[330, 210])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1B1C1A")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 3, colors.HexColor("#B8924A")),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. Tarjetas KPI de Resumen
    kpi1 = [Paragraph("INGRESOS NETOS", kpi_title_style), Paragraph(f"Bs {total_rev:,.2f}", kpi_val_style), Paragraph(f"Subtotal: Bs {subtotal_rev:,.2f}", kpi_sub_style)]
    kpi2 = [Paragraph("TRANSACCIONES", kpi_title_style), Paragraph(str(sales_count), kpi_val_style), Paragraph(f"Ticket Prom: Bs {avg_ticket:,.2f}", kpi_sub_style)]
    kpi3 = [Paragraph("DESCUENTOS", kpi_title_style), Paragraph(f"Bs {discount_rev:,.2f}", kpi_val_style), Paragraph(f"Tasa Descto: {discount_rate:.1f}%", kpi_sub_style)]
    kpi4 = [Paragraph("MARGEN COMERCIAL", kpi_title_style), Paragraph(f"{net_margin:.1f}%", kpi_val_style), Paragraph("Margen neto sobre bruto", kpi_sub_style)]

    kpis_table = Table([[kpi1, kpi2, kpi3, kpi4]], colWidths=[135, 135, 135, 135])
    kpis_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF9F5")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E5DFD5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5DFD5")),
        ("LINEABOVE", (0, 0), (-1, -1), 2, colors.HexColor("#B8924A")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(kpis_table)
    story.append(Spacer(1, 10))

    # 3. Tabla: Top Productos Más Vendidos
    story.append(Paragraph("<b>PRODUCTOS MÁS VENDIDOS (TOP PRODUCTOS)</b>", section_h_style))
    prod_data = [
        [
            Paragraph("<b>#</b>", th_center_style),
            Paragraph("<b>PRENDA / ARTÍCULO</b>", th_style),
            Paragraph("<b>UNIDADES</b>", th_right_style),
            Paragraph("<b>TOTAL RECAUDADO</b>", th_right_style),
            Paragraph("<b>CUOTA</b>", th_right_style),
        ]
    ]
    for idx, item in enumerate(snapshot.top_products[:10], start=1):
        share_pct = (Decimal(str(item.revenue)) / total_rev * 100) if total_rev > 0 else Decimal("0.0")
        badge = f"{idx} 🏆" if idx == 1 else str(idx)
        prod_data.append([
            Paragraph(badge, cell_bold_style),
            Paragraph(item.product_name, cell_text_style),
            Paragraph(str(item.units_sold), cell_right_style),
            Paragraph(f"Bs {_decimal(item.revenue):,.2f}", cell_right_style),
            Paragraph(f"{share_pct:.1f}%", cell_right_style),
        ])

    if len(prod_data) == 1:
        prod_data.append([Paragraph("-", cell_bold_style), Paragraph("Sin ventas registradas en el período", cell_text_style), Paragraph("-", cell_right_style), Paragraph("-", cell_right_style), Paragraph("-", cell_right_style)])

    t_prod = Table(prod_data, colWidths=[35, 245, 75, 115, 70])
    t_prod.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B1C1A")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#FBF9F5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5DFD5")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#B8924A")),
    ]))
    story.append(t_prod)
    story.append(Spacer(1, 10))

    # 4. Tabla: Ventas por Sucursal
    story.append(Paragraph("<b>VENTAS POR SUCURSAL</b>", section_h_style))
    branch_data = [
        [
            Paragraph("<b>SUCURSAL</b>", th_style),
            Paragraph("<b>TRANSACCIONES</b>", th_right_style),
            Paragraph("<b>TOTAL FACTURADO</b>", th_right_style),
            Paragraph("<b>PARTICIPACIÓN</b>", th_right_style),
        ]
    ]
    for item in snapshot.sales_by_branch:
        share_pct = (Decimal(str(item.total)) / total_rev * 100) if total_rev > 0 else Decimal("0.0")
        branch_data.append([
            Paragraph(item.branch_name, cell_text_style),
            Paragraph(f"{item.sales_count} ventas", cell_right_style),
            Paragraph(f"Bs {_decimal(item.total):,.2f}", cell_right_style),
            Paragraph(f"{share_pct:.1f}%", cell_right_style),
        ])
    if len(branch_data) == 1:
        branch_data.append([Paragraph("Sin sucursales registradas", cell_text_style), Paragraph("-", cell_right_style), Paragraph("-", cell_right_style), Paragraph("-", cell_right_style)])

    t_branch = Table(branch_data, colWidths=[200, 100, 130, 110])
    t_branch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B1C1A")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#FBF9F5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5DFD5")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#B8924A")),
    ]))
    story.append(t_branch)
    story.append(Spacer(1, 10))

    # 5. Tabla: Canales de Venta & Reservas
    story.append(Paragraph("<b>OMNICANALIDAD &amp; ESTADO DE RESERVAS</b>", section_h_style))
    channel_data = [
        [
            Paragraph("<b>CANAL DE VENTA</b>", th_style),
            Paragraph("<b>OPERACIONES</b>", th_right_style),
            Paragraph("<b>FACTURACIÓN</b>", th_right_style),
            Paragraph("<b>CUOTA</b>", th_right_style),
        ]
    ]
    for item in snapshot.sales_by_channel:
        share_pct = (Decimal(str(item.total)) / total_rev * 100) if total_rev > 0 else Decimal("0.0")
        channel_data.append([
            Paragraph(f"Canal {item.channel}", cell_text_style),
            Paragraph(f"{item.sales_count} ventas", cell_right_style),
            Paragraph(f"Bs {_decimal(item.total):,.2f}", cell_right_style),
            Paragraph(f"{share_pct:.1f}%", cell_right_style),
        ])
    if len(channel_data) == 1:
        channel_data.append([Paragraph("Sin canales registrados", cell_text_style), Paragraph("-", cell_right_style), Paragraph("-", cell_right_style), Paragraph("-", cell_right_style)])

    t_channel = Table(channel_data, colWidths=[200, 100, 130, 110])
    t_channel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B1C1A")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#FBF9F5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5DFD5")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#B8924A")),
    ]))
    story.append(t_channel)
    story.append(Spacer(1, 10))

    # 6. Alertas de Stock Crítico (si existen)
    if snapshot.low_stock:
        story.append(Paragraph("<b>ALERTAS DE INVENTARIO CRÍTICO (&le; 2 UNIDADES)</b>", section_h_style))
        stock_data = [
            [
                Paragraph("<b>PRENDA / ARTÍCULO</b>", th_style),
                Paragraph("<b>SKU</b>", th_style),
                Paragraph("<b>SUCURSAL</b>", th_style),
                Paragraph("<b>STOCK</b>", th_right_style),
                Paragraph("<b>ESTADO</b>", th_center_style),
            ]
        ]
        for item in snapshot.low_stock[:12]:
            badge_style = cell_badge_crit if item.available_quantity <= 2 else cell_badge_opt
            status_text = "CRÍTICO" if item.available_quantity <= 2 else "BAJO"
            stock_data.append([
                Paragraph(item.product_name, cell_text_style),
                Paragraph(item.sku, cell_text_style),
                Paragraph(item.branch_name, cell_text_style),
                Paragraph(f"{item.available_quantity} unid.", cell_right_style),
                Paragraph(status_text, badge_style),
            ])

        t_stock = Table(stock_data, colWidths=[170, 100, 140, 60, 70])
        t_stock.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B1C1A")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#FBF9F5")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5DFD5")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#B8924A")),
        ]))
        story.append(t_stock)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


# ==============================================================================
# MOTOR POWERPOINT PPTX (COMPATIBILIDAD INTERNA)
# ==============================================================================

def _slide_text(title: str, lines: list[str]) -> str:
    escaped_title = html.escape(title)
    body = "".join(f"<a:p><a:r><a:t>{html.escape(line)}</a:t></a:r></a:p>" for line in lines)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr><p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="457200" y="274320"/><a:ext cx="8229600" cy="731520"/></a:xfrm></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="3200" b="1"/><a:t>{escaped_title}</a:t></a:r></a:p></p:txBody></p:sp><p:sp><p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="457200" y="1188720"/><a:ext cx="8229600" cy="5029200"/></a:xfrm></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""


def _zip_write(zip_file: ZipFile, name: str, data: str | bytes) -> None:
    info = ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    zip_file.writestr(info, data)


def _build_pptx_with_python_pptx(snapshot: ReportSnapshot) -> bytes:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[0])
    slide.shapes.title.text = "FashionStore report summary"
    slide.placeholders[1].text = "\n".join(
        [
            f"Sales: {snapshot.revenue.sales_count}",
            f"Total: {_money(snapshot.revenue.total)}",
            f"Discount: {_money(snapshot.revenue.discount)}",
            f"Branch: {snapshot.filters.branch_id if snapshot.filters.branch_id is not None else 'All'}",
        ]
    )

    branch_slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    branch_slide.shapes.title.text = "Sales by branch"
    maximum = max((_decimal(item.total) for item in snapshot.sales_by_branch), default=Decimal("1")) or Decimal("1")
    y = Inches(1.2)
    for item in snapshot.sales_by_branch[:8]:
        label = branch_slide.shapes.add_textbox(Inches(0.6), y, Inches(2.4), Inches(0.25))
        label.text_frame.text = item.branch_name
        bar_width = float((_decimal(item.total) / maximum) * Decimal("4.5"))
        bar = branch_slide.shapes.add_shape(1, Inches(3.1), y, Inches(bar_width), Inches(0.22))
        bar.fill.solid()
        bar.fill.fore_color.rgb = RGBColor(31, 78, 121)
        value = branch_slide.shapes.add_textbox(Inches(7.7), y, Inches(1.6), Inches(0.25))
        value.text_frame.text = _money(item.total)
        y += Inches(0.42)

    products_slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    products_slide.shapes.title.text = "Top products"
    rows = max(len(snapshot.top_products[:8]) + 1, 2)
    table_shape = products_slide.shapes.add_table(rows, 3, Inches(0.5), Inches(1.2), Inches(9), Inches(0.35 * rows))
    table = table_shape.table
    for index, header in enumerate(["Product", "Units", "Revenue"]):
        cell = table.cell(0, index)
        cell.text = header
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(12)
    for row_index, item in enumerate(snapshot.top_products[:8], start=1):
        table.cell(row_index, 0).text = item.product_name
        table.cell(row_index, 1).text = str(item.units_sold)
        table.cell(row_index, 2).text = _money(item.revenue)

    output = BytesIO()
    presentation.save(output)
    return _normalize_zip_timestamps(output.getvalue())


def build_pptx(snapshot: ReportSnapshot) -> bytes:
    try:
        return _build_pptx_with_python_pptx(snapshot)
    except ImportError:
        pass

    summary_lines = [
        f"Sales: {snapshot.revenue.sales_count}",
        f"Total: {_money(snapshot.revenue.total)}",
        f"Discount: {_money(snapshot.revenue.discount)}",
        f"Branch: {snapshot.filters.branch_id if snapshot.filters.branch_id is not None else 'All'}",
    ]
    branch_lines = [f"{item.branch_name}: {_money(item.total)} ({item.sales_count} sales)" for item in snapshot.sales_by_branch[:8]] or ["No branch sales"]
    product_lines = [f"{item.product_name}: {item.units_sold} units / {_money(item.revenue)}" for item in snapshot.top_products[:8]] or ["No product sales"]

    output = BytesIO()
    with ZipFile(output, "w") as package:
        _zip_write(package, "[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/><Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/><Override PartName="/ppt/slides/slide3.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>""")
        _zip_write(package, "_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>""")
        _zip_write(package, "ppt/presentation.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldSz cx="9144000" cy="6858000" type="screen4x3"/><p:sldIdLst><p:sldId id="256" r:id="rId1"/><p:sldId id="257" r:id="rId2"/><p:sldId id="258" r:id="rId3"/></p:sldIdLst></p:presentation>""")
        _zip_write(package, "ppt/_rels/presentation.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml recovery"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide3.xml"/></Relationships>""")
        _zip_write(package, "ppt/slides/slide1.xml", _slide_text("FashionStore report summary", summary_lines))
        _zip_write(package, "ppt/slides/slide2.xml", _slide_text("Sales by branch", branch_lines))
        _zip_write(package, "ppt/slides/slide3.xml", _slide_text("Top products", product_lines))
    return output.getvalue()
