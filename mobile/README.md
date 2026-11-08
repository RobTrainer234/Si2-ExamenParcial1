# FashionStore Mobile

## Photo-based AI virtual fitting

The virtual fitting screen is a capture-only VTON flow. It never renders the catalog garment as a live AR overlay, fake mannequin garment, or local composite. The app only shows a result after the backend returns a composite image from `POST /catalogo/vton/try-on`.

User flow:

1. Open a product and enter **LOOK ATELIER**.
2. Choose the primary action **Elegir foto de galería** or use **Usar cámara** and capture a still photo.
3. The app validates the selected/captured image locally before upload:
   - supported image signatures: JPG, PNG, or WebP;
   - base64 upload payload target: `<= 7 MB`.
4. A local preview asks for confirmation. The user can generate the try-on, cancel, or choose another photo.
5. The confirmed photo is base64-encoded and sent to the existing backend route `POST /catalogo/vton/try-on` through `VirtualFittingRepository.vtonTryOn(imageBase64: ...)`.
6. While pending, the UI shows a neutral studio/loading state. If the backend returns an error or the VTON provider is unavailable, the app shows an honest error and retry path.
7. On success, the screen shows only the returned composite image, the provider/result status, the selected product name, and existing actions to change garment, retry with another photo, reserve a fitting room, or add the product to the cart.

Save/share is intentionally not added in this version because doing it safely would require additional mobile storage/share dependencies. Result actions stay bounded to retry/change garment/reserve/add cart.

No Gemini, Stripe, or other secret keys belong in the mobile app. Configure only public/runtime values via `--dart-define`; provider secrets stay on the backend.

## Checkout con tarjeta y sandbox

El checkout con tarjeta usa PaymentSheet cuando el backend devuelve un intent real. Si el backend no tiene `STRIPE_SECRET_KEY`, devuelve un intent sandbox y la app lo confirma directamente en el backend sin abrir Stripe. La clave secreta nunca se incluye en la app:

```bash
flutter run \
  --dart-define=API_URL=http://10.0.2.2:8000/api/v1 \
  --dart-define=STRIPE_PUBLISHABLE_KEY=pk_live_or_test_public_key \
  --dart-define=STRIPE_CURRENCY=USD
```

Para generar una APK de producción apuntando al backend desplegado:

```bash
# PowerShell: usa una sola línea o el acento grave (`) como continuación.
flutter build apk --release `
  --dart-define="API_URL=http://fashionstore.3.94.34.64.nip.io/api/v1" `
  --dart-define="STRIPE_PUBLISHABLE_KEY=pk_live_or_test_public_key" `
  --dart-define="STRIPE_CURRENCY=USD"
```

La APK se genera en `build/app/outputs/flutter-apk/app-release.apk`. La
configuración release conserva los metadatos necesarios de ML Kit, WorkManager
y Stripe para evitar cierres al iniciar. Para una instalación rápida en un
dispositivo conectado por ADB usa `flutter install`.
La clave secreta `STRIPE_SECRET_KEY` debe configurarse únicamente en el
backend; la app móvil solo recibe la clave pública.

The app calls the existing backend flow only:

1. `POST /purchases/digital`
2. `POST /payments/stripe/intent`
3. Si el intent es real, Stripe PaymentSheet/client confirmation; si es sandbox, confirmación backend
4. `POST /payments/stripe/confirm`

The separate **Sandbox demo** button still uses `/payments/electronic` and `/payments/electronic/notification` for simulated payments.

Cliente Flutter del Ciclo 1 para autenticacion, catalogo, detalle de producto
y consulta de disponibilidad.

## Requisitos

- Flutter `3.44.1` y Dart `3.12.1`.
- Backend disponible en la URL configurada mediante `API_URL`.
- Permisos de galería/fotos y cámara configurados para la plataforma cuando se pruebe en dispositivo real.
- Dependencia Flutter ya declarada: `image_picker` para selección de fotos de galería.

## Desarrollo

```bash
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` funciona en el emulador Android. En iOS simulator puede usarse
`http://127.0.0.1:8000/api/v1`; en un dispositivo fisico debe usarse la IP del
equipo que ejecuta el backend.

## Verificacion

```bash
dart format lib test
flutter analyze
flutter test
flutter build apk --debug --dart-define=API_URL=http://10.0.2.2:8000/api/v1 --dart-define=STRIPE_PUBLISHABLE_KEY=pk_test_your_key --dart-define=STRIPE_CURRENCY=USD
```
