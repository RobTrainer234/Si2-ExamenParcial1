import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/catalog_models.dart';

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
      appBar: AppBar(title: const Text('Detalle')),
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
          const SizedBox(height: 18),
          if (checked && availability.isEmpty)
            const Text('No hay existencias registradas para esta combinación.'),
          for (final branch in availability)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(branch.branchName),
              subtitle: Text('${branch.cityName} · ${branch.address}'),
              trailing: Text(
                branch.available ? '${branch.stock} disponibles' : 'Agotado',
                style: TextStyle(
                  color: branch.available ? Colors.green.shade700 : Colors.grey,
                ),
              ),
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
}
