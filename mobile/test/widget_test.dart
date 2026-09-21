import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fashionstore_mobile/main.dart';

void main() {
  testWidgets('muestra estado inicial premium mientras restaura sesión', (
    tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: FashionStoreApp()));

    expect(find.text('Preparando tu experiencia'), findsOneWidget);
    expect(find.byIcon(Icons.auto_awesome_outlined), findsOneWidget);
  });
}
