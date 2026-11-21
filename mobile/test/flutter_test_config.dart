import 'dart:async';

import 'package:google_fonts/google_fonts.dart';

/// Configuration commune à tous les tests Flutter.
///
/// La police DM Sans est embarquée dans `assets/google_fonts/` : les tests
/// n'ont donc jamais besoin de la télécharger (le réseau y est bloqué).
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  GoogleFonts.config.allowRuntimeFetching = false;
  await testMain();
}
