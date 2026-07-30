import 'package:flutter/material.dart';
import '../storage/local_storage_service.dart';
import '../storage/secure_storage_service.dart';

enum SessionKind { none, guest, profile }

/// App-wide state that isn't specific to one open document: theme, locale,
/// onboarding progress, and whether the current session is a guest or a
/// local profile. Deliberately small — per-document state lives in
/// [CanvasController] instances created per editor screen.
class AppState extends ChangeNotifier {
  AppState(this._localStorage, this._secureStorage);

  final LocalStorageService _localStorage;
  final SecureStorageService _secureStorage;

  ThemeMode _themeMode = ThemeMode.system;
  ThemeMode get themeMode => _themeMode;

  Locale _locale = const Locale('en');
  Locale get locale => _locale;

  bool _onboardingComplete = false;
  bool get onboardingComplete => _onboardingComplete;

  SessionKind _session = SessionKind.none;
  SessionKind get session => _session;

  String? profileName;
  String? profileEmail;

  bool _loaded = false;
  bool get loaded => _loaded;

  Future<void> bootstrap() async {
    final themeString = await _localStorage.getString(LocalStorageService.keyThemeMode);
    _themeMode = switch (themeString) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };

    final localeString = await _localStorage.getString(LocalStorageService.keyLocale);
    _locale = Locale(localeString ?? 'en');

    _onboardingComplete =
        await _localStorage.getBool(LocalStorageService.keyOnboardingComplete);

    final isGuest = await _localStorage.getBool(LocalStorageService.keyIsGuest);
    final hasProfile = await _localStorage.getBool(LocalStorageService.keyHasProfile);
    if (hasProfile) {
      _session = SessionKind.profile;
      profileName = await _secureStorage.read(SecureStorageService.keyProfileName);
      profileEmail = await _secureStorage.read(SecureStorageService.keyProfileEmail);
    } else if (isGuest) {
      _session = SessionKind.guest;
    } else {
      _session = SessionKind.none;
    }

    _loaded = true;
    notifyListeners();
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    await _localStorage.setString(LocalStorageService.keyThemeMode, mode.name);
    notifyListeners();
  }

  Future<void> setLocale(Locale locale) async {
    _locale = locale;
    await _localStorage.setString(LocalStorageService.keyLocale, locale.languageCode);
    notifyListeners();
  }

  Future<void> completeOnboarding() async {
    _onboardingComplete = true;
    await _localStorage.setBool(LocalStorageService.keyOnboardingComplete, true);
    notifyListeners();
  }

  Future<void> continueAsGuest() async {
    _session = SessionKind.guest;
    await _localStorage.setBool(LocalStorageService.keyIsGuest, true);
    notifyListeners();
  }

  Future<void> createLocalProfile({
    required String name,
    required String email,
    required String passcodeHash,
  }) async {
    await _secureStorage.write(SecureStorageService.keyProfileName, name);
    await _secureStorage.write(SecureStorageService.keyProfileEmail, email);
    await _secureStorage.write(
        SecureStorageService.keyProfilePasscodeHash, passcodeHash);
    await _localStorage.setBool(LocalStorageService.keyHasProfile, true);
    profileName = name;
    profileEmail = email;
    _session = SessionKind.profile;
    notifyListeners();
  }

  Future<String?> getStoredProfileEmail() =>
      _secureStorage.read(SecureStorageService.keyProfileEmail);

  Future<bool> hasLocalProfile() => _localStorage
      .getBool(LocalStorageService.keyHasProfile)
      .then((v) => v);

  Future<bool> verifyPasscode(String passcodeHash) async {
    final stored =
        await _secureStorage.read(SecureStorageService.keyProfilePasscodeHash);
    return stored != null && stored == passcodeHash;
  }

  /// Ends the current session only. The local profile itself (name, email,
  /// passcode hash) stays on-device, so relaunching the app — or entering
  /// the passcode again via [verifyPasscode] — restores it. This is a
  /// lock, not a delete.
  Future<void> signOut() async {
    await _localStorage.setBool(LocalStorageService.keyIsGuest, false);
    _session = SessionKind.none;
    notifyListeners();
  }

  Future<void> resumeProfileSession() async {
    _session = SessionKind.profile;
    profileName = await _secureStorage.read(SecureStorageService.keyProfileName);
    profileEmail = await _secureStorage.read(SecureStorageService.keyProfileEmail);
    notifyListeners();
  }

  /// Permanently removes the local profile and everything tied to it.
  /// Distinct from [signOut] — this cannot be undone by re-entering a
  /// passcode.
  Future<void> deleteProfile() async {
    await _localStorage.setBool(LocalStorageService.keyIsGuest, false);
    await _localStorage.setBool(LocalStorageService.keyHasProfile, false);
    await _secureStorage.delete(SecureStorageService.keyProfileName);
    await _secureStorage.delete(SecureStorageService.keyProfileEmail);
    await _secureStorage.delete(SecureStorageService.keyProfilePasscodeHash);
    profileName = null;
    profileEmail = null;
    _session = SessionKind.none;
    notifyListeners();
  }
}
