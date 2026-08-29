import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import 'network/api_client.dart';
import 'storage/session_storage.dart';
import '../features/auth/data/auth_repository.dart';
import '../features/auth/application/auth_controller.dart';
import '../features/catalog/data/catalog_repository.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final sessionStorageProvider = Provider<SessionStorage>(
  (ref) => SessionStorage(),
);
final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStorageProvider),
  ),
);
final authControllerProvider = ChangeNotifierProvider<AuthController>(
  (ref) => AuthController(ref.watch(authRepositoryProvider)),
);
final catalogRepositoryProvider = Provider<CatalogRepository>(
  (ref) => CatalogRepository(ref.watch(apiClientProvider)),
);
