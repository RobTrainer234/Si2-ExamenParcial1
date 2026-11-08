import 'package:flutter_test/flutter_test.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/features/reports/data/reports_repository.dart';

class _FakeApiClient extends ApiClient {
  _FakeApiClient(this.response);

  final dynamic response;
  Object? lastBody;

  @override
  Future<dynamic> post(String path, {Object? body, Map<String, String>? headers}) async {
    lastBody = body;
    return response;
  }
}

void main() {
  test('reads the backend text response and sends the selected audio MIME', () async {
    final api = _FakeApiClient({'text': '¿Qué productos se vendieron más?'});
    final repository = ReportsRepository(api);

    final transcript = await repository.transcribeAudio('encoded-audio');

    expect(transcript, '¿Qué productos se vendieron más?');
    expect((api.lastBody as Map<String, dynamic>)['mime_type'], 'audio/mp4');
  });

  test('does not turn an empty backend transcript into a report request', () async {
    final api = _FakeApiClient({'text': ''});
    final repository = ReportsRepository(api);

    expect(await repository.transcribeAudio('encoded-audio'), isEmpty);
  });
}
