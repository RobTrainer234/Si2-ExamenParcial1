import '../../../core/network/api_client.dart';
import 'catalog_models.dart';

class CatalogRepository {
  CatalogRepository(this._api);
  final ApiClient _api;

  Future<CatalogPage> list({String query = '', int page = 1}) async {
    final json =
        await _api.get(
              '/catalog',
              query: {
                'page': '$page',
                'page_size': '20',
                if (query.isNotEmpty) 'q': query,
              },
            )
            as Map<String, dynamic>;
    return CatalogPage(
      (json['items'] as List<dynamic>)
          .map((item) => CatalogItem.fromJson(item as Map<String, dynamic>))
          .toList(),
      json['total_pages'] as int,
    );
  }

  Future<CatalogDetail> detail(int id) async => CatalogDetail.fromJson(
    await _api.get('/catalog/$id') as Map<String, dynamic>,
  );

  Future<List<AvailabilityItem>> availability(
    int id,
    CatalogVariant variant,
  ) async {
    final json =
        await _api.get(
              '/catalog/$id/availability',
              query: {
                'size_id': '${variant.sizeId}',
                'color_id': '${variant.colorId}',
              },
            )
            as List<dynamic>;
    return json
        .map((item) => AvailabilityItem.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Map<String, dynamic>>> getBranches() async {
    final json = await _api.get('/catalog/filters') as Map<String, dynamic>;
    final list = (json['branches'] as List<dynamic>?) ?? const [];
    return list.map((b) => Map<String, dynamic>.from(b as Map)).toList();
  }
}
