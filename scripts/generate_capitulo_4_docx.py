import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level):
    h = doc.add_heading(level=level)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(text)
    run.font.name = 'Arial'
    run.bold = True
    
    if level == 1:
        run.font.size = Pt(15)
        run.font.color.rgb = RGBColor(0, 51, 102) # Azul institucional
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
    elif level == 2:
        run.font.size = Pt(12.5)
        run.font.color.rgb = RGBColor(30, 30, 30)
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
    elif level == 3:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(60, 60, 60)
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
    return h

def add_body_p(doc, text="", bold_prefix="", italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Arial'
        r_b.font.size = Pt(10.5)
        r_b.bold = True
        
    if text:
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(10.5)
        r.italic = italic
    return p

def add_bullet_p(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3.5)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Arial'
        r_b.font.size = Pt(10.5)
        r_b.bold = True
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(10.5)
    return p

def add_figure(doc, img_path, caption_text, width=Inches(5.8)):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(3)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=width)
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run(caption_text)
        r_cap.font.name = 'Arial'
        r_cap.font.size = Pt(9)
        r_cap.font.color.rgb = RGBColor(90, 90, 90)
        r_cap.italic = True
    else:
        add_body_p(doc, f"[Aviso: Archivo de imagen no encontrado en {img_path}]")

def add_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F6F9")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    cp = cell.paragraphs[0]
    cp.paragraph_format.space_after = Pt(0)
    cp.paragraph_format.line_spacing = 1.05
    crun = cp.add_run(code_text)
    crun.font.name = 'Consolas'
    crun.font.size = Pt(9)
    crun.font.color.rgb = RGBColor(30, 40, 50)
    
    p_post = doc.add_paragraph()
    p_post.paragraph_format.space_after = Pt(4)

def format_table(tbl, col_widths, headers, data):
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tbl.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], "003366")
        set_cell_margins(hdr_cells[i], top=90, bottom=90, left=110, right=110)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Arial'
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.bold = True
            
    for row_idx, row_data in enumerate(data):
        row_cells = tbl.add_row().cells
        bg_color = "FFFFFF" if row_idx % 2 == 0 else "F7FAFC"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value)
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=60, bottom=60, left=90, right=90)
            p = row_cells[col_idx].paragraphs[0]
            for r in p.runs:
                r.font.name = 'Arial'
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(40, 40, 40)
                
    for row in tbl.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def build_document():
    doc = docx.Document()
    
    # Configurar márgenes estándar (0.98 pulgadas = 2.5 cm)
    for section in doc.sections:
        section.top_margin = Inches(0.98)
        section.bottom_margin = Inches(0.98)
        section.left_margin = Inches(0.98)
        section.right_margin = Inches(0.98)
        
        # Encabezado institucional conforme a formato de examen universitario
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.paragraph_format.space_after = Pt(12)
        hrun = hp.add_run("EXAMEN 2          SISTEMAS 2 – S2-2026          MSc. Ing. Angélica Garzón Cuéllar")
        hrun.font.name = 'Arial'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(120, 120, 120)
        
    print("Iniciando generación exhaustiva de Capítulo IV en Word...")
    
    # Título Principal
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(14)
    r_title = p_title.add_run("CAPÍTULO IV. DESARROLLO E IMPLEMENTACIÓN")
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(17)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(0, 51, 102)

    add_body_p(doc, "El presente capítulo describe de manera técnica, rigurosa y exhaustiva el proceso de desarrollo, implementación y despliegue físico de la plataforma de comercio electrónico y gestión comercial multitienda FashionStore. Los componentes aquí documentados corresponden a los resultados consolidados de la Etapa 1 del proyecto (Casos de Uso CU-01 al CU-07 y CU-23 al CU-25), abarcando la selección de herramientas tecnológicas, la arquitectura en capas y en la nube (AWS), la implementación de bases de datos relacionales y desconectadas, el desarrollo detallado de cada módulo funcional con sus diagramas dinámicos y la integración interoperable entre sus componentes heterogéneos.")

    # ==========================================
    # 4.1. Herramientas y tecnologías utilizadas
    # ==========================================
    add_styled_heading(doc, "4.1. Herramientas y tecnologías utilizadas", level=1)
    
    add_body_p(doc, "Para la materialización técnica de la plataforma se seleccionó un conjunto de herramientas y tecnologías de grado de producción, orientadas a garantizar alta concurrencia, seguridad criptográfica, aislamiento lógico multi-inquilino (multi-tenancy) y capacidad operativa en escenarios de conectividad nula o intermitente (offline-first).")

    add_styled_heading(doc, "4.1.1. Ecosistema de Backend (API REST Asíncrona)", level=2)
    add_bullet_p(doc, " Lenguaje base optimizado que incorpora mejoras notables en el recolector de basura, optimización de tipos y soporte asíncrono nativo para operaciones I/O concurrentes.", bold_prefix="Python 3.13:")
    add_bullet_p(doc, " Framework web asíncrono de alto rendimiento basado en el estándar ASGI y OpenAPI (Swagger). Proporciona inyección de dependencias modular y serialización estricta de esquemas.", bold_prefix="FastAPI 0.116.1:")
    add_bullet_p(doc, " Servidor de aplicaciones web asíncrono de grado industrial basado en uvloop y httptools, capaz de gestionar miles de peticiones de sincronización en paralelo.", bold_prefix="Uvicorn 0.35.0:")
    add_bullet_p(doc, " Mapeador Objeto-Relacional (ORM) bajo el paradigma Data Mapper con sintaxis declarativa moderna 2.0, garantizando sesiones transaccionales ACID y consultas fuertemente tipadas.", bold_prefix="SQLAlchemy 2.0.43:")
    add_bullet_p(doc, " Herramienta de control de versiones y migraciones de esquemas relacionales, asegurando cambios de base de datos idempotentes y aditivos sin tiempo de inactividad.", bold_prefix="Alembic 1.16.4:")
    add_bullet_p(doc, " Driver de conexión nativo y moderno para PostgreSQL con soporte avanzado de pipelines binarios y multiplexación de conexiones.", bold_prefix="Psycopg 3.2.9 (psycopg[binary]):")
    add_bullet_p(doc, " Algoritmo criptográfico de derivación de claves ganador de la Password Hashing Competition (PHC), altamente resistente a ataques por hardware acelerado (GPU y ASIC).", bold_prefix="Argon2-cffi 25.1.0:")
    add_bullet_p(doc, " Librería criptográfica para el firmado simétrico y validación de tokens de acceso JSON Web Tokens (JWT) mediante HMAC-SHA256 (HS256).", bold_prefix="Python-Jose 3.5.0:")
    add_bullet_p(doc, " Validación rigurosa de entradas y salidas en el borde de la API mediante contratos de datos y configuración tipada mediante variables de entorno.", bold_prefix="Pydantic v2 & Pydantic-Settings 2.10.1:")
    add_bullet_p(doc, " Motores de exportación formal de documentos administrativos en formato PDF estructurado y hojas de cálculo Excel.", bold_prefix="ReportLab 4.4.3 & OpenPyXL 3.1.5:")

    add_styled_heading(doc, "4.1.2. Ecosistema de Frontend Web (Progressive Web App - PWA)", level=2)
    add_bullet_p(doc, " Implementado bajo la arquitectura de Standalone Components (eliminación de NgModules), lo que optimiza el tamaño de los paquetes de distribución (bundles) y habilita carga perezosa (lazy loading).", bold_prefix="Angular 21 (v21.0.0):")
    add_bullet_p(doc, " Paradigma de reactividad fina que prescinde de ciclos de detección de cambios pesados, combinado con RxJS 7.8.2 para la gestión de flujos de eventos asíncronos.", bold_prefix="Angular Signals & RxJS:")
    add_bullet_p(doc, " Módulo de Service Worker que intercepta peticiones de red y cachea el Application Shell (HTML, CSS, JS, fuentes tipográficas) mediante políticas performance y freshness.", bold_prefix="@angular/service-worker 21.0.0:")
    add_bullet_p(doc, " Motor transaccional relacional embebido en el navegador cliente para el almacenamiento persistente de prendas, variantes y existencias de stock.", bold_prefix="IndexedDB API:")
    add_bullet_p(doc, " Framework para pruebas de extremo a extremo (E2E) simulando escenarios de desconexión de red y validación del comportamiento PWA.", bold_prefix="Playwright 1.55.0 & Vitest 4.1.11:")

    add_styled_heading(doc, "4.1.3. Ecosistema de Aplicación Móvil (Terminal Desconectado)", level=2)
    add_bullet_p(doc, " Framework multiplataforma de compilación nativa para Android e iOS con lenguaje Dart fuertemente tipado.", bold_prefix="Flutter (Dart SDK >=3.12.0 <4.0.0):")
    add_bullet_p(doc, " Gestor de estado reactivo y contenedor de inyección de dependencias declarativo desacoplado del árbol de widgets.", bold_prefix="Flutter Riverpod 3.0.0:")
    add_bullet_p(doc, " Motor de base de datos relacional embebida SQLite local para Android/iOS con ejecución atómica de consultas ACID.", bold_prefix="sqflite 2.4.5 & sqflite_common_ffi:")
    add_bullet_p(doc, " Monitoreo reactivo en tiempo real de los cambios en interfaces de red (Wi-Fi, datos móviles, desconexión) que alimenta el componente Semáforo.", bold_prefix="connectivity_plus 7.3.2:")

    add_styled_heading(doc, "4.1.4. Sistemas Gestores de Bases de Datos y Almacenamiento", level=2)
    add_bullet_p(doc, " Motor relacional centralizado con particionamiento lógico multi-tenant, índices compuestos B-Tree y garantías ACID completas.", bold_prefix="PostgreSQL 16 (Nube Central):")
    add_bullet_p(doc, " Motores desconectados embebidos en el cliente móvil y en el navegador para la réplica transaccional del catálogo.", bold_prefix="SQLite 3 & IndexedDB:")
    add_bullet_p(doc, " Almacenamiento de objetos duradero (99.999999999%) para activos fotográficos de prendas textiles y comprobantes.", bold_prefix="Amazon S3 (Simple Storage Service):")

    add_styled_heading(doc, "4.1.5. Herramientas de Análisis, Diseño y Calidad", level=2)
    add_bullet_p(doc, " Herramienta CASE oficial para la construcción de los artefactos ICONIX (Modelo de Dominio, Diagramas de Robustez, Diagramas de Comunicación y Diagramas de Secuencia UML).", bold_prefix="Sparx Systems Enterprise Architect 16:")
    add_bullet_p(doc, " Linter y formateador ultrarrápido de código Python que asegura estándares PEP 8 y buenas prácticas de seguridad.", bold_prefix="Ruff 0.12.9 & Flutter Lints 6.0:")
    add_bullet_p(doc, " Contenedores para la reproducibilidad de entornos de base de datos, APIs y proxies de desarrollo.", bold_prefix="Docker & Docker Compose:")

    # Tabla 4.1
    p_tbl = doc.add_paragraph()
    p_tbl.paragraph_format.space_before = Pt(8)
    p_tbl.paragraph_format.space_after = Pt(2)
    r_t = p_tbl.add_run("Tabla 4.1. Resumen de la pila tecnológica implementada (FashionStore)")
    r_t.font.name = 'Arial'
    r_t.font.size = Pt(9)
    r_t.italic = True
    
    tbl1 = doc.add_table(rows=1, cols=4)
    headers1 = ["Capa / Subsistema", "Tecnología Principal", "Versión", "Rol en el Sistema"]
    data1 = [
        ["Backend API", "FastAPI / Python", "0.116.1 / 3.13", "API REST Asíncrona, Multi-tenant y Sincronización"],
        ["Servidor ASGI", "Uvicorn", "0.35.0", "Servidor de aplicaciones concurrente uvloop"],
        ["ORM", "SQLAlchemy", "2.0.43", "Persistencia relacional y sesiones ACID"],
        ["Base de Datos Nube", "PostgreSQL", "16.x", "SGBD central con aislamiento por tenant_id"],
        ["Base de Datos Móvil", "SQLite (sqflite)", "2.4.5", "Persistencia local para terminal desconectado"],
        ["Almacén Web", "IndexedDB", "W3C API", "Almacenamiento transaccional local en navegador"],
        ["Frontend Web", "Angular", "21.0.0", "PWA Standalone, Signals y catálogo offline"],
        ["Frontend Móvil", "Flutter / Dart", "3.x / >=3.12", "Terminal móvil de ventas y sincronización"],
        ["Infraestructura Nube", "AWS (ECS, RDS, S3)", "Cloud Native", "Despliegue escalable y seguro multi-inquilino"],
        ["Modelado UML", "Enterprise Architect", "16.1", "Artefactos de análisis y diseño ICONIX"]
    ]
    format_table(tbl1, [Inches(1.5), Inches(1.6), Inches(1.1), Inches(2.0)], headers1, data1)

    # ==========================================
    # 4.2. Diseño de la arquitectura del sistema
    # ==========================================
    add_styled_heading(doc, "4.2. Diseño de la arquitectura del sistema", level=1)
    
    add_body_p(doc, "La arquitectura del sistema FashionStore responde al patrón de Monolito Modular Multi-tenant con Clientes Híbridos Offline-First, diseñado para desacoplar responsabilidades, garantizar aislamiento estricto de datos y soportar la continuidad operativa de las tiendas comerciales ante fallos en la conectividad a Internet.")

    # 4.2.1. Diagrama de Paquetes
    add_styled_heading(doc, "4.2.1. Diagrama de Paquetes — Arquitectura en Capas (UML 2.5)", level=2)
    add_body_p(doc, "El Diagrama de Paquetes es uno de los diagramas estructurales normados en UML 2.5, utilizado para definir los distintos paquetes a nivel lógico que forman parte de la aplicación y las relaciones de dependencia entre ellos, con el objetivo de maximizar la cohesión y minimizar el acoplamiento. Siguiendo las directrices metodológicas de la asignatura, el diagrama organiza las capas como paquetes contenedores que agrupan a sus respectivos subpaquetes funcionales:")

    img_paquetes = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\diagrama_paquetes_diapositivas_exacto.png'
    add_figure(doc, img_paquetes, "Figura 4.1. Diagrama de Paquetes - Arquitectura en Capas (UML 2.5)", width=Inches(6.0))

    add_body_p(doc, "1. Capa de presentación (Paquete Contenedor Superior):", bold_prefix="")
    add_bullet_p(doc, " Aplicación cliente en Angular 21 orientada a vendedores y compradores, con Service Worker y catálogo en IndexedDB.", bold_prefix="Interfaz web PWA:")
    add_bullet_p(doc, " Aplicación nativa en Flutter para vendedores en piso de venta, conectada a SQLite local.", bold_prefix="Interfaz móvil:")
    add_bullet_p(doc, " Panel web administrativo para alta de empresas SaaS (Tenants), planes, sucursales y personal.", bold_prefix="Interfaz admin:")

    add_body_p(doc, "2. Capa de Lógica de Negocio (Paquete Contenedor Intermedio):", bold_prefix="")
    add_bullet_p(doc, " Aprovisionamiento de empresas, validación de subdominios y aislamiento lógico (CU-01).", bold_prefix="Subsistema de gestión SaaS y empresas:")
    add_bullet_p(doc, " Parametrización y control de contratos comerciales y vigencias (CU-02, CU-03).", bold_prefix="Subsistema de planes y suscripciones:")
    add_bullet_p(doc, " Gobernanza transaccional de topes de sucursales y usuarios por plan (CU-04).", bold_prefix="Subsistema de control de límites de plan:")
    add_bullet_p(doc, " Configuración de tiendas físicas y asignación de personal comercial acotado al tenant (CU-05).", bold_prefix="Subsistema de gestión de sucursales:")
    add_bullet_p(doc, " Taxonomía de prendas, variantes de color/talla y stock multitienda (CU-06, CU-07).", bold_prefix="Subsistema de catálogo y existencias:")
    add_bullet_p(doc, " Sincronización diferencial, colas de contingencia y semáforo de red (CU-23, CU-24, CU-25).", bold_prefix="Subsistema de sincronización offline:")

    add_body_p(doc, "3. Paquetes de Base de Datos y Persistencia (Almacenamiento):", bold_prefix="")
    add_bullet_p(doc, " Base de datos relacional principal alojada en la nube con discriminador tenant_id.", bold_prefix="Base de datos central PostgreSQL:")
    add_bullet_p(doc, " Motor SQLite embebido en dispositivos móviles para soporte transaccional sin internet.", bold_prefix="Base de datos embebida SQLite móvil:")
    add_bullet_p(doc, " Base de datos transaccional en el navegador web para la persistencia del catálogo.", bold_prefix="Almacén local IndexedDB PWA:")

    add_body_p(doc, "4. Dependencias entre Paquetes (Flechas Discontinuas):", bold_prefix="")
    add_bullet_p(doc, " La capa de presentación requiere de los servicios, validaciones y contratos provistos por la lógica de negocio para operar.", bold_prefix="Presentación -> Lógica de Negocio:")
    add_bullet_p(doc, " Los motores de persistencia se estructuran y ejecutan en función de las entidades dictadas por la lógica de negocio.", bold_prefix="Bases de Datos -> Lógica de Negocio:")

    # 4.2.2. Diagrama de Despliegue
    add_styled_heading(doc, "4.2.2. Diagrama de Despliegue — Topología Cloud AWS Multi-Tenant (UML 2.5)", level=2)
    add_body_p(doc, "El Diagrama de Despliegue describe la topología física, los contenedores Docker y los servicios gestionados en la nube de Amazon Web Services (AWS) que albergan los artefactos de software del sistema, garantizando alta disponibilidad, aislamiento multi-inquilino y seguridad perimetral:")

    img_despliegue = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\diagrama_despliegue_aws_exacto_ejemplo.png'
    add_figure(doc, img_despliegue, "Figura 4.2. Diagrama de Despliegue - AWS Cloud Multi-Tenant (UML 2.5)", width=Inches(6.0))

    add_body_p(doc, "1. Nodos Cliente («device»):", bold_prefix="")
    add_bullet_p(doc, " Terminal de ventas en tienda física con la app Flutter y base SQLite embebida.", bold_prefix="Dispositivo Movil (Android / iOS):")
    add_bullet_p(doc, " Estaciones de trabajo que ejecutan el entorno «executionEnvironment» Navegador Web y descargan el artefacto compilado Frontend Web Angular 21 (SPA Build / Dist).", bold_prefix="Dispositivo del Usuario (PC / Laptop / Tablet):")

    add_body_p(doc, "2. Nodo de Red e Ingreso AWS:", bold_prefix="")
    add_bullet_p(doc, " Canal público seguro sobre el cual viaja el tráfico HTTPS y WebSockets (WSS).", bold_prefix="Internet (HTTPS / WSS / TLS):")
    add_bullet_p(doc, " Punto de entrada central en AWS con terminación TLS 443 y reenvío Reverse Proxy (HTTP/WSS) hacia el clúster interno.", bold_prefix="AWS Application Load Balancer (ALB):")

    add_body_p(doc, "3. Cómputo en Clúster Docker («node» AWS EC2 / ECS Cluster):", bold_prefix="")
    add_bullet_p(doc, " API REST modular construida en FastAPI / Python 3.13 con sesiones transaccionales.", bold_prefix="Contenedor Backend:")
    add_bullet_p(doc, " Microservicio de aprendizaje automático para predicción de demanda y recomendaciones.", bold_prefix="Contenedor Servicio IA:")
    add_bullet_p(doc, " Enlace de red interna de alta velocidad entre ambos microservicios.", bold_prefix="REST Inter-service:")

    add_body_p(doc, "4. Persistencia, Seguridad y Servicios Externos AWS:", bold_prefix="")
    add_bullet_p(doc, " Clúster de base de datos relacional multi-tenant en subred privada aislada (puerto TCP 5432).", bold_prefix="Amazon RDS PostgreSQL 16:")
    add_bullet_p(doc, " Cifrado de registros de auditoría y gestión de secretos criptográficos.", bold_prefix="AWS KMS:")
    add_bullet_p(doc, " Almacén de objetos para imágenes de prendas textiles y respaldos automatizados.", bold_prefix="Amazon S3 Bucket:")
    add_bullet_p(doc, " Pasarela de pagos externa para cobro recurrente de suscripciones vía webhooks HTTPS.", bold_prefix="Stripe API Cloud:")
    add_bullet_p(doc, " Proveedor en la nube para el despacho de correos transaccionales vía SMTP 587.", bold_prefix="Brevo Cloud API:")

    # Tabla 4.2
    p_tbl2 = doc.add_paragraph()
    p_tbl2.paragraph_format.space_before = Pt(8)
    p_tbl2.paragraph_format.space_after = Pt(2)
    r_t2 = p_tbl2.add_run("Tabla 4.2. Matriz de conectividad, puertos y protocolos en AWS")
    r_t2.font.name = 'Arial'
    r_t2.font.size = Pt(9)
    r_t2.italic = True
    
    tbl2 = doc.add_table(rows=1, cols=4)
    headers2 = ["Origen", "Destino", "Protocolo / Puerto", "Propósito de la Comunicación"]
    data2 = [
        ["Dispositivo Móvil", "Internet", "HTTPS / WSS : 443", "Tráfico seguro de sincronización de catálogo"],
        ["Dispositivo Usuario", "Internet", "HTTPS : 443", "Descarga de SPA Angular y consumo de API"],
        ["Internet", "AWS ALB", "TLS : 443", "Ingreso perimetral cifrado con certificado SSL"],
        ["AWS ALB", "Contenedor Backend", "HTTP : 8000 / WSS", "Reenvío proxy interno hacia la aplicación ASGI"],
        ["Contenedor Backend", "Contenedor IA", "HTTP : 8001 (REST)", "Invocación síncrona de modelos analíticos"],
        ["Contenedor Backend", "Amazon RDS Postgres", "TCP : 5432", "Consultas y mutaciones relacionales SQLAlchemy"],
        ["Contenedor Backend", "AWS KMS", "HTTPS : 443", "Cifrado y descifrado de bitácoras con AWS SDK"],
        ["Contenedor Backend", "Amazon S3", "HTTPS : 443", "Subida y lectura de imágenes de prendas textiles"],
        ["Contenedor Backend", "Stripe API Cloud", "HTTPS : 443", "Cobro de suscripciones y recepción de webhooks"],
        ["Contenedor Backend", "Brevo Cloud API", "SMTP : 587", "Despacho de correos de confirmación y bienvenida"]
    ]
    format_table(tbl2, [Inches(1.5), Inches(1.5), Inches(1.4), Inches(1.8)], headers2, data2)

    add_styled_heading(doc, "4.2.3. Arquitectura Multi-tenant SaaS y Gobernanza de Inquilinos", level=2)
    add_body_p(doc, "La plataforma implementa el modelo Shared Database, Shared Schema con columna discriminadora tenant_id. Cada tabla perteneciente a la lógica de negocio (sucursales, usuarios, prendas, existencias, bitácoras) contiene obligatoriamente la clave foránea tenant_id. La inyección de dependencias get_current_tenant en FastAPI valida en cada petición HTTP la pertenencia del usuario al tenant activo a partir del token JWT firmado. Para prevenir la fuga de información (data leakage), cualquier petición a un identificador perteneciente a otra empresa retorna un código 404 Not Found no enumerable.")

    add_styled_heading(doc, "4.2.4. Arquitectura Offline-First de Doble Nivel con Semáforo de Red", level=2)
    add_body_p(doc, "Para asegurar la operación continua en tiendas con enlaces inestables, se implementó un mecanismo dual de contingencia:")
    add_bullet_p(doc, " Mediante Service Worker y la base de datos local IndexedDB, el vendedor puede consultar prendas y verificar disponibilidad estimada sin internet.", bold_prefix="Nivel Web PWA:")
    add_bullet_p(doc, " Mediante el motor SQLite embebido (fashionstore_local.db), el vendedor realiza búsquedas de productos por código de barras de manera ultrarrápida.", bold_prefix="Nivel Móvil Flutter:")
    add_bullet_p(doc, " Componente reactivo presente en ambas interfaces que alerta al usuario mediante colores: Verde (Online sincronizado), Amarillo (Sincronizando deltas) y Rojo (Desconectado operando sobre almacenamiento local).", bold_prefix="Semáforo de Conectividad:")

    # ==========================================
    # 4.3. Implementación de la base de datos
    # ==========================================
    add_styled_heading(doc, "4.3. Implementación de la base de datos", level=1)
    
    add_body_p(doc, "La persistencia de FashionStore se fundamenta en un modelo conceptual riguroso que refleja los objetos de la vida real del dominio textil y retail, traducido a un esquema físico relacional en PostgreSQL 16 y réplicas locales ligeras.")

    add_styled_heading(doc, "4.3.1. Modelo Conceptual y de Dominio de la Base de Datos (Etapa 1)", level=2)
    add_body_p(doc, "Siguiendo las reglas de la metodología ICONIX, el Modelo de Dominio contiene únicamente las 12 entidades principales correspondientes a la Etapa 1, excluyendo deliberadamente las entidades de etapas posteriores (como ventas, carritos y facturación):")

    img_dominio = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\modelo_dominio_etapa1_final.png'
    add_figure(doc, img_dominio, "Figura 4.3. Modelo de Dominio UML - Entidades y Multiplicidades (Etapa 1)", width=Inches(6.0))

    # Tabla 4.3: Entidades del Modelo de Dominio
    p_tbl3 = doc.add_paragraph()
    p_tbl3.paragraph_format.space_before = Pt(8)
    p_tbl3.paragraph_format.space_after = Pt(2)
    r_t3 = p_tbl3.add_run("Tabla 4.3. Entidades del Modelo de Dominio de la Base de Datos (Etapa 1)")
    r_t3.font.name = 'Arial'
    r_t3.font.size = Pt(9)
    r_t3.italic = True
    
    tbl3 = doc.add_table(rows=1, cols=4)
    headers3 = ["Entidad", "Propósito en el Dominio", "Multiplicidad / Relación Clave", "Atributos Principales"]
    data3 = [
        ["Tenant", "Empresa cliente contratante del servicio SaaS", "1 a N con Suscripciones, Sucursales y Usuarios", "id, codigo_tenant, nombre, subdominio, nit_ruc, estado"],
        ["SubscriptionPlan", "Definición del paquete comercial contratado", "1 a N con Suscripciones de Tenants", "id, codigo_plan, nombre, precio, max_sucursales, max_usuarios"],
        ["Subscription", "Contrato de vigencia temporal de una empresa", "N a 1 con Tenant y con SubscriptionPlan", "id, tenant_id, plan_id, fecha_inicio, fecha_fin, estado"],
        ["Sucursal", "Tienda física o punto de venta comercial", "N a 1 con Tenant, 1 a N con Inventario y Usuarios", "id, tenant_id, nombre, direccion, ciudad, telefono, is_active"],
        ["Usuario", "Operador, vendedor o administrador", "N a 1 con Tenant, N a 1 con Sucursal y Rol", "id, tenant_id, branch_id, email, password_hash, rol_id, is_active"],
        ["Rol", "Perfil de permisos y privilegios RBAC", "1 a N con Usuarios", "id, codigo, nombre, descripcion"],
        ["Categoria", "Taxonomía de prendas de vestir", "N a 1 con Tenant, 1 a N con Productos", "id, tenant_id, nombre, descripcion, is_active"],
        ["Producto", "Prenda base del catálogo textil", "N a 1 con Categoria, 1 a N con Variantes", "id, tenant_id, category_id, codigo, nombre, precio_base"],
        ["VarianteProducto", "Unidad tangible comercial (talla/color)", "N a 1 con Producto, 1 a N con Inventario", "id, tenant_id, product_id, sku, talla, color, precio_ajustado"],
        ["Inventario", "Existencias físicas y disponibles en tienda", "N a 1 con Sucursal y con VarianteProducto", "id, tenant_id, branch_id, variant_id, stock_fisico, reservado"],
        ["SyncOperation", "Registro de mutaciones locales desconectadas", "N a 1 con Tenant y con Usuario", "id, tenant_id, user_id, device_id, operacion, payload, estado"],
        ["Bitacora", "Pista de auditoría inmutable de eventos", "N a 1 con Tenant", "id, tenant_id, user_id, accion, detalle, ip_origen, created_at"]
    ]
    format_table(tbl3, [Inches(1.4), Inches(1.8), Inches(1.6), Inches(1.6)], headers3, data3)

    add_styled_heading(doc, "4.3.2. Restricciones de Integridad e Índices Compuestos", level=2)
    add_body_p(doc, "Para garantizar que dos empresas clientes distintas puedan registrar el mismo código de SKU o el mismo nombre de sucursal sin colisionar, el esquema físico aplica índices únicos compuestos por tenant_id:")

    sql_code = """-- 1. Unicidad global del subdominio de acceso SaaS
CREATE UNIQUE INDEX uq_tenants_subdominio ON tenants(LOWER(subdominio));

-- 2. Restricción de SKU único POR EMPRESA (Multi-tenant)
CREATE UNIQUE INDEX uq_product_variants_tenant_sku ON product_variants(tenant_id, LOWER(sku));

-- 3. Restricción de un solo registro de inventario por variante y sucursal
CREATE UNIQUE INDEX uq_inventory_tenant_branch_variant ON inventory(tenant_id, branch_id, variant_id);

-- 4. Restricción de integridad matemática del stock
ALTER TABLE inventory ADD CONSTRAINT chk_inventory_stock_logic 
    CHECK (stock_fisico >= 0 AND stock_reservado >= 0 AND stock_disponible = (stock_fisico - stock_reservado));"""
    add_code_block(doc, sql_code)

    add_styled_heading(doc, "4.3.3. Base de Datos Embebida Desconectada (SQLite e IndexedDB)", level=2)
    add_body_p(doc, "En los dispositivos cliente, la persistencia local replica de forma desnormalizada las entidades de catálogo mediante las tablas locales local_products, local_variants y local_inventory, junto con la tabla sync_metadata que almacena la marca temporal last_sync_timestamp para soportar sincronizaciones incrementales eficientes.")

    # ==========================================
    # 4.4. Desarrollo de los módulos del sistema
    # ==========================================
    add_styled_heading(doc, "4.4. Desarrollo de los módulos del sistema (Etapa 1)", level=1)
    add_body_p(doc, "A continuación se documentan de forma integral los 10 módulos funcionales correspondientes a la Etapa 1. Para cada módulo se expone su objetivo técnico, sus componentes de backend, componentes de interfaz de usuario (web y móvil), reglas de negocio implementadas, su Diagrama de Secuencia UML 2.5 y la captura de pantalla de su respectiva interfaz gráfica:")

    seq_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\secuencia_etapa1'
    ui_dir = r'C:\ProyectoSi2_TiendaRopa\docs\ui-screens\etapa-1'

    modulos_completos = [
        {
            "num": "4.4.1",
            "titulo": "Módulo 1: Registro y Aprovisionamiento de Empresa Contratante (CU-01)",
            "cu": "CU-01",
            "obj": "Permitir la incorporación automatizada de nuevas tiendas de ropa bajo el modelo SaaS, garantizando el aislamiento inmediato de sus datos.",
            "be": "Router en app.modules.subscriptions.router (POST /api/v1/saas/tenants) y servicio transaccional TenantService.register_tenant().",
            "fe": "Formulario web en Angular con validación reactiva asíncrona de disponibilidad de subdominio mediante Signals.",
            "logica": "Verifica la disponibilidad global del subdominio, inserta el Tenant en estado ACTIVO, crea la suscripción inicial al plan seleccionado, registra la cuenta del Administrador inicial con hash Argon2 y genera un registro de auditoría inmutable.",
            "seq_img": os.path.join(seq_dir, "sd_CU-01_Registrar_Empresa_Con.png"),
            "seq_cap": "Figura 4.4. Diagrama de Secuencia UML 2.5 - CU-01 Registrar Empresa Contratante",
            "ui_img": os.path.join(ui_dir, "CU-01_Registrar_Empresa_SaaS.png"),
            "ui_cap": "Figura 4.5. Interfaz Gráfica de Usuario - Registro de Empresa SaaS (CU-01)"
        },
        {
            "num": "4.4.2",
            "titulo": "Módulo 2: Gestión de Planes de Suscripción (CU-02)",
            "cu": "CU-02",
            "obj": "Parametrizar las ofertas comerciales del SaaS estableciendo cuotas duras y funcionalidades por nivel de servicio.",
            "be": "Endpoints GET, POST y PUT en /api/v1/saas/plans y servicio de aplicación SubscriptionService.",
            "fe": "Panel administrativo en Angular para la configuración visual de planes y cuotas.",
            "logica": "Controla topes duros: max_sucursales (ej. 2 en Básico, 10 en Pro), max_usuarios y la bandera permite_offline, impidiendo planes con cuotas negativas o códigos duplicados.",
            "seq_img": os.path.join(seq_dir, "sd_CU-02_Gestionar_Planes_de_S.png"),
            "seq_cap": "Figura 4.6. Diagrama de Secuencia UML 2.5 - CU-02 Gestionar Planes de Suscripción",
            "ui_img": os.path.join(ui_dir, "CU-02_Gestionar_Planes_Suscripcion.png"),
            "ui_cap": "Figura 4.7. Interfaz Gráfica de Usuario - Gestión de Planes de Suscripción (CU-02)"
        },
        {
            "num": "4.4.3",
            "titulo": "Módulo 3: Asignación y Renovación de Suscripciones (CU-03)",
            "cu": "CU-03",
            "obj": "Gestionar el ciclo de vida contractual de las empresas clientes y vigencias temporales de servicio.",
            "be": "Endpoints POST /api/v1/saas/subscriptions/assign y POST /api/v1/saas/subscriptions/renew.",
            "fe": "Vistas de facturación, estado contractual y renovación en el portal administrativo Angular.",
            "logica": "Calcula vigencias mensuales (30 días), valida estado de pagos y gestiona transiciones de estado contractual (ACTIVA, VENCIDA, SUSPENDIDA), revocando acceso si la suscripción expira.",
            "seq_img": os.path.join(seq_dir, "sd_CU-03_Asignar_y_Renovar_Sus.png"),
            "seq_cap": "Figura 4.8. Diagrama de Secuencia UML 2.5 - CU-03 Asignar y Renovar Suscripción",
            "ui_img": os.path.join(ui_dir, "CU-03_Asignar_Renovar_Suscripcion.png"),
            "ui_cap": "Figura 4.9. Interfaz Gráfica de Usuario - Suscripciones y Renovaciones (CU-03)"
        },
        {
            "num": "4.4.4",
            "titulo": "Módulo 4: Gobernanza y Control Transaccional de Límites por Plan (CU-04)",
            "cu": "CU-04",
            "obj": "Impedir la sobreutilización de recursos contratados bloqueando la creación de sucursales o usuarios excedentes.",
            "be": "Middleware y dependencias de validación verify_plan_branch_limit() y verify_plan_user_limit() en FastAPI.",
            "fe": "Mensajes de alerta visual, banners de advertencia de cuota y modal interactivo de upgrade de plan en Angular.",
            "logica": "Ejecuta SELECT COUNT(*) de sucursales activas del tenant. Si el total iguala al tope del plan contratado, interrumpe la transacción con código HTTP 403 Forbidden.",
            "seq_img": os.path.join(seq_dir, "sd_CU-04_Controlar_Límites_y_R.png"),
            "seq_cap": "Figura 4.10. Diagrama de Secuencia UML 2.5 - CU-04 Control de Límites por Plan",
            "ui_img": os.path.join(ui_dir, "CU-04_Control_Limites_Restricciones_Plan.png"),
            "ui_cap": "Figura 4.11. Interfaz Gráfica de Usuario - Control de Restricciones y Cuotas (CU-04)"
        },
        {
            "num": "4.4.5",
            "titulo": "Módulo 5: Gestión de Sucursales y Personal por Tenant (CU-05)",
            "cu": "CU-05",
            "obj": "Administrar la red física de puntos de venta y el personal autorizado por tienda de forma confinada.",
            "be": "Routers app.modules.locations.router y app.modules.users.router con filtros obligatorios de tenant.",
            "fe": "Módulos CRUD en Angular con selectores de sucursales, roles RBAC y tablas paginadas.",
            "logica": "Garantiza que usuarios y sucursales pertenezcan estrictamente al mismo tenant_id. Aplica borrado lógico (is_active = false) preservando integridad referencial histórica.",
            "seq_img": os.path.join(seq_dir, "sd_CU-05_Gestionar_Sucursales_.png"),
            "seq_cap": "Figura 4.12. Diagrama de Secuencia UML 2.5 - CU-05 Gestión de Sucursales y Empleados",
            "ui_img": os.path.join(ui_dir, "CU-05_Gestionar_Sucursales_Empleados_Tenant.png"),
            "ui_cap": "Figura 4.13. Interfaz Gráfica de Usuario - Administración de Tiendas y Personal (CU-05)"
        },
        {
            "num": "4.4.6",
            "titulo": "Módulo 6: Descarga y Almacenamiento de Catálogo Offline (CU-06)",
            "cu": "CU-06",
            "obj": "Descargar una copia estructurada y optimizada del catálogo de la tienda hacia el almacenamiento cliente local.",
            "be": "Endpoint GET /api/v1/sync/catalog con soporte de compresión gzip y filtrado por sucursal.",
            "fe": "Servicios OfflineCatalogService (Angular) y SyncCatalogService (Flutter Riverpod).",
            "logica": "Extrae categorías, prendas, variantes y existencias de la sucursal del usuario autenticado, serializándolas en un payload JSON e insertándolas en batch en SQLite o IndexedDB.",
            "seq_img": os.path.join(seq_dir, "sd_CU-06_Descargar_y_Almacenar.png"),
            "seq_cap": "Figura 4.14. Diagrama de Secuencia UML 2.5 - CU-06 Descarga de Catálogo Offline",
            "ui_img": os.path.join(ui_dir, "CU-06_Descargar_Almacenar_Catalogo_Offline.png"),
            "ui_cap": "Figura 4.15. Interfaz Gráfica de Usuario - Descarga y Caché de Catálogo (CU-06)"
        },
        {
            "num": "4.4.7",
            "titulo": "Módulo 7: Consulta de Catálogo y Existencias Offline (CU-07)",
            "cu": "CU-07",
            "obj": "Permitir la búsqueda instantánea de prendas en tienda sin requerir acceso a internet.",
            "be": "No requiere backend en tiempo de ejecución desconectado; opera 100% autónomo.",
            "fe": "Componente de búsqueda reactiva en Angular PWA y pantalla de catálogo textil en Flutter.",
            "logica": "Ejecuta consultas locales sobre IndexedDB o SQLite con tiempos de respuesta inferiores a 50 ms por SKU, nombre, talla o color, mostrando stock disponible estimado.",
            "seq_img": os.path.join(seq_dir, "sd_CU-07_Consultar_Catálogo_y_.png"),
            "seq_cap": "Figura 4.16. Diagrama de Secuencia UML 2.5 - CU-07 Consulta de Catálogo Offline",
            "ui_img": os.path.join(ui_dir, "CU-07_Consultar_Catalogo_Existencias_Offline.png"),
            "ui_cap": "Figura 4.17. Interfaz Gráfica de Usuario - Búsqueda de Productos Offline (CU-07)"
        },
        {
            "num": "4.4.8",
            "titulo": "Módulo 8: Semáforo y Notificación de Estado de Conectividad (CU-23)",
            "cu": "CU-23",
            "obj": "Monitorear la salud del enlace de red y orientar al operador sobre el modo operativo activo.",
            "be": "Endpoint liviano de sondeo ultrarrápido GET /api/v1/system/healthcheck con respuesta pong.",
            "fe": "Componente visual Semáforo presente de forma ubicua en el header de Angular y Flutter.",
            "logica": "Cambia dinámicamente: Verde (Online conectado y sincronizado), Amarillo (Sincronizando deltas en progreso) y Rojo (Desconectado operando sobre base local).",
            "seq_img": os.path.join(seq_dir, "sd_CU-23_Notificar_Estado_de_C.png"),
            "seq_cap": "Figura 4.18. Diagrama de Secuencia UML 2.5 - CU-23 Notificación de Conectividad (Semáforo)",
            "ui_img": os.path.join(ui_dir, "CU-23_Notificar_Estado_Conectividad.png"),
            "ui_cap": "Figura 4.19. Interfaz Gráfica de Usuario - Indicador Semáforo de Red (CU-23)"
        },
        {
            "num": "4.4.9",
            "titulo": "Módulo 9: Instalación y Registro de Service Worker PWA (CU-24)",
            "cu": "CU-24",
            "obj": "Habilitar la ejecución de la aplicación web en modo de escritorio instalable sin red.",
            "be": "Configuración de ngsw-config.json y manifiesto web manifest.webmanifest.",
            "fe": "Lógica de registro en Angular via provideServiceWorker('ngsw-worker.js') y modal de instalación PWA.",
            "logica": "Cachea archivos HTML, JS, CSS y activos multimedia mediante políticas de prefetching, permitiendo abrir la web app aún con la red desconectada.",
            "seq_img": os.path.join(seq_dir, "sd_CU-24_Instalar_y_Registrar_.png"),
            "seq_cap": "Figura 4.20. Diagrama de Secuencia UML 2.5 - CU-24 Registro de Service Worker PWA",
            "ui_img": os.path.join(ui_dir, "CU-24_Instalar_Service_Worker_PWA.png"),
            "ui_cap": "Figura 4.21. Interfaz Gráfica de Usuario - Instalación PWA y Service Worker (CU-24)"
        },
        {
            "num": "4.4.10",
            "titulo": "Módulo 10: Persistencia y Migración SQLite Móvil (CU-25)",
            "cu": "CU-25",
            "obj": "Asegurar la creación e inicialización determinista de la base relacional local en terminales móviles.",
            "be": "Servicio de inicialización y migración en mobile/lib/core/offline/offline_database.dart.",
            "fe": "Manejadores onCreate y onUpgrade en sqflite con verificación de versión de esquema.",
            "logica": "Crea las tablas locales con claves e índices secundarios sobre SKU y códigos de barras para acelerar la búsqueda por escáner en piso de venta.",
            "seq_img": os.path.join(seq_dir, "sd_CU-25_Configurar_y_Migrar_P.png"),
            "seq_cap": "Figura 4.22. Diagrama de Secuencia UML 2.5 - CU-25 Configuración SQLite Móvil",
            "ui_img": os.path.join(ui_dir, "CU-25_Persistencia_SQLite_Movil.png"),
            "ui_cap": "Figura 4.23. Interfaz Gráfica de Usuario - Persistencia Local SQLite (CU-25)"
        }
    ]

    for mod in modulos_completos:
        add_styled_heading(doc, f"{mod['num']}. {mod['titulo']}", level=2)
        add_body_p(doc, mod['obj'], bold_prefix="Objetivo: ")
        add_body_p(doc, mod['be'], bold_prefix="Componentes Backend: ")
        add_body_p(doc, mod['fe'], bold_prefix="Componentes Frontend / Móvil: ")
        add_body_p(doc, mod['logica'], bold_prefix="Lógica de Negocio y Reglas: ")
        
        # Insertar Diagrama de Secuencia
        add_figure(doc, mod['seq_img'], mod['seq_cap'], width=Inches(5.7))
        
        # Insertar Pantalla de Interfaz Gráfica
        add_figure(doc, mod['ui_img'], mod['ui_cap'], width=Inches(5.5))

    # ==========================================
    # 4.5. Integración de componentes
    # ==========================================
    add_styled_heading(doc, "4.5. Integración de componentes", level=1)
    add_body_p(doc, "La integración entre los diversos subsistemas heterogéneos de FashionStore se rige por contratos de interfaz normalizados y protocolos de comunicación desacoplados, asegurando interoperabilidad transparente entre el frontend web Angular, la aplicación móvil Flutter y la API central FastAPI:")

    add_styled_heading(doc, "4.5.1. Integración Frontend Web (Angular) <-> Backend (FastAPI)", level=2)
    add_body_p(doc, "La aplicación Angular se comunica con la API mediante un Interceptor HTTP funcional que inyecta automáticamente las cabeceras Authorization: Bearer <JWT> y X-Tenant-ID: <UUID_Tenant>. Las respuestas de error son procesadas de manera centralizada mediante un servicio de notificaciones reactivo que alerta al usuario sobre fallos de autenticación (401), excesos de cuota de plan (403) o recursos inexistentes (404).")

    add_styled_heading(doc, "4.5.2. Integración Móvil (Flutter) <-> Backend (FastAPI)", level=2)
    add_body_p(doc, "La aplicación Flutter encapsula la comunicación REST dentro de la clase ApiClient, configurada con límites de tiempo de espera (timeouts) estrictos de 8 segundos. Si la red no responde dentro de dicho margen, el cliente cancela la solicitud de red y conmuta de forma transparente hacia la base de datos SQLite embebida, garantizando que la interfaz del vendedor jamás se bloquee.")

    add_styled_heading(doc, "4.5.3. Mecanismo de Sincronización Diferencial (Delta Sync)", level=2)
    add_body_p(doc, "Para minimizar el consumo de datos móviles, el endpoint de sincronización (/api/v1/sync/catalog) admite el parámetro opcional since_timestamp. Cuando se provee, la consulta en PostgreSQL filtra únicamente los registros cuyo updated_at sea superior a dicha fecha, reduciendo el tamaño del payload transferido en un 95% y completando las actualizaciones de inventario en menos de 2 segundos.")

    add_styled_heading(doc, "4.5.4. Pipeline de Auditoría y Trazabilidad Transaccional", level=2)
    add_body_p(doc, "Un middleware asíncrono en FastAPI intercepta todas las operaciones que mutan el estado del sistema (POST, PUT, DELETE). Tras confirmarse la transacción en la base de datos central, extrae automáticamente el tenant_id, el user_id, la ruta del endpoint accedido y la dirección IP de origen, persistiendo un registro inmutable en la tabla audit_logs para asegurar la trazabilidad y la no repudiación de eventos.")

    # Tabla 4.4: Matriz de Integración de Componentes
    p_tbl4 = doc.add_paragraph()
    p_tbl4.paragraph_format.space_before = Pt(8)
    p_tbl4.paragraph_format.space_after = Pt(2)
    r_t4 = p_tbl4.add_run("Tabla 4.4. Matriz de integración y protocolos de comunicación entre subsistemas")
    r_t4.font.name = 'Arial'
    r_t4.font.size = Pt(9)
    r_t4.italic = True
    
    tbl4 = doc.add_table(rows=1, cols=4)
    headers4 = ["Subsistema Origen", "Subsistema Destino", "Canal / Protocolo", "Formato de Datos e Intercambio"]
    data4 = [
        ["Angular 21 (PWA)", "FastAPI Backend", "HTTPS REST / Bearer JWT", "JSON (Esquemas Pydantic / TypeScript Interfaces)"],
        ["Flutter Móvil", "FastAPI Backend", "HTTPS REST / Bearer JWT", "JSON Gzip comprimido (Catálogo y Deltas)"],
        ["FastAPI Backend", "PostgreSQL 16", "TCP 5432 / SQLAlchemy ORM", "Sesiones ACID con pool asíncrono Psycopg 3"],
        ["Flutter Móvil", "SQLite Embebido", "IPC / sqflite binario", "Sentencias SQL parametrizadas locales"],
        ["Angular 21 (PWA)", "IndexedDB Navegador", "DOM W3C IDBRequest API", "Objetos JavaScript indexados por clave SKU"],
        ["FastAPI Backend", "AWS KMS", "HTTPS / AWS Boto3 SDK", "Payloads binarios cifrados con envelopes AES-256"],
        ["FastAPI Backend", "Amazon S3", "HTTPS / AWS Boto3 SDK", "Archivos de imagen PNG/JPG y dumps de respaldo"],
        ["FastAPI Backend", "Brevo Cloud", "SMTP : 587 / TLS", "Plantillas HTML transaccionales de correo"]
    ]
    format_table(tbl4, [Inches(1.5), Inches(1.5), Inches(1.6), Inches(1.8)], headers4, data4)

    # Guardar en las dos ubicaciones
    out_path_docs = r'C:\ProyectoSi2_TiendaRopa\docs\Capitulo_IV_Desarrollo_e_Implementacion.docx'
    out_path_root = r'C:\ProyectoSi2_TiendaRopa\Capitulo_IV_Desarrollo_e_Implementacion.docx'
    
    doc.save(out_path_docs)
    doc.save(out_path_root)
    print(f"\nDocumento Word completo generado con éxito en:")
    print(f"  1. {out_path_docs}")
    print(f"  2. {out_path_root}")

if __name__ == '__main__':
    build_document()
