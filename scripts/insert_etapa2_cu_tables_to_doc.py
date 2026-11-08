# -*- coding: utf-8 -*-
"""
Script para generar e insertar los cuadros de especificación y diagramas de los 7 Casos de Uso
de la Etapa 2 en 'docsegundoparcialSI2.docx'.
"""

import os
import tempfile
import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.enum.text import WD_ALIGN_PARAGRAPH
import win32com.client

DOC_PATH = r"C:\ProyectoSi2_TiendaRopa\docsegundoparcialSI2.docx"
EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

ETAPA2_CU_DATA = [
    {
        "code": "CU-08",
        "diagram_id": 438,
        "heading": "CU-08: Registrar Venta de Contado Offline",
        "nombre": "CU-08: Registrar Venta de Contado Offline",
        "descripcion": "Permitir al Cajero/Vendedor procesar y registrar una venta asistida en el punto de venta (POS) en efectivo sin conexión a Internet, validando la disponibilidad de stock local en IndexedDB/SQLite, emitiendo el comprobante de venta local y encolando la operación en el Outbox para su posterior sincronización transaccional con el servidor.",
        "actores": "Cajero / Vendedor.",
        "precondiciones": "La aplicación web (PWA) o móvil debe tener una sesión iniciada con credenciales cacheadas y disponer del catálogo local y existencias descargadas en la sucursal asignada.",
        "flujo_normal": "1. El Cajero/Vendedor escanea el código de barras o busca las variantes de prendas seleccionadas por el cliente.\n2. El sistema consulta el saldo de existencias en la base de datos local y agrega las líneas al carrito de venta.\n3. El cajero ingresa el monto en efectivo entregado por el cliente.\n4. El sistema calcula el cambio, valida que el efectivo cubra el total de la orden y genera un identificador único universal (UUID v4) para la venta offline.\n5. El sistema descuenta el stock disponible local en la sucursal y persiste los registros de cabecera de venta, detalle y pago en la base de datos local.\n6. El sistema encola la transacción en la tabla local de operaciones pendientes (Outbox) con estado PENDIENTE.\n7. El sistema genera el comprobante digital/ticket de venta local y notifica al cajero la finalización exitosa.",
        "flujo_alternativo": "2.a. Stock local insuficiente: El sistema alerta que no hay disponibilidad física registrada en la tienda y bloquea el añadido de la prenda.\n4.a. Monto en efectivo insuficiente: El sistema solicita ingresar un monto igual o superior al total de la compra.",
        "poscondiciones": "Venta registrada localmente con pago en efectivo, stock local descontado, orden encolada en el Outbox para sincronización futura y ticket emitido."
    },
    {
        "code": "CU-09",
        "diagram_id": 439,
        "heading": "CU-09: Registrar Reserva de Prendas Offline",
        "nombre": "CU-09: Registrar Reserva de Prendas Offline",
        "descripcion": "Registrar el apartado temporal de una o varias prendas en la tienda física en modo fuera de línea, bloqueando temporalmente el saldo disponible en el inventario local por un plazo de 48 horas y registrando la operación en la cola de sincronización.",
        "actores": "Cajero / Vendedor, Cliente.",
        "precondiciones": "La tienda física debe contar con el catálogo cargado localmente y existir stock disponible de las prendas solicitadas.",
        "flujo_normal": "1. El cliente solicita apartar una prenda indicando sus datos de contacto (NIT/CI, nombre y teléfono).\n2. El cajero selecciona la prenda y la variante específica en la interfaz POS offline.\n3. El sistema valida que el stock disponible local sea mayor o igual a la cantidad solicitada.\n4. El cajero confirma la reserva fijando un plazo de validez de 48 horas.\n5. El sistema genera un código de reserva único offline (UUID v4), incrementa el stock_reservado local y descuenta el stock_disponible.\n6. El sistema almacena la reserva y sus detalles en el almacenamiento local y encola la acción en la tabla Outbox.\n7. El sistema emite la constancia de reserva local con la fecha y hora límite de retiro.",
        "flujo_alternativo": "3.a. Prenda sin stock disponible: El sistema informa que no hay unidades libres para reservar en la sucursal y cancela la operación.",
        "poscondiciones": "Reserva creada en estado PENDIENTE localmente, inventario local reservado y comprobante entregado al cliente."
    },
    {
        "code": "CU-10",
        "diagram_id": 440,
        "heading": "CU-10: Consultar Operaciones Locales Pendientes (Outbox)",
        "nombre": "CU-10: Consultar Operaciones Locales Pendientes (Outbox)",
        "descripcion": "Visualizar el listado y estado de todas las transacciones generadas en modo fuera de línea (ventas, reservas, cambios y altas de clientes) almacenadas en la cola de salida local (Outbox) del dispositivo, permitiendo supervisar qué operaciones esperan ser sincronizadas con el servidor.",
        "actores": "Cajero / Vendedor.",
        "precondiciones": "Dispositivo con aplicación POS o móvil en ejecución y base de datos local accesible.",
        "flujo_normal": "1. El cajero accede a la sección de 'Bandeja de Operaciones Locales / Outbox' en el panel de control o menú lateral.\n2. El sistema consulta la tabla local de operaciones (SyncOperation) filtrando por el identificador de la sucursal y dispositivo.\n3. El sistema muestra la lista clasificada por tipo de operación, código de referencia local, marca temporal y estado (PENDIENTE, EN_PROCESO, ERROR).\n4. El usuario puede seleccionar una operación específica para ver el desglose del payload y su monto.\n5. El sistema presenta el resumen consolidado de transacciones pendientes acumuladas.",
        "flujo_alternativo": "3.a. Outbox vacío: El sistema notifica que todas las transacciones locales se encuentran al día y sincronizadas con la nube.",
        "poscondiciones": "El usuario conoce el volumen y detalle exacto de transacciones pendientes de consolidación en el servidor."
    },
    {
        "code": "CU-11",
        "diagram_id": 441,
        "heading": "CU-11: Sincronizar Operaciones con el Servidor",
        "nombre": "CU-11: Sincronizar Operaciones con el Servidor",
        "descripcion": "Transmitir en lotes las operaciones pendientes del Outbox hacia la API central una vez detectado el restablecimiento de la conexión a Internet o mediante acción manual del cajero, asegurando idempotencia transaccional y conciliación central de inventario.",
        "actores": "Cajero / Vendedor, Actores de Sistema (Motor de Sincronización).",
        "precondiciones": "Existencia de conectividad a Internet validada y sesión autenticada con token JWT vigente.",
        "flujo_normal": "1. El motor de sincronización detecta conexión en línea o el usuario presiona 'Sincronizar Ahora'.\n2. El sistema extrae las operaciones pendientes del Outbox ordenadas cronológicamente (FIFO) en lotes de hasta 50 registros.\n3. El sistema marca las operaciones locales con estado EN_PROCESO.\n4. El cliente envía el lote vía solicitud POST autenticada al endpoint /api/sync/operations/batch del backend.\n5. El servidor procesa cada operación dentro de una transacción atómica verificando la clave de idempotencia (client_operation_id).\n6. El servidor actualiza las tablas centrales (ventas, pagos, inventario, kardex), audita el evento en bitácora y responde con el resultado de cada ítem.\n7. El cliente recibe la respuesta del servidor, marca las operaciones como SINCRONIZADAS en el Outbox y purga o archiva los ítems confirmados.",
        "flujo_alternativo": "4.a. Pérdida súbita de conectividad durante el envío: La transacción aborta en el cliente, las operaciones retornan al estado PENDIENTE y se reprograma un reintento con backoff exponencial.\n6.a. Error transaccional en servidor: Se marca la operación con estado ERROR y se deriva a gestión de conflictos (CU-12).",
        "poscondiciones": "Operaciones locales consolidadas en la base de datos central multi-tenant, inventario central actualizado y Outbox local actualizado."
    },
    {
        "code": "CU-12",
        "diagram_id": 442,
        "heading": "CU-12: Gestionar Conflictos de Sincronización",
        "nombre": "CU-12: Gestionar Conflictos de Sincronización",
        "descripcion": "Detectar, clasificar y resolver discrepancias entre transacciones comerciales originadas fuera de línea y el estado actual de los datos en el servidor (p. ej. venta offline de una prenda cuyo stock físico central fue consumido concurrentemente en otro canal), aplicando la política no destructiva establecida (RN06).",
        "actores": "Tenant Admin, Cajero / Vendedor.",
        "precondiciones": "El motor de sincronización ha identificado una colisión al procesar un lote de transacciones del Outbox.",
        "flujo_normal": "1. Durante la sincronización en el backend, el validador de concurrencia detecta una discrepancia de stock o estado.\n2. El servidor registra la colisión en la tabla de operaciones marcando el estado como CONFLICTO y preserva la auditoría del payload original.\n3. El sistema aplica la política de resolución predeterminada: la venta offline se respeta como válida financieramente, se genera un ajuste de inventario negativo o se desvía el déficit a cuarentena para reposición prioritaria.\n4. El sistema notifica al Tenant Admin y al cajero en el panel de incidencias con los detalles de la discordancia.\n5. El administrador confirma la acción correctiva (reposición de stock, transferencia entre sucursales o compensación).\n6. El sistema cierra el conflicto, actualiza el estado a RESUELTO y deja constancia en la bitácora.",
        "flujo_alternativo": "5.a. Solicitud de anulación administrativa: El Tenant Admin rechaza la operación offline y emite una nota de crédito o reembolso al cliente.",
        "poscondiciones": "Conflicto resuelto sin pérdida de integridad financiera, kardex ajustado y trazabilidad completa del evento."
    },
    {
        "code": "CU-13",
        "diagram_id": 443,
        "heading": "CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)",
        "nombre": "CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)",
        "descripcion": "Procesar en el punto de venta asistido la solicitud de cambio de una o varias prendas adquiridas previamente por el cliente, verificando que la compra original no supere los 30 días calendario (RN07), ingresando la prenda retornada al área de cuarentena para inspección técnica y entregando la nueva prenda con el balance monetario correspondiente.",
        "actores": "Cajero / Vendedor.",
        "precondiciones": "El cliente debe presentar el comprobante de venta original o código de orden emitido dentro de los últimos 30 días, y la tienda debe tener stock disponible de la nueva variante seleccionada.",
        "flujo_normal": "1. El cliente se presenta en la tienda solicitando cambio de talla, color o modelo de una prenda.\n2. El cajero ingresa el código de orden o escanea el comprobante de venta original.\n3. El sistema verifica que la venta exista, esté en estado PAGADA y que la fecha de compra no exceda los 30 días calendario.\n4. El cajero selecciona las prendas a devolver y especifica las nuevas prendas que el cliente desea llevarse.\n5. El sistema calcula la diferencia monetaria: valor de prendas entregadas versus valor reconocido de prendas devueltas.\n6. Si existe diferencia a favor de la tienda, el cajero registra el cobro de la diferencia en efectivo; si el saldo es a favor del cliente, se emite reembolso o saldo a favor.\n7. El cajero confirma la operación ingresando la clave de idempotencia única.\n8. El sistema persiste el registro de cambio en garment_exchanges y garment_exchange_items, crea el registro en inventory_quarantine para la prenda devuelta, descuenta el stock de la nueva prenda entregada y genera el comprobante de cambio.",
        "flujo_alternativo": "3.a. Plazo vencido (> 30 días): El sistema bloquea el cambio informando que la garantía de 30 días ha expirado según la regla RN07.\n5.a. Nueva variante sin stock: El sistema alerta que la talla o color deseado no tiene inventario disponible y ofrece variantes alternativas.",
        "poscondiciones": "Prenda devuelta aislada en cuarentena para inspección, nueva prenda descontada del inventario físico, registro de cambio auditado y comprobante entregado al cliente."
    },
    {
        "code": "CU-22",
        "diagram_id": 444,
        "heading": "CU-22: Gestionar Datos Mínimos de Clientes Offline",
        "nombre": "CU-22: Gestionar Datos Mínimos de Clientes Offline",
        "descripcion": "Permitir al Cajero/Vendedor capturar y registrar en la base de datos local los datos esenciales de un cliente nuevo (NIT/CI, razón social/nombre, teléfono y correo electrónico) en condiciones de desconexión, facilitando la emisión inmediata de tickets y su posterior vinculación y enriquecimiento en el servidor.",
        "actores": "Cajero / Vendedor.",
        "precondiciones": "Aplicación POS o PWA en ejecución con almacenamiento local habilitado.",
        "flujo_normal": "1. El cajero atiende a un cliente que no figura en la caché local durante una venta o reserva offline.\n2. El cajero selecciona 'Nuevo Cliente Rápido' en el formulario de facturación o registro.\n3. El cajero ingresa los datos mínimos requeridos: NIT o Cédula de Identidad, Nombre/Razón Social y Teléfono.\n4. El sistema valida el formato de los datos y confirma que el documento no esté duplicado en la caché local.\n5. El sistema persiste el cliente en la tabla local clientes asignando un identificador local y 0 puntos de fidelidad iniciales.\n6. El sistema encola la acción de alta de cliente en la tabla de operaciones pendientes (Outbox) con tipo CLIENTE_OFFLINE.\n7. El sistema asocia inmediatamente el nuevo cliente a la transacción en curso y notifica al cajero.",
        "flujo_alternativo": "4.a. Documento ya registrado en caché: El sistema carga automáticamente los datos existentes del cliente para evitar duplicados locales.",
        "poscondiciones": "Cliente registrado en la base de datos local, disponible para la venta/reserva actual y encolado en el Outbox para su sincronización con la nube."
    }
]

def export_diagram_images():
    print("Exportando imágenes de diagramas de Casos de Uso desde EA...")
    rep = win32com.client.Dispatch("EA.Repository")
    rep.OpenFile(EAP_PATH)
    proj = rep.GetProjectInterface()

    temp_dir = tempfile.mkdtemp(prefix="ea_uc_imgs_")
    exported_paths = {}

    for spec in ETAPA2_CU_DATA:
        diag = rep.GetDiagramByID(spec["diagram_id"])
        out_path = os.path.join(temp_dir, f"{spec['code']}.png")
        proj.PutDiagramImageToFile(diag.DiagramGUID, out_path, 1)
        exported_paths[spec["code"]] = out_path
        print(f"  {spec['code']} -> {out_path}")

    rep.CloseFile()
    rep.Exit()
    return temp_dir, exported_paths

def insert_tables_into_doc(exported_paths):
    print("Abriendo documento Word:", DOC_PATH)
    doc = docx.Document(DOC_PATH)

    # Buscar el índice del párrafo 'Capítulo 3: Análisis y diseño con ICONIX'
    cap3_idx = None
    for i, p in enumerate(doc.paragraphs):
        if "Capítulo 3" in p.text or "Captulo 3" in p.text:
            cap3_idx = i
            break

    if cap3_idx is None:
        raise RuntimeError("No se encontró el párrafo 'Capítulo 3'")

    target_p = doc.paragraphs[cap3_idx]
    print(f"Punto de inserción encontrado antes de párrafo {cap3_idx}: '{target_p.text}'")

    for spec in ETAPA2_CU_DATA:
        code = spec["code"]
        img_path = exported_paths[code]
        print(f"Insertando cuadro de especificación para: {spec['heading']}")

        # 1. Párrafo de título del Caso de Uso
        p_head = doc.add_paragraph(spec["heading"])
        p_head.style = doc.styles["Normal"]
        p_head.paragraph_format.space_before = docx.shared.Pt(14)
        p_head.paragraph_format.space_after = docx.shared.Pt(4)
        p_head.paragraph_format.keep_with_next = True
        run_h = p_head.runs[0]
        run_h.bold = True
        run_h.font.size = docx.shared.Pt(11)

        # Mover antes de target_p
        target_p._element.addprevious(p_head._element)

        # 2. Crear tabla de especificación (10 filas, 2 columnas)
        table = doc.add_table(rows=10, cols=2)
        tblPr = table._element.xpath('w:tblPr')[0]
        borders = parse_xml(r'''
            <w:tblBorders %s>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:left w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:right w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:insideH w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:insideV w:val="single" w:sz="6" w:space="0" w:color="000000"/>
            </w:tblBorders>
        ''' % nsdecls('w'))
        tblPr.append(borders)
        jc = parse_xml(r'<w:jc %s w:val="center"/>' % nsdecls('w'))
        tblPr.append(jc)

        # Fila 0: Diagrama de Caso de Uso (celda combinada)
        r0 = table.rows[0]
        c0 = r0.cells[0].merge(r0.cells[1])
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = docx.shared.Pt(4)
        p0.paragraph_format.space_after = docx.shared.Pt(4)
        run0 = p0.add_run()
        run0.add_picture(img_path, width=docx.shared.Inches(4.3))

        # Fila 1: Nombre
        r1 = table.rows[1]
        p1_0 = r1.cells[0].paragraphs[0]
        p1_0.paragraph_format.space_after = docx.shared.Pt(2)
        r_lbl1 = p1_0.add_run("Nombre:")
        r_lbl1.bold = True
        r_lbl1.font.size = docx.shared.Pt(9.5)
        r1.cells[0].width = 1433830

        p1_1 = r1.cells[1].paragraphs[0]
        p1_1.paragraph_format.space_after = docx.shared.Pt(2)
        r_txt1 = p1_1.add_run(spec["nombre"])
        r_txt1.font.size = docx.shared.Pt(9.5)
        r1.cells[1].width = 3956050

        # Fila 2: Autor
        r2 = table.rows[2]
        p2_0 = r2.cells[0].paragraphs[0]
        p2_0.paragraph_format.space_after = docx.shared.Pt(2)
        r_lbl2 = p2_0.add_run("Autor:")
        r_lbl2.bold = True
        r_lbl2.font.size = docx.shared.Pt(9.5)
        r2.cells[0].width = 1433830

        p2_1 = r2.cells[1].paragraphs[0]
        p2_1.paragraph_format.space_after = docx.shared.Pt(2)
        r_txt2 = p2_1.add_run("Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia")
        r_txt2.font.size = docx.shared.Pt(9.5)
        r2.cells[1].width = 3956050

        # Fila 3: Fecha
        r3 = table.rows[3]
        p3_0 = r3.cells[0].paragraphs[0]
        p3_0.paragraph_format.space_after = docx.shared.Pt(2)
        r_lbl3 = p3_0.add_run("Fecha:")
        r_lbl3.bold = True
        r_lbl3.font.size = docx.shared.Pt(9.5)
        r3.cells[0].width = 1433830

        p3_1 = r3.cells[1].paragraphs[0]
        p3_1.paragraph_format.space_after = docx.shared.Pt(2)
        r_txt3 = p3_1.add_run("24/10/2026")
        r_txt3.font.size = docx.shared.Pt(9.5)
        r3.cells[1].width = 3956050

        # Filas 4 a 9: Celdas combinadas
        sections = [
            (4, "Descripción: ", spec["descripcion"]),
            (5, "Actores: ", spec["actores"]),
            (6, "Precondiciones: ", spec["precondiciones"]),
            (7, "Flujo Normal:\n", spec["flujo_normal"]),
            (8, "Flujo Alternativo:\n", spec["flujo_alternativo"]),
            (9, "Poscondiciones: ", spec["poscondiciones"]),
        ]

        for row_idx, label, text in sections:
            row = table.rows[row_idx]
            cell = row.cells[0].merge(row.cells[1])
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = docx.shared.Pt(2)
            p.paragraph_format.line_spacing = 1.15
            run_lbl = p.add_run(label)
            run_lbl.bold = True
            run_lbl.font.size = docx.shared.Pt(9.5)
            run_txt = p.add_run(text)
            run_txt.bold = False
            run_txt.font.size = docx.shared.Pt(9.5)

        # Mover la tabla antes de target_p
        target_p._element.addprevious(table._element)

        # Párrafo de separación
        p_sep = doc.add_paragraph("")
        p_sep.paragraph_format.space_before = docx.shared.Pt(0)
        p_sep.paragraph_format.space_after = docx.shared.Pt(8)
        target_p._element.addprevious(p_sep._element)

    print("Guardando documento:", DOC_PATH)
    doc.save(DOC_PATH)
    print("Documento guardado exitosamente!")

def main():
    temp_dir, exported_paths = export_diagram_images()
    try:
        insert_tables_into_doc(exported_paths)
    finally:
        # Limpiar directorio temporal
        for f in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, f))
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass

    print("=" * 70)
    print("¡CUADROS DE ESPECIFICACIÓN Y DIAGRAMAS DE LA ETAPA 2 INSERTADOS AL 100%!")
    print("=" * 70)

if __name__ == '__main__':
    main()
