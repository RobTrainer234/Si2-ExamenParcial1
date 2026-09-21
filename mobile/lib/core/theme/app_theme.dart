import 'package:flutter/material.dart';

class AppColors {
  const AppColors._();

  static const ivory = Color(0xfffbf7ef);
  static const ivoryDeep = Color(0xfff0e8db);
  static const parchment = Color(0xfffffcf6);
  static const charcoal = Color(0xff25211d);
  static const charcoalMuted = Color(0xff6f675d);
  static const gold = Color(0xffb8924a);
  static const goldDeep = Color(0xff8f6d2d);
  static const sage = Color(0xff7f8a72);
  static const rose = Color(0xffb46a57);
}

class AppSpacing {
  const AppSpacing._();

  static const xs = 6.0;
  static const sm = 10.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const xxl = 44.0;
}

class AppRadii {
  const AppRadii._();

  static const sm = 12.0;
  static const md = 18.0;
  static const lg = 26.0;
  static const xl = 34.0;
}

class AppTheme {
  const AppTheme._();

  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(
      seedColor: AppColors.gold,
      brightness: Brightness.light,
      primary: AppColors.charcoal,
      secondary: AppColors.gold,
      surface: AppColors.parchment,
      error: AppColors.rose,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.ivory,
      fontFamily: 'Arial',
    );

    final text = base.textTheme.apply(
      bodyColor: AppColors.charcoal,
      displayColor: AppColors.charcoal,
    );

    return base.copyWith(
      textTheme: text.copyWith(
        displaySmall: text.displaySmall?.copyWith(
          fontWeight: FontWeight.w300,
          letterSpacing: -.8,
          height: 1.02,
        ),
        headlineLarge: text.headlineLarge?.copyWith(
          fontWeight: FontWeight.w300,
          letterSpacing: -.7,
          height: 1.02,
        ),
        headlineMedium: text.headlineMedium?.copyWith(
          fontWeight: FontWeight.w300,
          letterSpacing: -.4,
        ),
        titleLarge: text.titleLarge?.copyWith(fontWeight: FontWeight.w700),
        titleMedium: text.titleMedium?.copyWith(fontWeight: FontWeight.w700),
        labelSmall: text.labelSmall?.copyWith(
          letterSpacing: 1.5,
          fontWeight: FontWeight.w800,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.ivory,
        foregroundColor: AppColors.charcoal,
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: TextStyle(
          color: AppColors.charcoal,
          fontSize: 15,
          letterSpacing: 2.4,
          fontWeight: FontWeight.w800,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.parchment,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.lg),
          side: const BorderSide(color: AppColors.ivoryDeep),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.parchment,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 18,
          vertical: 18,
        ),
        labelStyle: const TextStyle(color: AppColors.charcoalMuted),
        hintStyle: const TextStyle(color: AppColors.charcoalMuted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
          borderSide: const BorderSide(color: AppColors.ivoryDeep),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
          borderSide: const BorderSide(color: AppColors.ivoryDeep),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
          borderSide: const BorderSide(color: AppColors.gold, width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          backgroundColor: AppColors.charcoal,
          foregroundColor: AppColors.ivory,
          textStyle: const TextStyle(fontWeight: FontWeight.w800),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadii.md),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          foregroundColor: AppColors.charcoal,
          side: const BorderSide(color: AppColors.gold),
          textStyle: const TextStyle(fontWeight: FontWeight.w800),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadii.md),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: AppColors.charcoal),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: AppColors.parchment,
        selectedColor: AppColors.charcoal,
        labelStyle: const TextStyle(color: AppColors.charcoal),
        secondaryLabelStyle: const TextStyle(color: AppColors.ivory),
        side: const BorderSide(color: AppColors.ivoryDeep),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.sm),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.parchment,
        indicatorColor: AppColors.ivoryDeep,
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            color: states.contains(WidgetState.selected)
                ? AppColors.charcoal
                : AppColors.charcoalMuted,
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
