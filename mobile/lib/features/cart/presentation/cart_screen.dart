import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';

class CartScreen extends ConsumerStatefulWidget {
  const CartScreen({super.key});
  @override
  ConsumerState<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends ConsumerState<CartScreen> {
  Map<String, dynamic>? cart;
  final branchController = TextEditingController();
  bool loading = true;
  bool paying = false;
  String message = '';

  @override
  void initState() { super.initState(); load(); }
  @override
  void dispose() { branchController.dispose(); super.dispose(); }

  Future<void> load() async {
    try { final result = await ref.read(cartRepositoryProvider).get(); if (mounted) setState(() { cart = result; loading = false; }); }
    catch (_) { if (mounted) setState(() { loading = false; message = 'No se pudo cargar el carrito.'; }); }
  }

  Future<void> remove(int id) async { final result = await ref.read(cartRepositoryProvider).remove(id); if (mounted) setState(() => cart = result); }

  Future<void> checkout() async {
    final branchId = int.tryParse(branchController.text);
    if (branchId == null || branchId <= 0 || cart == null) { setState(() => message = 'Indica el ID de la sucursal de retiro.'); return; }
    setState(() { paying = true; message = ''; });
    try {
      final sale = await ref.read(cartRepositoryProvider).purchase(branchId);
      final payment = await ref.read(cartRepositoryProvider).pay(sale['id'] as int, 'mobile-${sale['id']}-${DateTime.now().millisecondsSinceEpoch}');
      await ref.read(cartRepositoryProvider).approve(payment['transaction_reference'] as String, sale['total'].toString());
      if (mounted) { setState(() { paying = false; message = 'Compra ${sale['order_number']} confirmada.'; }); await load(); }
    } catch (_) { if (mounted) setState(() { paying = false; message = 'No se pudo completar el pago.'; }); }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final items = (cart?['items'] as List<dynamic>?) ?? const [];
    final total = cart?['total']?.toString() ?? '0.00';
    return Scaffold(appBar: AppBar(title: const Text('Mi carrito')), body: ListView(padding: const EdgeInsets.all(20), children: [if (message.isNotEmpty) Text(message), if (items.isEmpty) const Text('Tu carrito está vacío.'), for (final raw in items) _item(raw as Map<String, dynamic>), if (items.isNotEmpty) ...[
      const SizedBox(height: 20), Text('Total: $total'), TextField(controller: branchController, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'ID de sucursal de retiro')), const SizedBox(height: 12), FilledButton(onPressed: paying ? null : checkout, child: Text(paying ? 'Procesando...' : 'Pagar en sandbox')),
    ]]));
  }

  Widget _item(Map<String, dynamic> item) => Card(child: ListTile(title: Text(item['product_name'] as String), subtitle: Text('${item['size_name']} · ${item['color_name']}\nCantidad: ${item['quantity']}'), trailing: IconButton(onPressed: () => remove(item['id'] as int), icon: const Icon(Icons.delete_outline))));
}
