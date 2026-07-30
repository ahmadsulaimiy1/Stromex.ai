import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tasmim/features/editor/canvas/canvas_model.dart';
import 'package:tasmim/features/editor/canvas/color_codec.dart';

void main() {
  group('color codec', () {
    test('round-trips ARGB through encode/decode', () {
      const original = Color(0xFFC9A227);
      final encoded = colorToArgb(original);
      final decoded = colorFromArgb(encoded);
      expect(decoded.toARGB32(), original.toARGB32());
    });
  });

  group('CanvasDocument serialization', () {
    test('round-trips a document with every object type through JSON', () {
      final document = CanvasDocument(
        title: 'Test Design',
        canvasWidth: 1080,
        canvasHeight: 1080,
        backgroundColor: const Color(0xFFFAF8F3),
        category: 'islamic-flyer',
        objects: [
          TextObject(
            x: 10,
            y: 20,
            width: 300,
            height: 80,
            text: 'دعوة إلى الإفطار',
            fontFamily: 'Amiri',
            textDirection: TextDirection.rtl,
            textAlign: TextAlign.center,
          ),
          ShapeObject(
            x: 0,
            y: 0,
            width: 100,
            height: 100,
            shapeKind: ShapeKind.roundedRectangle,
            fillColor: const Color(0xFF0B6E4F),
            cornerRadius: 12,
          ),
          IconObjectData(
            x: 5,
            y: 5,
            width: 40,
            height: 40,
            iconKey: 'crescent',
            color: const Color(0xFFC9A227),
          ),
        ],
      );

      final json = document.toJson();
      final restored = CanvasDocument.fromJson(json);

      expect(restored.title, document.title);
      expect(restored.canvasWidth, document.canvasWidth);
      expect(restored.category, 'islamic-flyer');
      expect(restored.objects, hasLength(3));

      final restoredText = restored.objects[0] as TextObject;
      expect(restoredText.text, 'دعوة إلى الإفطار');
      expect(restoredText.textDirection, TextDirection.rtl);

      final restoredShape = restored.objects[1] as ShapeObject;
      expect(restoredShape.shapeKind, ShapeKind.roundedRectangle);
      expect(restoredShape.cornerRadius, 12);

      final restoredIcon = restored.objects[2] as IconObjectData;
      expect(restoredIcon.iconKey, 'crescent');
    });
  });

  group('CanvasSizePreset', () {
    test('blank() creates a document sized to the chosen preset', () {
      final doc = CanvasDocument.blank(title: 'New', preset: CanvasSizePreset.story);
      expect(doc.canvasWidth, CanvasSizePreset.story.width);
      expect(doc.canvasHeight, CanvasSizePreset.story.height);
      expect(doc.objects, isEmpty);
    });
  });
}
