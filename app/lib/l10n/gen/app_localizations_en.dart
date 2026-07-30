// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'TASMIM';

  @override
  String get appTagline => 'Design, elevated.';

  @override
  String get onboardTitle1 => 'Design in seconds';

  @override
  String get onboardBody1 =>
      'Describe what you need or start from a template — TASMIM builds a real, editable first draft instantly.';

  @override
  String get onboardTitle2 => 'A professional canvas';

  @override
  String get onboardBody2 =>
      'Text, shapes, icons, layers, and precise color control — never limited, however far you want to take it.';

  @override
  String get onboardTitle3 => 'Built for Islamic design';

  @override
  String get onboardBody3 =>
      'Real Arabic typography and a dedicated suite of Islamic flyer, mosque event, and da\'wah templates.';

  @override
  String get skip => 'Skip';

  @override
  String get continueLabel => 'Continue';

  @override
  String get getStarted => 'Get Started';

  @override
  String get continueWithoutAccount => 'Continue without account';

  @override
  String get createLocalProfile => 'Create a local profile';

  @override
  String get alreadyHaveProfile => 'I already have a profile on this device';

  @override
  String get profileDisclaimer =>
      'Profiles are stored securely on this device only — TASMIM has no cloud account system in this release.';

  @override
  String get dashboardGreetingGuest => 'Welcome — designing as guest';

  @override
  String dashboardGreetingBack(String name) {
    return 'Welcome back, $name';
  }

  @override
  String get whatToCreate => 'What would you like to create today?';

  @override
  String get newDesign => 'New Design';

  @override
  String get aiGenerate => 'AI Generate';

  @override
  String get templates => 'Templates';

  @override
  String get inspiration => 'Inspiration';

  @override
  String get recentProjects => 'Recent Projects';

  @override
  String get noProjectsTitle => 'No projects yet';

  @override
  String get noProjectsMessage =>
      'Start from a template or generate one with AI — your saved projects will show up here.';

  @override
  String get browseTemplates => 'Browse Templates';

  @override
  String get settingsTitle => 'Settings';

  @override
  String get appearance => 'Appearance';

  @override
  String get light => 'Light';

  @override
  String get dark => 'Dark';

  @override
  String get systemDefault => 'Follow system';

  @override
  String get language => 'Language';

  @override
  String get english => 'English';

  @override
  String get arabic => 'العربية (Arabic)';

  @override
  String get aiSection => 'AI';

  @override
  String get apiKeyLabel => 'Anthropic API key';

  @override
  String get apiKeyConfigured => 'Configured';

  @override
  String get apiKeyNotSet => 'Not set — AI features need a key';

  @override
  String get accountSection => 'Account';

  @override
  String get signOut => 'Sign out';

  @override
  String get deleteProfileAction => 'Delete profile';

  @override
  String get diagnostics => 'Diagnostics';

  @override
  String get save => 'Save';

  @override
  String get export => 'Export';

  @override
  String get cancel => 'Cancel';

  @override
  String get done => 'Done';
}
