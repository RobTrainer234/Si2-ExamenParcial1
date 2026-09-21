import '../../../core/network/api_client.dart';

class PurchaseRepository {
  PurchaseRepository(this._api);
  final ApiClient _api;

  Future<Map<String, dynamic>> mine() async =>
      await _api.get('/purchases/mine') as Map<String, dynamic>;

  Future<Map<String, dynamic>> detail(int id) async =>
      await _api.get('/purchases/mine/$id') as Map<String, dynamic>;
}
