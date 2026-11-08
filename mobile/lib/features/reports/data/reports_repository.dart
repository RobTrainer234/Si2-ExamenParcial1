import '../../../core/network/api_client.dart';
import 'reports_models.dart';

class ReportsRepository {
  const ReportsRepository(this._api);

  final ApiClient _api;

  Future<ReportAssistantResponse> askAssistant(
    String prompt, {
    String? dateFrom,
    String? dateTo,
    int? branchId,
  }) async {
    final body = <String, dynamic>{'prompt': prompt};
    if (dateFrom != null) body['date_from'] = dateFrom;
    if (dateTo != null) body['date_to'] = dateTo;
    if (branchId != null) body['branch_id'] = branchId;

    final response = await _api.post('/reports/assistant', body: body);
    return ReportAssistantResponse.fromJson(response as Map<String, dynamic>);
  }

  Future<DemandForecastResponse> getDemandForecast({
    int? branchId,
    int weeksAhead = 6,
  }) async {
    final query = <String, String>{'weeks_ahead': weeksAhead.toString()};
    if (branchId != null) query['branch_id'] = branchId.toString();

    final response = await _api.get('/reports/ml/demand-forecast', query: query);
    return DemandForecastResponse.fromJson(response as Map<String, dynamic>);
  }

  Future<CustomerSegmentationResponse> getCustomerSegments({
    int nClusters = 4,
  }) async {
    final query = <String, String>{
      'n_clusters': nClusters.toString(),
    };
    final response = await _api.get('/reports/ml/customer-segments', query: query);
    return CustomerSegmentationResponse.fromJson(response as Map<String, dynamic>);
  }

  Future<MLTrainingResponse> trainMLModels() async {
    final response = await _api.post('/reports/ml/train', body: {});
    return MLTrainingResponse.fromJson(response as Map<String, dynamic>);
  }

  Future<String> transcribeAudio(
    String audioBase64, {
    String mimeType = 'audio/mp4',
  }) async {
    final response = await _api.post(
      '/reports/transcribe-audio',
      body: {
        'audio_base64': audioBase64,
        'mime_type': mimeType,
      },
    );
    final map = response as Map<String, dynamic>;
    return map['text'] as String? ?? '';
  }
}
