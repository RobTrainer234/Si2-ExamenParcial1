import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final firstName = TextEditingController();
  final lastName = TextEditingController();
  final email = TextEditingController();
  final phone = TextEditingController();
  final password = TextEditingController();

  @override
  void dispose() {
    for (final controller in [firstName, lastName, email, phone, password]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> submit() async {
    if ([
      firstName,
      lastName,
      email,
      phone,
      password,
    ].any((controller) => controller.text.trim().isEmpty)) {
      return;
    }
    final success = await ref.read(authControllerProvider).register({
      'first_name': firstName.text.trim(),
      'last_name': lastName.text.trim(),
      'email': email.text.trim(),
      'phone': phone.text.trim(),
      'password': password.text,
    });
    if (success && mounted) {
      Navigator.of(context).popUntil((route) => route.isFirst);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('CREAR CUENTA')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const FashionSectionHeader(
                eyebrow: 'Acceso privado',
                title: 'Armemos tu perfil de estilo.',
                body:
                    'Usaremos estos datos para tus reservas, compras y recomendaciones personalizadas.',
              ),
              const SizedBox(height: AppSpacing.xl),
              TextField(
                controller: firstName,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'Nombres',
                  prefixIcon: Icon(Icons.person_outline),
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              TextField(
                controller: lastName,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(labelText: 'Apellidos'),
              ),
              const SizedBox(height: AppSpacing.md),
              TextField(
                controller: email,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'Correo electrónico',
                  prefixIcon: Icon(Icons.mail_outline),
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              TextField(
                controller: phone,
                keyboardType: TextInputType.phone,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'Teléfono',
                  prefixIcon: Icon(Icons.phone_outlined),
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              TextField(
                controller: password,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Contraseña segura',
                  helperText: 'Incluí mayúscula, minúscula, número y símbolo.',
                  prefixIcon: Icon(Icons.lock_outline),
                ),
              ),
              if (auth.error != null) ...[
                const SizedBox(height: AppSpacing.md),
                FashionMessageCard(
                  message: auth.error!,
                  icon: Icons.info_outline,
                ),
              ],
              const SizedBox(height: AppSpacing.lg),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: auth.loading ? null : submit,
                  child: Text(auth.loading ? 'Creando...' : 'Crear cuenta'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
