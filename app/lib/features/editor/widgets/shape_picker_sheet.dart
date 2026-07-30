import 'package:flutter/material.dart';
import '../canvas/canvas_model.dart';

const _shapeIcons = {
  ShapeKind.rectangle: Icons.crop_square_rounded,
  ShapeKind.roundedRectangle: Icons.rounded_corner_rounded,
  ShapeKind.circle: Icons.circle_outlined,
  ShapeKind.triangle: Icons.change_history_rounded,
  ShapeKind.star: Icons.star_border_rounded,
  ShapeKind.line: Icons.horizontal_rule_rounded,
};

const _shapeLabels = {
  ShapeKind.rectangle: 'Rectangle',
  ShapeKind.roundedRectangle: 'Rounded',
  ShapeKind.circle: 'Circle',
  ShapeKind.triangle: 'Triangle',
  ShapeKind.star: 'Star',
  ShapeKind.line: 'Line',
};

Future<ShapeKind?> showShapePickerSheet(BuildContext context) {
  return showModalBottomSheet<ShapeKind>(
    context: context,
    showDragHandle: true,
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Add Shape', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            GridView.count(
              crossAxisCount: 3,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.1,
              children: ShapeKind.values.map((kind) {
                return Material(
                  color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(16),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(16),
                    onTap: () => Navigator.of(context).pop(kind),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(_shapeIcons[kind], size: 28, color: Theme.of(context).colorScheme.primary),
                        const SizedBox(height: 6),
                        Text(_shapeLabels[kind]!, style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    ),
  );
}
