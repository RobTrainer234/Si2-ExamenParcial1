import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/config/app_config.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/features/cart/data/cart_repository.dart';

void main() {
  test('mantiene payload legacy para compra pickup por defecto', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path.endsWith('/purchases/digital'), isTrue);
      expect(jsonDecode(request.body), {'branch_id': 3});
      return http.Response('{"id":10,"order_number":"FS-10"}', 200);
    });

    final result = await CartRepository(ApiClient(client: client)).purchase(3);

    expect(result['order_number'], 'FS-10');
  });

  test('envia fulfillment de delivery con datos de envio estructurados', () async {
    final shippingDetails = {
      'recipient_name': 'Ana Pérez',
      'recipient_ci': '1234567',
      'recipient_phone': '70000000',
      'department_or_city': 'Santa Cruz',
      'zone': 'Equipetrol',
      'street': 'Av. San Martín',
      'house_number': '55',
      'reference': 'Portón negro',
    };
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path.endsWith('/purchases/digital'), isTrue);
      expect(jsonDecode(request.body), {
        'branch_id': 4,
        'fulfillment_type': 'DELIVERY',
        'shipping_details': shippingDetails,
      });
      return http.Response('{"id":11,"order_number":"FS-11"}', 200);
    });

    final result = await CartRepository(ApiClient(client: client)).purchase(
      4,
      fulfillmentType: 'DELIVERY',
      shippingDetails: shippingDetails,
    );

    expect(result['order_number'], 'FS-11');
  });

  test('envia firma sandbox al aprobar pago electronico demo', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(
        request.url.path.endsWith('/payments/electronic/notification'),
        isTrue,
      );
      expect(
        request.headers['X-Sandbox-Signature'],
        AppConfig.sandboxPaymentWebhookSecret,
      );
      expect(jsonDecode(request.body)['transaction_reference'], 'SANDBOX-1');
      return http.Response('{}', 200);
    });

    await CartRepository(
      ApiClient(client: client),
    ).approve('SANDBOX-1', '200.00');
  });

  test('confirma pago Stripe con payment intent existente', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path.endsWith('/payments/stripe/confirm'), isTrue);
      expect(jsonDecode(request.body), {'payment_intent_id': 'pi_test_123'});
      return http.Response('{"id":42,"order_number":"ORD-42"}', 200);
    });

    final result = await CartRepository(
      ApiClient(client: client),
    ).confirmStripePayment('pi_test_123');

    expect(result['order_number'], 'ORD-42');
  });
}
