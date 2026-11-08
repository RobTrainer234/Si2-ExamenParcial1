import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fashionstore_mobile/core/errors/api_exception.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/connectivity_monitor.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';
import 'package:fashionstore_mobile/core/offline/offline_transaction_repository.dart';
import 'package:fashionstore_mobile/core/providers.dart';
import 'package:fashionstore_mobile/features/exchange/data/exchange_models.dart';
import 'package:fashionstore_mobile/features/exchange/data/exchange_repository.dart';
import 'package:fashionstore_mobile/features/exchange/presentation/garment_exchange_screen.dart';
import 'package:fashionstore_mobile/main.dart';

class _ControlledConnectivitySource implements ConnectivitySource {
  _ControlledConnectivitySource(this.initial);

  final List<ConnectivityResult> initial;
  final StreamController<List<ConnectivityResult>> controller =
      StreamController<List<ConnectivityResult>>.broadcast();

  @override
  Future<List<ConnectivityResult>> checkConnectivity() async => initial;

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged =>
      controller.stream;

  Future<void> dispose() async {
    await controller.close();
  }
}

class _SpyOfflineTransactionRepository extends OfflineTransactionRepository {
  _SpyOfflineTransactionRepository() : super(OfflineDatabase(inMemory: true));

  int enqueuedCalls = 0;

  @override
  Future<OfflineOperationRecord> recordOfflineSale({
    required int branchId,
    required OfflineSalePayload payload,
  }) async {
    enqueuedCalls += 1;
    throw UnimplementedError('Exchanges must never enqueue offline sales');
  }

  @override
  Future<OfflineOperationRecord> recordOfflineReservation({
    required int branchId,
    required OfflineReservationPayload payload,
  }) async {
    enqueuedCalls += 1;
    throw UnimplementedError(
      'Exchanges must never enqueue offline reservations',
    );
  }
}

class _FakeExchangeRepository extends ExchangeRepository {
  _FakeExchangeRepository() : super(ApiClient());

  int lookupCalls = 0;
  final List<ExchangeFinalizeRequest> finalizeRequests = [];
  ExchangeLookupResult lookupResponse = const ExchangeLookupResult(
    saleId: 42,
    orderNumber: 'FS-2026-0042',
    saleDate: '2026-10-30T14:30:00Z',
    branchId: 2,
    status: 'COMPLETED',
    items: [
      ExchangeLookupItem(
        id: 501,
        variantId: 11,
        name: 'Camisa Oxford (M / Negro)',
        sku: 'CAM-001-M-NEG',
        purchasedQuantity: 2,
        netPaidLineTotal: 400.0,
        remainingExchangeableQuantity: 2,
      ),
    ],
  );
  List<ExchangeReplacementOption> branchVariantsResponse = const [
    ExchangeReplacementOption(
      inventoryId: 91,
      branchId: 2,
      branchName: 'FashionStore Norte',
      variantId: 22,
      productId: 7,
      productName: 'Chaqueta Urbana',
      sku: 'CHA-002-L-AZUL',
      sizeName: 'L',
      colorName: 'Azul',
      availableQuantity: 5,
      available: true,
    ),
  ];
  ExchangeQuote quoteResponse = const ExchangeQuote(
    saleId: 42,
    saleItemId: 501,
    returnedVariantId: 11,
    returnedQuantity: 1,
    newVariantId: 22,
    newQuantity: 1,
    returnedValue: 200.0,
    replacementUnitPrice: 230.0,
    deliveredValue: 230.0,
    difference: 30.0,
    cashSettlementEligible: true,
    availableStock: 5,
    reservedStock: 1,
    expiresAt: '2026-11-02T01:30:00Z',
    quoteFingerprint: 'abcdef0123456789abcdef0123456789',
  );
  Future<ExchangeReceipt> Function(int saleId, ExchangeFinalizeRequest request)?
  onFinalize;

  @override
  Future<ExchangeLookupResult> lookupSale(String orderNumber) async {
    lookupCalls += 1;
    return lookupResponse;
  }

  @override
  Future<List<ExchangeReplacementOption>> fetchBranchVariants(
    int branchId,
  ) async {
    return branchVariantsResponse;
  }

  @override
  Future<ExchangeQuote> requestQuote(
    int saleId,
    ExchangeQuoteRequest request,
  ) async {
    return quoteResponse;
  }

  @override
  Future<ExchangeReceipt> finalizeExchange(
    int saleId,
    ExchangeFinalizeRequest request,
  ) async {
    finalizeRequests.add(request);
    if (onFinalize != null) {
      return onFinalize!(saleId, request);
    }
    return ExchangeReceipt(
      saleId: saleId,
      orderNumber: lookupResponse.orderNumber,
      returnedVariantId: request.returnedVariantId,
      returnedQuantity: request.returnedQuantity,
      newVariantId: request.newVariantId,
      newQuantity: request.newQuantity,
      status: 'EXCHANGED',
      quarantineId: 77,
      quarantineStatus: 'PENDING',
      returnedValue: quoteResponse.returnedValue,
      deliveredValue: quoteResponse.deliveredValue,
      difference: quoteResponse.difference,
      cashTendered: request.cashTendered != null
          ? double.tryParse(request.cashTendered!)
          : null,
      cashChange: request.cashTendered != null
          ? (double.parse(request.cashTendered!) - quoteResponse.difference)
          : null,
      cashRefunded: quoteResponse.difference < 0
          ? -quoteResponse.difference
          : null,
      exchangedAt: '2026-11-02T01:15:00Z',
    );
  }
}

void main() {
  test('canAccessCashierExchange habilita ADMIN y personal con sales.create y bloquea CLIENT', () {
    expect(canAccessCashierExchange(null), isFalse);
    expect(
      canAccessCashierExchange({
        'role': 'CLIENT',
        'permissions': ['catalog.read', 'sales.read'],
      }),
      isFalse,
    );
    expect(
      canAccessCashierExchange({
        'role': 'CASHIER',
        'permissions': ['sales.read', 'sales.create', 'inventory.read'],
      }),
      isTrue,
    );
    expect(
      canAccessCashierExchange({
        'role': 'ADMIN',
        'permissions': <String>[],
      }),
      isTrue,
    );
  });

  testWidgets('completa flujo online de cambio con diferencia a cobrar y muestra cuarentena PENDING', (
    tester,
  ) async {
    final source = _ControlledConnectivitySource([ConnectivityResult.wifi]);
    final monitor = ConnectivityMonitor(source);
    await monitor.start();
    addTearDown(() async {
      monitor.dispose();
      await source.dispose();
    });

    final fakeRepo = _FakeExchangeRepository();
    final spyOfflineRepo = _SpyOfflineTransactionRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          connectivityMonitorProvider.overrideWith((ref) => monitor),
          exchangeRepositoryProvider.overrideWithValue(fakeRepo),
          offlineTransactionRepositoryProvider.overrideWithValue(spyOfflineRepo),
        ],
        child: const MaterialApp(home: GarmentExchangeScreen()),
      ),
    );
    await tester.pump();

    await tester.enterText(
      find.byKey(const Key('exchange_order_input')),
      'FS-2026-0042',
    );
    await tester.tap(find.byKey(const Key('exchange_lookup_btn')));
    await tester.pumpAndSettle();

    expect(find.textContaining('FS-2026-0042'), findsWidgets);
    expect(find.textContaining('Camisa Oxford'), findsWidgets);

    await tester.ensureVisible(find.byKey(const Key('exchange_quote_btn')));
    await tester.tap(find.byKey(const Key('exchange_quote_btn')));
    await tester.pumpAndSettle();

    expect(find.textContaining('30.00'), findsWidgets);

    await tester.ensureVisible(
      find.byKey(const Key('exchange_cash_tendered_input')),
    );
    await tester.enterText(
      find.byKey(const Key('exchange_cash_tendered_input')),
      '50',
    );
    await tester.pump();

    await tester.ensureVisible(find.byKey(const Key('exchange_finalize_btn')));
    await tester.tap(find.byKey(const Key('exchange_finalize_btn')));
    await tester.pumpAndSettle();

    expect(fakeRepo.finalizeRequests, hasLength(1));
    expect(fakeRepo.finalizeRequests.first.cashTendered, '50.00');
    expect(find.byKey(const Key('exchange_receipt_card')), findsOneWidget);
    expect(find.textContaining('#77'), findsOneWidget);
    expect(find.textContaining('PENDING'), findsWidgets);
    expect(spyOfflineRepo.enqueuedCalls, 0);
  });

  testWidgets('exige confirmacion explicita del cajero para reembolso en efectivo y bloquea diferencias no elegibles', (
    tester,
  ) async {
    final source = _ControlledConnectivitySource([ConnectivityResult.wifi]);
    final monitor = ConnectivityMonitor(source);
    await monitor.start();
    addTearDown(() async {
      monitor.dispose();
      await source.dispose();
    });

    final fakeRepo = _FakeExchangeRepository()
      ..quoteResponse = const ExchangeQuote(
        saleId: 42,
        saleItemId: 501,
        returnedVariantId: 11,
        returnedQuantity: 1,
        newVariantId: 22,
        newQuantity: 1,
        returnedValue: 200.0,
        replacementUnitPrice: 150.0,
        deliveredValue: 150.0,
        difference: -50.0,
        cashSettlementEligible: false,
        availableStock: 5,
        reservedStock: 0,
        expiresAt: '2026-11-02T01:30:00Z',
        quoteFingerprint: 'abcdef0123456789abcdef0123456789',
      );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          connectivityMonitorProvider.overrideWith((ref) => monitor),
          exchangeRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const MaterialApp(home: GarmentExchangeScreen()),
      ),
    );
    await tester.pump();

    await tester.enterText(
      find.byKey(const Key('exchange_order_input')),
      'FS-2026-0042',
    );
    await tester.tap(find.byKey(const Key('exchange_lookup_btn')));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('exchange_quote_btn')));
    await tester.tap(find.byKey(const Key('exchange_quote_btn')));
    await tester.pumpAndSettle();

    // Non-eligible nonzero difference must disable finalization
    final disabledBtn = tester.widget<FilledButton>(
      find.byKey(const Key('exchange_finalize_btn')),
    );
    expect(disabledBtn.onPressed, isNull);
    expect(
      find.textContaining('no fue liquidada íntegramente en efectivo'),
      findsOneWidget,
    );

    // Switch quote to eligible negative difference and re-quote
    fakeRepo.quoteResponse = const ExchangeQuote(
      saleId: 42,
      saleItemId: 501,
      returnedVariantId: 11,
      returnedQuantity: 1,
      newVariantId: 22,
      newQuantity: 1,
      returnedValue: 200.0,
      replacementUnitPrice: 150.0,
      deliveredValue: 150.0,
      difference: -50.0,
      cashSettlementEligible: true,
      availableStock: 5,
      reservedStock: 0,
      expiresAt: '2026-11-02T01:35:00Z',
      quoteFingerprint: '11112222333344445555666677778888',
    );
    await tester.ensureVisible(find.byKey(const Key('exchange_quote_btn')));
    await tester.tap(find.byKey(const Key('exchange_quote_btn')));
    await tester.pumpAndSettle();

    // Tapping finalize without checking confirmation shows inline error and does not call API
    await tester.ensureVisible(find.byKey(const Key('exchange_finalize_btn')));
    await tester.tap(find.byKey(const Key('exchange_finalize_btn')));
    await tester.pump();
    expect(fakeRepo.finalizeRequests, isEmpty);

    await tester.ensureVisible(
      find.byKey(const Key('exchange_cashier_confirmed_checkbox')),
    );
    await tester.tap(
      find.byKey(const Key('exchange_cashier_confirmed_checkbox')),
    );
    await tester.pump();

    await tester.ensureVisible(find.byKey(const Key('exchange_finalize_btn')));
    await tester.tap(find.byKey(const Key('exchange_finalize_btn')));
    await tester.pumpAndSettle();

    expect(fakeRepo.finalizeRequests, hasLength(1));
    expect(fakeRepo.finalizeRequests.first.cashierConfirmed, isTrue);
    expect(find.byKey(const Key('exchange_receipt_card')), findsOneWidget);
  });

  testWidgets('preserva idempotency_key ante fallo de red incierto y reintenta sin duplicar', (
    tester,
  ) async {
    final source = _ControlledConnectivitySource([ConnectivityResult.wifi]);
    final monitor = ConnectivityMonitor(source);
    await monitor.start();
    addTearDown(() async {
      monitor.dispose();
      await source.dispose();
    });

    var attempt = 0;
    final fakeRepo = _FakeExchangeRepository()
      ..quoteResponse = const ExchangeQuote(
        saleId: 42,
        saleItemId: 501,
        returnedVariantId: 11,
        returnedQuantity: 1,
        newVariantId: 22,
        newQuantity: 1,
        returnedValue: 200.0,
        replacementUnitPrice: 200.0,
        deliveredValue: 200.0,
        difference: 0.0,
        cashSettlementEligible: true,
        availableStock: 5,
        reservedStock: 0,
        expiresAt: '2026-11-02T01:30:00Z',
        quoteFingerprint: 'abcdef0123456789abcdef0123456789',
      );
    fakeRepo.onFinalize = (saleId, req) async {
      attempt += 1;
      if (attempt == 1) {
        throw const ApiException('Timeout de conexión', 0);
      }
      return ExchangeReceipt(
        saleId: saleId,
        orderNumber: 'FS-2026-0042',
        returnedVariantId: req.returnedVariantId,
        returnedQuantity: req.returnedQuantity,
        newVariantId: req.newVariantId,
        newQuantity: req.newQuantity,
        status: 'EXCHANGED',
        quarantineId: 88,
        quarantineStatus: 'PENDING',
        returnedValue: 200.0,
        deliveredValue: 200.0,
        difference: 0.0,
        exchangedAt: '2026-11-02T01:18:00Z',
      );
    };

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          connectivityMonitorProvider.overrideWith((ref) => monitor),
          exchangeRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const MaterialApp(home: GarmentExchangeScreen()),
      ),
    );
    await tester.pump();

    await tester.enterText(
      find.byKey(const Key('exchange_order_input')),
      'FS-2026-0042',
    );
    await tester.tap(find.byKey(const Key('exchange_lookup_btn')));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('exchange_quote_btn')));
    await tester.tap(find.byKey(const Key('exchange_quote_btn')));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('exchange_finalize_btn')));
    await tester.tap(find.byKey(const Key('exchange_finalize_btn')));
    await tester.pumpAndSettle();

    expect(fakeRepo.finalizeRequests, hasLength(1));
    expect(find.byKey(const Key('exchange_retry_btn')), findsOneWidget);
    expect(find.byKey(const Key('exchange_receipt_card')), findsNothing);

    await tester.ensureVisible(find.byKey(const Key('exchange_retry_btn')));
    await tester.tap(find.byKey(const Key('exchange_retry_btn')));
    await tester.pumpAndSettle();

    expect(fakeRepo.finalizeRequests, hasLength(2));
    expect(
      fakeRepo.finalizeRequests[1].idempotencyKey,
      fakeRepo.finalizeRequests[0].idempotencyKey,
    );
    expect(find.byKey(const Key('exchange_receipt_card')), findsOneWidget);
    expect(find.textContaining('#88'), findsOneWidget);
  });

  testWidgets('invalida cotizacion obsoleta ante conflicto 409 y permite recotizar sin bloquear', (
    tester,
  ) async {
    final source = _ControlledConnectivitySource([ConnectivityResult.wifi]);
    final monitor = ConnectivityMonitor(source);
    await monitor.start();
    addTearDown(() async {
      monitor.dispose();
      await source.dispose();
    });

    var attempt = 0;
    final fakeRepo = _FakeExchangeRepository()
      ..quoteResponse = const ExchangeQuote(
        saleId: 42,
        saleItemId: 501,
        returnedVariantId: 11,
        returnedQuantity: 1,
        newVariantId: 22,
        newQuantity: 1,
        returnedValue: 200.0,
        replacementUnitPrice: 200.0,
        deliveredValue: 200.0,
        difference: 0.0,
        cashSettlementEligible: true,
        availableStock: 5,
        reservedStock: 0,
        expiresAt: '2026-11-02T01:30:00Z',
        quoteFingerprint: 'stale-fingerprint-0000111122223333',
      );
    fakeRepo.onFinalize = (saleId, req) async {
      attempt += 1;
      if (attempt == 1) {
        throw const ApiException(
          'La cotización expiró o los precios cambiaron.',
          409,
          code: 'EXCHANGE_QUOTE_STALE',
        );
      }
      return ExchangeReceipt(
        saleId: saleId,
        orderNumber: 'FS-2026-0042',
        returnedVariantId: req.returnedVariantId,
        returnedQuantity: req.returnedQuantity,
        newVariantId: req.newVariantId,
        newQuantity: req.newQuantity,
        status: 'EXCHANGED',
        quarantineId: 99,
        quarantineStatus: 'PENDING',
        returnedValue: 200.0,
        deliveredValue: 200.0,
        difference: 0.0,
        exchangedAt: '2026-11-02T01:20:00Z',
      );
    };

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          connectivityMonitorProvider.overrideWith((ref) => monitor),
          exchangeRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const MaterialApp(home: GarmentExchangeScreen()),
      ),
    );
    await tester.pump();

    await tester.enterText(
      find.byKey(const Key('exchange_order_input')),
      'FS-2026-0042',
    );
    await tester.tap(find.byKey(const Key('exchange_lookup_btn')));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('exchange_quote_btn')));
    await tester.tap(find.byKey(const Key('exchange_quote_btn')));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('exchange_finalize_btn')));
    await tester.tap(find.byKey(const Key('exchange_finalize_btn')));
    await tester.pumpAndSettle();

    // 409 clears quote and does not enter frozen retry state
    expect(find.byKey(const Key('exchange_retry_btn')), findsNothing);
    expect(find.byKey(const Key('exchange_finalize_btn')), findsNothing);
    expect(
      find.textContaining('La cotización expiró o los precios cambiaron.'),
      findsOneWidget,
    );

    // Re-quote with fresh fingerprint and confirm
    fakeRepo.quoteResponse = const ExchangeQuote(
      saleId: 42,
      saleItemId: 501,
      returnedVariantId: 11,
      returnedQuantity: 1,
      newVariantId: 22,
      newQuantity: 1,
      returnedValue: 200.0,
      replacementUnitPrice: 200.0,
      deliveredValue: 200.0,
      difference: 0.0,
      cashSettlementEligible: true,
      availableStock: 5,
      reservedStock: 0,
      expiresAt: '2026-11-02T01:40:00Z',
      quoteFingerprint: 'fresh-fingerprint-4444555566667777',
    );
    await tester.ensureVisible(find.byKey(const Key('exchange_quote_btn')));
    await tester.tap(find.byKey(const Key('exchange_quote_btn')));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('exchange_finalize_btn')));
    await tester.tap(find.byKey(const Key('exchange_finalize_btn')));
    await tester.pumpAndSettle();

    expect(fakeRepo.finalizeRequests, hasLength(2));
    expect(
      fakeRepo.finalizeRequests[1].quoteFingerprint,
      'fresh-fingerprint-4444555566667777',
    );
    expect(
      fakeRepo.finalizeRequests[1].idempotencyKey,
      isNot(fakeRepo.finalizeRequests[0].idempotencyKey),
    );
    expect(find.byKey(const Key('exchange_receipt_card')), findsOneWidget);
    expect(find.textContaining('#99'), findsOneWidget);
  });

  testWidgets('bloquea busqueda y confirmacion cuando esta offline y nunca encola en SQLite outbox', (
    tester,
  ) async {
    final source = _ControlledConnectivitySource([ConnectivityResult.none]);
    final monitor = ConnectivityMonitor(source);
    await monitor.start();
    addTearDown(() async {
      monitor.dispose();
      await source.dispose();
    });

    final fakeRepo = _FakeExchangeRepository();
    final spyOfflineRepo = _SpyOfflineTransactionRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          connectivityMonitorProvider.overrideWith((ref) => monitor),
          exchangeRepositoryProvider.overrideWithValue(fakeRepo),
          offlineTransactionRepositoryProvider.overrideWithValue(spyOfflineRepo),
        ],
        child: const MaterialApp(home: GarmentExchangeScreen()),
      ),
    );
    await tester.pump();

    expect(
      find.textContaining('Operación exclusiva en línea'),
      findsOneWidget,
    );
    final lookupBtn = tester.widget<FilledButton>(
      find.byKey(const Key('exchange_lookup_btn')),
    );
    expect(lookupBtn.onPressed, isNull);
    expect(fakeRepo.lookupCalls, 0);
    expect(spyOfflineRepo.enqueuedCalls, 0);
  });
}
