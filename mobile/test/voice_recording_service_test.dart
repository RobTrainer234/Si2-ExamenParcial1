import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:fashionstore_mobile/features/reports/data/voice_recording_service.dart';

class _FakeRecorder implements VoiceRecorderBackend {
  _FakeRecorder({this.permission = true, this.path});

  bool permission;
  String? path;
  bool started = false;
  bool cancelled = false;
  bool disposed = false;

  @override
  Future<bool> requestPermission() async => permission;

  @override
  Future<void> start() async => started = true;

  @override
  Future<String?> stop() async => path;

  @override
  Future<void> cancel() async => cancelled = true;

  @override
  Future<void> dispose() async => disposed = true;
}

void main() {
  test('denied permission prevents recording', () async {
    final recorder = _FakeRecorder(permission: false);
    final service = VoiceRecordingService(recorder);

    await expectLater(
      service.start(),
      throwsA(isA<VoiceRecordingException>()),
    );
    expect(recorder.started, isFalse);
  });

  test('stops to a reviewable audio payload without uploading', () async {
    final file = File('${Directory.systemTemp.path}/voice-test.m4a');
    await file.writeAsBytes(List<int>.filled(12, 7));
    final recorder = _FakeRecorder(path: file.path);
    final service = VoiceRecordingService(recorder);

    await service.start();
    final recording = await service.stopForReview();

    expect(recording.mimeType, 'audio/mp4');
    expect(base64Decode(recording.base64Audio), List<int>.filled(12, 7));
    expect(recorder.cancelled, isFalse);
    if (await file.exists()) await file.delete();
  });

  test('rejects decoded audio larger than two MiB', () async {
    final file = File('${Directory.systemTemp.path}/voice-large.m4a');
    await file.writeAsBytes(List<int>.filled(2 * 1024 * 1024 + 1, 1));
    final recorder = _FakeRecorder(path: file.path);
    final service = VoiceRecordingService(recorder);

    await service.start();
    await expectLater(
      service.stopForReview(),
      throwsA(isA<VoiceRecordingException>()),
    );
    expect(recorder.cancelled, isTrue);
    if (await file.exists()) await file.delete();
  });

  test('discard cancels and disposal releases recorder', () async {
    final recorder = _FakeRecorder();
    final service = VoiceRecordingService(recorder);

    await service.start();
    await service.discard();
    await service.dispose();

    expect(recorder.cancelled, isTrue);
    expect(recorder.disposed, isTrue);
  });
}
