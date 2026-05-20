import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/features/parcels/data/parcel_repository.dart';
import 'package:sen_parcelle/features/auth/data/auth_repository.dart';

void main() {
  group('ParcelRepository', () {
    test('devrait être instancié avec Dio', () {
      final repo = ParcelRepository(Dio());
      expect(repo, isA<ParcelRepository>());
    });
  });

  group('AuthRepository', () {
    test('devrait être instancié avec Dio', () {
      final repo = AuthRepository(Dio());
      expect(repo, isA<AuthRepository>());
    });
  });
}
