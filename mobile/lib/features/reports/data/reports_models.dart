class ReportAssistantIntent {
  const ReportAssistantIntent({
    required this.kind,
    required this.chartType,
    this.reasoning,
  });

  final String kind;
  final String chartType;
  final String? reasoning;

  factory ReportAssistantIntent.fromJson(Map<String, dynamic> json) =>
      ReportAssistantIntent(
        kind: json['kind'] as String? ?? 'dashboard',
        chartType: json['chart_type'] as String? ?? 'bar',
        reasoning: json['reasoning'] as String?,
      );
}

class ReportAssistantResponse {
  const ReportAssistantResponse({
    required this.intent,
    required this.narrative,
    required this.provider,
    required this.fallbackUsed,
    required this.data,
  });

  final ReportAssistantIntent intent;
  final String narrative;
  final String provider;
  final bool fallbackUsed;
  final dynamic data;

  factory ReportAssistantResponse.fromJson(Map<String, dynamic> json) =>
      ReportAssistantResponse(
        intent: ReportAssistantIntent.fromJson(
          json['intent'] as Map<String, dynamic>? ?? {},
        ),
        narrative: json['narrative'] as String? ?? '',
        provider: json['provider'] as String? ?? 'local',
        fallbackUsed: json['fallback_used'] as bool? ?? false,
        data: json['data'],
      );
}

class DemandForecastMetrics {
  const DemandForecastMetrics({
    this.mae,
    this.rmse,
    this.r2Score,
  });

  final double? mae;
  final double? rmse;
  final double? r2Score;

  factory DemandForecastMetrics.fromJson(Map<String, dynamic> json) =>
      DemandForecastMetrics(
        mae: (json['mae'] as num?)?.toDouble(),
        rmse: (json['rmse'] as num?)?.toDouble(),
        r2Score: (json['r2_score'] as num?)?.toDouble(),
      );
}

class DemandForecastPoint {
  const DemandForecastPoint({
    required this.weekStart,
    required this.predictedUnits,
    required this.lowerBound,
    required this.upperBound,
  });

  final String weekStart;
  final int predictedUnits;
  final int lowerBound;
  final int upperBound;

  factory DemandForecastPoint.fromJson(Map<String, dynamic> json) =>
      DemandForecastPoint(
        weekStart: json['week_start'] as String? ?? '',
        predictedUnits: json['predicted_units'] as int? ?? 0,
        lowerBound: json['lower_bound'] as int? ?? 0,
        upperBound: json['upper_bound'] as int? ?? 0,
      );
}

class DemandForecastResponse {
  const DemandForecastResponse({
    required this.target,
    required this.horizonWeeks,
    this.branchId,
    required this.metrics,
    required this.forecast,
    required this.historicalSamples,
    required this.narrative,
  });

  final String target;
  final int horizonWeeks;
  final int? branchId;
  final DemandForecastMetrics metrics;
  final List<DemandForecastPoint> forecast;
  final int historicalSamples;
  final String narrative;

  factory DemandForecastResponse.fromJson(Map<String, dynamic> json) =>
      DemandForecastResponse(
        target: json['target'] as String? ?? 'ventas_semanales',
        horizonWeeks: json['horizon_weeks'] as int? ?? 0,
        branchId: json['branch_id'] as int?,
        metrics: DemandForecastMetrics.fromJson(
          json['metrics'] as Map<String, dynamic>? ?? {},
        ),
        forecast: (json['forecast'] as List<dynamic>? ?? [])
            .map((e) => DemandForecastPoint.fromJson(e as Map<String, dynamic>))
            .toList(),
        historicalSamples: json['historical_samples'] as int? ?? 0,
        narrative: json['narrative'] as String? ?? '',
      );
}

class CustomerSegmentItem {
  const CustomerSegmentItem({
    required this.clusterId,
    required this.name,
    required this.customerCount,
    required this.percentage,
    required this.avgRecencyDays,
    required this.avgFrequency,
    required this.avgMonetary,
    required this.suggestedAction,
  });

  final int clusterId;
  final String name;
  final int customerCount;
  final double percentage;
  final double avgRecencyDays;
  final double avgFrequency;
  final double avgMonetary;
  final String suggestedAction;

  factory CustomerSegmentItem.fromJson(Map<String, dynamic> json) =>
      CustomerSegmentItem(
        clusterId: json['cluster_id'] as int? ?? 0,
        name: json['name'] as String? ?? '',
        customerCount: json['customer_count'] as int? ?? 0,
        percentage: (json['percentage'] as num?)?.toDouble() ?? 0.0,
        avgRecencyDays: (json['avg_recency_days'] as num?)?.toDouble() ?? 0.0,
        avgFrequency: (json['avg_frequency'] as num?)?.toDouble() ?? 0.0,
        avgMonetary: (json['avg_monetary'] as num?)?.toDouble() ?? 0.0,
        suggestedAction: json['suggested_action'] as String? ?? '',
      );
}

class CustomerSegmentationResponse {
  const CustomerSegmentationResponse({
    required this.algorithm,
    required this.clustersCount,
    required this.silhouetteScore,
    required this.inertia,
    required this.segments,
    required this.narrative,
  });

  final String algorithm;
  final int clustersCount;
  final double silhouetteScore;
  final double inertia;
  final List<CustomerSegmentItem> segments;
  final String narrative;

  factory CustomerSegmentationResponse.fromJson(Map<String, dynamic> json) =>
      CustomerSegmentationResponse(
        algorithm: json['algorithm'] as String? ?? 'K-Means RFM',
        clustersCount: json['clusters_count'] as int? ?? 0,
        silhouetteScore: (json['silhouette_score'] as num?)?.toDouble() ?? 0.0,
        inertia: (json['inertia'] as num?)?.toDouble() ?? 0.0,
        segments: (json['segments'] as List<dynamic>? ?? [])
            .map((e) => CustomerSegmentItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        narrative: json['narrative'] as String? ?? '',
      );
}

class MLTrainingResponse {
  const MLTrainingResponse({
    required this.status,
    required this.message,
    required this.timestamp,
  });

  final String status;
  final String message;
  final String timestamp;

  factory MLTrainingResponse.fromJson(Map<String, dynamic> json) =>
      MLTrainingResponse(
        status: json['status'] as String? ?? 'SUCCESS',
        message: json['message'] as String? ?? '',
        timestamp: json['timestamp'] as String? ?? '',
      );
}
