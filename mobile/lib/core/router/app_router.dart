// ═══════════════════════════════════════════════════════════════
// lib/core/router/app_router.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:sen_parcelle/features/auth/presentation/providers/auth_provider.dart';
import 'package:sen_parcelle/features/auth/presentation/screens/login_screen.dart';
import 'package:sen_parcelle/features/auth/presentation/screens/register_screen.dart';
import 'package:sen_parcelle/features/auth/presentation/screens/otp_screen.dart';
import 'package:sen_parcelle/features/auth/presentation/screens/splash_screen.dart';
import 'package:sen_parcelle/features/parcels/presentation/screens/home_screen.dart';
import 'package:sen_parcelle/features/parcels/presentation/screens/explore_screen.dart';
import 'package:sen_parcelle/features/parcels/presentation/screens/parcel_detail_screen.dart';
import 'package:sen_parcelle/features/parcels/presentation/screens/publier_screen.dart';
import 'package:sen_parcelle/features/parcels/presentation/screens/certificat_screen.dart';
import 'package:sen_parcelle/features/profile/presentation/screens/profile_screen.dart';
import 'package:sen_parcelle/features/profile/presentation/screens/kyc_screen.dart';
import 'package:sen_parcelle/features/messages/presentation/screens/messages_screen.dart';
import 'package:sen_parcelle/shared/widgets/main_shell.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final isLoggedIn    = authState.isAuthenticated;
      final isAuthRoute   = state.matchedLocation.startsWith('/auth');
      final isSplash      = state.matchedLocation == '/splash';

      if (isSplash) return null;
      if (!isLoggedIn && !isAuthRoute) return '/auth/login';
      if (isLoggedIn && isAuthRoute)   return '/home';
      return null;
    },
    routes: [
      GoRoute(path: '/splash',   builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/auth/login',    builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/auth/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(path: '/auth/otp',      builder: (c, s)  => OTPScreen(extra: s.extra as Map<String, dynamic>)),

      ShellRoute(
        builder: (_, __, child) => MainShell(child: child),
        routes: [
          GoRoute(path: '/home',     builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/explore',  builder: (_, __) => const ExploreScreen()),
          GoRoute(path: '/messages', builder: (_, __) => const MessagesScreen()),
          GoRoute(path: '/profile',  builder: (_, __) => const ProfileScreen()),
          GoRoute(
            path: '/parcelle/:id',
            builder: (_, state) => ParcelDetailScreen(id: state.pathParameters['id']!),
          ),
          GoRoute(
            path: '/parcelle/:id/certificat',
            builder: (_, state) => CertificatScreen(parcelId: state.pathParameters['id']!),
          ),
          GoRoute(path: '/publier',  builder: (_, __) => const PublierScreen()),
          GoRoute(path: '/kyc',      builder: (_, __) => const KYCScreen()),
        ],
      ),
    ],
    errorBuilder: (_, state) => Scaffold(
      body: Center(child: Text('Page introuvable : ${state.error}')),
    ),
  );
});
