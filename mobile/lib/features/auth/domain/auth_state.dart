import 'package:flutter/foundation.dart';

enum AuthStatus { authenticated, unauthenticated, loading }

@immutable
class AuthState {
  final AuthStatus status;
  final AuthUser? user;
  final String? error;

  const AuthState({
    this.status = AuthStatus.unauthenticated,
    this.user,
    this.error,
  });

  const AuthState.initial()
      : status = AuthStatus.unauthenticated,
        user = null,
        error = null;

  const AuthState.authenticated({required AuthUser user})
      : status = AuthStatus.authenticated,
        user = user,
        error = null;

  const AuthState.loading()
      : status = AuthStatus.loading,
        user = null,
        error = null;

  const AuthState.error(this.error)
      : status = AuthStatus.unauthenticated,
        user = null;

  bool get isAuthenticated => status == AuthStatus.authenticated;
  bool get isLoading => status == AuthStatus.loading;
}

class AuthUser {
  final String id;
  final String email;
  final String nom;
  final String role;
  final String? phone;
  final String? kycStatus;
  final String? avatarUrl;

  const AuthUser({
    required this.id,
    required this.email,
    required this.nom,
    required this.role,
    this.phone,
    this.kycStatus,
    this.avatarUrl,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as String,
      email: json['email'] as String,
      nom: json['nom'] as String,
      role: json['role'] as String,
      phone: json['phone'] as String?,
      kycStatus: json['kyc_status'] as String?,
      avatarUrl: json['avatar_url'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'nom': nom,
        'role': role,
        'phone': phone,
        'kyc_status': kycStatus,
        'avatar_url': avatarUrl,
      };

  String get initials {
    final parts = nom.split(' ');
    if (parts.length >= 2) {
      return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
    }
    return nom.isNotEmpty ? nom[0].toUpperCase() : '?';
  }

  bool get isAdmin => role == 'admin';
  bool get isVendeur => role == 'vendeur';
  bool get isAcheteur => role == 'acheteur';
  bool get kycVerified => kycStatus == 'verified';
}
