import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../editor/canvas/canvas_model.dart';
import 'ai_models.dart';
import 'ai_service.dart';
import 'design_brief_applier.dart';

enum PromptToDesignMode { general, flyer, socialPost }

extension on PromptToDesignMode {
  String get title => switch (this) {
        PromptToDesignMode.general => 'AI Generate',
        PromptToDesignMode.flyer => 'Flyer Generator',
        PromptToDesignMode.socialPost => 'Social Post Generator',
      };

  String get hint => switch (this) {
        PromptToDesignMode.general => 'e.g. "Announce our new store opening downtown"',
        PromptToDesignMode.flyer => 'e.g. "Islamic conference flyer for a weekend seminar"',
        PromptToDesignMode.socialPost =>
          'e.g. "Eid greeting post for our community page"',
      };

  CanvasSizePreset get defaultPreset => switch (this) {
        PromptToDesignMode.general => CanvasSizePreset.social,
        PromptToDesignMode.flyer => CanvasSizePreset.flyer,
        PromptToDesignMode.socialPost => CanvasSizePreset.social,
      };
}

class PromptToDesignScreen extends StatefulWidget {
  const PromptToDesignScreen({super.key, this.mode = PromptToDesignMode.general});

  final PromptToDesignMode mode;

  @override
  State<PromptToDesignScreen> createState() => _PromptToDesignScreenState();
}

class _PromptToDesignScreenState extends State<PromptToDesignScreen> {
  final _promptController = TextEditingController();
  late CanvasSizePreset _preset;
  bool _includeArabic = true;
  bool _generating = false;
  String? _error;
  bool? _hasKey;

  static const _presetLabels = {
    CanvasSizePreset.social: 'Social Post',
    CanvasSizePreset.story: 'Story',
    CanvasSizePreset.flyer: 'Flyer',
    CanvasSizePreset.poster: 'Poster',
    CanvasSizePreset.banner: 'Banner',
  };

  @override
  void initState() {
    super.initState();
    _preset = widget.mode.defaultPreset;
    _checkKey();
  }

  Future<void> _checkKey() async {
    final has = await context.read<AiService>().hasApiKey();
    if (mounted) setState(() => _hasKey = has);
  }

  Future<void> _generate() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty) {
      setState(() => _error = 'Describe what you want to create first.');
      return;
    }
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final brief = await context.read<AiService>().generateDesignBrief(
            prompt: prompt,
            targetFormat: _presetLabels[_preset]!,
            includeArabic: _includeArabic,
          );
      final document = applyDesignBrief(brief, _preset);
      if (mounted) {
        context.pushReplacement('/editor', extra: {
          'document': document,
          'isExisting': false,
        });
      }
    } on AiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_hasKey == false) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.mode.title)),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.vpn_key_rounded, size: 48, color: theme.colorScheme.primary),
                const SizedBox(height: 16),
                Text('Add your API key', style: theme.textTheme.titleLarge, textAlign: TextAlign.center),
                const SizedBox(height: 8),
                Text(
                  'AI generation uses your own Anthropic API key, kept encrypted on this device.',
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => context.push('/settings'),
                  child: const Text('Open Settings'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(widget.mode.title)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Describe your design', style: theme.textTheme.titleMedium),
              const SizedBox(height: 10),
              TextField(
                controller: _promptController,
                maxLines: 4,
                decoration: InputDecoration(hintText: widget.mode.hint, errorText: _error),
              ),
              const SizedBox(height: 20),
              Text('Format', style: theme.textTheme.titleMedium),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                children: CanvasSizePreset.all.map((preset) {
                  return ChoiceChip(
                    label: Text(_presetLabels[preset]!),
                    selected: _preset == preset,
                    onSelected: (_) => setState(() => _preset = preset),
                  );
                }).toList(),
              ),
              const SizedBox(height: 12),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Include Arabic headline'),
                subtitle: const Text('Adds an Arabic translation where the template supports it'),
                value: _includeArabic,
                onChanged: (v) => setState(() => _includeArabic = v),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: _generating ? null : _generate,
                icon: _generating
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.auto_awesome_rounded),
                label: Text(_generating ? 'Generating...' : 'Generate Design'),
              ),
              const SizedBox(height: 12),
              Text(
                'TASMIM generates headline copy and a color direction, then applies '
                'them to one of its own crafted templates — fully editable afterward.',
                style: theme.textTheme.bodySmall
                    ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
