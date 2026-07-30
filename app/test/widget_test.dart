// Exercises the real first-run flow: onboarding -> welcome -> guest mode
// -> dashboard. This is the golden path every reviewer will hit first, so
// it is covered by an actual widget test rather than the counter-app
// boilerplate Flutter scaffolds by default.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:tasmim/app.dart';
import 'package:tasmim/core/router/app_router.dart';
import 'package:tasmim/core/state/app_state.dart';
import 'package:tasmim/core/storage/local_storage_service.dart';
import 'package:tasmim/core/storage/project_repository.dart';
import 'package:tasmim/core/storage/secure_storage_service.dart';
import 'package:tasmim/features/ai/ai_service.dart';

Widget _buildTestApp(AppState appState) {
  final router = buildRouter(appState);
  return MultiProvider(
    providers: [
      ChangeNotifierProvider<AppState>.value(value: appState),
      Provider<ProjectRepository>.value(value: ProjectRepository()),
      Provider<AiService>.value(value: AiService(SecureStorageService())),
      Provider<GoRouter>.value(value: router),
    ],
    child: const TasmimApp(),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('onboarding -> welcome -> guest -> dashboard', (tester) async {
    final appState = AppState(LocalStorageService(), SecureStorageService());
    await appState.bootstrap();

    await tester.pumpWidget(_buildTestApp(appState));
    await tester.pumpAndSettle();

    // Onboarding is the first screen a fresh install shows.
    expect(find.text('Design in seconds'), findsOneWidget);

    await tester.tap(find.text('Skip'));
    await tester.pumpAndSettle();

    // Skipping onboarding lands on the guest-or-profile welcome screen.
    expect(find.text('Continue without account'), findsOneWidget);

    // The dashboard's recent-projects list stays in a loading state until
    // its (platform-channel-backed) directory lookup resolves, which never
    // settles in the test harness — pump bounded frames instead of
    // `pumpAndSettle` so an indeterminate spinner can't hang the test.
    await tester.tap(find.text('Continue without account'));
    for (var i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }

    // Guest mode reaches the dashboard with its core quick actions intact.
    // "Templates"/"Inspiration" appear twice by design: once as a quick
    // action and once as a bottom navigation destination label.
    expect(find.text('New Design'), findsOneWidget);
    expect(find.text('AI Generate'), findsOneWidget);
    expect(find.text('Templates'), findsWidgets);
    expect(find.text('Inspiration'), findsWidgets);
  });
}
