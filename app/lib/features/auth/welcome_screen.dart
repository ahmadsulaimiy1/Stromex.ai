import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/state/app_state.dart';
import '../../l10n/gen/app_localizations.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            children: [
              const Spacer(),
              Image.asset('assets/branding/tasmim_mark.png', width: 120, height: 120),
              const SizedBox(height: 20),
              Text(l10n.appName, style: theme.textTheme.headlineLarge),
              const SizedBox(height: 8),
              Text(
                l10n.appTagline,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
              ),
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () async {
                    await context.read<AppState>().continueAsGuest();
                    if (context.mounted) context.go('/dashboard');
                  },
                  child: Text(l10n.continueWithoutAccount),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => context.push('/create-profile'),
                  child: Text(l10n.createLocalProfile),
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => context.push('/sign-in'),
                child: Text(l10n.alreadyHaveProfile),
              ),
              const SizedBox(height: 12),
              Text(
                l10n.profileDisclaimer,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
