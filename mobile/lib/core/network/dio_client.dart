// ═══════════════════════════════════════════════════════════════
// lib/core/network/dio_client.dart
// Client HTTP Dio avec interceptors JWT + retry + offline
// ═══════════════════════════════════════════════════════════════

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

// ─── Config ───
const kBaseUrl     = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000/api');
const kTimeout     = Duration(seconds: 30);
const kConnTimeout = Duration(seconds: 10);

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl:        kBaseUrl,
    connectTimeout: kConnTimeout,
    receiveTimeout: kTimeout,
    headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
  ));

  dio.interceptors.addAll([
    JWTInterceptor(dio, ref),
    RetryInterceptor(dio),
    LoggingInterceptor(),
  ]);

  return dio;
});


// ═══════════════════════════════════════════════════════════════
// INTERCEPTEUR JWT — Injecte le token + refresh auto
// ═══════════════════════════════════════════════════════════════

class JWTInterceptor extends Interceptor {
  final Dio         _dio;
  final Ref         _ref;
  final _storage  = const FlutterSecureStorage();
  bool _isRefreshing = false;

  JWTInterceptor(this._dio, this._ref);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // Routes publiques → pas de token
    final publicRoutes = ['/auth/login/', '/auth/inscription/', '/auth/refresh/'];
    if (publicRoutes.any((r) => options.path.contains(r))) {
      return handler.next(options);
    }

    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      _isRefreshing = true;
      try {
        final newToken = await _refreshToken();
        if (newToken != null) {
          // Rejouer la requête originale avec le nouveau token
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          final response = await _dio.fetch(err.requestOptions);
          _isRefreshing = false;
          return handler.resolve(response);
        }
      } catch (_) {
        // Refresh échoué → déconnecter l'utilisateur
        await _storage.deleteAll();
        _ref.read(authNotifierProvider.notifier).logout();
      }
      _isRefreshing = false;
    }
    handler.next(err);
  }

  Future<String?> _refreshToken() async {
    final refresh = await _storage.read(key: 'refresh_token');
    if (refresh == null) return null;

    final response = await _dio.post('/auth/refresh/', data: {'refresh': refresh});
    final newAccess = response.data['access'] as String;
    await _storage.write(key: 'access_token', value: newAccess);
    return newAccess;
  }
}


// ═══════════════════════════════════════════════════════════════
// INTERCEPTEUR RETRY — Retry automatique en cas d'erreur réseau
// ═══════════════════════════════════════════════════════════════

class RetryInterceptor extends Interceptor {
  final Dio _dio;
  static const _maxRetries = 2;

  RetryInterceptor(this._dio);

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final retries = err.requestOptions.extra['retries'] as int? ?? 0;

    final shouldRetry = (
      err.type == DioExceptionType.connectionTimeout ||
      err.type == DioExceptionType.receiveTimeout   ||
      (err.response?.statusCode != null && err.response!.statusCode! >= 500)
    ) && retries < _maxRetries;

    if (shouldRetry) {
      await Future.delayed(Duration(seconds: (retries + 1) * 2));
      err.requestOptions.extra['retries'] = retries + 1;
      try {
        final response = await _dio.fetch(err.requestOptions);
        return handler.resolve(response);
      } catch (e) {
        return handler.next(err);
      }
    }
    handler.next(err);
  }
}


// ═══════════════════════════════════════════════════════════════
// INTERCEPTEUR LOGGING
// ═══════════════════════════════════════════════════════════════

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    print('→ ${options.method} ${options.path}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    print('← ${response.statusCode} ${response.requestOptions.path}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    print('✗ ${err.response?.statusCode} ${err.requestOptions.path}: ${err.message}');
    handler.next(err);
  }
}
