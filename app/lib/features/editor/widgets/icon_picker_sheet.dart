import 'package:flutter/material.dart';
import '../../../shared/widgets/islamic_icons.dart';

Future<String?> showIconPickerSheet(BuildContext context) {
  return showModalBottomSheet<String>(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (context) {
      return DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) {
          return SafeArea(
            child: ListView(
              controller: scrollController,
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
              children: [
                Text('Add Icon', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text(
                  'Islamic iconography',
                  style: Theme.of(context)
                      .textTheme
                      .labelMedium
                      ?.copyWith(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5)),
                ),
                const SizedBox(height: 10),
                _iconGrid(context, IconRegistry.islamicIcons.keys.toList()),
                const SizedBox(height: 20),
                Text(
                  'General',
                  style: Theme.of(context)
                      .textTheme
                      .labelMedium
                      ?.copyWith(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5)),
                ),
                const SizedBox(height: 10),
                _iconGrid(context, IconRegistry.materialIcons.keys.toList()),
              ],
            ),
          );
        },
      );
    },
  );
}

Widget _iconGrid(BuildContext context, List<String> keys) {
  return GridView.count(
    crossAxisCount: 5,
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    mainAxisSpacing: 10,
    crossAxisSpacing: 10,
    children: keys.map((key) {
      return Material(
        color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: () => Navigator.of(context).pop(key),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: IconRegistry.render(key, size: 26, color: Theme.of(context).colorScheme.primary),
          ),
        ),
      );
    }).toList(),
  );
}
