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
            .having((error) => error.message, 'message', 'No existe'),
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
