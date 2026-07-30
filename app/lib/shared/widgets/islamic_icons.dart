import 'dart:math' as math;
import 'package:flutter/material.dart';

/// TASMIM's small hand-drawn Islamic iconography set — vector, not raster,
/// so it scales cleanly on the canvas at any size. This is a deliberately
/// narrow MVP set (Islamic Creative Suite, Tier A per the Feature
/// Prioritization Framework), not the full geometric pattern generator
/// described in the Phase 2 architecture.
enum IslamicIconKind {
  crescent,
  starEight,
  mosqueDome,
  lantern,
  minaret,
  ornamentDivider,
}

class IslamicIconPainter extends CustomPainter {
  IslamicIconPainter(this.kind, this.color);

  final IslamicIconKind kind;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;
    switch (kind) {
      case IslamicIconKind.crescent:
        _paintCrescent(canvas, size, paint);
      case IslamicIconKind.starEight:
        _paintStar(canvas, size, paint, points: 8);
      case IslamicIconKind.mosqueDome:
        _paintDome(canvas, size, paint);
      case IslamicIconKind.lantern:
        _paintLantern(canvas, size, paint);
      case IslamicIconKind.minaret:
        _paintMinaret(canvas, size, paint);
      case IslamicIconKind.ornamentDivider:
        _paintDivider(canvas, size, paint);
    }
  }

  void _paintCrescent(Canvas canvas, Size size, Paint paint) {
    final r = size.width / 2;
    final outer = Path()
      ..addOval(Rect.fromCircle(center: Offset(r, r), radius: r));
    final inner = Path()
      ..addOval(Rect.fromCircle(
          center: Offset(r + r * 0.42, r - r * 0.05), radius: r * 0.82));
    final crescent = Path.combine(PathOperation.difference, outer, inner);
    canvas.drawPath(crescent, paint);
    final starCenter = Offset(r * 0.55, r * 0.9);
    canvas.drawPath(_starPath(starCenter, r * 0.16, r * 0.07, 4), paint);
  }

  void _paintStar(Canvas canvas, Size size, Paint paint, {int points = 8}) {
    final center = Offset(size.width / 2, size.height / 2);
    final outerR = size.width / 2;
    final innerR = outerR * 0.42;
    canvas.drawPath(_starPath(center, outerR, innerR, points), paint);
  }

  Path _starPath(Offset center, double outerR, double innerR, int points) {
    final path = Path();
    final step = math.pi / points;
    for (int i = 0; i < points * 2; i++) {
      final r = i.isEven ? outerR : innerR;
      final angle = i * step - math.pi / 2;
      final point = Offset(
        center.dx + r * math.cos(angle),
        center.dy + r * math.sin(angle),
      );
      if (i == 0) {
        path.moveTo(point.dx, point.dy);
      } else {
        path.lineTo(point.dx, point.dy);
      }
    }
    path.close();
    return path;
  }

  void _paintDome(Canvas canvas, Size size, Paint paint) {
    final w = size.width;
    final h = size.height;
    final domePath = Path()
      ..moveTo(w * 0.15, h * 0.55)
      ..cubicTo(w * 0.15, h * 0.15, w * 0.85, h * 0.15, w * 0.85, h * 0.55)
      ..lineTo(w * 0.15, h * 0.55)
      ..close();
    canvas.drawPath(domePath, paint);
    canvas.drawRect(Rect.fromLTWH(w * 0.1, h * 0.55, w * 0.8, h * 0.14), paint);
    canvas.drawRect(Rect.fromLTWH(w * 0.02, h * 0.69, w * 0.96, h * 0.1), paint);
    for (final dx in [0.12, 0.42, 0.72]) {
      canvas.drawRect(
          Rect.fromLTWH(w * dx, h * 0.79, w * 0.16, h * 0.19), paint);
    }
    canvas.drawCircle(Offset(w * 0.5, h * 0.08), w * 0.035, paint);
    canvas.drawLine(Offset(w * 0.5, h * 0.03), Offset(w * 0.5, h * 0.17),
        paint..strokeWidth = w * 0.03..style = PaintingStyle.stroke);
  }

  void _paintLantern(Canvas canvas, Size size, Paint paint) {
    final w = size.width;
    final h = size.height;
    canvas.drawRect(Rect.fromLTWH(w * 0.42, h * 0.02, w * 0.16, h * 0.08), paint);
    final body = RRect.fromRectAndRadius(
        Rect.fromLTWH(w * 0.2, h * 0.12, w * 0.6, h * 0.6),
        Radius.circular(w * 0.1));
    canvas.drawRRect(body, paint);
    canvas.drawRect(Rect.fromLTWH(w * 0.3, h * 0.74, w * 0.4, h * 0.06), paint);
    final path = Path()
      ..moveTo(w * 0.38, h * 0.8)
      ..lineTo(w * 0.62, h * 0.8)
      ..lineTo(w * 0.5, h * 0.98)
      ..close();
    canvas.drawPath(path, paint);
  }

  void _paintMinaret(Canvas canvas, Size size, Paint paint) {
    final w = size.width;
    final h = size.height;
    canvas.drawRect(Rect.fromLTWH(w * 0.35, h * 0.25, w * 0.3, h * 0.65), paint);
    canvas.drawRect(Rect.fromLTWH(w * 0.28, h * 0.18, w * 0.44, h * 0.08), paint);
    final cap = Path()
      ..moveTo(w * 0.32, h * 0.18)
      ..lineTo(w * 0.5, h * 0.02)
      ..lineTo(w * 0.68, h * 0.18)
      ..close();
    canvas.drawPath(cap, paint);
    canvas.drawRect(Rect.fromLTWH(w * 0.25, h * 0.88, w * 0.5, h * 0.08), paint);
  }

  void _paintDivider(Canvas canvas, Size size, Paint paint) {
    final w = size.width;
    final h = size.height;
    final strokePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = h * 0.08;
    canvas.drawLine(Offset(0, h / 2), Offset(w * 0.38, h / 2), strokePaint);
    canvas.drawLine(Offset(w * 0.62, h / 2), Offset(w, h / 2), strokePaint);
    canvas.drawPath(_starPath(Offset(w / 2, h / 2), h * 0.42, h * 0.18, 4), paint);
  }

  @override
  bool shouldRepaint(covariant IslamicIconPainter oldDelegate) =>
      oldDelegate.kind != kind || oldDelegate.color != color;
}

class IslamicIcon extends StatelessWidget {
  const IslamicIcon(this.kind, {super.key, this.size = 32, this.color = Colors.black});

  final IslamicIconKind kind;
  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.square(size),
      painter: IslamicIconPainter(kind, color),
    );
  }
}

/// One flat registry mapping a stable string key -> renderable icon,
/// combining curated Material glyphs with the Islamic set above. Both the
/// icon picker sheet and the canvas renderer read from here so there is
/// exactly one source of truth for "what icons exist in TASMIM".
class IconRegistry {
  IconRegistry._();

  static const Map<String, IconData> materialIcons = {
    'star': Icons.star_rounded,
    'heart': Icons.favorite_rounded,
    'check_circle': Icons.check_circle_rounded,
    'arrow_right': Icons.arrow_circle_right_rounded,
    'location': Icons.location_on_rounded,
    'calendar': Icons.calendar_month_rounded,
    'clock': Icons.access_time_rounded,
    'phone': Icons.phone_rounded,
    'email': Icons.email_rounded,
    'people': Icons.groups_rounded,
    'gift': Icons.card_giftcard_rounded,
    'megaphone': Icons.campaign_rounded,
    'book': Icons.menu_book_rounded,
    'quote': Icons.format_quote_rounded,
    'sparkle': Icons.auto_awesome_rounded,
    'flag': Icons.flag_rounded,
    'sun': Icons.wb_sunny_rounded,
    'moon': Icons.dark_mode_rounded,
    'shield': Icons.shield_rounded,
    'hand_heart': Icons.volunteer_activism_rounded,
  };

  static const Map<String, IslamicIconKind> islamicIcons = {
    'crescent': IslamicIconKind.crescent,
    'star_eight': IslamicIconKind.starEight,
    'mosque_dome': IslamicIconKind.mosqueDome,
    'lantern': IslamicIconKind.lantern,
    'minaret': IslamicIconKind.minaret,
    'ornament_divider': IslamicIconKind.ornamentDivider,
  };

  static bool isIslamic(String key) => islamicIcons.containsKey(key);

  static Widget render(String key, {required double size, required Color color}) {
    if (islamicIcons.containsKey(key)) {
      return IslamicIcon(islamicIcons[key]!, size: size, color: color);
    }
    final iconData = materialIcons[key] ?? Icons.star_rounded;
    return Icon(iconData, size: size, color: color);
  }
}
