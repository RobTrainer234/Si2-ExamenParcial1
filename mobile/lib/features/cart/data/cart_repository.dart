import '../../../core/config/app_config.dart';
import '../../../core/network/api_client.dart';

class CartRepository {
  CartRepository(this._api);
  final ApiClient _api;

  Future<Map<String, dynamic>> get() async =>
      await _api.get('/cart') as Map<String, dynamic>;
  Future<Map<String, dynamic>> add(int variantId, {int quantity = 1}) async =>
      await _api.post(
            '/cart/items',
            body: {'product_variant_id': variantId, 'quantity': quantity},
          )
          as Map<String, dynamic>;
  Future<Map<String, dynamic>> remove(int itemId) async =>
      await _api.delete('/cart/items/$itemId') as Map<String, dynamic>;
  Future<Map<String, dynamic>> update(int itemId, int quantity) async =>
      await _api.patch('/cart/items/$itemId', body: {'quantity': quantity})
          as Map<String, dynamic>;
  Future<Map<String, dynamic>> purchase(
    int branchId, {
    String? fulfillmentType,
    Map<String, dynamic>? shippingDetails,
  }) async {
    final body = <String, dynamic>{'branch_id': branchId};
    if (fulfillmentType != null) body['fulfillment_type'] = fulfillmentType;
    if (shippingDetails != null) body['shipping_details'] = shippingDetails;
    return await _api.post('/purchases/digital', body: body)
        as Map<String, dynamic>;
  }
  Future<Map<String, dynamic>> pay(int saleId, String key) async =>
      await _api.post(
            '/payments/electronic',
            body: {'sale_id': saleId, 'idempotency_key': key, 'method': 'CARD'},
          )
          as Map<String, dynamic>;
  Future<Map<String, dynamic>> createStripeIntent(
    int saleId,
    String key,
  ) async =>
      await _api.post(
            '/payments/stripe/intent',
            body: {'sale_id': saleId, 'idempotency_key': key, 'method': 'CARD'},
          )
          as Map<String, dynamic>;

  Future<Map<String, dynamic>> confirmStripePayment(
    String paymentIntentId,
  ) async =>
      await _api.post(
            '/payments/stripe/confirm',
            body: {'payment_intent_id': paymentIntentId},
          )
          as Map<String, dynamic>;

  Future<void> approve(String reference, String amount) async {
    await _api.post(
      '/payments/electronic/notification',
      headers: {'X-Sandbox-Signature': AppConfig.sandboxPaymentWebhookSecret},
      body: {
        'transaction_reference': reference,
        'status': 'APPROVED',
        'amount': amount,
      },
    );
  }
}
