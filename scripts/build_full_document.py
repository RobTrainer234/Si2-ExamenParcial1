# -*- coding: utf-8 -*-
"""
Master script to generate docsegundoparcialSI2.docx with:
- Preserved institutional cover page (UAGRM / FICCT / Grupo 26)
- CAPÍTULO I. ASPECTOS GENERALES (completo con introducción de 1 plana, nuevos objetivos y los 20 módulos)
- CAPÍTULO II. ANÁLISIS DE REQUISITOS:
  * 2.1. Descripción del Sistema Propuesto
  * 2.2. Identificación de Actores
  * 2.3. Requisitos Funcionales y No Funcionales (RF01-RF16, RNF01-RNF12)
  * 2.4. Reglas de Negocio (RN01-RN10)
  * 2.5. Diagrama UML de Casos de Uso y Matriz Oficial de los 25 Casos de Uso del Segundo Parcial
  * 2.6. Especificación de Casos de Uso (Fichas estructuradas de los Casos de Uso de la Primera Fase según el formato de la imagen)
"""

import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

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

def build_entire_document():
    doc = docx.Document('docsegundoparcialSI2_backup.docx')

    # Remove old body elements between index 24 (after Semestre II/2026) and sectPr
    while len(doc._body._element) > 25:
        el = doc._body._element[24]
        if el.tag.endswith('sectPr'):
            break
        doc._body._element.remove(el)

    # Configure Margins, Header & Footer on section
    for section in doc.sections:
        section.top_margin = Inches(0.984)     # ~2.5 cm
        section.bottom_margin = Inches(0.984)  # ~2.5 cm
        section.left_margin = Inches(1.181)    # ~3.0 cm
        section.right_margin = Inches(0.984)   # ~2.5 cm

        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.text = ""
        hrun = hp.add_run("FashionStore SaaS — Plataforma de Comercio Electrónico Multi-tenant")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(113, 128, 150)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.text = ""
        frun = fp.add_run("Sistemas de Información II — FICCT UAGRM | Semestre II/2026")
        frun.font.name = "Arial"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(113, 128, 150)

    # Color palette
    NAVY_BLUE = RGBColor(27, 54, 93)      # #1B365D - Heading 1 & Titles
    SLATE_BLUE = RGBColor(44, 82, 130)    # #2C5282 - Heading 2
    ACCENT_BLUE = RGBColor(43, 108, 176)  # #2B6CB0 - Heading 3 & Subtitles
    DARK_TEXT = RGBColor(34, 34, 34)      # #222222 - Body text

    # Helpers
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

    def add_module_item(num, name, description):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.20)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(5)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        run_num = p.add_run(f"{num}. ")
        run_num.bold = True
        run_num.font.name = "Arial"
        run_num.font.size = Pt(11)
        run_num.font.color.rgb = ACCENT_BLUE

        run_name = p.add_run(f"{name}: ")
        run_name.bold = True
        run_name.font.name = "Arial"
        run_name.font.size = Pt(11)
        run_name.font.color.rgb = DARK_TEXT

        run_desc = p.add_run(description)
        run_desc.font.name = "Arial"
        run_desc.font.size = Pt(11)
        run_desc.font.color.rgb = DARK_TEXT
        return p

    # =========================================================================
    # CAPÍTULO I. ASPECTOS GENERALES
    # =========================================================================
    add_chapter_title("CAPÍTULO I. ASPECTOS GENERALES")

    # 1.1. Introducción
    add_h1("1.1. INTRODUCCIÓN")
    add_body_p(
        "El sector de la moda y la comercialización minorista de prendas de vestir atraviesa "
        "una profunda transformación tecnológica, impulsada por la exigencia de experiencias "
        "omnicanal fluidas, la personalización masiva y la necesidad imperiosa de alta disponibilidad "
        "operativa en los puntos de venta físicos y virtuales. Durante la primera fase del proyecto "
        "académico, se concibió e implementó el prototipo funcional de FashionStore como una solución "
        "de comercio electrónico destinada a una cadena de tiendas de ropa, integrando la administración "
        "centralizada de catálogos con variantes de talla y color, inventarios distribuidos en múltiples "
        "sucursales, pasarelas de pago, reservas de prendas y un probador interactivo pionero asistido "
        "por visión por computadora y realidad aumentada. Si bien dicho prototipo resolvió con éxito las "
        "demandas comerciales inmediatas de una sola empresa, su arquitectura monolítica y orientada a "
        "un único inquilino (single-tenant) restringía severamente su viabilidad como producto tecnológico "
        "escalable y comercializable hacia el ecosistema empresarial."
    )
    add_body_p(
        "Frente a este escenario, la presente segunda fase marca un salto cuantitativo y cualitativo "
        "fundamental: la evolución estratégica de FashionStore hacia una plataforma integral bajo el "
        "modelo Software as a Service (SaaS) Multi-tenant. Bajo este nuevo paradigma, la infraestructura "
        "de software se desacopla de una empresa en particular para transformarse en un servicio cloud "
        "multicliente, permitiendo que múltiples marcas, confeccionistas y cadenas de tiendas operen de "
        "manera simultánea y rigurosamente aislada sobre una única base de datos compartida en PostgreSQL. "
        "Mediante esquemas de suscripción comercialmente estructurados (Planes Básico y Profesional), cada "
        "empresa cliente (tenant) adquiere un entorno lógico privado con gobernanza autónoma sobre sus "
        "sucursales, inventarios, empleados, clientes y ventas, eliminando las onerosas barreras de entrada "
        "técnicas y económicas que tradicionalmente marginan a las pequeñas y medianas empresas del retail."
    )
    add_body_p(
        "Asimismo, el proyecto asume con realismo operativo las debilidades de infraestructura que "
        "aquejan al comercio minorista en la región, donde la inestabilidad de la conectividad a Internet "
        "suele provocar la parálisis total de las cajas de cobro y pérdidas económicas sustantivas. En "
        "respuesta a esta contingencia, FashionStore incorpora una arquitectura resiliente Offline-First. "
        "Tanto la aplicación web evolucionada a Progressive Web App (PWA con almacenamiento en IndexedDB) "
        "como la aplicación móvil desarrollada en Flutter (apoyada en una base de datos relacional local en "
        "SQLite) están facultadas para continuar operando sin interrupción ante la pérdida de señal. Cajeros "
        "y vendedores pueden consultar el catálogo descargado, registrar ventas presenciales de contado y "
        "efectuar reservas de prendas de forma desconectada. Al restablecerse la red, un protocolo de "
        "sincronización transaccional por lotes basado en el patrón Outbox e identificadores universales "
        "(UUID) transfiere los registros al backend, aplicando políticas de idempotencia estricta, descuento "
        "atómico de stock y detección formal de conflictos de inventario (sobreventas), garantizando la "
        "absoluta integridad de los datos centrales."
    )
    add_body_p(
        "Como complemento estratégico a la resiliencia operativa, FashionStore trasciende la analítica "
        "convencional de reportes estáticos mediante la integración de Inteligencia Artificial Generativa y "
        "Machine Learning. La plataforma dota a los directivos y gerentes de un motor analítico interactivo "
        "que procesa solicitudes en lenguaje natural formuladas por texto o comandos de voz (micrófono), "
        "construyendo al vuelo consultas estructuradas, visualizaciones gráficas interactivas y reportes "
        "oficiales exportables en formatos PDF y Excel. Simultáneamente, se incorporan modelos predictivos "
        "supervisados para pronosticar la demanda futura de prendas y modelos no supervisados de clusterización "
        "RFM para segmentar clientes, optimizando sustancialmente el abastecimiento y la toma de decisiones."
    )
    add_body_p(
        "Para gobernar este complejo ecosistema con máximo rigor de ingeniería de software, el equipo "
        "adopta la metodología ICONIX, un proceso ágil y dirigido por casos de uso que optimiza el modelado "
        "UML mediante la regla 80/20. A través de diagramas de robustez (Boundary-Controller-Entity) y su "
        "posterior refinamiento en diagramas de secuencia y clases, se asegura una trazabilidad transparente "
        "y verificable entre los requisitos del negocio, la arquitectura cloud-edge y las pruebas automatizadas. "
        "El presente Capítulo I establece los aspectos generales, problemáticas, objetivos rectores, "
        "justificaciones interdisciplinarias y el alcance detallado de todos los módulos que conforman la "
        "plataforma FashionStore SaaS."
    )

    # 1.2. Planteamiento del Problema
    add_h1("1.2. PLANTEAMIENTO DEL PROBLEMA")
    add_body_p(
        "El sector de comercialización de prendas de vestir enfrenta un entorno altamente competitivo y "
        "demandante, en el cual las limitaciones de las herramientas de software convencionales frenan el "
        "crecimiento de las empresas y generan graves ineficiencias operativas. A partir del diagnóstico "
        "del prototipo unitenant desarrollado en la fase inicial y del análisis de campo de las cadenas de retail, "
        "se identifican cuatro problemas nodales que sustentan la evolución del presente proyecto:"
    )
    add_bullet_item(
        "Inescalabilidad y altos costos del modelo tradicional monousuario: ",
        "El despliegue de instancias independientes de software por cada comercio de ropa genera costos "
        "de infraestructura insostenibles, complejidad en el mantenimiento preventivo y barreras de entrada "
        "inalcanzables para marcas medianas y pequeñas. La ausencia de una arquitectura multitenant impide a "
        "los proveedores de software ofrecer soluciones accesibles mediante suscripción, restringiendo el "
        "potencial de comercialización masiva de la solución."
    )
    add_bullet_item(
        "Vulnerabilidad operativa por interrupción de conectividad a Internet: ",
        "La inmensa mayoría de los sistemas de punto de venta (POS) y comercio electrónico contemporáneos "
        "dependen de una conexión ininterrumpida a servidores en la nube. Cuando la red colapsa —un evento "
        "frecuente en las sucursales físicas—, los locales quedan incapacitados para cobrar, facturar o reservar "
        "artículos. Esto ocasiona fuga de clientes hacia la competencia, pérdidas económicas directas y caos en "
        "el control de cajas al intentar registrar ventas mediante anotaciones manuales propensas al error."
    )
    add_bullet_item(
        "Inconsistencias y conflictos de sobreventa en operaciones desconectadas: ",
        "Cuando se habilita la venta fuera de línea de manera rudimentaria, surge el grave riesgo de "
        "inconsistencia de existencias: múltiples terminales pueden vender la misma prenda sin conocer el stock "
        "real remanente. Sin un protocolo robusto de sincronización outbox, validación de idempotencia y reglas "
        "de resolución de conflictos de inventario, la base central queda expuesta a descuadres de stock y "
        "duplicaciones transaccionales que perjudican la credibilidad del negocio."
    )
    add_bullet_item(
        "Rigidez en la explotación analítica de la información para la toma de decisiones: ",
        "Las plataformas de e-commerce comerciales suelen ofrecer reportes tabulares estáticos y predefinidos. "
        "Los gerentes de tienda carecen de flexibilidad para cruzar variables sobre la marcha o formular preguntas "
        "complejas en lenguaje natural. Esta rigidez impide anticipar tendencias de demanda estacional o segmentar "
        "adecuadamente a los clientes, derivando en acumulación de prendas obsoletas o desabastecimiento de tallas "
        "y modelos críticos."
    )

    # 1.3. Objetivos del Proyecto
    add_h1("1.3. OBJETIVOS DEL PROYECTO")
    add_h2("1.3.1. Objetivo General")
    add_body_p(
        "Diseñar, desarrollar y evolucionar la plataforma integral de comercio electrónico de prendas de vestir "
        "FashionStore hacia un ecosistema tecnológico escalable bajo el modelo Software as a Service (SaaS) "
        "Multi-tenant, dotado de resiliencia operativa Offline-First (PWA y móvil) con sincronización "
        "transaccional consistente, y capacidades avanzadas de Inteligencia Artificial Generativa y Analítica "
        "Predictiva (Machine Learning) para la optimización comercial, gobernado bajo la metodología dirigida "
        "por casos de uso ICONIX y validado mediante pruebas automatizadas rigurosas."
    )

    add_h2("1.3.2. Objetivos Específicos")
    add_bullet_item(
        "Arquitectura e Infraestructura SaaS Multi-tenant: ",
        "Diseñar e implementar una arquitectura de base de datos relacional compartida en PostgreSQL con "
        "aislamiento lógico riguroso mediante discriminador tenant_id en todas las entidades de negocio, "
        "incorporando la administración paramétrica de planes de suscripción (Básico y Profesional) con políticas "
        "de control de acceso y cuotas operativas ejecutadas estrictamente en el backend."
    )
    add_bullet_item(
        "Resiliencia Comercial Offline en Web (Angular PWA): ",
        "Evolucionar la aplicación web desarrollada en Angular hacia una Progressive Web App instalable, "
        "configurando Service Workers para el almacenamiento en caché del Application Shell y un almacén "
        "relacional local en IndexedDB, permitiendo la consulta de catálogo y el registro local de ventas al "
        "contado y reservas de prendas ante caídas de la red."
    )
    add_bullet_item(
        "Persistencia Local y Movilidad en Terminales de Venta (Flutter + SQLite): ",
        "Implementar en la aplicación móvil desarrollada en Flutter un mecanismo de persistencia relacional "
        "embebida mediante SQLite, facilitando la descarga de un subconjunto del catálogo y la continuidad de "
        "las operaciones de venta y apartado de prendas para el personal de sucursal bajo condiciones de conectividad nula."
    )
    add_bullet_item(
        "Protocolo Transaccional de Sincronización y Consistencia de Inventario: ",
        "Construir un servicio centralizado de sincronización resiliente basado en el patrón Outbox y UUIDs "
        "únicos, implementando políticas de idempotencia estricta, descuento atómico de inventario en Kardex y "
        "detección/clasificación formal de conflictos de sobreventa (INSUFFICIENT_STOCK) sin degradar la base central."
    )
    add_bullet_item(
        "Inteligencia Artificial Generativa Multimodal para Inteligencia de Negocios: ",
        "Integrar un motor de procesamiento de lenguaje natural (con soporte de interacción escrita y por voz) "
        "capaz de interpretar intenciones gerenciales complejas, extraer filtros dinámicos (fechas, sucursales, "
        "categorías), ejecutar consultas seguras acotadas al tenant y presentar resultados mediante síntesis narrativa, "
        "gráficos seleccionados dinámicamente y exportación a archivos PDF y Excel."
    )
    add_bullet_item(
        "Analítica Predictiva y Modelado de Datos con Machine Learning: ",
        "Desarrollar e incorporar modelos de aprendizaje automático supervisado para la predicción de demanda de "
        "prendas y modelos no supervisados de clusterización (K-Means RFM) para la segmentación estratégica de clientes, "
        "evaluados mediante métricas formales (MAE, RMSE, R² y Silhouette Score) y respaldados por datos sintéticos."
    )
    add_bullet_item(
        "Políticas Comerciales de Fidelización y Soporte Posventa: ",
        "Implementar un flujo transaccional seguro para la gestión de cambios y devoluciones de prendas dentro de "
        "un plazo límite de 30 días, garantizando la reintegración controlada de stock al inventario y el ajuste "
        "contable correspondiente."
    )
    add_bullet_item(
        "Trazabilidad de Ingeniería y Modelado Formal con ICONIX: ",
        "Aplicar metódicamente el proceso ICONIX en la evolución del software, articulando la transición entre "
        "los requisitos de negocio, los diagramas de robustez (BCE), los diagramas de secuencia UML 2.5+, el "
        "diagrama de clases y el código fuente ejecutable."
    )
    add_bullet_item(
        "Garantía de Calidad, Seguridad y Observabilidad: ",
        "Establecer una batería integral de pruebas automatizadas (unitarias, de integración, de aislamiento "
        "multitenant y de consistencia transaccional) bajo el enfoque Test-Driven Development (TDD), auditando "
        "la robustez del sistema y la no repudiación de eventos."
    )

    # 1.4. Justificación
    add_h1("1.4. JUSTIFICACIÓN")
    add_h2("1.4.1. Justificación Técnica")
    add_body_p(
        "Desde la perspectiva técnica, la consolidación de una arquitectura SaaS Multitenant basada en el patrón "
        "de esquema compartido con discriminador lógico (tenant_id) en PostgreSQL maximiza la eficiencia en el "
        "uso de recursos de cómputo y simplifica las operaciones de despliegue y migración de esquemas. Por otra "
        "parte, la combinación del framework asíncrono FastAPI en backend con Angular PWA (IndexedDB) y Flutter "
        "(SQLite) en clientes implementa una arquitectura edge computing distribuida y desacoplada. La adopción "
        "del patrón Outbox para la sincronización transaccional garantiza que las ventas y reservas nunca se pierdan "
        "en tránsito, confiriendo al sistema tolerancia a fallos, idempotencia y alta concurrencia."
    )
    add_h2("1.4.2. Justificación Económica")
    add_body_p(
        "En el ámbito económico, la transformación a un modelo SaaS democratiza el acceso a tecnología de punta "
        "para el sector de la confección y venta de ropa. Al sustituir la compra de costosas licencias e infraestructura "
        "propia por un esquema de suscripción mensual predecible y escalable (OPEX en lugar de CAPEX), se reduce "
        "drásticamente el Costo Total de Propiedad (TCO) para las empresas suscritas. Asimismo, la resiliencia offline "
        "evita las pérdidas monetarias directas asociadas a la inoperatividad de cajas en horarios pico, y los modelos "
        "de Machine Learning reducen el capital inmovilizado al evitar el sobreabastecimiento de prendas de baja rotación."
    )
    add_h2("1.4.3. Justificación Social y Operativa")
    add_body_p(
        "A nivel social y operativo, el proyecto dignifica y optimiza el trabajo diario de cajeros, administradores "
        "y encargados de tienda al liberarlos de la frustración que provocan las caídas de sistema. La interfaz "
        "intuitiva de punto de venta y la posibilidad de consultar indicadores clave mediante comandos de voz "
        "fomentan la inclusión digital y aceleran los tiempos de atención, impactando positivamente en la percepción "
        "de calidad y confianza del cliente final."
    )
    add_h2("1.4.4. Justificación Metodológica")
    add_body_p(
        "Metodológicamente, la adopción de ICONIX proporciona el equilibrio óptimo entre la rigidez burocrática "
        "del Proceso Unificado tradicional (PUDS/RUP) y la informalidad de ciertas corrientes ágiles. Mediante la "
        "regla 80/20, ICONIX focaliza el esfuerzo de modelado en los diagramas de robustez y de secuencia, cerrando "
        "eficazmente la brecha histórica entre el 'qué debe hacer el sistema' (casos de uso) y el 'cómo lo hace' "
        "(diseño detallado y código), garantizando una documentación viva y coherente con el software final."
    )

    # 1.5. Alcance y Limitaciones
    add_h1("1.5. ALCANCE Y LIMITACIONES")
    add_h2("1.5.1. Alcance del Proyecto por Módulos del Sistema")
    add_body_p(
        "El alcance funcional y técnico de FashionStore SaaS comprende la totalidad de los módulos desarrollados "
        "durante el primer parcial, enriquecidos y articulados con los nuevos componentes y subsistemas "
        "incorporados en esta segunda fase. A continuación, se presenta la descripción exhaustiva de cada uno de "
        "los 20 módulos que integran la plataforma:"
    )

    add_h3("A. Módulos del Núcleo y Gestión Retail (Base Comercial y Operativa)")
    modules_core = [
        (1, "Módulo de Autenticación, Seguridad y Gestión de Usuarios (RBAC Multi-tenant)",
         "Gestiona el ciclo de vida completo de identidades, credenciales cifradas mediante hashing seguro (bcrypt) "
         "y emisión de tokens JWT criptográficamente firmados. Implementa el control de acceso basado en roles "
         "(Superadministrador SaaS, Administrador de Tenant, Vendedor/Cajero de Sucursal, Cliente) y valida "
         "rigurosamente en cada petición al backend la pertenencia del usuario al tenant activo, impidiendo accesos "
         "cruzados o escaladas de privilegios no autorizadas."),
        (2, "Módulo de Gestión de Sucursales y Ubicaciones Geográficas",
         "Permite a cada empresa suscripta registrar, configurar y administrar su red física de tiendas y almacenes, "
         "vinculándolos a ciudades y zonas geográficas. Controla los topes de sucursales habilitadas según el plan "
         "contratado (hasta 2 en Básico, hasta 10 en Profesional) y asigna el personal comercial a puntos de venta específicos."),
        (3, "Módulo de Catálogo Maestro, Prendas y Variantes (Tallas y Colores)",
         "Administra la taxonomía completa de productos textiles: categorías, géneros, temporadas (Primavera-Verano, "
         "Otoño-Invierno), colecciones y marcas. Gestiona las matrices de variantes físicas (combinatorias de talla, "
         "color y material), códigos SKU únicos por empresa, descripciones técnicas, precios de lista y galerías fotográficas."),
        (4, "Módulo de Gestión de Proveedores y Cadena de Abastecimiento",
         "Controla el registro de proveedores mayoristas y talleres de confección, la recepción y comparación de "
         "ofertas de suministro de materias primas o prendas terminadas, la emisión de órdenes de compra y el "
         "seguimiento de los ciclos de reposición de mercadería dentro del ámbito exclusivo de cada empresa."),
        (5, "Módulo de Inventario Centralizado y Control de Stock (Kardex Multitienda)",
         "Mantiene el registro de existencias en tiempo real por cada variante de prenda y por cada sucursal física. "
         "Registra de forma inmutable cada movimiento de entrada, salida, ajuste por merma o transferencia entre tiendas "
         "en un Kardex formal, calculando stock disponible, stock bloqueado por reserva y alertas de inventario crítico."),
        (6, "Módulo de Punto de Venta (POS) y Venta Omnicanal",
         "Facilita la atención ágil en el mostrador físico de la tienda. Permite la selección rápida de prendas mediante "
         "lectores de códigos de barra o búsqueda predictiva, cálculo automático de importes, desglose impositivo, "
         "aplicación de promociones vigentes y emisión inmediata de comprobantes de venta."),
        (7, "Módulo de Carrito de Compras y Comercio Electrónico Web",
         "Brinda a los clientes finales una experiencia interactiva de compra digital para explorar colecciones, "
         "seleccionar variantes con validación instantánea de disponibilidad, gestionar artículos en el carrito de compras, "
         "elegir modalidades de entrega (retiro en sucursal o despacho a domicilio) y formalizar pedidos en línea."),
        (8, "Módulo de Gestión y Control de Reservas de Prendas",
         "Permite a los clientes apartar prendas físicas tanto a través del portal web como directamente en tienda. "
         "El módulo bloquea temporalmente las existencias en el inventario de la sucursal seleccionada para evitar que "
         "otro comprador las adquiera, aplicando una política de expiración automática si la reserva no se concreta "
         "en el plazo límite pactado."),
        (9, "Módulo de Procesamiento de Pagos y Facturación",
         "Orquesta las transacciones financieras asociadas a compras y reservas. Soporta pagos presenciales al contado "
         "(efectivo), cobro mediante transferencias QR interoperables y simulación de pagos electrónicos con tarjeta "
         "de crédito/débito a través de pasarelas virtuales, emitiendo comprobantes de venta con numeración correlativa."),
        (10, "Módulo de Gestión de Cambios de Prendas y Devoluciones Posventa",
         "Implementa la política comercial de posventa permitiendo procesar solicitudes de cambio de prendas dentro de "
         "un plazo comercial de 30 días calendario desde la venta original. Verifica la validez del comprobante, "
         "reingresa la prenda devuelta al inventario bajo movimiento formal de devolución (RETURN) y despacha la nueva "
         "prenda seleccionada (SALE), ajustando diferencias monetarias."),
        (11, "Módulo de Campañas Comerciales, Promociones y Descuentos",
         "Permite a los administradores estructurar campañas de marketing mediante descuentos porcentuales o de monto fijo "
         "aplicables a categorías, colecciones o prendas particulares, con programación de vigencia temporal y validación "
         "automática de restricciones en el carrito de compras y en las terminales POS."),
        (12, "Módulo de Probador Virtual y Realidad Aumentada (AR)",
         "Ofrece una experiencia visual innovadora que reduce la incertidumbre del comprador. En terminales móviles con "
         "cámara, utiliza algoritmos de visión artificial para detectar la pose corporal y la anchura de los hombros del "
         "usuario, superponiendo una representación a escala de la prenda en tiempo real; cuenta además con un simulador "
         "académico para navegadores web de escritorio."),
        (13, "Módulo de Asistente Virtual Inteligente y Recomendaciones de Moda",
         "Asistente conversacional ('Sofía IA') integrado en la interfaz de usuario que atiende dudas frecuentes sobre "
         "prendas, disponibilidad y guías de tallas. Incorpora un motor de recomendaciones personalizadas que sugiere "
         "artículos complementarios en base al historial de compras, navegación y preferencias de estilo del cliente."),
        (14, "Módulo de Auditoría del Sistema y Bitácora Transaccional",
         "Registra de manera secuencial, cronológica e inmutable todas las operaciones críticas ejecutadas en el "
         "sistema (inicios de sesión, cambios en inventario, modificaciones de precios, operaciones de sincronización y "
         "gestión de planes SaaS), asegurando la no repudiación de eventos y facilitando auditorías técnicas.")
    ]
    for num, name, desc in modules_core:
        add_module_item(num, name, desc)

    add_h3("B. Módulos de Evolución Tecnológica (SaaS, Resiliencia Offline y Analítica Avanzada)")
    modules_evolution = [
        (15, "Módulo de Administración SaaS Multi-tenant y Gestión de Suscripciones",
         "Permite la comercialización de FashionStore bajo la modalidad de software como servicio. Administra el alta "
         "y parametrización de empresas clientes (tenants), asignándoles identificadores globales únicos y garantizando "
         "el aislamiento lógico absoluto de su información en la base de datos PostgreSQL. Controla la contratación, "
         "vigencia y renovación de planes de suscripción (Plan Básico: hasta 2 sucursales activas, sin IA generativa; "
         "Plan Profesional: hasta 10 sucursales activas, con IA generativa y analítica habilitadas) y aplica las restricciones "
         "de funcionalidad correspondientes en el backend."),
        (16, "Módulo de Punto de Venta Web Progresivo (Angular PWA Offline con IndexedDB)",
         "Evoluciona la aplicación web Angular hacia una Progressive Web App instalable en sistemas operativos de escritorio "
         "y móviles. Mediante Service Workers implementa estrategias de almacenamiento en caché para la carga instantánea "
         "del Application Shell sin conexión. Utiliza el motor relacional local IndexedDB para almacenar catálogos, variantes "
         "y precios conocidos, permitiendo registrar ventas presenciales de contado y reservas de prendas fuera de línea, "
         "mostrando alertas visuales de conectividad y conservando los datos ante el reinicio del navegador."),
        (17, "Módulo de Terminal Móvil Desconectado (Flutter + SQLite)",
         "Aplicación móvil nativa multiplataforma (Android/iOS) desarrollada en Flutter + Dart para operadores y vendedores "
         "en piso de venta. Incorpora una base de datos embebida SQLite que almacena un subconjunto operativo del catálogo, "
         "sucursales y clientes. Permite formalizar ventas de contado y reservas en zonas de nula conectividad, persistiendo "
         "las transacciones de forma duradera y asegurando que ninguna venta se destruya al cerrar o apagar el dispositivo móvil."),
        (18, "Módulo de Sincronización Transaccional Resiliente y Resolución de Conflictos",
         "Motor de sincronización asíncrona sustentado en el patrón arquitectónico Outbox. Asigna identificadores universales "
         "únicos (UUID v4) a cada transacción originada fuera de línea y gestiona el envío por lotes (batch sync) hacia "
         "la API central al restablecerse la conexión a Internet. Aplica mecanismos de idempotencia estricta para ignorar "
         "reintentos duplicados, ejecuta el descuento atómico de inventario en el servidor y, ante insuficiencia de existencias "
         "reales, clasifica y notifica el conflicto comercial (INSUFFICIENT_STOCK) para su gestión en una bandeja de pendientes."),
        (19, "Módulo de Inteligencia Artificial Generativa para Reportes Ejecutivos (Texto y Voz)",
         "Subsistema analítico impulsado por modelos LLM que interpreta solicitudes gerenciales formuladas en lenguaje natural, "
         "ya sea mediante texto escrito o comandos de voz (Web Speech API y dictado móvil). Clasifica intenciones de consulta, "
         "extrae filtros dinámicos (períodos, sucursales, categorías), ejecuta consultas SQL controladas y estrictamente "
         "acotadas al tenant del usuario, generando dinámicamente síntesis narrativas, tablas de datos, gráficos interactivos "
         "(barras, líneas, pastel) y exportaciones formales a documentos PDF y hojas de cálculo Excel (.xlsx)."),
        (20, "Módulo de Analítica Predictiva y Modelado de Datos (Machine Learning Supervisado y No Supervisado)",
         "Subsistema de ciencia de datos que comprende: a) un servicio generador de datos sintéticos representativos del "
         "retail de moda; b) un modelo de aprendizaje supervisado (Ridge / Random Forest Regressor) para la proyección "
         "de demanda y ventas futuras evaluado con métricas MAE, RMSE y R²; c) un modelo no supervisado de agrupamiento "
         "(K-Means Clustering) basado en métricas RFM (Recencia, Frecuencia, Monto) para segmentar la base de clientes "
         "en perfiles estratégicos; y d) un dashboard analítico interactivo que visualiza dichos patrones en tiempo real.")
    ]
    for num, name, desc in modules_evolution:
        add_module_item(num, name, desc)

    # 1.5.2. Limitaciones del Proyecto
    add_h2("1.5.2. Limitaciones del Proyecto")
    add_bullet_item(
        "Simulación administrativa de facturación SaaS: ",
        "Para el alcance del prototipo académico, la contratación, renovación y cambio de planes de suscripción de las "
        "empresas clientes se gestionará y simulará administrativamente desde la plataforma, no requiriéndose la "
        "integración con pasarelas de pago recurrente bancario o plataformas externas como Stripe Billing."
    )
    add_bullet_item(
        "Ventas offline limitadas estrictamente a pago en efectivo / contado: ",
        "Las transacciones comerciales formalizadas en modo desconectado (tanto en la PWA como en Flutter) admitirán "
        "exclusivamente la modalidad de pago al contado en efectivo, quedando excluido el procesamiento diferido de tarjetas "
        "de crédito o débitos electrónicos mientras no exista enlace activo con el servidor central."
    )
    add_bullet_item(
        "Alcance del probador virtual y realidad aumentada: ",
        "Se conserva y consolida el módulo de vestidor virtual desarrollado en el primer parcial como un prototipo académico "
        "de posicionamiento visual basado en detección de pose corporal y hombros, sin incluir renderizado tridimensional "
        "avanzado de simulación física fotorrealista de telas ni garantías ergonómicas de entalle."
    )
    add_bullet_item(
        "Acceso de solo lectura y consultas controladas del motor de IA: ",
        "El motor de Inteligencia Artificial Generativa no posee acceso irrestricto ni permisos de escritura en la base de "
        "datos PostgreSQL. Su radio de acción se limita estrictamente a la interpretación de esquemas analíticos de solo "
        "lectura validados y parametrizados por el backend de FastAPI, garantizando que ninguna consulta vulnere el "
        "aislamiento entre empresas ni comprometa la integridad de los datos."
    )

    # 1.6. Metodología ICONIX
    add_h1("1.6. METODOLOGÍA DE DESARROLLO ICONIX")
    add_body_p(
        "Para guiar el proceso de ingeniería de software en esta segunda fase, se seleccionó la metodología ICONIX, "
        "un proceso unificado ágil, iterativo e incremental concebido por Doug Rosenberg. ICONIX se posiciona "
        "estratégicamente en el punto medio entre la pesadez documental del RUP/PUDS tradicional y la ligereza extrema "
        "de Extreme Programming (XP), sustentándose en la célebre 'Regla del 80/20': aproximadamente el 80% del valor "
        "arquitectónico del modelado se obtiene empleando únicamente el 20% del vocabulario estándar de UML."
    )
    add_body_p(
        "La metodología ICONIX se estructura a través de cuatro fases secuenciales e interactivas que aseguran una "
        "trazabilidad directa y verificable entre los requerimientos del usuario y el código fuente desplegado:"
    )
    add_bullet_item(
        "Fase 1: Análisis de Requisitos: ",
        "En esta etapa se capturan las expectativas del usuario mediante la elaboración de Storyboards y prototipos rápidos "
        "de interfaz. Simultáneamente, a partir de la identificación de los sustantivos clave del vocabulario del negocio "
        "(Tenant, Plan, Prenda, Sucursal, Venta, Inventario, Sincronización), se construye el Modelo de Dominio inicial "
        "y se formalizan los Casos de Uso estructurados."
    )
    add_bullet_item(
        "Fase 2: Análisis y Diseño Preliminar (Diagramas de Robustez): ",
        "Constituye el elemento distintivo y núcleo fundamental de ICONIX. Se redactan las fichas de casos de uso y se "
        "construyen los Diagramas de Robustez bajo el patrón Boundary-Controller-Entity (BCE). Este análisis descompone cada "
        "flujo de interacción en tres tipos de objetos: a) Objetos Frontera (Boundary), que representan las pantallas y vistas "
        "con las que interactúa el actor; b) Objetos de Control (Controller), que encapsulan la lógica de negocio, validaciones "
        "y reglas operativas; y c) Objetos de Entidad (Entity), que corresponden a las estructuras de datos y tablas de persistencia. "
        "El análisis de robustez valida la coherencia lógica de los casos de uso y actúa como puente inquebrantable entre "
        "los requerimientos y el diseño detallado."
    )
    add_bullet_item(
        "Fase 3: Diseño Detallado: ",
        "A partir de los controladores y entidades validados en los diagramas de robustez, se elaboran los Diagramas de "
        "Secuencia UML 2.5+, asignando mensajes, métodos y responsabilidades específicas a cada clase de software. En esta "
        "fase, el Modelo de Dominio evoluciona hacia el Diagrama de Clases Extendido con especificación formal de atributos, "
        "tipos de datos, cardinalidades y visibilidad, sirviendo como plano maestro para la codificación."
    )
    add_bullet_item(
        "Fase 4: Implementación y Pruebas Automatizadas: ",
        "Se procede al desarrollo de la solución en la pila tecnológica elegida (Python/FastAPI en backend, Angular PWA en web "
        "y Flutter en móvil). Se aplica la disciplina Test-Driven Development (TDD) para verificar las reglas críticas de negocio, "
        "el aislamiento multi-tenant, la resiliencia offline de IndexedDB/SQLite y la sincronización idempotente con resolución "
        "de conflictos, asegurando la perfecta correspondencia entre el software ejecutable y los modelos UML diseñados."
    )

    # =========================================================================
    # CAPÍTULO II. ANÁLISIS DE REQUISITOS
    # =========================================================================
    add_chapter_title("CAPÍTULO II. ANÁLISIS DE REQUISITOS")

    # 2.1. Descripción del Sistema Propuesto
    add_h1("2.1. DESCRIPCIÓN DEL SISTEMA PROPUESTO")
    add_body_p(
        "La plataforma propuesta, denominada FashionStore SaaS, representa un ecosistema tecnológico integral "
        "de comercio electrónico y gestión empresarial en la nube, diseñado específicamente para la comercialización "
        "minorista de prendas de vestir bajo un modelo de Software como Servicio (SaaS) Multi-tenant. La solución "
        "permite que múltiples empresas y marcas de moda independientes operen de forma concurrente, autónoma y segura "
        "sobre una arquitectura compartida en backend con aislamiento lógico absoluto de información mediante el "
        "discriminador tenant_id en PostgreSQL, eliminando la necesidad de desplegar costosas instancias de software "
        "dedicadas para cada cliente."
    )
    add_body_p(
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
    add_body_p(
        "Adicionalmente, el sistema integra capacidades de vanguardia en Inteligencia Artificial Generativa y Analítica "
        "Predictiva mediante Machine Learning. Los directivos y encargados de tienda pueden formular consultas complejas en "
        "lenguaje natural mediante texto o comandos de voz, obteniendo diagnósticos ejecutivos, visualizaciones gráficas "
        "interactivas y reportes oficiales exportables en formatos PDF y Excel (.xlsx). De forma complementaria, los modelos "
        "de Machine Learning supervisados (proyección de ventas y demanda con Ridge Regression) y no supervisados (clusterización "
        "RFM con K-Means) permiten anticipar tendencias de aprovisionamiento y segmentar la cartera de compradores, todo "
        "gobernado bajo los límites y permisos del plan de suscripción contratado (Básico o Profesional)."
    )

    # 2.2. Identificación de Actores del Sistema
    add_h1("2.2. IDENTIFICACIÓN DE ACTORES DEL SISTEMA")
    add_body_p(
        "Para el alcance del proyecto FashionStore SaaS en el Segundo Examen Parcial, se formaliza y acota la "
        "estructura de participantes en exactamente cinco actores oficiales (cuatro actores humanos que operan las "
        "diversas interfaces de usuario según sus roles de negocio, y un actor compuesto de sistema que orquesta los "
        "servicios autónomos en segundo plano):"
    )
    actores_list = [
        ("1. Superadmin SaaS (Administrador de la Plataforma): ",
         "Administra el ecosistema multitenant global, registra nuevas empresas contratantes (tenants), parametriza y "
         "fiscaliza los planes de suscripción (Básico y Profesional), supervisa la vigencia de los contratos y gestiona la "
         "asignación y renovación de los planes contratados para cada cliente empresarial."),
        ("2. Tenant Admin (Administrador de Empresa / Tienda): ",
         "Máxima autoridad de gestión dentro de una empresa cliente suscripta. Administra el personal, los usuarios y roles "
         "de su compañía, configura sucursales comerciales dentro de las cuotas contratadas, gestiona el catálogo de prendas "
         "y analiza los reportes ejecutivos e insights predictivos generados por Inteligencia Artificial y Machine Learning."),
        ("3. Cajero / Vendedor (Operador de Tienda y Punto de Venta POS): ",
         "Operador de terminal física y móvil de punto de venta. Realiza ventas presenciales de contado y formaliza reservas "
         "de prendas tanto en modo en línea como fuera de línea (offline), procesa cobros en caja, atiende cambios de prendas "
         "dentro del plazo comercial de 30 días y gestiona la bandeja local de transacciones pendientes de sincronización (Outbox)."),
        ("4. Cliente (Comprador Final): ",
         "Usuario final que interactúa con la plataforma a través de la tienda web (Progressive Web App - PWA) o la aplicación "
         "móvil. Consulta prendas y existencias por sucursal, aparta ropa para reserva en tienda física, formaliza compras de contado "
         "e instala y ejecuta la Progressive Web App en su dispositivo."),
        ("5. Actores de Sistema (IA, Middleware, Motor de Sincronización): ",
         "Conjunto especializado de componentes y microservicios automatizados que operan de forma autónoma en el backend y frontend:\n"
         "• Middleware de Restricciones SaaS: Intercepta peticiones para evaluar, validar y hacer cumplir las cuotas contractuales por plan (límite de sucursales y usuarios).\n"
         "• Motor de Sincronización y Persistencia: Monitorea reactivamente el enlace de red (semáforo online/offline), gestiona el almacenamiento relacional local (IndexedDB y SQLite) y ejecuta la sincronización por lotes hacia el servidor central.\n"
         "• Asistente de Inteligencia Artificial: Servicio cognitivo backend que procesa solicitudes analíticas en lenguaje natural (Text-to-SQL) y entrena los modelos de Machine Learning (demanda supervisada y clustering RFM).")
    ]
    for bold_p, text_p in actores_list:
        add_bullet_item(bold_p, text_p)

    # 2.3. Requisitos Funcionales y No Funcionales
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

    # 2.4. Reglas de Negocio
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
    # 2.5. DIAGRAMA UML DE CASOS DE USO Y MATRIZ OFICIAL DE LOS 25 CASOS DE USO
    # -------------------------------------------------------------------------
    add_h1("2.5. DIAGRAMA UML DE CASOS DE USO")

    add_body_p(
        "Para el Segundo Examen Parcial de Sistemas de Información II, el alcance funcional del proyecto "
        "se formalizó y acotó en una matriz oficial de exactamente 25 Casos de Uso (CU-01 al CU-25), estructurados "
        "metodológicamente bajo el ciclo de vida ICONIX y distribuidos estratégicamente a lo largo de las tres etapas "
        "de desarrollo del proyecto: Etapa 1 (SaaS Multitenant, PWA y Catálogo Offline), Etapa 2 (Operaciones Comerciales "
        "Offline y Sincronización Transaccional) y Etapa 3 (Inteligencia Artificial Generativa y Analítica Predictiva)."
    )

    add_h2("2.5.1. Diagrama General de Casos de Uso — Etapa 1")
    add_body_p(
        "El modelado formal de casos de uso para la primera etapa del proyecto comprende la interacción entre los cuatro "
        "actores principales del sistema (Superadmin SaaS, Tenant Admin, Cajero / Vendedor y Cliente) y los diez casos de uso "
        "que componen el núcleo de la fundación multitenant y la capacidad desconectada de consulta de catálogo:"
    )

    # Insertar Imagen del Diagrama de Casos de Uso Etapa 1
    diagram_path = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\diagrama_casos_uso_etapa1.png"
    if os.path.exists(diagram_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(diagram_path, width=Inches(6.4))

        p_caption = doc.add_paragraph()
        p_caption.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_caption.paragraph_format.space_after = Pt(12)
        run_cap = p_caption.add_run("Figura 2.1: Diagrama General de Casos de Uso UML — Etapa 1 (Fundación Multitenant y Catálogo Offline).")
        run_cap.italic = True
        run_cap.font.name = "Arial"
        run_cap.font.size = Pt(9.0)
        run_cap.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    add_body_p(
        "En el diagrama precedente se modelan de manera rigurosa las siguientes relaciones estereotipadas entre casos de uso:"
    )
    add_bullet_item("Relaciones «include» (Inclusión obligatoria): ",
                    "CU-01 (Registrar Empresa) incluye obligatoriamente a CU-03 (Asignar Suscripción) para provisionar el esquema de cobro y límites; "
                    "CU-03 incluye a CU-02 (Gestionar Planes) para consultar y parametrizar los tiers vigentes; "
                    "CU-05 (Gestionar Sucursales y Empleados) incluye a CU-04 (Controlar Límites por Plan) como middleware de verificación de cuotas; "
                    "y CU-07 (Consultar Catálogo Offline) incluye a CU-06 (Descargar y Almacenar Catálogo) para garantizar la disponibilidad local de las prendas.")
    add_bullet_item("Relaciones «extend» (Extensión condicional/soporte): ",
                    "CU-23 (Notificar Estado de Conectividad) extiende reactivamente a CU-06 cuando la red conmuta entre modo en línea y fuera de línea; "
                    "mientras que CU-24 (Instalar Service Worker PWA en Web) y CU-25 (Configurar Persistencia SQLite en Móvil) extienden y soportan "
                    "el aprovisionamiento de las bases de datos locales requeridas por CU-06.")

    add_h2("2.5.2. Matriz General de los 25 Casos de Uso del Proyecto")
    add_body_p(
        "A continuación se presenta la tabla integral de casos de uso requerida para el Segundo Parcial, especificando en "
        "columnas dedicadas: el identificador y nombre del caso de uso, los actores principales involucrados, la plataforma o canal tecnológico "
        "donde se ejecuta (Web, Móvil o Ambos), y la etapa de desarrollo a la que corresponde dentro del proyecto:"
    )

    # Official 25 Use Cases Matrix for 2nd Partial (Consolidated with the 5 Official Actors)
    use_cases_data_25 = [
        # Etapa 1
        ("CU-01: Registrar Empresa Contratante (Tenant)", "Superadmin SaaS", "Web", "Etapa 1"),
        ("CU-02: Gestionar Planes de Suscripción", "Superadmin SaaS", "Web", "Etapa 1"),
        ("CU-03: Asignar y Renovar Suscripción de Empresa", "Superadmin SaaS", "Web", "Etapa 1"),
        ("CU-04: Controlar Límites y Restricciones por Plan", "Tenant Admin", "Ambos (Web y Móvil)", "Etapa 1"),
        ("CU-05: Gestionar Sucursales y Empleados por Tenant", "Tenant Admin", "Web", "Etapa 1"),
        ("CU-06: Descargar y Almacenar Catálogo Offline", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 1"),
        ("CU-07: Consultar Catálogo y Existencias Offline", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 1"),
        ("CU-23: Notificar Estado de Conectividad (Semáforo)", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 1"),
        ("CU-24: Instalar y Registrar Service Worker (PWA)", "Cliente", "Web", "Etapa 1"),
        ("CU-25: Configurar y Migrar Persistencia SQLite Móvil", "Cajero / Vendedor", "Móvil", "Etapa 1"),
        # Etapa 2
        ("CU-08: Registrar Venta de Contado Offline", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 2"),
        ("CU-09: Registrar Reserva de Prendas Offline", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 2"),
        ("CU-10: Consultar Operaciones Locales Pendientes (Outbox)", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 2"),
        ("CU-11: Sincronizar Operaciones con el Servidor", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 2"),
        ("CU-12: Gestionar Conflictos de Sincronización", "Tenant Admin", "Ambos (Web y Móvil)", "Etapa 2"),
        ("CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 2"),
        ("CU-22: Gestionar Datos Mínimos de Clientes Offline", "Cajero / Vendedor", "Ambos (Web y Móvil)", "Etapa 2"),
        # Etapa 3
        ("CU-14: Solicitar Reporte por Lenguaje Natural (Texto/Voz)", "Tenant Admin", "Ambos (Web y Móvil)", "Etapa 3"),
        ("CU-15: Interpretar Consulta Analítica (Text-to-SQL)", "Actores de Sistema (IA), Tenant Admin", "Ambos (Web y Móvil)", "Etapa 3"),
        ("CU-16: Visualizar Reporte Dinámico (Tablas y Gráficos)", "Tenant Admin", "Ambos (Web y Móvil)", "Etapa 3"),
        ("CU-17: Exportar Reporte a Excel y PDF", "Tenant Admin", "Web", "Etapa 3"),
        ("CU-18: Generar Dataset Sintético de Entrenamiento", "Actores de Sistema (IA), Tenant Admin", "Web", "Etapa 3"),
        ("CU-19: Entrenar y Evaluar Modelo Supervisado (Demanda)", "Tenant Admin", "Web", "Etapa 3"),
        ("CU-20: Entrenar Modelo No Supervisado (Clustering RFM)", "Tenant Admin", "Web", "Etapa 3"),
        ("CU-21: Visualizar Dashboard Analítico Inteligente", "Tenant Admin", "Web", "Etapa 3")
    ]

    table_p25 = doc.add_table(rows=len(use_cases_data_25) + 1, cols=4)
    table_p25.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_p25, color="4A5568", sz="4", val="single")

    headers_25 = ["Caso de Uso (Código y Nombre)", "Actores Involucrados", "Plataforma / Canal", "Etapa"]
    widths_25 = [Inches(2.6), Inches(1.8), Inches(1.3), Inches(0.8)]

    hdr_cells_25 = table_p25.rows[0].cells
    for i, h_text in enumerate(headers_25):
        hdr_cells_25[i].text = ""
        set_cell_background(hdr_cells_25[i], "1B365D")
        set_cell_margins(hdr_cells_25[i], top=120, bottom=120, left=120, right=120)
        hdr_cells_25[i].width = widths_25[i]
        p = hdr_cells_25[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, (cu_name, cu_actors, cu_platform, cu_etapa) in enumerate(use_cases_data_25, start=1):
        row_cells = table_p25.rows[row_idx].cells
        bg_col = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"

        for col_idx, (val, width) in enumerate(zip([cu_name, cu_actors, cu_platform, cu_etapa], widths_25)):
            row_cells[col_idx].text = ""
            set_cell_background(row_cells[col_idx], bg_col)
            set_cell_margins(row_cells[col_idx], top=70, bottom=70, left=100, right=100)
            row_cells[col_idx].width = width
            p = row_cells[col_idx].paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(2)

            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(val)
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(9)
                run.font.color.rgb = DARK_TEXT
            elif col_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(val)
                run.font.name = "Arial"
                run.font.size = Pt(8.5)
                run.font.color.rgb = DARK_TEXT
            elif col_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(val)
                run.font.name = "Arial"
                run.font.size = Pt(8.5)
                if "Ambos" in val:
                    run.bold = True
                    run.font.color.rgb = ACCENT_BLUE
                else:
                    run.font.color.rgb = DARK_TEXT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(val)
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(8.5)
                if "Etapa 1" in val:
                    run.font.color.rgb = RGBColor(44, 122, 123) # Teal
                elif "Etapa 2" in val:
                    run.font.color.rgb = RGBColor(183, 121, 31) # Amber
                else:
                    run.font.color.rgb = RGBColor(107, 70, 193) # Purple

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(8)

    # -------------------------------------------------------------------------
    # 2.6. ESPECIFICACIÓN DE CASOS DE USO (Fichas Estructuradas de la Primera Fase)
    # -------------------------------------------------------------------------
    add_h1("2.6. ESPECIFICACIÓN DE CASOS DE USO")

    intro_p26_1 = (
        "A partir de cada caso de uso se obtienen sus correspondientes fichas de caso de uso. Cabe destacar "
        "que estas fichas no pertenecen formalmente al estándar UML, sino que constituyen una técnica estructurada "
        "esencial en la metodología ICONIX orientada a documentar de forma precisa, intuitiva y rigurosa la interacción del "
        "usuario con el sistema, describiendo precondiciones, secuencias de pasos normales, flujos alternativos o excepciones "
        "y poscondiciones garantizadas."
    )
    add_body_p(intro_p26_1)

    intro_p26_2 = (
        "En estricto apego al formato de especificación estructurada requerido para el proyecto, a continuación "
        "se detallan las fichas completas de los casos de uso fundamentales que componen la primera fase del sistema "
        "(Etapa 1: Fundación SaaS Multitenant, Aislamiento Backend, Progressive Web App y Consulta de Catálogo Offline):"
    )
    add_body_p(intro_p26_2)

    # Fichas for the 9 core use cases of the First Phase of the 2nd Partial
    fichas_segundo_parcial = [
        # CU-01
        {
            "nombre": "CU-01: Registrar Empresa Contratante (Tenant)",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al Superadministrador de la plataforma dar de alta a una nueva empresa cliente (tenant) en el ecosistema SaaS, configurando su razón social, identificador único (tenant_id), datos de contacto y creando la cuenta del Administrador de la Empresa.",
            "actores": "Superadmin SaaS.",
            "precondiciones": "El superadministrador debe haberse autenticado en la plataforma con credenciales válidas y rol de plataforma explícito.",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción 'Empresas Contratantes' en el panel SaaS.",
                "2. El sistema muestra la lista de empresas activas y el botón 'Registrar Nueva Empresa'.",
                "3. El actor pulsa sobre el botón para registrar una nueva empresa.",
                "4. El sistema muestra un formulario solicitando razón social, NIT/identificación fiscal, correo corporativo, teléfono, dirección y datos del administrador inicial.",
                "5. El actor introduce los datos de la empresa y del administrador responsable, y pulsa 'Guardar Empresa'.",
                "6. El sistema comprueba la validez de los datos y verifica que el correo del administrador no esté duplicado en el sistema.",
                "7. El sistema genera un identificador único (tenant_id), crea la entidad Tenant en PostgreSQL, provisiona el usuario administrador con rol de empresa y almacena la información.",
                "8. El sistema notifica al actor que la empresa ha sido registrada exitosamente y redirige a la asignación de plan."
            ],
            "flujo_alternativo": [
                "6.a. El sistema comprueba la validez de los datos; si los datos no son correctos o faltan campos obligatorios, se avisa al actor de ello permitiéndole que los corrija.",
                "6.b. El correo electrónico del administrador ya está en uso por otro usuario; el sistema notifica el conflicto y solicita ingresar una cuenta de correo distinta."
            ],
            "poscondiciones": "La nueva empresa queda registrada con su tenant_id único y su entorno lógico aislado en la base de datos central PostgreSQL."
        },
        # CU-02
        {
            "nombre": "CU-02: Gestionar Planes de Suscripción",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al Superadministrador de plataforma crear, configurar y actualizar el catálogo de planes de suscripción (Plan Básico y Plan Profesional), definiendo límites de sucursales activas, cuotas y habilitación de funcionalidades avanzadas como IA generativa.",
            "actores": "Superadmin SaaS.",
            "precondiciones": "Superadministrador autenticado con permisos de administración de planes SaaS.",
            "flujo_normal": [
                "1. El actor pulsa sobre la opción 'Planes de Suscripción' en el menú de plataforma.",
                "2. El sistema recupera y muestra los planes existentes (Básico y Profesional) con sus límites configurados y estado.",
                "3. El actor selecciona un plan para editar o pulsa sobre 'Crear Nuevo Plan'.",
                "4. El sistema muestra un formulario solicitando código de plan, nombre descriptivo, límite máximo de sucursales activas, indicador de habilitación de reportes IA generativa y estado activo.",
                "5. El actor introduce los parámetros del plan (ej. Básico: 2 sucursales, sin IA; Profesional: 10 sucursales, con IA y analítica) y pulsa 'Guardar Plan'.",
                "6. El sistema comprueba la validez de los límites numéricos y almacena la configuración en la tabla SubscriptionPlan.",
                "7. El sistema confirma la actualización y refresca la matriz de planes disponibles."
            ],
            "flujo_alternativo": [
                "6.a. El actor introduce un límite de sucursales menor a 1 o un código de plan duplicado; el sistema avisa del error en los datos y permite corregirlos."
            ],
            "poscondiciones": "El catálogo de planes de suscripción queda actualizado y disponible para su asignación a las empresas clientes."
        },
        # CU-03
        {
            "nombre": "CU-03: Asignar y Renovar Suscripción de Empresa",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al Superadministrador asignar un plan de suscripción a una empresa cliente, registrar las fechas de inicio y vencimiento, simular administrativamente la contratación o renovación y gestionar cambios de plan según el modelo de negocio SaaS.",
            "actores": "Superadmin SaaS.",
            "precondiciones": "La empresa (tenant) debe existir y encontrarse registrada en el sistema.",
            "flujo_normal": [
                "1. El actor ingresa a la ficha de la empresa y selecciona la pestaña 'Suscripción'.",
                "2. El sistema muestra el estado actual de la suscripción, plan vigente, fecha de inicio, fecha de expiración y sucursales en uso.",
                "3. El actor pulsa sobre 'Cambiar de Plan / Renovar Suscripción'.",
                "4. El sistema despliega la lista de planes disponibles (Básico y Profesional) con sus características comerciales.",
                "5. El actor selecciona el nuevo plan, define la vigencia (ej. 30 días o 1 año) y confirma la operación.",
                "6. El sistema comprueba que las sucursales actualmente activas de la empresa no superen el nuevo límite del plan seleccionado.",
                "7. El sistema crea un nuevo registro en la tabla Subscription con estado ACTIVE, actualiza el período de vigencia y registra el evento en la bitácora.",
                "8. El sistema notifica al actor la confirmación de la suscripción y habilita de inmediato las nuevas capacidades en el backend."
            ],
            "flujo_alternativo": [
                "6.a. La empresa cuenta con más sucursales activas que las permitidas por el plan destino (ej. tiene 4 sucursales e intenta cambiar a Básico que admite 2); el sistema bloquea el cambio y avisa al actor que debe desactivar sucursales excedentes antes de degradar el plan."
            ],
            "poscondiciones": "La suscripción queda activada en el sistema, vinculando la empresa al plan elegido y actualizando sus cuotas en tiempo real."
        },
        # CU-04
        {
            "nombre": "CU-04: Controlar Límites y Restricciones por Plan",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Mecanismo transversal de control que intercepta y valida automáticamente en el backend que las operaciones ejecutadas por una empresa no excedan las cuotas de sucursales ni accedan a funciones restringidas por su plan contratado (ej. bloqueo de IA en Plan Básico con error 403).",
            "actores": "Tenant Admin.",
            "precondiciones": "Usuario autenticado perteneciente a un tenant con suscripción activa.",
            "flujo_normal": [
                "1. El actor intenta ejecutar una operación sensible (ej. dar de alta una nueva sucursal física o solicitar un reporte generativo por IA).",
                "2. El sistema intercepta la petición a través de las dependencias de autorización en FastAPI.",
                "3. El sistema consulta la suscripción activa del tenant_id del usuario y recupera los límites del plan contratado.",
                "4. El sistema comprueba que la operación solicitada cumpla con las políticas del plan (número de sucursales activas < límite y generative_reports_enabled == True).",
                "5. El sistema autoriza la ejecución y procesa normalmente la petición."
            ],
            "flujo_alternativo": [
                "4.a. El tenant tiene Plan Básico e intenta acceder a reportes generativos de IA; el sistema comprueba la restricción del plan, bloquea la ejecución y responde con código HTTP 403 FEATURE_NOT_IN_PLAN.",
                "4.b. El tenant alcanzó el número máximo de sucursales activas de su plan; el sistema deniega el registro de la nueva sucursal y muestra un aviso visual indicando que ha alcanzado el límite de su plan."
            ],
            "poscondiciones": "Las restricciones contractuales del plan se cumplen estrictamente en el backend, impidiendo el uso no autorizado de recursos."
        },
        # CU-05
        {
            "nombre": "CU-05: Gestionar Sucursales y Empleados por Tenant",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al Administrador de Empresa registrar y mantener la red de sucursales físicas de su compañía, asociarlas a ciudades geográficas, asignar encargados y colaboradores (Cajeros, Vendedores) y controlar su activación sin vulnerar las cuotas de su suscripción.",
            "actores": "Tenant Admin.",
            "precondiciones": "Administrador autenticado con suscripción vigente en su empresa.",
            "flujo_normal": [
                "1. El actor pulsa sobre el módulo 'Sucursales y Personal' en el panel administrativo.",
                "2. El sistema muestra la lista de sucursales de la empresa, su personal asignado y el contador de sucursales activas frente al límite contratado.",
                "3. El actor pulsa sobre el botón 'Registrar Sucursal'.",
                "4. El sistema comprueba que no se haya superado la cuota de sucursales activas del plan y muestra el formulario de captura.",
                "5. El actor introduce nombre de la tienda, ciudad, dirección, teléfono y asigna los empleados autorizados a operar en ella.",
                "6. El actor pulsa sobre el botón 'Guardar'.",
                "7. El sistema comprueba la validez de los datos, almacena la sucursal y sus asociaciones de usuario vinculadas al tenant_id en PostgreSQL, y actualiza la lista."
            ],
            "flujo_alternativo": [
                "4.a. La empresa alcanzó el límite de sucursales activas; el sistema bloquea el formulario e informa que debe actualizar al Plan Profesional para aperturar más sucursales.",
                "6.a. Los datos requeridos están incompletos o la combinación de sucursal y ciudad ya existe en la empresa; el sistema avisa al actor para que corrija la información."
            ],
            "poscondiciones": "La nueva sucursal física queda registrada y disponible para recibir inventario y transacciones comerciales de su empresa."
        },
        # CU-06
        {
            "nombre": "CU-06: Descargar y Almacenar Catálogo Offline",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al cajero y personal de ventas en terminales móviles o web descargar y persistir de forma duradera el catálogo de prendas, variantes, precios y existencias en motores de almacenamiento local (IndexedDB o SQLite) para operar el punto de venta sin red.",
            "actores": "Cajero / Vendedor.",
            "precondiciones": "Dispositivo con conectividad activa y usuario autenticado en su empresa y sucursal.",
            "flujo_normal": [
                "1. El actor o la aplicación inicia el proceso de sincronización inicial o actualización del catálogo local.",
                "2. El sistema cliente invoca el endpoint GET /api/v1/sync/catalog enviando el token de autenticación.",
                "3. El servidor backend valida el tenant_id y la sucursal autorizada del usuario, y recopila las prendas activas, variantes (talla/color), precios y stock conocido.",
                "4. El servidor retorna el paquete de catálogo en formato JSON junto con la marca temporal (timestamp) de sincronización.",
                "5. La aplicación cliente recibe los datos y los almacena localmente: en IndexedDB si es la PWA de Angular, o en la base relacional SQLite si es la app móvil Flutter.",
                "6. El sistema cliente almacena la fecha de descarga y muestra una notificación de catálogo descargado exitosamente."
            ],
            "flujo_alternativo": [
                "3.a. El usuario intenta sincronizar una sucursal no autorizada o perteneciente a otra empresa; el backend deniega la petición con error 403.",
                "5.a. Ocurre una interrupción de red durante la descarga; el sistema cliente detecta el fallo, cancela la transacción local conservando los datos anteriores intactos y notifica al actor para reintentar."
            ],
            "poscondiciones": "El catálogo de prendas y existencias conocidas queda persistido en el dispositivo local, listo para consultas y transacciones sin conexión."
        },
        # CU-07
        {
            "nombre": "CU-07: Consultar Catálogo y Existencias Offline",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al cajero y personal de ventas consultar prendas, precios de venta, tallas, colores y existencias locales conocidas en la terminal de punto de venta cuando el dispositivo carece de conexión a Internet, advirtiendo claramente el estado de vigencia de los datos.",
            "actores": "Cajero / Vendedor.",
            "precondiciones": "La aplicación debe haber completado previamente la descarga del catálogo local (CU-06).",
            "flujo_normal": [
                "1. El actor ingresa al catálogo de productos desde la aplicación web PWA o la aplicación móvil en un momento sin conexión a Internet.",
                "2. El sistema cliente detecta la ausencia de red y conmuta al modo de consulta local.",
                "3. El sistema cliente lee los datos desde el almacén local (IndexedDB en Angular o SQLite en Flutter).",
                "4. El sistema presenta la cuadrícula de productos con sus variantes y precios, mostrando un indicador visual destacado ('Modo Sin Conexión - Los precios y existencias pueden diferir de la base central').",
                "5. El actor aplica filtros por categoría o talla, o introduce un texto de búsqueda.",
                "6. El sistema cliente ejecuta la consulta localmente y actualiza los resultados en pantalla al instante."
            ],
            "flujo_alternativo": [
                "3.a. No existe un catálogo descargado previamente en el almacenamiento local; el sistema muestra un mensaje indicando que se requiere al menos una conexión previa a Internet para inicializar el catálogo desconectado."
            ],
            "poscondiciones": "El usuario accede a la información comercial necesaria para continuar la atención presencial sin detener la operativa por fallas de conectividad."
        },
        # CU-08
        {
            "nombre": "CU-08: Registrar Venta de Contado Offline",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite al cajero o vendedor registrar una venta presencial pagada en efectivo cuando la tienda ha perdido la conexión a Internet, generando un UUID único, deduciendo provisionalmente el stock local y encolando la transacción en la bandeja Outbox (IndexedDB / SQLite) para su sincronización posterior.",
            "actores": "Cajero / Vendedor.",
            "precondiciones": "Catálogo local disponible y venta al contado en efectivo (las ventas offline no admiten procesamiento electrónico diferido).",
            "flujo_normal": [
                "1. El actor ingresa al Punto de Venta (POS) en modo desconectado y selecciona las prendas y variantes solicitadas por el cliente.",
                "2. El sistema calcula el total de la venta aplicando precios locales y solicita confirmar el pago en efectivo.",
                "3. El actor introduce el monto recibido en efectivo y pulsa sobre el botón 'Finalizar Venta Offline'.",
                "4. El sistema genera un identificador universal único (client_operation_id UUID v4).",
                "5. El sistema descuenta provisionalmente las cantidades vendidas en el inventario local (IndexedDB o SQLite) para prevenir sobreventas locales inmediatas.",
                "6. El sistema almacena la transacción en la tabla local de operaciones pendientes con estado PENDING_SYNC.",
                "7. El sistema emite el comprobante de venta local y actualiza el contador de transacciones pendientes en la interfaz."
            ],
            "flujo_alternativo": [
                "5.a. La cantidad solicitada supera las existencias conocidas localmente; el sistema avisa al vendedor indicando disponibilidad insuficiente y solicita ajustar la cantidad."
            ],
            "poscondiciones": "La venta queda registrada de forma duradera en el almacenamiento local del dispositivo (sobreviviendo a reinicios) en espera de conectividad."
        },
        # CU-09
        {
            "nombre": "CU-09: Registrar Reserva de Prendas Offline",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite registrar el apartado temporal de una prenda en la sucursal física sin conexión a Internet, asignando un identificador UUID, bloqueando localmente las unidades seleccionadas y persistiendo la reserva en la bandeja Outbox para su confirmación central al restablecerse la red.",
            "actores": "Cajero / Vendedor.",
            "precondiciones": "Prenda disponible en el catálogo local y datos mínimos de identificación del cliente.",
            "flujo_normal": [
                "1. El actor selecciona la prenda, talla y color a reservar en el mostrador de la tienda sin conexión a Internet.",
                "2. El actor captura los datos básicos del cliente (nombre y teléfono) y pulsa sobre 'Crear Reserva Offline'.",
                "3. El sistema genera un UUID v4 inmutable para la operación.",
                "4. El sistema bloquea localmente la cantidad solicitada en la base de datos IndexedDB/SQLite.",
                "5. El sistema guarda la reserva con estado PENDING_SYNC en la bandeja de operaciones fuera de línea.",
                "6. El sistema genera un comprobante de apartado local con fecha y hora de expiración comercial (48 horas) y confirma la operación al actor."
            ],
            "flujo_alternativo": [
                "4.a. El artículo ya no cuenta con existencias locales para reserva; el sistema notifica al actor que la prenda está agotada localmente."
            ],
            "poscondiciones": "La reserva de prenda queda persistida localmente con estado PENDING_SYNC y las existencias locales quedan bloqueadas preventivamente."
        },
        # CU-23 (Complementario Etapa 1)
        {
            "nombre": "CU-23: Notificar Estado de Conectividad (Semáforo Online/Offline)",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Monitorea continuamente el estado del enlace de red en la aplicación web y móvil, desplegando un componente visual tipo semáforo que informa al usuario si opera en modo en línea o fuera de línea, alertando sobre operaciones encoladas.",
            "actores": "Cajero / Vendedor.",
            "precondiciones": "La aplicación debe estar ejecutándose en el dispositivo del usuario.",
            "flujo_normal": [
                "1. El sistema cliente escucha reactivamente los eventos de red (window online/offline en Web o Connectivity stream en Flutter).",
                "2. Al detectarse pérdida de conectividad, el sistema actualiza de inmediato el indicador visual a color ámbar/rojo con la leyenda 'Sin Conexión'.",
                "3. El sistema comprueba si existen operaciones en cola local y muestra un distintivo numérico (badge) con la cantidad de transacciones pendientes.",
                "4. Al restablecerse la conectividad, el sistema actualiza el semáforo a color verde ('En Línea') y dispara la notificación para sincronización."
            ],
            "flujo_alternativo": [
                "2.a. Ocurre una conexión intermitente de alta latencia; el sistema realiza una comprobación de ping al backend antes de declarar el estado 'En Línea'."
            ],
            "poscondiciones": "El usuario dispone de retroalimentación clara sobre la conectividad y el estado de sus operaciones."
        },
        # CU-24 (Complementario Etapa 1)
        {
            "nombre": "CU-24: Instalar y Registrar Service Worker (PWA)",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Permite registrar el Service Worker y el manifiesto de la aplicación web progresiva (PWA) en navegadores compatibles, almacenando en caché el Application Shell para posibilitar la instalación como app de escritorio y la apertura sin conexión.",
            "actores": "Cliente.",
            "precondiciones": "Navegador compatible con Service Workers y conexión HTTPS activa durante la primera carga.",
            "flujo_normal": [
                "1. El usuario accede a la URL de FashionStore desde su navegador web compatible.",
                "2. El navegador descarga el Web App Manifest y ejecuta el script de registro del Service Worker.",
                "3. El Service Worker intercepta la petición, pre-almacena en caché los archivos estáticos críticos (HTML, scripts compilados de Angular, hojas de estilo e iconos).",
                "4. El navegador detecta la capacidad PWA y despliega en la barra de direcciones el botón 'Instalar Aplicación'.",
                "5. El usuario pulsa sobre 'Instalar Aplicación', creándose un acceso directo nativo en su sistema operativo."
            ],
            "flujo_alternativo": [
                "2.a. El navegador del usuario no soporta Service Workers; el sistema continúa operando como una aplicación web tradicional informando que la experiencia offline no está disponible."
            ],
            "poscondiciones": "La aplicación queda instalada en el dispositivo y su Application Shell queda en caché para arrancar en ausencia de red."
        },
        # CU-25 (Complementario Etapa 1)
        {
            "nombre": "CU-25: Configurar y Migrar Persistencia SQLite Móvil",
            "autor": "Grupo 26: Carlos Rodrigo Carvallo Andreu - Roberto Carlos Cervantes Arancibia",
            "fecha": "24/10/2026",
            "descripcion": "Inicializar y versionar la base de datos local SQLite en la aplicación móvil Flutter, ejecutando migraciones automáticas de esquema para soportar el almacenamiento offline del catálogo de prendas, existencias, clientes locales y cola de operaciones pendientes.",
            "actores": "Cajero / Vendedor.",
            "precondiciones": "La aplicación móvil debe estar instalada y ejecutándose en el dispositivo Android/iOS con permisos de almacenamiento local concedidos.",
            "flujo_normal": [
                "1. El usuario inicia la aplicación móvil por primera vez o tras recibir una actualización de versión.",
                "2. El motor móvil verifica la existencia y versión actual del archivo local de base de datos SQLite.",
                "3. Si la base no existe, ejecuta el script DDL de creación de tablas: catálogo de prendas, variantes, clientes, existencias y cola de outbox.",
                "4. Si existe una versión anterior, ejecuta las migraciones incrementales de esquema sin pérdida de datos locales no sincronizados.",
                "5. El sistema confirma la integridad estructural de la base de datos y habilita los servicios de caché y sincronización local."
            ],
            "flujo_alternativo": [
                "2.a. Fallo por espacio insuficiente en almacenamiento interno: el sistema notifica al usuario el error y solicita liberar espacio antes de continuar operando."
            ],
            "poscondiciones": "Base de datos SQLite local inicializada, migrada y lista para almacenar registros en modo desconectado."
        }
    ]

    for idx, ficha in enumerate(fichas_segundo_parcial, start=1):
        p_cu_title = doc.add_paragraph()
        p_cu_title.paragraph_format.space_before = Pt(14)
        p_cu_title.paragraph_format.space_after = Pt(4)
        p_cu_title.paragraph_format.keep_with_next = True
        run_ct = p_cu_title.add_run(f"2.6.{idx}. Caso de Uso — {ficha['nombre']}")
        run_ct.bold = True
        run_ct.font.name = "Arial"
        run_ct.font.size = Pt(11.5)
        run_ct.font.color.rgb = SLATE_BLUE

        # 1. Encabezado "Diagrama de caso de uso"
        p_diag_lbl = doc.add_paragraph()
        p_diag_lbl.paragraph_format.space_before = Pt(4)
        p_diag_lbl.paragraph_format.space_after = Pt(2)
        p_diag_lbl.paragraph_format.keep_with_next = True
        r_dl = p_diag_lbl.add_run("Diagrama de caso de uso")
        r_dl.bold = True
        r_dl.font.name = "Arial"
        r_dl.font.size = Pt(10.5)
        r_dl.font.color.rgb = DARK_TEXT

        # 2. Imagen individual del diagrama de caso de uso
        cu_id_match = re.search(r"CU-(\d+)", ficha["nombre"])
        if cu_id_match:
            cu_num = cu_id_match.group(1)
            img_path = os.path.join(r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\individual_cus", f"cu{cu_num}_diagram.png")
            if os.path.exists(img_path):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                p_img.paragraph_format.space_before = Pt(2)
                p_img.paragraph_format.space_after = Pt(4)
                p_img.paragraph_format.keep_with_next = True
                run_p_img = p_img.add_run()
                run_p_img.add_picture(img_path, width=Inches(4.8))

        # 3. Encabezado "Descripción de caso de uso"
        p_desc_lbl = doc.add_paragraph()
        p_desc_lbl.paragraph_format.space_before = Pt(4)
        p_desc_lbl.paragraph_format.space_after = Pt(4)
        p_desc_lbl.paragraph_format.keep_with_next = True
        r_dsl = p_desc_lbl.add_run("Descripción de caso de uso")
        r_dsl.bold = True
        r_dsl.font.name = "Arial"
        r_dsl.font.size = Pt(10.5)
        r_dsl.font.color.rgb = DARK_TEXT

        # 4. Tabla de especificación estructurada
        tbl = doc.add_table(rows=9, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(tbl, color="000000", sz="6", val="single")

        col_w0 = Inches(1.5)
        col_w1 = Inches(5.0)

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

                run_lbl = p.add_run(label)
                run_lbl.bold = True
                run_lbl.font.name = "Arial"
                run_lbl.font.size = Pt(9.5)
                run_lbl.font.color.rgb = DARK_TEXT

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

        populate_field_row(0, "Nombre:", ficha["nombre"], is_merged=False)
        populate_field_row(1, "Autor:", ficha["autor"], is_merged=False)
        populate_field_row(2, "Fecha:", ficha["fecha"], is_merged=False)
        populate_field_row(3, "Descripción:", ficha["descripcion"], is_merged=True)
        populate_field_row(4, "Actores:", ficha["actores"], is_merged=True)
        populate_field_row(5, "Precondiciones:", ficha["precondiciones"], is_merged=True)
        populate_field_row(6, "Flujo Normal:", ficha["flujo_normal"], is_merged=True)
        populate_field_row(7, "Flujo Alternativo:", ficha["flujo_alternativo"], is_merged=True)
        populate_field_row(8, "Poscondiciones:", ficha["poscondiciones"], is_merged=True)

        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(4)
        p_after.paragraph_format.space_after = Pt(8)

    # Save to file
    output_filename = "docsegundoparcialSI2.docx"
    doc.save(output_filename)
    print(f"Documento completo regenerado exitosamente como '{output_filename}'.")

if __name__ == "__main__":
    build_entire_document()
