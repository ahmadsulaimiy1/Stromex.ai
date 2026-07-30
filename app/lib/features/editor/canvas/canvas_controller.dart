import 'dart:collection';
import 'package:flutter/material.dart';
import '../../../core/logging/app_logger.dart';
import 'canvas_model.dart';

/// Owns one open [CanvasDocument] and every mutation made to it: selection,
/// add/remove/reorder, transform, and a bounded undo/redo history. Every
/// editor widget reads through this controller rather than touching the
/// document directly, so "no broken workflows" has a single enforcement
/// point.
class CanvasController extends ChangeNotifier {
  CanvasController(CanvasDocument document) : _document = document;

  static const _tag = 'CanvasController';
  static const int _maxHistory = 60;

  CanvasDocument _document;
  CanvasDocument get document => _document;

  String? _selectedId;
  String? get selectedId => _selectedId;

  CanvasObject? get selectedObject {
    if (_selectedId == null) return null;
    try {
      return _document.objects.firstWhere((o) => o.id == _selectedId);
    } catch (_) {
      return null;
    }
  }

  final ListQueue<CanvasDocument> _undoStack = ListQueue<CanvasDocument>();
  final ListQueue<CanvasDocument> _redoStack = ListQueue<CanvasDocument>();

  bool get canUndo => _undoStack.isNotEmpty;
  bool get canRedo => _redoStack.isNotEmpty;

  bool _dirty = false;
  bool get isDirty => _dirty;

  void _pushHistory() {
    _undoStack.add(_document.deepClone());
    while (_undoStack.length > _maxHistory) {
      _undoStack.removeFirst();
    }
    _redoStack.clear();
  }

  void _commit({bool recordHistory = true, bool markDirty = true}) {
    if (recordHistory) {
      // history snapshot already taken before mutation by caller
    }
    if (markDirty) _dirty = true;
    _document.updatedAt = DateTime.now();
    notifyListeners();
  }

  void undo() {
    if (_undoStack.isEmpty) return;
    _redoStack.add(_document.deepClone());
    _document = _undoStack.removeLast();
    _dirty = true;
    notifyListeners();
  }

  void redo() {
    if (_redoStack.isEmpty) return;
    _undoStack.add(_document.deepClone());
    _document = _redoStack.removeLast();
    _dirty = true;
    notifyListeners();
  }

  void select(String? id) {
    _selectedId = id;
    notifyListeners();
  }

  void addObject(CanvasObject object, {bool select = true}) {
    _pushHistory();
    _document.objects.add(object);
    if (select) _selectedId = object.id;
    AppLogger.instance.debug(_tag, 'Added ${object.type.name} ${object.id}');
    _commit();
  }

  void removeObject(String id) {
    _pushHistory();
    _document.objects.removeWhere((o) => o.id == id);
    if (_selectedId == id) _selectedId = null;
    _commit();
  }

  void duplicateObject(String id) {
    final source = _document.objects.where((o) => o.id == id).firstOrNull;
    if (source == null) return;
    _pushHistory();
    final copy = source.clone()
      ..x = source.x + 24
      ..y = source.y + 24;
    _document.objects.add(copy);
    _selectedId = copy.id;
    _commit();
  }

  void reorder(String id, {required bool toFront}) {
    final index = _document.objects.indexWhere((o) => o.id == id);
    if (index == -1) return;
    _pushHistory();
    final obj = _document.objects.removeAt(index);
    if (toFront) {
      _document.objects.add(obj);
    } else {
      _document.objects.insert(0, obj);
    }
    _commit();
  }

  void moveLayer(String id, {required bool up}) {
    final index = _document.objects.indexWhere((o) => o.id == id);
    if (index == -1) return;
    final target = up ? index + 1 : index - 1;
    if (target < 0 || target >= _document.objects.length) return;
    _pushHistory();
    final obj = _document.objects.removeAt(index);
    _document.objects.insert(target, obj);
    _commit();
  }

  /// Live-drag transforms (position/size/rotation) intentionally do not
  /// push a new history entry on every frame — [beginTransform] snapshots
  /// once at gesture start instead.
  void beginTransform() => _pushHistory();

  void updateTransform(String id,
      {double? x, double? y, double? width, double? height, double? rotation}) {
    final obj = _document.objects.where((o) => o.id == id).firstOrNull;
    if (obj == null) return;
    if (x != null) obj.x = x;
    if (y != null) obj.y = y;
    if (width != null) obj.width = width;
    if (height != null) obj.height = height;
    if (rotation != null) obj.rotation = rotation;
    _commit(recordHistory: false);
  }

  void updateTextObject(String id, void Function(TextObject) mutate) {
    final obj = _document.objects.where((o) => o.id == id).firstOrNull;
    if (obj is! TextObject) return;
    _pushHistory();
    mutate(obj);
    _commit();
  }

  void updateShapeObject(String id, void Function(ShapeObject) mutate) {
    final obj = _document.objects.where((o) => o.id == id).firstOrNull;
    if (obj is! ShapeObject) return;
    _pushHistory();
    mutate(obj);
    _commit();
  }

  void updateIconObject(String id, void Function(IconObjectData) mutate) {
    final obj = _document.objects.where((o) => o.id == id).firstOrNull;
    if (obj is! IconObjectData) return;
    _pushHistory();
    mutate(obj);
    _commit();
  }

  void setBackgroundColor(Color color) {
    _pushHistory();
    _document.backgroundColor = color;
    _commit();
  }

  void setTitle(String title) {
    _document.title = title;
    _commit(recordHistory: false);
  }

  void toggleVisibility(String id) {
    final obj = _document.objects.where((o) => o.id == id).firstOrNull;
    if (obj == null) return;
    _pushHistory();
    obj.visible = !obj.visible;
    _commit();
  }

  void toggleLock(String id) {
    final obj = _document.objects.where((o) => o.id == id).firstOrNull;
    if (obj == null) return;
    obj.locked = !obj.locked;
    _commit(recordHistory: false);
  }

  void markSaved() {
    _dirty = false;
    notifyListeners();
  }

  void replaceDocument(CanvasDocument newDocument) {
    _document = newDocument;
    _selectedId = null;
    _undoStack.clear();
    _redoStack.clear();
    _dirty = false;
    notifyListeners();
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
