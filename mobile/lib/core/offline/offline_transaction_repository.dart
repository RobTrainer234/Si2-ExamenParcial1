import 'dart:convert';
import 'dart:math';

import 'offline_database.dart';
import 'offline_models.dart';

class OfflineTransactionRepository {
  OfflineTransactionRepository(this._db);

  final OfflineDatabase _db;

  String _generateOperationId() {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final randomSuffix = Random().nextInt(900000) + 100000;
    return 'op-mob-$timestamp-$randomSuffix';
  }

  Future<OfflineCustomerRecord> saveCustomer({
    String? id,
    required String fullName,
    required String nitCi,
    String? phone,
    String? email,
  }) async {
    return await _db.saveCustomer(
      id: id,
      fullName: fullName,
      nitCi: nitCi,
      phone: phone,
      email: email,
    );
  }

  Future<List<OfflineCustomerRecord>> listCustomers({String query = ''}) async {
    return await _db.listCustomers(query: query);
  }

  Future<void> deleteCustomer(String id) async {
    await _db.deleteCustomer(id);
  }

  Future<OfflineOperationRecord> recordOfflineSale({
    required int branchId,
    required OfflineSalePayload payload,
  }) async {
    final clientOpId = _generateOperationId();
    final now = DateTime.now().toUtc().toIso8601String();

    final record = OfflineOperationRecord(
      clientOperationId: clientOpId,
      branchId: branchId,
      operationType: 'SALE',
      status: 'PENDING_SYNC',
      payloadJson: jsonEncode(payload.toJson()),
      createdAt: now,
    );

    if (payload.customerName != null &&
        payload.customerName!.trim().isNotEmpty) {
      await _db.saveCustomer(
        fullName: payload.customerName!.trim(),
        nitCi: (payload.customerNit ?? '0').trim(),
        phone: payload.customerPhone,
      );
    }

    // Persist operation record in SQLite outbox
    await _db.insertOperation(record);

    // Deduct provisional stock in SQLite local inventory
    for (final item in payload.items) {
      await _db.decrementLocalInventory(
        item.productVariantId,
        item.quantity,
      );
    }

    return record;
  }

  Future<OfflineOperationRecord> recordOfflineReservation({
    required int branchId,
    required OfflineReservationPayload payload,
  }) async {
    final clientOpId = _generateOperationId();
    final now = DateTime.now().toUtc().toIso8601String();

    final record = OfflineOperationRecord(
      clientOperationId: clientOpId,
      branchId: branchId,
      operationType: 'RESERVATION',
      status: 'PENDING_SYNC',
      payloadJson: jsonEncode(payload.toJson()),
      createdAt: now,
    );

    if (payload.customerName.trim().isNotEmpty) {
      await _db.saveCustomer(
        fullName: payload.customerName.trim(),
        nitCi: (payload.customerNit ?? '0').trim(),
        phone: payload.customerPhone,
      );
    }

    // Persist operation record in SQLite outbox
    await _db.insertOperation(record);

    // Update provisional reserved stock in SQLite local inventory
    for (final item in payload.items) {
      await _db.reserveLocalInventory(
        item.productVariantId,
        item.quantity,
      );
    }

    return record;
  }

  Future<List<OfflineOperationRecord>> listOperations({String? status}) async {
    return await _db.listOperations(status: status);
  }

  Future<int> countPendingOperations() async {
    return await _db.countPendingOperations();
  }

  Future<OfflineOperationRecord?> getOperation(String clientOperationId) async {
    return await _db.getOperation(clientOperationId);
  }

  Future<void> updateOperation(OfflineOperationRecord record) async {
    await _db.updateOperation(record);
  }

  Future<void> clearOperations() async {
    await _db.clearOperations();
  }
}
