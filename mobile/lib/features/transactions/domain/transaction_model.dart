// lib/features/transactions/domain/transaction_model.dart
// ═══════════════════════════════════════════════════════════════

class TransactionModel {
  final String id;
  final String parcelId;
  final String buyerId;
  final double amountFcfa;
  final String provider;
  final String status;
  final String? paymentRef;
  final String? blockchainTx;
  final DateTime createdAt;

  const TransactionModel({
    required this.id,
    required this.parcelId,
    required this.buyerId,
    required this.amountFcfa,
    required this.provider,
    required this.status,
    this.paymentRef,
    this.blockchainTx,
    required this.createdAt,
  });

  factory TransactionModel.fromJson(Map<String, dynamic> j) => TransactionModel(
        id: j['id'] as String,
        parcelId: j['parcel_id'] as String,
        buyerId: j['buyer_id'] as String,
        amountFcfa: (j['amount_fcfa'] as num).toDouble(),
        provider: j['provider'] as String,
        status: j['status'] as String,
        paymentRef: j['payment_ref'] as String?,
        blockchainTx: j['blockchain_tx'] as String?,
        createdAt: DateTime.parse(j['created_at'] as String),
      );
}

class InitiatePaymentResponse {
  final String transactionId;
  final String paymentUrl;
  final double amount;
  final String provider;
  final String message;

  const InitiatePaymentResponse({
    required this.transactionId,
    required this.paymentUrl,
    required this.amount,
    required this.provider,
    required this.message,
  });

  factory InitiatePaymentResponse.fromJson(Map<String, dynamic> j) =>
      InitiatePaymentResponse(
        transactionId: j['transaction_id'] as String,
        paymentUrl: j['payment_url'] as String,
        amount: (j['amount'] as num).toDouble(),
        provider: j['provider'] as String,
        message: j['message'] as String,
      );
}
