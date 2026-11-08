import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

enum ConnectivityStatus { unknown, offline, online }

abstract interface class ConnectivitySource {
  Future<List<ConnectivityResult>> checkConnectivity();

  Stream<List<ConnectivityResult>> get onConnectivityChanged;
}

class ConnectivityPlusSource implements ConnectivitySource {
  ConnectivityPlusSource([Connectivity? connectivity])
      : _connectivity = connectivity ?? Connectivity();

  final Connectivity _connectivity;

  @override
  Future<List<ConnectivityResult>> checkConnectivity() =>
      _connectivity.checkConnectivity();

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged =>
      _connectivity.onConnectivityChanged;
}

class ConnectivityMonitor extends ChangeNotifier {
  ConnectivityMonitor(this._source);

  final ConnectivitySource _source;
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  ConnectivityStatus _status = ConnectivityStatus.unknown;
  bool _started = false;
  bool _receivedStreamValue = false;
  bool _disposed = false;

  ConnectivityStatus get status => _status;

  Future<void> start() async {
    if (_started) return;
    _started = true;
    _subscription = _source.onConnectivityChanged.listen((results) {
      _receivedStreamValue = true;
      _setStatus(_statusFor(results));
    });

    final initialResults = await _source.checkConnectivity();
    if (!_receivedStreamValue) {
      _setStatus(_statusFor(initialResults));
    }
  }

  ConnectivityStatus _statusFor(List<ConnectivityResult> results) {
    return results.any((result) => result != ConnectivityResult.none)
        ? ConnectivityStatus.online
        : ConnectivityStatus.offline;
  }

  void _setStatus(ConnectivityStatus nextStatus) {
    if (_status == nextStatus) return;
    _status = nextStatus;
    notifyListeners();
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _subscription?.cancel();
    _subscription = null;
    super.dispose();
  }
}
