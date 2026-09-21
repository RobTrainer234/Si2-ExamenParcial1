import 'package:flutter/material.dart';

class NotificationService {
  NotificationService({GlobalKey<ScaffoldMessengerState>? messengerKey})
    : messengerKey = messengerKey ?? GlobalKey<ScaffoldMessengerState>();

  final GlobalKey<ScaffoldMessengerState> messengerKey;

  void showSuccess(String message) {
    _show(message, backgroundColor: const Color(0xff2e6f40));
  }

  void showError(String message) {
    _show(message, backgroundColor: const Color(0xffa53d32));
  }

  void _show(String message, {required Color backgroundColor}) {
    ScaffoldMessengerState? messenger;
    try {
      messenger = messengerKey.currentState;
    } on FlutterError {
      return;
    }
    if (messenger == null) return;
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: backgroundColor,
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 4),
        ),
      );
  }
}
