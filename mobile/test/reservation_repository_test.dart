import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/features/reservations/data/reservation_repository.dart';

Map<String, dynamic> reservationJson(int id, String status) => {
  'id': id,
  'branch_name': 'Centro',
  'status': status,
  'scheduled_for': '2030-01-02T10:00:00Z',
  'expires_at': '2030-01-02T12:00:00Z',
  'items': [
    {
      'product_name': 'Camisa',
      'size_name': 'M',
      'color_name': 'Azul',
      'quantity': 1,
      'unit_price': '100.00',
    },
  ],
};

void main() {
  test('crea, consulta y cancela reservas', () async {
    final client = MockClient((request) async {
      if (request.method == 'POST') {
        return http.Response(jsonEncode(reservationJson(1, 'PENDING')), 201);
      }
      if (request.url.path.endsWith('/mine')) {
        return http.Response(
          jsonEncode({
            'items': [reservationJson(1, 'PENDING')],
          }),
          200,
        );
      }
      return http.Response(jsonEncode(reservationJson(1, 'CANCELLED')), 200);
    });
    final repository = ReservationRepository(ApiClient(client: client));

    final created = await repository.create(
      branchId: 1,
      items: [
        {'product_variant_id': 2, 'quantity': 1},
      ],
      scheduledFor: DateTime.utc(2030, 1, 2, 10),
    );
    expect(created.status, 'PENDING');
    expect((await repository.mine()).single.id, 1);
    expect((await repository.cancel(1)).status, 'CANCELLED');
  });
}
