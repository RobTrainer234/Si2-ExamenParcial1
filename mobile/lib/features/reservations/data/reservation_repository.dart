import '../../../core/network/api_client.dart';
import 'reservation_models.dart';

class ReservationRepository {
  ReservationRepository(this._api);
  final ApiClient _api;

  Future<Reservation> create({required int branchId, required List<Map<String, int>> items, required DateTime scheduledFor}) async {
    final response = await _api.post('/reservations', body: {
      'branch_id': branchId,
      'scheduled_for': scheduledFor.toUtc().toIso8601String(),
      'items': items,
    });
    return Reservation.fromJson(response as Map<String, dynamic>);
  }

  Future<List<Reservation>> mine() async { final response = await _api.get('/reservations/mine', query: {'page': '1', 'page_size': '100'}); return ((response as Map<String, dynamic>)['items'] as List<dynamic>).map((item) => Reservation.fromJson(item as Map<String, dynamic>)).toList(); }
  Future<Reservation> get(int id) async => Reservation.fromJson(await _api.get('/reservations/$id') as Map<String, dynamic>);
  Future<Reservation> cancel(int id) async => Reservation.fromJson(await _api.patch('/reservations/$id/cancel', body: {}) as Map<String, dynamic>);
}
