import '../../../core/network/api_client.dart';

class RecommendationRepository {
  RecommendationRepository(this._api);
  final ApiClient _api;

  Future<List<dynamic>> mine() async {
    final response =
        await _api.get('/recommendations/mine') as Map<String, dynamic>;
    return response['items'] as List<dynamic>;
  }
}
