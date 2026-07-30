import 'package:flutter/material.dart';
import '../canvas/canvas_controller.dart';
import '../canvas/canvas_model.dart';
import 'color_picker_sheet.dart';
import 'text_edit_dialog.dart';

const _fontFamilies = ['Inter', 'Cairo', 'NotoNaskhArabic', 'Amiri'];

class SelectionToolbar extends StatelessWidget {
  const SelectionToolbar({super.key, required this.controller, required this.object});

  final CanvasController controller;
  final CanvasObject object;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).colorScheme.surface,
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              height: 64,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  if (object is TextObject) ..._textControls(context, object as TextObject),
                  if (object is ShapeObject) ..._shapeControls(context, object as ShapeObject),
                  if (object is IconObjectData) ..._iconControls(context, object as IconObjectData),
                ],
              ),
            ),
            const Divider(height: 1),
            SizedBox(
              height: 56,
              child: Row(
                children: [
                  _actionButton(context, Icons.flip_to_front_rounded, 'Front',
                      () => controller.reorder(object.id, toFront: true)),
                  _actionButton(context, Icons.flip_to_back_rounded, 'Back',
                      () => controller.reorder(object.id, toFront: false)),
                  _actionButton(context, Icons.copy_rounded, 'Duplicate',
                      () => controller.duplicateObject(object.id)),
                  _actionButton(context, Icons.delete_outline_rounded, 'Delete',
                      () => controller.removeObject(object.id)),
                  const Spacer(),
                  TextButton(
                    onPressed: () => controller.select(null),
                    child: const Text('Done'),
                  ),
                  const SizedBox(width: 8),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _actionButton(BuildContext context, IconData icon, String label, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 20, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7)),
          ],
        ),
      ),
    );
  }

  List<Widget> _textControls(BuildContext context, TextObject text) {
    return [
      _chipButton(
        context,
        icon: Icons.edit_rounded,
        label: 'Edit',
        onTap: () async {
          final result = await showTextEditDialog(context, text.text);
          if (result != null) {
            controller.updateTextObject(text.id, (t) => t.text = result);
          }
        },
      ),
      _dropdownChip(
        context,
        value: text.fontFamily,
        items: _fontFamilies,
        onChanged: (v) => controller.updateTextObject(text.id, (t) => t.fontFamily = v),
      ),
      _stepperChip(
        context,
        icon: Icons.text_decrease_rounded,
        onDecrease: () => controller.updateTextObject(
            text.id, (t) => t.fontSize = (t.fontSize - 2).clamp(8, 400)),
        onIncrease: () => controller.updateTextObject(
            text.id, (t) => t.fontSize = (t.fontSize + 2).clamp(8, 400)),
      ),
      _toggleChip(
        context,
        icon: Icons.format_bold_rounded,
        selected: text.fontWeightValue >= 700,
        onTap: () => controller.updateTextObject(
            text.id, (t) => t.fontWeightValue = t.fontWeightValue >= 700 ? 400 : 700),
      ),
      _iconOnlyChip(
        context,
        icon: Icons.format_align_left_rounded,
        onTap: () => controller.updateTextObject(text.id, (t) => t.textAlign = TextAlign.left),
      ),
      _iconOnlyChip(
        context,
        icon: Icons.format_align_center_rounded,
        onTap: () => controller.updateTextObject(text.id, (t) => t.textAlign = TextAlign.center),
      ),
      _iconOnlyChip(
        context,
        icon: Icons.format_align_right_rounded,
        onTap: () => controller.updateTextObject(text.id, (t) => t.textAlign = TextAlign.right),
      ),
      _toggleChip(
        context,
        icon: Icons.format_textdirection_r_to_l_rounded,
        selected: text.textDirection == TextDirection.rtl,
        onTap: () => controller.updateTextObject(
            text.id,
            (t) => t.textDirection =
                t.textDirection == TextDirection.rtl ? TextDirection.ltr : TextDirection.rtl),
      ),
      _colorSwatchChip(
        context,
        color: text.color,
        onTap: () async {
          final c = await showAppColorPicker(context, initial: text.color);
          if (c != null) controller.updateTextObject(text.id, (t) => t.color = c);
        },
      ),
    ];
  }

  List<Widget> _shapeControls(BuildContext context, ShapeObject shape) {
    return [
      _colorSwatchChip(
        context,
        color: shape.fillColor ?? Colors.transparent,
        label: 'Fill',
        onTap: () async {
          final c = await showAppColorPicker(context, initial: shape.fillColor);
          if (c != null) controller.updateShapeObject(shape.id, (s) => s.fillColor = c);
        },
      ),
      _colorSwatchChip(
        context,
        color: shape.strokeColor ?? Colors.transparent,
        label: 'Stroke',
        onTap: () async {
          final c = await showAppColorPicker(context, initial: shape.strokeColor ?? Colors.black);
          if (c != null) {
            controller.updateShapeObject(shape.id, (s) {
              s.strokeColor = c;
              if (s.strokeWidth <= 0) s.strokeWidth = 4;
            });
          }
        },
      ),
      if (shape.shapeKind == ShapeKind.roundedRectangle)
        _stepperChip(
          context,
          icon: Icons.rounded_corner_rounded,
          onDecrease: () => controller.updateShapeObject(
              shape.id, (s) => s.cornerRadius = (s.cornerRadius - 4).clamp(0, 200)),
          onIncrease: () => controller.updateShapeObject(
              shape.id, (s) => s.cornerRadius = (s.cornerRadius + 4).clamp(0, 200)),
        ),
    ];
  }

  List<Widget> _iconControls(BuildContext context, IconObjectData icon) {
    return [
      _colorSwatchChip(
        context,
        color: icon.color,
        onTap: () async {
          final c = await showAppColorPicker(context, initial: icon.color);
          if (c != null) controller.updateIconObject(icon.id, (i) => i.color = c);
        },
      ),
    ];
  }

  Widget _chipButton(BuildContext context,
      {required IconData icon, required String label, required VoidCallback onTap}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 12),
      child: ActionChip(
        avatar: Icon(icon, size: 16),
        label: Text(label),
        onPressed: onTap,
      ),
    );
  }

  Widget _iconOnlyChip(BuildContext context, {required IconData icon, required VoidCallback onTap}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: CircleAvatar(
          radius: 18,
          backgroundColor: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
          child: Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
        ),
      ),
    );
  }

  Widget _toggleChip(BuildContext context,
      {required IconData icon, required bool selected, required VoidCallback onTap}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: CircleAvatar(
          radius: 18,
          backgroundColor: selected
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
          child: Icon(icon, size: 18, color: selected ? Colors.white : Theme.of(context).colorScheme.primary),
        ),
      ),
    );
  }

  Widget _stepperChip(BuildContext context,
      {required IconData icon, required VoidCallback onDecrease, required VoidCallback onIncrease}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      child: Row(
        children: [
          IconButton(icon: const Icon(Icons.remove_rounded), onPressed: onDecrease, iconSize: 18),
          Icon(icon, size: 18, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6)),
          IconButton(icon: const Icon(Icons.add_rounded), onPressed: onIncrease, iconSize: 18),
        ],
      ),
    );
  }

  Widget _colorSwatchChip(BuildContext context,
      {required Color color, String? label, required VoidCallback onTap}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 26,
              height: 26,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.black.withValues(alpha: 0.15)),
              ),
            ),
            if (label != null) ...[
              const SizedBox(width: 6),
              Text(label, style: Theme.of(context).textTheme.labelSmall),
            ],
          ],
        ),
      ),
    );
  }

  Widget _dropdownChip(BuildContext context,
      {required String value, required List<String> items, required void Function(String) onChanged}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 14),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          items: items
              .map((f) => DropdownMenuItem(
                    value: f,
                    child: Text(f, style: TextStyle(fontFamily: f)),
                  ))
              .toList(),
          onChanged: (v) {
            if (v != null) onChanged(v);
          },
        ),
      ),
    );
  }
}
