import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';

class PurchaseHistoryScreen extends ConsumerStatefulWidget {
  const PurchaseHistoryScreen({super.key});

  @override
  ConsumerState<PurchaseHistoryScreen> createState() =>
      _PurchaseHistoryScreenState();
}

class _PurchaseHistoryScreenState extends ConsumerState<PurchaseHistoryScreen> {
  List<dynamic> items = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final response = await ref.read(purchaseRepositoryProvider).mine();
      if (!mounted) return;
      setState(() {
        items = response['items'] as List<dynamic>;
        loading = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          error = 'No pudimos cargar tu historial.';
          loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const FashionState(
        icon: Icons.receipt_long_outlined,
        title: 'Revisando tus compras',
        message: 'Estamos preparando tu historial.',
      );
    }
    if (error != null) {
      return FashionState(
        icon: Icons.wifi_off_outlined,
        title: 'Historial no disponible',
        message: error!,
      );
    }
    if (items.isEmpty) {
      return const FashionState(
        icon: Icons.local_mall_outlined,
        title: 'Aún no registramos compras',
        message: 'Cuando completes una compra, la vas a ver acá.',
      );
    }
    return RefreshIndicator(
      onRefresh: load,
      child: ListView.separated(
        padding: const EdgeInsets.all(AppSpacing.lg),
        itemCount: items.length + 1,
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
        itemBuilder: (context, index) {
          if (index == 0) {
            return const Padding(
              padding: EdgeInsets.only(bottom: AppSpacing.md),
              child: FashionSectionHeader(
                eyebrow: 'Historial',
                title: 'Tus compras FashionStore.',
              ),
            );
          }
          final sale = items[index - 1] as Map<String, dynamic>;
          return Card(
            child: ListTile(
              minVerticalPadding: 16,
              title: Text(sale['order_number'] as String),
              subtitle: Text('${sale['channel']} · ${sale['status']} · ${_fulfillmentSummary(sale)}'),
              trailing: Text(
                '${sale['total']} BOB',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
          );
        },
      ),
    );
  }

  String _fulfillmentSummary(Map<String, dynamic> sale) {
    if (sale['fulfillment_type'] != 'DELIVERY') return 'Retiro en tienda';
    final details = sale['shipping_details'] as Map<String, dynamic>?;
    if (details == null) return 'Delivery';
    return 'Delivery: ${details['street']} ${details['house_number']}, ${details['zone']}';
  }
}
