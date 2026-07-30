import 'package:flutter/material.dart';
import '../canvas/canvas_controller.dart';
import '../canvas/canvas_model.dart';
import 'color_picker_sheet.dart';
import 'icon_picker_sheet.dart';
import 'layers_panel_sheet.dart';
import 'shape_picker_sheet.dart';

class MainToolbar extends StatelessWidget {
  const MainToolbar({super.key, required this.controller});

  final CanvasController controller;

  void _addText(BuildContext context) {
    final doc = controller.document;
    final object = TextObject(
      x: doc.canvasWidth * 0.15,
      y: doc.canvasHeight * 0.45,
      width: doc.canvasWidth * 0.7,
      height: 80,
      text: 'Tap to edit',
      fontSize: doc.canvasWidth * 0.045,
      color: const Color(0xFF1A1D1B),
      textAlign: TextAlign.center,
    );
    controller.addObject(object);
  }

  Future<void> _addShape(BuildContext context) async {
    final kind = await showShapePickerSheet(context);
    if (kind == null) return;
    final doc = controller.document;
    final size = doc.canvasWidth * 0.35;
    controller.addObject(ShapeObject(
      x: (doc.canvasWidth - size) / 2,
      y: (doc.canvasHeight - size) / 2,
      width: size,
      height: kind == ShapeKind.line ? 6 : size,
      shapeKind: kind,
      fillColor: const Color(0xFF0B6E4F),
    ));
  }

  Future<void> _addIcon(BuildContext context) async {
    final key = await showIconPickerSheet(context);
    if (key == null) return;
    final doc = controller.document;
    final size = doc.canvasWidth * 0.16;
    controller.addObject(IconObjectData(
      x: (doc.canvasWidth - size) / 2,
      y: (doc.canvasHeight - size) / 2,
      width: size,
      height: size,
      iconKey: key,
      color: const Color(0xFF0B6E4F),
    ));
  }

  Future<void> _setBackground(BuildContext context) async {
    final color = await showAppColorPicker(context, initial: controller.document.backgroundColor);
    if (color != null) controller.setBackgroundColor(color);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 84,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _ToolButton(icon: Icons.text_fields_rounded, label: 'Text', onTap: () => _addText(context)),
          _ToolButton(icon: Icons.category_rounded, label: 'Shape', onTap: () => _addShape(context)),
          _ToolButton(
              icon: Icons.emoji_symbols_rounded, label: 'Icon', onTap: () => _addIcon(context)),
          _ToolButton(
              icon: Icons.format_color_fill_rounded,
              label: 'Background',
              onTap: () => _setBackground(context)),
          _ToolButton(
              icon: Icons.layers_rounded,
              label: 'Layers',
              onTap: () => showLayersPanelSheet(context, controller)),
        ],
      ),
    );
  }
}

class _ToolButton extends StatelessWidget {
  const _ToolButton({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 4),
            Text(label, style: Theme.of(context).textTheme.labelSmall),
          ],
        ),
      ),
    );
  }
}
