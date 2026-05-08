// lib/features/auth/presentation/screens/register_screen.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/features/auth/presentation/providers/auth_provider.dart';
import 'package:sen_parcelle/shared/widgets/app_text_field.dart';
import 'package:sen_parcelle/shared/widgets/gradient_button.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey     = GlobalKey<FormState>();
  final _nomCtrl     = TextEditingController();
  final _emailCtrl   = TextEditingController();
  final _phoneCtrl   = TextEditingController();
  final _passCtrl    = TextEditingController();
  String _role       = 'acheteur';
  int    _step       = 0;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final ok = await ref.read(authNotifierProvider.notifier).register(
      nom: _nomCtrl.text.trim(),
      email: _emailCtrl.text.trim(),
      telephone: _phoneCtrl.text.trim(),
      password: _passCtrl.text,
      role: _role,
    );
    if (ok && mounted) context.pushReplacement('/auth/login');
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(authNotifierProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Créer un compte')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── Barre de progression ───
              LinearProgressIndicator(
                value: (_step + 1) / 2,
                backgroundColor: AppTheme.greenLight,
                color: AppTheme.green,
                borderRadius: BorderRadius.circular(4),
                minHeight: 4,
              ),
              const SizedBox(height: 24),

               AppTextField(controller: _nomCtrl, label: 'Nom complet',
                 hint: 'Votre nom complet',
                 prefixIcon: Icons.person_outline,
                 validator: (v) => (v?.length ?? 0) >= 2 ? null : 'Requis'),
               const SizedBox(height: 16),
               AppTextField(controller: _emailCtrl, label: 'Email',
                 hint: 'email@exemple.com',
                 prefixIcon: Icons.email_outlined,
                 keyboardType: TextInputType.emailAddress,
                 validator: (v) => (v?.contains('@') ?? false) ? null : 'Email invalide'),
               const SizedBox(height: 16),
               AppTextField(controller: _phoneCtrl, label: 'Téléphone',
                 hint: '+221 7X XXX XX',
                 prefixIcon: Icons.phone_outlined,
                 keyboardType: TextInputType.phone,
                 validator: (v) => (v?.length ?? 0) >= 9 ? null : 'Numéro invalide'),
               const SizedBox(height: 16),
               AppTextField(controller: _passCtrl, label: 'Mot de passe',
                 hint: '••••••••',
                 prefixIcon: Icons.lock_outlined,
                 obscureText: true,
                 validator: (v) => (v?.length ?? 0) >= 8 ? null : 'Minimum 8 caractères'),
              const SizedBox(height: 16),

              // ─── Sélecteur rôle ───
              Text('Je suis un :', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              Row(children: [
                _RoleChip(label: '👤 Acheteur', value: 'acheteur', selected: _role,
                  onTap: () => setState(() => _role = 'acheteur')),
                const SizedBox(width: 10),
                _RoleChip(label: '🏠 Vendeur', value: 'vendeur', selected: _role,
                  onTap: () => setState(() => _role = 'vendeur')),
              ]),
              const SizedBox(height: 24),

              if (state.error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(state.error!,
                    style: const TextStyle(color: AppTheme.red, fontSize: 13)),
                ),

              GradientButton(
                label:      'Créer mon compte',

                isLoading:  state.isLoading,
                onPressed:  _submit,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoleChip extends StatelessWidget {
  final String label, value, selected;
  final VoidCallback onTap;
  const _RoleChip({required this.label, required this.value,
    required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isSelected = value == selected;
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppTheme.green : AppTheme.bgLight,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? AppTheme.green : Colors.grey.shade300,
              width: 1.5,
            ),
          ),
          child: Text(label,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: isSelected ? Colors.white : AppTheme.slate,
              fontWeight: FontWeight.w600,
              fontSize: 14,
            )),
        ),
      ),
    );
  }
}