import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/logging/app_logger.dart';
import '../../core/storage/project_repository.dart';
import 'canvas/canvas_controller.dart';
import 'canvas/canvas_model.dart';
import 'canvas/canvas_view.dart';
import 'export/export_service.dart';
import 'widgets/main_toolbar.dart';
import 'widgets/selection_toolbar.dart';

class EditorScreen extends StatefulWidget {
  const EditorScreen({super.key, required this.initialDocument, required this.isExistingProject});

  final CanvasDocument initialDocument;
  final bool isExistingProject;

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  static const _tag = 'EditorScreen';
  late final CanvasController _controller;
  final GlobalKey _exportKey = GlobalKey();
  bool _saving = false;
  bool _exporting = false;

  @override
  void initState() {
    super.initState();
    _controller = CanvasController(widget.initialDocument);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<bool> _confirmDiscardIfDirty() async {
    if (!_controller.isDirty) return true;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Discard changes?'),
        content: const Text('You have unsaved changes. Save before leaving?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep editing'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Discard'),
          ),
          ElevatedButton(
            onPressed: () async {
              await _save();
              if (context.mounted) Navigator.of(context).pop(true);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
    return result ?? false;
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await context.read<ProjectRepository>().save(_controller.document);
      _controller.markSaved();
      AppLogger.instance.info(_tag, 'Project saved: ${_controller.document.id}');
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Saved to your projects')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Could not save this project')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _renameDocument() async {
    final controller = TextEditingController(text: _controller.document.title);
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rename design'),
        content: TextField(controller: controller, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
          ElevatedButton(
              onPressed: () => Navigator.of(context).pop(controller.text), child: const Text('Save')),
        ],
      ),
    );
    if (result != null && result.trim().isNotEmpty) {
      _controller.setTitle(result.trim());
    }
  }

  Future<void> _showExportSheet() async {
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Export', style: Theme.of(sheetContext).textTheme.titleLarge),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.image_rounded),
                title: const Text('Save PNG to gallery'),
                subtitle: const Text('Best for transparency and sharp text'),
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  _export(ExportFormat.png, toGallery: true);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_rounded),
                title: const Text('Save JPG to gallery'),
                subtitle: const Text('Smaller file size'),
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  _export(ExportFormat.jpg, toGallery: true);
                },
              ),
              ListTile(
                leading: const Icon(Icons.ios_share_rounded),
                title: const Text('Share'),
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  _export(ExportFormat.png, toGallery: false);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _export(ExportFormat format, {required bool toGallery}) async {
    setState(() => _exporting = true);
    final exportService = ExportService();
    try {
      final bytes = await exportService.renderBytes(
        boundaryKey: _exportKey,
        documentWidth: _controller.document.canvasWidth,
        format: format,
      );
      if (bytes == null) {
        throw Exception('render failed');
      }
      final fileName = _controller.document.title.replaceAll(RegExp(r'[^\w\s-]'), '').trim();
      final safeName = fileName.isEmpty ? 'tasmim-design' : fileName;
      final result = toGallery
          ? await exportService.saveToGallery(bytes, format, safeName)
          : await exportService.share(bytes, format, safeName);

      if (!mounted) return;
      final message = switch (result) {
        ExportResult.savedToGallery => 'Saved to your gallery',
        ExportResult.shared => 'Shared',
        ExportResult.permissionDenied => 'Permission denied — enable photo access in Settings',
        ExportResult.failed => 'Export failed. Please try again.',
      };
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Export failed', e, st);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Export failed. Please try again.')));
      }
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final shouldPop = await _confirmDiscardIfDirty();
        if (shouldPop && mounted) Navigator.of(context).pop();
      },
      child: Scaffold(
        appBar: AppBar(
          title: AnimatedBuilder(
            animation: _controller,
            builder: (context, _) => InkWell(
              onTap: _renameDocument,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Flexible(
                    child: Text(
                      _controller.document.title,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (_controller.isDirty)
                    const Padding(
                      padding: EdgeInsets.only(left: 6),
                      child: Icon(Icons.circle, size: 8, color: Colors.orange),
                    ),
                  const Icon(Icons.edit_rounded, size: 16),
                ],
              ),
            ),
          ),
          actions: [
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) => IconButton(
                icon: const Icon(Icons.undo_rounded),
                onPressed: _controller.canUndo ? _controller.undo : null,
              ),
            ),
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) => IconButton(
                icon: const Icon(Icons.redo_rounded),
                onPressed: _controller.canRedo ? _controller.redo : null,
              ),
            ),
            IconButton(
              icon: _saving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save_outlined),
              onPressed: _saving ? null : _save,
            ),
            IconButton(
              icon: _exporting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.file_download_outlined),
              onPressed: _exporting ? null : _showExportSheet,
            ),
          ],
        ),
        body: Column(
          children: [
            Expanded(
              child: Container(
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.04),
                padding: const EdgeInsets.all(20),
                child: CanvasView(controller: _controller, exportKey: _exportKey),
              ),
            ),
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                final selected = _controller.selectedObject;
                if (selected != null) {
                  return SelectionToolbar(controller: _controller, object: selected);
                }
                return MainToolbar(controller: _controller);
              },
            ),
          ],
        ),
      ),
    );
  }
}
