import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/features/auth/presentation/providers/auth_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: CustomScrollView(slivers: [
        SliverAppBar(
          expandedHeight: 200,
          pinned: true,
          backgroundColor: AppTheme.greenDark,
          flexibleSpace: FlexibleSpaceBar(
            background: Container(
              decoration: AppTheme.gradientDecoration(),
              child: SafeArea(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const CircleAvatar(
                      radius: 40,
                      backgroundColor: Colors.white24,
                      child:
                          Text('M', style: TextStyle(fontSize: 32, color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(height: 10),
                    const Text('Moussa Faye',
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.person, size: 14, color: Colors.white),
                        Text(' Acheteur', style: TextStyle(color: Colors.white, fontSize: 12)),
                      ]),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        SliverList(
          delegate: SliverChildListDelegate([
            const _SectionHeader(title: 'Général'),
            _ProfileItem(icon: Icons.person_outline, title: 'Informations personnelles', onTap: () {}),
            _ProfileItem(
                icon: Icons.verified_user_outlined,
                title: 'Vérification d\'identité (KYC)',
                onTap: () => context.push('/kyc')),
            _ProfileItem(icon: Icons.lock_outline, title: 'Sécurité & Mot de passe', onTap: () {}),
            const _SectionHeader(title: 'Activité'),
            _ProfileItem(icon: Icons.history, title: 'Historique des transactions', onTap: () {}),
            _ProfileItem(icon: Icons.favorite_border, title: 'Mes favoris', onTap: () {}),
            const _SectionHeader(title: 'Support'),
            _ProfileItem(icon: Icons.help_outline, title: 'Centre d\'aide', onTap: () {}),
            _ProfileItem(icon: Icons.info_outline, title: 'À propos', onTap: () {}),
            const SizedBox(height: 24),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.red,
                  side: const BorderSide(color: AppTheme.red),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                icon: const Icon(Icons.logout),
                label: const Text('Se déconnecter'),
                onPressed: () async {
                  await ref.read(authNotifierProvider.notifier).logout();
                  if (context.mounted) context.go('/auth/login');
                },
              ),
            ),
            const SizedBox(height: 40),
          ]),
        ),
      ]),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
        child: Text(title,
            style:
                const TextStyle(color: AppTheme.muted, fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1.1)),
      );
}

class _ProfileItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;

  const _ProfileItem({required this.icon, required this.title, required this.onTap});

  @override
  Widget build(BuildContext context) => ListTile(
        leading: Icon(icon, color: AppTheme.slate),
        title: Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
        trailing: const Icon(Icons.chevron_right, size: 20, color: AppTheme.muted),
        onTap: onTap,
      );
}
