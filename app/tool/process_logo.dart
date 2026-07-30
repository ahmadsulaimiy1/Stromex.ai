// Processes the supplied TASMIM logo (assets/branding/tasmim_logo_source.jpg)
// into two derived assets:
//  - tasmim_logo_full.png: tightly cropped to the full mark + wordmark,
//    transparent background, for in-app branding surfaces.
//  - tasmim_mark.png: cropped to just the emblem (above the wordmark),
//    transparent background, square-padded — used as the launcher icon
//    source, since a wordmark reads as clutter at launcher-icon sizes.
import 'dart:io';
import 'package:image/image.dart' as img;

const _brightnessThreshold = 18; // near-black cutoff

bool _isBackground(img.Pixel p) {
  final lum = 0.299 * p.r + 0.587 * p.g + 0.114 * p.b;
  return lum < _brightnessThreshold;
}

void main() {
  final src = img.decodeImage(File('assets/branding/tasmim_logo_source.jpg').readAsBytesSync())!;

  int top = src.height, bottom = 0, left = src.width, right = 0;
  for (int y = 0; y < src.height; y++) {
    for (int x = 0; x < src.width; x++) {
      if (!_isBackground(src.getPixel(x, y))) {
        if (y < top) top = y;
        if (y > bottom) bottom = y;
        if (x < left) left = x;
        if (x > right) right = x;
      }
    }
  }
  print('Full bounds: x=[$left,$right] y=[$top,$bottom]');

  // Find the vertical gap between the emblem and the wordmark: scan rows
  // in the lower half of the bounding box for the first fully-background
  // row following a non-background row.
  int splitY = bottom;
  final midY = top + ((bottom - top) * 0.45).round();
  for (int y = midY; y < bottom; y++) {
    bool rowIsBackground = true;
    for (int x = left; x <= right; x++) {
      if (!_isBackground(src.getPixel(x, y))) {
        rowIsBackground = false;
        break;
      }
    }
    if (rowIsBackground) {
      splitY = y;
      break;
    }
  }
  print('Mark/wordmark split at y=$splitY');

  Uint8ListLike cropWithAlpha(int x0, int y0, int x1, int y1) {
    final w = x1 - x0 + 1;
    final h = y1 - y0 + 1;
    final out = img.Image(width: w, height: h, numChannels: 4);
    for (int yy = 0; yy < h; yy++) {
      for (int xx = 0; xx < w; xx++) {
        final p = src.getPixel(x0 + xx, y0 + yy);
        final bg = _isBackground(p);
        out.setPixelRgba(xx, yy, p.r.toInt(), p.g.toInt(), p.b.toInt(), bg ? 0 : 255);
      }
    }
    return Uint8ListLike(out);
  }

  // Full logo (mark + wordmark), modest padding.
  final pad = ((right - left) * 0.06).round();
  final fullX0 = (left - pad).clamp(0, src.width - 1);
  final fullY0 = (top - pad).clamp(0, src.height - 1);
  final fullX1 = (right + pad).clamp(0, src.width - 1);
  final fullY1 = (bottom + pad).clamp(0, src.height - 1);
  final full = cropWithAlpha(fullX0, fullY0, fullX1, fullY1).image;
  File('assets/branding/tasmim_logo_full.png').writeAsBytesSync(img.encodePng(full));
  print('Wrote tasmim_logo_full.png ${full.width}x${full.height}');

  // Emblem-only, square-padded on transparent canvas for a clean launcher icon.
  final markPad = ((right - left) * 0.10).round();
  final markX0 = (left - markPad).clamp(0, src.width - 1);
  final markY0 = (top - markPad).clamp(0, src.height - 1);
  final markX1 = (right + markPad).clamp(0, src.width - 1);
  final markY1 = (splitY - markPad ~/ 2).clamp(0, src.height - 1);
  final mark = cropWithAlpha(markX0, markY0, markX1, markY1).image;

  final side = mark.width > mark.height ? mark.width : mark.height;
  final square = img.Image(width: side, height: side, numChannels: 4);
  img.fill(square, color: img.ColorRgba8(0, 0, 0, 0));
  img.compositeImage(
    square,
    mark,
    dstX: (side - mark.width) ~/ 2,
    dstY: (side - mark.height) ~/ 2,
  );
  File('assets/branding/tasmim_mark.png').writeAsBytesSync(img.encodePng(square));
  print('Wrote tasmim_mark.png ${square.width}x${square.height}');

  // Flat (opaque near-black background) version for the legacy/non-adaptive
  // launcher icon path, which does not support a transparent source image.
  final flat = img.Image(width: side, height: side, numChannels: 4);
  img.fill(flat, color: img.ColorRgba8(5, 7, 12, 255));
  img.compositeImage(flat, square);
  File('assets/branding/tasmim_mark_flat.png').writeAsBytesSync(img.encodePng(flat));
  print('Wrote tasmim_mark_flat.png ${flat.width}x${flat.height}');
}

// Tiny wrapper so cropWithAlpha can return an img.Image without repeating
// the type in a very long generic signature above.
class Uint8ListLike {
  Uint8ListLike(this.image);
  final img.Image image;
}
