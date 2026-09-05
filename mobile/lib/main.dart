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
      fontFamily: 'Arial',
      useMaterial3: true,
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xfff6f3ee),
        foregroundColor: Color(0xff242321),
        elevation: 0,
        centerTitle: false,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Color(0xffebe6de),
        border: OutlineInputBorder(borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Color(0xffc35f43)),
        ),
      ),
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
