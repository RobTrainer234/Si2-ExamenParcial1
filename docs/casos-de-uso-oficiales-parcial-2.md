# Matriz Oficial de Casos de Uso — Segundo Parcial (ICONIX)

> **Documento de Referencia Oficial**: Esta matriz define los 29 Casos de Uso (CU-01 al CU-29) acordados formalmente para el Segundo Parcial de Sistemas de Información 2 (S2-2026), distribuidos en las 3 Etapas de entrega bajo la metodología ICONIX.

---

## 📋 Matriz Detallada de Casos de Uso por Plataforma

| ID | Caso de Uso | Actor Principal | Plataforma | Etapa Asignada | Justificación en el Examen |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **CU-01** | **Registrar Empresa Contratante (Tenant)** | Superadmin SaaS | 🌐 Web | **Etapa 1** | Portal central de administración de la plataforma SaaS (Backoffice). |
| **CU-02** | **Gestionar Planes de Suscripción** | Superadmin SaaS | 🌐 Web | **Etapa 1** | Configuración de planes (*Básico* vs *Profesional*) y límites globales. |
| **CU-03** | **Asignar y Renovar Suscripción de Empresa** | Tenant Admin / Superadmin | 🌐 Web | **Etapa 1** | Gestión comercial y simulación administrativa de suscripciones. |
| **CU-04** | **Controlar Límites y Restricciones por Plan** | Sistema (Middleware) | 🔄 Ambos | **Etapa 1** | El backend bloquea acciones no permitidas y ambos clientes muestran alertas de límite alcanzado. |
| **CU-05** | **Gestionar Sucursales y Empleados por Tenant** | Tenant Admin | 🌐 Web | **Etapa 1** | Gestión administrativa corporativa de tiendas y asignación de personal. |
| **CU-06** | **Descargar y Almacenar Catálogo Offline** | Cajero / Vendedor | 🔄 Ambos | **Etapa 1** | **Web:** Guarda en IndexedDB / **Móvil:** Guarda en base SQLite local. |
| **CU-07** | **Consultar Catálogo y Existencias Offline** | Cajero / Vendedor / Cliente | 🔄 Ambos | **Etapa 1** | Búsqueda local con alerta de *"información posiblemente desactualizada"*. |
| **CU-08** | **Registrar Venta de Contado Offline** | Cajero / Vendedor | 🔄 Ambos | **Etapa 2** | Venta en efectivo sin red; encola transacción con UUID en IndexedDB o SQLite. |
| **CU-09** | **Registrar Reserva de Prendas Offline** | Cajero / Vendedor / Cliente | 🔄 Ambos | **Etapa 2** | Reserva de artículos sin conexión para sincronización posterior. |
| **CU-10** | **Consultar Operaciones Locales Pendientes** | Cajero / Vendedor | 🔄 Ambos | **Etapa 2** | Bandeja de transacciones locales en espera de confirmación del servidor. |
| **CU-11** | **Sincronizar Operaciones con el Servidor** | Motor de Sync / Cajero | 🔄 Ambos | **Etapa 2** | Envío por lotes al detectar conectividad respetando idempotencia. |
| **CU-12** | **Gestionar Conflictos de Sincronización** | Cajero / Tenant Admin | 🔄 Ambos | **Etapa 2** | Notificación y resolución si el stock central se agotó mientras se operaba offline. |
| **CU-13** | **Gestionar Cambio de Prendas de Vestir** | Cajero / Vendedor | 🔄 Ambos | **Etapa 2** | Post-venta presencial en el POS de tienda (sea en terminal Web o Móvil/Tablet). |
| **CU-22** | **Gestionar Datos Mínimos de Clientes Offline** | Cajero / Vendedor | 🔄 Ambos | **Etapa 2** | Alta y selección rápida de cliente para emitir comprobante de venta o reserva sin internet. |
| **CU-14** | **Solicitar Reporte por Lenguaje Natural (Texto/Voz)** | Tenant Admin | 🔄 Ambos | **Etapa 3** | **Móvil:** Entrada de voz por micrófono / **Web:** Entrada escrita y Web Speech API. |
| **CU-15** | **Interpretar Consulta Analítica (Text-to-SQL Seguro)** | Asistente IA (Backend) | 🔄 Ambos | **Etapa 3** | Servicio que valida que el usuario solo consulte los datos de su propio tenant. |
| **CU-16** | **Visualizar Reporte Dinámico (Tablas y Gráficos)** | Tenant Admin | 🔄 Ambos | **Etapa 3** | Renderizado adaptativo: tablas y gráficos interactivos tanto en desktop como móvil. |
| **CU-17** | **Exportar Reporte a Excel y PDF** | Tenant Admin | 🌐 Web | **Etapa 3** | Generación y descarga directa de documentos ofimáticos formales. |
| **CU-18** | **Generar Dataset Sintético de Entrenamiento** | Sistema / Tenant Admin | 🌐 Web | **Etapa 3** | Pipeline de generación de datos artificiales para entrenar los modelos (Secc. 8.4). |
| **CU-19** | **Entrenar y Evaluar Modelo Supervisado (Predicción)** | Tenant Admin | 🌐 Web | **Etapa 3** | Módulo analítico de predicción de ventas/demanda con métricas de validación. |
| **CU-20** | **Entrenar Modelo No Supervisado (Clustering/Anomalías)** | Tenant Admin | 🌐 Web | **Etapa 3** | Segmentación no supervisada de clientes y detección de patrones de compra. |
| **CU-21** | **Visualizar Dashboard Analítico Inteligente** | Tenant Admin | 🌐 Web | **Etapa 3** | Panel integral con indicadores de negocio y métricas de desempeño de ML. |
| **CU-26** | **Gestionar Devolución y Reposición de Prendas** | Cajero / Vendedor, Admin Sucursal | 🔄 Ambos | **Etapa 3** | Devolución en tienda, reintegro de stock en Kardex (`RETURN`/`RESTOCK`) y nota de crédito. |
| **CU-23** | **Notificar Estado de Conectividad (Semáforo Online/Offline)** | Sistema Cliente | 🔄 Ambos | **Etapa 1** | Barra de estado visual en UI indicando pérdida de red y operaciones en cola. |
| **CU-24** | **Instalar y Registrar Service Worker (PWA)** | Usuario Web | 🌐 Web | **Etapa 1** | Exclusivo del navegador: Web App Manifest, Service Worker y caché de activos estáticos. |
| **CU-25** | **Configurar y Migrar Persistencia SQLite Móvil** | Motor Móvil | 📱 Móvil | **Etapa 1** | Exclusivo de Flutter: inicialización de la base de datos local SQLite y transacciones ACID nativas. |
| **CU-27** | **Escanear Prendas por Código de Barras y Facturación Omnicanal (POS y Online)** | Cajero / Vendedor, Cliente | 🔄 Ambos | **Etapa 2 / 3** | Aporte de innovación: lectura de barras/cámara/celular, ticket multilínea y emisión de factura comercial con QR tanto en POS como en Compra Online. |
| **CU-28** | **Generar e Imprimir Etiquetas Colgantes con Código de Barras para Prendas (Hangtags)** | Encargado de Inventario / Cajero | 🌐 Web | **Etapa 3** | Aporte de innovación: generación de planillas de etiquetas colgantes con código `Code-128`, QR, talla, color y precio para prendas físicas. |
| **CU-29** | **Gestionar Arqueo y Cierre de Caja por Turno (Reporte Z Imprimible)** | Cajero / Supervisor de Sucursal | 🌐 Web | **Etapa 3** | Aporte de innovación: conteo físico de billetes/monedas por denominación, conciliación de ventas (Efectivo/QR/Tarjeta/Devoluciones) y emisión de Reporte Z. |

---

## 🗂️ Desglose por Etapas de Presentación

### 🏢 Etapa 1 — SaaS Multitenant, PWA y Catálogo Offline (Hito: 25/10/2026)
* **CU-01:** Registrar Empresa Contratante (Tenant)
* **CU-02:** Gestionar Planes de Suscripción
* **CU-03:** Asignar y Renovar Suscripción de Empresa
* **CU-04:** Controlar Límites y Restricciones por Plan
* **CU-05:** Gestionar Sucursales y Empleados por Tenant
* **CU-06:** Descargar y Almacenar Catálogo Offline
* **CU-07:** Consultar Catálogo y Existencias Offline
* **CU-23:** Notificar Estado de Conectividad (Semáforo Online/Offline)
* **CU-24:** Instalar y Registrar Service Worker (PWA)
* **CU-25:** Configurar y Migrar Persistencia SQLite Móvil

### 📦 Etapa 2 — Operaciones Comerciales Offline y Sincronización (Hito: 01/11/2026)
* **CU-08:** Registrar Venta de Contado Offline
* **CU-09:** Registrar Reserva de Prendas Offline
* **CU-10:** Consultar Operaciones Locales Pendientes
* **CU-11:** Sincronizar Operaciones con el Servidor
* **CU-12:** Gestionar Conflictos de Sincronización
* **CU-13:** Gestionar Cambio de Prendas de Vestir
* **CU-22:** Gestionar Datos Mínimos de Clientes Offline

### 🧠 Etapa 3 — IA Generativa y Analítica Predictiva Multi-tenant (Hito: 08/11/2026 / Defensa: 10/11/2026)
* **CU-14:** Solicitar Reporte por Lenguaje Natural (Texto/Voz)
* **CU-15:** Interpretar Consulta Analítica (Text-to-SQL Seguro)
* **CU-16:** Visualizar Reporte Dinámico (Tablas y Gráficos)
* **CU-17:** Exportar Reporte a Excel y PDF
* **CU-18:** Generar Dataset Sintético de Entrenamiento
* **CU-19:** Entrenar y Evaluar Modelo Supervisado (Predicción)
* **CU-20:** Entrenar Modelo No Supervisado (Clustering/Anomalías)
* **CU-21:** Visualizar Dashboard Analítico Inteligente
* **CU-26:** Gestionar Devolución y Reposición de Prendas
* **CU-27:** Escanear Prendas por Código de Barras y Facturación Omnicanal (POS y Online)
* **CU-28:** Generar e Imprimir Etiquetas Colgantes con Código de Barras para Prendas (Hangtags)
* **CU-29:** Gestionar Arqueo y Cierre de Caja por Turno (Reporte Z Imprimible)
