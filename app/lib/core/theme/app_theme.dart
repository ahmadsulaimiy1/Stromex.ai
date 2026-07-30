import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Central theme factory. One design system, two brightness modes — the
/// Experience Design System calls for zero-clutter, premium motion, and a
/// consistent identity across light and dark.
class AppTheme {
  AppTheme._();

  static ThemeData light() => _base(
        brightness: Brightness.light,
        background: AppColors.creamBackground,
        surface: AppColors.creamSurface,
        onBackground: AppColors.inkLight,
      );

  static ThemeData dark() => _base(
        brightness: Brightness.dark,
        background: AppColors.charcoalBackground,
        surface: AppColors.charcoalSurface,
        onBackground: AppColors.inkDark,
      );

  static ThemeData _base({
    required Brightness brightness,
    required Color background,
    required Color surface,
    required Color onBackground,
  }) {
    final colorScheme = ColorScheme(
      brightness: brightness,
      primary: AppColors.emerald,
      onPrimary: Colors.white,
      secondary: AppColors.gold,
      onSecondary: Colors.black,
      error: AppColors.danger,
      onError: Colors.white,
      surface: surface,
      onSurface: onBackground,
    );

    // 'Inter' has no Arabic glyphs. Every text style below carries Cairo and
    // NotoNaskhArabic as fallbacks so any Arabic string in the app's own
    // chrome (not just canvas content, which sets its font explicitly)
    // renders correctly instead of showing tofu boxes — Flutter substitutes
    // per-glyph from the fallback list rather than needing the whole run to
    // be in one font.
    const arabicFallback = ['Cairo', 'NotoNaskhArabic'];

    final baseTextTheme = ThemeData(brightness: brightness).textTheme;
    final textTheme = baseTextTheme
        .apply(
          fontFamily: 'Inter',
          fontFamilyFallback: arabicFallback,
          bodyColor: onBackground,
          displayColor: onBackground,
        )
        .copyWith(
          headlineLarge: baseTextTheme.headlineLarge?.copyWith(
            fontFamily: 'Cairo',
            fontFamilyFallback: arabicFallback,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.5,
          ),
          headlineMedium: baseTextTheme.headlineMedium?.copyWith(
            fontFamily: 'Cairo',
            fontFamilyFallback: arabicFallback,
            fontWeight: FontWeight.w700,
          ),
          titleLarge: baseTextTheme.titleLarge?.copyWith(
            fontFamily: 'Cairo',
            fontFamilyFallback: arabicFallback,
            fontWeight: FontWeight.w600,
          ),
        );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: background,
      fontFamily: 'Inter',
      textTheme: textTheme,
      splashFactory: InkSparkle.splashFactory,
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
        },
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        foregroundColor: onBackground,
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: false,
        titleTextStyle: textTheme.titleLarge,
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(
            color: onBackground.withValues(alpha: 0.06),
          ),
        ),
        clipBehavior: Clip.antiAlias,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.emerald,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          textStyle: TextStyle(
            fontFamily: 'Cairo',
            fontFamilyFallback: arabicFallback,
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: onBackground,
          side: BorderSide(color: onBackground.withValues(alpha: 0.16)),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.emerald,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: onBackground.withValues(alpha: 0.04),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: onBackground.withValues(alpha: 0.05),
        selectedColor: AppColors.emerald.withValues(alpha: 0.18),
        labelStyle: TextStyle(color: onBackground),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(100),
        ),
        side: BorderSide.none,
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: surface,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: surface,
        indicatorColor: AppColors.emerald.withValues(alpha: 0.16),
        elevation: 0,
        height: 68,
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: onBackground.withValues(alpha: 0.08),
        space: 1,
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: onBackground,
        contentTextStyle: TextStyle(color: background),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}
