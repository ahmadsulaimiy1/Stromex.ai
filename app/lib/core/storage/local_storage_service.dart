import 'package:shared_preferences/shared_preferences.dart';
import '../logging/app_logger.dart';

/// Non-secret local preferences: theme mode, locale, onboarding state,
/// guest-vs-profile flag. Nothing here ever leaves the device.
class LocalStorageService {
  static const _tag = 'LocalStorageService';

  static const keyThemeMode = 'tasmim_theme_mode';
  static const keyLocale = 'tasmim_locale';
  static const keyOnboardingComplete = 'tasmim_onboarding_complete';
  static const keyIsGuest = 'tasmim_is_guest';
  static const keyHasProfile = 'tasmim_has_profile';

  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  Future<void> setString(String key, String value) async {
    try {
      final prefs = await _prefs;
      await prefs.setString(key, value);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'setString failed for "$key"', e, st);
    }
  }

  Future<String?> getString(String key) async {
    try {
      final prefs = await _prefs;
      return prefs.getString(key);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'getString failed for "$key"', e, st);
      return null;
    }
  }

  Future<void> setBool(String key, bool value) async {
    try {
      final prefs = await _prefs;
      await prefs.setBool(key, value);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'setBool failed for "$key"', e, st);
    }
  }

  Future<bool> getBool(String key, {bool fallback = false}) async {
    try {
      final prefs = await _prefs;
      return prefs.getBool(key) ?? fallback;
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'getBool failed for "$key"', e, st);
      return fallback;
    }
  }
}
