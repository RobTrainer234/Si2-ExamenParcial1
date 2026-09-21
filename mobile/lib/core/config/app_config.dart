import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  const AppConfig._();

  static String _customBaseUrl = '';

  static String get apiBaseUrl {
    if (_customBaseUrl.isNotEmpty) {
      return _customBaseUrl;
    }
    return const String.fromEnvironment(
      'API_URL',
      defaultValue: 'http://10.0.2.2:8000/api/v1',
    );
  }

  static String get serverBaseUrl {
    final base = apiBaseUrl.trim();
    return base.replaceAll(RegExp(r'/api/v1/?$'), '');
  }

  static String? resolveImageUrl(String? rawUrl) {
    if (rawUrl == null) return null;
    var trimmed = rawUrl.trim();
    if (trimmed.isEmpty) return null;
    if (trimmed.startsWith('/')) {
      return '$serverBaseUrl$trimmed';
    }
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      return '$serverBaseUrl/$trimmed';
    }
    final serverUri = Uri.tryParse(serverBaseUrl);
    if (serverUri != null &&
        serverUri.host.isNotEmpty &&
        serverUri.host != 'localhost' &&
        serverUri.host != '127.0.0.1') {
      trimmed = trimmed
          .replaceFirst('http://localhost:8000', serverBaseUrl)
          .replaceFirst('http://127.0.0.1:8000', serverBaseUrl)
          .replaceFirst('https://localhost:8000', serverBaseUrl)
          .replaceFirst('https://127.0.0.1:8000', serverBaseUrl);
    }
    return trimmed;
  }

  static Future<void> loadCustomBaseUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('custom_api_base_url');
      if (saved != null && saved.trim().isNotEmpty) {
        _customBaseUrl = saved.trim();
      }
    } catch (_) {}
  }

  static Future<void> setCustomBaseUrl(String url) async {
    _customBaseUrl = url.trim();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('custom_api_base_url', _customBaseUrl);
    } catch (_) {}
  }

  static Future<bool> testConnection([String? testUrl]) async {
    final baseUrl = (testUrl ?? apiBaseUrl).trim();
    final healthUrl = baseUrl.endsWith('/api/v1')
        ? '$baseUrl/health'
        : (baseUrl.endsWith('/') ? '${baseUrl}health' : '$baseUrl/health');
    try {
      final response = await http
          .get(Uri.parse(healthUrl))
          .timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static const sandboxPaymentWebhookSecret = String.fromEnvironment(
    'SANDBOX_PAYMENT_WEBHOOK_SECRET',
    defaultValue: 'sandbox-webhook-secret',
  );
}
