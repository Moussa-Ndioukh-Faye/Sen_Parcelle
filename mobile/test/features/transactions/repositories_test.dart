import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/features/transactions/data/transaction_repository.dart';
import 'package:sen_parcelle/features/transactions/data/payment_repository.dart';

void main() {
  group('TransactionRepository', () {
    test('devrait être instancié avec Dio', () {
      final repo = TransactionRepository(Dio());
      expect(repo, isA<TransactionRepository>());
    });
  });

  group('PaymentRepository', () {
    test('devrait être instancié avec Dio', () {
      final repo = PaymentRepository(Dio());
      expect(repo, isA<PaymentRepository>());
    });
  });
}
