import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../shared/widgets/islamic_icons.dart';
import 'canvas_model.dart';

/// Pure, non-interactive rendering of a single [CanvasObject] at whatever
/// size its parent gives it. Shared by the live editor, template gallery
/// thumbnails, and inspiration cards — one rendering code path, so a
/// thumbnail is always an accurate preview of the real design.
class CanvasObjectRenderer extends StatelessWidget {
  const CanvasObjectRenderer({super.key, required this.object});

  final CanvasObject object;

  @override
  Widget build(BuildContext context) {
    if (!object.visible) return const SizedBox.shrink();
    final content = switch (object) {
      TextObject text => _buildText(text),
      ShapeObject shape => _buildShape(shape),
      IconObjectData icon => _buildIcon(icon),
      _ => const SizedBox.shrink(),
    };
    return Opacity(opacity: object.opacity, child: content);
  }

  Widget _buildText(TextObject text) {
    return Align(
      alignment: Alignment.center,
      child: Text(
        text.text,
        textAlign: text.textAlign,
        textDirection: text.textDirection,
        style: TextStyle(
          fontFamily: text.fontFamily,
          fontSize: text.fontSize,
          fontWeight: text.fontWeight,
          color: text.color,
          letterSpacing: text.letterSpacing,
          height: text.lineHeight,
        ),
      ),
    );
  }

  Widget _buildShape(ShapeObject shape) {
    return CustomPaint(
      painter: _ShapePainter(shape),
      size: Size(shape.width, shape.height),
    );
  }

  Widget _buildIcon(IconObjectData icon) {
    return Center(
      child: IconRegistry.render(
        icon.iconKey,
        size: icon.width < icon.height ? icon.width : icon.height,
        color: icon.color,
      ),
    );
  }
}

class _ShapePainter extends CustomPainter {
  _ShapePainter(this.shape);

  final ShapeObject shape;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final fillPaint = shape.fillColor != null
        ? (Paint()
          ..color = shape.fillColor!
          ..style = PaintingStyle.fill
          ..isAntiAlias = true)
        : null;
    final strokePaint = shape.strokeColor != null && shape.strokeWidth > 0
        ? (Paint()
          ..color = shape.strokeColor!
          ..style = PaintingStyle.stroke
          ..strokeWidth = shape.strokeWidth
          ..isAntiAlias = true)
        : null;

    Path path;
    switch (shape.shapeKind) {
      case ShapeKind.rectangle:
        path = Path()..addRect(rect);
      case ShapeKind.roundedRectangle:
        path = Path()
          ..addRRect(
              RRect.fromRectAndRadius(rect, Radius.circular(shape.cornerRadius)));
      case ShapeKind.circle:
        path = Path()..addOval(rect);
      case ShapeKind.triangle:
        path = Path()
          ..moveTo(size.width / 2, 0)
          ..lineTo(size.width, size.height)
          ..lineTo(0, size.height)
          ..close();
      case ShapeKind.line:
        strokePaint?.strokeWidth = shape.strokeWidth <= 0 ? 4 : shape.strokeWidth;
        canvas.drawLine(
          Offset(0, size.height / 2),
          Offset(size.width, size.height / 2),
          strokePaint ??
              (Paint()
                ..color = shape.fillColor ?? Colors.black
                ..strokeWidth = 4),
        );
        return;
      case ShapeKind.star:
        path = _starPath(size);
    }

    if (fillPaint != null) canvas.drawPath(path, fillPaint);
    if (strokePaint != null) canvas.drawPath(path, strokePaint);
  }

  Path _starPath(Size size) {
    const points = 5;
    final center = Offset(size.width / 2, size.height / 2);
    final outerR = size.width / 2;
    final innerR = outerR * 0.42;
    final path = Path();
    for (int i = 0; i < points * 2; i++) {
      final r = i.isEven ? outerR : innerR;
      final angle = (i * math.pi / points) - math.pi / 2;
      final point = Offset(
        center.dx + r * math.cos(angle),
        center.dy + r * math.sin(angle),
      );
      i == 0 ? path.moveTo(point.dx, point.dy) : path.lineTo(point.dx, point.dy);
    }
    path.close();
    return path;
  }

  @override
  bool shouldRepaint(covariant _ShapePainter oldDelegate) => true;
}
