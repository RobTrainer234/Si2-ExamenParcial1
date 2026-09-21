import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/errors/api_exception.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/features/virtual_fitting/data/virtual_fitting_repository.dart';

void main() {
  test(
    'sends captured image base64 to existing VTON try-on endpoint',
    () async {
      final client = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path.endsWith('/catalogo/vton/try-on'), isTrue);
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body['product_id'], 7);
        expect(body['image_base64'], 'captured-image-b64');
        expect(body['metrics']['device'], 'camera_capture');
        return http.Response('{"composite_image_base64":"ZmFrZQ=="}', 200);
      });

      final result = await VirtualFittingRepository(ApiClient(client: client))
          .vtonTryOn(
            7,
            imageBase64: 'captured-image-b64',
            metrics: {'device': 'camera_capture'},
          );

      expect(result['composite_image_base64'], 'ZmFrZQ==');
    },
  );

  test(
    'surfaces unavailable VTON errors instead of local fallback data',
    () async {
      final client = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': {
              'code': 'VTON_PROVIDER_UNAVAILABLE',
              'message': 'El motor VTON no está disponible en este momento.',
            },
          }),
          503,
        );
      });

      expect(
        () => VirtualFittingRepository(
          ApiClient(client: client),
        ).vtonTryOn(7, imageBase64: 'captured-image-b64'),
        throwsA(
          isA<ApiException>()
              .having((error) => error.statusCode, 'statusCode', 503)
              .having(
                (error) => error.message,
                'message',
                contains('motor VTON no está disponible'),
              ),
        ),
      );
    },
  );
}
