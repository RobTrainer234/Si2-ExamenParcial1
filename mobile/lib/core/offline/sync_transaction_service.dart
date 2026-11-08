import 'dart:convert';
import 'package:flutter/foundation.dart';

import '../network/api_client.dart';
import 'offline_models.dart';
import 'offline_transaction_repository.dart';

class SyncTransactionService extends ChangeNotifier {
  SyncTransactionService({
    required this.api,
    required this.offlineRepo,
  });

  final ApiClient api;
  final OfflineTransactionRepository offlineRepo;

  bool _isSyncing = false;
  String? _syncError;
  int _pendingCount = 0;
  SyncTransactionBatchResponse? _lastBatchResult;

  bool get isSyncing => _isSyncing;
  String? get syncError => _syncError;
  int get pendingCount => _pendingCount;
  SyncTransactionBatchResponse? get lastBatchResult => _lastBatchResult;

  Future<void> refreshPendingCount() async {
    _pendingCount = await offlineRepo.countPendingOperations();
    notifyListeners();
  }

  Future<SyncTransactionBatchResponse?> syncPendingTransactions() async {
    final pending = await offlineRepo.listOperations(status: 'PENDING_SYNC');
    if (pending.isEmpty) {
      _pendingCount = 0;
      notifyListeners();
      return null;
    }

    _isSyncing = true;
    _syncError = null;
    notifyListeners();

    try {
      final operationsPayload = pending.map((op) {
        Map<String, dynamic> payloadMap = {};
        try {
          payloadMap = jsonDecode(op.payloadJson) as Map<String, dynamic>;
        } catch (_) {}

        return {
          'client_operation_id': op.clientOperationId,
          'branch_id': op.branchId,
          'operation_type': op.operationType,
          'payload': payloadMap,
          'created_at': op.createdAt,
        };
      }).toList();

      final responseJson = await api.post(
        '/sync/transactions',
        body: {'operations': operationsPayload},
      ) as Map<String, dynamic>;

      final batchResponse =
          SyncTransactionBatchResponse.fromJson(responseJson);

      // Update SQLite operations based on backend results
      for (final result in batchResponse.results) {
        final existing =
            await offlineRepo.getOperation(result.clientOperationId);
        if (existing != null) {
          final updated = existing.copyWith(
            status: result.status,
            saleId: result.saleId,
            orderNumber: result.orderNumber,
            reservationId: result.reservationId,
            conflictDetailJson: result.conflict != null
                ? jsonEncode(result.conflict!.toJson())
                : null,
            syncedAt: result.processedAt.isNotEmpty
                ? result.processedAt
                : DateTime.now().toUtc().toIso8601String(),
          );
          await offlineRepo.updateOperation(updated);
        }
      }

      _lastBatchResult = batchResponse;
      _pendingCount = await offlineRepo.countPendingOperations();
      _isSyncing = false;
      notifyListeners();
      return batchResponse;
    } catch (e) {
      _isSyncing = false;
      _syncError = e.toString().replaceFirst(RegExp(r'^Exception:\s*'), '');
      _pendingCount = await offlineRepo.countPendingOperations();
      notifyListeners();
      return null;
    }
  }
}
