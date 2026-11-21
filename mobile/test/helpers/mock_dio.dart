import 'dart:typed_data';

import 'package:dio/dio.dart';

Dio createMockDio({int statusCode = 200, dynamic data}) {
  final dio = Dio();
  dio.options.baseUrl = 'http://test.com/api';
  dio.httpClientAdapter = MockAdapter(
    statusCode: statusCode,
    data: data,
  );
  return dio;
}

class MockAdapter implements HttpClientAdapter {
  final int statusCode;
  final dynamic data;

  MockAdapter({this.statusCode = 200, this.data});

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      data != null ? data.toString() : '[]',
      statusCode,
      headers: {
        'content-type': ['application/json'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
