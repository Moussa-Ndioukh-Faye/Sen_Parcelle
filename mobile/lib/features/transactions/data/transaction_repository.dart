// lib/features/transactions/data/transaction_repository.dart
// ═════════════════════════════════════════════════════

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sen_parcelle/core/network/dio_client.dart';
import 'package:sen_parcelle/core/network/result.dart';
import 'package:sen_parcelle/core/network/api_exception.dart';
import '../domain/transaction_model.dart';

class TransactionRepository {
  final Dio _dio;
  TransactionRepository(this._dio);

  Future<Result<InitiatePaymentResponse>> initiatePayment({
    required String parcelId,
    required String provider,
  }) async {
    try {
      final response = await _dio.post('/transactions/initier/', data: {
        'parcel_id': parcelId,
        'provider': provider,
      });
      return Success(InitiatePaymentResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<Result<List<TransactionModel>>> fetchMyPurchases() async {
    try {
      final response = await _dio.get('/transactions/mes-achats/');
      return Success((response.data as List).map((e) => TransactionModel.fromJson(e)).toList());
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }

  Future<Result<List<TransactionModel>>> fetchMySales() async {
    try {
      final response = await _dio.get('/transactions/mes-ventes/');
      return Success((response.data as List).map((e) => TransactionModel.fromJson(e)).toList());
    } on DioException catch (e) {
      return Failure(ApiException.fromDioError(e));
    } catch (e) {
      return Failure(ApiException(code: 'unknown', message: e.toString()));
    }
  }
}

final transactionRepositoryProvider = Provider<TransactionRepository>(
  (ref) => TransactionRepository(ref.watch(dioProvider)),
);
