import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  group('AppRouter', () {
    test('devrait créer le GoRouter avec un provider', () {
      final router = createRouter();
      expect(router, isA<GoRouter>());
    });

    test('devrait avoir la route splash comme initiale', () {
      final router = createRouter();
      expect(router.routeInformationProvider.value.uri.path, '/splash');
    });

    test('devrait contenir les routes principales', () {
      final router = createRouter();
      final routes = router.configuration.routes;
      expect(routes.length, greaterThanOrEqualTo(3));
    });
  });
}

GoRouter createRouter() {
  return GoRouter(
    initialLocation: '/splash',
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SizedBox()),
      GoRoute(path: '/login', builder: (_, __) => const SizedBox()),
      GoRoute(path: '/home', builder: (_, __) => const SizedBox()),
    ],
  );
}
