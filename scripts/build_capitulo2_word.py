# -*- coding: utf-8 -*-
"""
Script to append Chapter 2 (Análisis de Requisitos) to docsegundoparcialSI2.docx
Following all user instructions and academic guidelines for Sistemas 2.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="000000", sz="4", val="single"):
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            </w:tblBorders>
        ''')
        tblPr[0].append(borders)

def append_capitulo2():
    doc = docx.Document('docsegundoparcialSI2.docx')

    # Color palette
    NAVY_BLUE = RGBColor(27, 54, 93)      # #1B365D - Heading 1 & Titles
    SLATE_BLUE = RGBColor(44, 82, 130)    # #2C5282 - Heading 2
    ACCENT_BLUE = RGBColor(43, 108, 176)  # #2B6CB0 - Heading 3 & Subtitles
    DARK_TEXT = RGBColor(34, 34, 34)      # #222222 - Body text
    MUTED_GRAY = RGBColor(74, 85, 104)    # #4A5568 - Captions

    # Helper formatting functions
    def add_chapter_title(text):
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(18)
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(16)
        run.font.color.rgb = NAVY_BLUE
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(13)
        run.font.color.rgb = NAVY_BLUE
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(12)
        run.font.color.rgb = SLATE_BLUE
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(11)
        run.font.color.rgb = ACCENT_BLUE
        return p

    def add_body_p(text, bold_prefix=None, space_after=6):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(space_after)
        if bold_prefix:
            run_b = p.add_run(bold_prefix)
            run_b.bold = True
            run_b.font.name = "Arial"
            run_b.font.size = Pt(11)
            run_b.font.color.rgb = DARK_TEXT
        run_t = p.add_run(text)
        run_t.font.name = "Arial"
        run_t.font.size = Pt(11)
        run_t.font.color.rgb = DARK_TEXT
        return p

    def add_bullet_item(bold_prefix, text, space_after=4):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(space_after)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        run_bullet = p.add_run("•  ")
        run_bullet.bold = True
        run_bullet.font.name = "Arial"
        run_bullet.font.size = Pt(11)
        run_bullet.font.color.rgb = ACCENT_BLUE

        if bold_prefix:
            run_b = p.add_run(bold_prefix)
            run_b.bold = True
            run_b.font.name = "Arial"
            run_b.font.size = Pt(11)
            run_b.font.color.rgb = DARK_TEXT

        run_t = p.add_run(text)
        run_t.font.name = "Arial"
        run_t.font.size = Pt(11)
        run_t.font.color.rgb = DARK_TEXT
        return p

    # =========================================================================
    # CAPÍTULO II. ANÁLISIS DE REQUISITOS
    # =========================================================================
    add_chapter_title("CAPÍTULO II. ANÁLISIS DE REQUISITOS")

    # -------------------------------------------------------------------------
    # 2.1. DESCRIPCIÓN DEL SISTEMA PROPUESTO
    # -------------------------------------------------------------------------
    add_h1("2.1. DESCRIPCIÓN DEL SISTEMA PROPUESTO")

    p21_1 = (
        "La plataforma propuesta, denominada FashionStore SaaS, representa un ecosistema tecnológico integral "
        "de comercio electrónico y gestión empresarial en la nube, diseñado específicamente para la comercialización "
        "minorista de prendas de vestir bajo un modelo de Software como Servicio (SaaS) Multi-tenant. La solución "
        "permite que múltiples empresas y marcas de moda independientes operen de forma concurrente, autónoma y segura "
        "sobre una arquitectura compartida en backend con aislamiento lógico absoluto de información mediante el "
        "discriminador tenant_id en PostgreSQL, eliminando la necesidad de desplegar costosas instancias de software "
        "dedicadas para cada cliente."
    )
    add_body_p(p21_1)

    p21_2 = (
        "El sistema se fundamenta en un paradigma arquitectónico desacoplado y orientado a la resiliencia operativa "
        "Offline-First. El núcleo de servicios backend está implementado con el framework asíncrono Python FastAPI, "
        "exponiendo interfaces REST seguras, tipadas y de alto rendimiento. En el nivel de clientes, la plataforma "
        "ofrece dos canales de interacción complementarios: una aplicación web desarrollada en Angular evolucionada a "
        "Progressive Web App (PWA) con almacenamiento local relacional en IndexedDB, y una aplicación móvil nativa "
        "multiplataforma en Flutter (Android/iOS) respaldada por una base de datos relacional embebida SQLite. Ambas "
        "aplicaciones garantizan que los operadores de sucursal puedan continuar consultando el catálogo, registrando "
        "ventas de contado y apartando reservas de prendas aun cuando se interrumpa la conectividad a Internet. Mediante "
        "el patrón arquitectónico Outbox e identificadores universales (UUID v4), las operaciones fuera de línea se "
        "sincronizan por lotes al restablecerse la red, aplicando políticas de idempotencia estricta, descuento atómico "
        "de stock y detección de conflictos por insuficiencia de existencias (INSUFFICIENT_STOCK)."
    )
    add_body_p(p21_2)

    p21_3 = (
        "Adicionalmente, el sistema integra capacidades de vanguardia en Inteligencia Artificial Generativa y Analítica "
        "Predictiva mediante Machine Learning. Los directivos y encargados de tienda pueden formular consultas complejas en "
        "lenguaje natural mediante texto o comandos de voz, obteniendo diagnósticos ejecutivos, visualizaciones gráficas "
        "interactivas y reportes oficiales exportables en formatos PDF y Excel (.xlsx). De forma complementaria, los modelos "
        "de Machine Learning supervisados (proyección de ventas y demanda con Ridge Regression) y no supervisados (clusterización "
        "RFM con K-Means) permiten anticipar tendencias de aprovisionamiento y segmentar la cartera de compradores, todo "
        "gobernado bajo los límites y permisos del plan de suscripción contratado (Básico o Profesional)."
    )
    add_body_p(p21_3)

    # -------------------------------------------------------------------------
    # 2.2. IDENTIFICACIÓN DE ACTORES
    # -------------------------------------------------------------------------
    add_h1("2.2. IDENTIFICACIÓN DE ACTORES")

    add_body_p(
        "El análisis del sistema identifica ocho actores clave (seis roles humanos internos y externos, y dos sistemas "
        "externos complementarios) que interactúan con las diversas fronteras funcionales de FashionStore SaaS:"
    )

    actores_list = [
        ("Superadministrador de Plataforma (SaaS Admin): ",
         "Actor interno responsable de la administración global de la infraestructura multitenant. Gestiona el registro "
         "de empresas clientes (tenants), asigna y fiscaliza los planes de suscripción (Básico y Profesional), monitorea "
         "las métricas de salud del sistema, audita eventos de plataforma y configura parámetros generales del servicio."),

        ("Administrador de Empresa (Tenant Admin): ",
         "Máxima autoridad de gestión dentro del entorno lógico de una empresa suscripta. Administra los usuarios y roles "
         "de su compañía, configura sucursales físicas dentro del cupo contratado, gestiona el catálogo de prendas, temporadas, "
         "proveedores, promociones comerciales y consulta reportes analíticos de IA y modelos de Machine Learning."),

        ("Encargado de Sucursal (Branch Manager): ",
         "Responsable de la supervisión logística y operativa de un establecimiento comercial específico. Monitorea las "
         "existencias locales en Kardex, recibe transferencias de mercadería, aprueba reposiciones de prendas, atiende y "
         "despacha reservas presenciales y supervisa a los cajeros del punto de venta."),

        ("Cajero / Vendedor (POS Operator): ",
         "Operador de la terminal de punto de venta físico (POS en Web PWA o Móvil). Registra ventas presenciales al "
         "contado y electrónicas, procesa cobros en caja (efectivo, tarjeta, transferencias QR), atiende cambios de prendas "
         "dentro de la ventana de 30 días y opera en modo fuera de línea cuando se interrumpe la red, gestionando la "
         "bandeja de transacciones pendientes de sincronización."),

        ("Cliente (Comprador Final): ",
         "Usuario final que accede a través del portal e-commerce web o la app móvil. Explora el catálogo de colecciones "
         "con filtros avanzados, consulta la disponibilidad de tallas y colores en sucursales físicas, utiliza el vestidor "
         "virtual asistido por realidad aumentada, gestiona su carrito de compras, realiza pedidos digitales o aparta "
         "prendas para probarse en tienda física."),

        ("Proveedor de Indumentaria (Supplier): ",
         "Actor comercial externo que provee prendas terminadas o insumos textiles a una empresa. Accede al portal de "
         "proveedores para consultar órdenes de compra adjudicadas, registrar ofertas de abastecimiento y dar seguimiento "
         "a sus entregas comerciales."),

        ("Pasarela de Pagos (Sistema Externo - Payment Gateway): ",
         "Entidad externa encargada de validar, procesar y conciliar transacciones monetarias electrónicas en línea "
         "(tarjetas de crédito/débito y pasarelas de pago interoperables mediante códigos QR) para ventas digitales y reservas."),

        ("Motor de Inteligencia Artificial (Sistema Externo - LLM / Generative AI): ",
         "Servicio cognitivo avanzado (API de modelos de lenguaje natural LLM y bibliotecas de ciencia de datos) que "
         "procesa solicitudes en lenguaje natural formuladas por texto o voz, infiere intenciones analíticas, clasifica "
         "perfiles RFM y genera proyecciones de demanda de indumentaria acotadas estrictamente a los datos del tenant.")
    ]

    for bold_p, text_p in actores_list:
        add_bullet_item(bold_p, text_p)

    # -------------------------------------------------------------------------
    # 2.3. REQUISITOS FUNCIONALES Y NO FUNCIONALES
    # -------------------------------------------------------------------------
    add_h1("2.3. REQUISITOS FUNCIONALES Y NO FUNCIONALES")

    add_h2("2.3.1. Requisitos Funcionales (RF)")
    add_body_p(
        "Los requisitos funcionales describen los servicios, comportamientos y transformaciones de datos que el sistema "
        "debe ejecutar obligatoriamente para satisfacer las demandas del negocio:"
    )

    rf_list = [
        ("RF01 - Gestión de Empresas y Suscripciones SaaS: ",
         "El sistema debe permitir el alta, parametrización y gestión de empresas clientes (tenants), asociándoles un plan "
         "de suscripción (Básico o Profesional) con cuotas de sucursales y vigencia temporal claramente definidas."),

        ("RF02 - Autenticación y Autorización Multi-tenant (RBAC): ",
         "El sistema debe autenticar usuarios mediante correo y contraseña encriptada (bcrypt), emitiendo tokens JWT con "
         "discriminador tenant_id y roles asignados, restringiendo el acceso exclusivamente a los datos de la propia empresa."),

        ("RF03 - Gestión de Sucursales y Geografía: ",
         "El sistema debe permitir administrar sucursales físicas asociadas a ciudades, validando que el número de tiendas "
         "activas no exceda el límite permitido por la suscripción (hasta 2 en Básico, hasta 10 en Profesional)."),

        ("RF04 - Gestión de Catálogo Maestro y Variantes de Prendas: ",
         "El sistema debe permitir crear y clasificar prendas de vestir por categoría, temporada y colección, generando "
         "automáticamente combinatorias de variantes (talla, color) con códigos SKU universales y galería multimedia."),

        ("RF05 - Gestión de Proveedores y Ofertas de Abastecimiento: ",
         "El sistema debe registrar información comercial de proveedores mayoristas y capturar ofertas de suministro "
         "asociadas a variantes de prendas y colecciones."),

        ("RF06 - Control Centralizado de Inventario y Kardex Multitienda: ",
         "El sistema debe mantener el saldo de existencias en tiempo real por variante y sucursal, registrando de forma "
         "inmutable cada entrada, salida, traslado o merma en un Kardex histórico con alertas de stock crítico."),

        ("RF07 - Punto de Venta Presencial (POS): ",
         "El sistema debe proveer una interfaz de venta asistida rápida para cajeros en tienda física, permitiendo lectura "
         "de códigos de barra, selección de tallas/colores, cálculo de impuestos, aplicación de promociones y emisión de tickets."),

        ("RF08 - Comercio Electrónico Web y Carrito de Compras: ",
         "El sistema debe permitir a los clientes explorar el catálogo digital, verificar existencias en línea, añadir "
         "artículos a su carrito de compras y tramitar órdenes de compra con entrega a domicilio o retiro en tienda."),

        ("RF09 - Gestión de Reservas de Prendas: ",
         "El sistema debe permitir apartar prendas físicas tanto desde el portal digital como en mostrador, bloqueando "
         "temporalmente el stock en la sucursal seleccionada con expiración automática si no se concreta la compra."),

        ("RF10 - Procesamiento de Pagos y Facturación: ",
         "El sistema debe admitir múltiples formas de pago: efectivo al contado, transferencias QR interoperables y "
         "simulación de cobro electrónico con tarjeta de crédito/débito, generando el comprobante fiscal correlativo."),

        ("RF11 - Gestión de Cambios de Prendas Posventa: ",
         "El sistema debe validar solicitudes de cambio de prendas dentro de un plazo comercial límite de 30 días, reintegrando "
         "el artículo devuelto al inventario (RETURN) y despachando la nueva prenda elegida (SALE) de forma atómica."),

        ("RF12 - Operación Fuera de Línea (Offline-First): ",
         "Tanto la aplicación Angular PWA (vía IndexedDB) como la aplicación móvil Flutter (vía SQLite) deben permitir la "
         "consulta del catálogo almacenado localmente y el registro desconectado de ventas de contado y reservas de prendas."),

        ("RF13 - Sincronización Transaccional Resiliente y Manejo de Conflictos: ",
         "El sistema debe recibir lotes de operaciones originadas fuera de línea con identificadores UUID v4, garantizando "
         "idempotencia estricta, descuento atómico en base central y detección de sobreventas (INSUFFICIENT_STOCK) sin abortar el lote."),

        ("RF14 - Inteligencia Artificial Generativa para Reportes (Texto y Voz): ",
         "El sistema debe interpretar consultas gerenciales en lenguaje natural por teclado o micrófono, extraer filtros "
         "dinámicos, ejecutar consultas SQL seguras en el tenant y generar gráficos interactivos, narrativas y reportes en PDF y Excel."),

        ("RF15 - Analítica Predictiva y Modelado de Datos (Machine Learning): ",
         "El sistema debe incorporar modelos supervisados (Ridge Regression) para estimar la demanda futura y modelos no "
         "supervisados (K-Means RFM) para segmentar clientes, visualizados a través de un dashboard analítico gerencial."),

        ("RF16 - Probador Virtual Interactivo con Realidad Aumentada: ",
         "El sistema debe permitir al usuario probar prendas virtualmente sobre su imagen en tiempo real detectando la "
         "pose de los hombros en dispositivos móviles con cámara, o mediante un simulador visual en navegadores web.")
    ]

    for bold_p, text_p in rf_list:
        add_bullet_item(bold_p, text_p)

    add_h2("2.3.2. Requisitos No Funcionales (RNF)")
    add_body_p(
        "Los requisitos no funcionales definen los atributos de calidad, rendimiento, restricciones de seguridad y "
        "principios arquitectónicos que rigen el comportamiento técnico del sistema:"
    )

    rnf_list = [
        ("RNF01 - Seguridad y Cifrado: ",
         "Todas las comunicaciones entre clientes y servidores deben cifrarse mediante HTTPS/TLS. Las contraseñas se deben "
         "hashear con bcrypt y las peticiones a la API deben autenticarse mediante tokens JWT criptográficamente firmados."),

        ("RNF02 - Aislamiento Lógico de Datos Multi-tenant: ",
         "Ningún usuario o proceso de una empresa debe tener acceso a datos pertenecientes a otro tenant. Dicho aislamiento "
         "debe aplicarse obligatoriamente en la capa de persistencia y servicios de FastAPI, no solo en la interfaz gráfica."),

        ("RNF03 - Persistencia Local Duradera Offline: ",
         "Las transacciones registradas sin conexión deben almacenarse de forma persistente en IndexedDB (Web) y SQLite (Móvil), "
         "garantizando que sobrevivan al cierre, reinicio o apagado inesperado del navegador o terminal móvil."),

        ("RNF04 - Integridad Transaccional y Consistencia de Inventario: ",
         "Las ventas y reservas confirmadas centralmente deben respetar propiedades ACID. Los movimientos de inventario deben "
         "ejecutarse bajo bloqueos pesimistas o niveles de aislamiento que impidan la inconsistencia de existencias."),

        ("RNF05 - Idempotencia en Sincronización: ",
         "El reenvío múltiple de una misma transacción originada fuera de línea (mismo client_operation_id) debe ser inocuo, "
         "retornando el resultado previamente confirmado sin duplicar cobros ni descontar inventario doble."),

        ("RNF06 - Recuperación ante Fallos y Resiliencia de Red: ",
         "Ante fallas de conexión o caídas intermitentes durante la sincronización, las operaciones locales pendientes nunca "
         "deben borrarse ni alterarse; permanecerán en la bandeja outbox para reintento automático."),

        ("RNF07 - Mantenibilidad y Arquitectura Modular: ",
         "El código fuente debe organizarse bajo una arquitectura limpia y modularizada por dominios de negocio, separando "
         "estrictamente responsabilidades de presentación, lógica de dominio, persistencia y sincronización."),

        ("RNF08 - Compatibilidad Multiplataforma: ",
         "La Progressive Web App debe funcionar en navegadores modernos que soporten Service Workers e IndexedDB (Chrome, "
         "Edge, Firefox, Safari). La aplicación Flutter debe compilar y operar de forma fluida en Android e iOS."),

        ("RNF09 - Rendimiento y Tiempos de Respuesta: ",
         "Las consultas al catálogo y procesamiento de ventas en línea deben responder en tiempos inferiores a 500 ms en "
         "condiciones de red normales. Las inferencias analíticas de IA no deben exceder 3.5 segundos."),

        ("RNF10 - Observabilidad y Auditoría: ",
         "El sistema debe registrar trazas y logs estructurados de cada intento de sincronización transaccional, errores de "
         "red y conflictos de stock en una bitácora inmutable por empresa sin exponer datos confidenciales."),

        ("RNF11 - Calidad y Verificación Automatizada (TDD): ",
         "El desarrollo debe gobernarse bajo la disciplina Test-Driven Development (TDD), disponiendo de una suite integral "
         "de pruebas unitarias, de integración y de reglas críticas de negocio en backend (pytest), web (npm test) y móvil (flutter test)."),

        ("RNF12 - Coherencia Documental y Modelado Formal UML: ",
         "Todos los modelos de dominio, diagramas de robustez (BCE), diagramas de secuencia y de clases elaborados bajo "
         "ICONIX deben representar con absoluta fidelidad el código fuente implementado.")
    ]

    for bold_p, text_p in rnf_list:
        add_bullet_item(bold_p, text_p)

    # -------------------------------------------------------------------------
    # 2.4. REGLAS DE NEGOCIO
    # -------------------------------------------------------------------------
    add_h1("2.4. REGLAS DE NEGOCIO")

    add_body_p(
        "Las reglas de negocio establecen las directrices, políticas comerciales e invariantes operativas que gobiernan "
        "la lógica del dominio en FashionStore SaaS:"
    )

    rn_list = [
        ("RN01 - Aislamiento Estricto por Tenant: ",
         "Toda entidad de negocio (usuarios, sucursales, productos, inventarios, ventas, reservas, bitácora) debe asociarse "
         "a un tenant_id. Queda terminantemente prohibido acceder, consultar o modificar datos entre empresas distintas."),

        ("RN02 - Restricción de Recursos por Nivel de Suscripción: ",
         "Una empresa en Plan Básico puede registrar y mantener hasta 2 sucursales activas y no tiene acceso a reportes "
         "generativos de IA ni analítica predictiva. Una empresa en Plan Profesional puede activar hasta 10 sucursales y dispone "
         "de acceso irrestricto al motor de IA generativa y módulos de Machine Learning."),

        ("RN03 - Unicidad de Códigos Comerciales dentro del Tenant: ",
         "Los códigos de producto, slugs web y SKUs de variantes deben ser únicos dentro del ámbito de la empresa propietaria, "
         "permitiéndose que dos empresas distintas utilicen coincidentemente el mismo código interno sin colisión."),

        ("RN04 - Exclusividad de Pago en Efectivo para Ventas Fuera de Línea: ",
         "Las operaciones comerciales de venta registradas sin conexión a Internet admiten exclusivamente la modalidad de "
         "pago al contado en efectivo; los pagos electrónicos requieren validación en línea de la pasarela."),

        ("RN05 - Idempotencia Transaccional Basada en UUID v4: ",
         "Cada transacción comercial originada fuera de línea debe generar un UUID v4 inmutable (client_operation_id). El "
         "backend garantiza que una operación ya procesada devuelva su estado previo sin ejecutar modificaciones duplicadas."),

        ("RN06 - Tratamiento No Destructivo de Conflictos de Inventario: ",
         "Si durante la sincronización de una venta fuera de línea se detecta que el inventario central es insuficiente "
         "(INSUFFICIENT_STOCK), la operación se etiqueta como CONFLICT y se conserva intacta en la base central y local "
         "para resolución administrativa, sin abortar las restantes operaciones válidas del lote."),

        ("RN07 - Plazo Límite de 30 Días para Cambios de Prendas: ",
         "Los cambios de prendas devueltas por clientes solo se autorizan dentro de un plazo máximo de 30 días calendario "
         "posteriores a la fecha de la venta original, previa verificación del comprobante y estado de la prenda."),

        ("RN08 - Bloqueo Temporal de Stock en Reservas: ",
         "Al registrarse una reserva de prenda (física o digital), la cantidad correspondiente se bloquea temporalmente "
         "en el inventario de la sucursal (reserved_quantity), impidiendo su venta a terceros por un plazo de 48 horas."),

        ("RN09 - Restricción de Solo Lectura para el Motor de IA Generativa: ",
         "El motor de Inteligencia Artificial solo puede ejecutar consultas de solo lectura (SELECT) parametrizadas y "
         "validadas por el backend, teniendo vedada cualquier instrucción de modificación estructural (DDL) o mutación de datos (DML)."),

        ("RN10 - Inmutabilidad del Registro de Kardex y Auditoría: ",
         "Los registros de movimientos de inventario y entradas de bitácora no pueden ser editados ni eliminados por ningún "
         "rol de usuario, garantizando la trazabilidad histórica y no repudiación legal de las operaciones.")
    ]

    for bold_p, text_p in rn_list:
        add_bullet_item(bold_p, text_p)

    # -------------------------------------------------------------------------
    # 2.5. DIAGRAMA UML DE CASOS DE USO Y MATRIZ INTEGRAL DE CASOS DE USO
    # -------------------------------------------------------------------------
    add_h1("2.5. DIAGRAMA UML DE CASOS DE USO")

    add_body_p(
        "El modelado funcional de FashionStore SaaS mediante casos de uso articula los requerimientos del sistema en cinco "
        "paquetes arquitectónicos que agrupan los 32 casos de uso que componen la plataforma completa: 1) Paquete de Seguridad, "
        "Acceso y Plataforma SaaS; 2) Paquete de Catálogo Maestro, Proveedores y Ubicaciones; 3) Paquete de Operación Comercial, "
        "POS e Inventarios; 4) Paquete de Resiliencia Offline y Sincronización Transaccional; y 5) Paquete de Analítica "
        "Inteligente, IA Generativa y Experiencia de Usuario."
    )

    add_body_p(
        "En cumplimiento de las directrices metodológicas, a continuación se presenta la matriz integral que consolida "
        "la totalidad de los casos de uso del sistema, especificando en columnas dedicadas: el nombre y código del caso de uso, "
        "los actores involucrados en su ejecución, y la plataforma o canal tecnológico en el cual se encuentra disponible "
        "(Web, Móvil, o Ambos):"
    )

    # Table 2.5: All 32 use cases, actors, platform (Web/Móvil/Web y Móvil)
    use_cases_data = [
        # Ciclo 1: Catálogo y Base
        ("CU01: Registrar Cliente", "Cliente", "Web y Móvil"),
        ("CU02: Autenticación (Iniciar / Cerrar Sesión)", "Cliente, Cajero, Encargado, Administrador, Superadmin", "Web y Móvil"),
        ("CU03: Gestionar Usuarios y Asignación de Roles", "Administrador de Tenant, Superadministrador", "Web"),
        ("CU04: Gestionar Sucursales y Ciudades", "Administrador de Tenant", "Web"),
        ("CU05: Gestionar Productos y Variantes de Ropa", "Administrador de Tenant, Encargado de Sucursal", "Web"),
        ("CU06: Gestionar Catálogo Base (Categorías, Tallas y Colores)", "Administrador de Tenant", "Web"),
        ("CU07: Gestionar Proveedores de Indumentaria", "Administrador de Tenant, Proveedor", "Web"),
        ("CU08: Consultar Catálogo y Buscar Prendas con Filtros", "Cliente, Cajero, Encargado de Sucursal", "Web y Móvil"),
        ("CU09: Consultar Disponibilidad de Existencias por Tienda", "Cliente, Vendedor de Sucursal", "Web y Móvil"),
        # Ciclo 2: Operación Comercial y Logística
        ("CU10: Realizar Reserva de Prendas", "Cliente, Vendedor de Sucursal", "Web y Móvil"),
        ("CU11: Atender y Despachar Reservas en Sucursal", "Encargado de Sucursal, Cajero", "Web y Móvil"),
        ("CU12: Sesión de Probador Virtual y Realidad Aumentada", "Cliente", "Web y Móvil (AR en Móvil, Simulador en Web)"),
        ("CU13: Gestionar Carrito de Compras E-commerce", "Cliente", "Web y Móvil"),
        ("CU14: Realizar Compra Digital (E-commerce Checkout)", "Cliente", "Web y Móvil"),
        ("CU15: Realizar Venta Presencial en Punto de Venta (POS)", "Cajero / Vendedor", "Web (PWA) y Móvil"),
        ("CU16: Cobrar en Caja (Efectivo / Tarjeta / Transferencia QR)", "Cajero", "Web (PWA) y Móvil"),
        ("CU17: Procesar Pago Electrónico con Pasarela", "Pasarela de Pagos (Sistema Externo), Cliente", "Web y Móvil"),
        ("CU18: Gestionar Inventario, Movimientos y Kardex", "Encargado de Sucursal, Administrador de Tenant", "Web"),
        ("CU19: Gestionar Temporadas y Colecciones de Moda", "Administrador de Tenant", "Web"),
        # Ciclo 3: Analítica, Experiencia y Marketing
        ("CU20: Gestionar Campañas de Promoción y Descuentos", "Administrador de Tenant", "Web"),
        ("CU21: Consultar Dashboards y Reportes Gerenciales con IA", "Administrador de Tenant, Motor de IA", "Web y Móvil"),
        ("CU22: Obtener Recomendaciones Personalizadas con IA", "Cliente, Motor de IA", "Web y Móvil"),
        ("CU23: Consultar Historial de Compras y Comprobantes", "Cliente", "Web y Móvil"),
        # Segundo Parcial: SaaS, Resiliencia Offline, ML y Cambios
        ("CU24: Registrar Empresa y Plan SaaS Multi-tenant", "Superadministrador de Plataforma", "Web"),
        ("CU25: Gestionar Suscripciones y Límites de Empresa", "Superadministrador de Plataforma, Administrador", "Web"),
        ("CU26: Sincronizar y Consultar Catálogo Offline", "Cajero / Vendedor, Cliente", "Web (IndexedDB) y Móvil (SQLite)"),
        ("CU27: Sincronización Transaccional en Lote y Conflictos", "Cajero / Vendedor (Sistema Central)", "Web (PWA) y Móvil"),
        ("CU28: Bandeja de Operaciones Offline y Auditoría Sync", "Cajero, Encargado de Sucursal", "Web (PWA) y Móvil"),
        ("CU29: Gestión de Cambios de Prendas (Ventana de 30 Días)", "Cajero, Cliente", "Web (PWA) y Móvil"),
        ("CU30: Proyección Supervisada de Demanda (Machine Learning)", "Administrador de Tenant", "Web"),
        ("CU31: Segmentación No Supervisada de Clientes (K-Means RFM)", "Administrador de Tenant", "Web"),
        ("CU32: Exportación Dinámica de Reportes (Excel y PDF)", "Administrador de Tenant", "Web y Móvil")
    ]

    table_p25 = doc.add_table(rows=len(use_cases_data) + 1, cols=3)
    table_p25.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_p25, color="4A5568", sz="4", val="single")

    # Header row
    headers_25 = ["Caso de Uso (Código y Nombre)", "Actores Involucrados", "Plataforma / Canal"]
    widths_25 = [Inches(2.7), Inches(2.3), Inches(1.5)]

    hdr_cells_25 = table_p25.rows[0].cells
    for i, h_text in enumerate(headers_25):
        hdr_cells_25[i].text = ""
        set_cell_background(hdr_cells_25[i], "1B365D")
        set_cell_margins(hdr_cells_25[i], top=120, bottom=120, left=140, right=140)
        hdr_cells_25[i].width = widths_25[i]
        p = hdr_cells_25[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Data rows
    for row_idx, (cu_name, cu_actors, cu_platform) in enumerate(use_cases_data, start=1):
        row_cells = table_p25.rows[row_idx].cells
        bg_col = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"

        for col_idx, (val, width) in enumerate(zip([cu_name, cu_actors, cu_platform], widths_25)):
            row_cells[col_idx].text = ""
            set_cell_background(row_cells[col_idx], bg_col)
            set_cell_margins(row_cells[col_idx], top=80, bottom=80, left=120, right=120)
            row_cells[col_idx].width = width
            p = row_cells[col_idx].paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(2)

            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(val)
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(9.5)
                run.font.color.rgb = DARK_TEXT
            elif col_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(val)
                run.font.name = "Arial"
                run.font.size = Pt(9)
                run.font.color.rgb = DARK_TEXT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(val)
                run.font.name = "Arial"
                run.font.size = Pt(9)
                if "Web y Móvil" in val or "Ambos" in val:
                    run.bold = True
                    run.font.color.rgb = ACCENT_BLUE
                else:
                    run.font.color.rgb = DARK_TEXT

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(8)

    # -------------------------------------------------------------------------
    # 2.6. ESPECIFICACIÓN DE CASOS DE USO (9 Fichas de la Primera Fase: CU01 - CU09)
    # -------------------------------------------------------------------------
    add_h1("2.6. ESPECIFICACIÓN DE CASOS DE USO")

    intro_p26_1 = (
        "A partir de cada caso de uso se obtienen sus correspondientes fichas de caso de uso. Cabe destacar "
        "que estas fichas no pertenecen formalmente al estándar UML, sino que constituyen una técnica estructurada "
        "de ingeniería de software orientada a documentar de forma precisa, intuitiva y rigurosa la interacción del usuario "
        "con el sistema, describiendo precondiciones, secuencias de pasos normales, flujos alternativos o excepciones y "
        "poscondiciones garantizadas."
    )
    add_body_p(intro_p26_1)

    intro_p26_2 = (
        "En estricto apego al estándar metodológico solicitado para el proyecto y al formato de especificación "
        "estructurada, a continuación se detallan las fichas completas de los 9 casos de uso fundamentales que "
        "componen la primera fase del sistema (Ciclo 1: Catálogo y Base de Plataforma):"
    )
    add_body_p(intro_p26_2)

    # Data for the 9 use cases matching the uploaded image format
    fichas_data = [
        # CU01
        {
            "nombre": "CU01: Registrar Cliente",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite a un nuevo usuario cliente darse de alta en la plataforma de comercio electrónico proporcionando sus datos personales y credenciales de acceso, asignándole automáticamente el rol de Cliente dentro del tenant.",
            "actores": "Cliente.",
            "precondiciones": "El usuario no debe tener una cuenta registrada previamente con el mismo correo electrónico en la empresa (tenant).",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción de registro desde la interfaz web o móvil.",
                "2. El sistema muestra el formulario de registro solicitando nombre completo, correo electrónico, teléfono y contraseña.",
                "3. El actor introduce los datos requeridos y pulsa sobre el botón 'Registrarse'.",
                "4. El sistema comprueba la validez del formato de correo y la longitud requerida de la contraseña.",
                "5. El sistema comprueba que el correo electrónico no esté registrado previamente en el tenant.",
                "6. El sistema cifra la contraseña mediante algoritmo bcrypt, crea el registro de usuario con rol CLIENT vinculado al tenant_id y almacena los datos.",
                "7. El sistema genera los tokens de sesión (JWT) y notifica al actor que su registro fue exitoso, redirigiéndolo a la pantalla principal."
            ],
            "flujo_alternativo": [
                "4.a. El sistema comprueba la validez de los datos, si los datos no son correctos o faltan campos obligatorios, se avisa al actor de ello permitiéndole que los corrija.",
                "5.a. El sistema comprueba que el correo electrónico ya existe registrado en la empresa; el sistema notifica al actor que la cuenta ya existe y sugiere iniciar sesión o recuperar su contraseña."
            ],
            "poscondiciones": "La cuenta del cliente queda almacenada en el sistema con rol CLIENT y se inicia automáticamente una sesión autenticada."
        },
        # CU02
        {
            "nombre": "CU02: Autenticación de Usuario (Iniciar / Cerrar Sesión)",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite a los usuarios registrados (Clientes, Cajeros, Encargados, Administradores) ingresar al sistema mediante sus credenciales para acceder a las operaciones autorizadas, así como cerrar su sesión de forma segura revocando sus tokens.",
            "actores": "Cliente, Cajero, Encargado de Sucursal, Administrador de Tenant, Superadministrador de Plataforma.",
            "precondiciones": "El usuario debe poseer una cuenta activa y registrada en el sistema.",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción de inicio de sesión e introduce su correo electrónico y contraseña.",
                "2. El actor pulsa sobre el botón 'Iniciar Sesión'.",
                "3. El sistema valida las credenciales contrastando el hash bcrypt almacenado en la base de datos.",
                "4. El sistema comprueba que el usuario se encuentre activo, identifica su rol, permisos y el tenant_id al que pertenece.",
                "5. El sistema genera los tokens criptográficos de sesión (Access Token y Refresh Token).",
                "6. El sistema redirige al actor al panel o catálogo correspondiente a su perfil de usuario.",
                "7. (Cierre de Sesión): Cuando el actor pulsa 'Cerrar Sesión', el sistema envía el Refresh Token, revoca la sesión activa en el servidor y purga el almacenamiento local de credenciales."
            ],
            "flujo_alternativo": [
                "3.a. El sistema comprueba la validez de las credenciales; si el correo o contraseña son incorrectos, se avisa al actor indicando 'Credenciales inválidas' permitiéndole reintentar sin revelar la existencia del correo.",
                "4.a. El sistema detecta que la cuenta del usuario se encuentra inactiva o suspendida; se notifica al actor denegando el acceso y sugiriendo contactar al administrador.",
                "7.a. El token de refresco enviado al cerrar sesión ya está revocado o es inválido; el sistema elimina el token local del cliente de todas formas."
            ],
            "poscondiciones": "El usuario dispone de una sesión autenticada con acceso limitado a su tenant; al cerrar sesión, los tokens quedan invalidados en el sistema."
        },
        # CU03
        {
            "nombre": "CU03: Gestionar Usuarios y Asignación de Roles",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al Administrador registrar nuevos colaboradores para su empresa, consultar la lista de usuarios, actualizar datos, asignar roles operativos (Cajero, Encargado, Administrador), asociar sucursales y suspender cuentas.",
            "actores": "Administrador de Tenant, Superadministrador de Plataforma.",
            "precondiciones": "El administrador debe haberse autenticado y poseer permisos de administración de usuarios en el tenant.",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción 'Gestión de Usuarios' en el panel administrativo.",
                "2. El sistema recupera y muestra la lista tabular de los usuarios pertenecientes al tenant con sus roles, sucursales asignadas y estado.",
                "3. El actor pulsa sobre el botón 'Nuevo Usuario'.",
                "4. El sistema muestra un formulario solicitando nombre completo, correo, teléfono, rol funcional y sucursales autorizadas.",
                "5. El actor introduce los datos del colaborador y pulsa sobre el botón 'Guardar'.",
                "6. El sistema comprueba que el correo no esté duplicado en el tenant, almacena el nuevo usuario con su rol y membresías de sucursal, y actualiza la lista."
            ],
            "flujo_alternativo": [
                "3.a. El actor selecciona un usuario existente y pulsa sobre 'Editar': el sistema carga los datos actuales, el actor modifica roles o sucursales y confirma la actualización.",
                "5.a. El actor intenta suspender su propia cuenta de usuario o revocar su propio rol de administrador; el sistema comprueba la identidad y avisa al actor de que no está permitido auto-desactivarse.",
                "6.a. El sistema comprueba los datos introducidos; si el correo ya existe o faltan campos requeridos, se avisa al actor permitiéndole corregir la información."
            ],
            "poscondiciones": "El usuario queda registrado o modificado en el tenant con sus roles y sucursales debidamente asignados y auditados."
        },
        # CU04
        {
            "nombre": "CU04: Gestionar Sucursales y Ciudades",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al Administrador registrar, actualizar y consultar las sucursales físicas de su empresa, asociándolas a ciudades geográficas y verificando el cumplimiento de la cuota de sucursales permitida por su plan SaaS.",
            "actores": "Administrador de Tenant.",
            "precondiciones": "El administrador debe estar autenticado y la empresa debe contar con una suscripción SaaS activa.",
            "flujo_normal": [
                "1. El actor pulsa sobre el módulo 'Sucursales y Ubicaciones'.",
                "2. El sistema muestra el listado de sucursales de la empresa, su dirección, ciudad y estado, junto al contador de sucursales activas frente al límite del plan.",
                "3. El actor pulsa sobre el botón 'Registrar Sucursal'.",
                "4. El sistema comprueba que el número de sucursales activas no supere el cupo contratado en el plan SaaS (ej. 2 en Básico, 10 en Profesional).",
                "5. El sistema muestra el formulario solicitando ciudad geográfica, nombre de la sucursal, dirección, teléfono y encargado.",
                "6. El actor introduce la información y pulsa sobre 'Crear Sucursal'.",
                "7. El sistema comprueba los datos, almacena la nueva sucursal vinculada al tenant_id y actualiza la vista."
            ],
            "flujo_alternativo": [
                "4.a. El sistema comprueba que la empresa alcanzó el límite máximo de sucursales permitido por su suscripción; el sistema avisa al actor indicando que debe actualizar al Plan Profesional para habilitar más sucursales.",
                "6.a. Ya existe una sucursal con el mismo nombre y ciudad en la empresa; el sistema avisa al actor de la duplicidad permitiéndole modificar el nombre."
            ],
            "poscondiciones": "La sucursal física queda registrada en el sistema y habilitada para recibir asignaciones de personal, inventario y ventas."
        },
        # CU05
        {
            "nombre": "CU05: Gestionar Productos y Variantes de Ropa",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite crear, modificar y catalogar prendas de vestir de la empresa, definiendo sus atributos descriptivos, precios de lista, categoría, temporada, colección y generando la matriz de variantes por talla y color con códigos SKU únicos.",
            "actores": "Administrador de Tenant, Encargado de Sucursal.",
            "precondiciones": "El actor debe tener permisos de gestión de catálogo; deben existir categorías, tallas y colores previamente registrados.",
            "flujo_normal": [
                "1. El actor pulsa sobre el módulo 'Productos' en el panel de administración.",
                "2. El sistema muestra la tabla de prendas de la empresa con filtros por categoría y estado.",
                "3. El actor pulsa sobre el botón 'Agregar Producto'.",
                "4. El sistema muestra el formulario para capturar nombre de la prenda, código base, descripción, categoría, temporada, colección y precio de venta.",
                "5. El actor introduce los datos y selecciona las combinaciones de tallas y colores que corresponden a las variantes de la prenda.",
                "6. El sistema genera automáticamente los códigos SKU únicos para cada variante seleccionada.",
                "7. El actor carga las fotografías de la prenda y pulsa sobre 'Guardar Producto'.",
                "8. El sistema comprueba la validez de los datos, almacena el producto con sus variantes en la base de datos y publica la prenda en el catálogo."
            ],
            "flujo_alternativo": [
                "4.a. El código base del producto o el nombre ya existe en la empresa; el sistema comprueba la duplicidad, avisa al actor y le permite corregirlo.",
                "7.a. El actor no seleccionó ninguna variante de talla y color; el sistema comprueba que exista al menos una variante activa y avisa al actor para que la agregue."
            ],
            "poscondiciones": "La prenda y sus variantes físicas quedan almacenadas en el catálogo de la empresa con sus códigos SKU generados."
        },
        # CU06
        {
            "nombre": "CU06: Gestionar Catálogo Base (Categorías, Tallas y Colores)",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite administrar los catálogos maestros necesarios para la clasificación de prendas textiles, incluyendo la creación y edición de categorías de ropa propias de la empresa, así como la consulta de la tabla estandarizada de tallas y paleta de colores.",
            "actores": "Administrador de Tenant.",
            "precondiciones": "El usuario debe haberse autenticado con credenciales de administrador.",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción 'Maestros de Catálogo'.",
                "2. El sistema muestra pestañas separadas para Categorías (de la empresa), Tallas (estándar) y Colores (paleta cromática con código hexadecimal).",
                "3. El actor pulsa sobre la pestaña 'Categorías' y presiona el botón 'Nueva Categoría'.",
                "4. El sistema muestra un formulario solicitando nombre de la categoría, género de prenda (Damas, Caballeros, Niños, Unisex) y descripción.",
                "5. El actor introduce los datos y pulsa sobre 'Guardar'.",
                "6. El sistema comprueba que el nombre no esté duplicado en el tenant, almacena la nueva categoría y actualiza la lista."
            ],
            "flujo_alternativo": [
                "3.a. El actor selecciona la pestaña 'Colores': el sistema despliega la paleta de colores activa con muestra visual y código HEX; el actor puede registrar un nuevo tono cromático.",
                "6.a. La categoría introducida ya existe en la empresa; el sistema avisa al actor de la duplicidad impidiendo guardar el registro repetido."
            ],
            "poscondiciones": "Las categorías y parámetros maestros quedan almacenados y disponibles para clasificar nuevas prendas en el catálogo."
        },
        # CU07
        {
            "nombre": "CU07: Gestionar Proveedores de Indumentaria",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite registrar y mantener la información comercial de los proveedores mayoristas y talleres de confección que abastecen a la empresa, registrando datos de contacto, identificación fiscal (NIT), dirección y acuerdos comerciales de suministro.",
            "actores": "Administrador de Tenant, Proveedor.",
            "precondiciones": "El administrador debe estar autenticado con permisos de adquisiciones en el tenant.",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción 'Proveedores' en el menú de navegación.",
                "2. El sistema muestra la nómina de proveedores registrados para la empresa con su razón social, NIT, teléfono y estado.",
                "3. El actor pulsa sobre el botón 'Nuevo Proveedor'.",
                "4. El sistema muestra un formulario solicitando razón social, NIT/cédula fiscal, dirección, teléfono, correo y catálogo de productos suministrados.",
                "5. El actor introduce los datos comerciales y pulsa sobre 'Registrar Proveedor'.",
                "6. El sistema comprueba que el NIT no esté duplicado para el tenant, almacena la ficha del proveedor y actualiza la vista."
            ],
            "flujo_alternativo": [
                "3.a. El actor selecciona un proveedor existente y pulsa sobre 'Editar': el sistema carga la información comercial, el actor actualiza datos y guarda los cambios.",
                "6.a. El NIT introducido ya pertenece a otro proveedor registrado en la empresa; el sistema avisa al actor del conflicto y solicita corregir el documento."
            ],
            "poscondiciones": "El proveedor queda registrado en la base de datos de la empresa, habilitado para órdenes de compra y ofertas de suministro."
        },
        # CU08
        {
            "nombre": "CU08: Consultar Catálogo y Buscar Prendas con Filtros",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite a los clientes y personal comercial explorar la colección de prendas activas, buscar artículos por nombre o descripción y aplicar filtros combinados por categoría, temporada, rango de precios, talla y color.",
            "actores": "Cliente, Cajero, Encargado de Sucursal.",
            "precondiciones": "Deben existir prendas de vestir activas y publicadas en el catálogo de la empresa.",
            "flujo_normal": [
                "1. El actor accede a la vista principal del catálogo desde el navegador web o la aplicación móvil.",
                "2. El sistema recupera y muestra la cuadrícula de prendas activas con su fotografía principal, nombre, precio de venta y tallas disponibles.",
                "3. El actor introduce un término de búsqueda (ej. 'Vestido Seda') o pulsa sobre los filtros de categoría, temporada, talla o color.",
                "4. El sistema filtra dinámicamente las prendas que coinciden con los criterios y actualiza la cuadrícula de resultados.",
                "5. El actor pulsa sobre la tarjeta de una prenda para ver su detalle.",
                "6. El sistema muestra la ficha técnica completa con galería de imágenes, selector de variantes con disponibilidad y descripción del producto."
            ],
            "flujo_alternativo": [
                "4.a. Ningún producto coincide con los filtros aplicados; el sistema muestra un mensaje indicando 'No se encontraron prendas para los filtros seleccionados' y ofrece una opción para restablecer la búsqueda.",
                "1.a. (Modo Offline en PWA o Móvil): El dispositivo carece de conectividad; el sistema consulta el catálogo persistido localmente en IndexedDB o SQLite y presenta las prendas con la advertencia visual 'Catálogo fuera de línea'."
            ],
            "poscondiciones": "El actor visualiza la información y detalle de las prendas deseadas, pudiendo proceder a consultar disponibilidad en tiendas o agregar al carrito."
        },
        # CU09
        {
            "nombre": "CU09: Consultar Disponibilidad de Existencias por Tienda",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al cliente, desde la ficha de una prenda, consultar el stock físico disponible en cada una de las sucursales de la empresa para una variante específica (talla y color), facilitando la decisión de compra presencial o la derivación al flujo de reserva de prendas.",
            "actores": "Cliente, Vendedor de Sucursal.",
            "precondiciones": "La prenda debe estar publicada en el catálogo y el actor debe seleccionar una variante específica (talla y color).",
            "flujo_normal": [
                "1. El actor se encuentra en la pantalla de detalle de una prenda específica.",
                "2. El actor selecciona la talla y el color de su preferencia.",
                "3. El actor pulsa sobre el botón 'Ver disponibilidad en tiendas'.",
                "4. El sistema consulta las existencias en tiempo real filtrando por el tenant, la variante seleccionada y las sucursales activas.",
                "5. El sistema muestra una lista organizada por ciudad y sucursal, indicando dirección, nivel de stock (Disponible, Stock Bajo, Agotado) y la opción 'Reservar para probar en tienda'.",
                "6. El actor identifica la sucursal de su preferencia para visitarla o iniciar el apartado de la prenda."
            ],
            "flujo_alternativo": [
                "2.a. El actor pulsa sobre consultar disponibilidad sin haber seleccionado talla o color; el sistema comprueba la omisión y avisa al actor para que elija ambos atributos.",
                "4.a. La variante no cuenta con existencias en ninguna sucursal física; el sistema muestra el mensaje 'Sin existencias en tiendas físicas por el momento' y sugiere consultar otras variantes o comprar vía envío a domicilio."
            ],
            "poscondiciones": "El actor conoce en qué sucursales físicas se encuentra disponible la prenda y queda habilitado para realizar una reserva presencial (CU10)."
        }
    ]

    # Render each of the 9 use case tables matching the exact image layout
    for idx, ficha in enumerate(fichas_data, start=1):
        # Heading for each use case
        p_cu_title = doc.add_paragraph()
        p_cu_title.paragraph_format.space_before = Pt(14)
        p_cu_title.paragraph_format.space_after = Pt(4)
        p_cu_title.paragraph_format.keep_with_next = True
        run_ct = p_cu_title.add_run(f"2.6.{idx}. Ficha de Especificación — {ficha['nombre']}")
        run_ct.bold = True
        run_ct.font.name = "Arial"
        run_ct.font.size = Pt(11.5)
        run_ct.font.color.rgb = SLATE_BLUE

        # Create table: 9 rows, 2 columns
        tbl = doc.add_table(rows=9, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(tbl, color="000000", sz="6", val="single")

        col_w0 = Inches(1.5)
        col_w1 = Inches(5.0)

        # Helper to set cell content with label and text
        def populate_field_row(row_idx, label, val_text, is_merged=False):
            if is_merged:
                cell = tbl.cell(row_idx, 0).merge(tbl.cell(row_idx, 1))
                cell.width = Inches(6.5)
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                cell.text = ""
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(2)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                # Bold label
                run_lbl = p.add_run(label)
                run_lbl.bold = True
                run_lbl.font.name = "Arial"
                run_lbl.font.size = Pt(9.5)
                run_lbl.font.color.rgb = DARK_TEXT

                # Content
                if isinstance(val_text, list):
                    for item in val_text:
                        p_item = cell.add_paragraph()
                        p_item.paragraph_format.left_indent = Inches(0.20)
                        p_item.paragraph_format.line_spacing = 1.15
                        p_item.paragraph_format.space_after = Pt(2)
                        p_item.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        run_item = p_item.add_run(item)
                        run_item.font.name = "Arial"
                        run_item.font.size = Pt(9)
                        run_item.font.color.rgb = DARK_TEXT
                else:
                    p_val = cell.add_paragraph()
                    p_val.paragraph_format.left_indent = Inches(0.20)
                    p_val.paragraph_format.line_spacing = 1.15
                    p_val.paragraph_format.space_after = Pt(2)
                    p_val.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    run_val = p_val.add_run(val_text)
                    run_val.font.name = "Arial"
                    run_val.font.size = Pt(9)
                    run_val.font.color.rgb = DARK_TEXT
            else:
                # 2 separate cells
                c0 = tbl.cell(row_idx, 0)
                c1 = tbl.cell(row_idx, 1)
                c0.width = col_w0
                c1.width = col_w1
                set_cell_margins(c0, top=70, bottom=70, left=100, right=100)
                set_cell_margins(c1, top=70, bottom=70, left=100, right=100)

                c0.text = ""
                p0 = c0.paragraphs[0]
                p0.paragraph_format.line_spacing = 1.15
                p0.paragraph_format.space_after = Pt(1)
                run0 = p0.add_run(label)
                run0.bold = True
                run0.font.name = "Arial"
                run0.font.size = Pt(9.5)
                run0.font.color.rgb = DARK_TEXT

                c1.text = ""
                p1 = c1.paragraphs[0]
                p1.paragraph_format.line_spacing = 1.15
                p1.paragraph_format.space_after = Pt(1)
                run1 = p1.add_run(val_text)
                run1.font.name = "Arial"
                run1.font.size = Pt(9)
                run1.font.color.rgb = DARK_TEXT

        # Populate rows according to the uploaded image structure
        populate_field_row(0, "Nombre:", ficha["nombre"], is_merged=False)
        populate_field_row(1, "Autor:", ficha["autor"], is_merged=False)
        populate_field_row(2, "Fecha:", ficha["fecha"], is_merged=False)
        populate_field_row(3, "Descripción:", ficha["descripcion"], is_merged=True)
        populate_field_row(4, "Actores:", ficha["actores"], is_merged=True)
        populate_field_row(5, "Precondiciones:", ficha["precondiciones"], is_merged=True)
        populate_field_row(6, "Flujo Normal:", ficha["flujo_normal"], is_merged=True)
        populate_field_row(7, "Flujo Alternativo:", ficha["flujo_alternativo"], is_merged=True)
        populate_field_row(8, "Poscondiciones:", ficha["poscondiciones"], is_merged=True)

        # Space after each table
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(4)
        p_after.paragraph_format.space_after = Pt(8)

    # Save document
    output_filename = "docsegundoparcialSI2.docx"
    doc.save(output_filename)
    print(f"Capítulo II incorporado exitosamente en '{output_filename}'.")

if __name__ == "__main__":
    append_capitulo2()
