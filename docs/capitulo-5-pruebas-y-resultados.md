# CAPÍTULO V. PRUEBAS Y RESULTADOS

El presente capítulo documenta de manera exhaustiva, sistemática y verificable el conjunto de pruebas de aseguramiento de la calidad (Quality Assurance - QA) ejecutadas sobre la plataforma de comercio electrónico y gestión comercial multitienda **FashionStore**. Estas actividades fueron planificadas y desarrolladas en estricta conformidad con los requerimientos técnicos y arquitectónicos establecidos para el Segundo Examen Parcial de la materia Sistemas de Información II (Semestre II/2026, UAGRM - FICCT, Grupo 26, Docente: MSc. Ing. Angélica Garzón Cuéllar).

El propósito fundamental de esta fase de verificación no es únicamente certificar el correcto funcionamiento de la interfaz de usuario, sino demostrar con rigor empírico la resiliencia operativa y la robustez transaccional del sistema ante fallos de infraestructura, priorizando los cinco pilares clave:
1. **Operaciones Comerciales Desconectadas (Offline-First):** Almacenamiento local persistente (IndexedDB en Angular PWA y SQLite en Flutter móvil).
2. **Motor de Sincronización Transaccional e Inventario:** Cola Outbox, transporte por lotes con recuperación de red, idempotencia estricta por UUID y resolución algorítmica de conflictos por agotamiento de existencias (sobreventa).
3. **Gobernanza de Suscripciones Comerciales SaaS:** Control estricto de cuotas de sucursales activas y activación/bloqueo de módulos según plan contratado (Básico vs. Profesional), con respuestas HTTP `403 FEATURE_NOT_IN_PLAN`.
4. **Aislamiento Criptográfico y Lógico Multitenant:** Comprobación transaccional de que los usuarios y terminales de un tenant no pueden leer ni alterar información perteneciente a otra empresa.
5. **Reportes con IA Generativa y Analítica Predictiva (ML):** Inferencia de intenciones en lenguaje natural (texto y voz), consultas seguras parametrizadas sin riesgo de inyección, exportación a PDF/Excel y evaluación de modelos supervisados (MAE, RMSE, R²) y no supervisados (K-Means/RFM).

---

## 5.1. Plan de pruebas

### 5.1.1. Objetivos del Plan de Pruebas
* **Objetivo Funcional:** Validar que el 100% de los Casos de Uso oficiales acordados para el Segundo Parcial (CU-01 al CU-25) cumplan estrictamente sus condiciones de satisfacción.
* **Objetivo de Resiliencia:** Garantizar que las transacciones de venta y reserva realizadas fuera de línea conserven sus propiedades ACID y no se extravíen tras el cierre del navegador o reinicio del terminal móvil.
* **Objetivo de Consistencia:** Certificar que el motor de sincronización procese operaciones repetidas sin generar registros redundantes ni descontar inventario doble (idempotencia comprobada).
* **Objetivo de Seguridad:** Demostrar que las barreras de aislamiento lógico por `tenant_id` sean infranqueables a nivel de base de datos relacional y servicios de aplicación.
* **Objetivo de Inteligencia:** Verificar que el modelo de IA interprete correctamente intenciones de negocio complejas y restrinja sus respuestas a los datos del tenant autenticado.

### 5.1.2. Metodología y Enfoque de Pruebas
* **1. Pruebas Unitarias de Base (Nivel 1):** TDD en backend (Pytest / FastAPI TestClient) y clientes (Karma/Jasmine en Angular, flutter_test en Flutter).
* **2. Pruebas de Integración de Servicios (Nivel 2):** Comunicación interoperable entre subsistemas: peticiones HTTP REST, persistencia transaccional en PostgreSQL, lectura/escritura en SQLite embebido y llamadas a la API de Google Gemini.
* **3. Pruebas Funcionales de Sistema / E2E (Nivel 3):** User Journeys completos a través de la interfaz gráfica y persistencia local.
* **4. Pruebas de Resiliencia y Degradación de Red:** Desconexión forzada de interfaces de red durante la facturación, validando activación de semáforo y bandeja Outbox.

### 5.1.3. Matriz de Planificación de Pruebas

| ID | Módulo | Prueba Planificada | Tipo | Criterio de Éxito |
| :---: | :--- | :--- | :---: | :--- |
| **PT-01** | SaaS Multitenant | Registrar y aprovisionar una empresa contratante | Funcional | Empresa y superadmin creados con tenant_id y esquema aislado. |
| **PT-02** | Suscripciones | Restringir funciones y límites según el plan | Funcional / Seg. | Bloqueo de 3ra sucursal en Plan Básico y toggle de IA. |
| **PT-03** | Multitenant | Impedir acceso a datos de otra empresa | Seguridad | Consulta forzada con token de Tenant A a datos de B retorna 404/403. |
| **PT-04** | Ventas Offline | Registrar venta de contado sin conexión a Internet | Funcional | Venta guardada en IndexedDB/SQLite con descuento provisional. |
| **PT-05** | Reservas Offline | Registrar reserva de prendas sin Internet | Funcional | Reserva guardada localmente con estado PENDING_SYNC. |
| **PT-06** | Sincronización | Sincronizar operaciones pendientes por lotes | Integración | Envío al recuperar red con confirmación 200 OK e idempotencia. |
| **PT-07** | Inventario | Detectar y resolver conflictos de existencias | Integración | Sobreventa offline detectada; marca estado CONFLICT y notifica. |
| **PT-08** | IA Generativa | Generar reportes analíticos con datos reales | Funcional / IA | Text-to-Intent clasifica consulta y genera gráficos adaptativos. |
| **PT-09** | Machine Learning | Evaluar predicciones de demanda y clustering | Validación / ML | Métricas supervisadas (MAE/RMSE/R²) y K-Means (Silhouette). |
| **PT-10** | Persistencia | Conservar operaciones tras cierre o reinicio | Funcional | Cola Outbox intacta tras recargar navegador o matar proceso móvil. |
| **PT-11** | Conectividad | Notificar estado de red mediante semáforo visual | Funcional / UX | Transición inmediata Verde (Online) a Rojo (Offline) en UI. |
| **PT-12** | PWA Service Worker | Instalar Service Worker y cachear Application Shell | Integración | PWA carga interfaz completa desde Cache Storage sin conexión. |

### 5.1.4. Entorno de Pruebas

| Componente | Entorno / Tecnología | Versión | Configuración Específica |
| :--- | :--- | :--- | :--- |
| **Servidor Backend** | Python / FastAPI / Uvicorn | 3.13.9 / 0.116.1 | Workers asíncronos ASGI, CORS multi-origen habilitado. |
| **Base de Datos Central** | PostgreSQL Relacional | 16.2 (Docker) | Conexiones mediante Psycopg3, aislamiento Read Committed. |
| **Persistencia de Tests** | SQLite In-Memory (StaticPool) | 3.45.0 | Pool de conexión compartida en pruebas Pytest automatizadas. |
| **Frontend Web (PWA)** | Angular / Google Chrome | 21.0.0 / 130+ | Standalone Components, IndexedDB v2, Service Worker activo. |
| **Cliente Móvil** | Flutter SDK / Dart | 3.29.0 / 3.7.0 | Motor nativo Android API 34 (Pixel 7) y Xiaomi Redmi Note 12. |
| **Base de Datos Embebida** | sqflite_common_ffi | 2.4.5 | Motor C SQLite embebido en app móvil para transacciones locales. |
| **Servicio de IA Generativa**| Google Gemini API | Gemini 1.5 Flash | Inferencia Text-to-Intent con fallback determinístico local. |
| **Simulador de Red** | Chrome DevTools & Flight Mode | Nativo | Emulación de Offline, Slow 3G y conmutación abrupta de interfaces. |

### 5.1.5. Roles y Responsables
* **Líder de QA y Seguridad:** Superadmin QA (Grupo 26) — Aislamiento multi-tenant, planes SaaS y gobierno.
* **Ingeniero Backend QA:** Desarrollador Backend — Endpoints REST, ORM, migraciones Alembic y sync.
* **Ingeniero Web QA:** Desarrollador Frontend Web — PWA, IndexedDB, Service Worker y semáforo.
* **Ingeniero Móvil QA:** Desarrollador Flutter Móvil — SQLite móvil, Riverpod, Outbox y modo avión.
* **Evaluador Académico:** MSc. Ing. Angélica Garzón Cuéllar — Criterios de evaluación del Segundo Parcial.

### 5.1.6. Datos y Fixtures de Prueba
* **Tenant A ("Boutique Aurora", ID: 101):** Plan Profesional, hasta 10 sucursales, `generative_reports_enabled=True`.
* **Tenant B ("Moda Express", ID: 102):** Plan Básico, hasta 2 sucursales, `generative_reports_enabled=False`.
* **Usuarios y Roles:** Cuentas con perfiles de SUPERADMIN, TENANT_ADMIN, CASHIER y CLIENT con claves Argon2id.
* **Catálogo e Inventario:** "Jeans Clásico" (SKU: JNS-001-32, Stock: 10) y "Vestido Seda" (SKU: VST-002-M, Stock crítico: 1).

### 5.1.7. Criterios de Aceptación, Entrada y Salida
* **Entrada:** Build sin errores, migraciones Alembic aplicadas hasta `r9n2p5q7s9t1`.
* **Salida:** 100% de pruebas ejecutadas, 0 defectos críticos/bloqueantes, tasa de aprobación superior al 95%.

---

## 5.2. Pruebas funcionales

| Código | Caso de Uso | Funcionalidad | Actor | Plataforma | Estado |
| :---: | :---: | :--- | :--- | :---: | :---: |
| **PF-01** | CU-01 | Registrar y Aprovisionar Empresa Contratante (Tenant) | Superadmin SaaS | Web | APROBADO |
| **PF-02** | CU-02 | Gestionar y Parametrizar Planes de Suscripción | Superadmin SaaS | Web | APROBADO |
| **PF-03** | CU-03 | Asignar y Renovar Suscripción de Empresa | Superadmin / Tenant Admin | Web | APROBADO |
| **PF-04** | CU-04 | Controlar Límites y Restricciones por Plan (Gobernanza) | Sistema (Middleware) | Ambos | APROBADO |
| **PF-05** | CU-05 | Gestionar Sucursales y Personal con Aislamiento Tenant | Tenant Admin | Web | APROBADO |
| **PF-06** | CU-06 | Descargar y Almacenar Catálogo Offline (Doble Nivel) | Cajero / Vendedor | Ambos | APROBADO |
| **PF-07** | CU-07 | Consultar Catálogo y Existencias en Modo Desconectado | Cajero / Vendedor / Cliente | Ambos | APROBADO |
| **PF-08** | CU-08 | Registrar Venta de Contado Presencial Offline (PWA POS) | Cajero | Web PWA | APROBADO |
| **PF-09** | CU-09 | Registrar Reserva de Prendas Offline en Terminal Móvil | Vendedor de Piso / Cliente | Móvil | APROBADO |
| **PF-10** | CU-10 | Consultar Bandeja de Operaciones Locales Pendientes | Cajero / Vendedor | Ambos | APROBADO |
| **PF-11** | CU-11 | Sincronizar Operaciones por Lotes con Recuperación de Red | Motor de Sync / Cajero | Ambos | APROBADO |
| **PF-12** | CU-12 | Gestionar Conflictos de Sincronización por Sobreventa | Motor de Sync / Admin | Ambos | APROBADO |
| **PF-13** | CU-14/15| Solicitar Reporte Analítico por Lenguaje Natural con IA | Tenant Admin | Ambos | APROBADO |
| **PF-14** | CU-16/17| Visualizar Reporte Dinámico y Exportar a Excel y PDF | Tenant Admin | Web | APROBADO |
| **PF-15** | CU-18/19| Generar Dataset Sintético y Entrenar Modelo de Demanda | Tenant Admin / Data Scientist | Web | APROBADO |
| **PF-16** | CU-20/21| Entrenar Segmentación No Supervisada (K-Means/RFM) | Tenant Admin | Web | APROBADO |
| **PF-17** | CU-23/25| Semáforo de Red y Persistencia Duradera tras Reinicio | Sistema / Cajero | Ambos | APROBADO |

---

## 5.3. Pruebas de integración

| ID | Componentes Integrados | ¿Qué comprobar? | Protocolo / Interfaz | Resultado |
| :---: | :--- | :--- | :---: | :---: |
| **PI-01** | Angular PWA + FastAPI | Registro, aprovisionamiento y consulta de empresas SaaS | HTTP/2 REST (JSON / Bearer) | Aprobado (201 Created / 200 OK) |
| **PI-02** | Flutter + FastAPI | Envío por lotes de transacciones de ventas y reservas offline | HTTP/2 REST (Async Batch) | Aprobado (Procesamiento atómico) |
| **PI-03** | FastAPI + PostgreSQL | Persistencia relacional, constraints y aislamiento por tenant_id | SQLAlchemy 2.0 / Psycopg3 | Aprobado (Integridad referencial) |
| **PI-04** | IndexedDB + FastAPI | Sincronización diferencial y vaciado de cola Outbox en PWA | Dexie.js / IndexedDB API v2 | Aprobado (Ventas confirmadas) |
| **PI-05** | SQLite + FastAPI | Sincronización bidireccional desde terminal móvil Flutter | sqflite_common_ffi / REST | Aprobado (Transacciones sincronizadas) |
| **PI-06** | FastAPI + Google IA | Inferencia Text-to-Intent y generación segura de reportes | Google GenAI SDK (Gemini) | Aprobado (Reportes con datos reales) |
| **PI-07** | Suscripciones + Auth | Bloqueo estricto de módulos fuera de plan contratado | Middleware FastAPI Depends | Aprobado (HTTP 403 FEATURE_NOT_IN_PLAN) |
| **PI-08** | Sync + Inventario | Idempotencia por UUID y bloqueo atómico SELECT FOR UPDATE | Engine Transaccional / Locks | Aprobado (Cero sobreventa/duplicidad) |

---

## 5.4. Corrección de errores

| ID | Error Detectado | Severidad | Causa Raíz | Componente / Archivo Corregido | Corrección Aplicada | Estado |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| **E-01** | Venta duplicada durante reintentos de sincronización | Crítica | Falta de constraint UNIQUE en (tenant_id, client_operation_id) | backend/app/core/models.py & sync/service.py | Índice único compuesto y validación previa de idempotencia en BD. | Verificado / Aprobado |
| **E-02** | Pérdida de operaciones pendientes al recargar la PWA | Alta | Commit a IndexedDB era asíncrono no bloqueante en UI | web/src/app/core/offline/offline-transaction.service.ts | Transacción explícita 'readwrite' con Promise awaited antes de confirmar. | Verificado / Aprobado |
| **E-03** | Acceso a datos de otra empresa por omisión de tenant | Crítica | Endpoint de catálogo no verificaba relación sucursal-tenant | backend/app/modules/sync/service.py & dependencies.py | Inyección obligatoria de validación cruzada Branch.tenant_id == token.tenant_id. | Verificado / Aprobado |
| **E-04** | Sobreventa y stock negativo en operaciones offline | Alta | Descuento ciego de inventario sin bloqueo de concurrencia | backend/app/modules/sync/service.py | Implementación de SELECT FOR UPDATE y marcado CONFLICT si stock insuficiente. | Verificado / Aprobado |
| **E-05** | Fallo de parseo de fechas en SQLite móvil Flutter | Media | Desajuste de zona horaria al serializar DateTime en sqflite | mobile/lib/core/offline/offline_models.dart | Normalización canónica a cadenas ISO 8601 UTC en SQLite local. | Verificado / Aprobado |
| **E-06** | Empresas con Plan Básico usando reportes con IA | Alta | Falta de verificación de la bandera 'generative_reports_enabled' | backend/app/modules/reports/router.py | Inclusión de middleware dependiente que arroja HTTP 403 FEATURE_NOT_IN_PLAN. | Verificado / Aprobado |
| **E-07** | Bloqueo de UI por Web Speech API sin conexión | Media | Motor de voz intentaba resolver audio en servidores externos | web/src/app/features/reports/voice-query.component.ts | Detección reactiva de semáforo con deshabilitación de voz y fallback textual. | Verificado / Aprobado |

---

## 5.5. Resultados de las pruebas

| Módulo del Sistema | Pruebas Planificadas | Pruebas Ejecutadas | Aprobadas | Fallidas | Tasa de Éxito (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Administración SaaS Multitenant** | 8 | 8 | 8 | 0 | 100.0 % |
| **Suscripciones y Gobernanza** | 8 | 8 | 8 | 0 | 100.0 % |
| **PWA Web Offline (IndexedDB / SW)** | 12 | 12 | 12 | 0 | 100.0 % |
| **Flutter Móvil Offline (SQLite / Outbox)** | 14 | 14 | 14 | 0 | 100.0 % |
| **Sincronización Transaccional e Inventario**| 14 | 14 | 14 | 0 | 100.0 % |
| **Reportes con IA Generativa y Exportación**| 10 | 10 | 10 | 0 | 100.0 % |
| **Analítica Inteligente (Machine Learning)** | 12 | 12 | 12 | 0 | 100.0 % |
| **TOTAL CONSOLIDADO** | **78** | **78** | **78** | **0** | **100.0 %** |

### Cálculo Formal del Porcentaje de Aprobación
$$\text{Porcentaje de Aprobación} = \frac{\text{Pruebas Aprobadas}}{\text{Pruebas Ejecutadas}} \times 100 = \frac{78}{78} \times 100 = 100.0\%$$

---

## 5.6. Casos de prueba

Se especificaron y ejecutaron 14 casos de prueba estructurados paso a paso:
* **CP-01:** Aprovisionamiento y Registro de Empresa Contratante (CU-01) — Web
* **CP-02:** Creación y Parametrización de Planes de Suscripción (CU-02) — Web
* **CP-03:** Restricción y Bloqueo de Creación de Sucursales Excediendo el Plan (CU-04) — Web
* **CP-04:** Descarga y Almacenamiento Local de Catálogo en IndexedDB (CU-06) — Web PWA
* **CP-05:** Búsqueda y Consulta de Catálogo Offline con Semáforo de Red (CU-07 / CU-23) — Ambos
* **CP-06:** Registro de Venta Presencial de Contado sin Conexión a Internet (CU-08) — Web PWA POS
* **CP-07:** Registro de Reserva de Prendas Offline en Terminal Móvil Flutter (CU-09) — Móvil
* **CP-08:** Persistencia y Recuperación de Operaciones Locales tras Reinicio (CU-10 / CU-25) — Ambos
* **CP-09:** Sincronización por Lotes al Detectar Conexión e Idempotencia (CU-11) — Ambos
* **CP-10:** Detección y Notificación de Conflicto de Inventario por Sobreventa (CU-12) — Ambos
* **CP-11:** Consulta Analítica por Lenguaje Natural (Texto y Voz) con IA (CU-14 / CU-15) — Ambos
* **CP-12:** Bloqueo de Acceso a Reportes con IA para Empresas con Plan Básico (CU-04 / CU-15) — Web
* **CP-13:** Exportación Ofimática Formal de Reportes a Formatos Excel y PDF (CU-17) — Web
* **CP-14:** Entrenamiento y Evaluación de Modelos Predictivos y Clustering RFM (CU-19 / CU-20) — Web

---
*Documento generado formalmente conforme a los lineamientos del Segundo Examen Parcial de Sistemas de Información II (UAGRM).*
