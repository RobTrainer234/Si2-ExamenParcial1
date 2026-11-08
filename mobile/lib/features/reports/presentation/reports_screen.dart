import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../data/reports_models.dart';
import '../data/voice_recording_service.dart';

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key, this.voiceService});

  final VoiceRecordingService? voiceService;

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  final _promptController = TextEditingController(
    text: '¿Cuáles fueron los diez productos más vendidos este mes?',
  );
  late final VoiceRecordingService _voiceService;
  VoiceRecording? _pendingVoiceRecording;
  bool _isRecording = false;
  bool _isTranscribing = false;
  String? _voiceError;
  Timer? _voiceLimitTimer;

  bool _isAssistantLoading = false;
  String? _assistantError;
  ReportAssistantResponse? _assistantResult;

  bool _isLoadingML = false;
  bool _isTrainingML = false;
  String? _mlError;
  DemandForecastResponse? _demandForecast;
  CustomerSegmentationResponse? _customerSegments;

  final _quickPrompts = const [
    '¿Qué sucursal vendió más?',
    '¿Cuáles son los productos más vendidos?',
    '¿Qué productos tienen bajo stock?',
    '¿Qué categorías generaron mayores ingresos?',
  ];

  @override
  void initState() {
    super.initState();
    _voiceService = widget.voiceService ?? VoiceRecordingService.production();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadMLAnalytics();
    });
  }

  @override
  void dispose() {
    _voiceLimitTimer?.cancel();
    _voiceService.dispose();
    _promptController.dispose();
    super.dispose();
  }

  Future<void> _askAssistant([String? promptOverride]) async {
    final prompt = (promptOverride ?? _promptController.text).trim();
    if (prompt.isEmpty) return;

    setState(() {
      _isAssistantLoading = true;
      _assistantError = null;
    });

    try {
      final repo = ref.read(reportsRepositoryProvider);
      final result = await repo.askAssistant(prompt);
      if (!mounted) return;
      setState(() {
        _assistantResult = result;
        _isAssistantLoading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _isAssistantLoading = false;
        if (e.code == 'FEATURE_NOT_IN_PLAN') {
          _assistantError =
              'Los reportes generativos con IA no están incluidos en su plan de suscripción actual (Plan Básico). Actualice al Plan Profesional para desbloquear esta funcionalidad.';
        } else {
          _assistantError = e.message;
        }
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isAssistantLoading = false;
        _assistantError =
            'No se pudo conectar con Sofía IA. Intenta nuevamente.';
      });
    }
  }

  Future<void> _loadMLAnalytics() async {
    setState(() {
      _isLoadingML = true;
      _mlError = null;
    });

    try {
      final repo = ref.read(reportsRepositoryProvider);
      final forecast = await repo.getDemandForecast();
      final segments = await repo.getCustomerSegments();

      if (!mounted) return;
      setState(() {
        _demandForecast = forecast;
        _customerSegments = segments;
        _isLoadingML = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoadingML = false;
        if (e.code == 'FEATURE_NOT_IN_PLAN') {
          _mlError =
              'Modelos de Machine Learning no habilitados en el Plan Básico.';
        } else {
          _mlError = e.message;
        }
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isLoadingML = false;
        _mlError = 'Error al cargar analítica de Machine Learning.';
      });
    }
  }

  Future<void> _trainML() async {
    setState(() => _isTrainingML = true);
    try {
      final repo = ref.read(reportsRepositoryProvider);
      final res = await repo.trainMLModels();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res.message),
          backgroundColor: const Color(0xFF0F766E),
        ),
      );
      await _loadMLAnalytics();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Error al reentrenar modelos ML.'),
          backgroundColor: Colors.redAccent,
        ),
      );
    } finally {
      if (mounted) setState(() => _isTrainingML = false);
    }
  }

  Future<void> _toggleVoiceRecording() async {
    if (_isRecording) {
      await _stopVoiceRecording();
      return;
    }
    setState(() => _voiceError = null);
    try {
      await _voiceService.start();
      if (!mounted) return;
      _voiceLimitTimer?.cancel();
      _voiceLimitTimer = Timer(const Duration(seconds: 30), _stopVoiceRecording);
      setState(() => _isRecording = true);
    } on VoiceRecordingException catch (e) {
      if (mounted) setState(() => _voiceError = e.message);
    } catch (_) {
      if (mounted) setState(() => _voiceError = 'No se pudo iniciar la grabación.');
    }
  }

  Future<void> _stopVoiceRecording() async {
    _voiceLimitTimer?.cancel();
    _voiceLimitTimer = null;
    if (!mounted) return;
    setState(() => _isRecording = false);
    try {
      final recording = await _voiceService.stopForReview();
      if (!mounted) return;
      setState(() {
        _pendingVoiceRecording = recording;
        _voiceError = null;
      });
    } on VoiceRecordingException catch (e) {
      if (mounted) setState(() => _voiceError = e.message);
    } catch (_) {
      if (mounted) setState(() => _voiceError = 'No se pudo finalizar la grabación.');
    }
  }

  Future<void> _transcribeVoice() async {
    final recording = _pendingVoiceRecording;
    if (recording == null || _isTranscribing) return;
    setState(() {
      _isTranscribing = true;
      _voiceError = null;
    });
    try {
      final transcript = await ref.read(reportsRepositoryProvider).transcribeAudio(
            recording.base64Audio,
            mimeType: recording.mimeType,
          );
      if (!mounted) return;
      if (transcript.trim().isEmpty) {
        setState(() {
          _isTranscribing = false;
          _voiceError = 'El servicio no devolvió una transcripción.';
        });
        return;
      }
      setState(() {
        _promptController.text = transcript;
        _pendingVoiceRecording = null;
        _isTranscribing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Texto transcrito. Revisá la consulta antes de enviarla.')),
      );
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _isTranscribing = false;
          _voiceError = e.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isTranscribing = false;
          _voiceError = 'No se pudo transcribir el audio. Intentá nuevamente.';
        });
      }
    }
  }

  Future<void> _discardVoiceRecording() async {
    await _voiceService.discard();
    if (!mounted) return;
    setState(() {
      _pendingVoiceRecording = null;
      _voiceError = null;
      _isRecording = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('REPORTES & IA PREDICTIVA'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar analítica',
            onPressed: () {
              _loadMLAnalytics();
              if (_promptController.text.trim().isNotEmpty) {
                _askAssistant();
              }
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildCopilotHeader(),
            const SizedBox(height: AppSpacing.sm),
            _buildQuickPrompts(),
            const SizedBox(height: AppSpacing.sm),
            _buildPromptInput(),
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text(
                'La grabación se enviará al backend y puede procesarse con Google Gemini cuando esté configurado.',
                style: TextStyle(fontSize: 11, color: Colors.black54),
              ),
            ),
            if (_isRecording || _pendingVoiceRecording != null || _voiceError != null)
              _buildVoiceReviewPanel(),
            const SizedBox(height: AppSpacing.md),
            if (_isAssistantLoading)
              const Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 24.0),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (_assistantError != null)
              _buildAlertBox(_assistantError!, isError: true)
            else if (_assistantResult != null)
              _buildAssistantCard(_assistantResult!),
            const SizedBox(height: AppSpacing.lg),
            const Divider(),
            const SizedBox(height: AppSpacing.md),
            _buildMLSectionHeader(),
            const SizedBox(height: AppSpacing.sm),
            if (_isLoadingML)
              const Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 24.0),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (_mlError != null)
              _buildAlertBox(_mlError!, isError: true)
            else ...[
              if (_demandForecast != null) _buildDemandForecastCard(_demandForecast!),
              const SizedBox(height: AppSpacing.md),
              if (_customerSegments != null) _buildCustomerSegmentsCard(_customerSegments!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildCopilotHeader() {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: const Color(0xFF1B1C1A),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFB8924A).withAlpha(50),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.auto_awesome,
              color: Color(0xFFD4AF37),
              size: 28,
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Sofía IA Copilot',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Consultas en lenguaje natural, dictado por voz y analítica en tiempo real.',
                  style: TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickPrompts() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: _quickPrompts.map((p) {
          return Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: ActionChip(
              label: Text(p, style: const TextStyle(fontSize: 12)),
              avatar: const Icon(Icons.chat_bubble_outline, size: 14),
              onPressed: () {
                _promptController.text = p;
                _askAssistant(p);
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildPromptInput() {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: _promptController,
            decoration: InputDecoration(
              hintText: 'Preguntale a Sofía IA sobre tus ventas...',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            ),
            onSubmitted: (v) => _askAssistant(v),
          ),
        ),
        const SizedBox(width: 8),
        Semantics(
          button: true,
          label: _isRecording ? 'Detener grabación' : 'Grabar consulta por voz',
          child: IconButton.filledTonal(
            icon: Icon(_isRecording ? Icons.stop : Icons.mic),
            tooltip: _isRecording ? 'Detener grabación' : 'Dictar consulta por voz',
            onPressed: _toggleVoiceRecording,
          ),
        ),
        const SizedBox(width: 4),
        IconButton.filled(
          icon: const Icon(Icons.send),
          tooltip: 'Consultar reporte',
          onPressed: () => _askAssistant(),
        ),
      ],
    );
  }

  Widget _buildVoiceReviewPanel() {
    final hasRecording = _pendingVoiceRecording != null;
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: AppSpacing.sm),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBEB),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFD97706)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_isRecording) ...[
            const Row(
              children: [
                Icon(Icons.fiber_manual_record, color: Colors.red, size: 18),
                SizedBox(width: 8),
                Text('Grabando… máximo 30 segundos'),
              ],
            ),
            const SizedBox(height: 8),
            const Text('Presioná detener para revisar el audio. No se enviará automáticamente.'),
          ] else if (hasRecording) ...[
            const Text(
              'La grabación se enviará al backend de FashionStore para transcribirla. Puede procesarse con Google Gemini cuando esté configurado.',
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            const Text('Revisá esta consulta antes de presionar enviar.'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: _isTranscribing ? null : _transcribeVoice,
                  icon: _isTranscribing
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.cloud_upload_outlined),
                  label: Text(_isTranscribing ? 'Transcribiendo…' : 'Enviar para transcribir'),
                ),
                OutlinedButton.icon(
                  onPressed: _isTranscribing ? null : _discardVoiceRecording,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('Descartar'),
                ),
              ],
            ),
          ],
          if (_voiceError != null) ...[
            if (_isRecording || hasRecording) const SizedBox(height: 8),
            Text(_voiceError!, style: const TextStyle(color: Color(0xFFB91C1C))),
          ],
        ],
      ),
    );
  }

  Widget _buildAlertBox(String message, {bool isError = false}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: isError ? const Color(0xFFFEE2E2) : const Color(0xFFD1FAE5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isError ? const Color(0xFFEF4444) : const Color(0xFF10B981),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isError ? Icons.error_outline : Icons.check_circle_outline,
            color: isError ? const Color(0xFFB91C1C) : const Color(0xFF047857),
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: isError ? const Color(0xFF991B1B) : const Color(0xFF065F46),
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAssistantCard(ReportAssistantResponse result) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                Chip(
                  label: Text(
                    result.intent.kind.toUpperCase(),
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                  backgroundColor: const Color(0xFFF3F4F6),
                ),
                Chip(
                  label: Text(
                    'GRÁFICO: ${result.intent.chartType.toUpperCase()}',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                  backgroundColor: const Color(0xFFE0E7FF),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              result.narrative,
              style: const TextStyle(fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: AppSpacing.md),
            _buildDynamicChart(result),
          ],
        ),
      ),
    );
  }

  Widget _buildDynamicChart(ReportAssistantResponse result) {
    final chartType = result.intent.chartType.toLowerCase();
    final rows = _chartRows(result.data);
    if (rows.isEmpty || (chartType == 'line' && rows.any((row) => row.timestamp == null))) {
      return _buildChartFallback(result.data);
    }

    switch (chartType) {
      case 'bar':
        return _buildBarChart(rows);
      case 'line':
        return _buildLineChart(rows);
      case 'pie':
        return _buildPieChart(rows);
      case 'table':
        return _buildDataTable(rows);
      case 'kpi':
        return _buildKpiCards(rows);
      default:
        return _buildChartFallback(result.data);
    }
  }

  List<_ChartRow> _chartRows(dynamic rawData) {
    if (rawData is! List) return const [];
    return rawData.whereType<Map>().map((item) {
      final map = Map<String, dynamic>.from(item);
      final label = map['label'] ?? map['name'] ?? map['product_name'] ??
          map['category_name'] ?? map['branch_name'] ?? map['status'] ?? map['period'] ?? map['date'];
      final rawValue = map['value'] ?? map['total_revenue'] ?? map['revenue'] ??
          map['total'] ?? map['count'] ?? map['units_sold'] ?? map['sales_count'] ??
          map['available_quantity'] ?? map['predicted_units'];
      final value = rawValue is num ? rawValue.toDouble() : double.tryParse('$rawValue');
      if (label == null || value == null || !value.isFinite) return null;
      final timestamp = DateTime.tryParse('${map['date'] ?? map['period'] ?? map['week_start'] ?? map['month'] ?? ''}');
      return _ChartRow(label.toString(), value, map, timestamp);
    }).whereType<_ChartRow>().toList(growable: false);
  }

  Widget _chartHeading(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
      );

  Widget _buildBarChart(List<_ChartRow> rows) {
    final sorted = [...rows]..sort((a, b) => b.value.compareTo(a.value));
    final maxValue = sorted.map((r) => r.value).reduce((a, b) => a > b ? a : b);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _chartHeading('Rendimiento por categoría'),
        ...sorted.take(8).map((row) {
          final fraction = maxValue <= 0 ? 0.0 : row.value / maxValue;
          return Semantics(
            label: '${row.label}: ${_formatNumber(row.value)}',
            button: true,
            child: Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: InkWell(
                onTap: () => _showChartDetail(row),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Expanded(child: Text(row.label, maxLines: 2, overflow: TextOverflow.ellipsis)),
                      const SizedBox(width: 8),
                      Text(_formatNumber(row.value), style: const TextStyle(fontWeight: FontWeight.bold)),
                    ]),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: FractionallySizedBox(
                        widthFactor: fraction.clamp(0.0, 1.0),
                        child: Container(height: 10, color: const Color(0xFF1B1C1A)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildLineChart(List<_ChartRow> rows) {
    final chronologicalRows = [...rows]..sort((a, b) => a.timestamp!.compareTo(b.timestamp!));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _chartHeading('Tendencia temporal'),
        SizedBox(
          height: 160,
          width: double.infinity,
          child: CustomPaint(painter: _LineChartPainter(chronologicalRows)),
        ),
        const SizedBox(height: 8),
        ...chronologicalRows.map((row) => Semantics(
              label: '${row.label}: ${_formatNumber(row.value)}',
              button: true,
              child: InkWell(
                onTap: () => _showChartDetail(row),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(children: [
                    Expanded(child: Text(row.label, overflow: TextOverflow.ellipsis)),
                    Text(_formatNumber(row.value), style: const TextStyle(fontWeight: FontWeight.bold)),
                  ]),
                ),
              ),
            )),
      ],
    );
  }

  Widget _buildPieChart(List<_ChartRow> rows) {
    final total = rows.fold<double>(0, (sum, row) => sum + row.value);
    if (total <= 0) return _buildChartFallback(rows.map((r) => r.raw).toList());
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _chartHeading('Distribución de ingresos'),
        Row(children: [
          SizedBox(width: 130, height: 130, child: CustomPaint(painter: _PieChartPainter(rows, total))),
          const SizedBox(width: 12),
          Expanded(child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: rows.take(8).map((row) {
              final percent = row.value / total * 100;
              return Semantics(
                label: '${row.label}: ${_formatNumber(row.value)}, ${percent.round()} por ciento',
                button: true,
                child: InkWell(
                  onTap: () => _showChartDetail(row),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Text('${row.label}: ${percent.round()}% (${_formatNumber(row.value)})'),
                  ),
                ),
              );
            }).toList(),
          )),
        ]),
      ],
    );
  }

  Widget _buildKpiCards(List<_ChartRow> rows) => Wrap(
        spacing: 8,
        runSpacing: 8,
        children: rows.take(6).map((row) => Semantics(
              label: '${row.label}: ${_formatNumber(row.value)}',
              child: Card(
                margin: EdgeInsets.zero,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(row.label, style: const TextStyle(fontSize: 12)),
                    const SizedBox(height: 4),
                    Text(_formatNumber(row.value), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  ]),
                ),
              ),
            )).toList(),
      );

  Widget _buildDataTable(List<_ChartRow> rows) => SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columns: const [DataColumn(label: Text('Nombre')), DataColumn(label: Text('Valor'))],
          rows: rows.map((row) => DataRow(cells: [
            DataCell(Text(row.label)),
            DataCell(Text(_formatNumber(row.value))),
          ])).toList(),
        ),
      );

  Widget _buildChartFallback(dynamic rawData) {
    final rows = rawData is List ? rawData.whereType<Map>().toList() : const <Map>[];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('No hay datos gráficos válidos; se muestra una tabla accesible.', style: TextStyle(fontWeight: FontWeight.w500)),
        const SizedBox(height: 8),
        if (rows.isEmpty) const Text('No hay filas para mostrar.')
        else SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columns: const [DataColumn(label: Text('Campo')), DataColumn(label: Text('Valor'))],
            rows: rows.expand((map) => map.entries.map((entry) => DataRow(cells: [
              DataCell(Text(entry.key)), DataCell(Text('${entry.value}')),
            ]))).toList(),
          ),
        ),
      ],
    );
  }

  void _showChartDetail(_ChartRow row) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${row.label}: ${_formatNumber(row.value)}')));
  }

  String _formatNumber(double value) => value == value.roundToDouble() ? value.toInt().toString() : value.toStringAsFixed(1);

  Widget _buildMLSectionHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Machine Learning Predictivo',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Text(
                'Modelos supervisados (Ridge) y no supervisados (RFM)',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
        FilledButton.icon(
          icon: _isTrainingML
              ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Icon(Icons.model_training, size: 16),
          label: Text(_isTrainingML ? 'Entrenando…' : 'Reentrenar'),
          onPressed: _isTrainingML ? null : _trainML,
        ),
      ],
    );
  }

  Widget _buildDemandForecastCard(DemandForecastResponse forecast) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Expanded(
                  child: Text(
                    'Proyección de Demanda Semanal',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                ),
                if (forecast.metrics.mae != null)
                  Chip(
                    label: Text(
                      'MAE: ${forecast.metrics.mae}',
                      style: const TextStyle(fontSize: 11),
                    ),
                    backgroundColor: const Color(0xFFEFF6FF),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              forecast.narrative,
              style: const TextStyle(fontSize: 13, color: Colors.black87),
            ),
            const SizedBox(height: AppSpacing.md),
            ...forecast.forecast.map((pt) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4.0),
                child: Row(
                  children: [
                    SizedBox(
                      width: 75,
                      child: Text(
                        pt.weekStart.split('T').first,
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ),
                    Expanded(
                      child: LinearProgressIndicator(
                        value: (pt.predictedUnits / 60.0).clamp(0.1, 1.0),
                        backgroundColor: Colors.grey.shade200,
                        color: const Color(0xFF0F766E),
                        minHeight: 8,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      '${pt.predictedUnits} un.',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildCustomerSegmentsCard(CustomerSegmentationResponse segments) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Expanded(
                  child: Text(
                    'Segmentación de Clientes (K-Means RFM)',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                ),
                Chip(
                  label: Text(
                    'Silhouette: ${segments.silhouetteScore}',
                    style: const TextStyle(fontSize: 11),
                  ),
                  backgroundColor: const Color(0xFFFDF2F8),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              segments.narrative,
              style: const TextStyle(fontSize: 13, color: Colors.black87),
            ),
            const SizedBox(height: AppSpacing.md),
            ...segments.segments.map((seg) {
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFF9FAFB),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      alignment: WrapAlignment.spaceBetween,
                      children: [
                        Text(
                          seg.name,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        Text(
                          '${seg.percentage}% (${seg.customerCount} clientes)',
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'R: ${seg.avgRecencyDays.toStringAsFixed(0)}d · F: ${seg.avgFrequency.toStringAsFixed(1)} · M: Bs ${seg.avgMonetary.toStringAsFixed(0)}',
                      style: const TextStyle(fontSize: 12, color: Colors.black87),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Acción: ${seg.suggestedAction}',
                      style: const TextStyle(fontSize: 11, color: Color(0xFF0F766E), fontStyle: FontStyle.italic),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _ChartRow {
  const _ChartRow(this.label, this.value, this.raw, [this.timestamp]);

  final String label;
  final double value;
  final Map<String, dynamic> raw;
  final DateTime? timestamp;
}

class _LineChartPainter extends CustomPainter {
  const _LineChartPainter(this.rows);

  final List<_ChartRow> rows;

  @override
  void paint(Canvas canvas, Size size) {
    if (rows.isEmpty) return;
    final values = rows.map((row) => row.value).toList();
    final minValue = values.reduce((a, b) => a < b ? a : b);
    final maxValue = values.reduce((a, b) => a > b ? a : b);
    final range = (maxValue - minValue) == 0 ? 1 : maxValue - minValue;
    final paint = Paint()..color = const Color(0xFF0F766E)..strokeWidth = 3..style = PaintingStyle.stroke;
    final pointPaint = Paint()..color = const Color(0xFF0F766E);
    final path = Path();
    for (var index = 0; index < values.length; index++) {
      final x = values.length == 1 ? size.width / 2 : index * size.width / (values.length - 1);
      final y = size.height - ((values[index] - minValue) / range * (size.height - 20)) - 10;
      if (index == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
      canvas.drawCircle(Offset(x, y), 5, pointPaint);
    }
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter oldDelegate) => oldDelegate.rows != rows;
}

class _PieChartPainter extends CustomPainter {
  const _PieChartPainter(this.rows, this.total);

  final List<_ChartRow> rows;
  final double total;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    var start = -3.14159265359 / 2;
    final colors = [
      const Color(0xFF1B1C1A), const Color(0xFF0F766E), const Color(0xFFB8924A),
      const Color(0xFF7C3AED), const Color(0xFFDC2626), const Color(0xFF2563EB),
    ];
    for (var index = 0; index < rows.length; index++) {
      final sweep = rows[index].value / total * 2 * 3.14159265359;
      final paint = Paint()..color = colors[index % colors.length];
      canvas.drawArc(rect, start, sweep, true, paint);
      start += sweep;
    }
    final hole = Paint()..color = Colors.white;
    canvas.drawCircle(size.center(Offset.zero), size.shortestSide * .23, hole);
  }

  @override
  bool shouldRepaint(covariant _PieChartPainter oldDelegate) => oldDelegate.rows != rows || oldDelegate.total != total;
}
