double _parseDecimal(dynamic value) {
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value) ?? 0.0;
  return 0.0;
}

double? _parseNullableDecimal(dynamic value) {
  if (value == null) return null;
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value);
  return null;
}

class ExchangeLookupItem {
  const ExchangeLookupItem({
    required this.id,
    required this.variantId,
    required this.name,
    required this.sku,
    required this.purchasedQuantity,
    required this.netPaidLineTotal,
    required this.remainingExchangeableQuantity,
  });

  final int id;
  final int variantId;
  final String name;
  final String sku;
  final int purchasedQuantity;
  final double netPaidLineTotal;
  final int remainingExchangeableQuantity;

  ExchangeLookupItem copyWith({int? remainingExchangeableQuantity}) =>
      ExchangeLookupItem(
        id: id,
        variantId: variantId,
        name: name,
        sku: sku,
        purchasedQuantity: purchasedQuantity,
        netPaidLineTotal: netPaidLineTotal,
        remainingExchangeableQuantity:
            remainingExchangeableQuantity ?? this.remainingExchangeableQuantity,
      );

  factory ExchangeLookupItem.fromJson(Map<String, dynamic> json) =>
      ExchangeLookupItem(
        id: json['id'] as int,
        variantId: json['variant_id'] as int,
        name: json['name'] as String,
        sku: json['sku'] as String,
        purchasedQuantity: json['purchased_quantity'] as int,
        netPaidLineTotal: _parseDecimal(json['net_paid_line_total']),
        remainingExchangeableQuantity:
            json['remaining_exchangeable_quantity'] as int,
      );
}

class ExchangeLookupResult {
  const ExchangeLookupResult({
    required this.saleId,
    required this.orderNumber,
    required this.saleDate,
    required this.branchId,
    required this.status,
    required this.items,
  });

  final int saleId;
  final String orderNumber;
  final String saleDate;
  final int branchId;
  final String status;
  final List<ExchangeLookupItem> items;

  ExchangeLookupResult copyWith({List<ExchangeLookupItem>? items}) =>
      ExchangeLookupResult(
        saleId: saleId,
        orderNumber: orderNumber,
        saleDate: saleDate,
        branchId: branchId,
        status: status,
        items: items ?? this.items,
      );

  factory ExchangeLookupResult.fromJson(Map<String, dynamic> json) =>
      ExchangeLookupResult(
        saleId: json['sale_id'] as int,
        orderNumber: json['order_number'] as String,
        saleDate: json['sale_date'].toString(),
        branchId: json['branch_id'] as int,
        status: json['status'] as String,
        items: ((json['items'] as List<dynamic>?) ?? const [])
            .map(
              (item) =>
                  ExchangeLookupItem.fromJson(Map<String, dynamic>.from(item as Map)),
            )
            .toList(),
      );
}

class ExchangeReplacementOption {
  const ExchangeReplacementOption({
    required this.inventoryId,
    required this.branchId,
    required this.branchName,
    required this.variantId,
    required this.productId,
    required this.productName,
    required this.sku,
    required this.sizeName,
    required this.colorName,
    required this.availableQuantity,
    required this.available,
  });

  final int inventoryId;
  final int branchId;
  final String branchName;
  final int variantId;
  final int productId;
  final String productName;
  final String sku;
  final String sizeName;
  final String colorName;
  final int availableQuantity;
  final bool available;

  String get displayLabel =>
      '$productName ($sizeName / $colorName) · SKU $sku · Disp: $availableQuantity';

  factory ExchangeReplacementOption.fromJson(Map<String, dynamic> json) =>
      ExchangeReplacementOption(
        inventoryId: json['id'] as int,
        branchId: json['branch_id'] as int,
        branchName: (json['branch_name'] ?? '').toString(),
        variantId: json['product_variant_id'] as int,
        productId: json['product_id'] as int,
        productName: json['product_name'] as String,
        sku: json['sku'] as String,
        sizeName: (json['size_name'] ?? '').toString(),
        colorName: (json['color_name'] ?? '').toString(),
        availableQuantity: (json['available_quantity'] as int?) ?? 0,
        available: (json['available'] as bool?) ?? false,
      );
}

class ExchangeQuoteRequest {
  const ExchangeQuoteRequest({
    required this.returnedVariantId,
    required this.returnedQuantity,
    required this.newVariantId,
    required this.newQuantity,
  });

  final int returnedVariantId;
  final int returnedQuantity;
  final int newVariantId;
  final int newQuantity;

  Map<String, dynamic> toJson() => {
    'returned_variant_id': returnedVariantId,
    'returned_quantity': returnedQuantity,
    'new_variant_id': newVariantId,
    'new_quantity': newQuantity,
  };
}

class ExchangeQuote {
  const ExchangeQuote({
    required this.saleId,
    required this.saleItemId,
    required this.returnedVariantId,
    required this.returnedQuantity,
    required this.newVariantId,
    required this.newQuantity,
    required this.returnedValue,
    required this.replacementUnitPrice,
    required this.deliveredValue,
    required this.difference,
    required this.cashSettlementEligible,
    required this.availableStock,
    required this.reservedStock,
    required this.expiresAt,
    required this.quoteFingerprint,
  });

  final int saleId;
  final int saleItemId;
  final int returnedVariantId;
  final int returnedQuantity;
  final int newVariantId;
  final int newQuantity;
  final double returnedValue;
  final double replacementUnitPrice;
  final double deliveredValue;
  final double difference;
  final bool cashSettlementEligible;
  final int availableStock;
  final int reservedStock;
  final String expiresAt;
  final String quoteFingerprint;

  factory ExchangeQuote.fromJson(Map<String, dynamic> json) => ExchangeQuote(
    saleId: json['sale_id'] as int,
    saleItemId: json['sale_item_id'] as int,
    returnedVariantId: json['returned_variant_id'] as int,
    returnedQuantity: json['returned_quantity'] as int,
    newVariantId: json['new_variant_id'] as int,
    newQuantity: json['new_quantity'] as int,
    returnedValue: _parseDecimal(json['returned_value']),
    replacementUnitPrice: _parseDecimal(json['replacement_unit_price']),
    deliveredValue: _parseDecimal(json['delivered_value']),
    difference: _parseDecimal(json['difference']),
    cashSettlementEligible: json['cash_settlement_eligible'] as bool,
    availableStock: json['available_stock'] as int,
    reservedStock: json['reserved_stock'] as int,
    expiresAt: json['expires_at'].toString(),
    quoteFingerprint: json['quote_fingerprint'] as String,
  );
}

class ExchangeFinalizeRequest {
  const ExchangeFinalizeRequest({
    required this.returnedVariantId,
    required this.returnedQuantity,
    required this.newVariantId,
    required this.newQuantity,
    required this.quoteFingerprint,
    required this.quoteExpiresAt,
    required this.idempotencyKey,
    this.cashTendered,
    this.cashierConfirmed = false,
    this.reason,
  });

  final int returnedVariantId;
  final int returnedQuantity;
  final int newVariantId;
  final int newQuantity;
  final String quoteFingerprint;
  final String quoteExpiresAt;
  final String idempotencyKey;
  final String? cashTendered;
  final bool cashierConfirmed;
  final String? reason;

  Map<String, dynamic> toJson() => {
    'returned_variant_id': returnedVariantId,
    'returned_quantity': returnedQuantity,
    'new_variant_id': newVariantId,
    'new_quantity': newQuantity,
    'quote_fingerprint': quoteFingerprint,
    'quote_expires_at': quoteExpiresAt,
    'idempotency_key': idempotencyKey,
    if (cashTendered != null) 'cash_tendered': cashTendered,
    'cashier_confirmed': cashierConfirmed,
    if (reason != null && reason!.trim().isNotEmpty) 'reason': reason!.trim(),
  };
}

class ExchangeReceipt {
  const ExchangeReceipt({
    required this.saleId,
    required this.orderNumber,
    required this.returnedVariantId,
    required this.returnedQuantity,
    required this.newVariantId,
    required this.newQuantity,
    required this.status,
    required this.quarantineId,
    required this.quarantineStatus,
    required this.returnedValue,
    required this.deliveredValue,
    required this.difference,
    this.cashTendered,
    this.cashChange,
    this.cashRefunded,
    required this.exchangedAt,
  });

  final int saleId;
  final String orderNumber;
  final int returnedVariantId;
  final int returnedQuantity;
  final int newVariantId;
  final int newQuantity;
  final String status;
  final int? quarantineId;
  final String? quarantineStatus;
  final double returnedValue;
  final double deliveredValue;
  final double difference;
  final double? cashTendered;
  final double? cashChange;
  final double? cashRefunded;
  final String exchangedAt;

  factory ExchangeReceipt.fromJson(Map<String, dynamic> json) =>
      ExchangeReceipt(
        saleId: json['sale_id'] as int,
        orderNumber: json['order_number'] as String,
        returnedVariantId: json['returned_variant_id'] as int,
        returnedQuantity: json['returned_quantity'] as int,
        newVariantId: json['new_variant_id'] as int,
        newQuantity: json['new_quantity'] as int,
        status: json['status'] as String,
        quarantineId: json['quarantine_id'] as int?,
        quarantineStatus: json['quarantine_status'] as String?,
        returnedValue: _parseDecimal(json['returned_value']),
        deliveredValue: _parseDecimal(json['delivered_value']),
        difference: _parseDecimal(json['difference']),
        cashTendered: _parseNullableDecimal(json['cash_tendered']),
        cashChange: _parseNullableDecimal(json['cash_change']),
        cashRefunded: _parseNullableDecimal(json['cash_refunded']),
        exchangedAt: json['exchanged_at'].toString(),
      );
}
