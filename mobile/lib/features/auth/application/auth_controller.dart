import 'package:flutter/foundation.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/offline/offline_database.dart';
import '../../../core/storage/session_storage.dart';
import '../data/auth_repository.dart';

class AuthController extends ChangeNotifier {
  AuthController(this._repository, {this.offlineDb}) {
    restore();
  }

  final AuthRepository _repository;
  final OfflineDatabase? offlineDb;
  SessionData? session;
  bool loading = true;
  String? error;

  bool get isAuthenticated => session != null;

  Future<void> restore() async {
    session = await _repository.restore();
    loading = false;
    notifyListeners();
  }

  Future<bool> login(String email, String password) =>
      _run(() => _repository.login(email, password));

  Future<bool> register(Map<String, String> data) =>
      _run(() => _repository.register(data));

  Future<void> logout() async {
    await _repository.logout(session);
    await offlineDb?.clearAll();
    session = null;
    notifyListeners();
  }

  Future<bool> _run(Future<SessionData> Function() action) async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      final oldTenantId = session?.user['tenant_id'];
      final oldUserId = session?.user['id'];
      session = await action();
      final newTenantId = session?.user['tenant_id'];
      final newUserId = session?.user['id'];
      if (oldTenantId != newTenantId || oldUserId != newUserId) {
        await offlineDb?.clearAll();
      }
      return true;
    } on ApiException catch (exception) {
      error = exception.message;
      return false;
    } catch (e) {
      error = 'Error al procesar la autenticación: $e';
      return false;
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}
