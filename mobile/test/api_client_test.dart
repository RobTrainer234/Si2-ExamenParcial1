import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/errors/api_exception.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/notifications/notification_service.dart';

class RecordingNotifications extends NotificationService {
  final successes = <String>[];
  final errors = <String>[];

  @override
  void showSuccess(String message) => successes.add(message);

  @override
  void showError(String message) => errors.add(message);
}

void main() {
  test('aplica timeout de 45 segundos solo a transcripcion de audio', () async {
    final observedTimeouts = <String, Duration>{};
    final client = ApiClient(
      client: MockClient((request) async => http.Response('{"ok":true}', 200)),
      timeoutForPath: (path, timeout) {
        observedTimeouts[path] = timeout;
        return timeout;
      },
    );

    await client.post('/reports/transcribe-audio', body: {'audio': 'payload'});
    await client.get('/health');
    await client.post('/catalogo/vton/try-on', body: {'image': 'payload'});

    expect(
      observedTimeouts['/reports/transcribe-audio'],
      const Duration(seconds: 45),
    );
    expect(observedTimeouts['/health'], const Duration(seconds: 10));
    expect(
      observedTimeouts['/catalogo/vton/try-on'],
      const Duration(seconds: 90),
    );
  });

  test('incluye el token y decodifica respuestas JSON', () async {
    final client = ApiClient(
      client: MockClient((request) async {
        expect(request.headers['Authorization'], 'Bearer access-token');
        expect(request.url.queryParameters['page'], '1');
        return http.Response('{"status":"ok"}', 200);
      }),
    );
    client.accessToken = 'access-token';

    final response = await client.get('/health', query: {'page': '1'});
    expect(response['status'], 'ok');
  });

  test('convierte errores estructurados en ApiException y notifica', () async {
    final notifications = RecordingNotifications();
    final client = ApiClient(
      client: MockClient(
        (_) async => http.Response(
          '{"detail":{"code":"NOT_FOUND","message":"No existe"}}',
          404,
        ),
      ),
      notifications: notifications,
    );

    await expectLater(
      client.get('/catalog/999'),
      throwsA(
        isA<ApiException>()
            .having((error) => error.statusCode, 'statusCode', 404)
            .having((error) => error.message, 'message', 'No existe')
            .having((error) => error.code, 'code', 'NOT_FOUND'),
      ),
    );
    expect(notifications.errors, ['No existe']);
  });

  test('notifica y convierte errores inesperados del cliente HTTP', () async {
    final notifications = RecordingNotifications();
    final client = ApiClient(
      client: MockClient((_) async => throw Exception('socket closed')),
      notifications: notifications,
    );

    await expectLater(
      client.post('/auth/register', body: {'email': 'a@b.com'}),
      throwsA(
        isA<ApiException>()
            .having((error) => error.statusCode, 'statusCode', 0)
            .having(
              (error) => error.message,
              'message',
              contains('Error al conectar con el servidor'),
            ),
      ),
    );
    expect(
      notifications.errors.first,
      contains('Error al conectar con el servidor'),
    );
  });

  test('convierte detalles de validacion en lista', () async {
    final notifications = RecordingNotifications();
    final client = ApiClient(
      client: MockClient(
        (_) async => http.Response(
          '{"detail":[{"loc":["body","email"],"msg":"email invalido"}]}',
          422,
        ),
      ),
      notifications: notifications,
    );

    await expectLater(
      client.post('/auth/login', body: {}),
      throwsA(
        isA<ApiException>().having(
          (error) => error.message,
          'message',
          'email invalido',
        ),
      ),
    );
    expect(notifications.errors, ['email invalido']);
  });

  test('notifica éxito en solicitudes mutantes', () async {
    final notifications = RecordingNotifications();
    final client = ApiClient(
      client: MockClient((_) async => http.Response('{"id":1}', 201)),
      notifications: notifications,
    );

    await client.post('/auth/register', body: {'email': 'a@b.com'});

    expect(notifications.successes, ['Cuenta creada correctamente.']);
  });
}
