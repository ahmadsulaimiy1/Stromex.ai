import 'package:flutter/material.dart';
import '../ai/ai_assistant_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../inspiration/inspiration_gallery_screen.dart';
import '../settings/settings_screen.dart';
import '../templates/template_gallery_screen.dart';

/// The post-onboarding shell: one persistent bottom navigation bar across
/// the five always-reachable top-level destinations. Every other screen
/// (editor, AI generators, auth) is a pushed route on top of this shell,
/// so the user is never more than "back" away from a known-good screen —
/// the concrete mechanism behind the "no broken navigation" requirement.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key, this.initialIndex = 0});

  final int initialIndex;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  late int _index = widget.initialIndex;

  static const _screens = [
    DashboardScreen(),
    TemplateGalleryScreen(),
    InspirationGalleryScreen(),
    AiAssistantScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'Home'),
          NavigationDestination(
              icon: Icon(Icons.dashboard_customize_outlined),
              selectedIcon: Icon(Icons.dashboard_customize_rounded),
              label: 'Templates'),
          NavigationDestination(
              icon: Icon(Icons.explore_outlined), selectedIcon: Icon(Icons.explore_rounded), label: 'Inspiration'),
          NavigationDestination(
              icon: Icon(Icons.auto_awesome_outlined),
              selectedIcon: Icon(Icons.auto_awesome_rounded),
              label: 'AI'),
          NavigationDestination(
              icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings_rounded), label: 'Settings'),
        ],
      ),
    );
  }
}
