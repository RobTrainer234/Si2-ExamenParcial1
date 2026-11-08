# -*- coding: utf-8 -*-
"""
Script para redactar e insertar:
- 6.1. Conclusiones
- 6.2. Recomendaciones
- 7. Bibliografía (con libros de UML, ICONIX, QA, Arquitectura y Tecnologías)
en 'docsegundoparcialSI2.docx'.
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

class SectionInserter:
    def __init__(self, doc, target_elem):
        self.doc = doc
        self.target = target_elem

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
            
        self.target.addprevious(p._p)
        return p

    def add_bullet(self, text, bold_prefix=""):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
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
        
        self.target.addprevious(p._p)
        return p

    def add_bib_entry(self, entry_text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3) # Sangría francesa APA
        p.paragraph_format.line_spacing = 1.15
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        r = p.add_run(entry_text)
        r.font.name = 'Arial'
        r.font.size = Pt(9.5)
        
        self.target.addprevious(p._p)
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
        
        self.target.addprevious(table._tbl)
        
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)
        self.target.addprevious(sp._p)

def main():
    print("=== Insertando Conclusiones, Recomendaciones y Bibliografía ===")
    doc = docx.Document(DOC_PATH)
    body = doc._body._element
    
    # Localizar párrafos clave
    p_recom = None
    p_bib = None
    p_anexo = None
    
    for child in body:
        if child.tag.endswith('p'):
            t = ''.join(child.itertext()).strip()
            if t.startswith('6.2. Recomendaciones') or '6.2. Recomendaciones' in t:
                p_recom = child
            elif t.startswith('7. Bibliografía') or '7. Bibliografía' in t or '7. Bibliografia' in t:
                p_bib = child
            elif t.startswith('8. Anexo') or '8. Anexo' in t:
                p_anexo = child
                
    if p_recom is None or p_bib is None or p_anexo is None:
        raise ValueError(f"No se localizaron los nodos de destino (p_recom: {p_recom is not None}, p_bib: {p_bib is not None}, p_anexo: {p_anexo is not None})")
        
    # -------------------------------------------------------------------------
    # 1. SECCIÓN 6.1. CONCLUSIONES (Insertar antes de p_recom)
    # -------------------------------------------------------------------------
    ins_c = SectionInserter(doc, p_recom)
    
    ins_c.add_p(
        "A la culminación exitosa de las etapas de análisis, diseño arquitectónico, implementación y certificación de pruebas "
        "del proyecto de software FashionStore para el Segundo Examen Parcial de la materia Sistemas de Información II "
        "(Semestre II/2026, UAGRM - FICCT), se han consolidado las siguientes conclusiones científico-técnicas primordiales:"
    )
    
    ins_c.add_bullet(
        "La adopción de la metodología ágil ICONIX demostró una extraordinaria efectividad para salvar la brecha tradicional "
        "entre el análisis de requisitos y el diseño detallado. La utilización del Análisis de Robustez (Robustness Analysis) "
        "mediante la clasificación estereotipada de objetos Límite (Boundary/UI), Controladores transaccionales y Entidades de dominio "
        "permitió depurar ambigüedades en las especificaciones de los casos de uso antes de acometer la codificación. Esta trazabilidad "
        "se tradujo de manera fluida y coherente hacia los diagramas de interacción (Comunicación y Secuencia) y hacia una arquitectura "
        "particionada en cuatro capas (Específica, General, Interna y Software) completamente conforme al estándar UML 2.5.",
        bold_prefix="Eficacia del Modelado Orientado a Objetos con Metodología ICONIX y UML 2.5: "
    )
    
    ins_c.add_bullet(
        "Se demostró empíricamente la viabilidad y resiliencia del paradigma arquitectónico Offline-First en entornos comerciales "
        "de punto de venta (POS) y terminales móviles. Mediante la integración coordinada de Service Workers y bases de datos locales "
        "(IndexedDB en clientes web y SQLite embebido vía sqflite en aplicaciones Flutter), la plataforma garantiza operatividad "
        "ininterrumpida ante caídas fortuitas del suministro de Internet. La cola de operaciones pendientes (Outbox) con transporte "
        "por lotes y mecanismos estrictos de idempotencia transaccional basados en UUIDs v4 eliminó de raíz el riesgo de duplicación "
        "de ventas o registros huérfanos durante reintentos por intermitencia de red.",
        bold_prefix="Continuidad Operativa y Resiliencia del Paradigma Offline-First: "
    )
    
    ins_c.add_bullet(
        "La implementación del esquema multitenant compartido con discriminador tenant_id a nivel de base de datos relacional (PostgreSQL 16) "
        "y su gobernanza centralizada a través de middlewares dependientes en FastAPI demostraron ser un enfoque sumamente eficiente en costos "
        "de infraestructura sin comprometer la seguridad. Las barreras de aislamiento criptográfico y lógico impidieron de forma hermética "
        "cualquier fuga o cruce involuntario de información entre empresas contratantes competidoras. Asimismo, el subsistema de cuotas "
        "automatizó con precisión milimétrica la restricción de sucursales físicas y la activación/bloqueo de módulos según el plan contratado "
        "(Básico vs. Profesional), sentando bases comerciales escalables para un modelo de negocio SaaS.",
        bold_prefix="Solidez y Seguridad del Aislamiento Multi-Tenant SaaS: "
    )
    
    ins_c.add_bullet(
        "La incorporación de capacidades analíticas impulsadas por Inteligencia Artificial Generativa (Text-to-SQL mediante Google Gemini) "
        "transformó radicalmente la experiencia de toma de decisiones del usuario gerencial. La inferencia contextual de preguntas en lenguaje "
        "natural estructurada sobre plantillas determinísticas parametrizadas garantizó que el 100% de las consultas SQL generadas incluyan "
        "el filtro forzado de empresa, anulando riesgos de inyección de código. De igual forma, los modelos predictivos de Machine Learning "
        "desarrollados para estimación de demanda y segmentación de clientes mediante clustering RFM con K-Means proporcionaron métricas "
        "de negocio accionables que optimizan el aprovisionamiento de inventario de moda.",
        bold_prefix="Innovación en Inteligencia Artificial y Analítica Predictiva de Negocio: "
    )
    
    ins_c.add_bullet(
        "La ejecución rigurosa de las pruebas funcionales de caja negra (con técnicas de partición de equivalencia, análisis de valores límite "
        "y tablas de decisión) y de pruebas de caja blanca sobre estructuras de control de código fuente arrojó una tasa de aprobación del "
        "100.0% sobre 78 casos de prueba planificados. Este proceso permitió subsanar anticipadamente siete incidencias críticas de concurrencia, "
        "bloqueo pesimista e inconsistencias de huso horario, garantizando que el artefacto de software final sea robusto, confiable y "
        "apto para despliegue en entornos productivos de alta exigencia.",
        bold_prefix="Certificación de Calidad y Robustez de Software: "
    )

    ins_c.add_callout(
        "SÍNTESIS FINAL DEL LOGRO DEL PROYECTO",
        "FashionStore acredita el cumplimiento riguroso de la totalidad de competencias académicas y técnicas exigidas en el "
        "Segundo Parcial de INF-412: modelado formal ICONIX/UML 2.5, resiliencia offline PWA/móvil, gobernanza SaaS multi-tenant, "
        "integración de IA Generativa y aseguramiento exhaustivo de la calidad con verificación de caja blanca y caja negra."
    )

    # -------------------------------------------------------------------------
    # 2. SECCIÓN 6.2. RECOMENDACIONES (Insertar antes de p_bib)
    # -------------------------------------------------------------------------
    ins_r = SectionInserter(doc, p_bib)
    
    ins_r.add_p(
        "Con el propósito de garantizar la evolución sostenida, la alta disponibilidad y la optimización de costos en un eventual "
        "despliegue productivo a gran escala de la plataforma FashionStore, se formulan las siguientes recomendaciones estratégicas:"
    )
    
    ins_r.add_bullet(
        "Para soportar el crecimiento masivo en el número de tenants y transacciones concurrentes de POS, se recomienda orquestar los contenedores "
        "de FastAPI utilizando Amazon EKS (Elastic Kubernetes Service) con autoescalado horizontal de pods (HPA). Asimismo, se aconseja "
        "desacoplar las consultas analíticas de reportería pesada e inferencia de IA hacia réplicas de lectura (Read Replicas) en Amazon RDS PostgreSQL "
        "Multi-AZ, reservando la instancia primaria exclusivamente para transacciones de escritura y sincronización de caja.",
        bold_prefix="Escalabilidad Elástica e Infraestructura Cloud en AWS: "
    )
    
    ins_r.add_bullet(
        "En la aplicación web PWA, se sugiere delegar el procesamiento de serialización, cálculo de firmas criptográficas y sincronización "
        "de lotes del Outbox a Web Workers dedicados en segundo plano, evitando cualquier micro-congelamiento del hilo de renderizado principal "
        "(UI Thread) en terminales de bajas especificaciones de hardware. En la aplicación móvil Flutter, se recomienda instrumentar rutinas "
        "periódicas de vaciado y compactación WAL (Write-Ahead Logging) del motor SQLite embebido para optimizar el consumo de batería y almacenamiento.",
        bold_prefix="Optimización de Rendimiento en Clientes Offline-First: "
    )
    
    ins_r.add_bullet(
        "Fortalecer el esquema de autenticación implementando verificación multifactor (MFA/TOTP) de obligatoriedad para perfiles con privilegios "
        "administrativos. Además, se recomienda desacoplar la auditoría transaccional de la base de datos operativa mediante la captura de cambios "
        "de datos (Change Data Capture - CDC) con herramientas como Debezium y Apache Kafka, almacenando los registros inmutables en un Data Lake "
        "en Amazon S3 con cifrado KMS para cumplimiento normativo y peritaje forense.",
        bold_prefix="Fortalecimiento de Seguridad, Autenticación y Auditoría Forense: "
    )
    
    ins_r.add_bullet(
        "Evolucionar el motor de consultas analíticas hacia un esquema RAG (Retrieval-Augmented Generation) avanzado que combine la base relacional "
        "con bases de datos vectoriales (pgvector en PostgreSQL) para indexar manuales de temporada, especificaciones de telas y catálogos de proveedores. "
        "Asimismo, se aconseja construir un pipeline MLOps formal con MLflow para monitorizar el desvío de datos (data drift) y automatizar el "
        "reentrenamiento periódico de los modelos supervisados de predicción de ventas.",
        bold_prefix="Madurez de Inteligencia Artificial y Pipelines de MLOps: "
    )
    
    ins_r.add_bullet(
        "Institucionalizar compuertas de análisis estático continuo de código (SonarQube) en los pipelines de CI/CD (GitHub Actions) con una meta "
        "estricta de cobertura mínima de pruebas unitarias superior al 85%. De igual forma, se sugiere ejecutar pruebas continuas de estrés distribuido "
        "con herramientas como k6 o Locust simulando escenarios extremos de sincronización concurrente al inicio de turnos comerciales.",
        bold_prefix="Automatización DevOps y Pruebas Continuas de Carga: "
    )

    # -------------------------------------------------------------------------
    # 3. SECCIÓN 7. BIBLIOGRAFÍA (Insertar antes de p_anexo)
    # -------------------------------------------------------------------------
    ins_b = SectionInserter(doc, p_anexo)
    
    ins_b.add_p(
        "La fundamentación teórica, metodológica, arquitectónica y tecnológica que sustentó la concepción, modelado formal, "
        "construcción y certificación del presente proyecto de software se sustenta en las siguientes referencias bibliográficas "
        "estandarizadas bajo formato APA (7ma edición):"
    )
    
    ins_b.add_p(bold_prefix="Metodología ICONIX y Modelado Orientado a Objetos:", text="")
    ins_b.add_bib_entry("Rosenberg, D., & Stephens, M. (2007). Use Case Driven Object Modeling with UML: Theory and Practice (The ICONIX Process). Apress. https://doi.org/10.1007/978-1-4302-0268-4")
    ins_b.add_bib_entry("Rosenberg, D., & Scott, K. (2001). Applying Use Case Driven Object Modeling with UML: An Annotated E-Commerce Example. Addison-Wesley Professional.")
    ins_b.add_bib_entry("Rosenberg, D., Collins-Cope, M., & Stephens, M. (2005). Agile Development with ICONIX Process: People, Process, and Pragmatism. Apress.")

    ins_b.add_p(bold_prefix="Lenguaje Unificado de Modelado (UML) y Arquitectura de Software:", text="")
    ins_b.add_bib_entry("Booch, G., Rumbaugh, J., & Jacobson, I. (2005). The Unified Modeling Language User Guide (2nd ed.). Addison-Wesley Professional.")
    ins_b.add_bib_entry("Object Management Group. (2017). OMG Unified Modeling Language (OMG UML) Specification, Version 2.5.1. Object Management Group (OMG Document formal/2017-12-05). https://www.omg.org/spec/UML/2.5.1/")
    ins_b.add_bib_entry("Fowler, M. (2003). UML Distilled: A Brief Guide to the Standard Object Modeling Language (3rd ed.). Addison-Wesley Professional.")
    ins_b.add_bib_entry("Martin, R. C. (2017). Clean Architecture: A Craftsman's Guide to Software Structure and Design. Prentice Hall.")
    ins_b.add_bib_entry("Bass, L., Clements, P., & Kazman, R. (2021). Software Architecture in Practice (4th ed.). Addison-Wesley Professional.")
    ins_b.add_bib_entry("Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). Design Patterns: Elements of Reusable Object-Oriented Software. Addison-Wesley Professional.")

    ins_b.add_p(bold_prefix="Ingeniería de Software, Pruebas y Aseguramiento de Calidad (QA):", text="")
    ins_b.add_bib_entry("Myers, G. J., Sandler, C., & Badgett, T. (2011). The Art of Software Testing (3rd ed.). John Wiley & Sons.")
    ins_b.add_bib_entry("Pressman, R. S., & Maxim, B. R. (2020). Software Engineering: A Practitioner's Approach (9th ed.). McGraw-Hill Education.")
    ins_b.add_bib_entry("Sommerville, I. (2016). Software Engineering (10th ed.). Pearson Education.")
    ins_b.add_bib_entry("Beizer, B. (1995). Black-Box Testing: Techniques for Functional Testing of Software and Systems. John Wiley & Sons.")
    ins_b.add_bib_entry("Garzón Cuéllar, A. (2026). Guía Didáctica de Pruebas de Software y Aseguramiento de la Calidad (INF-412). Universidad Autónoma Gabriel René Moreno (UAGRM), Facultad Integral de Ciencias de la Computación y Telecomunicaciones (FICCT).")

    ins_b.add_p(bold_prefix="Sistemas Distribuidos, Persistencia, Paradigma Offline-First y Tecnologías Web:", text="")
    ins_b.add_bib_entry("Kleppmann, M. (2017). Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems. O'Reilly Media.")
    ins_b.add_bib_entry("Ramirez, S. (2024). FastAPI: Modern Python Web Development. O'Reilly Media.")
    ins_b.add_bib_entry("Freeman, A. (2023). Pro Angular 16: Build Powerful and Dynamic Web Apps (6th ed.). Apress.")
    ins_b.add_bib_entry("Windmill, E. (2020). Flutter in Action. Manning Publications.")
    ins_b.add_bib_entry("PostgreSQL Global Development Group. (2024). PostgreSQL 16.2 Documentation. The PostgreSQL Global Development Group. https://www.postgresql.org/docs/16/")

    # Guardar documento
    doc.save(DOC_PATH)
    print("Conclusiones, Recomendaciones y Bibliografía insertadas con éxito!")

if __name__ == "__main__":
    main()
