// lib/features/auth/data/auth_repository.dart
// ═══════════════════════════════════════════════

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/core/network/api_exception.dart';
import 'package:sen_parcelle/core/network/dio_client.dart';

class AuthRepository {
  final Dio     _dio;
  final _storage = const FlutterSecureStorage();

  AuthRepository(this._dio);

  Future<Result<Map<String, dynamic>>> login({
    required String email,
    required String password,
    String? otpCode,
  }) async {
    try {
      final response = await _dio.post('/auth/login/', data: {
        'email':    email,
        'password': password,
        if (otpCode != null) 'otp_code': otpCode,
      });
      final data = response.data as Map<String, dynamic>;
      // Sauvegarder tokens si connexion complète
      if (data['access_token'] != null) {
        await _storage.write(key: 'access_token',  value: data['access_token']);
        await _storage.write(key: 'refresh_token', value: data['refresh_token']);
        await _storage.write(key: 'user_id',       value: data['user_id']);
        await _storage.write(key: 'user_role',     value: data['role']);
      }
      return Success(data);
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<Result<Map<String, dynamic>>> register({
    required String nom,
    required String email,
    required String telephone,
    required String password,
    String role = 'acheteur',
  }) async {
    try {
      final response = await _dio.post('/auth/inscription/', data: {
        'nom': nom, 'email': email, 'telephone': telephone,
        'password': password, 'role': role,
      });
      return Success(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }

  Future<String?> getUserRole() => _storage.read(key: 'user_role');
}

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(dioProvider)),
);



// ═══════════════════════════════════════════════════════════════