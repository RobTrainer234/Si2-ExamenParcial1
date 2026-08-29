import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';

import 'package:fashionstore_mobile/main.dart';

void main() {
  testWidgets('muestra la aplicacion inicial', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: FashionStoreApp()));

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
