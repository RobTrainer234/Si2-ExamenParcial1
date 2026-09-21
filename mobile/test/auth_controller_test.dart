import 'package:flutter_test/flutter_test.dart';

import 'package:fashionstore_mobile/core/errors/api_exception.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/storage/session_storage.dart';
import 'package:fashionstore_mobile/features/auth/application/auth_controller.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_repository.dart';

class FakeAuthRepository extends AuthRepository {
  FakeAuthRepository() : super(ApiClient(), SessionStorage());

  Object? nextError;

  @override
  Future<SessionData?> restore() async => null;

  @override
  Future<SessionData> register(Map<String, String> data) async {
    final error = nextError;
    if (error != null) throw error;
    return const SessionData(
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      user: {'email': 'ana@example.com'},
    );
  }
}

void main() {
  test('register clears loading after unexpected errors', () async {
    final repository = FakeAuthRepository()..nextError = Exception('offline');
    final controller = AuthController(repository);
    await Future<void>.delayed(Duration.zero);

    final result = await controller.register({'email': 'ana@example.com'});

    expect(result, isFalse);
    expect(controller.loading, isFalse);
    expect(controller.error, contains('Error al procesar la autenticación'));
    expect(controller.session, isNull);
  });

  test(
    'register clears loading and keeps backend messages for ApiException',
    () async {
      final repository = FakeAuthRepository()
        ..nextError = const ApiException('El correo ya existe.', 400);
      final controller = AuthController(repository);
      await Future<void>.delayed(Duration.zero);

      final result = await controller.register({'email': 'ana@example.com'});

      expect(result, isFalse);
      expect(controller.loading, isFalse);
      expect(controller.error, 'El correo ya existe.');
    },
  );

  test('register stores the session and clears loading on success', () async {
    final controller = AuthController(FakeAuthRepository());
    await Future<void>.delayed(Duration.zero);

    final result = await controller.register({'email': 'ana@example.com'});

    expect(result, isTrue);
    expect(controller.loading, isFalse);
    expect(controller.error, isNull);
    expect(controller.session?.accessToken, 'access-token');
  });
}
