# -*- coding: utf-8 -*-
"""
Script to generate Chapter 1 in docsegundoparcialSI2.docx
Preserving the existing cover page and formatting according to academic standards.
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

def create_document():
    doc = docx.Document('docsegundoparcialSI2_backup.docx')
    
    # Keep only the cover page elements (indices 0 to 23: title, authors table, semester)
    while len(doc._body._element) > 24:
        doc._body._element.remove(doc._body._element[24])
    
    # Configure margins for all sections: Left 3.0 cm, Right 2.5 cm, Top 2.5 cm, Bottom 2.5 cm
    for section in doc.sections:
        section.top_margin = Inches(0.984)     # ~2.5 cm
        section.bottom_margin = Inches(0.984)  # ~2.5 cm
        section.left_margin = Inches(1.181)    # ~3.0 cm
        section.right_margin = Inches(0.984)   # ~2.5 cm
        
        # Configure Header & Footer
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

    # Insert clean page break after cover page
    doc.add_page_break()

    # Color palette
    NAVY_BLUE = RGBColor(27, 54, 93)      # #1B365D - Heading 1 & Titles
    SLATE_BLUE = RGBColor(44, 82, 130)    # #2C5282 - Heading 2
    ACCENT_BLUE = RGBColor(43, 108, 176)  # #2B6CB0 - Heading 3 & Subtitles
    DARK_TEXT = RGBColor(34, 34, 34)      # #222222 - Body text
    MUTED_GRAY = RGBColor(74, 85, 104)    # #4A5568 - Captions / notes

    # Helper functions
    def add_chapter_title(text):
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
    # DOCUMENT STRUCTURE: CAPÍTULO I. ASPECTOS GENERALES
    # =========================================================================
    add_chapter_title("CAPÍTULO I. ASPECTOS GENERALES")

    # -------------------------------------------------------------------------
    # 1.1. INTRODUCCIÓN (Extensión: ~1 Plana Completa / ~550 Palabras)
    # -------------------------------------------------------------------------
    add_h1("1.1. INTRODUCCIÓN")

    intro_p1 = (
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
    add_body_p(intro_p1)

    intro_p2 = (
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
    add_body_p(intro_p2)

    intro_p3 = (
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
    add_body_p(intro_p3)

    intro_p4 = (
        "Como complemento estratégico a la resiliencia operativa, FashionStore trasciende la analítica "
        "convencional de reportes estáticos mediante la integración de Inteligencia Artificial Generativa y "
        "Machine Learning. La plataforma dota a los directivos y gerentes de un motor analítico interactivo "
        "que procesa solicitudes en lenguaje natural formuladas por texto o comandos de voz (micrófono), "
        "construyendo al vuelo consultas estructuradas, visualizaciones gráficas interactivas y reportes "
        "oficiales exportables en formatos PDF y Excel. Simultáneamente, se incorporan modelos predictivos "
        "supervisados para pronosticar la demanda futura de prendas y modelos no supervisados de clusterización "
        "RFM para segmentar clientes, optimizando sustancialmente el abastecimiento y la toma de decisiones."
    )
    add_body_p(intro_p4)

    intro_p5 = (
        "Para gobernar este complejo ecosistema con máximo rigor de ingeniería de software, el equipo "
        "adopta la metodología ICONIX, un proceso ágil y dirigido por casos de uso que optimiza el modelado "
        "UML mediante la regla 80/20. A través de diagramas de robustez (Boundary-Controller-Entity) y su "
        "posterior refinamiento en diagramas de secuencia y clases, se asegura una trazabilidad transparente "
        "y verificable entre los requisitos del negocio, la arquitectura cloud-edge y las pruebas automatizadas. "
        "El presente Capítulo I establece los aspectos generales, problemáticas, objetivos rectores, "
        "justificaciones interdisciplinarias y el alcance detallado de todos los módulos que conforman la "
        "plataforma FashionStore SaaS."
    )
    add_body_p(intro_p5)

    # -------------------------------------------------------------------------
    # 1.2. PLANTEAMIENTO DEL PROBLEMA
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # 1.3. OBJETIVOS DEL PROYECTO
    # -------------------------------------------------------------------------
    add_h1("1.3. OBJETIVOS DEL PROYECTO")

    # 1.3.1. Objetivo General (Completamente Nuevo, Profesional y en Contexto)
    add_h2("1.3.1. Objetivo General")
    obj_general = (
        "Diseñar, desarrollar y evolucionar la plataforma integral de comercio electrónico de prendas de vestir "
        "FashionStore hacia un ecosistema tecnológico escalable bajo el modelo Software as a Service (SaaS) "
        "Multi-tenant, dotado de resiliencia operativa Offline-First (PWA y móvil) con sincronización "
        "transaccional consistente, y capacidades avanzadas de Inteligencia Artificial Generativa y Analítica "
        "Predictiva (Machine Learning) para la optimización comercial, gobernado bajo la metodología dirigida "
        "por casos de uso ICONIX y validado mediante pruebas automatizadas rigurosas."
    )
    add_body_p(obj_general)

    # 1.3.2. Objetivos Específicos (Estructurados Formalmente por Ejes de Ingeniería)
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

    # -------------------------------------------------------------------------
    # 1.4. JUSTIFICACIÓN
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # 1.5. ALCANCE Y LIMITACIONES
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # 1.6. METODOLOGÍA DE DESARROLLO ICONIX
    # -------------------------------------------------------------------------
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

    # Save to file
    output_filename = "docsegundoparcialSI2.docx"
    doc.save(output_filename)
    print(f"Documento guardado exitosamente como '{output_filename}'.")

if __name__ == "__main__":
    create_document()
