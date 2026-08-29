import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/errors/api_exception.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';

void main() {
  test('incluye el token y decodifica respuestas JSON', () async {
    final client = ApiClient(client: MockClient((request) async {
      expect(request.headers['Authorization'], 'Bearer access-token');
      expect(request.url.queryParameters['page'], '1');
      return http.Response('{"status":"ok"}', 200);
    }));
    client.accessToken = 'access-token';

    final response = await client.get('/health', query: {'page': '1'});
    expect(response['status'], 'ok');
  });

  test('convierte errores estructurados en ApiException', () async {
    final client = ApiClient(client: MockClient((_) async => http.Response(
          '{"detail":{"code":"NOT_FOUND","message":"No existe"}}',
          404,
        )));

    expect(
      () => client.get('/catalog/999'),
      throwsA(isA<ApiException>().having((error) => error.statusCode, 'statusCode', 404).having((error) => error.message, 'message', 'No existe')),
    );
  });
}
