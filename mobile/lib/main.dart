// ═══════════════════════════════════════════════════════════════
// lib/main.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ─── Forcer orientation portrait ───
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // ─── Status bar transparente ───
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor:           Colors.transparent,
    statusBarIconBrightness:  Brightness.dark,
  ));

  runApp(
    const ProviderScope(
      child: SenParcelleApp(),
    ),
  );
}

class SenParcelleApp extends ConsumerWidget {
  const SenParcelleApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title:            'Sen_parcelle',
      debugShowCheckedModeBanner: false,
      theme:            AppTheme.lightTheme,
      darkTheme:        AppTheme.darkTheme,
      themeMode:        ThemeMode.system,
      routerConfig:     router,
      builder:          (context, child) => _AppWrapper(child: child!),
    );
  }
}

/// Wrapper global : gestion connectivité + overlay loading
class _AppWrapper extends ConsumerWidget {
  final Widget child;
  const _AppWrapper({required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textScaler = MediaQuery.textScalerOf(context);
    return MediaQuery(
      data: MediaQuery.of(context).copyWith(
        textScaler: textScaler.clamp(maxScaleFactor: 1.4),
      ),
      child: child,
    );
  }
}
