// lib/features/transactions/presentation/providers/transaction_notifier.dart
// ═══════════════════════════════════════════

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/features/transactions/data/payment_repository.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/core/network/dio_client.dart';

// ─── State ───
class TransactionState {
  final bool isLoading;
  final PaymentResponse? paymentResponse;
  final String? error;

  const TransactionState({
    this.isLoading = false,
    this.paymentResponse,
    this.error,
  });

  TransactionState copyWith({
    bool? isLoading,
    PaymentResponse? paymentResponse,
    String? error,
  }) =>
      TransactionState(
        isLoading: isLoading ?? this.isLoading,
        paymentResponse: paymentResponse ?? this.paymentResponse,
        error: error,
      );
}

// ─── Notifier ───
class TransactionNotifier extends StateNotifier<TransactionState> {
  final PaymentRepository _repo;

  TransactionNotifier(this._repo) : super(const TransactionState());

  Future<void> initiatePayment({
    required String parcelId,
    required String provider,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repo.initiatePayment(
      parcelId: parcelId,
      provider: provider,
    );

    result.when(
      success: (data) {
        state = state.copyWith(
          isLoading: false,
          paymentResponse: data,
        );
      },
      failure: (error) {
        state = state.copyWith(
          isLoading: false,
          error: error.message,
        );
      },
    );
  }
}

// ─── Providers ───
final paymentRepositoryProvider = Provider<PaymentRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return PaymentRepository(dio);
});

final transactionNotifierProvider =
    StateNotifierProvider<TransactionNotifier, TransactionState>((ref) {
  final repo = ref.watch(paymentRepositoryProvider);
  return TransactionNotifier(repo);
});
