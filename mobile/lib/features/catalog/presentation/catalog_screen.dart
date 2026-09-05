import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
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
          error = 'No se pudo cargar el catálogo.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('FASHIONSTORE', style: TextStyle(fontSize: 16, letterSpacing: 2, fontWeight: FontWeight.w700)),
        actions: [
          IconButton(
            onPressed: auth.logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 0,
        onDestinationSelected: (_) {},
        destinations: const [
          NavigationDestination(icon: Icon(Icons.auto_awesome_outlined), label: 'Catálogo'),
          NavigationDestination(icon: Icon(Icons.storefront_outlined), label: 'Tiendas'),
          NavigationDestination(icon: Icon(Icons.favorite_border), label: 'Favoritos'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Perfil'),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: load,
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 22, 20, 10),
                child: _header(
                  context,
                  auth.session?.user['first_name'] as String?,
                ),
              ),
            ),
            if (loading)
              const SliverFillRemaining(
                child: Center(child: CircularProgressIndicator()),
              )
            else if (error != null)
              SliverFillRemaining(child: Center(child: Text(error!)))
            else if (items.isEmpty)
              const SliverFillRemaining(
                child: Center(child: Text('No encontramos prendas.')),
              )
            else
              SliverPadding(
                padding: const EdgeInsets.all(16),
                sliver: SliverGrid(
                  delegate: SliverChildBuilderDelegate(
                    _productCard,
                    childCount: items.length,
                  ),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 18,
                    childAspectRatio: .68,
                  ),
                ),
              ),
            if (!loading && totalPages > 1)
              SliverToBoxAdapter(child: _pagination()),
          ],
        ),
      ),
    );
  }

  Widget _header(BuildContext context, String? firstName) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        'HOLA, ${(firstName ?? 'CLIENTE').toUpperCase()}',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          letterSpacing: 2,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
      const SizedBox(height: 8),
      Text(
        'Encuentra tu\npróxima prenda.',
        style: Theme.of(
          context,
        ).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w300),
      ),
      const SizedBox(height: 10),
      const Text('NUEVA COLECCIÓN · OTOÑO 2024', style: TextStyle(fontSize: 10, letterSpacing: 1.4, color: Color(0xffc35f43))),
      const SizedBox(height: 22),
      TextField(
        controller: search,
        onSubmitted: (_) {
          page = 1;
          load();
        },
        decoration: InputDecoration(
          hintText: 'Buscar prendas...',
          prefixIcon: const Icon(Icons.search),
          suffixIcon: IconButton(
            onPressed: () {
              page = 1;
              load();
            },
            icon: const Icon(Icons.arrow_forward),
          ),
        ),
      ),
      const SizedBox(height: 12),
    ],
  );

  Widget _productCard(BuildContext context, int index) {
    final item = items[index];
    return InkWell(
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
                 Container(
                   color: const Color(0xffebe6de),
                   child: item.imageUrl == null
                       ? const Center(child: Icon(Icons.checkroom, size: 45, color: Colors.black26))
                       : Image.network(
                           item.imageUrl!,
                           fit: BoxFit.cover,
                           width: double.infinity,
                           errorBuilder: (_, _, _) => const Icon(Icons.checkroom, size: 45, color: Colors.black26),
                         ),
                 ),
                 Positioned(top: 8, left: 8, child: Container(color: const Color(0xddf6f3ee), padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4), child: const Text('NUEVO', style: TextStyle(fontSize: 9, letterSpacing: 1)))),
                 const Positioned(top: 6, right: 6, child: Icon(Icons.favorite_border, size: 19)),
               ],
             ),
           ),
          const SizedBox(height: 8),
          Text(
            item.categoryName.toUpperCase(),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              letterSpacing: 1,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          Text(item.name, maxLines: 1, overflow: TextOverflow.ellipsis),
          Text(
            '${item.price.toStringAsFixed(2)} BOB',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _pagination() => Padding(
    padding: const EdgeInsets.symmetric(vertical: 20),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          onPressed: page > 1
              ? () {
                  page--;
                  load();
                }
              : null,
          icon: const Icon(Icons.chevron_left),
        ),
        Text('$page / $totalPages'),
        IconButton(
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
