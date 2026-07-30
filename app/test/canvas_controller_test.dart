import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tasmim/features/editor/canvas/canvas_controller.dart';
import 'package:tasmim/features/editor/canvas/canvas_model.dart';

CanvasDocument _blankDoc() =>
    CanvasDocument.blank(title: 'Test', preset: CanvasSizePreset.social);

void main() {
  group('CanvasController', () {
    test('addObject adds, selects, and marks the document dirty', () {
      final controller = CanvasController(_blankDoc());
      expect(controller.isDirty, isFalse);

      final text = TextObject(x: 0, y: 0, width: 100, height: 40, text: 'Hello');
      controller.addObject(text);

      expect(controller.document.objects, hasLength(1));
      expect(controller.selectedId, text.id);
      expect(controller.isDirty, isTrue);
    });

    test('undo reverts the last mutation and redo reapplies it', () {
      final controller = CanvasController(_blankDoc());
      controller.addObject(TextObject(x: 0, y: 0, width: 100, height: 40, text: 'A'));
      expect(controller.document.objects, hasLength(1));

      controller.undo();
      expect(controller.document.objects, isEmpty);
      expect(controller.canRedo, isTrue);

      controller.redo();
      expect(controller.document.objects, hasLength(1));
    });

    test('removeObject clears selection when the selected object is removed', () {
      final controller = CanvasController(_blankDoc());
      final shape = ShapeObject(
        x: 0,
        y: 0,
        width: 50,
        height: 50,
        shapeKind: ShapeKind.circle,
        fillColor: Colors.red,
      );
      controller.addObject(shape);
      expect(controller.selectedId, shape.id);

      controller.removeObject(shape.id);
      expect(controller.document.objects, isEmpty);
      expect(controller.selectedId, isNull);
    });

    test('duplicateObject creates an offset copy and selects it', () {
      final controller = CanvasController(_blankDoc());
      final shape = ShapeObject(
        x: 10,
        y: 10,
        width: 50,
        height: 50,
        shapeKind: ShapeKind.circle,
        fillColor: Colors.blue,
      );
      controller.addObject(shape);
      controller.duplicateObject(shape.id);

      expect(controller.document.objects, hasLength(2));
      final duplicate = controller.document.objects.last;
      expect(duplicate.id, isNot(shape.id));
      expect(duplicate.x, shape.x + 24);
      expect(controller.selectedId, duplicate.id);
    });

    test('updateTransform moves an object without growing undo history per frame', () {
      final controller = CanvasController(_blankDoc());
      final shape = ShapeObject(
        x: 0,
        y: 0,
        width: 50,
        height: 50,
        shapeKind: ShapeKind.rectangle,
        fillColor: Colors.green,
      );
      controller.addObject(shape);
      controller.beginTransform();
      for (var i = 0; i < 5; i++) {
        controller.updateTransform(shape.id, x: i * 10.0);
      }
      expect(controller.document.objects.first.x, 40);
      // One undo should revert the whole drag gesture, not one frame of it.
      controller.undo();
      expect(controller.document.objects.first.x, 0);
    });
  });
}
