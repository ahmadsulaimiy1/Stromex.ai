import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'canvas_controller.dart';
import 'canvas_model.dart';
import 'canvas_renderer.dart';

/// The live, editable canvas. A [RepaintBoundary] wraps only the real
/// document content (background + objects) so exports never include
/// selection handles; a second, un-captured layer on top handles taps,
/// drag-to-move, resize, and rotate.
class CanvasView extends StatefulWidget {
  const CanvasView({
    super.key,
    required this.controller,
    required this.exportKey,
  });

  final CanvasController controller;
  final GlobalKey exportKey;

  @override
  State<CanvasView> createState() => _CanvasViewState();
}

class _CanvasViewState extends State<CanvasView> {
  final GlobalKey _stageKey = GlobalKey();

  Offset? _dragStartGlobal;
  double _dragStartX = 0, _dragStartY = 0;
  double _dragStartWidth = 0, _dragStartHeight = 0;

  double _fitScale(BoxConstraints constraints, CanvasDocument doc) {
    final scaleW = constraints.maxWidth / doc.canvasWidth;
    final scaleH = constraints.maxHeight / doc.canvasHeight;
    return math.min(scaleW, scaleH);
  }

  Offset _stageOriginGlobal() {
    final box = _stageKey.currentContext?.findRenderObject() as RenderBox?;
    return box?.localToGlobal(Offset.zero) ?? Offset.zero;
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        final doc = widget.controller.document;
        return LayoutBuilder(
          builder: (context, constraints) {
            final scale = _fitScale(constraints, doc);
            final stageW = doc.canvasWidth * scale;
            final stageH = doc.canvasHeight * scale;
            return Center(
              child: SizedBox(
                key: _stageKey,
                width: stageW,
                height: stageH,
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Positioned.fill(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: () => widget.controller.select(null),
                      ),
                    ),
                    _buildCapturedContent(doc, scale, stageW, stageH),
                    for (final object in doc.objects)
                      if (object.visible) _buildInteractionLayer(object, scale),
                    if (widget.controller.selectedObject != null)
                      ..._buildHandles(widget.controller.selectedObject!, scale),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildCapturedContent(
      CanvasDocument doc, double scale, double stageW, double stageH) {
    return RepaintBoundary(
      key: widget.exportKey,
      child: Container(
        width: stageW,
        height: stageH,
        color: doc.backgroundColor,
        child: Stack(
          children: [
            for (final object in doc.objects)
              if (object.visible)
                Positioned(
                  left: object.x * scale,
                  top: object.y * scale,
                  width: object.width * scale,
                  height: object.height * scale,
                  child: Transform.rotate(
                    angle: object.rotation,
                    child: _scaledRender(object, scale),
                  ),
                ),
          ],
        ),
      ),
    );
  }

  Widget _scaledRender(CanvasObject object, double scale) {
    if (scale == 1.0) return CanvasObjectRenderer(object: object);
    final scaled = object.clone();
    if (scaled is TextObject) {
      scaled.fontSize = scaled.fontSize * scale;
      scaled.letterSpacing = scaled.letterSpacing * scale;
    }
    return CanvasObjectRenderer(object: scaled);
  }

  Widget _buildInteractionLayer(CanvasObject object, double scale) {
    final isSelected = widget.controller.selectedId == object.id;
    return Positioned(
      left: object.x * scale,
      top: object.y * scale,
      width: object.width * scale,
      height: object.height * scale,
      child: Transform.rotate(
        angle: object.rotation,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: object.locked ? null : () => widget.controller.select(object.id),
          onPanStart: object.locked
              ? null
              : (details) {
                  widget.controller.select(object.id);
                  widget.controller.beginTransform();
                  _dragStartGlobal = details.globalPosition;
                  _dragStartX = object.x;
                  _dragStartY = object.y;
                },
          onPanUpdate: object.locked
              ? null
              : (details) {
                  if (_dragStartGlobal == null) return;
                  final delta = details.globalPosition - _dragStartGlobal!;
                  widget.controller.updateTransform(
                    object.id,
                    x: _dragStartX + delta.dx / scale,
                    y: _dragStartY + delta.dy / scale,
                  );
                },
          onPanEnd: (_) => _dragStartGlobal = null,
          child: Container(
            decoration: BoxDecoration(
              border: isSelected
                  ? Border.all(
                      color: Theme.of(context).colorScheme.primary, width: 2)
                  : null,
            ),
          ),
        ),
      ),
    );
  }

  List<Widget> _buildHandles(CanvasObject object, double scale) {
    if (object.locked) return const [];
    final left = object.x * scale;
    final top = object.y * scale;
    final w = object.width * scale;
    final h = object.height * scale;
    final center = Offset(left + w / 2, top + h / 2);

    return [
      // Resize handle (bottom-right).
      Positioned(
        left: left + w - 14,
        top: top + h - 14,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onPanStart: (details) {
            widget.controller.beginTransform();
            _dragStartGlobal = details.globalPosition;
            _dragStartWidth = object.width;
            _dragStartHeight = object.height;
          },
          onPanUpdate: (details) {
            if (_dragStartGlobal == null) return;
            final delta = details.globalPosition - _dragStartGlobal!;
            final newWidth = math.max(24.0, _dragStartWidth + delta.dx / scale);
            final newHeight = math.max(24.0, _dragStartHeight + delta.dy / scale);
            widget.controller
                .updateTransform(object.id, width: newWidth, height: newHeight);
          },
          onPanEnd: (_) => _dragStartGlobal = null,
          child: _HandleDot(icon: Icons.open_in_full_rounded),
        ),
      ),
      // Rotate handle (above top-center).
      Positioned(
        left: center.dx - 14,
        top: top - 40,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onPanStart: (details) => widget.controller.beginTransform(),
          onPanUpdate: (details) {
            final origin = _stageOriginGlobal();
            final screenCenter = origin + center;
            final vector = details.globalPosition - screenCenter;
            final angle = math.atan2(vector.dy, vector.dx) + math.pi / 2;
            widget.controller.updateTransform(object.id, rotation: angle);
          },
          child: _HandleDot(icon: Icons.rotate_right_rounded),
        ),
      ),
    ];
  }
}

class _HandleDot extends StatelessWidget {
  const _HandleDot({required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
        shape: BoxShape.circle,
        boxShadow: const [
          BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0, 2)),
        ],
      ),
      child: Icon(icon, size: 16, color: Colors.white),
    );
  }
}
