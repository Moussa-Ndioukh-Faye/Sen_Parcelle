// lib/features/auth/presentation/screens/otp_screen.dart
// Écran de saisie du code OTP 2FA
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/features/auth/presentation/providers/auth_provider.dart';
import 'package:sen_parcelle/shared/widgets/gradient_button.dart';

class OTPScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic> extra;
  const OTPScreen({super.key, required this.extra});
  String get userId => extra['userId'] as String;
  String get _email => extra['email'] as String;
  String get _password => extra['password'] as String;
  @override ConsumerState<OTPScreen> createState() => _OTPScreenState();
}

class _OTPScreenState extends ConsumerState<OTPScreen> {
  final List<TextEditingController> _controllers =
      List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _focusNodes =
      List.generate(6, (_) => FocusNode());
  // int _countdown = 300; // 5 minutes

  String get _otpCode => _controllers.map((c) => c.text).join();

  void _onDigitChanged(int index, String value) {
    if (value.isNotEmpty && index < 5) {
      _focusNodes[index + 1].requestFocus();
    }
    if (value.isEmpty && index > 0) {
      _focusNodes[index - 1].requestFocus();
    }
    if (_otpCode.length == 6) _submit();
  }

  Future<void> _submit() async {
    if (_otpCode.length != 6) return;
    await ref.read(authNotifierProvider.notifier).login(
      widget._email,
      widget._password,
      otp: _otpCode,
    );
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AuthNotifierState>(authNotifierProvider, (_, next) {
      if (next.isAuthenticated) context.go('/home');
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Vérification')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 32),
            const Text('📱', textAlign: TextAlign.center,
              style: TextStyle(fontSize: 60)),
            const SizedBox(height: 16),
            Text('Code de vérification',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 8),
            Text('Entrez le code à 6 chiffres envoyé par SMS',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.muted)),
            const SizedBox(height: 40),

            // ─── 6 cases OTP ───
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: List.generate(6, (i) => SizedBox(
                width: 46, height: 56,
                child: TextField(
                  controller:  _controllers[i],
                  focusNode:   _focusNodes[i],
                  textAlign:   TextAlign.center,
                  keyboardType: TextInputType.number,
                  maxLength:   1,
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  decoration: InputDecoration(
                    counterText:  '',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: Colors.grey.shade300),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: AppTheme.green, width: 2),
                    ),
                  ),
                  onChanged: (v) => _onDigitChanged(i, v),
                ),
              )),
            ),
            const SizedBox(height: 32),

            Consumer(builder: (_, ref, __) {
              final state = ref.watch(authNotifierProvider);
              return GradientButton(
                label:      'Valider',
                isLoading:  state.isLoading,
                onPressed:  _submit,
              );
            }),

            const SizedBox(height: 16),
            TextButton(
              onPressed: () {},
              child: const Text('Renvoyer le code'),
            ),
          ],
        ),
      ),
    );
  }
}


// ═══════════════════════════════════════════════════════════════