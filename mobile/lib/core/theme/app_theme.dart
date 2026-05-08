// lib/core/theme/app_theme.dart
// ═════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ─── Couleurs principales ───
  static const greenDark  = Color(0xFF1B5E20);
  static const green       = Color(0xFF4CAF50);
  static const greenLight = Color(0xFFC8E6C9);
  static const greenBg    = Color(0xFFE8F5E9);

  static const amber      = Color(0xFFFFB300);
  static const red        = Color(0xFFE53935);
  static const slate      = Color(0xFF455A64);

  static const bgLight   = Color(0xFFF5F5F5);
  static const muted     = Color(0xFF757575);

  // ─── Light Theme ───
  static final lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: green,
      brightness: Brightness.light,
    ),
    textTheme: GoogleFonts.dmSansTextTheme(),
    appBarTheme: AppBarTheme(
      backgroundColor: greenDark,
      foregroundColor: Colors.white,
      elevation: 0,
    ),
  );

  // ─── Gradient decorations ───
  static BoxDecoration gradientDecoration() => BoxDecoration(
        gradient: LinearGradient(
          colors: [greenDark, green],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      );
}
