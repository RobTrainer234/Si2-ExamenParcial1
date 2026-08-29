import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/providers.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/catalog/presentation/catalog_screen.dart';

void main() => runApp(const ProviderScope(child: FashionStoreApp()));

class FashionStoreApp extends StatelessWidget {
  const FashionStoreApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'FashionStore',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xffc35f43),
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: const Color(0xfff6f3ee),
      useMaterial3: true,
    ),
    home: const AuthGate(),
  );
}

class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    if (auth.loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return auth.isAuthenticated ? const CatalogScreen() : const LoginScreen();
  }
}
