import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/providers.dart';
import 'package:fashionstore_mobile/features/reservations/data/reservation_models.dart';
import 'package:fashionstore_mobile/features/reservations/data/reservation_repository.dart';
import 'package:fashionstore_mobile/features/reservations/presentation/reservations_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('muestra acción de reintento cuando falla la carga', (
    tester,
  ) async {
    final repository = _FakeReservationRepository(
      loads: [Exception('network'), <Reservation>[]],
    );

    await tester.pumpWidget(_app(repository));
    await tester.pumpAndSettle();

    expect(find.text('Reservas no disponibles'), findsOneWidget);
    expect(find.text('Reintentar'), findsOneWidget);

    await tester.tap(find.text('Reintentar'));
    await tester.pumpAndSettle();

    expect(find.text('Todavía no tenés reservas'), findsOneWidget);
    expect(repository.mineCalls, 2);
  });

  testWidgets('pide confirmación antes de cancelar una reserva', (
    tester,
  ) async {
    final repository = _FakeReservationRepository(
      loads: [
        [_reservation(status: 'PENDING')],
      ],
      cancellation: _reservation(status: 'CANCELLED'),
    );

    await tester.pumpWidget(_app(repository));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Reserva #1'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cancelar reserva'));
    await tester.pumpAndSettle();

    expect(
      find.text(
        '¿Querés cancelar esta reserva? Esta acción no se puede deshacer.',
      ),
      findsOneWidget,
    );
    expect(repository.cancelCalls, 0);

    await tester.tap(find.text('Sí, cancelar'));
    await tester.pumpAndSettle();

    expect(repository.cancelCalls, 1);
    expect(find.text('CANCELADA'), findsOneWidget);
  });

  testWidgets('refresca la lista al volver desde el detalle', (tester) async {
    final repository = _FakeReservationRepository(
      loads: [
        [_reservation(status: 'PENDING')],
        [_reservation(status: 'READY')],
      ],
    );

    await tester.pumpWidget(_app(repository));
    await tester.pumpAndSettle();

    expect(find.text('PENDIENTE'), findsOneWidget);

    await tester.tap(find.text('Reserva #1'));
    await tester.pumpAndSettle();
    Navigator.of(tester.element(find.text('RESERVA #1'))).pop();
    await tester.pumpAndSettle();

    expect(repository.mineCalls, 2);
    expect(find.text('LISTA'), findsOneWidget);
  });
}

Widget _app(_FakeReservationRepository repository) => ProviderScope(
  overrides: [reservationRepositoryProvider.overrideWithValue(repository)],
  child: const MaterialApp(home: Scaffold(body: ReservationsScreen())),
);

Reservation _reservation({required String status}) => Reservation(
  id: 1,
  branchName: 'Sucursal Centro',
  status: status,
  scheduledFor: DateTime(2025, 1, 10, 15),
  expiresAt: DateTime(2025, 1, 11, 15),
  items: const [
    ReservationItem(
      productName: 'Camisa lino',
      sizeName: 'M',
      colorName: 'Blanco',
      quantity: 1,
      unitPrice: 120,
    ),
  ],
);

class _FakeReservationRepository extends ReservationRepository {
  _FakeReservationRepository({required List<Object> loads, this.cancellation})
    : _loads = List<Object>.of(loads),
      super(ApiClient());

  final List<Object> _loads;
  final Reservation? cancellation;
  int mineCalls = 0;
  int cancelCalls = 0;

  @override
  Future<List<Reservation>> mine() async {
    mineCalls += 1;
    final next = _loads.length > 1 ? _loads.removeAt(0) : _loads.first;
    if (next is Exception) throw next;
    return next as List<Reservation>;
  }

  @override
  Future<Reservation> cancel(int id) async {
    cancelCalls += 1;
    return cancellation ?? _reservation(status: 'CANCELLED');
  }
}
