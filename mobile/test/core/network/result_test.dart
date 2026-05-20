import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/core/network/api_exception.dart';

void main() {
  group('Result', () {
    test('Success contient la valeur', () {
      const result = Success<int>(42);
      expect(result.isSuccess, true);
      expect(result.isFailure, false);
      expect(result.dataOrNull, 42);
    });

    test('Failure contient l\'erreur', () {
      final result = Failure<int>(ApiException(code: 'err', message: 'test error'));
      expect(result.isSuccess, false);
      expect(result.isFailure, true);
      expect(result.errorOrNull, isA<ApiException>());
      expect(result.errorOrNull!.message, 'test error');
    });

    test('when success transforme la valeur', () {
      const result = Success<int>(5);
      final transformed = result.when(
        success: (v) => v * 2,
        failure: (e) => 0,
      );
      expect(transformed, 10);
    });

    test('when failure retourne la valeur par défaut', () {
      final result = Failure<int>(ApiException(code: 'err', message: 'err'));
      final transformed = result.when(
        success: (v) => v,
        failure: (e) => -1,
      );
      expect(transformed, -1);
    });

    test('dataOrNull retourne la valeur sur success', () {
      const result = Success<int>(7);
      expect(result.dataOrNull, 7);
    });

    test('dataOrNull retourne null sur failure', () {
      final result = Failure<int>(ApiException(code: 'err', message: 'err'));
      expect(result.dataOrNull, isNull);
    });

    test('safeApiCall retourne Success quand la fonction réussit', () async {
      final result = await safeApiCall<int>(() async => 42);
      expect(result.isSuccess, true);
      expect(result.dataOrNull, 42);
    });

    test('safeApiCall retourne Failure quand la fonction échoue', () async {
      final result = await safeApiCall<int>(() async => throw DioException(
        requestOptions: RequestOptions(path: '/test'),
        type: DioExceptionType.connectionTimeout,
      ));
      expect(result.isFailure, true);
    });
  });
}
