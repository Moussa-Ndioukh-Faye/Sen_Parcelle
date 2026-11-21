import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/features/parcels/domain/parcel_model.dart';

class ParcelCard extends StatelessWidget {
  final ParcelModel parcel;
  final VoidCallback onTap;

  const ParcelCard({super.key, required this.parcel, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 14),
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
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ─── Image ───
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
              child: Stack(
                children: [
                  SizedBox(
                    height: 160,
                    width: double.infinity,
                    child: parcel.photoPrincipale != null
                        ? CachedNetworkImage(
                            imageUrl: parcel.photoPrincipale!,
                            fit: BoxFit.cover,
                            placeholder: (_, __) => Container(color: AppTheme.greenLight),
                            errorWidget: (_, __, ___) => _ImagePlaceholder(type: parcel.typeTerrain),
                          )
                        : _ImagePlaceholder(type: parcel.typeTerrain),
                  ),
                  Positioned(
                    top: 10,
                    left: 10,
                    child: _CertificationBadge(isCertified: parcel.isCertified),
                  ),
                ],
              ),
            ),
            // ─── Infos ───
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(parcel.titre,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 4),
                  Row(children: [
                    const Icon(Icons.location_on, size: 12, color: AppTheme.muted),
                    const SizedBox(width: 3),
                    Expanded(
                        child: Text(parcel.localisation,
                            style: const TextStyle(color: AppTheme.muted, fontSize: 12),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis)),
                  ]),
                  const SizedBox(height: 10),
                  Row(children: [
                    Expanded(
                      child: Text(parcel.prixFormate,
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.greenDark)),
                    ),
                    _MetaTag(label: '${parcel.superficie.toStringAsFixed(0)} m²'),
                    const SizedBox(width: 6),
                    _MetaTag(label: parcel.typeTerrain),
                  ]),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ImagePlaceholder extends StatelessWidget {
  final String type;
  const _ImagePlaceholder({required this.type});
  static const _icons = {
    'residentiel': Icons.home,
    'commercial': Icons.business,
    'agricole': Icons.agriculture,
    'industriel': Icons.factory,
  };
  @override
  Widget build(BuildContext context) => Container(
        color: AppTheme.greenLight,
        child: Center(child: Icon(_icons[type] ?? Icons.landscape, size: 50, color: AppTheme.green)),
      );
}

class _CertificationBadge extends StatelessWidget {
  final bool isCertified;
  const _CertificationBadge({required this.isCertified});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: isCertified ? AppTheme.green : AppTheme.amber,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(
            isCertified ? Icons.verified : Icons.hourglass_empty,
            size: 10,
            color: Colors.white,
          ),
          const SizedBox(width: 3),
          Text(
            isCertified ? 'Certifiée' : 'En vérification',
            style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
          ),
        ]),
      );
}

class _MetaTag extends StatelessWidget {
  final String label;
  const _MetaTag({required this.label});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppTheme.bgLight,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.muted)),
      );
}
