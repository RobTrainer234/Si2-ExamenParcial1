import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/connectivity_monitor.dart';
import 'package:fashionstore_mobile/core/providers.dart';
import 'package:fashionstore_mobile/features/catalog/data/catalog_models.dart';
import 'package:fashionstore_mobile/features/catalog/data/catalog_repository.dart';
import 'package:fashionstore_mobile/features/catalog/presentation/catalog_screen.dart';

class StubOfflineCatalogRepo extends CatalogRepository {
  StubOfflineCatalogRepo() : super(_DummyApiClient());

  @override
  Future<CatalogPage> list({
    String query = '',
    int page = 1,
  }) async {
    return const CatalogPage(
      [
        CatalogItem(
          id: 1,
          name: 'Vestido Offline Lino',
          categoryName: 'Vestidos',
          price: 120.0,
        ),
      ],
      1,
      isOffline: true,
    );
  }
}

class _DummyApiClient extends ApiClient {}

class _FakeConnectivitySource implements ConnectivitySource {
  final controller = StreamController<List<ConnectivityResult>>.broadcast();

  @override
  Future<List<ConnectivityResult>> checkConnectivity() async =>
      const [ConnectivityResult.none];

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged =>
      controller.stream;
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  testWidgets('T1.4.5: CatalogScreen muestra estado offline y banner de advertencia de vigencia', (tester) async {
    final connectivitySource = _FakeConnectivitySource();
    final connectivityMonitor = ConnectivityMonitor(connectivitySource);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          catalogRepositoryProvider.overrideWithValue(StubOfflineCatalogRepo()),
          connectivityMonitorProvider.overrideWith((ref) {
            connectivityMonitor.start();
            return connectivityMonitor;
          }),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: CatalogScreen(),
          ),
        ),
      ),
    );

    // Initial pump & settle
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    // Verify offline badge / status
    expect(find.textContaining('Modo offline'), findsOneWidget);
    expect(find.text('Conectividad: Sin conexión'), findsOneWidget);

    connectivitySource.controller.add(const [ConnectivityResult.wifi]);
    await tester.pump(const Duration(milliseconds: 1));
    expect(find.text('Conectividad: Conexión disponible'), findsOneWidget);

    // Verify warning banner on staleness
    expect(
      find.text('Precios y disponibilidad locales pueden estar desactualizados.'),
      findsOneWidget,
    );

    // Verify download button
    expect(find.text('Descargar offline'), findsOneWidget);

    // Verify product rendered from offline items
    expect(find.text('Vestido Offline Lino'), findsOneWidget);
  });
}
