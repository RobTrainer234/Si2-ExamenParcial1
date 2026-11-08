import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/offline/offline_database.dart';
import 'package:fashionstore_mobile/core/offline/offline_models.dart';
import 'package:fashionstore_mobile/core/storage/session_storage.dart';
import 'package:fashionstore_mobile/features/auth/application/auth_controller.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_repository.dart';

class FakeAuthRepository extends AuthRepository {
  FakeAuthRepository()
      : super(
          _DummyApiClient(),
          _DummySessionStorage(),
        );

  SessionData? currentSession;

  @override
  Future<SessionData?> restore() async => currentSession;

  @override
  Future<SessionData> login(String email, String password) async {
    if (email.contains('beta')) {
      return SessionData(
        accessToken: 'token-beta',
        refreshToken: 'refresh-beta',
        user: {'id': 20, 'tenant_id': 2, 'email': email, 'first_name': 'BetaUser'},
      );
    }
    return SessionData(
      accessToken: 'token-alpha',
      refreshToken: 'refresh-alpha',
      user: {'id': 10, 'tenant_id': 1, 'email': email, 'first_name': 'AlphaUser'},
    );
  }

  @override
  Future<void> logout(SessionData? session) async {
    currentSession = null;
  }
}

class _DummyApiClient extends ApiClient {}

class _DummySessionStorage implements SessionStorage {
  @override
  Future<void> clear() async {}

  @override
  Future<SessionData?> read() async => null;

  @override
  Future<void> write(SessionData session) async {}
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late OfflineDatabase offlineDb;
  late FakeAuthRepository fakeRepo;

  setUp(() {
    offlineDb = OfflineDatabase(inMemory: true);
    fakeRepo = FakeAuthRepository();
  });

  tearDown(() async {
    await offlineDb.close();
  });

  final sampleSync = SyncCatalogResponse(
    metadata: const SyncMetadata(
      tenantId: 1,
      tenantName: 'Empresa Alpha',
      branchId: 1,
      branchName: 'Casa Matriz',
      syncTimestamp: '2026-10-23T20:00:00Z',
      catalogVersion: 'v1.0-alpha',
    ),
    categories: [const SyncCategory(id: 1, name: 'Tops', isActive: true)],
    products: [
      const SyncProduct(
        id: 1,
        categoryId: 1,
        categoryName: 'Tops',
        name: 'Top Alpha',
        code: 'TOP-1',
        slug: 'top-alpha',
        price: 50.0,
        imageUrl: null,
        isActive: true,
      ),
    ],
    variants: [
      const SyncVariant(
        id: 1,
        productId: 1,
        sku: 'TOP-1-S',
        sizeId: 1,
        sizeName: 'S',
        colorId: 1,
        colorName: 'Blanco',
        price: 50.0,
        isActive: true,
      ),
    ],
    inventory: [
      const SyncInventory(
        productVariantId: 1,
        stockQuantity: 10,
        reservedQuantity: 0,
        availableQuantity: 10,
      ),
    ],
  );

  test('T1.4.6: logout purga completamente el catálogo offline de SQLite', () async {
    final controller = AuthController(fakeRepo, offlineDb: offlineDb);
    await controller.login('alpha@example.com', 'secret');
    expect(controller.isAuthenticated, isTrue);

    // Save offline catalog
    await offlineDb.saveCatalogSync(sampleSync);
    expect(await offlineDb.hasOfflineData(), isTrue);

    // User logs out
    await controller.logout();
    expect(controller.isAuthenticated, isFalse);

    // Verify local SQLite storage was purged
    expect(await offlineDb.hasOfflineData(), isFalse);
    expect(await offlineDb.getMetadata(), isNull);
  });

  test('T1.4.6: cambio de usuario o tenant purga el catálogo previo para evitar fuga de datos', () async {
    final controller = AuthController(fakeRepo, offlineDb: offlineDb);
    await controller.login('alpha@example.com', 'secret');
    expect(controller.session?.user['tenant_id'], 1);

    // Save offline catalog belonging to Tenant 1
    await offlineDb.saveCatalogSync(sampleSync);
    expect(await offlineDb.hasOfflineData(), isTrue);

    // Log in with Tenant 2 user
    await controller.login('beta@example.com', 'secret');
    expect(controller.session?.user['tenant_id'], 2);

    // Verify SQLite storage of Tenant 1 was purged
    expect(await offlineDb.hasOfflineData(), isFalse);
  });
}
