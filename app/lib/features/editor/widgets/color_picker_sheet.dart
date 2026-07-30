import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import '../../../core/theme/app_colors.dart';

Future<Color?> showAppColorPicker(BuildContext context, {Color? initial}) {
  Color selected = initial ?? AppColors.emerald;
  return showModalBottomSheet<Color>(
    context: context,
    showDragHandle: true,
    builder: (context) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Color', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: AppColors.canvasPaletteDefaults.map((c) {
                  return GestureDetector(
                    onTap: () => Navigator.of(context).pop(c),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: c,
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.black.withValues(alpha: 0.08)),
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
              const Divider(),
              const SizedBox(height: 8),
              Text('Custom', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              ColorPicker(
                pickerColor: selected,
                onColorChanged: (c) => selected = c,
                enableAlpha: true,
                labelTypes: const [],
                pickerAreaHeightPercent: 0.7,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).pop(selected),
                  child: const Text('Apply'),
                ),
              ),
            ],
          ),
        ),
      );
    },
  );
}
