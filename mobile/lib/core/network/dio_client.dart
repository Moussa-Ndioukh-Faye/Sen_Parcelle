// ═══════════════════════════════════════════════════════════════
// lib/core/network/dio_client.dart
// Client HTTP Dio avec interceptors JWT + retry + offline
// ═══════════════════════════════════════════════════════════════

import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

// ─── Config ───
const kBaseUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000/api');
const kTimeout = Duration(seconds: 30);
const kConnTimeout = Duration(seconds: 10);

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: kBaseUrl,
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
  final Dio _dio;
  final Ref _ref;
  final _storage = const FlutterSecureStorage();
  bool _isRefreshing = false;
  Completer<String?>? _refreshTokenCompleter;

  JWTInterceptor(this._dio, this._ref);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // Routes publiques → pas de token
    final publicRoutes = ['/auth/login/', '/auth/inscription/', '/auth/token/refresh/'];
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
    if (err.response?.statusCode == 401) {
      // Si une session de rafraîchissement est déjà en cours, on attend
      if (_isRefreshing) {
        final token = await _refreshTokenCompleter?.future;
        if (token != null) {
          err.requestOptions.headers['Authorization'] = 'Bearer $token';
          final response = await _dio.fetch(err.requestOptions);
          return handler.resolve(response);
        }
      } else {
        _isRefreshing = true;
        _refreshTokenCompleter = Completer<String?>();
        try {
          final newToken = await _refreshToken();
          _refreshTokenCompleter?.complete(newToken);
          _isRefreshing = false;

          if (newToken != null) {
            err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
            final response = await _dio.fetch(err.requestOptions);
            return handler.resolve(response);
          }
        } catch (_) {
          _refreshTokenCompleter?.complete(null);
          _isRefreshing = false;
          await _storage.deleteAll();
          _ref.read(authNotifierProvider.notifier).logout();
        }
      }
    }
    handler.next(err);
  }

  Future<String?> _refreshToken() async {
    final refresh = await _storage.read(key: 'refresh_token');
    if (refresh == null) return null;

    final response = await _dio.post('/auth/token/refresh/', data: {'refresh': refresh});
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

    final shouldRetry = (err.type == DioExceptionType.connectionTimeout ||
            err.type == DioExceptionType.receiveTimeout ||
            (err.response?.statusCode != null && err.response!.statusCode! >= 500)) &&
        retries < _maxRetries;

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
// INTERCEPTEUR LOGGING (masque les tokens et données sensibles)
// ═══════════════════════════════════════════════════════════════

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final sanitizedPath = options.path.replaceAll(RegExp(r'token=[^&]+'), 'token=***');
    debugPrint('→ ${options.method} $sanitizedPath');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    final sanitizedPath = response.requestOptions.path.replaceAll(RegExp(r'token=[^&]+'), 'token=***');
    debugPrint('← ${response.statusCode} $sanitizedPath');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final sanitizedPath = err.requestOptions.path.replaceAll(RegExp(r'token=[^&]+'), 'token=***');
    debugPrint('✗ ${err.response?.statusCode} $sanitizedPath: ${err.message}');
    handler.next(err);
  }
}
