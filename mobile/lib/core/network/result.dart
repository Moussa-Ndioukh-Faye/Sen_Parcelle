import 'package:dio/dio.dart';
import 'api_exception.dart';

sealed class Result<T> {
  const Result();
}

class Success<T> extends Result<T> {
  final T data;
  const Success(this.data);
}

class Failure<T> extends Result<T> {
  final ApiException error;
  const Failure(this.error);
}

extension ResultExtension<T> on Result<T> {
  bool get isSuccess => this is Success<T>;
  bool get isFailure => this is Failure<T>;

  T? get dataOrNull => isSuccess ? (this as Success<T>).data : null;
  ApiException? get errorOrNull => isFailure ? (this as Failure<T>).error : null;

  R when<R>({
    required R Function(T data) success,
    required R Function(ApiException error) failure,
  }) {
    return switch (this) {
      Success<T> s => success(s.data),
      Failure<T> f => failure(f.error),
    };
  }
}

/// Helper pour wrapper les appels API en Result<T>
Future<Result<T>> safeApiCall<T>(Future<T> Function() call) async {
  try {
    return Success(await call());
  } on DioException catch (e) {
    return Failure(ApiException.fromDioError(e));
  } catch (e) {
    return Failure(ApiException(code: 'unknown', message: e.toString()));
  }
}
