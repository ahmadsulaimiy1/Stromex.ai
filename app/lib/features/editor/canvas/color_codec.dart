import 'package:flutter/material.dart';

/// Flutter's [Color] no longer exposes a stable single `.value` int on
/// every channel — encode/decode explicitly via the 0-1 float components
/// so JSON persistence survives Flutter version upgrades.
int colorToArgb(Color color) {
  int channel(double v) => (v.clamp(0.0, 1.0) * 255).round();
  return (channel(color.a) << 24) |
      (channel(color.r) << 16) |
      (channel(color.g) << 8) |
      channel(color.b);
}

Color colorFromArgb(int argb) {
  final a = ((argb >> 24) & 0xFF) / 255;
  final r = ((argb >> 16) & 0xFF) / 255;
  final g = ((argb >> 8) & 0xFF) / 255;
  final b = (argb & 0xFF) / 255;
  return Color.from(alpha: a, red: r, green: g, blue: b);
}
