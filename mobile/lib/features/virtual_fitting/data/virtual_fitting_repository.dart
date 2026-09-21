import '../../../core/network/api_client.dart';

class VirtualFittingRepository {
  VirtualFittingRepository(this._api);
  final ApiClient _api;

  Future<Map<String, dynamic>> start(
    int productId, {
    String deviceInfo = 'mobile-simulator',
  }) async =>
      await _api.post(
            '/virtual-fitting/sessions',
            body: {'product_id': productId, 'device_info': deviceInfo},
          )
          as Map<String, dynamic>;

  Future<Map<String, dynamic>> finish(int sessionId) async =>
      await _api.patch('/virtual-fitting/sessions/$sessionId/finish', body: {})
          as Map<String, dynamic>;

  Future<List<dynamic>> mine() async {
    final response =
        await _api.get('/virtual-fitting/sessions/mine')
            as Map<String, dynamic>;
    return response['items'] as List<dynamic>;
  }

  Future<Map<String, dynamic>> vtonTryOn(
    int productId, {
    String? imageBase64,
    Map<String, dynamic>? metrics,
  }) async {
    final body = <String, dynamic>{'product_id': productId};
    if (imageBase64 != null) body['image_base64'] = imageBase64;
    if (metrics != null) body['metrics'] = metrics;
    return await _api.post('/catalogo/vton/try-on', body: body)
        as Map<String, dynamic>;
  }
}
