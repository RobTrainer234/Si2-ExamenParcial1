import 'package:flutter/foundation.dart';

import '../network/api_client.dart';
import 'offline_database.dart';
import 'offline_models.dart';

class SyncCatalogService extends ChangeNotifier {
  SyncCatalogService({
    required this.api,
    required this.offlineDb,
  });

  final ApiClient api;
  final OfflineDatabase offlineDb;

  bool _isSyncing = false;
  String? _syncError;
  DateTime? _lastSync;
  SyncMetadata? _lastMetadata;

  bool get isSyncing => _isSyncing;
  String? get syncError => _syncError;
  DateTime? get lastSync => _lastSync;
  SyncMetadata? get lastMetadata => _lastMetadata;

  Future<void> init() async {
    final meta = await offlineDb.getMetadata();
    if (meta != null) {
      _lastMetadata = meta;
      _lastSync = DateTime.tryParse(meta.syncTimestamp);
      notifyListeners();
    }
  }

  Future<bool> syncCatalog({int? branchId}) async {
    _isSyncing = true;
    _syncError = null;
    notifyListeners();

    try {
      final json = await api.get(
        '/sync/catalog',
        query: {
          if (branchId != null) 'branch_id': '$branchId',
        },
      ) as Map<String, dynamic>;

      final syncData = SyncCatalogResponse.fromJson(json);
      await offlineDb.saveCatalogSync(syncData);

      _lastSync = DateTime.tryParse(syncData.metadata.syncTimestamp) ??
          DateTime.now().toUtc();
      _lastMetadata = syncData.metadata;
      _isSyncing = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isSyncing = false;
      _syncError = e.toString().replaceFirst(RegExp(r'^Exception:\s*'), '');
      notifyListeners();
      return false;
    }
  }

  Future<void> clear() async {
    await offlineDb.clearAll();
    _lastSync = null;
    _lastMetadata = null;
    _syncError = null;
    notifyListeners();
  }
}
