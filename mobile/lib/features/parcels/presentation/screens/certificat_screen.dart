import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/features/parcels/presentation/providers/parcel_providers.dart';

class CertificatScreen extends ConsumerWidget {
  final String parcelId;
  const CertificatScreen({super.key, required this.parcelId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final parcelAsync = ref.watch(parcelDetailProvider(parcelId));

    return Scaffold(
      appBar: AppBar(title: const Text('Certificat Blockchain')),
      body: parcelAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error:   (e, _) => Center(child: Text('Erreur : $e')),
        data: (parcel) {
          if (parcel == null || parcel.certificat == null) {
            return const Center(child: Text('Certificat non disponible'));
          }
          final cert = parcel.certificat!;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(children: [

              // ─── Badge validé ───
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [AppTheme.greenDark, AppTheme.green]),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(children: [
                  const Icon(Icons.check_circle, size: 56, color: Colors.white),
                  const SizedBox(height: 12),
                  const Text('Certificat Valide',
                    style: TextStyle(color: Colors.white, fontSize: 22,
                      fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  const Text('Enregistré sur Blockchain Polygon',
                    style: TextStyle(color: Colors.white70, fontSize: 13)),
                ]),
              ),
              const SizedBox(height: 20),

               // ─── Infos parcelle ───
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.08),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(children: [
                  _CertRow('Parcelle',     parcel.titre),
                  _CertRow('Région',       parcel.region),
                  _CertRow('Superficie',   '${parcel.superficie.toStringAsFixed(0)} m²'),
                  _CertRow('Validé le',    _formatDate(cert.dateValidation)),
                  _CertRow('Réseau',       'Polygon (MATIC)'),
                ]),
              ),
              const SizedBox(height: 16),

              // ─── Hash ───
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceDark,
                  borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                ),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('HASH BLOCKCHAIN',
                    style: TextStyle(color: Colors.white38, fontSize: 10,
                      fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                  SizedBox(height: AppTheme.space8),
                  Text(cert.hashBlockchain,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      color: AppTheme.green400,
                      fontSize: 12,
                      height: 1.6,
                    )),
              ],
              ),
              ),
              const SizedBox(height: 16),

              // ─── Bouton explorer ───
              OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.open_in_new),
                label: const Text('Voir sur Polygon Explorer'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 48),
                ),
              ),

              const SizedBox(height: 12),

              // ─── Vérification manuelle ───
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.bgLight,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: const Row(children: [
                  Icon(Icons.info_outline, color: AppTheme.muted, size: 18),
                  SizedBox(width: 10),
                  Expanded(child: Text(
                    'Ce certificat peut être vérifié indépendamment sur '
                    'polygonscan.com en utilisant le hash ci-dessus.',
                    style: TextStyle(color: AppTheme.muted, fontSize: 12, height: 1.5),
                  )),
                ]),
              ),
            ]),
          );
        },
      ),
    );
  }

  String _formatDate(DateTime d) =>
    '${d.day.toString().padLeft(2, '0')}/'
    '${d.month.toString().padLeft(2, '0')}/${d.year}';
}

class _CertRow extends StatelessWidget {
  final String label, value;
  const _CertRow(this.label, this.value);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    child: Row(children: [
      Text(label, style: const TextStyle(color: AppTheme.muted, fontSize: 13)),
      const Spacer(),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
    ]),
  );
}


// ═══════════════════════════════════════════════════════════════