// lib/features/profile/presentation/providers/kyc_provider.dart
// ═══════════════════════════════════════════════════════

import 'package:flutter_riverpod/flutter_riverpod.dart';

// ─── State ───
enum KYCStep { info, upload, pending }

class KYCNotifier extends StateNotifier<KYCStep> {
  KYCNotifier() : super(KYCStep.info);
  void goToUpload() => state = KYCStep.upload;
  void goToPending() => state = KYCStep.pending;
}

final kycProvider = StateNotifierProvider<KYCNotifier, KYCStep>(
  (ref) => KYCNotifier(),
);
