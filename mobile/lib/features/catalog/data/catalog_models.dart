class CatalogItem {
  const CatalogItem({
    required this.id,
    required this.name,
    required this.categoryName,
    required this.price,
    this.imageUrl,
  });
  final int id;
  final String name;
  final String categoryName;
  final double price;
  final String? imageUrl;

  factory CatalogItem.fromJson(Map<String, dynamic> json) => CatalogItem(
    id: json['id'] as int,
    name: json['name'] as String,
    categoryName: json['category_name'] as String,
    price: double.parse('${json['price']}'),
    imageUrl: json['image_url'] as String?,
  );
}

class CatalogPage {
  const CatalogPage(this.items, this.totalPages);
  final List<CatalogItem> items;
  final int totalPages;
}

class CatalogVariant {
  const CatalogVariant({
    required this.id,
    required this.sizeId,
    required this.sizeName,
    required this.colorId,
    required this.colorName,
  });
  final int id;
  final int sizeId;
  final String sizeName;
  final int colorId;
  final String colorName;

  factory CatalogVariant.fromJson(Map<String, dynamic> json) => CatalogVariant(
    id: json['id'] as int,
    sizeId: json['size_id'] as int,
    sizeName: json['size_name'] as String,
    colorId: json['color_id'] as int,
    colorName: json['color_name'] as String,
  );
}

class CatalogDetail extends CatalogItem {
  const CatalogDetail({
    required super.id,
    required super.name,
    required super.categoryName,
    required super.price,
    super.imageUrl,
    required this.description,
    required this.variants,
  });
  final String? description;
  final List<CatalogVariant> variants;

  factory CatalogDetail.fromJson(Map<String, dynamic> json) => CatalogDetail(
    id: json['id'] as int,
    name: json['name'] as String,
    categoryName: json['category_name'] as String,
    price: double.parse('${json['price']}'),
    description: json['description'] as String?,
    variants: (json['variants'] as List<dynamic>)
        .map((item) => CatalogVariant.fromJson(item as Map<String, dynamic>))
        .toList(),
    imageUrl: (json['images'] as List<dynamic>).isEmpty
        ? null
        : ((json['images'] as List<dynamic>).first
                  as Map<String, dynamic>)['image_url']
              as String?,
  );
}

class AvailabilityItem {
  const AvailabilityItem({
    required this.branchName,
    required this.cityName,
    required this.address,
    required this.available,
    required this.stock,
  });
  final String branchName;
  final String cityName;
  final String address;
  final bool available;
  final int stock;

  factory AvailabilityItem.fromJson(Map<String, dynamic> json) =>
      AvailabilityItem(
        branchName: json['branch_name'] as String,
        cityName: json['city_name'] as String,
        address: json['address'] as String,
        available: json['available'] as bool,
        stock: json['stock'] as int,
      );
}
