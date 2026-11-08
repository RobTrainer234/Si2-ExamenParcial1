# Etapa 3 — Inteligencia Artificial Generativa y Analítica Predictiva Multi-tenant

## Objetivo
Evolucionar la plataforma **FashionStore** incorporando reportes generativos mediante Inteligencia Artificial y lenguaje natural (escrito y voz), gobernados por planes de suscripción SaaS (`generative_reports_enabled`), junto con un módulo de analítica inteligente mediante **Machine Learning supervisado** (predicción de demanda/ventas con MAE/RMSE/R²) y **no supervisado** (segmentación de clientes RFM/clustering con Silhouette Score e Inercia), con soporte visual y exportación en Web (Angular) y Móvil (Flutter), documentado bajo la metodología **ICONIX**.

> **Autoridad y estado:** La fuente de verdad para IDs y criterios es `docs/casos-de-uso-oficiales-parcial-2.md` (Etapa 3: CU-14–CU-21 y CU-26). Los IDs T3.x de esta hoja son tareas de roadmap, no IDs oficiales. Los checks históricos de abajo no prueban por sí solos la aceptación de cada CU; la auditoría y el cierre integral siguen abiertos. Los antiguos rótulos CU-30/31/32 de la documentación ICONIX no reemplazan la numeración oficial.

### CU-14 — Estado de implementación
- **Implementado en Web:** entrada por teclado y voz con Web Speech API (`es-BO`), reconocimiento integrado al prompt de reportes y manejo de navegador/errores.
- **Implementado en Flutter:** grabación real, aviso explícito sobre envío al backend y posible procesamiento por Gemini, revisión y acción separada para transcribir; el texto resultante no ejecuta el informe automáticamente.
- **Implementado en backend:** autorización `reports.read`, control `generative_reports_enabled`, MIME/Base64 estrictos, límite de 2 MiB, errores de proveedor sin transcripciones inventadas y timeouts de audio dedicados (35 s backend / 45 s Flutter).
- **Evidencia automatizada independiente:** backend (21 tests y Ruff), Flutter (78 tests, analyze y APK debug), Web (150 tests y build); no se hicieron llamadas reales a Gemini ni pruebas con micrófono físico.

### CU-15 — Interpretación analítica segura
- **Ejecución tenant-bound:** `/reports/assistant` y `/reports/assistant/export/{format}` rechazan usuarios sin tenant antes de consultar el plan o invocar servicios. El servicio exige que la sesión SQLAlchemy esté activa y asociada al mismo tenant autenticado; sucursales explícitas y derivadas de la intención deben pertenecer a ese tenant y estar activas, con `404` no enumerante.
- **Sin SQL libre del proveedor:** Gemini/OpenAI producen una intención estructurada con tipos de reporte permitidos y filtros acotados; el backend despacha funciones propias y no ejecuta SQL generado. Los esquemas Pydantic rechazan campos desconocidos como `sql` y `tenant_id`; el esquema OpenAI además usa `additionalProperties: false`. Salidas Gemini inválidas caen al clasificador local.
- **Verificación local:** `backend/tests/test_generative_reports_ml.py` (27 pruebas) y Ruff aprobados. Tests offline cubren sesiones ausentes/mismatch, sucursal externa/inactiva, respuesta maliciosa del proveedor y aislamiento de dos tenants en categorías, productos, sucursales y dashboard, con totales exactos. Se vacían claves de proveedor o se usan clientes falsos; no hubo llamadas reales.
- **Límite:** la aplicación de filtros de fila en las consultas agregadas continúa apoyándose en el listener SQLAlchemy tenant-scoped de `backend/app/core/database.py`; el contrato del servicio ahora exige ese contexto y los tests lo ejercitan por HTTP. No se realizó validación PostgreSQL específica ni prueba con proveedores desplegados.

### CU-16 — Visualización dinámica (Web y Móvil)
- **Web:** renderiza `bar`, `line`, `pie`, `table` y `kpi` a partir de datos reales del reporte; calcula proporciones, mantiene geometría responsive y ofrece etiquetas/tabla accesibles.
- **Móvil:** renderiza gráficos y tablas data-driven sin dependencia adicional; barras ordenadas por valor, líneas ordenadas cronológicamente cuando hay fechas parseables, segmentos pie y fallback tabular accesible para datos no temporales o inválidos.
- **Verificación local:** Web `npm test` (28 archivos / 156 pruebas) y build; Flutter 5 pruebas widget enfocadas CU16 y `flutter analyze`. Se usaron datos de prueba, no hardware ni servicios reales.

### CU-17 — Exportación Excel/PDF (Web)
- **Contrato:** `POST /api/v1/reports/assistant/export/{format}` recibe `ReportAssistantRequest`, coincidiendo con el cliente Web y respondiendo como descarga binaria; formatos admitidos: XLSX y PDF.
- **Cobertura:** se exportan datos de reportes de categorías, productos, sucursales, inventario, reservas, canales y dashboard. El permiso `reports.read` y `generative_reports_enabled` se conservan antes del procesamiento.
- **Protecciones:** valores string que podrían interpretarse como fórmula de Excel se neutralizan; los números negativos preservan su tipo. El título dinámico del PDF se escapa antes de generar el párrafo.
- **Verificación local:** backend (26 pruebas de exportación/asistente y Ruff) y Web (28 archivos / 156 pruebas). No se probaron servicios desplegados ni datos reales. La rama genérica de listas no-dict no tiene un test de ruta dedicado; las formas producidas por los servicios están cubiertas.

### CU-18 — Dataset sintético de entrenamiento (pipeline interno)
- **Alcance acordado:** generación en memoria dentro del pipeline; no se requiere endpoint ni acción Web separada para inspeccionar datasets.
- **Comportamiento:** generadores tenant-seeded y repetibles dentro del mismo día UTC; forecast y segmentación recurren a datos sintéticos cuando el historial es escaso. Las métricas reportan muestras totales, reales y sintéticas por separado.
- **Verificación:** tests locales deterministas cubren ambos fallbacks y la contabilización de fechas reales que sustituyen fechas sintéticas. No hay persistencia de datasets.

### CU-19 — Predicción supervisada
- **Implementado:** forecast Ridge con validación cronológica; rutas ML rechazan usuarios sin tenant, validan sucursales activas del tenant y limitan horizonte a 1–12 semanas. R² negativo se conserva; valores no disponibles quedan nulos con narrativa precisa.
- **Verificación:** tests locales cubren aislamiento tenant/sucursal, límites, orden temporal, R² negativo/null/NaN y fallback sintético.
- **Límite:** el modelo se vuelve a entrenar por solicitud; no hay registro persistente de versiones/historial, que no está requerido explícitamente por la matriz oficial.

### CU-20 — Clustering y anomalías
- **Implementado:** clustering RFM con K-Means más detección explícita de anomalías con IsolationForest determinista. La respuesta identifica origen real/sintético, limita el detalle a 10 filas y conserva el conteo total; no expone IDs de clientes ni pseudo-IDs.
- **Verificación:** tests locales cubren perfil atípico sintético, orden y límite, provenance y entrada vacía/degenerada.
- **Límite:** la contaminación se mantiene en el modo automático del algoritmo; no se calibró contra datos reales de producción.

### CU-21 — Dashboard analítico Web
- **Implementado:** contratos Angular alineados con respuestas backend para períodos, ingresos/confianza, `segment_id`, descripciones, métricas de entrenamiento, anomalías y procedencia real/sintética. Las pruebas de componente usan payloads con la forma real del backend.
- **Verificación final:** backend `test_generative_reports_ml.py` (20 pruebas) y Ruff; Web (`npm test`: 28 archivos / 156 pruebas; `npm run build`: aprobado). Los tests reportan ruido `AggregateError` de jsdom, pero terminan exitosamente.
- **Límite común:** no se hicieron llamadas a APIs externas, servicios desplegados, hardware ni datos reales. Las pruebas de UI son locales con mocks; no sustituyen un smoke test de despliegue.

---

## Hojas de Ruta y Fases de Implementación

### Fase 3.1 — Backend: Reportes Generativos con IA, Control de Suscripción y Exportación Dinámica
- [x] **T3.1.1** Mejorar el servicio de inteligencia artificial (`backend/app/modules/reports/ai_service.py`) con soporte estructurado para modelos generativos LLM (Gemini API con fallback heurístico local), extracción de intenciones y filtros dinámicos (`date_from`, `date_to`, `branch_id`, `category_id`), sugerencia de tipo de visualización (`chart_type`) y síntesis narrativa ejecutiva.
- [x] **T3.1.2** Implementar consultas seguras parametrizadas en PostgreSQL protegidas por el ámbito estricto de `tenant_id` para los 4 reportes obligatorios:
  1. Ventas por período agrupadas por sucursal / comparación temporal.
  2. Top prendas y productos más vendidos.
  3. Alerta de bajo stock y necesidad de reposición por sucursal.
  4. Ingresos por categoría y rendimiento de colecciones.
- [x] **T3.1.3** Implementar verificación estricta de planes de suscripción: impedir acceso a reportes generativos de IA a tenants con planes sin el feature (`generative_reports_enabled=False`), respondiendo con HTTP `403 FEATURE_NOT_IN_PLAN`.
- [x] **T3.1.4** Implementar exportación dinámica a PDF y Excel del reporte generado por lenguaje natural en `backend/app/modules/reports/export_service.py`.

### Fase 3.2 — Backend: Módulo de Analítica Inteligente con Machine Learning
- [x] **T3.2.1** Implementar generador de datos sintéticos y aumentados (`SyntheticDataService`) para entrenamiento y validación de modelos basados en la estructura del tenant.
- [x] **T3.2.2** Implementar modelo supervisado de Predicción de Demanda / Ventas Futuras con métricas de evaluación (MAE, RMSE, R²).
- [x] **T3.2.3** Implementar modelo no supervisado de Segmentación de Clientes y Patrones de Compra (Clustering K-Means / RFM) con métricas de evaluación (Silhouette Score e Inercia).
- [x] **T3.2.4** Publicar endpoints REST en `backend/app/modules/reports/router.py`:
  - `GET /api/v1/reports/ml/demand-forecast`
  - `GET /api/v1/reports/ml/customer-segments`
  - `POST /api/v1/reports/ml/train`
- [x] **T3.2.5** Implementar suite de pruebas automáticas en `backend/tests/test_generative_reports_ml.py` (TDD: RED -> GREEN): interpretación de intenciones, aislamiento multi-tenant, bloqueo por plan básico, entrenamiento y evaluación de modelos ML.

### Fase 3.3 — Frontend Web (Angular) y Móvil (Flutter): Interfaz Generativa, Voz y Dashboard Analítico
- [x] **T3.3.1** Actualizar `cycle3-admin.component.ts` en Angular para incorporar entrada por voz (Web Speech API), visualización de gráficos dinámicos recomendados por la IA, botones de exportación dinámica a PDF/Excel y tarjetas del dashboard analítico de ML (predicciones y clusters).
- [x] **T3.3.2** Implementar servicio y repositorio de reportes IA y analítica en Flutter (`reports_repository.dart`).
- [x] **T3.3.3** Implementar pantalla de Reportes Generativos y Analítica en Flutter (`reports_screen.dart`) con prompts rápidos, dictado por voz, gráficos dinámicos y métricas de ML.
- [x] **T3.3.4** Implementar pruebas unitarias y de widgets en Web (`npm test`) y Móvil (`flutter test`).

### Fase 3.4 — Verificación Integral, Regresión y Documentación ICONIX (Etapa 3)
- [x] **T3.4.1** Ejecutar la suite completa de pruebas: Backend (pytest), Web (npm test + build) y Móvil (flutter test + analyze), documentando métricas y comandos.
- [ ] **T3.4.2** Reconciliar la documentación ICONIX en `docs/uml/diagramas_uml.md` con la matriz oficial: revisar Modelo de Dominio, diagramas BCE y de Secuencia y actualizar la Matriz de Trazabilidad usando los IDs CU-14–CU-21; tratar CU-26 según su flujo oficial de devoluciones/reposición. Los antiguos rótulos CU-30/31/32 quedan pendientes de corrección.
- [ ] **T3.4.3** Auditar criterios de aceptación contra cada caso oficial de Etapa 3, completar las brechas y cerrar la etapa. No marcar cerrado antes de verificar CU-14–CU-21 y CU-26.

---

## Criterios de Aceptación Registrados en el Plan (estado histórico)

> Estos checks representan el estado que registraba la hoja antes de la reconciliación con la matriz oficial. No son evidencia de que todos los criterios oficiales estén implementados ni de que las suites se hayan reejecutado en esta actualización.
- [x] **Lenguaje Natural (Escrito y Voz):** Usuarios autorizados solicitan reportes mediante teclado o voz (Web Speech API en Angular; grabación y transcripción backend en Flutter, con revisión antes de ejecutar el informe).
- [x] **Extracción de Intenciones y Filtros:** El motor clasifica intenciones (`sales_by_branch`, `top_products`, `inventory`, `revenue_by_category`, `dashboard`), extrae fechas y sucursales y recomienda visualizaciones (`bar`, `line`, `pie`, `table`, `kpi`).
- [x] **Aislamiento Multi-tenant Riguroso:** Las consultas se ejecutan filtrando estrictamente por `tenant_id` y estado de venta (`CONFIRMED`, `COMPLETED`), impidiendo cualquier fuga de datos entre empresas.
- [x] **Los 4 Reportes Obligatorios:** Demostrados y validados con consultas parametrizadas en base de datos real.
- [x] **Visualización y Síntesis:** Resultados presentados en componentes gráficos interactivos, tablas formateadas y diagnósticos ejecutivos formulados por la IA.
- [x] **Exportación Dinámica:** Generación y descarga directa en servidor de informes oficiales en Excel (.xlsx) con fórmulas y estilos corporativos, y en PDF (.pdf) formal.
- [x] **Control de Suscripciones SaaS:** Tenants en Plan Básico reciben HTTP `403 FEATURE_NOT_IN_PLAN`, mientras tenants en Plan Profesional acceden a Sofía IA y Machine Learning.
- [x] **Machine Learning Supervisado & No Supervisado:**
  - `DemandForecastService`: Ridge regression con rezagos y medias móviles, evaluado con MAE, RMSE y R² (proyección a 4-6 semanas).
  - `CustomerSegmentationService`: K-Means RFM clustering con StandardScaler, evaluado con Silhouette Score e Inercia, categorizando a clientes en 4 perfiles estratégicos con acciones sugeridas.
  - `SyntheticDataService`: Generación de series calibradas por tenant para entrenamiento y validación continua.
- [x] **Documentación Formal ICONIX (registro histórico):** La hoja registraba la sección 17 y una matriz de trazabilidad; la corrección de su numeración y concordancia con los IDs oficiales permanece pendiente en T3.4.2.

---

## Evidencia Histórica de Ejecución (snapshot anterior)

> Las siguientes cifras pertenecen al snapshot que documentaba esta hoja antes de la reconciliación oficial. No representan la verificación actual de todos los CU; consultar las secciones CU-14, CU-16 y CU-17 y mantener pendiente el cierre integral de T3.4.2/T3.4.3.

- **Backend Pytest:** 46 pruebas pasadas en aquel snapshot.
- **Web Angular:** 84 pruebas y compilación de producción en aquel snapshot.
- **Móvil Flutter:** 53 pruebas y `flutter analyze` en aquel snapshot.
