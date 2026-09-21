import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../../cart/presentation/cart_screen.dart';
import '../../virtual_fitting/presentation/virtual_fitting_screen.dart';
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
      return const Scaffold(
        body: FashionState(
          icon: Icons.hourglass_top,
          title: 'Preparando la ficha',
          message: 'Estamos cargando tallas, colores y disponibilidad.',
        ),
      );
    }
    final item = product;
    if (item == null) {
      return const Scaffold(
        body: FashionState(
          icon: Icons.search_off_outlined,
          title: 'Producto no encontrado',
          message: 'La prenda ya no está disponible en el catálogo.',
        ),
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: const Text('DETALLE'),
        actions: [
          IconButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute<void>(builder: (_) => const CartScreen()),
            ),
            icon: const Icon(Icons.shopping_bag_outlined),
            tooltip: 'Ver carrito',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          FashionImageFrame(imageUrl: item.imageUrl, height: 380),
          const SizedBox(height: AppSpacing.lg),
          Text(
            item.categoryName.toUpperCase(),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: AppColors.goldDeep,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(item.name, style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.xs),
          Text(
            '${item.price.toStringAsFixed(2)} BOB',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            item.description ??
                'Una prenda seleccionada para elevar tu día a día con comodidad y carácter.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.charcoalMuted,
              height: 1.45,
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('TALLA Y COLOR', style: Theme.of(context).textTheme.labelSmall),
          const SizedBox(height: AppSpacing.sm),
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
          const SizedBox(height: AppSpacing.lg),
          FilledButton.icon(
            onPressed: selected == null || checking ? null : checkAvailability,
            icon: const Icon(Icons.storefront_outlined),
            label: Text(checking ? 'Consultando...' : 'Ver disponibilidad'),
          ),
          const SizedBox(height: AppSpacing.sm),
          OutlinedButton.icon(
            onPressed: selected == null ? null : addToCart,
            icon: const Icon(Icons.add_shopping_cart),
            label: const Text('Agregar al carrito'),
          ),
          const SizedBox(height: AppSpacing.sm),
          OutlinedButton.icon(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute<void>(
                builder: (_) => VirtualFittingScreen(
                  productId: item.id,
                  productName: item.name,
                  imageUrl: item.imageUrl,
                ),
              ),
            ),
            icon: const Icon(Icons.view_in_ar_outlined),
            label: const Text('Probar en vestidor virtual'),
          ),
          const SizedBox(height: AppSpacing.lg),
          if (checked && availability.isEmpty)
            const FashionMessageCard(
              message:
                  'No hay existencias registradas para esta combinación. Elegí otra variante o consultá más tarde.',
              icon: Icons.inventory_2_outlined,
            ),
          for (final branch in availability) ...[
            _availabilityCard(context, branch),
            const SizedBox(height: AppSpacing.sm),
          ],
        ],
      ),
    );
  }

  Widget _availabilityCard(BuildContext context, AvailabilityItem branch) =>
      Card(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      branch.branchName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  StatusPill(
                    label: branch.available ? 'Disponible' : 'Agotado',
                    tone: branch.available
                        ? StatusTone.success
                        : StatusTone.neutral,
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xs),
              Text('${branch.cityName} · ${branch.address}'),
              const SizedBox(height: AppSpacing.xs),
              Text('Stock: ${branch.stock}'),
              const SizedBox(height: AppSpacing.md),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: branch.available ? () => reserve(branch) : null,
                  child: const Text('Reservar para probar'),
                ),
              ),
            ],
          ),
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
      await ref
          .read(reservationRepositoryProvider)
          .create(
            branchId: branch.branchId,
            items: [
              {'product_variant_id': current.id, 'quantity': 1},
            ],
            scheduledFor: scheduled,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Reserva creada correctamente.')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo crear la reserva.')),
        );
      }
    }
  }

  Future<void> addToCart() async {
    final current = selected;
    if (current == null) return;
    try {
      await ref.read(cartRepositoryProvider).add(current.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Producto agregado al carrito.')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo agregar al carrito.')),
        );
      }
    }
  }
}
