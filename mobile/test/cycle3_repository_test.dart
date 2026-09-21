import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/features/purchases/data/purchase_repository.dart';
import 'package:fashionstore_mobile/features/recommendations/data/recommendation_repository.dart';
import 'package:fashionstore_mobile/features/virtual_fitting/data/virtual_fitting_repository.dart';

void main() {
  test('consume superficies moviles del ciclo 3', () async {
    final paths = <String>[];
    final client = MockClient((request) async {
      paths.add(request.url.path);
      if (request.url.path.endsWith('/purchases/mine')) {
        return http.Response(jsonEncode({'items': [], 'total': 0}), 200);
      }
      if (request.url.path.endsWith('/recommendations/mine')) {
        return http.Response(
          jsonEncode({
            'items': [
              {'product_id': 1, 'reason': 'Disponible'},
            ],
          }),
          200,
        );
      }
      if (request.url.path.endsWith('/virtual-fitting/sessions') &&
          request.method == 'POST') {
        expect(jsonDecode(request.body)['product_id'], 1);
        return http.Response(jsonEncode({'id': 7, 'status': 'STARTED'}), 201);
      }
      if (request.url.path.endsWith('/virtual-fitting/sessions/7/finish')) {
        return http.Response(jsonEncode({'id': 7, 'status': 'FINISHED'}), 200);
      }
      return http.Response('{}', 200);
    });
    final api = ApiClient(client: client);

    expect((await PurchaseRepository(api).mine())['total'], 0);
    expect(
      (await RecommendationRepository(api).mine()).single['product_id'],
      1,
    );
    expect((await VirtualFittingRepository(api).start(1))['id'], 7);
    expect(
      (await VirtualFittingRepository(api).finish(7))['status'],
      'FINISHED',
    );
    expect(paths, contains('/api/v1/purchases/mine'));
    expect(paths, contains('/api/v1/recommendations/mine'));
  });
}
