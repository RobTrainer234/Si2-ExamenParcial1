import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fashionstore_mobile/core/errors/api_exception.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/providers.dart';
import 'package:fashionstore_mobile/features/reports/data/reports_models.dart';
import 'package:fashionstore_mobile/features/reports/data/reports_repository.dart';
import 'package:fashionstore_mobile/features/reports/data/voice_recording_service.dart';
import 'package:fashionstore_mobile/features/reports/presentation/reports_screen.dart';

class _FakeVoiceRecorder implements VoiceRecorderBackend {
  @override
  Future<bool> requestPermission() async => true;

  @override
  Future<void> start() async {}

  @override
  Future<String?> stop() async => null;

  @override
  Future<void> cancel() async {}

  @override
  Future<void> dispose() async {}
}

class _FakeReportsApiClient extends ApiClient {
  _FakeReportsApiClient({this.assistantError, this.assistantResponse});

  final ApiException? assistantError;
  final Map<String, dynamic>? assistantResponse;

  @override
  Future<dynamic> post(String path, {Object? body, Map<String, String>? headers}) async {
    if (path == '/reports/assistant' && assistantError != null) {
      throw assistantError!;
    }
    if (path == '/reports/assistant') {
      return assistantResponse ?? {
        'intent': {
          'kind': 'revenue_by_category',
          'chart_type': 'pie',
          'reasoning': 'Categorías con mayores ingresos',
        },
        'narrative': 'Vestidos Fiesta lidera con Bs 4,500 en ventas este período.',
        'provider': 'gemini',
        'fallback_used': false,
        'data': [
          {'category_name': 'Vestidos Fiesta', 'total_revenue': 4500, 'units_sold': 20},
          {'category_name': 'Pantalones Lino', 'total_revenue': 2200, 'units_sold': 12},
        ],
      };
    }
    if (path == '/reports/ml/train') {
      return {
        'status': 'SUCCESS',
        'message': 'Modelos de Machine Learning reentrenados exitosamente.',
        'timestamp': '2026-10-24T03:00:00Z',
      };
    }
    return {};
  }

  @override
  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    if (path == '/reports/ml/demand-forecast') {
      return {
        'target': 'ventas_semanales',
        'horizon_weeks': 4,
        'branch_id': 1,
        'metrics': {'mae': 2.3, 'rmse': 3.1, 'r2_score': 0.89},
        'forecast': [
          {'week_start': '2026-10-26T00:00:00Z', 'predicted_units': 42, 'lower_bound': 36, 'upper_bound': 48},
          {'week_start': '2026-11-02T00:00:00Z', 'predicted_units': 48, 'lower_bound': 40, 'upper_bound': 56},
        ],
        'historical_samples': 60,
        'narrative': 'Proyección supervisada de demanda para las próximas 4 semanas.',
      };
    }
    if (path == '/reports/ml/customer-segments') {
      return {
        'algorithm': 'K-Means RFM',
        'clusters_count': 4,
        'silhouette_score': 0.44,
        'inertia': 118.0,
        'segments': [
          {
            'cluster_id': 0,
            'name': 'Clientes VIP / Champions',
            'customer_count': 28,
            'percentage': 28.0,
            'avg_recency_days': 4.5,
            'avg_frequency': 11.2,
            'avg_monetary': 4800.0,
            'suggested_action': 'Beneficios exclusivos y preventas de alta costura.',
          },
          {
            'cluster_id': 1,
            'name': 'Clientes Leales',
            'customer_count': 32,
            'percentage': 32.0,
            'avg_recency_days': 14.0,
            'avg_frequency': 6.0,
            'avg_monetary': 2100.0,
            'suggested_action': 'Incentivos de recompra y cupones de temporada.',
          },
        ],
        'narrative': 'Segmentación no supervisada RFM completada.',
      };
    }
    return {};
  }
}

void main() {
  group('ReportsModels serialization', () {
    test('ReportAssistantResponse fromJson parses intent, narrative, and chart_type', () {
      final json = {
        'intent': {
          'kind': 'top_products',
          'chart_type': 'bar',
          'reasoning': 'Top 10 prendas más vendidas',
        },
        'narrative': 'Blazer Noir encabeza el volumen de unidades.',
        'provider': 'gemini',
        'fallback_used': false,
        'data': [
          {'product_name': 'Blazer Noir', 'units_sold': 18},
        ],
      };

      final response = ReportAssistantResponse.fromJson(json);
      expect(response.intent.kind, 'top_products');
      expect(response.intent.chartType, 'bar');
      expect(response.narrative, contains('Blazer Noir'));
      expect(response.provider, 'gemini');
      expect(response.fallbackUsed, isFalse);
    });

    test('DemandForecastResponse and CustomerSegmentationResponse parse ML metrics', () {
      final forecastJson = {
        'target': 'ventas_semanales',
        'horizon_weeks': 6,
        'metrics': {'mae': 1.8, 'rmse': 2.4, 'r2_score': 0.91},
        'forecast': [
          {'week_start': '2026-10-26T00:00:00Z', 'predicted_units': 35, 'lower_bound': 30, 'upper_bound': 40},
        ],
        'historical_samples': 90,
        'narrative': 'Tendencia positiva.',
      };

      final forecast = DemandForecastResponse.fromJson(forecastJson);
      expect(forecast.target, 'ventas_semanales');
      expect(forecast.horizonWeeks, 6);
      expect(forecast.metrics.mae, 1.8);
      expect(forecast.metrics.rmse, 2.4);
      expect(forecast.metrics.r2Score, 0.91);
      expect(forecast.forecast.length, 1);
      expect(forecast.forecast.first.predictedUnits, 35);

      final segmentsJson = {
        'algorithm': 'K-Means RFM',
        'clusters_count': 4,
        'silhouette_score': 0.48,
        'inertia': 95.0,
        'segments': [
          {
            'cluster_id': 0,
            'name': 'Clientes VIP / Champions',
            'customer_count': 20,
            'percentage': 20.0,
            'avg_recency_days': 3.0,
            'avg_frequency': 15.0,
            'avg_monetary': 5200.0,
            'suggested_action': 'Atención VIP',
          },
        ],
        'narrative': 'Clustering exitoso.',
      };

      final clustering = CustomerSegmentationResponse.fromJson(segmentsJson);
      expect(clustering.clustersCount, 4);
      expect(clustering.silhouetteScore, 0.48);
      expect(clustering.inertia, 95.0);
      expect(clustering.segments.first.name, 'Clientes VIP / Champions');
    });
  });

  group('ReportsScreen Widget Tests', () {
    late _FakeReportsApiClient fakeApi;

    Future<void> pumpChart(
      WidgetTester tester, {
      required String chartType,
      required List<Map<String, dynamic>> data,
    }) async {
      final chartRepository = ReportsRepository(
        _FakeReportsApiClient(
          assistantResponse: {
            'intent': {'kind': 'chart_test', 'chart_type': chartType, 'reasoning': 'test'},
            'narrative': 'Reporte de prueba',
            'provider': 'test',
            'fallback_used': false,
            'data': data,
          },
        ),
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [reportsRepositoryProvider.overrideWithValue(chartRepository)],
          child: MaterialApp(
            home: ReportsScreen(voiceService: VoiceRecordingService(_FakeVoiceRecorder())),
          ),
        ),
      );
      await tester.pump();
      await tester.tap(find.byTooltip('Consultar reporte'));
      await tester.pumpAndSettle();
    }
    late ReportsRepository repository;

    setUp(() {
      fakeApi = _FakeReportsApiClient();
      repository = ReportsRepository(fakeApi);
    });

    testWidgets('CU16 chart visualizations expose data values and accessible marks', (tester) async {
      await pumpChart(tester, chartType: 'bar', data: [
        {'product_name': 'Blazer Noir', 'units_sold': 18},
        {'product_name': 'Camisa Seda', 'units_sold': 6},
      ]);
      expect(find.text('Blazer Noir'), findsOneWidget);
      expect(find.text('18'), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'Blazer Noir.*18')), findsOneWidget);

      await pumpChart(tester, chartType: 'line', data: [
        {'date': '2026-02-01', 'value': 10},
        {'date': '2026-01-01', 'value': 25},
      ]);
      expect(find.text('2026-01-01'), findsOneWidget);
      expect(find.text('25'), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'2026-02-01.*10')), findsOneWidget);

      await pumpChart(tester, chartType: 'pie', data: [
        {'category_name': 'Vestidos', 'total_revenue': 4500},
        {'category_name': 'Pantalones', 'total_revenue': 2200},
      ]);
      expect(find.textContaining('Vestidos'), findsOneWidget);
      expect(find.textContaining('67%'), findsOneWidget);

      await pumpChart(tester, chartType: 'kpi', data: [
        {'label': 'Ingresos', 'value': 6700},
        {'label': 'Pedidos', 'value': 42},
      ]);
      expect(find.text('Ingresos'), findsOneWidget);
      expect(find.text('6700'), findsOneWidget);

      await pumpChart(tester, chartType: 'table', data: [
        {'branch_name': 'Centro', 'sales_count': 12},
      ]);
      expect(find.byType(DataTable), findsOneWidget);
      expect(find.text('Centro'), findsOneWidget);
    });

    testWidgets('CU16 chart normalizes report-shaped values and orders temporal lines', (tester) async {
      await pumpChart(tester, chartType: 'bar', data: [
        {'status': 'Completado', 'count': 7},
        {'branch_name': 'Centro', 'total': 1250},
        {'product_name': 'Blazer Noir', 'revenue': 2400},
      ]);
      expect(find.text('Completado'), findsOneWidget);
      expect(find.text('7'), findsOneWidget);
      expect(find.text('Centro'), findsOneWidget);
      expect(find.text('1250'), findsOneWidget);
      expect(find.text('Blazer Noir'), findsOneWidget);
      expect(find.text('2400'), findsOneWidget);

      await pumpChart(tester, chartType: 'line', data: [
        {'date': '2026-03-01', 'value': 30},
        {'date': '2026-01-01', 'value': 10},
        {'date': '2026-02-01', 'value': 20},
      ]);
      final january = tester.getTopLeft(find.text('2026-01-01')).dy;
      final march = tester.getTopLeft(find.text('2026-03-01')).dy;
      expect(january, lessThan(march));
    });

    testWidgets('CU16 chart falls back to an accessible table for non-temporal line data', (tester) async {
      await pumpChart(tester, chartType: 'line', data: [
        {'label': 'First', 'value': 10},
        {'label': 'Second', 'value': 20},
      ]);
      expect(find.byType(DataTable), findsOneWidget);
      expect(find.text('First'), findsOneWidget);
      expect(find.textContaining('No hay datos gráficos válidos'), findsOneWidget);
    });

    testWidgets('CU16 chart falls back to an accessible table for malformed data', (tester) async {
      await pumpChart(tester, chartType: 'bar', data: [
        {'product_name': 'Sin valor', 'units_sold': 'not-a-number'},
      ]);
      expect(find.byType(DataTable), findsOneWidget);
      expect(find.text('Sin valor'), findsOneWidget);
      expect(find.textContaining('No hay datos gráficos válidos'), findsOneWidget);
    });

    testWidgets('CU16 chart remains readable at narrow width', (tester) async {
      await tester.binding.setSurfaceSize(const Size(375, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await pumpChart(tester, chartType: 'bar', data: [
        {'product_name': 'Producto de nombre largo', 'units_sold': 18},
        {'product_name': 'Otro producto', 'units_sold': 4},
      ]);
      expect(tester.takeException(), isNull);
    });

    testWidgets('renders Copilot header, quick prompts, dynamic charts, and ML forecast cards', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            reportsRepositoryProvider.overrideWithValue(repository),
          ],
          child: MaterialApp(
            home: ReportsScreen(
              voiceService: VoiceRecordingService(_FakeVoiceRecorder()),
            ),
          ),
        ),
      );

      // Pump to trigger post frame callback for ML loading
      await tester.pump();
      await tester.pumpAndSettle();

      // Header y Sofía IA Copilot
      expect(find.text('REPORTES & IA PREDICTIVA'), findsOneWidget);
      expect(find.text('Sofía IA Copilot'), findsOneWidget);

      // Chips de preguntas rápidas
      expect(find.text('¿Qué sucursal vendió más?'), findsOneWidget);
      expect(find.text('¿Cuáles son los productos más vendidos?'), findsOneWidget);
      expect(find.text('¿Qué categorías generaron mayores ingresos?'), findsOneWidget);

      // Sección de Machine Learning
      expect(find.text('Machine Learning Predictivo'), findsOneWidget);
      expect(find.text('Proyección de Demanda Semanal'), findsOneWidget);
      expect(find.text('MAE: 2.3'), findsOneWidget);
      expect(find.text('42 un.'), findsOneWidget);

      // Segmentación RFM
      expect(find.text('Segmentación de Clientes (K-Means RFM)'), findsOneWidget);
      expect(find.text('Silhouette: 0.44'), findsOneWidget);
      expect(find.text('Clientes VIP / Champions'), findsOneWidget);
      expect(find.text('Clientes Leales'), findsOneWidget);
      expect(find.textContaining('Beneficios exclusivos', skipOffstage: false), findsWidgets);

      // Voice input requires review and explicit upload before transcription.
      final micButton = find.byIcon(Icons.mic);
      expect(micButton, findsOneWidget);
      await tester.tap(find.byTooltip('Dictar consulta por voz'));
      await tester.pump();
      expect(find.textContaining('grabación se enviará al backend', skipOffstage: false), findsOneWidget);
      expect(find.text('REVENUE_BY_CATEGORY'), findsNothing);
    });

    testWidgets('describes a plan upgrade only for FEATURE_NOT_IN_PLAN', (tester) async {
      final featureLimitedRepository = ReportsRepository(
        _FakeReportsApiClient(
          assistantError: const ApiException(
            'Feature blocked',
            403,
            code: 'FEATURE_NOT_IN_PLAN',
          ),
        ),
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [reportsRepositoryProvider.overrideWithValue(featureLimitedRepository)],
          child: const MaterialApp(home: ReportsScreen()),
        ),
      );
      await tester.pump();
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      expect(find.textContaining('Plan Profesional'), findsOneWidget);
      expect(find.text('Feature blocked'), findsNothing);
    });

    testWidgets('keeps unrelated 403 errors out of the plan upgrade alert', (tester) async {
      final unrelatedRepository = ReportsRepository(
        _FakeReportsApiClient(
          assistantError: const ApiException('Permission denied', 403, code: 'FORBIDDEN'),
        ),
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [reportsRepositoryProvider.overrideWithValue(unrelatedRepository)],
          child: const MaterialApp(home: ReportsScreen()),
        ),
      );
      await tester.pump();
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      expect(find.text('Permission denied'), findsOneWidget);
      expect(find.textContaining('Plan Profesional'), findsNothing);
    });

    testWidgets('triggers ML re-training when Reentrenar button is tapped', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            reportsRepositoryProvider.overrideWithValue(repository),
          ],
          child: const MaterialApp(
            home: ReportsScreen(),
          ),
        ),
      );

      await tester.pump();
      await tester.pumpAndSettle();

      final reentrenarBtn = find.text('Reentrenar');
      expect(reentrenarBtn, findsOneWidget);

      await tester.tap(reentrenarBtn);
      await tester.pumpAndSettle();

      // Confirmar mensaje de éxito en SnackBar
      expect(find.text('Modelos de Machine Learning reentrenados exitosamente.'), findsOneWidget);
    });
  });
}
