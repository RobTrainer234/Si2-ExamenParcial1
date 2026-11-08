import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late OfflineDatabase offlineDb;
  late Directory tempDir;

  setUp(() async {
    offlineDb = OfflineDatabase(inMemory: true);
    tempDir = await Directory.systemTemp.createTemp('fashionstore_offline_db_test_');
  });

  tearDown(() async {
    await offlineDb.close();
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  final sampleSync = SyncCatalogResponse(
    metadata: const SyncMetadata(
      tenantId: 101,
      tenantName: 'Boutique Aurora',
      branchId: 5,
      branchName: 'Sucursal Central',
      syncTimestamp: '2026-10-23T19:30:00Z',
      catalogVersion: 'v1.0-tenant-101-branch-5',
    ),
    categories: [
      const SyncCategory(id: 1, name: 'Vestidos', isActive: true),
      const SyncCategory(id: 2, name: 'Pantalones', isActive: true),
    ],
    products: [
      const SyncProduct(
        id: 10,
        categoryId: 1,
        categoryName: 'Vestidos',
        name: 'Vestido Seda Aurora',
        code: 'VES-001',
        slug: 'vestido-seda-aurora',
        price: 159.99,
        imageUrl: 'https://images.example.com/vestido1.jpg',
        isActive: true,
      ),
      const SyncProduct(
        id: 20,
        categoryId: 2,
        categoryName: 'Pantalones',
        name: 'Pantalón Lino Boreal',
        code: 'PAN-001',
        slug: 'pantalon-lino-boreal',
        price: 89.50,
        imageUrl: null,
        isActive: true,
      ),
    ],
    variants: [
      const SyncVariant(
        id: 101,
        productId: 10,
        sku: 'VES-001-S-BLU',
        sizeId: 1,
        sizeName: 'S',
        colorId: 2,
        colorName: 'Azul',
        price: 159.99,
        isActive: true,
      ),
      const SyncVariant(
        id: 102,
        productId: 10,
        sku: 'VES-001-M-BLU',
        sizeId: 2,
        sizeName: 'M',
        colorId: 2,
        colorName: 'Azul',
        price: 159.99,
        isActive: true,
      ),
      const SyncVariant(
        id: 201,
        productId: 20,
        sku: 'PAN-001-38-NEG',
        sizeId: 3,
        sizeName: '38',
        colorId: 1,
        colorName: 'Negro',
        price: 89.50,
        isActive: true,
      ),
    ],
    inventory: [
      const SyncInventory(
        productVariantId: 101,
        stockQuantity: 12,
        reservedQuantity: 2,
        availableQuantity: 10,
      ),
      const SyncInventory(
        productVariantId: 102,
        stockQuantity: 5,
        reservedQuantity: 0,
        availableQuantity: 5,
      ),
      const SyncInventory(
        productVariantId: 201,
        stockQuantity: 0,
        reservedQuantity: 0,
        availableQuantity: 0,
      ),
    ],
  );

  test('T1.4.2: almacena y recupera metadatos y catálogo sincronizado', () async {
    expect(await offlineDb.hasOfflineData(), isFalse);

    await offlineDb.saveCatalogSync(sampleSync);

    expect(await offlineDb.hasOfflineData(), isTrue);

    final metadata = await offlineDb.getMetadata();
    expect(metadata, isNotNull);
    expect(metadata!.tenantId, 101);
    expect(metadata.tenantName, 'Boutique Aurora');
    expect(metadata.branchId, 5);
    expect(metadata.branchName, 'Sucursal Central');
    expect(metadata.catalogVersion, 'v1.0-tenant-101-branch-5');

    final categories = await offlineDb.getCategories();
    expect(categories.length, 2);
    expect(categories.map((c) => c.name), containsAll(['Vestidos', 'Pantalones']));
  });

  test('T1.4.2: listProducts filtra por texto, categoría y soporte de paginación', () async {
    await offlineDb.saveCatalogSync(sampleSync);

    // List all
    final allPage = await offlineDb.listProducts();
    expect(allPage.items.length, 2);
    expect(allPage.totalPages, 1);

    // Query filter
    final filteredPage = await offlineDb.listProducts(query: 'seda');
    expect(filteredPage.items.length, 1);
    expect(filteredPage.items.first.name, 'Vestido Seda Aurora');

    // Category filter
    final catPage = await offlineDb.listProducts(categoryId: 2);
    expect(catPage.items.length, 1);
    expect(catPage.items.first.name, 'Pantalón Lino Boreal');

    // Non-existent filter
    final emptyPage = await offlineDb.listProducts(query: 'noexiste');
    expect(emptyPage.items, isEmpty);
  });

  test('T1.4.2: getProductDetail obtiene variantes y disponibilidad local de inventario', () async {
    await offlineDb.saveCatalogSync(sampleSync);

    final detail = await offlineDb.getProductDetail(10);
    expect(detail, isNotNull);
    expect(detail!.id, 10);
    expect(detail.name, 'Vestido Seda Aurora');
    expect(detail.categoryName, 'Vestidos');
    expect(detail.variants.length, 2);
    expect(detail.variants.first.sizeName, 'S');
    expect(detail.variants.first.colorName, 'Azul');

    // Availability for a variant
    final avail = await offlineDb.getVariantAvailability(10, detail.variants.first);
    expect(avail.length, 1);
    expect(avail.first.branchName, 'Sucursal Central');
    expect(avail.first.stock, 10); // available_quantity
  });

  test('CU-06: persists catalog data after closing and reopening the same SQLite file', () async {
    final dbPath = p.join(tempDir.path, 'persistent_catalog.db');
    final firstSession = OfflineDatabase(databasePath: dbPath);
    await firstSession.saveCatalogSync(sampleSync);
    await firstSession.close();

    final secondSession = OfflineDatabase(databasePath: dbPath);
    expect(await secondSession.hasOfflineData(), isTrue);
    expect((await secondSession.getMetadata())!.catalogVersion,
        'v1.0-tenant-101-branch-5');
    expect(
      (await secondSession.listProducts()).items.map((item) => item.name),
      contains('Vestido Seda Aurora'),
    );
    await secondSession.close();
  });

  test('CU-06/CU-25: upgrades an actual v1 SQLite file to the v2 schema', () async {
    final dbPath = p.join(tempDir.path, 'v1_catalog.db');
    final v1 = await databaseFactoryFfi.openDatabase(
      dbPath,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (db, version) async {
          await db.execute('''
            CREATE TABLE metadata (
              branch_id INTEGER PRIMARY KEY,
              tenant_id INTEGER NOT NULL,
              tenant_name TEXT NOT NULL,
              branch_name TEXT NOT NULL,
              sync_timestamp TEXT NOT NULL,
              catalog_version TEXT NOT NULL
            )
          ''');
          await db.execute('''
            CREATE TABLE categories (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              is_active INTEGER NOT NULL DEFAULT 1
            )
          ''');
          await db.execute('''
            CREATE TABLE products (
              id INTEGER PRIMARY KEY,
              category_id INTEGER NOT NULL,
              category_name TEXT NOT NULL,
              name TEXT NOT NULL,
              code TEXT NOT NULL,
              slug TEXT NOT NULL,
              price REAL NOT NULL,
              image_url TEXT,
              is_active INTEGER NOT NULL DEFAULT 1
            )
          ''');
          await db.execute('''
            CREATE TABLE variants (
              id INTEGER PRIMARY KEY,
              product_id INTEGER NOT NULL,
              sku TEXT NOT NULL,
              size_id INTEGER NOT NULL,
              size_name TEXT NOT NULL,
              color_id INTEGER NOT NULL,
              color_name TEXT NOT NULL,
              price REAL NOT NULL,
              is_active INTEGER NOT NULL DEFAULT 1
            )
          ''');
          await db.execute('''
            CREATE TABLE inventory (
              product_variant_id INTEGER PRIMARY KEY,
              stock_quantity INTEGER NOT NULL DEFAULT 0,
              reserved_quantity INTEGER NOT NULL DEFAULT 0,
              available_quantity INTEGER NOT NULL DEFAULT 0
            )
          ''');
        },
      ),
    );
    await v1.close();

    final upgraded = OfflineDatabase(databasePath: dbPath);
    await upgraded.insertOperation(const OfflineOperationRecord(
      clientOperationId: 'migration-op-1',
      branchId: 5,
      operationType: 'SALE',
      status: 'PENDING_SYNC',
      payloadJson: '{}',
      createdAt: '2026-10-23T20:00:00Z',
    ));
    expect(await upgraded.countPendingOperations(), 1);
    await upgraded.close();
  });

  test('T1.4.2: clearAll purga completamente las tablas locales', () async {
    await offlineDb.saveCatalogSync(sampleSync);
    expect(await offlineDb.hasOfflineData(), isTrue);

    await offlineDb.clearAll();

    expect(await offlineDb.hasOfflineData(), isFalse);
    expect(await offlineDb.getMetadata(), isNull);
    expect(await offlineDb.getCategories(), isEmpty);
    final page = await offlineDb.listProducts();
    expect(page.items, isEmpty);
  });
}
