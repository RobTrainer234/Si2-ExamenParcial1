import 'package:flutter_test/flutter_test.dart';

import 'package:fashionstore_mobile/features/catalog/data/catalog_models.dart';

void main() {
  test('parsea un producto del catálogo', () {
    final item = CatalogItem.fromJson({
      'id': 7,
      'name': 'Camisa Casual',
      'category_name': 'Camisas',
      'price': '199.90',
      'image_url': 'https://example.com/camisa.jpg',
    });

    expect(item.id, 7);
    expect(item.name, 'Camisa Casual');
    expect(item.price, 199.90);
    expect(item.imageUrl, startsWith('https://'));
  });

  test('parsea disponibilidad por sucursal', () {
    final item = AvailabilityItem.fromJson({
      'branch_id': 1,
      'branch_name': 'Sucursal Centro',
      'city_name': 'Santa Cruz',
      'address': 'Av. Principal 10',
      'available': true,
      'stock': 4,
    });

    expect(item.branchName, 'Sucursal Centro');
    expect(item.available, isTrue);
    expect(item.stock, 4);
  });
}
