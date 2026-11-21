import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/features/auth/presentation/providers/auth_provider.dart';
import 'package:sen_parcelle/features/auth/domain/auth_state.dart';

void main() {
  group('AuthNotifierState', () {
    test('initial state devrait être unauthenticated', () {
      const state = AuthNotifierState();
      expect(state.isAuthenticated, false);
      expect(state.isLoading, false);
      expect(state.error, isNull);
    });
  });

  group('isAdmin', () {
    test('devrait être vrai pour admin', () {
      const user = AuthUser(
        id: '1',
        email: 'admin@sn',
        nom: 'Admin',
        role: 'admin',
      );
      expect(user.isAdmin, true);
      expect(user.isVendeur, false);
      expect(user.isAcheteur, false);
    });

    test('devrait être vrai pour vendeur', () {
      const user = AuthUser(
        id: '2',
        email: 'vendeur@sn',
        nom: 'Vendeur',
        role: 'vendeur',
      );
      expect(user.isAdmin, false);
      expect(user.isVendeur, true);
      expect(user.isAcheteur, false);
    });

    test('devrait être vrai pour acheteur', () {
      const user = AuthUser(
        id: '3',
        email: 'acheteur@sn',
        nom: 'Acheteur',
        role: 'acheteur',
      );
      expect(user.isAdmin, false);
      expect(user.isVendeur, false);
      expect(user.isAcheteur, true);
    });
  });

  group('AuthUser.initials', () {
    test('devrait retourner les initiales', () {
      const user = AuthUser(
        id: '1',
        email: 'test@sn',
        nom: 'Moussa Faye',
        role: 'admin',
      );
      expect(user.initials, 'MF');
    });

    test('devrait gérer les noms simples', () {
      const user = AuthUser(
        id: '1',
        email: 'test@sn',
        nom: 'Admin',
        role: 'admin',
      );
      expect(user.initials, 'A');
    });
  });

  group('AuthUser.fromJson', () {
    test('devrait parser le JSON correctement', () {
      final json = {
        'id': 'user-1',
        'email': 'test@sn',
        'nom': 'Test User',
        'role': 'vendeur',
        'phone': '+221771234567',
        'kyc_status': 'verified',
      };
      final user = AuthUser.fromJson(json);
      expect(user.id, 'user-1');
      expect(user.email, 'test@sn');
      expect(user.nom, 'Test User');
      expect(user.role, 'vendeur');
      expect(user.phone, '+221771234567');
      expect(user.kycVerified, true);
    });

    test('toJson doit produire le bon format', () {
      const user = AuthUser(
        id: '1',
        email: 'a@sn',
        nom: 'A',
        role: 'acheteur',
      );
      final json = user.toJson();
      expect(json['id'], '1');
      expect(json['email'], 'a@sn');
      expect(json['role'], 'acheteur');
    });
  });
}
