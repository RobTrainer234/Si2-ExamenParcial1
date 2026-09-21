import 'package:flutter/material.dart';

import '../core/config/app_config.dart';
import '../core/theme/app_theme.dart';

class FashionSectionHeader extends StatelessWidget {
  const FashionSectionHeader({
    required this.eyebrow,
    required this.title,
    this.body,
    super.key,
  });

  final String eyebrow;
  final String title;
  final String? body;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        eyebrow.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: AppColors.goldDeep,
          letterSpacing: 2,
        ),
      ),
      const SizedBox(height: AppSpacing.sm),
      Text(title, style: Theme.of(context).textTheme.headlineLarge),
      if (body != null) ...[
        const SizedBox(height: AppSpacing.sm),
        Text(
          body!,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppColors.charcoalMuted,
            height: 1.45,
          ),
        ),
      ],
    ],
  );
}

class FashionState extends StatelessWidget {
  const FashionState({
    required this.icon,
    required this.title,
    required this.message,
    this.action,
    super.key,
  });

  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 82,
            height: 82,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.ivoryDeep,
            ),
            child: Icon(icon, size: 34, color: AppColors.goldDeep),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(
            title,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.charcoalMuted,
              height: 1.45,
            ),
          ),
          if (action != null) ...[
            const SizedBox(height: AppSpacing.lg),
            action!,
          ],
        ],
      ),
    ),
  );
}

class StatusPill extends StatelessWidget {
  const StatusPill({
    required this.label,
    this.tone = StatusTone.neutral,
    super.key,
  });

  final String label;
  final StatusTone tone;

  @override
  Widget build(BuildContext context) {
    final color = switch (tone) {
      StatusTone.success => AppColors.sage,
      StatusTone.warning => AppColors.goldDeep,
      StatusTone.danger => AppColors.rose,
      StatusTone.neutral => AppColors.charcoalMuted,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: .32)),
      ),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: color,
          fontSize: 10,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

enum StatusTone { neutral, success, warning, danger }

class FashionImageFrame extends StatelessWidget {
  const FashionImageFrame({this.imageUrl, this.height, super.key});

  final String? imageUrl;
  final double? height;

  @override
  Widget build(BuildContext context) {
    final resolvedUrl = AppConfig.resolveImageUrl(imageUrl);
    return ClipRRect(
      borderRadius: BorderRadius.circular(AppRadii.lg),
      child: Container(
        height: height,
        color: AppColors.ivoryDeep,
        child: resolvedUrl == null
            ? const Center(
                child: Icon(Icons.checkroom, size: 52, color: Colors.black26),
              )
            : Image.network(
                resolvedUrl,
                width: double.infinity,
                height: height,
                fit: BoxFit.cover,
                errorBuilder: (_, _, _) => const Center(
                  child: Icon(Icons.checkroom, size: 52, color: Colors.black26),
                ),
              ),
      ),
    );
  }
}

class FashionMessageCard extends StatelessWidget {
  const FashionMessageCard({required this.message, this.icon, super.key});

  final String message;
  final IconData? icon;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: AppColors.parchment,
      borderRadius: BorderRadius.circular(AppRadii.md),
      border: Border.all(color: AppColors.ivoryDeep),
    ),
    child: Row(
      children: [
        if (icon != null) ...[
          Icon(icon, color: AppColors.goldDeep),
          const SizedBox(width: AppSpacing.sm),
        ],
        Expanded(child: Text(message)),
      ],
    ),
  );
}
