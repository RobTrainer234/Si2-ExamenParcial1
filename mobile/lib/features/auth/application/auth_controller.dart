import 'package:flutter/foundation.dart';

import '../../../core/errors/api_exception.dart';
import '../data/auth_repository.dart';
import '../../../core/storage/session_storage.dart';

class AuthController extends ChangeNotifier {
  AuthController(this._repository) {
    restore();
  }

  final AuthRepository _repository;
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
    session = null;
    notifyListeners();
  }

  Future<bool> _run(Future<SessionData> Function() action) async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      session = await action();
      return true;
    } on ApiException catch (exception) {
      error = exception.message;
      return false;
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}
