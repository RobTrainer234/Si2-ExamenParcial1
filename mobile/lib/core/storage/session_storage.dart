import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class SessionData {
  const SessionData({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  final String accessToken;
  final String refreshToken;
  final Map<String, dynamic> user;

  Map<String, dynamic> toJson() => {
    'access_token': accessToken,
    'refresh_token': refreshToken,
    'user': user,
  };

  factory SessionData.fromJson(Map<String, dynamic> json) => SessionData(
    accessToken: json['access_token'] as String,
    refreshToken: json['refresh_token'] as String,
    user: Map<String, dynamic>.from(json['user'] as Map),
  );
}

class SessionStorage {
  static const _key = 'fashionstore_session';

  Future<SessionData?> read() async {
    final preferences = await SharedPreferences.getInstance();
    final raw = preferences.getString(_key);
    if (raw == null) return null;
    try {
      return SessionData.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      await clear();
      return null;
    }
  }

  Future<void> write(SessionData session) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_key, jsonEncode(session.toJson()));
  }

  Future<void> clear() async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.remove(_key);
  }
}
