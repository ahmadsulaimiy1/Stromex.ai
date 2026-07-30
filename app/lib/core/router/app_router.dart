import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/ai/ai_assistant_screen.dart';
import '../../features/ai/prompt_to_design_screen.dart';
import '../../features/auth/create_profile_screen.dart';
import '../../features/auth/sign_in_screen.dart';
import '../../features/auth/welcome_screen.dart';
import '../../features/editor/canvas/canvas_model.dart';
import '../../features/editor/editor_screen.dart';
import '../../features/home/home_shell.dart';
import '../../features/onboarding/onboarding_screen.dart';
import '../../features/settings/settings_screen.dart';
import '../state/app_state.dart';

/// One central, typed route table. Every navigable destination in TASMIM
/// is listed here — the "no broken navigation" requirement is enforced by
/// having exactly one place routes are defined, with a redirect guard
/// that always lands an unauthenticated or pre-onboarding user somewhere
/// valid rather than a dead screen.
GoRouter buildRouter(AppState appState) {
  return GoRouter(
    initialLocation: '/',
    refreshListenable: appState,
    redirect: (context, state) {
      if (!appState.loaded) return null;
      final path = state.matchedLocation;
      final onOnboarding = path == '/';
      final onAuthFlow = path == '/welcome' || path == '/create-profile' || path == '/sign-in';

      if (!appState.onboardingComplete) {
        return onOnboarding ? null : '/';
      }
      if (appState.session == SessionKind.none) {
        return onAuthFlow ? null : '/welcome';
      }
      if (onOnboarding || path == '/welcome') {
        return '/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (context, state) => const OnboardingScreen()),
      GoRoute(path: '/welcome', builder: (context, state) => const WelcomeScreen()),
      GoRoute(
        path: '/create-profile',
        builder: (context, state) => const CreateProfileScreen(),
      ),
      GoRoute(path: '/sign-in', builder: (context, state) => const SignInScreen()),
      GoRoute(path: '/dashboard', builder: (context, state) => const HomeShell()),
      GoRoute(path: '/templates', builder: (context, state) => const HomeShell(initialIndex: 1)),
      GoRoute(path: '/inspiration', builder: (context, state) => const HomeShell(initialIndex: 2)),
      GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
      GoRoute(
        path: '/editor',
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>?;
          final document = extra?['document'] as CanvasDocument? ??
              CanvasDocument.blank(title: 'Untitled Design', preset: CanvasSizePreset.social);
          final isExisting = extra?['isExisting'] as bool? ?? false;
          return EditorScreen(initialDocument: document, isExistingProject: isExisting);
        },
      ),
      GoRoute(path: '/ai/assistant', builder: (context, state) => const AiAssistantScreen()),
      GoRoute(
        path: '/ai/prompt-to-design',
        builder: (context, state) => const PromptToDesignScreen(),
      ),
      GoRoute(
        path: '/ai/flyer-generator',
        builder: (context, state) =>
            const PromptToDesignScreen(mode: PromptToDesignMode.flyer),
      ),
      GoRoute(
        path: '/ai/social-generator',
        builder: (context, state) =>
            const PromptToDesignScreen(mode: PromptToDesignMode.socialPost),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Page not found')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline_rounded, size: 48),
              const SizedBox(height: 12),
              Text('That screen could not be found.', style: Theme.of(context).textTheme.bodyLarge),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => context.go('/dashboard'),
                child: const Text('Go to Dashboard'),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
