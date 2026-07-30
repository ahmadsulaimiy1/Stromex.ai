import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/state/app_state.dart';
import '../../l10n/gen/app_localizations.dart';
import '../ai/ai_service.dart';
import 'diagnostics_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _hasKey = false;
  bool _loadingKey = true;

  @override
  void initState() {
    super.initState();
    _refreshKeyState();
  }

  Future<void> _refreshKeyState() async {
    final has = await context.read<AiService>().hasApiKey();
    if (mounted) {
      setState(() {
        _hasKey = has;
        _loadingKey = false;
      });
    }
  }

  Future<void> _editApiKey() async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Anthropic API key'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'TASMIM\'s AI features call the Anthropic API directly from this '
              'device using your own key. The key is stored encrypted on-device '
              'and never sent anywhere except Anthropic.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(labelText: 'sk-ant-...'),
              obscureText: true,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (result != null && result.trim().isNotEmpty) {
      await context.read<AiService>().setApiKey(result.trim());
      await _refreshKeyState();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('API key saved')));
      }
    }
  }

  Future<void> _removeApiKey() async {
    await context.read<AiService>().clearApiKey();
    await _refreshKeyState();
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.settingsTitle)),
      body: ListView(
        children: [
          _SectionLabel(l10n.appearance),
          RadioListTile<ThemeMode>(
            title: Text(l10n.light),
            value: ThemeMode.light,
            groupValue: appState.themeMode,
            onChanged: (v) => appState.setThemeMode(v!),
          ),
          RadioListTile<ThemeMode>(
            title: Text(l10n.dark),
            value: ThemeMode.dark,
            groupValue: appState.themeMode,
            onChanged: (v) => appState.setThemeMode(v!),
          ),
          RadioListTile<ThemeMode>(
            title: Text(l10n.systemDefault),
            value: ThemeMode.system,
            groupValue: appState.themeMode,
            onChanged: (v) => appState.setThemeMode(v!),
          ),
          const Divider(),
          _SectionLabel(l10n.language),
          RadioListTile<String>(
            title: Text(l10n.english),
            value: 'en',
            groupValue: appState.locale.languageCode,
            onChanged: (v) => appState.setLocale(const Locale('en')),
          ),
          RadioListTile<String>(
            title: Text(l10n.arabic),
            value: 'ar',
            groupValue: appState.locale.languageCode,
            onChanged: (v) => appState.setLocale(const Locale('ar')),
          ),
          const Divider(),
          _SectionLabel(l10n.aiSection),
          ListTile(
            leading: const Icon(Icons.vpn_key_rounded),
            title: Text(l10n.apiKeyLabel),
            subtitle: _loadingKey
                ? const Text('Checking...')
                : Text(_hasKey ? l10n.apiKeyConfigured : l10n.apiKeyNotSet),
            trailing: _hasKey
                ? IconButton(
                    icon: const Icon(Icons.delete_outline_rounded),
                    onPressed: _removeApiKey,
                  )
                : null,
            onTap: _editApiKey,
          ),
          const Divider(),
          _SectionLabel(l10n.accountSection),
          if (appState.session == SessionKind.profile) ...[
            ListTile(
              leading: const Icon(Icons.person_rounded),
              title: Text(appState.profileName ?? 'Profile'),
              subtitle: Text(appState.profileEmail ?? ''),
            ),
            ListTile(
              leading: const Icon(Icons.logout_rounded),
              title: Text(l10n.signOut),
              onTap: () async {
                await appState.signOut();
                if (context.mounted) context.go('/welcome');
              },
            ),
            ListTile(
              leading: Icon(Icons.delete_forever_rounded, color: theme.colorScheme.error),
              title: Text(l10n.deleteProfileAction, style: TextStyle(color: theme.colorScheme.error)),
              onTap: () async {
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Delete profile?'),
                    content: const Text(
                        'This permanently removes your local profile from this device. Your saved projects are not affected.'),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.of(context).pop(false),
                          child: const Text('Cancel')),
                      ElevatedButton(
                          onPressed: () => Navigator.of(context).pop(true),
                          child: const Text('Delete')),
                    ],
                  ),
                );
                if (confirmed == true) {
                  await appState.deleteProfile();
                  if (context.mounted) context.go('/welcome');
                }
              },
            ),
          ] else
            ListTile(
              leading: const Icon(Icons.person_add_alt_rounded),
              title: const Text('Create a local profile'),
              subtitle: const Text('Currently designing as guest'),
              onTap: () => context.push('/create-profile'),
            ),
          const Divider(),
          _SectionLabel(l10n.diagnostics),
          ListTile(
            leading: const Icon(Icons.bug_report_outlined),
            title: const Text('Diagnostics log'),
            subtitle: const Text('Recent app activity — useful for troubleshooting'),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const DiagnosticsScreen()),
            ),
          ),
          const Divider(),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Text(
              'TASMIM MVP · v1.0.0',
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.4)),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Text(
        text.toUpperCase(),
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              letterSpacing: 1.2,
            ),
      ),
    );
  }
}
