import 'package:flutter/material.dart';
import '../logging/app_logger.dart';

/// Installed as [ErrorWidget.builder] so a widget-build failure anywhere
/// in the tree renders a real, on-brand recovery screen instead of
/// Flutter's default red debug screen (or a blank frame in release) —
/// the concrete mechanism behind the "no crashes" requirement for
/// failures that happen during layout/paint rather than in an awaited
/// Future.
class AppErrorScreen extends StatelessWidget {
  const AppErrorScreen({super.key, required this.details});

  final FlutterErrorDetails details;

  @override
  Widget build(BuildContext context) {
    AppLogger.instance.error(
        'AppErrorScreen', details.exceptionAsString(), details.exception, details.stack);
    return Material(
      color: const Color(0xFFFAF8F3),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline_rounded, size: 48, color: Color(0xFF0B6E4F)),
              const SizedBox(height: 16),
              const Text(
                'Something went wrong on this screen',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Color(0xFF1A1D1B)),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'The rest of TASMIM is unaffected — try going back.',
                style: TextStyle(color: Color(0xFF4B5049)),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
