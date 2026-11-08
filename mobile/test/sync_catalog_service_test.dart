import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/sync_catalog_service.dart';

class MockApiClient extends ApiClient {
  MockApiClient({required this.handler});
  final Future<dynamic> Function(String path, Map<String, String>? query) handler;

  @override
  Future<dynamic> get(String path, {Map<String, String>? query}) =>
      handler(path, query);
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late OfflineDatabase offlineDb;

  setUp(() {
    offlineDb = OfflineDatabase(inMemory: true);
  });

  tearDown(() async {
    await offlineDb.close();
  });

  final fakeSyncResponse = {
    'metadata': {
      'tenant_id': 10,
      'tenant_name': 'Boutique Aurora',
      'branch_id': 2,
      'branch_name': 'Sucursal Norte',
      'sync_timestamp': '2026-10-23T19:50:00Z',
      'catalog_version': 'v1-test',
    },
    'categories': [
      {'id': 1, 'name': 'Vestidos', 'is_active': true},
    ],
    'products': [
      {
        'id': 100,
        'category_id': 1,
        'category_name': 'Vestidos',
        'name': 'Vestido Gala',
        'code': 'VG-001',
        'slug': 'vestido-gala',
        'price': 199.99,
        'image_url': null,
        'is_active': true,
      },
    ],
    'variants': [
      {
        'id': 1001,
        'product_id': 100,
        'sku': 'VG-001-M-RED',
        'size_id': 2,
        'size_name': 'M',
        'color_id': 3,
        'color_name': 'Rojo',
        'price': 199.99,
        'is_active': true,
      },
    ],
    'inventory': [
      {
        'product_variant_id': 1001,
        'stock_quantity': 8,
        'reserved_quantity': 1,
        'available_quantity': 7,
      },
    ],
  };

  test('T1.4.3: syncCatalog descarga exitosamente y guarda en OfflineDatabase', () async {
    String? calledPath;
    Map<String, String>? calledQuery;

    final mockApi = MockApiClient(
      handler: (path, query) async {
        calledPath = path;
        calledQuery = query;
        return fakeSyncResponse;
      },
    );

    final service = SyncCatalogService(
      api: mockApi,
      offlineDb: offlineDb,
    );

    expect(service.isSyncing, isFalse);
    expect(service.lastSync, isNull);

    final success = await service.syncCatalog(branchId: 2);

    expect(success, isTrue);
    expect(calledPath, '/sync/catalog');
    expect(calledQuery, {'branch_id': '2'});
    expect(service.isSyncing, isFalse);
    expect(service.syncError, isNull);
    expect(service.lastMetadata?.tenantId, 10);
    expect(service.lastMetadata?.branchId, 2);

    // Verify stored in SQLite
    expect(await offlineDb.hasOfflineData(), isTrue);
    final products = await offlineDb.listProducts();
    expect(products.items.length, 1);
    expect(products.items.first.name, 'Vestido Gala');
  });

  test('T1.4.3: syncCatalog maneja errores y registra syncError', () async {
    final mockApi = MockApiClient(
      handler: (path, query) async {
        throw Exception('Conexión rechazada');
      },
    );

    final service = SyncCatalogService(
      api: mockApi,
      offlineDb: offlineDb,
    );

    final success = await service.syncCatalog();

    expect(success, isFalse);
    expect(service.isSyncing, isFalse);
    expect(service.syncError, contains('Conexión rechazada'));
    expect(await offlineDb.hasOfflineData(), isFalse);
  });
}
