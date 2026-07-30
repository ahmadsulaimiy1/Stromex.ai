import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/state/app_state.dart';
import '../../core/storage/project_repository.dart';
import '../../l10n/gen/app_localizations.dart';
import '../editor/canvas/canvas_document_view.dart';
import '../editor/canvas/canvas_model.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/section_header.dart';
import 'new_design_sheet.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<List<CanvasDocument>> _projectsFuture;

  @override
  void initState() {
    super.initState();
    _projectsFuture = context.read<ProjectRepository>().loadAll();
  }

  void _refresh() {
    setState(() {
      _projectsFuture = context.read<ProjectRepository>().loadAll();
    });
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    final greetingName = appState.profileName ?? '';

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Image.asset('assets/branding/tasmim_mark.png', width: 24, height: 24),
            const SizedBox(width: 8),
            Text(l10n.appName),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () async => _refresh(),
        child: ListView(
          padding: const EdgeInsets.only(bottom: 32),
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
              child: Text(
                appState.session == SessionKind.guest
                    ? l10n.dashboardGreetingGuest
                    : l10n.dashboardGreetingBack(greetingName),
                style: theme.textTheme.headlineMedium,
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
              child: Text(
                l10n.whatToCreate,
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 14,
                crossAxisSpacing: 14,
                childAspectRatio: 1.5,
                children: [
                  _QuickAction(
                    icon: Icons.add_circle_rounded,
                    label: l10n.newDesign,
                    color: theme.colorScheme.primary,
                    onTap: () => showNewDesignSheet(context),
                  ),
                  _QuickAction(
                    icon: Icons.auto_awesome_rounded,
                    label: l10n.aiGenerate,
                    color: theme.colorScheme.secondary,
                    onTap: () => context.push('/ai/prompt-to-design'),
                  ),
                  _QuickAction(
                    icon: Icons.dashboard_customize_rounded,
                    label: l10n.templates,
                    color: const Color(0xFF16324F),
                    onTap: () => context.go('/templates'),
                  ),
                  _QuickAction(
                    icon: Icons.explore_rounded,
                    label: l10n.inspiration,
                    color: const Color(0xFF7A1F3D),
                    onTap: () => context.go('/inspiration'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            SectionHeader(title: l10n.recentProjects),
            FutureBuilder<List<CanvasDocument>>(
              future: _projectsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Padding(
                    padding: EdgeInsets.all(40),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                final projects = snapshot.data ?? [];
                if (projects.isEmpty) {
                  return EmptyState(
                    icon: Icons.folder_open_rounded,
                    title: l10n.noProjectsTitle,
                    message: l10n.noProjectsMessage,
                    actionLabel: l10n.browseTemplates,
                    onAction: () => context.go('/templates'),
                  );
                }
                return GridView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 14,
                    crossAxisSpacing: 14,
                    childAspectRatio: 0.82,
                  ),
                  itemCount: projects.length,
                  itemBuilder: (context, index) {
                    final project = projects[index];
                    return _ProjectCard(
                      document: project,
                      onTap: () async {
                        await context.push('/editor', extra: {
                          'document': project,
                          'isExisting': true,
                        });
                        _refresh();
                      },
                      onDelete: () async {
                        await context.read<ProjectRepository>().delete(project.id);
                        _refresh();
                      },
                    );
                  },
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color.withValues(alpha: 0.1),
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  label,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700, color: color),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProjectCard extends StatelessWidget {
  const _ProjectCard({required this.document, required this.onTap, required this.onDelete});

  final CanvasDocument document;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(child: CanvasDocumentView(document: document, borderRadius: 0)),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      document.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                    ),
                  ),
                  InkWell(
                    onTap: onDelete,
                    child: Icon(Icons.delete_outline_rounded,
                        size: 18, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4)),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
