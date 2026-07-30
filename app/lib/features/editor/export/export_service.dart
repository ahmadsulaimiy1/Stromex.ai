import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:gal/gal.dart';
import 'package:image/image.dart' as img;
import 'package:share_plus/share_plus.dart';
import '../../../core/logging/app_logger.dart';

enum ExportFormat { png, jpg }

enum ExportResult { savedToGallery, shared, failed, permissionDenied }

/// Renders the editor's [RepaintBoundary] at the document's real
/// resolution — not the on-screen display size — by driving
/// `toImage(pixelRatio:)` up from whatever scale the canvas is currently
/// shown at, then encodes PNG natively or JPG via the `image` package.
class ExportService {
  static const _tag = 'ExportService';

  Future<Uint8List?> renderBytes({
    required GlobalKey boundaryKey,
    required double documentWidth,
    required ExportFormat format,
    int jpgQuality = 92,
  }) async {
    try {
      final renderObject = boundaryKey.currentContext?.findRenderObject();
      if (renderObject is! RenderRepaintBoundary) {
        AppLogger.instance.error(_tag, 'Export boundary not found in tree');
        return null;
      }
      final displayedWidth = renderObject.size.width;
      final pixelRatio =
          displayedWidth == 0 ? 1.0 : (documentWidth / displayedWidth);
      final ui.Image image =
          await renderObject.toImage(pixelRatio: pixelRatio.clamp(0.5, 6.0));
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      image.dispose();
      if (byteData == null) return null;
      final pngBytes = byteData.buffer.asUint8List();

      if (format == ExportFormat.png) return pngBytes;

      final decoded = img.decodePng(pngBytes);
      if (decoded == null) {
        AppLogger.instance.error(_tag, 'Failed to decode PNG for JPG conversion');
        return null;
      }
      final flattened = img.Image(width: decoded.width, height: decoded.height);
      img.fill(flattened, color: img.ColorRgb8(255, 255, 255));
      img.compositeImage(flattened, decoded);
      return Uint8List.fromList(img.encodeJpg(flattened, quality: jpgQuality));
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'renderBytes failed', e, st);
      return null;
    }
  }

  Future<ExportResult> saveToGallery(
      Uint8List bytes, ExportFormat format, String fileNameBase) async {
    try {
      final hasAccess = await Gal.hasAccess();
      if (!hasAccess) {
        final granted = await Gal.requestAccess();
        if (!granted) return ExportResult.permissionDenied;
      }
      await Gal.putImageBytes(bytes, album: 'TASMIM', name: fileNameBase);
      AppLogger.instance.info(_tag, 'Saved $fileNameBase to gallery');
      return ExportResult.savedToGallery;
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'saveToGallery failed', e, st);
      return ExportResult.failed;
    }
  }

  Future<ExportResult> share(
      Uint8List bytes, ExportFormat format, String fileNameBase) async {
    try {
      final ext = format == ExportFormat.png ? 'png' : 'jpg';
      final params = ShareParams(
        files: [
          XFile.fromData(bytes,
              name: '$fileNameBase.$ext',
              mimeType: format == ExportFormat.png ? 'image/png' : 'image/jpeg'),
        ],
        text: 'Made with TASMIM',
      );
      final result = await SharePlus.instance.share(params);
      if (result.status == ShareResultStatus.success) {
        return ExportResult.shared;
      }
      return ExportResult.failed;
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'share failed', e, st);
      return ExportResult.failed;
    }
  }
}
