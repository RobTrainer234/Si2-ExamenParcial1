import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/providers.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/cart/presentation/cart_screen.dart';
import 'features/catalog/presentation/catalog_screen.dart';
import 'features/chat/presentation/ai_chat_screen.dart';
import 'core/config/app_config.dart';
import 'features/purchases/presentation/purchase_history_screen.dart';
import 'features/recommendations/presentation/recommendations_screen.dart';
import 'features/reservations/presentation/reservations_screen.dart';
import 'shared/fashion_ui.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppConfig.loadCustomBaseUrl();
  runApp(const ProviderScope(child: FashionStoreApp()));
}

class FashionStoreApp extends ConsumerWidget {
  const FashionStoreApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp(
    scaffoldMessengerKey: ref.watch(notificationServiceProvider).messengerKey,
    title: 'FashionStore',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light(),
    home: const AuthGate(),
  );
}

class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    if (auth.loading) {
      return const Scaffold(
        body: FashionState(
          icon: Icons.auto_awesome_outlined,
          title: 'Preparando tu experiencia',
          message: 'Estamos ajustando el showroom para vos.',
        ),
      );
    }
    return auth.isAuthenticated
        ? const FashionStoreShell()
        : const LoginScreen();
  }
}

class FashionStoreShell extends ConsumerStatefulWidget {
  const FashionStoreShell({super.key});

  @override
  ConsumerState<FashionStoreShell> createState() => _FashionStoreShellState();
}

class _FashionStoreShellState extends ConsumerState<FashionStoreShell> {
  int selectedIndex = 0;

  static const _titles = [
    'FASHIONSTORE',
    'RESERVAS',
    'RECOMENDADAS',
    'COMPRAS',
  ];

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[selectedIndex]),
        actions: [
          IconButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const CartScreen()),
            ),
            icon: const Icon(Icons.shopping_bag_outlined),
            tooltip: 'Carrito de compras',
          ),
          IconButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const AiChatScreen()),
            ),
            icon: const Icon(Icons.auto_awesome),
            tooltip: 'Sofía Asistente IA',
          ),
          IconButton(
            onPressed: auth.logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
          ),
        ],
      ),
      body: IndexedStack(
        index: selectedIndex,
        children: const [
          CatalogScreen(),
          ReservationsScreen(),
          RecommendationsScreen(),
          PurchaseHistoryScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: (index) => setState(() => selectedIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome),
            label: 'Catálogo',
          ),
          NavigationDestination(
            icon: Icon(Icons.bookmark_border),
            selectedIcon: Icon(Icons.bookmark),
            label: 'Reservas',
          ),
          NavigationDestination(
            icon: Icon(Icons.psychology_alt_outlined),
            selectedIcon: Icon(Icons.psychology_alt),
            label: 'IA',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Compras',
          ),
        ],
      ),
    );
  }
}
