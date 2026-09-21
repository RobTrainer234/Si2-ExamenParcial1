import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../data/reservation_models.dart';

class ReservationsScreen extends ConsumerStatefulWidget {
  const ReservationsScreen({super.key});
  @override
  ConsumerState<ReservationsScreen> createState() => _ReservationsScreenState();
}

class _ReservationsScreenState extends ConsumerState<ReservationsScreen> {
  List<Reservation> reservations = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    load(showLoading: true);
  }

  Future<void> load({bool showLoading = false}) async {
    if (showLoading && mounted) {
      setState(() {
        loading = true;
        error = null;
      });
    }

    try {
      final result = await ref.read(reservationRepositoryProvider).mine();
      if (mounted) {
        setState(() {
          reservations = result;
          loading = false;
          error = null;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          loading = false;
          error = 'No pudimos cargar tus reservas.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget content;
    if (loading) {
      content = _refreshableState(
        const FashionState(
          icon: Icons.bookmark_border,
          title: 'Buscando tus reservas',
          message: 'Estamos consultando el estado de tus prendas apartadas.',
        ),
      );
    } else if (error != null) {
      content = _refreshableState(
        FashionState(
          icon: Icons.wifi_off_outlined,
          title: 'Reservas no disponibles',
          message: error!,
          action: Semantics(
            button: true,
            label: 'Reintentar carga de reservas',
            child: FilledButton.icon(
              onPressed: () => load(showLoading: true),
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ),
        ),
      );
    } else if (reservations.isEmpty) {
      content = _refreshableState(
        const FashionState(
          icon: Icons.bookmark_add_outlined,
          title: 'Todavía no tenés reservas',
          message:
              'Reservá una prenda desde el detalle del producto para probarla en tienda.',
        ),
      );
    } else {
      content = ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          const FashionSectionHeader(
            eyebrow: 'Tus pruebas',
            title: 'Reservas activas e historial.',
          ),
          const SizedBox(height: AppSpacing.lg),
          for (final reservation in reservations) ...[
            _card(reservation),
            const SizedBox(height: AppSpacing.sm),
          ],
        ],
      );
    }
    return RefreshIndicator(onRefresh: load, child: content);
  }

  Widget _refreshableState(Widget child) => ListView(
    physics: const AlwaysScrollableScrollPhysics(),
    children: [
      SizedBox(height: MediaQuery.sizeOf(context).height * .62, child: child),
    ],
  );

  Widget _card(Reservation reservation) => Card(
    child: ListTile(
      minVerticalPadding: 16,
      title: Text('Reserva #${reservation.id}'),
      subtitle: Text(
        '${reservation.branchName}\n${reservation.scheduledFor == null ? 'Sin horario confirmado' : reservation.scheduledFor!.toLocal()}',
      ),
      isThreeLine: true,
      trailing: StatusPill(
        label: reservation.statusLabel,
        tone: reservation.statusTone,
      ),
      onTap: () async {
        await Navigator.push<void>(
          context,
          MaterialPageRoute<void>(
            builder: (_) => ReservationDetailScreen(reservation: reservation),
          ),
        );
        if (mounted) {
          await load();
        }
      },
    ),
  );
}

extension on Reservation {
  String get statusLabel =>
      ({
        'PENDING': 'Pendiente',
        'PREPARING': 'En preparación',
        'READY': 'Lista',
        'ATTENDED': 'Atendida',
        'CANCELLED': 'Cancelada',
        'EXPIRED': 'Vencida',
      })[status] ??
      status;

  StatusTone get statusTone => switch (status) {
    'READY' || 'ATTENDED' => StatusTone.success,
    'CANCELLED' || 'EXPIRED' => StatusTone.danger,
    'PREPARING' || 'PENDING' => StatusTone.warning,
    _ => StatusTone.neutral,
  };
}

class ReservationDetailScreen extends ConsumerStatefulWidget {
  const ReservationDetailScreen({required this.reservation, super.key});
  final Reservation reservation;
  @override
  ConsumerState<ReservationDetailScreen> createState() =>
      _ReservationDetailScreenState();
}

class _ReservationDetailScreenState
    extends ConsumerState<ReservationDetailScreen> {
  late Reservation reservation = widget.reservation;
  bool cancelling = false;

  Future<void> cancel() async {
    if (cancelling) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancelar reserva'),
        content: const Text(
          '¿Querés cancelar esta reserva? Esta acción no se puede deshacer.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Volver'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Sí, cancelar'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => cancelling = true);
    try {
      final updated = await ref
          .read(reservationRepositoryProvider)
          .cancel(reservation.id);
      if (mounted) {
        setState(() {
          reservation = updated;
          cancelling = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => cancelling = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo cancelar la reserva.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text('RESERVA #${reservation.id}')),
    body: ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        FashionSectionHeader(
          eyebrow: reservation.statusLabel,
          title: reservation.branchName,
          body: reservation.scheduledFor == null
              ? 'Aún no hay horario confirmado para esta reserva.'
              : 'Tu prueba está programada para ${reservation.scheduledFor!.toLocal()}.',
        ),
        const SizedBox(height: AppSpacing.md),
        if (reservation.expiresAt != null)
          FashionMessageCard(
            message: 'Vence: ${reservation.expiresAt!.toLocal()}',
            icon: Icons.schedule_outlined,
          ),
        const SizedBox(height: AppSpacing.lg),
        for (final item in reservation.items) ...[
          Card(
            child: ListTile(
              minVerticalPadding: 14,
              title: Text('${item.quantity} × ${item.productName}'),
              subtitle: Text('${item.sizeName} · ${item.colorName}'),
              trailing: Text('${item.unitPrice.toStringAsFixed(2)} BOB'),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
        ],
        if (reservation.status == 'PENDING' ||
            reservation.status == 'PREPARING')
          Semantics(
            button: true,
            label: 'Cancelar reserva ${reservation.id}',
            child: FilledButton(
              onPressed: cancelling ? null : cancel,
              child: Text(cancelling ? 'Cancelando...' : 'Cancelar reserva'),
            ),
          ),
      ],
    ),
  );
}
