import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';
import 'package:fashionstore_mobile/core/offline/offline_transaction_repository.dart';
import 'package:fashionstore_mobile/core/offline/sync_transaction_service.dart';

class MockSyncApiClient extends ApiClient {
  MockSyncApiClient({required this.postHandler});

  final Future<dynamic> Function(String path, Object? body) postHandler;

  @override
  Future<dynamic> post(
    String path, {
    Object? body,
    Map<String, String>? headers,
  }) =>
      postHandler(path, body);
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late OfflineDatabase offlineDb;
  late OfflineTransactionRepository repo;

  setUp(() async {
    offlineDb = OfflineDatabase(inMemory: true);
    repo = OfflineTransactionRepository(offlineDb);
  });

  tearDown(() async {
    await offlineDb.close();
  });

  test('T2.3.4: syncPendingTransactions returns null when no pending operations exist', () async {
    var wasCalled = false;
    final mockApi = MockSyncApiClient(
      postHandler: (path, body) async {
        wasCalled = true;
        return {};
      },
    );

    final service = SyncTransactionService(api: mockApi, offlineRepo: repo);
    final result = await service.syncPendingTransactions();

    expect(result, isNull);
    expect(wasCalled, isFalse);
    expect(service.pendingCount, equals(0));
  });

  test('T2.3.4: syncPendingTransactions uploads batch and updates confirmed status in SQLite', () async {
    final sale = await repo.recordOfflineSale(
      branchId: 5,
      payload: const OfflineSalePayload(
        items: [
          OfflineSaleItem(productVariantId: 101, quantity: 2, unitPrice: 120.0),
        ],
        total: 240.0,
      ),
    );

    var capturedPath = '';
    Map<String, dynamic>? capturedBody;

    final mockApi = MockSyncApiClient(
      postHandler: (path, body) async {
        capturedPath = path;
        capturedBody = body as Map<String, dynamic>?;
        return {
          'processed_count': 1,
          'confirmed_count': 1,
          'conflict_count': 0,
          'results': [
            {
              'client_operation_id': sale.clientOperationId,
              'operation_type': 'SALE',
              'status': 'CONFIRMED',
              'sale_id': 77,
              'order_number': 'ORD-MOB-77',
              'reservation_id': null,
              'conflict': null,
              'processed_at': '2026-10-23T20:15:00Z',
            },
          ],
        };
      },
    );

    final service = SyncTransactionService(api: mockApi, offlineRepo: repo);
    await service.refreshPendingCount();
    expect(service.pendingCount, equals(1));

    final result = await service.syncPendingTransactions();

    expect(result, isNotNull);
    expect(result!.confirmedCount, equals(1));
    expect(capturedPath, equals('/sync/transactions'));
    expect(capturedBody?['operations'], isList);

    // Verify SQLite update
    final updated = await repo.getOperation(sale.clientOperationId);
    expect(updated, isNotNull);
    expect(updated!.status, equals('CONFIRMED'));
    expect(updated.saleId, equals(77));
    expect(updated.orderNumber, equals('ORD-MOB-77'));

    expect(service.pendingCount, equals(0));
  });

  test('T2.3.4: syncPendingTransactions updates conflict status when stock is insufficient', () async {
    final sale = await repo.recordOfflineSale(
      branchId: 5,
      payload: const OfflineSalePayload(
        items: [
          OfflineSaleItem(productVariantId: 101, quantity: 5, unitPrice: 100.0),
        ],
        total: 500.0,
      ),
    );

    final mockApi = MockSyncApiClient(
      postHandler: (path, body) async {
        return {
          'processed_count': 1,
          'confirmed_count': 0,
          'conflict_count': 1,
          'results': [
            {
              'client_operation_id': sale.clientOperationId,
              'operation_type': 'SALE',
              'status': 'CONFLICT',
              'sale_id': null,
              'order_number': null,
              'reservation_id': null,
              'conflict': {
                'code': 'INSUFFICIENT_STOCK',
                'message': 'Stock insuficiente en el servidor. Solicitado: 5, disponible: 1',
                'available_stock': 1,
                'requested_quantity': 5,
                'variant_id': 101,
              },
              'processed_at': '2026-10-23T20:20:00Z',
            },
          ],
        };
      },
    );

    final service = SyncTransactionService(api: mockApi, offlineRepo: repo);
    final result = await service.syncPendingTransactions();

    expect(result, isNotNull);
    expect(result!.conflictCount, equals(1));

    final updated = await repo.getOperation(sale.clientOperationId);
    expect(updated!.status, equals('CONFLICT'));
    expect(updated.conflictDetailJson, contains('INSUFFICIENT_STOCK'));

    // Conflict operations are no longer PENDING_SYNC
    expect(service.pendingCount, equals(0));
  });

  test('T2.3.4: network failure retains pending operations in SQLite for retry', () async {
    final sale = await repo.recordOfflineSale(
      branchId: 5,
      payload: const OfflineSalePayload(
        items: [
          OfflineSaleItem(productVariantId: 101, quantity: 1, unitPrice: 80.0),
        ],
        total: 80.0,
      ),
    );

    final mockApi = MockSyncApiClient(
      postHandler: (path, body) async {
        throw Exception('Sin conexión al servidor central');
      },
    );

    final service = SyncTransactionService(api: mockApi, offlineRepo: repo);
    final result = await service.syncPendingTransactions();

    expect(result, isNull);
    expect(service.syncError, contains('Sin conexión'));

    // Operations must NOT be deleted or lost!
    final pending = await repo.listOperations(status: 'PENDING_SYNC');
    expect(pending.length, equals(1));
    expect(pending.first.clientOperationId, equals(sale.clientOperationId));
    expect(service.pendingCount, equals(1));
  });
}
