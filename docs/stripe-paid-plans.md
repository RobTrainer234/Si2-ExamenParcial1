# Prueba de planes SaaS pagos con Stripe

## Límites de seguridad

- El registro de prueba gratis de 14 días (`plan=TRIAL`) es independiente y no requiere tarjeta.
- Los planes pagos usan Stripe Checkout alojado. La empresa y su administrador se crean únicamente cuando el webhook firmado confirma un pago exitoso; la URL de retorno del navegador no concede acceso.
- Para estas instrucciones usá exclusivamente claves de **modo de prueba** y una tarjeta de prueba de Stripe. No uses datos de una tarjeta real.
- Guardá `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` sólo en el `.env` local ignorado por Git. Nunca los pegues en el chat, capturas, documentación versionada ni commits. La clave publicable puede estar en el frontend; no es una clave secreta.

## Requisitos

- FashionStore iniciado con `docker-compose.prod.yml` y la API accesible detrás del proxy web en `http://localhost:<WEB_PORT>/api/v1`.
- Stripe CLI instalada y autenticada en la cuenta de Stripe de prueba (`stripe login`).
- Plan activo con precio mensual/anual mayor que cero. El monto proviene de la configuración del plan en el servidor; el navegador no define el precio.
- Una cuenta Stripe de prueba habilitada para presentar la moneda definida en los precios del plan. La moneda y el monto se derivan de `subscription_plans` en el servidor; no configures `STRIPE_CURRENCY` para este flujo. La disponibilidad de cuenta y moneda live debe confirmarse en el Dashboard antes de producción.

## Configuración local de Brevo

Si querés enviar el correo real de confirmación de pago, agregá estas variables únicamente al `.env` local ignorado por Git:

```dotenv
BREVO_API_KEY=...
BREVO_SENDER_EMAIL=tu-remitente-verificado@example.com
BREVO_SENDER_NAME=FashionStore
```

`BREVO_SENDER_NAME` es opcional. `BREVO_SENDER_EMAIL` debe ser un remitente verificado en Brevo. Nunca pegues una clave en el chat, la documentación, capturas o commits; tampoco la imprimas en logs. Si estas variables no están configuradas, las pruebas no llaman a Brevo y no se envía ningún correo real.

La referencia oficial de la API es [Brevo API v3](https://developers.brevo.com/reference/sendtransacemail).

## Flujo de verificación y confirmación

- Antes de abrir el Checkout pago, la persona debe validar un código de verificación de seis dígitos.
- El código vence a los **10 minutos** y permite hasta **cinco intentos**.
- El reenvío tiene una espera de **60 segundos** y un máximo de **cinco envíos por hora**.
- La activación de la empresa y del plan pago ocurre únicamente mediante el webhook firmado de Stripe; volver desde Checkout no activa la cuenta por sí solo.
- Luego de la confirmación, el backend crea el correo de pago confirmado en `email_outbox`; `email-worker` lo entrega mediante Brevo cuando las credenciales están configuradas.
- `TRIAL` sigue siendo un camino separado, sin tarjeta y sin Checkout pago.

## Inicio y pruebas locales seguras

Desde la raíz del repositorio, una secuencia segura es:

```bash
docker compose -f docker-compose.prod.yml up -d migrate backend email-worker
cd backend && python -m pytest -q tests/test_paid_signup_email_migration.py
```

Para ejecutar el backend fuera de Compose, usá el entorno local con una base descartable y arrancá `email-worker` sólo en otra terminal con la misma configuración:

```bash
cd backend
python -c "from app.core.email_outbox_worker import run_worker; run_worker()"
```

No configures `BREVO_API_KEY` ni `BREVO_SENDER_EMAIL` para pruebas que no deban enviar correo real; el worker dejará el envío externo desactivado. No uses una base de producción ni `DATABASE_URL` para las pruebas de migración.

## Configuración local del webhook

1. En el `.env` local ignorado por Git, configura `STRIPE_SECRET_KEY` con una clave de prueba `sk_test_...` y `STRIPE_PUBLISHABLE_KEY` con una clave `pk_test_...`. La moneda se toma del plan en la base de datos.
2. En una terminal local, inicia el reenvío de webhooks hacia el puerto web expuesto por Compose (reemplazá `<WEB_PORT>` por el valor efectivo de `WEB_PORT`):

   ```bash
   stripe listen --events checkout.session.completed,checkout.session.expired,customer.subscription.created,customer.subscription.updated,customer.subscription.deleted,invoice.paid,invoice.payment_succeeded,invoice.payment_failed --forward-to http://localhost:<WEB_PORT>/api/v1/subscriptions/stripe/webhook
   ```

3. Stripe CLI muestra un secreto de firma `whsec_...` para esa sesión. Copialo directamente al `STRIPE_WEBHOOK_SECRET` del `.env` local. No lo compartas ni lo guardes en archivos versionados.
4. Recreá el servicio `backend` para que cargue la variable local actualizada:

   ```bash
   docker compose -f docker-compose.prod.yml up -d --force-recreate backend
   ```

5. Conservá `stripe listen` abierto mientras hacés las pruebas. El secreto `whsec_...` es específico del listener; si lo reiniciás, volvé a actualizar el valor local y recrear el backend.

## Casos manuales de prueba

### Plan pago, pago aprobado

1. Abrí `http://localhost:<WEB_PORT>/register-company?plan=BASIC&billing=monthly` (o elegí otro plan/intervalo activo con precio configurado).
2. Completá el formulario con un correo nuevo de prueba, solicitá el código de verificación, ingresá el código recibido y verificá el correo. Recién después se abrirá Stripe Checkout.
3. En Stripe Checkout usá una tarjeta de prueba publicada por Stripe (por ejemplo `4242 4242 4242 4242`), una fecha futura y un CVC de prueba; nunca uses una tarjeta real.
4. Volvé a la aplicación. La página espera, con límite, la confirmación del webhook. Sólo muestra la cuenta lista cuando el backend refleja `COMPLETED`.
5. Iniciá sesión con el correo y contraseña de prueba. La redirección exitosa por sí sola no activa la cuenta.

### Checkout cancelado o vencido

- Cancelá Checkout y comprobá que el sitio indique que no se activó acceso. No debe aparecer una sesión autenticada ni crearse un tenant por el retorno.
- Para probar expiración, dejá vencer una sesión de prueba y comprobá que la página presente el estado vencido. No reenvíes el formulario con el mismo correo mientras siga pendiente.

### Prueba gratis

1. Abrí `http://localhost:<WEB_PORT>/register-company?plan=TRIAL`.
2. Completá el formulario y verificá que se mantenga el alta trial existente, sin redirección a Stripe ni datos de tarjeta.

### Resultado verificado en modo de prueba (2026-10-31)

- La creación de Checkout respondió HTTP 201 y Stripe generó una sesión de prueba para el plan BASIC en BOB.
- Una sesión vencida produjo el evento firmado `checkout.session.expired` y el backend reflejó `EXPIRED`.
- La tarjeta de prueba `4242 4242 4242 4242` completó otra sesión; Stripe informó pago `paid` y suscripción `active`. Tras corregir la secuencia PostgreSQL que había impedido la primera activación y reproducir el payload real del evento con firma válida en el webhook local, el backend informó `COMPLETED`; tenant, administrador y suscripción quedaron `ACTIVE`.
- No se usó modo live ni se hizo ningún cargo real. El evento se probó sólo en la cuenta de prueba.

### Verificación automatizada del flujo local

Desde la raíz del repositorio:

```bash
cd backend && python -m pytest -q tests/test_saas_email_verification.py tests/test_saas_paid_checkout.py tests/test_paid_signup_email_migration.py
cd web && npm test
cd web && npm run build
```

La última verificación SPC-6 pasó **34 tests de backend** (un test PostgreSQL se omitió porque no se configuró explícitamente `MIGRATION_TEST_DATABASE_URL`), **128 tests web** y el build Angular. Las pruebas usan transporte simulado para Brevo/Stripe; no envían correos ni hacen cargos reales. El round-trip PostgreSQL también se ejecutó por separado con Alembic/SQLAlchemy en un esquema temporal y pasó; la variante pytest no corrió en el contenedor runtime porque esa imagen no incluye pytest.

Para ejecutar la variante PostgreSQL de la migración con pytest, configurá `MIGRATION_TEST_DATABASE_URL` sólo con una base descartable dedicada a pruebas. El test crea un esquema único y lo elimina al finalizar. No uses `DATABASE_URL` de la aplicación ni una base de producción.

## Antes de producción

- Reemplazá las credenciales de prueba por credenciales live sólo mediante el proceso de configuración segura del despliegue; no reutilices el secreto de `stripe listen`.
- Configurá y verificá un endpoint webhook HTTPS en Stripe Dashboard con los eventos necesarios de Checkout y ciclo de suscripción.
- Confirmá país de la cuenta, moneda admitida, precios, impuestos y requisitos comerciales directamente en el Dashboard de Stripe.
- No habilites producción hasta probar pago, cancelación, expiración y cambios de estado con el endpoint live y una revisión de seguridad independiente.
