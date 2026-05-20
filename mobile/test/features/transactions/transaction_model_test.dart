import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/features/transactions/domain/transaction_model.dart';

void main() {
  group('TransactionModel', () {
    test('devrait être créé depuis JSON', () {
      final json = {
        'id': 'tx-1',
        'parcel_id': 'parcel-1',
        'buyer_id': 'buyer-1',
        'amount_fcfa': 25000000,
        'provider': 'wave',
        'status': 'completed',
        'payment_ref': 'pay-123',
        'blockchain_tx': '0xabc',
        'created_at': '2026-05-10T12:00:00Z',
      };
      final tx = TransactionModel.fromJson(json);
      expect(tx.id, 'tx-1');
      expect(tx.parcelId, 'parcel-1');
      expect(tx.buyerId, 'buyer-1');
      expect(tx.amountFcfa, 25000000);
      expect(tx.provider, 'wave');
      expect(tx.status, 'completed');
      expect(tx.paymentRef, 'pay-123');
      expect(tx.blockchainTx, '0xabc');
    });

    test('devrait gérer les champs optionnels nulls', () {
      final json = {
        'id': 'tx-2',
        'parcel_id': 'parcel-2',
        'buyer_id': 'buyer-2',
        'amount_fcfa': 1000000,
        'provider': 'orange_money',
        'status': 'pending',
        'created_at': '2026-01-01T00:00:00Z',
      };
      final tx = TransactionModel.fromJson(json);
      expect(tx.paymentRef, isNull);
      expect(tx.blockchainTx, isNull);
    });
  });

  group('InitiatePaymentResponse', () {
    test('devrait être créé depuis JSON', () {
      final json = {
        'transaction_id': 'tx-1',
        'payment_url': 'https://pay.example.com/123',
        'amount': 25000000,
        'provider': 'wave',
        'message': 'Paiement initié',
      };
      final response = InitiatePaymentResponse.fromJson(json);
      expect(response.transactionId, 'tx-1');
      expect(response.paymentUrl, 'https://pay.example.com/123');
      expect(response.amount, 25000000);
      expect(response.provider, 'wave');
      expect(response.message, 'Paiement initié');
    });
  });
}
