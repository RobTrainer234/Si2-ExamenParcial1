import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/catalog_models.dart';
import '../../cart/presentation/cart_screen.dart';

class ProductDetailScreen extends ConsumerStatefulWidget {
  const ProductDetailScreen({required this.productId, super.key});
  final int productId;
  @override
  ConsumerState<ProductDetailScreen> createState() =>
      _ProductDetailScreenState();
}

class _ProductDetailScreenState extends ConsumerState<ProductDetailScreen> {
  CatalogDetail? product;
  CatalogVariant? selected;
  List<AvailabilityItem> availability = [];
  bool loading = true;
  bool checking = false;
  bool checked = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final result = await ref
          .read(catalogRepositoryProvider)
          .detail(widget.productId);
      if (mounted) {
        setState(() {
          product = result;
          loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> checkAvailability() async {
    final current = selected;
    if (current == null) return;
    setState(() {
      checking = true;
      checked = false;
    });
    try {
      final result = await ref
          .read(catalogRepositoryProvider)
          .availability(widget.productId, current);
      if (mounted) {
        setState(() {
          availability = result;
          checking = false;
          checked = true;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          availability = [];
          checking = false;
          checked = true;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final item = product;
    if (item == null) {
      return const Scaffold(
        body: Center(child: Text('Producto no encontrado')),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('FASHIONSTORE', style: TextStyle(fontSize: 16, letterSpacing: 2, fontWeight: FontWeight.w700)), actions: [IconButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CartScreen())), icon: const Icon(Icons.shopping_bag_outlined))]),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (item.imageUrl != null)
            Image.network(
              item.imageUrl!,
              height: 360,
              fit: BoxFit.cover,
              errorBuilder: (_, _, _) => _placeholder(),
            )
          else
            _placeholder(),
          const SizedBox(height: 22),
          Text(
            item.categoryName.toUpperCase(),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              letterSpacing: 2,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            item.name,
            style: Theme.of(
              context,
            ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w300),
          ),
          const SizedBox(height: 5),
          Text(
            '${item.price.toStringAsFixed(2)} BOB',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 14),
          Text(item.description ?? 'Una prenda pensada para tu día a día.'),
          const SizedBox(height: 25),
          Text(
            'TALLA Y COLOR',
            style: Theme.of(
              context,
            ).textTheme.labelSmall?.copyWith(letterSpacing: 2),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final variant in item.variants)
                ChoiceChip(
                  label: Text('${variant.sizeName} · ${variant.colorName}'),
                  selected: selected?.id == variant.id,
                  onSelected: (_) => setState(() {
                    selected = variant;
                    checked = false;
                    availability = [];
                  }),
                ),
            ],
          ),
          const SizedBox(height: 22),
           SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: selected == null || checking
                  ? null
                  : checkAvailability,
              icon: const Icon(Icons.storefront_outlined),
              label: Text(checking ? 'Consultando...' : 'Ver disponibilidad'),
            ),
           ),
           const SizedBox(height: 10),
           SizedBox(
             width: double.infinity,
             child: OutlinedButton.icon(
               onPressed: selected == null ? null : addToCart,
               icon: const Icon(Icons.add_shopping_cart),
               label: const Text('Agregar al carrito'),
             ),
           ),
           const SizedBox(height: 18),
          if (checked && availability.isEmpty)
            const Text('No hay existencias registradas para esta combinación.'),
           for (final branch in availability)
             ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(branch.branchName),
              subtitle: Text('${branch.cityName} · ${branch.address}'),
               trailing: branch.available
                   ? FilledButton(
                       onPressed: () => reserve(branch),
                       child: const Text('Reservar'),
                     )
                   : Text('Agotado', style: TextStyle(color: Colors.grey)),
             ),
        ],
      ),
    );
  }

  Widget _placeholder() => Container(
    height: 360,
    color: const Color(0xffebe6de),
    child: const Center(
      child: Icon(Icons.checkroom, size: 60, color: Colors.black26),
    ),
  );

  Future<void> reserve(AvailabilityItem branch) async {
    final current = selected;
    if (current == null) return;
    final date = await showDatePicker(
      context: context,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
      initialDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (date == null || !mounted) return;
    final scheduled = DateTime(date.year, date.month, date.day, 10);
    try {
      await ref.read(reservationRepositoryProvider).create(
        branchId: branch.branchId,
        variantId: current.id,
        scheduledFor: scheduled,
      );
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Reserva creada correctamente.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No se pudo crear la reserva.')));
    }
  }

  Future<void> addToCart() async {
    final current = selected;
    if (current == null) return;
    try {
      await ref.read(cartRepositoryProvider).add(current.id);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Producto agregado al carrito.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No se pudo agregar al carrito.')));
    }
  }
}
