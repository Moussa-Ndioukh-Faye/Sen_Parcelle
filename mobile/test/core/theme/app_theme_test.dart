import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:flutter/material.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('AppTheme', () {
    test('light theme devrait être Material3', () {
      final theme = AppTheme.lightTheme;
      expect(theme.useMaterial3, true);
    });

    test('dark theme devrait être Material3', () {
      final theme = AppTheme.darkTheme;
      expect(theme.useMaterial3, true);
    });

    test('light theme devrait avoir les couleurs primaires', () {
      final theme = AppTheme.lightTheme;
      expect(theme.colorScheme.primary, isNotNull);
      expect(theme.colorScheme.secondary, isNotNull);
    });

    test('light et dark ne devraient pas être identiques', () {
      expect(AppTheme.lightTheme.brightness, Brightness.light);
      expect(AppTheme.darkTheme.brightness, Brightness.dark);
    });
  });
}
