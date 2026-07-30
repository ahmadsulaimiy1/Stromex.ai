import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'core/state/app_state.dart';
import 'core/theme/app_theme.dart';
import 'l10n/gen/app_localizations.dart';

class TasmimApp extends StatelessWidget {
  const TasmimApp({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final router = context.read<GoRouter>();

    if (!appState.loaded) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: const Scaffold(body: Center(child: CircularProgressIndicator())),
      );
    }

    return MaterialApp.router(
      title: 'TASMIM',
      debugShowCheckedModeBanner: false,
      themeMode: appState.themeMode,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      locale: appState.locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      routerConfig: router,
      builder: (context, child) {
        final mq = MediaQuery.of(context);
        return MediaQuery(
          data: mq.copyWith(
            textScaler: mq.textScaler.clamp(minScaleFactor: 0.9, maxScaleFactor: 1.3),
          ),
          child: child ?? const SizedBox.shrink(),
        );
      },
    );
  }
}
