import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fashionstore_mobile/core/offline/connectivity_monitor.dart';

class FakeConnectivitySource implements ConnectivitySource {
  FakeConnectivitySource(this.initial);

  final List<ConnectivityResult> initial;
  final controller = StreamController<List<ConnectivityResult>>.broadcast();

  @override
  Future<List<ConnectivityResult>> checkConnectivity() async => initial;

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged =>
      controller.stream;

  Future<void> emit(List<ConnectivityResult> results) async {
    controller.add(results);
    await Future<void>.delayed(Duration.zero);
  }

  Future<void> dispose() => controller.close();
}

void main() {
  late FakeConnectivitySource source;
  late ConnectivityMonitor monitor;

  setUp(() {
    source = FakeConnectivitySource(const [ConnectivityResult.wifi]);
    monitor = ConnectivityMonitor(source);
  });

  tearDown(() async {
    monitor.dispose();
    await source.dispose();
  });

  test('uses the initial connectivity state and treats any transport as online', () async {
    await monitor.start();

    expect(monitor.status, ConnectivityStatus.online);
  });

  test('reacts to offline and multi-transport transitions', () async {
    await monitor.start();
    expect(monitor.status, ConnectivityStatus.online);

    await source.emit(const [ConnectivityResult.none]);
    expect(monitor.status, ConnectivityStatus.offline);

    await source.emit(const [
      ConnectivityResult.wifi,
      ConnectivityResult.vpn,
      ConnectivityResult.mobile,
    ]);
    expect(monitor.status, ConnectivityStatus.online);
  });

  test('stops listening after disposal', () async {
    await monitor.start();
    monitor.dispose();

    await source.emit(const [ConnectivityResult.none]);

    expect(monitor.status, ConnectivityStatus.online);
  });
}
