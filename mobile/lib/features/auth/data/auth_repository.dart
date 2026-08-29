import '../../../core/network/api_client.dart';
import '../../../core/storage/session_storage.dart';

class AuthRepository {
  AuthRepository(this._api, this._storage);

  final ApiClient _api;
  final SessionStorage _storage;

  Future<SessionData?> restore() async {
    final session = await _storage.read();
    _api.accessToken = session?.accessToken;
    return session;
  }

  Future<SessionData> login(String email, String password) async {
    final json =
        await _api.post(
              '/auth/login',
              body: {'email': email, 'password': password},
            )
            as Map<String, dynamic>;
    return _save(json);
  }

  Future<SessionData> register(Map<String, String> data) async {
    final json =
        await _api.post('/auth/register', body: data) as Map<String, dynamic>;
    return _save(json);
  }

  Future<void> logout(SessionData? session) async {
    if (session != null) {
      try {
        await _api.post(
          '/auth/logout',
          body: {'refresh_token': session.refreshToken},
        );
      } catch (_) {}
    }
    _api.accessToken = null;
    await _storage.clear();
  }

  Future<SessionData> _save(Map<String, dynamic> json) async {
    final session = SessionData.fromJson(json);
    _api.accessToken = session.accessToken;
    await _storage.write(session);
    return session;
  }
}
