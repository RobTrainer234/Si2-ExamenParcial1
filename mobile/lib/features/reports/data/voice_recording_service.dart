import 'dart:convert';
import 'dart:io';

import 'package:record/record.dart';

const voiceAudioMimeType = 'audio/mp4';
const maxVoiceAudioBytes = 2 * 1024 * 1024;

class VoiceRecordingException implements Exception {
  const VoiceRecordingException(this.message);

  final String message;

  @override
  String toString() => message;
}

class VoiceRecording {
  const VoiceRecording({required this.base64Audio, required this.mimeType});

  final String base64Audio;
  final String mimeType;
}

abstract interface class VoiceRecorderBackend {
  Future<bool> requestPermission();
  Future<void> start();
  Future<String?> stop();
  Future<void> cancel();
  Future<void> dispose();
}

class AudioRecorderBackend implements VoiceRecorderBackend {
  AudioRecorderBackend() : _recorder = AudioRecorder();

  final AudioRecorder _recorder;
  String? _path;

  @override
  Future<bool> requestPermission() => _recorder.hasPermission();

  @override
  Future<void> start() async {
    _path = '${Directory.systemTemp.path}${Platform.pathSeparator}'
        'fashionstore_voice_${DateTime.now().microsecondsSinceEpoch}.m4a';
    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        sampleRate: 16000,
        numChannels: 1,
        bitRate: 64000,
      ),
      path: _path!,
    );
  }

  @override
  Future<String?> stop() => _recorder.stop();

  @override
  Future<void> cancel() => _recorder.cancel();

  @override
  Future<void> dispose() => _recorder.dispose();
}

class VoiceRecordingService {
  VoiceRecordingService(this._recorder);

  factory VoiceRecordingService.production() =>
      VoiceRecordingService(AudioRecorderBackend());

  final VoiceRecorderBackend _recorder;
  bool _recording = false;

  Future<void> start() async {
    if (_recording) return;
    final permitted = await _recorder.requestPermission();
    if (!permitted) {
      throw const VoiceRecordingException(
        'No se concedió permiso para usar el micrófono.',
      );
    }
    try {
      await _recorder.start();
      _recording = true;
    } catch (_) {
      throw const VoiceRecordingException('No se pudo iniciar la grabación.');
    }
  }

  Future<VoiceRecording> stopForReview() async {
    if (!_recording) {
      throw const VoiceRecordingException('No hay una grabación activa.');
    }
    _recording = false;
    String? path;
    try {
      path = await _recorder.stop();
      if (path == null || path.isEmpty) {
        throw const VoiceRecordingException('La grabación está vacía.');
      }
      final file = File(path);
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty) {
        throw const VoiceRecordingException('La grabación está vacía.');
      }
      if (bytes.length > maxVoiceAudioBytes) {
        throw const VoiceRecordingException(
          'La grabación supera el límite de 2 MiB.',
        );
      }
      return VoiceRecording(
        base64Audio: base64Encode(bytes),
        mimeType: voiceAudioMimeType,
      );
    } on VoiceRecordingException {
      await _recorder.cancel();
      rethrow;
    } catch (_) {
      await _recorder.cancel();
      throw const VoiceRecordingException('No se pudo guardar la grabación.');
    } finally {
      if (path != null) {
        try {
          await File(path).delete();
        } catch (_) {}
      }
    }
  }

  Future<void> discard() async {
    _recording = false;
    await _recorder.cancel();
  }

  Future<void> dispose() => _recorder.dispose();
}
