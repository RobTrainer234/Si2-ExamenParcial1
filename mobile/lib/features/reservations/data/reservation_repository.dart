import '../../../core/network/api_client.dart';

class ReservationRepository {
  ReservationRepository(this._api);
  final ApiClient _api;

  Future<void> create({required int branchId, required int variantId, required DateTime scheduledFor, int quantity = 1}) async {
    await _api.post('/reservations', body: {
      'branch_id': branchId,
      'scheduled_for': scheduledFor.toUtc().toIso8601String(),
      'items': [{'product_variant_id': variantId, 'quantity': quantity}],
    });
  }
}
