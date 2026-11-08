import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import 'network/api_client.dart';
import 'notifications/notification_service.dart';
import 'offline/connectivity_monitor.dart';
import 'offline/offline_database.dart';
import 'offline/sync_catalog_service.dart';
import 'offline/offline_transaction_repository.dart';
import 'offline/sync_transaction_service.dart';
import 'storage/session_storage.dart';
import '../features/auth/data/auth_repository.dart';
import '../features/auth/application/auth_controller.dart';
import '../features/catalog/data/catalog_repository.dart';
import '../features/reservations/data/reservation_repository.dart';
import '../features/cart/data/cart_repository.dart';
import '../features/purchases/data/purchase_repository.dart';
import '../features/recommendations/data/recommendation_repository.dart';
import '../features/reports/data/reports_repository.dart';
import '../features/virtual_fitting/data/virtual_fitting_repository.dart';
import '../features/exchange/data/exchange_repository.dart';

final notificationServiceProvider = Provider<NotificationService>(
  (ref) => NotificationService(),
);
final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(notifications: ref.watch(notificationServiceProvider)),
);
final sessionStorageProvider = Provider<SessionStorage>(
  (ref) => SessionStorage(),
);
final connectivityMonitorProvider = ChangeNotifierProvider<ConnectivityMonitor>(
  (ref) {
    final monitor = ConnectivityMonitor(ConnectivityPlusSource());
    monitor.start();
    return monitor;
  },
);
final offlineDatabaseProvider = Provider<OfflineDatabase>(
  (ref) => OfflineDatabase(),
);
final syncCatalogServiceProvider = ChangeNotifierProvider<SyncCatalogService>(
  (ref) => SyncCatalogService(
    api: ref.watch(apiClientProvider),
    offlineDb: ref.watch(offlineDatabaseProvider),
  ),
);
final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStorageProvider),
  ),
);
final authControllerProvider = ChangeNotifierProvider<AuthController>(
  (ref) => AuthController(
    ref.watch(authRepositoryProvider),
    offlineDb: ref.watch(offlineDatabaseProvider),
  ),
);
final catalogRepositoryProvider = Provider<CatalogRepository>(
  (ref) => CatalogRepository(
    ref.watch(apiClientProvider),
    offlineDb: ref.watch(offlineDatabaseProvider),
  ),
);
final offlineTransactionRepositoryProvider = Provider<OfflineTransactionRepository>(
  (ref) => OfflineTransactionRepository(ref.watch(offlineDatabaseProvider)),
);
final syncTransactionServiceProvider =
    ChangeNotifierProvider<SyncTransactionService>(
  (ref) => SyncTransactionService(
    api: ref.watch(apiClientProvider),
    offlineRepo: ref.watch(offlineTransactionRepositoryProvider),
  ),
);
final reservationRepositoryProvider = Provider<ReservationRepository>(
  (ref) => ReservationRepository(ref.watch(apiClientProvider)),
);
final cartRepositoryProvider = Provider<CartRepository>(
  (ref) => CartRepository(ref.watch(apiClientProvider)),
);
final purchaseRepositoryProvider = Provider<PurchaseRepository>(
  (ref) => PurchaseRepository(ref.watch(apiClientProvider)),
);
final recommendationRepositoryProvider = Provider<RecommendationRepository>(
  (ref) => RecommendationRepository(ref.watch(apiClientProvider)),
);
final virtualFittingRepositoryProvider = Provider<VirtualFittingRepository>(
  (ref) => VirtualFittingRepository(ref.watch(apiClientProvider)),
);
final reportsRepositoryProvider = Provider<ReportsRepository>(
  (ref) => ReportsRepository(ref.watch(apiClientProvider)),
);
final exchangeRepositoryProvider = Provider<ExchangeRepository>(
  (ref) => ExchangeRepository(ref.watch(apiClientProvider)),
);
