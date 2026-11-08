class ReservationItem {
  const ReservationItem({
    required this.productName,
    required this.sizeName,
    required this.colorName,
    required this.quantity,
    required this.unitPrice,
  });
  final String productName;
  final String sizeName;
  final String colorName;
  final int quantity;
  final double unitPrice;

  factory ReservationItem.fromJson(Map<String, dynamic> json) =>
      ReservationItem(
        productName: json['product_name'] as String,
        sizeName: json['size_name'] as String,
        colorName: json['color_name'] as String,
        quantity: json['quantity'] as int,
        unitPrice: double.parse('${json['unit_price']}'),
      );
}

class Reservation {
  const Reservation({
    required this.id,
    required this.branchName,
    required this.status,
    required this.scheduledFor,
    required this.expiresAt,
    required this.items,
  });
  final int id;
  final String branchName;
  final String status;
  final DateTime? scheduledFor;
  final DateTime? expiresAt;
  final List<ReservationItem> items;

  factory Reservation.fromJson(Map<String, dynamic> json) => Reservation(
    id: json['id'] as int,
    branchName: json['branch_name'] as String,
    status: json['status'] as String,
    scheduledFor: json['scheduled_for'] == null
        ? null
        : DateTime.parse(json['scheduled_for'] as String),
    expiresAt: json['expires_at'] == null
        ? null
        : DateTime.parse(json['expires_at'] as String),
    items: (json['items'] as List<dynamic>)
        .map((item) => ReservationItem.fromJson(item as Map<String, dynamic>))
        .toList(),
  );
}
