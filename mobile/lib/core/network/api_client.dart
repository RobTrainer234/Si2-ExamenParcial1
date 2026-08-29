import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../errors/api_exception.dart';

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? accessToken;

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}$path',
    ).replace(queryParameters: query);
    return _send(() => _client.get(uri, headers: _headers));
  }

  Future<dynamic> post(String path, {Object? body}) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}$path');
    return _send(
      () => _client.post(
        uri,
        headers: _headers,
        body: body == null ? null : jsonEncode(body),
      ),
    );
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (accessToken != null) 'Authorization': 'Bearer $accessToken',
  };

  Future<dynamic> _send(Future<http.Response> Function() request) async {
    final response = await request();
    dynamic body;
    try {
      body = response.body.isEmpty ? null : jsonDecode(response.body);
    } catch (_) {
      body = null;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body is Map<String, dynamic> ? body['detail'] : null;
      final message = detail is Map<String, dynamic>
          ? detail['message'] as String?
          : detail as String?;
      throw ApiException(
        message ?? 'No se pudo completar la solicitud.',
        response.statusCode,
      );
    }
    return body;
  }
}
