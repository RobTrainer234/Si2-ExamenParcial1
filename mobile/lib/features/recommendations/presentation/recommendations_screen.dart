import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../../chat/presentation/ai_chat_screen.dart';

class RecommendationsScreen extends ConsumerStatefulWidget {
  const RecommendationsScreen({super.key});

  @override
  ConsumerState<RecommendationsScreen> createState() =>
      _RecommendationsScreenState();
}

class _RecommendationsScreenState extends ConsumerState<RecommendationsScreen> {
  List<dynamic> items = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await ref.read(recommendationRepositoryProvider).mine();
      if (!mounted) return;
      setState(() {
        items = result;
        loading = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          error = 'No pudimos cargar recomendaciones.';
          loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const FashionState(
        icon: Icons.psychology_alt_outlined,
        title: 'Leyendo tu estilo',
        message: 'La IA está preparando sugerencias para vos.',
      );
    }
    if (error != null) {
      return FashionState(
        icon: Icons.wifi_off_outlined,
        title: 'Recomendaciones no disponibles',
        message: error!,
      );
    }
    if (items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const FashionState(
                icon: Icons.auto_awesome_outlined,
                title: 'Sin recomendaciones todavía',
                message:
                    'Explorá prendas o chatea con nuestra asistente de inteligencia artificial.',
              ),
              const SizedBox(height: AppSpacing.md),
              FilledButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const AiChatScreen()),
                ),
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Consultar a Sofía IA'),
              ),
            ],
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: load,
      child: ListView.separated(
        padding: const EdgeInsets.all(AppSpacing.lg),
        itemCount: items.length + 1,
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
        itemBuilder: (context, index) {
          if (index == 0) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const FashionSectionHeader(
                  eyebrow: 'Curaduría IA',
                  title: 'Piezas pensadas para vos.',
                  body:
                      'Sugerencias basadas en tu actividad y preferencias recientes.',
                ),
                const SizedBox(height: AppSpacing.md),
                Card(
                  color: AppColors.charcoal,
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    child: Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: AppColors.goldDeep.withValues(
                            alpha: 0.2,
                          ),
                          child: const Icon(
                            Icons.auto_awesome,
                            color: AppColors.goldDeep,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Asistente Sofía IA',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Pregúntale en lenguaje natural sobre vestidos, sucursales y probador AR.',
                                style: TextStyle(
                                  color: Colors.white.withValues(alpha: 0.8),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        FilledButton.tonal(
                          onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const AiChatScreen(),
                            ),
                          ),
                          child: const Text('Chatear'),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            );
          }
          final item = items[index - 1] as Map<String, dynamic>;
          return Card(
            clipBehavior: Clip.antiAlias,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                FashionImageFrame(
                  imageUrl: item['image_url'] as String?,
                  height: 220,
                ),
                Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        (item['category_name'] as String).toUpperCase(),
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: AppColors.goldDeep,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        item['product_name'] as String,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Text(item['reason'] as String),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
