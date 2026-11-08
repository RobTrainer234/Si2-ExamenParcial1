import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';
import 'package:fashionstore_mobile/features/catalog/data/catalog_repository.dart';

class FailingApiClient extends ApiClient {
  @override
  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    throw const SocketException('No Internet Connection');
  }
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late Directory tempDir;
  late String dbPath;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('fashionstore_test_');
    dbPath = p.join(tempDir.path, 'test_offline.db');
  });

  tearDown(() async {
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  test('T1.4.4: CatalogRepository consulta SQLite sin conexión y conserva datos entre reinicios', () async {
    // 1. First session: populate the exact SQLite file that the second session reopens.
    final offlineDb1 = OfflineDatabase(databasePath: dbPath);
    final sampleSync = SyncCatalogResponse(
      metadata: const SyncMetadata(
        tenantId: 1,
        tenantName: 'Empresa Demo',
        branchId: 10,
        branchName: 'Sucursal Recoleta',
        syncTimestamp: '2026-10-23T20:00:00Z',
        catalogVersion: 'v1.0',
      ),
      categories: [
        const SyncCategory(id: 1, name: 'Calzado', isActive: true),
      ],
      products: [
        const SyncProduct(
          id: 50,
          categoryId: 1,
          categoryName: 'Calzado',
          name: 'Botines Cuero Negro',
          code: 'BOT-001',
          slug: 'botines-cuero-negro',
          price: 240.0,
          imageUrl: null,
          isActive: true,
        ),
      ],
      variants: [
        const SyncVariant(
          id: 501,
          productId: 50,
          sku: 'BOT-001-41-NEG',
          sizeId: 5,
          sizeName: '41',
          colorId: 1,
          colorName: 'Negro',
          price: 240.0,
          isActive: true,
        ),
      ],
      inventory: [
        const SyncInventory(
          productVariantId: 501,
          stockQuantity: 15,
          reservedQuantity: 2,
          availableQuantity: 13,
        ),
      ],
    );

    await offlineDb1.saveCatalogSync(sampleSync);

    await offlineDb1.close();

    // 2. Second session: reopen the same file and serve repository reads offline.
    final offlineDb2 = OfflineDatabase(databasePath: dbPath);
    final repo = CatalogRepository(
      FailingApiClient(),
      offlineDb: offlineDb2,
    );

    // Call list() with network failing -> returns offline items
    final page = await repo.list();
    expect(page.items.length, 1);
    expect(page.items.first.name, 'Botines Cuero Negro');
    expect(page.items.first.price, 240.0);

    // Call detail() with network failing -> returns offline detail
    final detail = await repo.detail(50);
    expect(detail.id, 50);
    expect(detail.name, 'Botines Cuero Negro');
    expect(detail.variants.length, 1);
    expect(detail.variants.first.sizeName, '41');

    // Call availability() with network failing -> returns offline branch inventory
    final availability = await repo.availability(50, detail.variants.first);
    expect(availability.length, 1);
    expect(availability.first.branchName, 'Sucursal Recoleta');
    expect(availability.first.stock, 13);
    expect(availability.first.available, isTrue);

    await offlineDb2.close();
  });
}
