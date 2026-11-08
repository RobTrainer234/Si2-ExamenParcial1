# Plan por fases — Landing y prueba self-service SaaS

## Objetivo y alcance

Crear una landing pública para FashionStore y permitir que una empresa acceda inmediatamente a una prueba self-service, sin esperar aprobación humana. El trabajo incluye navegación por rol y las capacidades de planes, suscripciones y restricciones relacionadas con CU-01 a CU-04.

Este documento es un **plan**, no una declaración de implementación ni de cumplimiento de los casos de uso. La matriz oficial es [`casos-de-uso-oficiales-parcial-2.md`](casos-de-uso-oficiales-parcial-2.md). El registro actual `/register` crea clientes, no empresas SaaS; el alta self-service requiere un flujo específico.

## Estado de las decisiones

La política de prueba, sus detalles operativos y la estructura oficial de precios y periodicidad están acordados formalmente e implementados de extremo a extremo:

- **Moneda oficial SaaS:** Bolivianos (`BOB` / `Bs`), coherente con la moneda local de la tienda.
- **Prueba para Empresas:** **Bs 0** durante 14 días (hasta 2 sucursales activas, sin IA generativa, sin tarjeta de crédito ni conversión automática).
- **Plan Básico (`BASIC`):** **Bs 199 / mes** (o **Bs 1.990 / año** en facturación anual, bonificando 2 meses de servicio). Hasta 2 sucursales activas, funciones operativas completas y modo offline.
- **Plan Profesional (`PROFESSIONAL` / `PRO`):** **Bs 499 / mes** (o **Bs 4.990 / año** en facturación anual, bonificando 2 meses de servicio). Hasta 10 sucursales activas, reportes y asistente con IA generativa (texto/voz) y analítica predictiva ML.

| Fase | Resultado esperado | Estado |
|---|---|---|
| 0 | Política de prueba acordada | Completada |
| 1 | Landing pública | Completada |
| 2 | Alta self-service y acceso inmediato | Completada |
| 3 | Gestión de planes y suscripciones | Completada |
| 4 | Límites y vencimiento | Completada |
| 5 | Navegación y acceso por rol | Completada |
| 6 | Verificación integral y trazabilidad | Completada |

## Fase 0 — Definir la prueba gratuita

**Objetivo:** acordar qué recibe una empresa al registrarse y qué ocurre después.

### Decisiones aprobadas

- Prueba de **14 días**, sin tarjeta ni cobro automático; alta y acceso inmediatos, sin aprobación humana.
- Hasta **2 sucursales activas**, funciones operativas y reportes generativos de IA deshabilitados.
- Verificación de correo mediante enlace automático después del primer ingreso; límites de solicitudes por red y controles de pruebas repetidas.
- Al vencer, permitir consulta y bloquear nuevas operaciones y modificaciones. Conservar los datos y permitir su exportación durante **90 días**; avisar antes de la eliminación y eliminarlos al terminar ese período.
- Reactivación solicitada desde la cuenta y activada por un administrador de plataforma, sin cobro automático.

### Detalles operativos implementados

- **Verificación de correo:** la empresa ingresa de inmediato tras registrarse y dispone de confirmación de correo desde su panel (`POST /api/v1/subscriptions/verify-email`), registrada en bitácora (`TRIAL_EMAIL_VERIFIED`).
- **Límites antiabuso:** control por dirección IP (máximo 5 altas self-service por hora por IP) y rechazo de nombres de empresa duplicados (`409 TENANT_NAME_EXISTS`) o correos existentes (`409 EMAIL_ALREADY_EXISTS`).
- **Exportación y retención de 90 días:** endpoint `GET /api/v1/subscriptions/export` que permite al administrador de empresa descargar en JSON los datos de su empresa, suscripciones, sucursales y usuarios durante la vigencia y los 90 días posteriores al vencimiento (`retention_days_remaining`).
- **Modo solo lectura al vencer:** cuando `valid_until` expira, las rutas operativas del tenant bloquean operaciones de escritura (`POST`, `PUT`, `PATCH`, `DELETE`) con `403 SUBSCRIPTION_EXPIRED`, manteniendo habilitada la lectura (`GET`), la exportación de datos y la solicitud de reactivación.
- **Canal de solicitud de reactivación/cambio de plan:** desde `/admin` la empresa registra su solicitud (`POST /api/v1/subscriptions/reactivation-request` con plan `BASIC` o `PRO`), visible en `/platform` para que el `PLATFORM_ADMIN` active o renueve la suscripción sin cobro automático.

**Criterio de salida:** política y detalles operativos implementados y verificados con pruebas automatizadas, sin asumir precios, moneda ni condiciones de facturación.

## Fase 1 — Landing pública

**Objetivo:** explicar FashionStore a empresas de indumentaria.

- Presentar beneficios, funcionalidades y planes existentes sin atribuirles condiciones no definidas.
- Separar la landing del catálogo operativo.
- Incorporar acceso al inicio de sesión y un llamado a la prueba.
- Diseñar para móvil y escritorio con accesibilidad básica.

**Criterio de salida:** la landing informa correctamente la oferta y no promete capacidades ni precios no definidos. El CTA de prueba solo se habilita como acceso real cuando exista el flujo de la Fase 2.

## Fase 2 — Alta self-service y prueba inmediata

**Objetivo:** que una empresa obtenga acceso sin esperar aprobación humana.

- Crear un flujo específico de registro de empresa y administrador.
- Asignar la prueba y sus límites según la política aprobada.
- Mantener separado este flujo de `/register`, que actualmente registra clientes.
- Proteger el alta frente a duplicados y abuso conforme a las decisiones de la Fase 0.
- Mostrar errores claros y confirmar el acceso.

**Criterio de salida:** una empresa nueva puede registrarse e ingresar inmediatamente a su espacio de prueba. Esta fase amplía el flujo de **CU-01**.

## Fase 3 — Planes y suscripciones: CU-02 y CU-03

**Objetivo:** permitir que la plataforma gestione la oferta y el ciclo de suscripción.

- Revisar y completar la administración de planes.
- Completar asignación, cambios, renovación e historial de suscripciones según los requisitos oficiales.
- Mostrar a la empresa su plan, estado y vigencia.
- Mantener la separación entre administrador de plataforma y administrador de empresa.

**Criterio de salida:** los flujos definidos de planes y suscripciones cuentan con interfaz, controles de permisos y pruebas. Los precios quedan fuera de alcance hasta que se definan.

## Fase 4 — Límites y vencimiento: CU-04

**Objetivo:** aplicar las reglas acordadas en el backend y comunicarlas en la interfaz.

- Controlar cuotas de sucursales y funcionalidades habilitadas.
- Aplicar las restricciones de la prueba y el comportamiento al vencer.
- Mostrar avisos de vigencia, límites alcanzados y opciones disponibles.
- Verificar que las restricciones no puedan eludirse mediante la API.

**Criterio de salida:** las restricciones se cumplen desde la interfaz y el backend, con mensajes comprensibles.

## Fase 5 — Navegación y acceso por rol

**Objetivo:** dirigir a cada usuario a las funciones que le corresponden.

- Administrador de plataforma: gestión SaaS.
- Administrador de empresa: administración de su empresa.
- Clientes y usuarios operativos: sus funciones correspondientes.
- Mantener controles de autorización en el backend: ocultar una pantalla o redirigir no reemplaza la seguridad.

**Criterio de salida:** cada rol accede solo a las áreas autorizadas y el inicio de sesión lo dirige de forma coherente.

## Fase 6 — Verificación y cierre

- Probar el recorrido completo: landing → registro → acceso → uso → vencimiento o reactivación.
- Probar aislamiento entre empresas, permisos, cuotas y casos de error.
- Seguir **Strict TDD** durante los cambios de código: prueba fallida, implementación, triangulación y refactor; ejecutar las pruebas de backend y web correspondientes.
- Actualizar la trazabilidad de los CU con evidencia real, sin declarar completo lo que siga parcial.

**Criterio de salida:** cada capacidad entregada cuenta con pruebas y evidencia; los pendientes y verificaciones no realizadas quedan explícitos.

## Dependencias y orden

La **Fase 0 bloquea las decisiones de implementación del trial**. Algunas tareas visuales de la landing pueden diseñarse antes, pero el CTA no debe presentarse como funcional hasta que exista el alta self-service. Las fases de planes, restricciones y navegación deben coordinarse para que el recorrido completo pueda verificarse en la Fase 6.

La corrección documental del alcance oficial de Etapa 1 no significa por sí sola que todos sus casos de uso estén implementados o verificados.
