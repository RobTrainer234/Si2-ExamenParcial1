import '../../../core/network/api_client.dart';

class CartRepository {
  CartRepository(this._api);
  final ApiClient _api;

  Future<Map<String, dynamic>> get() async => await _api.get('/cart') as Map<String, dynamic>;
  Future<Map<String, dynamic>> add(int variantId, {int quantity = 1}) async => await _api.post('/cart/items', body: {'product_variant_id': variantId, 'quantity': quantity}) as Map<String, dynamic>;
  Future<Map<String, dynamic>> remove(int itemId) async => await _api.delete('/cart/items/$itemId') as Map<String, dynamic>;
  Future<Map<String, dynamic>> update(int itemId, int quantity) async => await _api.patch('/cart/items/$itemId', body: {'quantity': quantity}) as Map<String, dynamic>;
  Future<Map<String, dynamic>> purchase(int branchId) async => await _api.post('/purchases/digital', body: {'branch_id': branchId}) as Map<String, dynamic>;
  Future<Map<String, dynamic>> pay(int saleId, String key) async => await _api.post('/payments/electronic', body: {'sale_id': saleId, 'idempotency_key': key, 'method': 'CARD'}) as Map<String, dynamic>;
  Future<void> approve(String reference, String amount) async { await _api.post('/payments/electronic/notification', body: {'transaction_reference': reference, 'status': 'APPROVED', 'amount': amount}); }
}
