// Generates the TASMIM app icon procedurally (no external image assets) —
// an emerald field with a gold crescent-and-star mark, matching the
// in-app IslamicIcon glyph. Run with: dart run tool/generate_icon.dart
import 'dart:io';
import 'dart:math' as math;
import 'package:image/image.dart' as img;

void main() {
  const size = 1024;
  final image = img.Image(width: size, height: size, numChannels: 4);

  final emerald = img.ColorRgb8(0x0B, 0x6E, 0x4F);
  final emeraldDark = img.ColorRgb8(0x06, 0x3D, 0x2C);
  final gold = img.ColorRgb8(0xC9, 0xA2, 0x27);

  // Radial-ish background: fill emerald, then a soft darker vignette ring.
  img.fill(image, color: emerald);
  for (int y = 0; y < size; y++) {
    for (int x = 0; x < size; x++) {
      final dx = x - size / 2;
      final dy = y - size / 2;
      final dist = math.sqrt(dx * dx + dy * dy) / (size / 2);
      if (dist > 0.78) {
        final t = ((dist - 0.78) / 0.22).clamp(0.0, 1.0);
        final r = _lerp(emerald.r.toInt(), emeraldDark.r.toInt(), t);
        final g = _lerp(emerald.g.toInt(), emeraldDark.g.toInt(), t);
        final b = _lerp(emerald.b.toInt(), emeraldDark.b.toInt(), t);
        image.setPixelRgb(x, y, r, g, b);
      }
    }
  }

  // Crescent: big gold circle minus an offset circle cut-out (back to
  // emerald), matching the in-app IslamicIconKind.crescent construction.
  final cx = size * 0.46;
  final cy = size * 0.44;
  final outerR = size * 0.27;
  final cutCx = cx + outerR * 0.42;
  final cutCy = cy - outerR * 0.05;
  final cutR = outerR * 0.82;

  for (int y = 0; y < size; y++) {
    for (int x = 0; x < size; x++) {
      final inOuter = _inCircle(x.toDouble(), y.toDouble(), cx, cy, outerR);
      final inCut = _inCircle(x.toDouble(), y.toDouble(), cutCx, cutCy, cutR);
      if (inOuter && !inCut) {
        image.setPixelRgb(x, y, gold.r, gold.g, gold.b);
      }
    }
  }

  // Small 4-point star accent near the crescent's lower tip.
  _drawStar(image, size * 0.34, size * 0.62, size * 0.055, size * 0.022, 4, gold);

  final png = img.encodePng(image);
  final outFile = File('assets/icon/icon.png');
  outFile.writeAsBytesSync(png);
  // ignore: avoid_print
  print('Wrote ${outFile.path} (${png.length} bytes)');
}

int _lerp(int a, int b, double t) => (a + (b - a) * t).round();

bool _inCircle(double x, double y, double cx, double cy, double r) {
  final dx = x - cx;
  final dy = y - cy;
  return dx * dx + dy * dy <= r * r;
}

void _drawStar(img.Image image, double cx, double cy, double outerR, double innerR,
    int points, img.Color color) {
  final path = <List<double>>[];
  for (int i = 0; i < points * 2; i++) {
    final r = i.isEven ? outerR : innerR;
    final angle = (i * math.pi / points) - math.pi / 2;
    path.add([cx + r * math.cos(angle), cy + r * math.sin(angle)]);
  }
  final minX = path.map((p) => p[0]).reduce(math.min).floor();
  final maxX = path.map((p) => p[0]).reduce(math.max).ceil();
  final minY = path.map((p) => p[1]).reduce(math.min).floor();
  final maxY = path.map((p) => p[1]).reduce(math.max).ceil();

  for (int y = minY; y <= maxY; y++) {
    for (int x = minX; x <= maxX; x++) {
      if (_pointInPolygon(x.toDouble(), y.toDouble(), path)) {
        image.setPixelRgb(x, y, color.r, color.g, color.b);
      }
    }
  }
}

bool _pointInPolygon(double x, double y, List<List<double>> polygon) {
  bool inside = false;
  for (int i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    final xi = polygon[i][0], yi = polygon[i][1];
    final xj = polygon[j][0], yj = polygon[j][1];
    final intersect = ((yi > y) != (yj > y)) &&
        (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}
