import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../errors/api_exception.dart';
import '../notifications/notification_service.dart';

class ApiClient {
  ApiClient({
    http.Client? client,
    NotificationService? notifications,
    this.timeoutForPath,
  }) : _client = client ?? http.Client(),
       _notifications = notifications ?? NotificationService();

  final http.Client _client;
  final NotificationService _notifications;
  final Duration Function(String path, Duration timeout)? timeoutForPath;
  String? accessToken;

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}$path',
    ).replace(queryParameters: query);
    return _send(() => _client.get(uri, headers: _headers), path: path);
  }

  Future<dynamic> post(
    String path, {
    Object? body,
    Map<String, String>? headers,
  }) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}$path');
    return _send(
      () => _client.post(
        uri,
        headers: {..._headers, ...?headers},
        body: body == null ? null : jsonEncode(body),
      ),
      method: 'POST',
      path: path,
    );
  }

  Future<dynamic> patch(String path, {Object? body}) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}$path');
    return _send(
      () => _client.patch(
        uri,
        headers: _headers,
        body: body == null ? null : jsonEncode(body),
      ),
      method: 'PATCH',
      path: path,
    );
  }

  Future<dynamic> delete(String path) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}$path');
    return _send(
      () => _client.delete(uri, headers: _headers),
      method: 'DELETE',
      path: path,
    );
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (accessToken != null) 'Authorization': 'Bearer $accessToken',
  };

  Future<dynamic> _send(
    Future<http.Response> Function() request, {
    String method = 'GET',
    required String path,
  }) async {
    late final http.Response response;
    try {
      response = await request().timeout(_timeoutFor(path));
    } catch (e) {
      final reason = e is TimeoutException
          ? 'La solicitud tardó demasiado.'
          : e.toString();
      final message =
          'Error al conectar con el servidor ($reason).\nURL: ${AppConfig.apiBaseUrl}$path';
      _notifications.showError(message);
      throw ApiException(message, 0);
    }
    dynamic body;
    try {
      body = response.body.isEmpty ? null : jsonDecode(response.body);
    } catch (_) {
      body = null;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body is Map<String, dynamic> ? body['detail'] : null;
      final message = switch (detail) {
        Map<String, dynamic>() => detail['message'] as String?,
        String value => value,
        List<dynamic> values =>
          values
              .map(
                (value) => value is Map<String, dynamic>
                    ? value['msg']?.toString() ?? value.toString()
                    : value.toString(),
              )
              .join('. '),
        _ => null,
      };
      final resolvedMessage =
          message ??
          'Error del servidor (${response.statusCode}): ${response.body}';
      final code = detail is Map<String, dynamic> && detail['code'] is String
          ? detail['code'] as String
          : null;
      _notifications.showError(resolvedMessage);
      throw ApiException(resolvedMessage, response.statusCode, code: code);
    }
    if (_isMutating(method)) {
      _notifications.showSuccess(_successMessage(method, path));
    }
    return body;
  }

  bool _isMutating(String method) =>
      {'POST', 'PATCH', 'DELETE'}.contains(method);

  Duration _timeoutFor(String path) {
    final timeout = path == '/catalogo/vton/try-on'
        ? const Duration(seconds: 90)
        : path == '/reports/transcribe-audio'
        ? const Duration(seconds: 45)
        : const Duration(seconds: 10);
    return timeoutForPath?.call(path, timeout) ?? timeout;
  }

  String _successMessage(String method, String path) {
    if (path == '/auth/login') return 'Inicio de sesión correcto.';
    if (path == '/auth/register') return 'Cuenta creada correctamente.';
    switch (method) {
      case 'POST':
        return 'Operación creada correctamente.';
      case 'PATCH':
        return 'Cambios guardados correctamente.';
      case 'DELETE':
        return 'Elemento eliminado correctamente.';
      default:
        return 'Operación completada correctamente.';
    }
  }
}
