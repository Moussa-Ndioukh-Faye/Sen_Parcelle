import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/core/network/dio_client.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/core/network/api_exception.dart';

void main() {
  group('ApiException', () {
    test('devrait créer une exception avec message', () {
      final exc = ApiException(code: 'network', message: 'Erreur réseau');
      expect(exc.message, 'Erreur réseau');
      expect(exc.toString(), contains('Erreur réseau'));
    });

    test('devrait créer une exception avec code statut', () {
      final exc = ApiException(code: '401', message: 'Non autorisé', statusCode: 401);
      expect(exc.statusCode, 401);
    });

    test('fromDioError crée une ApiException pour timeout', () {
      final dioErr = DioException(
        requestOptions: RequestOptions(path: '/test'),
        type: DioExceptionType.connectionTimeout,
      );
      final exc = ApiException.fromDioError(dioErr);
      expect(exc.code, 'timeout');
      expect(exc.message, contains('connexion'));
    });

    test('fromDioError crée une ApiException pour connectionError', () {
      final dioErr = DioException(
        requestOptions: RequestOptions(path: '/test'),
        type: DioExceptionType.connectionError,
      );
      final exc = ApiException.fromDioError(dioErr);
      expect(exc.code, 'no_connection');
      expect(exc.message, contains('connexion'));
    });
  });

  group('Result', () {
    test('Success contient la valeur', () {
      const result = Success<String>('OK');
      expect(result.isSuccess, true);
      expect(result.isFailure, false);
      expect(result.dataOrNull, 'OK');
    });

    test('Failure contient l\'erreur', () {
      final result = Failure<String>(ApiException(code: 'err', message: 'Erreur'));
      expect(result.isSuccess, false);
      expect(result.isFailure, true);
      expect(result.errorOrNull, isA<ApiException>());
    });

    test('when success appelle le callback', () {
      var called = false;
      const result = Success<String>('test');
      result.when(success: (_) => called = true, failure: (_) => null);
      expect(called, true);
    });

    test('when failure appelle le callback', () {
      var called = false;
      final result = Failure<String>(ApiException(code: 'e', message: 'err'));
      result.when(success: (_) => null, failure: (_) => called = true);
      expect(called, true);
    });

    test('when success appelle le callback', () {
      var called = false;
      const result = Success<String>('test');
      result.when(success: (_) => called = true, failure: (_) => null);
      expect(called, true);
    });

    test('when failure appelle le callback', () {
      var called = false;
      final result = Failure<String>(ApiException(code: 'e', message: 'err'));
      result.when(success: (_) => null, failure: (_) => called = true);
      expect(called, true);
    });
  });

  group('dioProvider', () {
    test('devrait avoir le bon baseUrl', () {
      final container = ProviderContainer();
      final dio = container.read(dioProvider);
      expect(dio.options.baseUrl, 'http://10.0.2.2:8000/api');
    });

    test('devrait configurer le timeout', () {
      final container = ProviderContainer();
      final dio = container.read(dioProvider);
      expect(dio.options.connectTimeout?.inMilliseconds, 10000);
      expect(dio.options.receiveTimeout?.inMilliseconds, 30000);
    });

    test('devrait ajouter le header JSON', () {
      final container = ProviderContainer();
      final dio = container.read(dioProvider);
      expect(dio.options.contentType, 'application/json');
    });
  });
}
