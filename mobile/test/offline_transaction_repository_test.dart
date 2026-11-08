import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';
import 'package:fashionstore_mobile/core/offline/offline_transaction_repository.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late OfflineDatabase offlineDb;
  late OfflineTransactionRepository repo;

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
      const SyncCategory(id: 1, name: 'Pantalones', isActive: true),
    ],
    products: [
      const SyncProduct(
        id: 10,
        categoryId: 1,
        categoryName: 'Pantalones',
        name: 'Jeans Clásico',
        code: 'JNS-001',
        slug: 'jeans-clasico',
        price: 150.0,
        imageUrl: null,
        isActive: true,
      ),
    ],
    variants: [
      const SyncVariant(
        id: 1001,
        productId: 10,
        sku: 'JNS-001-32',
        sizeId: 1,
        sizeName: '32',
        colorId: 1,
        colorName: 'Azul',
        price: 150.0,
        isActive: true,
      ),
    ],
    inventory: [
      const SyncInventory(
        productVariantId: 1001,
        stockQuantity: 10,
        reservedQuantity: 0,
        availableQuantity: 10,
      ),
    ],
  );

  setUp(() async {
    offlineDb = OfflineDatabase(inMemory: true);
    await offlineDb.saveCatalogSync(sampleSync);
    repo = OfflineTransactionRepository(offlineDb);
  });

  tearDown(() async {
    await offlineDb.close();
  });

  test('T2.3.2: recordOfflineSale deducts provisional stock in SQLite and stores operation as PENDING_SYNC', () async {
    const salePayload = OfflineSalePayload(
      items: [
        OfflineSaleItem(
          productVariantId: 1001,
          quantity: 2,
          unitPrice: 150.0,
        ),
      ],
      total: 300.0,
      discount: 0.0,
    );

    final record = await repo.recordOfflineSale(
      branchId: 5,
      payload: salePayload,
    );

    expect(record.clientOperationId, startsWith('op-mob-'));
    expect(record.branchId, equals(5));
    expect(record.operationType, equals('SALE'));
    expect(record.status, equals('PENDING_SYNC'));

    // Check inventory deduction
    final db = await offlineDb.database;
    final invRows = await db.query(
      OfflineDatabase.tableInventory,
      where: 'product_variant_id = ?',
      whereArgs: [1001],
    );
    expect(invRows.first['stock_quantity'], equals(8));
    expect(invRows.first['available_quantity'], equals(8));

    // Check count of pending
    final pendingCount = await repo.countPendingOperations();
    expect(pendingCount, equals(1));
  });

  test('T2.3.3: recordOfflineReservation updates reserved stock in SQLite and stores operation as PENDING_SYNC', () async {
    const resPayload = OfflineReservationPayload(
      customerName: 'Valeria Morales',
      customerPhone: '77712345',
      items: [
        OfflineReservationItem(
          productVariantId: 1001,
          quantity: 3,
        ),
      ],
    );

    final record = await repo.recordOfflineReservation(
      branchId: 5,
      payload: resPayload,
    );

    expect(record.clientOperationId, startsWith('op-mob-'));
    expect(record.operationType, equals('RESERVATION'));
    expect(record.status, equals('PENDING_SYNC'));

    // Check reservation stock update
    final db = await offlineDb.database;
    final invRows = await db.query(
      OfflineDatabase.tableInventory,
      where: 'product_variant_id = ?',
      whereArgs: [1001],
    );
    expect(invRows.first['reserved_quantity'], equals(3));
    expect(invRows.first['available_quantity'], equals(7));
  });

  test('T2.3.1: listOperations and updateOperation correctly manage outbox lifecycle', () async {
    final sale = await repo.recordOfflineSale(
      branchId: 5,
      payload: const OfflineSalePayload(
        items: [
          OfflineSaleItem(productVariantId: 1001, quantity: 1, unitPrice: 150.0),
        ],
        total: 150.0,
      ),
    );

    final all = await repo.listOperations();
    expect(all.length, equals(1));

    // Update to confirmed
    final confirmed = sale.copyWith(
      status: 'CONFIRMED',
      saleId: 99,
      orderNumber: 'MOB-ORD-99',
      syncedAt: DateTime.now().toUtc().toIso8601String(),
    );
    await repo.updateOperation(confirmed);

    final pending = await repo.listOperations(status: 'PENDING_SYNC');
    expect(pending.isEmpty, isTrue);

    final confList = await repo.listOperations(status: 'CONFIRMED');
    expect(confList.length, equals(1));
    expect(confList.first.orderNumber, equals('MOB-ORD-99'));
    expect(confList.first.saleId, equals(99));
  });

  test('CU-22: saveCustomer, listCustomers, deleteCustomer and auto-persist on offline sale', () async {
    final customer = await repo.saveCustomer(
      fullName: 'Fernando Quiroga',
      nitCi: '4455667',
      phone: '71122334',
    );
    expect(customer.id, isNotEmpty);
    expect(customer.fullName, equals('Fernando Quiroga'));

    await repo.recordOfflineSale(
      branchId: 5,
      payload: const OfflineSalePayload(
        customerName: 'Daniela Ortiz',
        customerNit: '8877665',
        customerPhone: '79988776',
        items: [
          OfflineSaleItem(productVariantId: 1001, quantity: 1, unitPrice: 150.0),
        ],
        total: 150.0,
      ),
    );

    final allCustomers = await repo.listCustomers();
    expect(allCustomers.length, equals(2));

    final filtered = await repo.listCustomers(query: '8877665');
    expect(filtered.length, equals(1));
    expect(filtered.first.fullName, equals('Daniela Ortiz'));

    await repo.deleteCustomer(customer.id);
    final afterDelete = await repo.listCustomers();
    expect(afterDelete.length, equals(1));
  });
}
