import '../../../core/network/api_client.dart';
import '../../../core/offline/offline_database.dart';
import 'catalog_models.dart';

class CatalogRepository {
  CatalogRepository(this._api, {this.offlineDb});

  final ApiClient _api;
  final OfflineDatabase? offlineDb;

  Future<CatalogPage> list({
    String query = '',
    int page = 1,
  }) async {
    try {
      final json = await _api.get(
        '/catalog',
        query: {
          'page': '$page',
          'page_size': '20',
          if (query.isNotEmpty) 'q': query,
        },
      ) as Map<String, dynamic>;
      return CatalogPage(
        (json['items'] as List<dynamic>)
            .map((item) => CatalogItem.fromJson(item as Map<String, dynamic>))
            .toList(),
        json['total_pages'] as int,
      );
    } catch (e) {
      final db = offlineDb;
      if (db != null && await db.hasOfflineData()) {
        return await db.listProducts(query: query, page: page);
      }
      rethrow;
    }
  }

  Future<CatalogPage> listOffline({
    String query = '',
    int page = 1,
  }) async {
    final db = offlineDb;
    if (db != null && await db.hasOfflineData()) {
      return await db.listProducts(query: query, page: page);
    }
    throw Exception('No hay catálogo descargado sin conexión.');
  }

  Future<CatalogDetail> detail(int id) async {
    try {
      final json = await _api.get('/catalog/$id') as Map<String, dynamic>;
      return CatalogDetail.fromJson(json);
    } catch (e) {
      final db = offlineDb;
      if (db != null) {
        final local = await db.getProductDetail(id);
        if (local != null) return local;
      }
      rethrow;
    }
  }

  Future<List<AvailabilityItem>> availability(
    int id,
    CatalogVariant variant,
  ) async {
    try {
      final json = await _api.get(
        '/catalog/$id/availability',
        query: {
          'size_id': '${variant.sizeId}',
          'color_id': '${variant.colorId}',
        },
      ) as List<dynamic>;
      return json
          .map((item) =>
              AvailabilityItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      final db = offlineDb;
      if (db != null) {
        return await db.getVariantAvailability(id, variant);
      }
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getBranches() async {
    final json = await _api.get('/catalog/filters') as Map<String, dynamic>;
    final list = (json['branches'] as List<dynamic>?) ?? const [];
    return list.map((b) => Map<String, dynamic>.from(b as Map)).toList();
  }
}
