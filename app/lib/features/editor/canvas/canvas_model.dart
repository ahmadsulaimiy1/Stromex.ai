import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'color_codec.dart';

const _uuid = Uuid();

enum CanvasObjectType { text, shape, icon }

enum ShapeKind { rectangle, roundedRectangle, circle, line, triangle, star }

/// Base class for every element that can live on a TASMIM canvas. Kept
/// deliberately small and serializable — this is the "document model"
/// referenced throughout the architecture docs: one shape, one JSON
/// representation, reusable for templates, saved projects, and export.
abstract class CanvasObject {
  CanvasObject({
    String? id,
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    this.rotation = 0,
    this.opacity = 1,
    this.locked = false,
    this.visible = true,
  }) : id = id ?? _uuid.v4();

  final String id;
  double x;
  double y;
  double width;
  double height;
  double rotation;
  double opacity;
  bool locked;
  bool visible;

  CanvasObjectType get type;

  Rect get bounds => Rect.fromLTWH(x, y, width, height);
  Offset get center => Offset(x + width / 2, y + height / 2);

  Map<String, dynamic> toJson();

  CanvasObject clone();

  static CanvasObject fromJson(Map<String, dynamic> json) {
    final type = CanvasObjectType.values.byName(json['type'] as String);
    switch (type) {
      case CanvasObjectType.text:
        return TextObject.fromJson(json);
      case CanvasObjectType.shape:
        return ShapeObject.fromJson(json);
      case CanvasObjectType.icon:
        return IconObjectData.fromJson(json);
    }
  }

  Map<String, dynamic> _baseJson() => {
        'id': id,
        'type': type.name,
        'x': x,
        'y': y,
        'width': width,
        'height': height,
        'rotation': rotation,
        'opacity': opacity,
        'locked': locked,
        'visible': visible,
      };
}

class TextObject extends CanvasObject {
  TextObject({
    super.id,
    required super.x,
    required super.y,
    required super.width,
    required super.height,
    super.rotation,
    super.opacity,
    super.locked,
    super.visible,
    required this.text,
    this.fontFamily = 'Inter',
    this.fontSize = 24,
    this.fontWeightValue = 600,
    this.color = const Color(0xFF1A1D1B),
    this.textAlign = TextAlign.left,
    this.textDirection = TextDirection.ltr,
    this.letterSpacing = 0,
    this.lineHeight = 1.2,
  });

  String text;
  String fontFamily;
  double fontSize;
  int fontWeightValue; // 100-900
  Color color;
  TextAlign textAlign;
  TextDirection textDirection;
  double letterSpacing;
  double lineHeight;

  FontWeight get fontWeight => FontWeight.values.firstWhere(
        (w) => w.value == fontWeightValue,
        orElse: () => FontWeight.w600,
      );

  @override
  CanvasObjectType get type => CanvasObjectType.text;

  @override
  Map<String, dynamic> toJson() => {
        ..._baseJson(),
        'text': text,
        'fontFamily': fontFamily,
        'fontSize': fontSize,
        'fontWeight': fontWeightValue,
        'color': colorToArgb(color),
        'textAlign': textAlign.name,
        'textDirection': textDirection.name,
        'letterSpacing': letterSpacing,
        'lineHeight': lineHeight,
      };

  factory TextObject.fromJson(Map<String, dynamic> json) => TextObject(
        id: json['id'] as String,
        x: (json['x'] as num).toDouble(),
        y: (json['y'] as num).toDouble(),
        width: (json['width'] as num).toDouble(),
        height: (json['height'] as num).toDouble(),
        rotation: (json['rotation'] as num?)?.toDouble() ?? 0,
        opacity: (json['opacity'] as num?)?.toDouble() ?? 1,
        locked: json['locked'] as bool? ?? false,
        visible: json['visible'] as bool? ?? true,
        text: json['text'] as String,
        fontFamily: json['fontFamily'] as String? ?? 'Inter',
        fontSize: (json['fontSize'] as num?)?.toDouble() ?? 24,
        fontWeightValue: json['fontWeight'] as int? ?? 600,
        color: colorFromArgb(json['color'] as int? ?? 0xFF1A1D1B),
        textAlign: TextAlign.values.byName(json['textAlign'] as String? ?? 'left'),
        textDirection: TextDirection.values
            .byName(json['textDirection'] as String? ?? 'ltr'),
        letterSpacing: (json['letterSpacing'] as num?)?.toDouble() ?? 0,
        lineHeight: (json['lineHeight'] as num?)?.toDouble() ?? 1.2,
      );

  @override
  TextObject clone() => TextObject(
        x: x,
        y: y,
        width: width,
        height: height,
        rotation: rotation,
        opacity: opacity,
        locked: locked,
        visible: visible,
        text: text,
        fontFamily: fontFamily,
        fontSize: fontSize,
        fontWeightValue: fontWeightValue,
        color: color,
        textAlign: textAlign,
        textDirection: textDirection,
        letterSpacing: letterSpacing,
        lineHeight: lineHeight,
      );
}

class ShapeObject extends CanvasObject {
  ShapeObject({
    super.id,
    required super.x,
    required super.y,
    required super.width,
    required super.height,
    super.rotation,
    super.opacity,
    super.locked,
    super.visible,
    required this.shapeKind,
    this.fillColor = const Color(0xFF0B6E4F),
    this.strokeColor,
    this.strokeWidth = 0,
    this.cornerRadius = 16,
  });

  ShapeKind shapeKind;
  Color? fillColor;
  Color? strokeColor;
  double strokeWidth;
  double cornerRadius;

  @override
  CanvasObjectType get type => CanvasObjectType.shape;

  @override
  Map<String, dynamic> toJson() => {
        ..._baseJson(),
        'shapeKind': shapeKind.name,
        'fillColor': fillColor != null ? colorToArgb(fillColor!) : null,
        'strokeColor': strokeColor != null ? colorToArgb(strokeColor!) : null,
        'strokeWidth': strokeWidth,
        'cornerRadius': cornerRadius,
      };

  factory ShapeObject.fromJson(Map<String, dynamic> json) => ShapeObject(
        id: json['id'] as String,
        x: (json['x'] as num).toDouble(),
        y: (json['y'] as num).toDouble(),
        width: (json['width'] as num).toDouble(),
        height: (json['height'] as num).toDouble(),
        rotation: (json['rotation'] as num?)?.toDouble() ?? 0,
        opacity: (json['opacity'] as num?)?.toDouble() ?? 1,
        locked: json['locked'] as bool? ?? false,
        visible: json['visible'] as bool? ?? true,
        shapeKind: ShapeKind.values.byName(json['shapeKind'] as String),
        fillColor: json['fillColor'] != null
            ? colorFromArgb(json['fillColor'] as int)
            : null,
        strokeColor: json['strokeColor'] != null
            ? colorFromArgb(json['strokeColor'] as int)
            : null,
        strokeWidth: (json['strokeWidth'] as num?)?.toDouble() ?? 0,
        cornerRadius: (json['cornerRadius'] as num?)?.toDouble() ?? 16,
      );

  @override
  ShapeObject clone() => ShapeObject(
        x: x,
        y: y,
        width: width,
        height: height,
        rotation: rotation,
        opacity: opacity,
        locked: locked,
        visible: visible,
        shapeKind: shapeKind,
        fillColor: fillColor,
        strokeColor: strokeColor,
        strokeWidth: strokeWidth,
        cornerRadius: cornerRadius,
      );
}

/// Bundled icon glyph placed on the canvas — either a Material glyph or one
/// of TASMIM's hand-drawn Islamic iconography set (see
/// `shared/widgets/islamic_icons.dart`), referenced by a stable string key
/// so both families share one serialization path.
class IconObjectData extends CanvasObject {
  IconObjectData({
    super.id,
    required super.x,
    required super.y,
    required super.width,
    required super.height,
    super.rotation,
    super.opacity,
    super.locked,
    super.visible,
    required this.iconKey,
    this.color = const Color(0xFF0B6E4F),
  });

  String iconKey;
  Color color;

  @override
  CanvasObjectType get type => CanvasObjectType.icon;

  @override
  Map<String, dynamic> toJson() => {
        ..._baseJson(),
        'iconKey': iconKey,
        'color': colorToArgb(color),
      };

  factory IconObjectData.fromJson(Map<String, dynamic> json) =>
      IconObjectData(
        id: json['id'] as String,
        x: (json['x'] as num).toDouble(),
        y: (json['y'] as num).toDouble(),
        width: (json['width'] as num).toDouble(),
        height: (json['height'] as num).toDouble(),
        rotation: (json['rotation'] as num?)?.toDouble() ?? 0,
        opacity: (json['opacity'] as num?)?.toDouble() ?? 1,
        locked: json['locked'] as bool? ?? false,
        visible: json['visible'] as bool? ?? true,
        iconKey: json['iconKey'] as String,
        color: colorFromArgb(json['color'] as int? ?? 0xFF0B6E4F),
      );

  @override
  IconObjectData clone() => IconObjectData(
        x: x,
        y: y,
        width: width,
        height: height,
        rotation: rotation,
        opacity: opacity,
        locked: locked,
        visible: visible,
        iconKey: iconKey,
        color: color,
      );
}

/// A full design: canvas size, background, and an ordered stack of objects
/// (list order = z-order, index 0 painted first). Every template, every
/// saved project, and every export renders from exactly this structure.
class CanvasDocument {
  CanvasDocument({
    String? id,
    required this.title,
    required this.canvasWidth,
    required this.canvasHeight,
    this.backgroundColor = const Color(0xFFFFFFFF),
    List<CanvasObject>? objects,
    this.category = 'general',
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : id = id ?? _uuid.v4(),
        objects = objects ?? [],
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  final String id;
  String title;
  double canvasWidth;
  double canvasHeight;
  Color backgroundColor;
  List<CanvasObject> objects;
  String category;
  DateTime createdAt;
  DateTime updatedAt;

  double get aspectRatio => canvasWidth / canvasHeight;

  CanvasDocument deepClone() => CanvasDocument(
        id: id,
        title: title,
        canvasWidth: canvasWidth,
        canvasHeight: canvasHeight,
        backgroundColor: backgroundColor,
        objects: objects.map((o) => o.clone()).toList(),
        category: category,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'canvasWidth': canvasWidth,
        'canvasHeight': canvasHeight,
        'backgroundColor': colorToArgb(backgroundColor),
        'objects': objects.map((o) => o.toJson()).toList(),
        'category': category,
        'createdAt': createdAt.toIso8601String(),
        'updatedAt': updatedAt.toIso8601String(),
      };

  factory CanvasDocument.fromJson(Map<String, dynamic> json) =>
      CanvasDocument(
        id: json['id'] as String,
        title: json['title'] as String,
        canvasWidth: (json['canvasWidth'] as num).toDouble(),
        canvasHeight: (json['canvasHeight'] as num).toDouble(),
        backgroundColor: colorFromArgb(json['backgroundColor'] as int),
        objects: (json['objects'] as List<dynamic>)
            .map((o) => CanvasObject.fromJson(o as Map<String, dynamic>))
            .toList(),
        category: json['category'] as String? ?? 'general',
        createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ??
            DateTime.now(),
        updatedAt: DateTime.tryParse(json['updatedAt'] as String? ?? '') ??
            DateTime.now(),
      );

  /// A blank canvas at a named preset size (flyer, social post, story...).
  factory CanvasDocument.blank({
    required String title,
    required CanvasSizePreset preset,
    String category = 'general',
  }) =>
      CanvasDocument(
        title: title,
        canvasWidth: preset.width,
        canvasHeight: preset.height,
        category: category,
      );
}

class CanvasSizePreset {
  const CanvasSizePreset(this.labelKey, this.width, this.height);

  final String labelKey;
  final double width;
  final double height;

  static const social = CanvasSizePreset('sizeSocialPost', 1080, 1080);
  static const story = CanvasSizePreset('sizeStory', 1080, 1920);
  static const flyer = CanvasSizePreset('sizeFlyer', 1240, 1748);
  static const poster = CanvasSizePreset('sizePoster', 1500, 2100);
  static const banner = CanvasSizePreset('sizeBanner', 1600, 900);

  static const all = [social, story, flyer, poster, banner];
}
