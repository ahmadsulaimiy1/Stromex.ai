import 'package:flutter/material.dart';
import 'canvas_model.dart';
import 'canvas_renderer.dart';

/// Renders a whole [CanvasDocument] scaled to fit whatever box it's given —
/// used for template gallery cards, saved-project thumbnails, and the
/// static preview inside pickers. Not interactive; see `CanvasView` for
/// the live, editable version used inside the editor itself.
class CanvasDocumentView extends StatelessWidget {
  const CanvasDocumentView({
    super.key,
    required this.document,
    this.borderRadius = 16,
  });

  final CanvasDocument document;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: AspectRatio(
        aspectRatio: document.aspectRatio,
        child: Container(
          color: document.backgroundColor,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final scale = constraints.maxWidth / document.canvasWidth;
              return Stack(
                children: [
                  for (final object in document.objects)
                    Positioned(
                      left: object.x * scale,
                      top: object.y * scale,
                      width: object.width * scale,
                      height: object.height * scale,
                      child: Transform.rotate(
                        angle: object.rotation,
                        child: _ScaledObject(object: object, scale: scale),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

/// Text/icon sizes live in real canvas units on the object itself; when a
/// thumbnail scales the whole stage down, font/icon sizes must scale with
/// it or a "1080px canvas" preview at 160px wide would render illegibly
/// tiny UI-sized text. This wrapper applies that scale to a clone.
class _ScaledObject extends StatelessWidget {
  const _ScaledObject({required this.object, required this.scale});

  final CanvasObject object;
  final double scale;

  @override
  Widget build(BuildContext context) {
    if (scale == 1.0) return CanvasObjectRenderer(object: object);
    final scaled = object.clone();
    if (scaled is TextObject) {
      scaled.fontSize = scaled.fontSize * scale;
      scaled.letterSpacing = scaled.letterSpacing * scale;
    }
    scaled.width = object.width * scale;
    scaled.height = object.height * scale;
    return CanvasObjectRenderer(object: scaled);
  }
}
