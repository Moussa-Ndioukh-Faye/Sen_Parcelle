import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/features/auth/domain/auth_state.dart';

void main() {
  group('AuthState', () {
    test('initial devrait être unauthenticated', () {
      const state = AuthState.initial();
      expect(state.isAuthenticated, false);
      expect(state.isLoading, false);
      expect(state.user, isNull);
      expect(state.error, isNull);
    });

    test('authenticated devrait renvoyer isAuthenticated true', () {
      final state = AuthState.authenticated(
        user: AuthUser(id: '1', email: 'test@sn', nom: 'Test', role: 'acheteur'),
      );
      expect(state.isAuthenticated, true);
      expect(state.user!.email, 'test@sn');
    });

    test('loading devrait renvoyer isLoading true', () {
      const state = AuthState.loading();
      expect(state.isLoading, true);
    });

    test('error devrait contenir le message', () {
      const state = AuthState.error('Erreur de connexion');
      expect(state.error, 'Erreur de connexion');
      expect(state.isAuthenticated, false);
    });
  });
}
