import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../logging/app_logger.dart';

/// Wraps on-device encrypted storage (Android Keystore-backed) for the
/// handful of secrets TASMIM ever holds: the local profile's credential
/// hash and the user's own AI provider API key (bring-your-own-key model,
/// per the Technology Stack Decision Report — TASMIM never ships with a
/// bundled key, and the key never leaves the device except in direct
/// calls to the provider the user configured).
class SecureStorageService {
  SecureStorageService() : _storage = const FlutterSecureStorage();

  final FlutterSecureStorage _storage;
  static const _tag = 'SecureStorageService';

  static const keyAiApiKey = 'tasmim_ai_api_key';
  static const keyProfilePasscodeHash = 'tasmim_profile_passcode_hash';
  static const keyProfileEmail = 'tasmim_profile_email';
  static const keyProfileName = 'tasmim_profile_name';

  Future<void> write(String key, String value) async {
    try {
      await _storage.write(key: key, value: value);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to write key "$key"', e, st);
      rethrow;
    }
  }

  Future<String?> read(String key) async {
    try {
      return await _storage.read(key: key);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to read key "$key"', e, st);
      return null;
    }
  }

  Future<void> delete(String key) async {
    try {
      await _storage.delete(key: key);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to delete key "$key"', e, st);
    }
  }

  Future<void> deleteAll() async {
    try {
      await _storage.deleteAll();
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to clear secure storage', e, st);
    }
  }
}
