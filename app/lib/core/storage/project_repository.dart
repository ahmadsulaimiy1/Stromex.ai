import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../../features/editor/canvas/canvas_model.dart';
import '../logging/app_logger.dart';

/// Local-first project persistence. Every saved TASMIM document is one
/// JSON file on-device under the app's documents directory — no account
/// and no network round-trip required to save or reopen a project, per
/// the MVP's offline-first requirement.
class ProjectRepository {
  static const _tag = 'ProjectRepository';
  static const _folderName = 'tasmim_projects';

  Future<Directory> _projectsDir() async {
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory(p.join(base.path, _folderName));
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
  }

  Future<void> save(CanvasDocument document) async {
    try {
      final dir = await _projectsDir();
      final file = File(p.join(dir.path, '${document.id}.json'));
      document.updatedAt = DateTime.now();
      await file.writeAsString(jsonEncode(document.toJson()));
      AppLogger.instance.info(_tag, 'Saved project ${document.id}');
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to save project ${document.id}', e, st);
      rethrow;
    }
  }

  Future<List<CanvasDocument>> loadAll() async {
    try {
      final dir = await _projectsDir();
      final files = dir
          .listSync()
          .whereType<File>()
          .where((f) => f.path.endsWith('.json'))
          .toList();
      final documents = <CanvasDocument>[];
      for (final file in files) {
        try {
          final raw = await file.readAsString();
          final json = jsonDecode(raw) as Map<String, dynamic>;
          documents.add(CanvasDocument.fromJson(json));
        } catch (e, st) {
          AppLogger.instance
              .warning(_tag, 'Skipping unreadable project file ${file.path}');
          AppLogger.instance.error(_tag, 'Parse error', e, st);
        }
      }
      documents.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      return documents;
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to list projects', e, st);
      return [];
    }
  }

  Future<CanvasDocument?> loadById(String id) async {
    try {
      final dir = await _projectsDir();
      final file = File(p.join(dir.path, '$id.json'));
      if (!await file.exists()) return null;
      final raw = await file.readAsString();
      return CanvasDocument.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to load project $id', e, st);
      return null;
    }
  }

  Future<void> delete(String id) async {
    try {
      final dir = await _projectsDir();
      final file = File(p.join(dir.path, '$id.json'));
      if (await file.exists()) await file.delete();
      AppLogger.instance.info(_tag, 'Deleted project $id');
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to delete project $id', e, st);
    }
  }
}
