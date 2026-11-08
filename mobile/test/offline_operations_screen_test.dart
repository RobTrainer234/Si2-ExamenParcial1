import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';
import 'package:fashionstore_mobile/core/offline/offline_transaction_repository.dart';
import 'package:fashionstore_mobile/core/offline/sync_transaction_service.dart';
import 'package:fashionstore_mobile/core/providers.dart';
import 'package:fashionstore_mobile/features/offline/presentation/offline_operations_screen.dart';

class _MockScreenApiClient extends ApiClient {
  @override
  Future<dynamic> post(String path, {Object? body, Map<String, String>? headers}) async {
    return {};
  }
}

class _DummyOfflineDb extends OfflineDatabase {
  _DummyOfflineDb() : super(inMemory: true);
}

class StubOfflineTransactionRepository extends OfflineTransactionRepository {
  StubOfflineTransactionRepository(this.operations) : super(_DummyOfflineDb());
  final List<OfflineOperationRecord> operations;

  @override
  Future<List<OfflineOperationRecord>> listOperations({String? status}) async {
    if (status != null) {
      return operations.where((op) => op.status == status).toList();
    }
    return List.from(operations);
  }

  @override
  Future<int> countPendingOperations() async {
    return operations.where((op) => op.status == 'PENDING_SYNC').length;
  }
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late StubOfflineTransactionRepository stubRepo;
  late SyncTransactionService syncService;

  setUp(() {
    final operations = [
      const OfflineOperationRecord(
        clientOperationId: 'op-mob-1700-001',
        branchId: 10,
        operationType: 'SALE',
        status: 'PENDING_SYNC',
        payloadJson: '{"items":[{"product_variant_id":1001,"quantity":2,"unit_price":150.0}],"total":300.0}',
        createdAt: '2026-10-23T20:00:00Z',
      ),
      const OfflineOperationRecord(
        clientOperationId: 'op-mob-1700-002',
        branchId: 10,
        operationType: 'RESERVATION',
        status: 'PENDING_SYNC',
        payloadJson: '{"customer_name":"Laura Mendez","customer_phone":"78901234","items":[{"product_variant_id":1001,"quantity":1}]}',
        createdAt: '2026-10-23T20:05:00Z',
      ),
    ];

    stubRepo = StubOfflineTransactionRepository(operations);
    syncService = SyncTransactionService(
      api: _MockScreenApiClient(),
      offlineRepo: stubRepo,
    );
  });

  testWidgets('T2.3.5: OfflineOperationsScreen displays outbox operations with badges and filters', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          offlineTransactionRepositoryProvider.overrideWithValue(stubRepo),
          syncTransactionServiceProvider.overrideWith((ref) => syncService),
        ],
        child: const MaterialApp(
          home: OfflineOperationsScreen(),
        ),
      ),
    );

    // Pump widget and allow async listOperations to complete
    await tester.pump();
    await tester.pump();

    expect(find.text('Bandeja Offline'), findsOneWidget);
    expect(find.text('Todas'), findsOneWidget);
    expect(find.text('Pendientes'), findsOneWidget);
    expect(find.text('Confirmadas'), findsOneWidget);
    expect(find.text('Conflictos'), findsOneWidget);

    // Verify operations cards
    expect(find.text('Venta Contado'), findsOneWidget);
    expect(find.text('Reserva Prenda'), findsOneWidget);
    expect(find.text('Total: \$300.0'), findsOneWidget);
    expect(find.text('Cliente: Laura Mendez'), findsOneWidget);
    expect(find.text('PENDIENTE'), findsNWidgets(2));

    // Tap on Confirmadas filter
    await tester.tap(find.text('Confirmadas'));
    await tester.pump();
    await tester.pump();

    // Confirmadas is currently empty
    expect(find.text('Sin operaciones registradas'), findsOneWidget);
  });
}
