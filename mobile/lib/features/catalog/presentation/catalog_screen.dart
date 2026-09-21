import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../data/catalog_models.dart';
import 'product_detail_screen.dart';

class CatalogScreen extends ConsumerStatefulWidget {
  const CatalogScreen({super.key});

  @override
  ConsumerState<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends ConsumerState<CatalogScreen> {
  final search = TextEditingController();
  List<CatalogItem> items = [];
  int page = 1;
  int totalPages = 1;
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await ref
          .read(catalogRepositoryProvider)
          .list(query: search.text.trim(), page: page);
      if (!mounted) return;
      setState(() {
        items = result.items;
        totalPages = result.totalPages;
        loading = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          loading = false;
          error = 'No pudimos cargar el catálogo en este momento.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return RefreshIndicator(
      onRefresh: load,
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 8),
              child: _header(
                context,
                auth.session?.user['first_name'] as String?,
              ),
            ),
          ),
          if (loading)
            const SliverFillRemaining(
              child: FashionState(
                icon: Icons.checkroom_outlined,
                title: 'Curando la colección',
                message:
                    'Un momento mientras preparamos las prendas disponibles.',
              ),
            )
          else if (error != null)
            SliverFillRemaining(
              child: FashionState(
                icon: Icons.wifi_off_outlined,
                title: 'No conectamos con el showroom',
                message: error!,
              ),
            )
          else if (items.isEmpty)
            const SliverFillRemaining(
              child: FashionState(
                icon: Icons.search_off_outlined,
                title: 'Sin prendas para mostrar',
                message:
                    'Probá con otra búsqueda o volvé a explorar la colección completa.',
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              sliver: SliverGrid(
                delegate: SliverChildBuilderDelegate(
                  _productCard,
                  childCount: items.length,
                ),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 18,
                  childAspectRatio: .62,
                ),
              ),
            ),
          if (!loading && totalPages > 1)
            SliverToBoxAdapter(child: _pagination()),
        ],
      ),
    );
  }

  Widget _header(BuildContext context, String? firstName) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      FashionSectionHeader(
        eyebrow: 'Hola, ${firstName ?? 'cliente'}',
        title: 'Elegí tu próxima pieza.',
        body:
            'Catálogo editorial con disponibilidad para reserva, carrito y vestidor virtual.',
      ),
      const SizedBox(height: AppSpacing.lg),
      TextField(
        controller: search,
        onSubmitted: (_) {
          page = 1;
          load();
        },
        decoration: InputDecoration(
          hintText: 'Buscar vestido, saco, color...',
          prefixIcon: const Icon(Icons.search),
          suffixIcon: IconButton(
            onPressed: () {
              page = 1;
              load();
            },
            icon: const Icon(Icons.arrow_forward),
            tooltip: 'Buscar',
          ),
        ),
      ),
    ],
  );

  Widget _productCard(BuildContext context, int index) {
    final item = items[index];
    return InkWell(
      borderRadius: BorderRadius.circular(AppRadii.lg),
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute<void>(
          builder: (_) => ProductDetailScreen(productId: item.id),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Stack(
              children: [
                Positioned.fill(
                  child: FashionImageFrame(imageUrl: item.imageUrl),
                ),
                const Positioned(
                  top: 10,
                  left: 10,
                  child: StatusPill(label: 'Nuevo', tone: StatusTone.warning),
                ),
                Positioned(
                  right: 10,
                  top: 10,
                  child: Container(
                    width: 36,
                    height: 36,
                    decoration: const BoxDecoration(
                      color: AppColors.parchment,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.favorite_border, size: 19),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            item.categoryName.toUpperCase(),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: AppColors.goldDeep,
              fontSize: 10,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            item.name,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 4),
          Text(
            '${item.price.toStringAsFixed(2)} BOB',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              color: AppColors.charcoal,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }

  Widget _pagination() => Padding(
    padding: const EdgeInsets.only(bottom: AppSpacing.lg),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton.filledTonal(
          onPressed: page > 1
              ? () {
                  page--;
                  load();
                }
              : null,
          icon: const Icon(Icons.chevron_left),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
          child: StatusPill(label: '$page / $totalPages'),
        ),
        IconButton.filledTonal(
          onPressed: page < totalPages
              ? () {
                  page++;
                  load();
                }
              : null,
          icon: const Icon(Icons.chevron_right),
        ),
      ],
    ),
  );
}
