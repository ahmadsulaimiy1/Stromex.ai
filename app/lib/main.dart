import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'core/error/error_screen.dart';
import 'core/logging/app_logger.dart';
import 'core/router/app_router.dart';
import 'core/state/app_state.dart';
import 'core/storage/local_storage_service.dart';
import 'core/storage/project_repository.dart';
import 'core/storage/secure_storage_service.dart';
import 'features/ai/ai_service.dart';

void main() {
  runZonedGuarded(() {
    WidgetsFlutterBinding.ensureInitialized();

    FlutterError.onError = (details) {
      AppLogger.instance
          .error('FlutterError', details.exceptionAsString(), details.exception, details.stack);
      FlutterError.presentError(details);
    };
    ErrorWidget.builder = (details) => AppErrorScreen(details: details);

    final localStorage = LocalStorageService();
    final secureStorage = SecureStorageService();
    final projectRepository = ProjectRepository();
    final aiService = AiService(secureStorage);

    final appState = AppState(localStorage, secureStorage);
    final router = buildRouter(appState);

    unawaited(appState.bootstrap());

    runApp(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AppState>.value(value: appState),
          Provider<LocalStorageService>.value(value: localStorage),
          Provider<SecureStorageService>.value(value: secureStorage),
          Provider<ProjectRepository>.value(value: projectRepository),
          Provider<AiService>.value(value: aiService),
          Provider.value(value: router),
        ],
        child: const TasmimApp(),
      ),
    );
  }, (error, stack) {
    AppLogger.instance.error('Uncaught', error.toString(), error, stack);
    if (kDebugMode) {
      // ignore: avoid_print
      print('Uncaught zone error: $error\n$stack');
    }
  });
}
