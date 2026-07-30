import 'dart:collection';
import 'package:flutter/foundation.dart';

enum LogLevel { debug, info, warning, error }

class LogEntry {
  LogEntry(this.level, this.tag, this.message, this.error, this.stackTrace)
      : timestamp = DateTime.now();

  final LogLevel level;
  final String tag;
  final String message;
  final Object? error;
  final StackTrace? stackTrace;
  final DateTime timestamp;

  @override
  String toString() {
    final buffer = StringBuffer()
      ..write('[${timestamp.toIso8601String()}] ')
      ..write('${level.name.toUpperCase()} ')
      ..write('($tag) ')
      ..write(message);
    if (error != null) buffer.write(' | error: $error');
    return buffer.toString();
  }
}

/// A lightweight, dependency-free structured logger.
///
/// Every screen and service reports through here rather than raw `print`,
/// so unexpected states (failed exports, AI errors, storage failures) are
/// captured consistently and can be inspected from the in-app diagnostics
/// view without needing a device log puller.
class AppLogger {
  AppLogger._();

  static final AppLogger instance = AppLogger._();

  final Queue<LogEntry> _buffer = ListQueue<LogEntry>();
  static const int _maxEntries = 400;

  List<LogEntry> get recentEntries => List.unmodifiable(_buffer);

  void debug(String tag, String message) => _log(LogLevel.debug, tag, message);

  void info(String tag, String message) => _log(LogLevel.info, tag, message);

  void warning(String tag, String message) =>
      _log(LogLevel.warning, tag, message);

  void error(String tag, String message,
      [Object? error, StackTrace? stackTrace]) {
    _log(LogLevel.error, tag, message, error, stackTrace);
  }

  void _log(LogLevel level, String tag, String message,
      [Object? error, StackTrace? stackTrace]) {
    final entry = LogEntry(level, tag, message, error, stackTrace);
    _buffer.add(entry);
    while (_buffer.length > _maxEntries) {
      _buffer.removeFirst();
    }
    if (kDebugMode) {
      // ignore: avoid_print
      print(entry);
      if (stackTrace != null) {
        // ignore: avoid_print
        print(stackTrace);
      }
    }
  }

  void clear() => _buffer.clear();
}
