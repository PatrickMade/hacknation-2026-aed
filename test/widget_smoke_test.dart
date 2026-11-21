import 'package:aed_dane_na_ratunek/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('app starts and shows its home screen', (tester) async {
    await tester.pumpWidget(const MainApp());

    expect(find.text('Hello World!'), findsOneWidget);
  });
}
