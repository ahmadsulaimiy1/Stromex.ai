import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../editor/canvas/canvas_model.dart';

class _SizeOption {
  const _SizeOption(this.preset, this.label, this.icon);
  final CanvasSizePreset preset;
  final String label;
  final IconData icon;
}

const _sizeOptions = [
  _SizeOption(CanvasSizePreset.social, 'Social Post (1:1)', Icons.crop_square_rounded),
  _SizeOption(CanvasSizePreset.story, 'Story (9:16)', Icons.crop_portrait_rounded),
  _SizeOption(CanvasSizePreset.flyer, 'Flyer (A4)', Icons.description_rounded),
  _SizeOption(CanvasSizePreset.poster, 'Poster', Icons.image_rounded),
  _SizeOption(CanvasSizePreset.banner, 'Banner (16:9)', Icons.crop_16_9_rounded),
];

Future<void> showNewDesignSheet(BuildContext context) {
  return showModalBottomSheet(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('New Design', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Choose a canvas size to start blank.',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6)),
            ),
            const SizedBox(height: 16),
            for (final option in _sizeOptions)
              Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: ListTile(
                  leading: Icon(option.icon, color: Theme.of(context).colorScheme.primary),
                  title: Text(option.label),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () {
                    Navigator.of(context).pop();
                    final document = CanvasDocument.blank(
                      title: 'Untitled Design',
                      preset: option.preset,
                    );
                    context.push('/editor', extra: {
                      'document': document,
                      'isExisting': false,
                    });
                  },
                ),
              ),
          ],
        ),
      ),
    ),
  );
}
