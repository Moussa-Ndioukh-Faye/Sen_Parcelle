import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('MaterialApp basic structure', (WidgetTester tester) async {
    await tester.pumpWidget(MaterialApp(
      home: const Scaffold(body: Center(child: Text('Test'))),
    ));
    expect(find.text('Test'), findsOneWidget);
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
