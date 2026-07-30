import 'dart:convert';
import 'package:crypto/crypto.dart';

/// TASMIM's "optional account" is a local, on-device profile — not a
/// cloud identity (see Known Limitations in the MVP docs). The passcode
/// never needs to defend against a networked attacker, only casual local
/// access, so a salted SHA-256 hash is an appropriate, honest amount of
/// protection for what this actually is.
String hashPasscode(String passcode, String email) {
  final salted = '$email::tasmim-local::$passcode';
  return sha256.convert(utf8.encode(salted)).toString();
}
