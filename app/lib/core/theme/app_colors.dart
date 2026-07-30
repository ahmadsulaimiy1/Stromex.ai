import 'package:flutter/material.dart';

/// TASMIM brand palette — deep emerald + gold, inspired by the Editorial
/// Bible's "premium, elegant, prestigious" visual personality.
class AppColors {
  AppColors._();

  static const Color emerald = Color(0xFF0B6E4F);
  static const Color emeraldDark = Color(0xFF063D2C);
  static const Color emeraldLight = Color(0xFF1E9C74);
  static const Color gold = Color(0xFFC9A227);
  static const Color goldLight = Color(0xFFE4C766);

  static const Color creamBackground = Color(0xFFFAF8F3);
  static const Color creamSurface = Color(0xFFFFFFFF);
  static const Color inkLight = Color(0xFF1A1D1B);

  static const Color charcoalBackground = Color(0xFF121412);
  static const Color charcoalSurface = Color(0xFF1B1E1B);
  static const Color inkDark = Color(0xFFF3F1EA);

  static const Color danger = Color(0xFFB3261E);
  static const Color success = Color(0xFF1E9C74);
  static const Color warning = Color(0xFFB8860B);

  static const List<Color> canvasPaletteDefaults = [
    emerald,
    gold,
    Color(0xFF16324F),
    Color(0xFF7A1F3D),
    Color(0xFF2E2A1F),
    Colors.white,
    Colors.black,
  ];
}
