import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

class PoseDetectorService {
  PoseDetectorService()
    : _detector = PoseDetector(
        options: PoseDetectorOptions(mode: PoseDetectionMode.stream),
      );

  final PoseDetector _detector;
  bool _busy = false;

  Future<Pose?> detect(CameraImage image, CameraDescription camera) async {
    if (_busy) return null;
    _busy = true;
    try {
      final bytes = WriteBuffer();
      for (final plane in image.planes) {
        bytes.putUint8List(plane.bytes);
      }
      final rotation =
          InputImageRotationValue.fromRawValue(camera.sensorOrientation) ??
          InputImageRotation.rotation0deg;
      final format =
          InputImageFormatValue.fromRawValue(image.format.raw) ??
          InputImageFormat.nv21;
      final input = InputImage.fromBytes(
        bytes: bytes.done().buffer.asUint8List(),
        metadata: InputImageMetadata(
          size: Size(image.width.toDouble(), image.height.toDouble()),
          rotation: rotation,
          format: format,
          bytesPerRow: image.planes.first.bytesPerRow,
        ),
      );
      final poses = await _detector.processImage(input);
      return poses.isEmpty ? null : poses.first;
    } finally {
      _busy = false;
    }
  }

  Future<void> dispose() => _detector.close();
}
