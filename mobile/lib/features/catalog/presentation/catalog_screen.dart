import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/offline/connectivity_monitor.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../../offline/presentation/offline_operations_screen.dart';
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
  bool isOffline = false;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(syncCatalogServiceProvider).init();
      ref.read(syncTransactionServiceProvider).refreshPendingCount();
    });
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
        isOffline = result.isOffline;
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

  Future<void> _handleSync() async {
    final syncService = ref.read(syncCatalogServiceProvider);
    final success = await syncService.syncCatalog();
    if (!mounted) return;
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Catálogo offline sincronizado correctamente.'),
          backgroundColor: Color(0xFF0F766E),
        ),
      );
      await load();
    } else if (syncService.syncError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al sincronizar: ${syncService.syncError}'),
          backgroundColor: Colors.redAccent,
        ),
      );
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
      _syncStatusBar(),
    ],
  );

  Widget _syncStatusBar() {
    final sync = ref.watch(syncCatalogServiceProvider);
    final connectivity = ref.watch(connectivityMonitorProvider);
    final lastSync = sync.lastSync;
    final lastSyncStr = lastSync != null
        ? '${lastSync.day.toString().padLeft(2, '0')}/${lastSync.month.toString().padLeft(2, '0')}/${lastSync.year} ${lastSync.hour.toString().padLeft(2, '0')}:${lastSync.minute.toString().padLeft(2, '0')}'
        : 'Sin sincronización previa';

    return Container(
      margin: const EdgeInsets.only(top: 14),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isOffline ? const Color(0xFFFEF3C7) : const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isOffline ? const Color(0xFFF59E0B) : const Color(0xFFCBD5E1),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isOffline ? Icons.cloud_off_outlined : Icons.cloud_done_outlined,
                size: 18,
                color: isOffline ? const Color(0xFFB45309) : const Color(0xFF0F766E),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  isOffline
                      ? 'Modo offline · Catálogo local'
                      : 'En línea · Showroom activo',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: isOffline
                        ? const Color(0xFF92400E)
                        : const Color(0xFF0F766E),
                  ),
                ),
              ),
              if (sync.isSyncing)
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              else
                TextButton.icon(
                  style: TextButton.styleFrom(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  onPressed: _handleSync,
                  icon: const Icon(Icons.sync, size: 14),
                  label: const Text(
                    'Descargar offline',
                    style: TextStyle(fontSize: 12),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Conectividad: ${_connectivityLabel(connectivity.status)}',
            style: const TextStyle(fontSize: 11, color: Color(0xFF475569)),
          ),
          Text(
            'Última actualización: $lastSyncStr',
            style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
          ),
          const SizedBox(height: 8),
          _offlineOperationsBar(context),
          if (isOffline) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFFFFFBEB),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.warning_amber_rounded,
                      size: 16, color: Color(0xFFD97706)),
                  SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Precios y disponibilidad locales pueden estar desactualizados.',
                      style: TextStyle(
                        fontSize: 12,
                        color: Color(0xFFB45309),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _connectivityLabel(ConnectivityStatus status) {
    switch (status) {
      case ConnectivityStatus.unknown:
        return 'Verificando conexión…';
      case ConnectivityStatus.offline:
        return 'Sin conexión';
      case ConnectivityStatus.online:
        return 'Conexión disponible';
    }
  }

  Widget _offlineOperationsBar(BuildContext context) {
    final txSync = ref.watch(syncTransactionServiceProvider);
    final count = txSync.pendingCount;

    return OutlinedButton.icon(
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      onPressed: () {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const OfflineOperationsScreen()),
        );
      },
      icon: Badge(
        isLabelVisible: count > 0,
        label: Text('$count'),
        child: const Icon(Icons.outbox_outlined, size: 16),
      ),
      label: Text(
        count > 0
            ? 'Bandeja offline ($count pendiente${count == 1 ? '' : 's'})'
            : 'Bandeja offline',
        style: const TextStyle(fontSize: 12),
      ),
    );
  }

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
