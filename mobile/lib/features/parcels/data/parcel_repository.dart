// lib/features/parcels/data/parcel_repository.dart
// ═════════════════════════════════════════════

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/core/network/dio_client.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/features/parcels/domain/parcel_model.dart';

class ParcelRepository {
  final Dio _dio;
  ParcelRepository(this._dio);

  Future<Result<ParcelsResponse>> fetchParcels({
    String? region,
    String? typeTerrain,
    double? minPrix,
    double? maxPrix,
    double? minSuperficie,
    String? search,
    double? lat,
    double? lng,
    double? radiusKm,
    String status = 'certified',
    int page = 1,
  }) =>
      safeApiCall(() async {
        final params = <String, dynamic>{
          'status': status,
          'page': page,
          if (region != null) 'region': region,
          if (typeTerrain != null) 'type_terrain': typeTerrain,
          if (minPrix != null) 'min_prix': minPrix,
          if (maxPrix != null) 'max_prix': maxPrix,
          if (minSuperficie != null) 'min_superficie': minSuperficie,
          if (search != null) 'search': search,
          if (lat != null) 'latitude': lat,
          if (lng != null) 'longitude': lng,
          if (radiusKm != null) 'radius_km': radiusKm,
        };
        final response = await _dio.get('/parcelles/', queryParameters: params);
        return ParcelsResponse.fromJson(response.data);
      });

  Future<Result<ParcelDetail>> fetchParcelDetail(String id) => safeApiCall(() async {
        final response = await _dio.get('/parcelles/$id/');
        return ParcelDetail.fromJson(response.data);
      });

  Future<Result<List<ParcelModel>>> fetchMyParcels() => safeApiCall(() async {
        final response = await _dio.get('/parcelles/mes-parcelles/');
        return (response.data as List).map((e) => ParcelModel.fromJson(e)).toList();
      });

  Future<Result<Map<String, dynamic>>> submitParcel({
    required String titre,
    required String description,
    required String localisation,
    required String region,
    required double latitude,
    required double longitude,
    required double superficie,
    required double prix,
    required String typeTerrain,
    required String documentPath,
    List<String> photoPaths = const [],
  }) =>
      safeApiCall(() async {
        final formData = FormData.fromMap({
          'titre': titre,
          'description': description,
          'localisation': localisation,
          'region': region,
          'latitude': latitude,
          'longitude': longitude,
          'superficie': superficie,
          'prix': prix,
          'type_terrain': typeTerrain,
          'document': await MultipartFile.fromFile(documentPath),
          'photos': [
            for (final p in photoPaths) await MultipartFile.fromFile(p),
          ],
        });
        final response = await _dio.post('/parcelles/', data: formData);
        return response.data as Map<String, dynamic>;
      });

  Future<Result<Map<String, dynamic>>> verifyCertificate(String hash) => safeApiCall(() async {
        final response = await _dio.get('/certificats/verifier/', queryParameters: {'hash': hash});
        return response.data as Map<String, dynamic>;
      });
}

final parcelRepositoryProvider = Provider<ParcelRepository>(
  (ref) => ParcelRepository(ref.watch(dioProvider)),
);

// ═══════════════════════════════════════════════════════════════
