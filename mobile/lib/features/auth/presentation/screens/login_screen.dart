// lib/features/auth/presentation/screens/login_screen.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/shared/widgets/app_text_field.dart';
import 'package:sen_parcelle/shared/widgets/gradient_button.dart';
import 'package:sen_parcelle/features/auth/presentation/providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailCtrl    = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _formKey      = GlobalKey<FormState>();
  bool  _obscure      = true;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    await ref.read(authNotifierProvider.notifier).login(
      _emailCtrl.text.trim(),
      _passwordCtrl.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);

    // Écouter les changements d'état
    ref.listen<AuthNotifierState>(authNotifierProvider, (_, next) {
      if (next.requiresOTP && next.userId != null) {
        context.push('/auth/otp', extra: {
          'userId': next.userId,
          'email': _emailCtrl.text.trim(),
          'password': _passwordCtrl.text,
        });
      } else if (next.isAuthenticated) {
        context.go('/home');
      }
    });

    return Scaffold(
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ─── Hero vert ───
            Container(
              height: 260,
              decoration: AppTheme.gradientDecoration(),
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.home, size: 52, color: Colors.white),
                      const SizedBox(height: 12),
                      Text('Sen_parcelle',
                        style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          color: Colors.white, fontSize: 28,
                        )),
                      const SizedBox(height: 6),
                      Text('Votre patrimoine, sécurisé',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white70,
                        )),
                    ],
                  ),
                ),
              ),
            ),

            // ─── Formulaire ───
            Padding(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: 8),
                    Text('Connexion',
                      style: Theme.of(context).textTheme.headlineMedium),
                    const SizedBox(height: 4),
                    Text('Bienvenue sur Sen_parcelle',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppTheme.muted,
                      )),
                    const SizedBox(height: 24),

                    AppTextField(
                      controller:  _emailCtrl,
                      label:       'Email',
                      hint:        'moussa@email.com',
                      prefixIcon:  Icons.email_outlined,
                      keyboardType: TextInputType.emailAddress,
                      validator: (v) => (v?.contains('@') ?? false) ? null : 'Email invalide',
                    ),
                    const SizedBox(height: 16),

                    AppTextField(
                      controller:  _passwordCtrl,
                      label:       'Mot de passe',
                      hint:        '••••••••',
                      prefixIcon:  Icons.lock_outlined,
                      obscureText: _obscure,
                      suffixIcon:  IconButton(
                        icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility,
                          color: AppTheme.muted),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                      validator: (v) => (v?.length ?? 0) >= 8 ? null : 'Minimum 8 caractères',
                    ),

                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () {},
                        child: const Text('Mot de passe oublié ?'),
                      ),
                    ),

                    // ─── Erreur ───
                    if (authState.error != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.red.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppTheme.red.withValues(alpha: 0.3)),
                        ),
                        child: Text(authState.error!,
                          style: const TextStyle(color: AppTheme.red, fontSize: 13)),
                      ),
                      const SizedBox(height: 16),
                    ],

                    GradientButton(
                      label: 'Se connecter',

                      isLoading:  authState.isLoading,
                      onPressed:  _submit,
                    ),
                    const SizedBox(height: 16),

                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Text("Pas encore de compte ? ",
                        style: TextStyle(color: AppTheme.muted)),
                      GestureDetector(
                        onTap: () => context.push('/auth/register'),
                        child: const Text("S'inscrire",
                          style: TextStyle(
                            color: AppTheme.green,
                            fontWeight: FontWeight.w700,
                          )),
                      ),
                    ]),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


// ═══════════════════════════════════════════════════════════════