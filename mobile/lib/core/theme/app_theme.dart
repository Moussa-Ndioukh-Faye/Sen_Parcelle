// lib/core/theme/app_theme.dart
// ═════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ─── Couleurs principales ───
  static const greenDark = Color(0xFF1B5E20);
  static const green = Color(0xFF4CAF50);
  static const greenLight = Color(0xFFC8E6C9);
  static const greenBg = Color(0xFFE8F5E9);

  static const amber = Color(0xFFFFB300);
  static const red = Color(0xFFE53935);
  static const slate = Color(0xFF455A64);

  static const bgLight = Color(0xFFF5F5F5);
  static const muted = Color(0xFF757575);

  // ─── Tokens additionnels ───
  static const surfaceDark = Color(0xFF0F172A);
  static const green400 = Color(0xFF4ADE80);

  // ─── Spacing tokens ───
  static const double space4 = 4;
  static const double space8 = 8;
  static const double space12 = 12;
  static const double space16 = 16;
  static const double space20 = 20;
  static const double space24 = 24;
  static const double space32 = 32;
  static const double space40 = 40;

  // ─── Radius tokens ───
  static const double radiusSm = 8;
  static const double radiusMd = 12;
  static const double radiusLg = 16;
  static const double radiusXl = 20;
  static const double radiusFull = 999;

  // ─── Light Theme ───
  static final lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: green,
      brightness: Brightness.light,
    ),
    textTheme: GoogleFonts.dmSansTextTheme(),
    appBarTheme: const AppBarTheme(
      backgroundColor: greenDark,
      foregroundColor: Colors.white,
      elevation: 0,
    ),
  );

  // ─── Dark Theme ───
  static final darkTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: green,
      brightness: Brightness.dark,
    ),
    textTheme: GoogleFonts.dmSansTextTheme(ThemeData.dark().textTheme),
    scaffoldBackgroundColor: surfaceDark,
    appBarTheme: const AppBarTheme(
      backgroundColor: surfaceDark,
      foregroundColor: Colors.white,
      elevation: 0,
    ),
  );

  // ─── Gradient decorations ───
  static BoxDecoration gradientDecoration() => const BoxDecoration(
        gradient: LinearGradient(
          colors: [greenDark, green],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      );
}
