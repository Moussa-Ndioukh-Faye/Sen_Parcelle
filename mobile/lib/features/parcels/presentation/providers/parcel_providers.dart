// lib/features/parcels/presentation/providers/parcel_providers.dart
// ═════════════════════════════════════════════

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/core/network/result.dart';
import '../../data/parcel_repository.dart';
import '../../domain/parcel_model.dart';

final parcelsProvider = FutureProvider.family<ParcelsResponse, Map<String, dynamic>>(
  (ref, params) async {
    final result = await ref.watch(parcelRepositoryProvider).fetchParcels(
          region: params['region'],
          search: params['search'],
          typeTerrain: params['type_terrain'],
          page: params['page'] ?? 1,
        );
    return result.when(
      success: (data) => data,
      failure: (_) => ParcelsResponse(count: 0, results: []),
    );
  },
);

final parcelDetailProvider = FutureProvider.family<ParcelDetail?, String>(
  (ref, id) async {
    final result = await ref.watch(parcelRepositoryProvider).fetchParcelDetail(id);
    return result.when(
      success: (data) => data,
      failure: (_) => null,
    );
  },
);

// Filtres actifs
final filterProvider = StateProvider<Map<String, dynamic>>((ref) => {});

// ═══════════════════════════════════════════════════════════════
