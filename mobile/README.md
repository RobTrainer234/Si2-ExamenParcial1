# FashionStore Mobile

Cliente Flutter del Ciclo 1 para autenticacion, catalogo, detalle de producto
y consulta de disponibilidad.

## Requisitos

- Flutter `3.44.1` y Dart `3.12.1`.
- Backend disponible en la URL configurada mediante `API_URL`.

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
flutter analyze
flutter test
flutter build apk --debug
```
