// lib/features/parcels/presentation/screens/parcel_detail_screen.dart
// ═════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
// import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/features/parcels/domain/parcel_model.dart';
import 'package:sen_parcelle/features/parcels/presentation/providers/parcel_providers.dart';
import 'package:sen_parcelle/features/transactions/presentation/providers/transaction_providers.dart';

class ParcelDetailScreen extends ConsumerWidget {
  final String id;
  const ParcelDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final parcelAsync = ref.watch(parcelDetailProvider(id));

    return parcelAsync.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error:   (e, _) => Scaffold(
        appBar: AppBar(),
        body: Center(child: Text('Erreur : $e')),
      ),
      data: (parcel) {
        if (parcel == null) return const Scaffold(
          body: Center(child: Text('Parcelle introuvable')),
        );
        return _ParcelDetailView(parcel: parcel);
      },
    );
  }
}

class _ParcelDetailView extends ConsumerWidget {
  final ParcelDetail parcel;
  const _ParcelDetailView({required this.parcel});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: CustomScrollView(slivers: [
        // ─── Image header ───
        SliverAppBar(
          expandedHeight: 240,
          pinned: true,
          backgroundColor: AppTheme.greenDark,
          flexibleSpace: FlexibleSpaceBar(
            background: parcel.photoPrincipale != null
              ? Image.network(parcel.photoPrincipale!, fit: BoxFit.cover)
              : Container(
                  decoration: AppTheme.gradientDecoration(),
                  child: const Center(child: Icon(Icons.home, size: 80, color: Colors.white54)),
                ),
          ),
        ),

        SliverToBoxAdapter(child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [

            // ─── Titre + badge ───
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(child: Text(parcel.titre,
                style: Theme.of(context).textTheme.headlineMedium)),
              const SizedBox(width: 8),
              _StatusBadge(isCertified: parcel.isCertified),
            ]),
            const SizedBox(height: 6),
            Row(children: [
              const Icon(Icons.location_on, size: 14, color: AppTheme.muted),
              const SizedBox(width: 4),
              Text(parcel.localisation, style: TextStyle(color: AppTheme.muted, fontSize: 13)),
            ]),
            const SizedBox(height: 14),

            // ─── Prix ───
            Text(parcel.prixFormate,
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                color: AppTheme.greenDark, fontWeight: FontWeight.w900, fontSize: 28,
              )),
            const SizedBox(height: 14),

            // ─── Métriques ───
            Row(children: [
              _MetricChip(icon: Icons.straighten, label: '${parcel.superficie.toStringAsFixed(0)} m²'),
              const SizedBox(width: 8),
              _MetricChip(icon: Icons.label, label: parcel.typeTerrain),
              const SizedBox(width: 8),
              _MetricChip(icon: Icons.location_on, label: parcel.region),
            ]),

            // ─── Certificat blockchain ───
            if (parcel.isCertified && parcel.certificat != null) ...[
              const SizedBox(height: 16),
              GestureDetector(
                onTap: () => context.push('/parcelle/${parcel.id}/certificat'),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppTheme.greenDark, AppTheme.green]),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Row(
                      children: [
                        Text('CERTIFICAT BLOCKCHAIN',
                          style: TextStyle(color: Colors.white60,
                            fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1)),
                        SizedBox(width: 4),
                        Icon(Icons.link, size: 12, color: Colors.white60),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text('Propriété vérifiée et certifiée',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        parcel.certificat!.hashBlockchain,
                        style: const TextStyle(
                          fontFamily: 'monospace', color: Colors.white70, fontSize: 10),
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Row(children: [
                      Spacer(),
                      Text('Voir sur Polygon',
                        style: TextStyle(color: Colors.white70, fontSize: 12)),
                      SizedBox(width: 4),
                      Icon(Icons.arrow_forward, size: 12, color: Colors.white70),
                    ]),
                  ]),
                ),
              ),
            ],

            // ─── Description ───
            if (parcel.description?.isNotEmpty ?? false) ...[
              const SizedBox(height: 16),
              Text('Description', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 6),
              Text(parcel.description!,
                style: TextStyle(color: AppTheme.muted, height: 1.6)),
            ],

            // ─── Vendeur ───
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.bgLight,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(children: [
                CircleAvatar(
                  backgroundColor: AppTheme.green,
                  child: Text(
                    parcel.vendeurNom.isNotEmpty ? parcel.vendeurNom[0] : 'V',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(width: 12),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(parcel.vendeurNom,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                  const Text('Vendeur vérifié',
                    style: TextStyle(color: AppTheme.muted, fontSize: 12)),
                ])),
                ElevatedButton.icon(
                  onPressed: () => context.push('/messages'),
                  icon: const Icon(Icons.chat_bubble_outline, size: 16),
                  label: const Text('Contacter'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size.zero,
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  ),
                ),
              ]),
            ),

            const SizedBox(height: 90),
          ]),
        )),
      ]),

      // ─── Bottom CTA ───
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(children: [
            Expanded(
              flex: 3,
              child: ElevatedButton(
                onPressed: parcel.isCertified ? () => _showPaymentSheet(context, ref, parcel) : null,
                child: const Text('Initier un achat'),
              ),
            ),
            const SizedBox(width: 12),
            OutlinedButton(
              onPressed: () {},
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(52, 52),
                side: const BorderSide(color: AppTheme.green, width: 1.5),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              child: const Icon(Icons.bookmark_border, color: AppTheme.green),
            ),
          ]),
        ),
      ),
    );
  }

  void _showPaymentSheet(BuildContext context, WidgetRef ref, ParcelDetail parcel) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Choisir un moyen de paiement',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('Montant à payer : ${parcel.prixFormate}',
                style: const TextStyle(color: AppTheme.muted)),
            const SizedBox(height: 24),
            _PaymentOptionTile(
              title: 'Wave Sénégal',
              subtitle: 'Rapide et sécurisé',
              icon: Icons.waves,
              onTap: () => _handlePayment(context, ref, parcel.id, 'wave'),
            ),
            const SizedBox(height: 12),
            _PaymentOptionTile(
              title: 'Orange Money',
              subtitle: 'Simple et direct',
              icon: Icons.payment,
              onTap: () => _handlePayment(context, ref, parcel.id, 'orange_money'),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Future<void> _handlePayment(
    BuildContext context, 
    WidgetRef ref, 
    String parcelId, 
    String provider
  ) async {
    Navigator.pop(context); // Fermer le bottom sheet

    // Afficher un loader global ou via le provider
    await ref.read(transactionNotifierProvider.notifier).initiatePayment(
          parcelId: parcelId,
          provider: provider,
        );

    final state = ref.read(transactionNotifierProvider);
    if (state.paymentResponse != null) {
      // Lancer l'URL de paiement
      launchUrl(Uri.parse(state.paymentResponse!.paymentUrl), mode: LaunchMode.externalApplication);
    } else if (state.error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur : ${state.error}'), backgroundColor: AppTheme.red),
      );
    }
  }
}

class _PaymentOptionTile extends StatelessWidget {
  final String title, subtitle;
  final IconData icon;
  final VoidCallback onTap;

  const _PaymentOptionTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: AppTheme.bgLight, width: 2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(children: [
          Icon(icon, color: AppTheme.green, size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text(subtitle, style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
              ],
            ),
          ),
          const Icon(Icons.arrow_forward_ios, size: 14, color: AppTheme.muted),
        ]),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final bool isCertified;
  const _StatusBadge({required this.isCertified});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: isCertified ? AppTheme.green : AppTheme.amber,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(isCertified ? Icons.verified : Icons.access_time, size: 12, color: Colors.white),
        const SizedBox(width: 4),
        Text(
          isCertified ? 'Certifiée' : 'En attente',
          style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
        ),
      ],
    ),
  );
}

class _MetricChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _MetricChip({required this.icon, required this.label});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
    decoration: BoxDecoration(
      color: AppTheme.bgLight,
      borderRadius: BorderRadius.circular(10),
    ),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 14, color: AppTheme.green),
      const SizedBox(width: 5),
      Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
    ]),
  );
}