// lib/features/auth/presentation/providers/auth_provider.dart
// ═════════════════════════════════════════════════

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/features/auth/data/auth_repository.dart';
import 'package:sen_parcelle/core/network/result.dart';

// ─── État (NE JAMAIS stocker le mot de passe en mémoire) ───
class AuthNotifierState {
  final bool isLoading;
  final bool isAuthenticated;
  final bool requiresOTP;
  final String? userId;
  final String? role;
  final String? error;
  final String? email;

  const AuthNotifierState({
    this.isLoading = false,
    this.isAuthenticated = false,
    this.requiresOTP = false,
    this.userId,
    this.role,
    this.error,
    this.email,
  });

  AuthNotifierState copyWith({
    bool? isLoading,
    bool? isAuthenticated,
    bool? requiresOTP,
    String? userId,
    String? role,
    String? error,
    String? email,
  }) =>
      AuthNotifierState(
        isLoading: isLoading ?? this.isLoading,
        isAuthenticated: isAuthenticated ?? this.isAuthenticated,
        requiresOTP: requiresOTP ?? this.requiresOTP,
        userId: userId ?? this.userId,
        role: role ?? this.role,
        error: error,
        email: email ?? this.email,
      );
}

// ─── Notifier ───
class AuthNotifier extends StateNotifier<AuthNotifierState> {
  final AuthRepository _repo;

  AuthNotifier(this._repo) : super(const AuthNotifierState()) {
    _checkInitialAuth();
  }

  Future<void> _checkInitialAuth() async {
    final isLoggedIn = await _repo.isLoggedIn();
    if (isLoggedIn) {
      final role = await _repo.getUserRole();
      state = state.copyWith(isAuthenticated: true, role: role);
    }
  }

  Future<void> login(String email, String password, {String? otp}) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repo.login(email: email, password: password, otpCode: otp);

    result.when(
      success: (data) {
        if (data['requires_otp'] == true) {
          state = state.copyWith(
            isLoading: false,
            requiresOTP: true,
            userId: data['user_id'],
            email: email,
          );
        } else {
          state = state.copyWith(
            isLoading: false,
            isAuthenticated: true,
            role: data['role'],
            userId: data['user_id'],
            email: null,
          );
        }
      },
      failure: (error) => state = state.copyWith(
        isLoading: false,
        error: error.message,
      ),
    );
  }

  Future<bool> register({
    required String nom,
    required String email,
    required String telephone,
    required String password,
    String role = 'acheteur',
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repo.register(
      nom: nom,
      email: email,
      telephone: telephone,
      password: password,
      role: role,
    );

    return result.when(
      success: (_) {
        state = state.copyWith(isLoading: false);
        return true;
      },
      failure: (e) {
        state = state.copyWith(isLoading: false, error: e.message);
        return false;
      },
    );
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthNotifierState();
  }
}

final authNotifierProvider = StateNotifierProvider<AuthNotifier, AuthNotifierState>(
  (ref) => AuthNotifier(ref.watch(authRepositoryProvider)),
);
