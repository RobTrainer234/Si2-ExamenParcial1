import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker/image_picker.dart';

import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/providers.dart';
import 'package:fashionstore_mobile/features/catalog/data/catalog_models.dart';
import 'package:fashionstore_mobile/features/catalog/data/catalog_repository.dart';
import 'package:fashionstore_mobile/features/virtual_fitting/data/virtual_fitting_repository.dart';
import 'package:fashionstore_mobile/features/virtual_fitting/presentation/virtual_fitting_screen.dart';

void main() {
  testWidgets(
    'starts in pending studio state without catalog overlay or fake fit',
    (tester) async {
      final virtualFitting = _FakeVirtualFittingRepository();

      await tester.pumpWidget(
        _screenUnderTest(
          virtualFitting: virtualFitting,
          catalog: _FakeCatalogRepository(items: const []),
          imageUrl: 'https://example.com/raw-catalog-photo.png',
        ),
      );
      await tester.pump();

      expect(virtualFitting.vtonTryOnCalls, 0);
      expect(find.byType(Image), findsNothing);
      expect(find.text('RESULTADO GEMINI'), findsOneWidget);
      expect(find.textContaining('99.'), findsNothing);
      expect(find.text('RESULTADO: GEMINI'), findsOneWidget);
      expect(find.text('TALLA SUGERIDA: PENDIENTE'), findsOneWidget);
    },
  );

  testWidgets('gallery cancel keeps the neutral studio pending state', (
    tester,
  ) async {
    final virtualFitting = _FakeVirtualFittingRepository();

    await tester.pumpWidget(
      _screenUnderTest(
        virtualFitting: virtualFitting,
        catalog: _FakeCatalogRepository(items: const []),
        pickImageFromGallery: () async => null,
      ),
    );
    await tester.pump();

    await _tapGalleryAction(tester);

    expect(virtualFitting.vtonTryOnCalls, 0);
    expect(find.text('RESULTADO GEMINI'), findsOneWidget);
    expect(find.text('Generar prueba virtual'), findsNothing);
  });

  testWidgets('gallery selection shows confirmation before shared submission', (
    tester,
  ) async {
    final photoBytes = _jpegBytes();
    final virtualFitting = _FakeVirtualFittingRepository();

    await tester.pumpWidget(
      _screenUnderTest(
        virtualFitting: virtualFitting,
        catalog: _FakeCatalogRepository(items: const []),
        pickImageFromGallery: () async => XFile.fromData(photoBytes),
      ),
    );
    await tester.pump();

    await _tapGalleryAction(tester);

    expect(find.textContaining('Foto de galería lista'), findsOneWidget);
    expect(find.text('Generar prueba virtual'), findsOneWidget);
    expect(virtualFitting.vtonTryOnCalls, 0);

    await _tapGenerateAction(tester);

    expect(virtualFitting.vtonTryOnCalls, 1);
    expect(virtualFitting.lastImageBase64, base64Encode(photoBytes));
    expect(virtualFitting.lastMetrics?['device'], 'gallery_photo');
    expect(find.byType(Image), findsOneWidget);
    expect(find.textContaining('Gemini: completed'), findsOneWidget);
  });

  testWidgets('invalid gallery input is rejected before upload', (
    tester,
  ) async {
    final virtualFitting = _FakeVirtualFittingRepository();

    await tester.pumpWidget(
      _screenUnderTest(
        virtualFitting: virtualFitting,
        catalog: _FakeCatalogRepository(items: const []),
        pickImageFromGallery: () async => XFile.fromData(
          Uint8List.fromList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
        ),
      ),
    );
    await tester.pump();

    await _tapGalleryAction(tester);

    expect(virtualFitting.vtonTryOnCalls, 0);
    expect(find.textContaining('Formato no soportado'), findsWidgets);
  });

  testWidgets('oversized gallery input is rejected before upload', (
    tester,
  ) async {
    final virtualFitting = _FakeVirtualFittingRepository();
    final oversized = Uint8List(6 * 1024 * 1024)
      ..[0] = 0xFF
      ..[1] = 0xD8
      ..[2] = 0xFF;

    await tester.pumpWidget(
      _screenUnderTest(
        virtualFitting: virtualFitting,
        catalog: _FakeCatalogRepository(items: const []),
        pickImageFromGallery: () async => XFile.fromData(oversized),
      ),
    );
    await tester.pump();

    await _tapGalleryAction(tester);

    expect(virtualFitting.vtonTryOnCalls, 0);
    expect(find.textContaining('límite de 7 MB'), findsWidgets);
  });

  testWidgets('backend error keeps retry available for the same photo', (
    tester,
  ) async {
    final virtualFitting = _FakeVirtualFittingRepository()..throwOnTryOn = true;

    await tester.pumpWidget(
      _screenUnderTest(
        virtualFitting: virtualFitting,
        catalog: _FakeCatalogRepository(items: const []),
        pickImageFromGallery: () async => XFile.fromData(_jpegBytes()),
      ),
    );
    await tester.pump();

    await _tapGalleryAction(tester);
    await _tapGenerateAction(tester);

    expect(virtualFitting.vtonTryOnCalls, 1);
    expect(find.textContaining('No pudimos generar'), findsWidgets);

    virtualFitting.throwOnTryOn = false;
    await _tapRetryAction(tester);

    expect(virtualFitting.vtonTryOnCalls, 2);
    expect(find.byType(Image), findsOneWidget);
  });

  testWidgets('selecting another garment prompts photo selection without VTON', (
    tester,
  ) async {
    final virtualFitting = _FakeVirtualFittingRepository();

    await tester.pumpWidget(
      _screenUnderTest(
        virtualFitting: virtualFitting,
        catalog: _FakeCatalogRepository(
          items: const [
            CatalogItem(
              id: 1,
              name: 'Blazer inicial',
              categoryName: 'Sacos',
              price: 120,
            ),
            CatalogItem(
              id: 2,
              name: 'Camisa nueva',
              categoryName: 'Camisas',
              price: 80,
            ),
          ],
        ),
      ),
    );
    await tester.pump();

    await tester.ensureVisible(find.text('Camisa nueva'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Camisa nueva'));
    await tester.pump();

    expect(virtualFitting.vtonTryOnCalls, 0);
    expect(find.text('RESULTADO GEMINI'), findsOneWidget);
    expect(
      find.text(
        'Prenda seleccionada. Elegí o capturá una foto para generar la prueba virtual.',
      ),
      findsOneWidget,
    );
  });
}

Future<void> _tapGalleryAction(WidgetTester tester) async {
  final finder = find.text('ELEGIR FOTO DE GALERÍA');
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pump();
}

Future<void> _tapGenerateAction(WidgetTester tester) async {
  final finder = find.text('Generar prueba virtual');
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> _tapRetryAction(WidgetTester tester) async {
  final finder = find.text('Reintentar').first;
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Widget _screenUnderTest({
  required _FakeVirtualFittingRepository virtualFitting,
  required _FakeCatalogRepository catalog,
  String? imageUrl,
  Future<XFile?> Function()? pickImageFromGallery,
}) {
  return ProviderScope(
    overrides: [
      virtualFittingRepositoryProvider.overrideWithValue(virtualFitting),
      catalogRepositoryProvider.overrideWithValue(catalog),
    ],
    child: MaterialApp(
      home: VirtualFittingScreen(
        productId: 1,
        productName: 'Blazer inicial',
        imageUrl: imageUrl,
        price: 120,
        pickImageFromGallery: pickImageFromGallery,
      ),
    ),
  );
}

class _FakeVirtualFittingRepository extends VirtualFittingRepository {
  _FakeVirtualFittingRepository() : super(_apiClient());

  int vtonTryOnCalls = 0;
  bool throwOnTryOn = false;
  String? lastImageBase64;
  Map<String, dynamic>? lastMetrics;

  @override
  Future<Map<String, dynamic>> start(
    int productId, {
    String deviceInfo = 'mobile-simulator',
  }) async => {'id': 10};

  @override
  Future<Map<String, dynamic>> vtonTryOn(
    int productId, {
    String? imageBase64,
    Map<String, dynamic>? metrics,
  }) async {
    vtonTryOnCalls += 1;
    lastImageBase64 = imageBase64;
    lastMetrics = metrics;
    if (throwOnTryOn) throw Exception('provider unavailable');
    return {
      'composite_image_base64': _transparentPngBase64,
      'calce_porcentaje': 98.5,
      'provider_status': 'completed',
    };
  }
}

class _FakeCatalogRepository extends CatalogRepository {
  _FakeCatalogRepository({required this.items}) : super(_apiClient());

  final List<CatalogItem> items;

  @override
  Future<CatalogPage> list({String query = '', int page = 1}) async =>
      CatalogPage(items, 1);
}

Uint8List _jpegBytes() => base64Decode(_transparentPngBase64);

const _transparentPngBase64 =
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=';

ApiClient _apiClient() =>
    ApiClient(client: MockClient((request) async => http.Response('{}', 200)));
