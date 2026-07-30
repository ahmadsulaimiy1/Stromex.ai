import 'package:flutter/material.dart';
import '../canvas/canvas_controller.dart';
import '../canvas/canvas_model.dart';

IconData _iconForType(CanvasObjectType type) => switch (type) {
      CanvasObjectType.text => Icons.text_fields_rounded,
      CanvasObjectType.shape => Icons.category_rounded,
      CanvasObjectType.icon => Icons.emoji_symbols_rounded,
    };

String _labelFor(CanvasObject object) {
  if (object is TextObject) {
    return object.text.isEmpty ? 'Text' : object.text;
  }
  if (object is ShapeObject) return object.shapeKind.name;
  if (object is IconObjectData) return 'Icon: ${object.iconKey}';
  return 'Layer';
}

void showLayersPanelSheet(BuildContext context, CanvasController controller) {
  showModalBottomSheet(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (context) {
      return AnimatedBuilder(
        animation: controller,
        builder: (context, _) {
          final layers = controller.document.objects.reversed.toList();
          return SafeArea(
            child: SizedBox(
              height: MediaQuery.of(context).size.height * 0.6,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Text('Layers', style: Theme.of(context).textTheme.titleLarge),
                  ),
                  const SizedBox(height: 8),
                  Expanded(
                    child: layers.isEmpty
                        ? Center(
                            child: Text(
                              'Nothing on the canvas yet',
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            itemCount: layers.length,
                            itemBuilder: (context, index) {
                              final object = layers[index];
                              final isSelected = controller.selectedId == object.id;
                              return ListTile(
                                selected: isSelected,
                                selectedTileColor:
                                    Theme.of(context).colorScheme.primary.withValues(alpha: 0.08),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                leading: Icon(_iconForType(object.type)),
                                title: Text(
                                  _labelFor(object),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                onTap: () => controller.select(object.id),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    IconButton(
                                      icon: Icon(object.visible
                                          ? Icons.visibility_rounded
                                          : Icons.visibility_off_rounded),
                                      onPressed: () => controller.toggleVisibility(object.id),
                                    ),
                                    IconButton(
                                      icon: Icon(
                                          object.locked ? Icons.lock_rounded : Icons.lock_open_rounded),
                                      onPressed: () => controller.toggleLock(object.id),
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.delete_outline_rounded),
                                      onPressed: () => controller.removeObject(object.id),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                  ),
                ],
              ),
            ),
          );
        },
      );
    },
  );
}
