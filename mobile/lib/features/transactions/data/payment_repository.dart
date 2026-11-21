// lib/features/transactions/data/payment_repository.dart
// ═════════════════════════════════════════════

import 'package:dio/dio.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/core/network/api_exception.dart';

class PaymentRepository {
  final Dio _dio;
  // final _storage = const FlutterSecureStorage();

  PaymentRepository(this._dio);

  Future<Result<PaymentResponse>> initiatePayment({
    required String parcelId,
    required String provider,
  }) async {
    try {
      final response = await _dio.post(
        '/transactions/initier/',
        data: {
          'parcel_id': parcelId,
          'provider': provider,
        },
      );
      return Success(PaymentResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<Result<TransactionDetail>> getTransactionStatus(String txId) async {
    try {
      final response = await _dio.get('/transactions/$txId/');
      return Success(TransactionDetail.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<Result<List<TransactionDetail>>> getMyPurchases() async {
    try {
      final response = await _dio.get('/transactions/mes-achats/');
      final list = (response.data as List)
          .map((json) => TransactionDetail.fromJson(json))
          .toList();
      return Success(list);
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<Result<List<TransactionDetail>>> getMySales() async {
    try {
      final response = await _dio.get('/transactions/mes-ventes/');
      final list = (response.data as List)
          .map((json) => TransactionDetail.fromJson(json))
          .toList();
      return Success(list);
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }
}

class PaymentResponse {
  final String transactionId;
  final String paymentUrl;
  final String status;

  PaymentResponse({
    required this.transactionId,
    required this.paymentUrl,
    required this.status,
  });

  factory PaymentResponse.fromJson(Map<String, dynamic> json) => PaymentResponse(
        transactionId: json['transaction_id'],
        paymentUrl: json['payment_url'],
        status: json['status'],
      );
}

class TransactionDetail {
  final String id;
  final String status;
  final double amount;
  final String provider;
  final String? paymentUrl;

  TransactionDetail({
    required this.id,
    required this.status,
    required this.amount,
    required this.provider,
    this.paymentUrl,
  });

  factory TransactionDetail.fromJson(Map<String, dynamic> json) => TransactionDetail(
        id: json['id'],
        status: json['status'],
        amount: (json['amount'] as num).toDouble(),
        provider: json['provider'],
        paymentUrl: json['payment_url'],
      );
}
