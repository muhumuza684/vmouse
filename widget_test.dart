import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:vmouse/main.dart';

void main() {
  testWidgets('VMouse app builds without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(const VMouseApp());
    await tester.pump();
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
