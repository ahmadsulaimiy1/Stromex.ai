import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/state/app_state.dart';
import 'passcode_hasher.dart';

class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends State<SignInScreen> {
  final _passcodeController = TextEditingController();
  String? _error;
  bool _checking = false;

  @override
  void dispose() {
    _passcodeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _checking = true;
      _error = null;
    });
    final appState = context.read<AppState>();
    final hasProfile = await appState.hasLocalProfile();
    final email = await appState.getStoredProfileEmail();
    if (!hasProfile || email == null) {
      setState(() {
        _checking = false;
        _error = 'No local profile exists on this device yet.';
      });
      return;
    }
    final hash = hashPasscode(_passcodeController.text.trim(), email);
    final ok = await appState.verifyPasscode(hash);
    if (!mounted) return;
    if (ok) {
      await appState.resumeProfileSession();
      if (mounted) context.go('/dashboard');
    } else {
      setState(() {
        _checking = false;
        _error = 'Incorrect passcode.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sign in')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Enter the passcode for the profile on this device.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _passcodeController,
                decoration: InputDecoration(
                  labelText: 'Passcode',
                  errorText: _error,
                ),
                obscureText: true,
                keyboardType: TextInputType.number,
                onSubmitted: (_) => _submit(),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _checking ? null : _submit,
                child: _checking
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Continue'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
