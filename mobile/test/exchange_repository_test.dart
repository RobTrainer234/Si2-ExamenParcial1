import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/features/exchange/data/exchange_models.dart';
import 'package:fashionstore_mobile/features/exchange/data/exchange_repository.dart';

void main() {
  test('lookupSale consulta /sales/lookup/{order} y parsea items con saldo intercambiable', () async {
    final client = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path.endsWith('/sales/lookup/FS-2026-0042'), isTrue);
      return http.Response(
        jsonEncode({
          'sale_id': 42,
          'order_number': 'FS-2026-0042',
          'sale_date': '2026-10-30T14:30:00Z',
          'branch_id': 2,
          'status': 'COMPLETED',
          'items': [
            {
              'id': 501,
              'variant_id': 11,
              'name': 'Camisa Oxford (M / Negro)',
              'sku': 'CAM-001-M-NEG',
              'purchased_quantity': 2,
              'net_paid_line_total': '400.00',
              'remaining_exchangeable_quantity': 1,
            },
          ],
        }),
        200,
      );
    });

    final repo = ExchangeRepository(ApiClient(client: client));
    final sale = await repo.lookupSale('  FS-2026-0042  ');

    expect(sale.saleId, 42);
    expect(sale.orderNumber, 'FS-2026-0042');
    expect(sale.branchId, 2);
    expect(sale.items, hasLength(1));
    expect(sale.items.first.variantId, 11);
    expect(sale.items.first.netPaidLineTotal, 400.0);
    expect(sale.items.first.remainingExchangeableQuantity, 1);
  });

  test('fetchBranchVariants consulta /inventory filtrado por sucursal', () async {
    final client = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path.endsWith('/inventory'), isTrue);
      expect(request.url.queryParameters['branch_id'], '2');
      expect(request.url.queryParameters['page_size'], '100');
      return http.Response(
        jsonEncode({
          'items': [
            {
              'id': 91,
              'branch_id': 2,
              'branch_name': 'FashionStore Norte',
              'product_variant_id': 22,
              'product_id': 7,
              'product_name': 'Chaqueta Urbana',
              'sku': 'CHA-002-L-AZUL',
              'size_id': 3,
              'size_name': 'L',
              'size_type': 'ALPHA',
              'size_sort_order': 40,
              'color_id': 2,
              'color_name': 'Azul',
              'stock_quantity': 6,
              'reserved_quantity': 1,
              'available_quantity': 5,
              'available': true,
            },
          ],
          'page': 1,
          'page_size': 100,
          'total': 1,
          'total_pages': 1,
        }),
        200,
      );
    });

    final repo = ExchangeRepository(ApiClient(client: client));
    final variants = await repo.fetchBranchVariants(2);

    expect(variants, hasLength(1));
    expect(variants.first.variantId, 22);
    expect(variants.first.productName, 'Chaqueta Urbana');
    expect(variants.first.availableQuantity, 5);
  });

  test('requestQuote envia solo variantes y cantidades sin precios del cliente', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path.endsWith('/sales/42/exchange/quote'), isTrue);
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      expect(payload, {
        'returned_variant_id': 11,
        'returned_quantity': 1,
        'new_variant_id': 22,
        'new_quantity': 1,
      });
      expect(payload.containsKey('unit_price'), isFalse);
      return http.Response(
        jsonEncode({
          'sale_id': 42,
          'sale_item_id': 501,
          'returned_variant_id': 11,
          'returned_quantity': 1,
          'new_variant_id': 22,
          'new_quantity': 1,
          'returned_value': '200.00',
          'replacement_unit_price': '230.00',
          'delivered_value': '230.00',
          'difference': '30.00',
          'cash_settlement_eligible': true,
          'available_stock': 5,
          'reserved_stock': 1,
          'expires_at': '2026-11-02T01:30:00Z',
          'quote_fingerprint': 'abcdef0123456789abcdef0123456789',
        }),
        200,
      );
    });

    final repo = ExchangeRepository(ApiClient(client: client));
    final quote = await repo.requestQuote(
      42,
      const ExchangeQuoteRequest(
        returnedVariantId: 11,
        returnedQuantity: 1,
        newVariantId: 22,
        newQuantity: 1,
      ),
    );

    expect(quote.difference, 30.0);
    expect(quote.cashSettlementEligible, isTrue);
    expect(quote.quoteFingerprint, 'abcdef0123456789abcdef0123456789');
  });

  test('finalizeExchange envia huella de cotizacion, idempotency_key y parsea cuarentena', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path.endsWith('/sales/42/exchange'), isTrue);
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      expect(payload, {
        'returned_variant_id': 11,
        'returned_quantity': 1,
        'new_variant_id': 22,
        'new_quantity': 1,
        'quote_fingerprint': 'abcdef0123456789abcdef0123456789',
        'quote_expires_at': '2026-11-02T01:30:00Z',
        'idempotency_key': 'mob-exch-fixed-key-001',
        'cash_tendered': '50.00',
        'cashier_confirmed': false,
        'reason': 'Cambio de talla a L',
      });
      return http.Response(
        jsonEncode({
          'sale_id': 42,
          'order_number': 'FS-2026-0042',
          'returned_variant_id': 11,
          'returned_quantity': 1,
          'new_variant_id': 22,
          'new_quantity': 1,
          'status': 'EXCHANGED',
          'quarantine_id': 77,
          'quarantine_status': 'PENDING',
          'returned_value': '200.00',
          'delivered_value': '230.00',
          'difference': '30.00',
          'cash_tendered': '50.00',
          'cash_change': '20.00',
          'cash_refunded': null,
          'exchanged_at': '2026-11-02T01:12:00Z',
        }),
        200,
      );
    });

    final repo = ExchangeRepository(ApiClient(client: client));
    final receipt = await repo.finalizeExchange(
      42,
      const ExchangeFinalizeRequest(
        returnedVariantId: 11,
        returnedQuantity: 1,
        newVariantId: 22,
        newQuantity: 1,
        quoteFingerprint: 'abcdef0123456789abcdef0123456789',
        quoteExpiresAt: '2026-11-02T01:30:00Z',
        idempotencyKey: 'mob-exch-fixed-key-001',
        cashTendered: '50.00',
        cashierConfirmed: false,
        reason: 'Cambio de talla a L',
      ),
    );

    expect(receipt.status, 'EXCHANGED');
    expect(receipt.quarantineId, 77);
    expect(receipt.quarantineStatus, 'PENDING');
    expect(receipt.cashChange, 20.0);
  });
}
