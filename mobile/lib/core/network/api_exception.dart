import 'package:dio/dio.dart';

class ApiException implements Exception {
  final String  code;
  final String  message;
  final int?    statusCode;
  final Map<String, dynamic>? details;

  const ApiException({
    required this.code,
    required this.message,
    this.statusCode,
    this.details,
  });

  factory ApiException.fromDioError(DioException e) {
    final data = e.response?.data;

    if (data is Map && data.containsKey('error')) {
      final error = data['error'] as Map<String, dynamic>;
      return ApiException(
        code:       error['code']    as String? ?? 'unknown',
        message:    error['message'] as String? ?? 'Erreur inconnue',
        statusCode: e.response?.statusCode,
        details:    error['details'] as Map<String, dynamic>?,
      );
    }

    // Erreurs réseau
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return const ApiException(
        code:    'timeout',
        message: 'La connexion a expiré. Vérifiez votre réseau.',
      );
    }

    if (e.type == DioExceptionType.connectionError) {
      return const ApiException(
        code:    'no_connection',
        message: 'Pas de connexion internet.',
      );
    }

    return ApiException(
      code:       'server_error',
      message:    'Erreur serveur. Réessayez.',
      statusCode: e.response?.statusCode,
    );
  }

  bool get isNotFound      => statusCode == 404;
  bool get isUnauthorized  => statusCode == 401;
  bool get isForbidden     => statusCode == 403;
  bool get isValidation    => code == 'validation_error';
  bool get isOffline       => code == 'no_connection';

  @override
  String toString() => 'ApiException($code): $message';
}
