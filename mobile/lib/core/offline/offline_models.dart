class SyncMetadata {
  const SyncMetadata({
    required this.tenantId,
    required this.tenantName,
    required this.branchId,
    required this.branchName,
    required this.syncTimestamp,
    required this.catalogVersion,
  });

  final int tenantId;
  final String tenantName;
  final int branchId;
  final String branchName;
  final String syncTimestamp;
  final String catalogVersion;

  factory SyncMetadata.fromJson(Map<String, dynamic> json) => SyncMetadata(
        tenantId: json['tenant_id'] as int,
        tenantName: json['tenant_name'] as String,
        branchId: json['branch_id'] as int,
        branchName: json['branch_name'] as String,
        syncTimestamp: json['sync_timestamp'] as String,
        catalogVersion: json['catalog_version'] as String,
      );

  factory SyncMetadata.fromMap(Map<String, dynamic> map) => SyncMetadata(
        tenantId: map['tenant_id'] as int,
        tenantName: map['tenant_name'] as String,
        branchId: map['branch_id'] as int,
        branchName: map['branch_name'] as String,
        syncTimestamp: map['sync_timestamp'] as String,
        catalogVersion: map['catalog_version'] as String,
      );

  Map<String, dynamic> toMap() => {
        'tenant_id': tenantId,
        'tenant_name': tenantName,
        'branch_id': branchId,
        'branch_name': branchName,
        'sync_timestamp': syncTimestamp,
        'catalog_version': catalogVersion,
      };
}

class SyncCategory {
  const SyncCategory({
    required this.id,
    required this.name,
    this.isActive = true,
  });

  final int id;
  final String name;
  final bool isActive;

  factory SyncCategory.fromJson(Map<String, dynamic> json) => SyncCategory(
        id: json['id'] as int,
        name: json['name'] as String,
        isActive: json['is_active'] as bool? ?? true,
      );

  factory SyncCategory.fromMap(Map<String, dynamic> map) => SyncCategory(
        id: map['id'] as int,
        name: map['name'] as String,
        isActive: (map['is_active'] as int? ?? 1) == 1,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'name': name,
        'is_active': isActive ? 1 : 0,
      };
}

class SyncProduct {
  const SyncProduct({
    required this.id,
    required this.categoryId,
    required this.categoryName,
    required this.name,
    required this.code,
    required this.slug,
    required this.price,
    this.imageUrl,
    this.isActive = true,
  });

  final int id;
  final int categoryId;
  final String categoryName;
  final String name;
  final String code;
  final String slug;
  final double price;
  final String? imageUrl;
  final bool isActive;

  factory SyncProduct.fromJson(Map<String, dynamic> json) => SyncProduct(
        id: json['id'] as int,
        categoryId: json['category_id'] as int,
        categoryName: json['category_name'] as String,
        name: json['name'] as String,
        code: json['code'] as String,
        slug: json['slug'] as String,
        price: double.parse('${json['price']}'),
        imageUrl: json['image_url'] as String?,
        isActive: json['is_active'] as bool? ?? true,
      );

  factory SyncProduct.fromMap(Map<String, dynamic> map) => SyncProduct(
        id: map['id'] as int,
        categoryId: map['category_id'] as int,
        categoryName: map['category_name'] as String,
        name: map['name'] as String,
        code: map['code'] as String,
        slug: map['slug'] as String,
        price: (map['price'] as num).toDouble(),
        imageUrl: map['image_url'] as String?,
        isActive: (map['is_active'] as int? ?? 1) == 1,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'category_id': categoryId,
        'category_name': categoryName,
        'name': name,
        'code': code,
        'slug': slug,
        'price': price,
        'image_url': imageUrl,
        'is_active': isActive ? 1 : 0,
      };
}

class SyncVariant {
  const SyncVariant({
    required this.id,
    required this.productId,
    required this.sku,
    required this.sizeId,
    required this.sizeName,
    required this.colorId,
    required this.colorName,
    required this.price,
    this.isActive = true,
  });

  final int id;
  final int productId;
  final String sku;
  final int sizeId;
  final String sizeName;
  final int colorId;
  final String colorName;
  final double price;
  final bool isActive;

  factory SyncVariant.fromJson(Map<String, dynamic> json) => SyncVariant(
        id: json['id'] as int,
        productId: json['product_id'] as int,
        sku: json['sku'] as String,
        sizeId: json['size_id'] as int,
        sizeName: json['size_name'] as String,
        colorId: json['color_id'] as int,
        colorName: json['color_name'] as String,
        price: double.parse('${json['price']}'),
        isActive: json['is_active'] as bool? ?? true,
      );

  factory SyncVariant.fromMap(Map<String, dynamic> map) => SyncVariant(
        id: map['id'] as int,
        productId: map['product_id'] as int,
        sku: map['sku'] as String,
        sizeId: map['size_id'] as int,
        sizeName: map['size_name'] as String,
        colorId: map['color_id'] as int,
        colorName: map['color_name'] as String,
        price: (map['price'] as num).toDouble(),
        isActive: (map['is_active'] as int? ?? 1) == 1,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'product_id': productId,
        'sku': sku,
        'size_id': sizeId,
        'size_name': sizeName,
        'color_id': colorId,
        'color_name': colorName,
        'price': price,
        'is_active': isActive ? 1 : 0,
      };
}

class SyncInventory {
  const SyncInventory({
    required this.productVariantId,
    required this.stockQuantity,
    required this.reservedQuantity,
    required this.availableQuantity,
  });

  final int productVariantId;
  final int stockQuantity;
  final int reservedQuantity;
  final int availableQuantity;

  factory SyncInventory.fromJson(Map<String, dynamic> json) => SyncInventory(
        productVariantId: json['product_variant_id'] as int,
        stockQuantity: json['stock_quantity'] as int? ?? 0,
        reservedQuantity: json['reserved_quantity'] as int? ?? 0,
        availableQuantity: json['available_quantity'] as int? ?? 0,
      );

  factory SyncInventory.fromMap(Map<String, dynamic> map) => SyncInventory(
        productVariantId: map['product_variant_id'] as int,
        stockQuantity: map['stock_quantity'] as int? ?? 0,
        reservedQuantity: map['reserved_quantity'] as int? ?? 0,
        availableQuantity: map['available_quantity'] as int? ?? 0,
      );

  Map<String, dynamic> toMap() => {
        'product_variant_id': productVariantId,
        'stock_quantity': stockQuantity,
        'reserved_quantity': reservedQuantity,
        'available_quantity': availableQuantity,
      };
}

class SyncCatalogResponse {
  const SyncCatalogResponse({
    required this.metadata,
    required this.categories,
    required this.products,
    required this.variants,
    required this.inventory,
  });

  final SyncMetadata metadata;
  final List<SyncCategory> categories;
  final List<SyncProduct> products;
  final List<SyncVariant> variants;
  final List<SyncInventory> inventory;

  factory SyncCatalogResponse.fromJson(Map<String, dynamic> json) =>
      SyncCatalogResponse(
        metadata:
            SyncMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
        categories: (json['categories'] as List<dynamic>)
            .map((e) => SyncCategory.fromJson(e as Map<String, dynamic>))
            .toList(),
        products: (json['products'] as List<dynamic>)
            .map((e) => SyncProduct.fromJson(e as Map<String, dynamic>))
            .toList(),
        variants: (json['variants'] as List<dynamic>)
            .map((e) => SyncVariant.fromJson(e as Map<String, dynamic>))
            .toList(),
        inventory: (json['inventory'] as List<dynamic>)
            .map((e) => SyncInventory.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class OfflineOperationRecord {
  const OfflineOperationRecord({
    required this.clientOperationId,
    required this.branchId,
    required this.operationType,
    required this.status,
    required this.payloadJson,
    this.conflictDetailJson,
    this.saleId,
    this.orderNumber,
    this.reservationId,
    required this.createdAt,
    this.syncedAt,
  });

  final String clientOperationId;
  final int branchId;
  final String operationType; // 'SALE' | 'RESERVATION'
  final String status; // 'PENDING_SYNC' | 'CONFIRMED' | 'CONFLICT'
  final String payloadJson;
  final String? conflictDetailJson;
  final int? saleId;
  final String? orderNumber;
  final int? reservationId;
  final String createdAt;
  final String? syncedAt;

  factory OfflineOperationRecord.fromMap(Map<String, dynamic> map) =>
      OfflineOperationRecord(
        clientOperationId: map['client_operation_id'] as String,
        branchId: map['branch_id'] as int,
        operationType: map['operation_type'] as String,
        status: map['status'] as String,
        payloadJson: map['payload'] as String,
        conflictDetailJson: map['conflict_detail'] as String?,
        saleId: map['sale_id'] as int?,
        orderNumber: map['order_number'] as String?,
        reservationId: map['reservation_id'] as int?,
        createdAt: map['created_at'] as String,
        syncedAt: map['synced_at'] as String?,
      );

  Map<String, dynamic> toMap() => {
        'client_operation_id': clientOperationId,
        'branch_id': branchId,
        'operation_type': operationType,
        'status': status,
        'payload': payloadJson,
        'conflict_detail': conflictDetailJson,
        'sale_id': saleId,
        'order_number': orderNumber,
        'reservation_id': reservationId,
        'created_at': createdAt,
        'synced_at': syncedAt,
      };

  OfflineOperationRecord copyWith({
    String? status,
    String? conflictDetailJson,
    int? saleId,
    String? orderNumber,
    int? reservationId,
    String? syncedAt,
  }) =>
      OfflineOperationRecord(
        clientOperationId: clientOperationId,
        branchId: branchId,
        operationType: operationType,
        status: status ?? this.status,
        payloadJson: payloadJson,
        conflictDetailJson: conflictDetailJson ?? this.conflictDetailJson,
        saleId: saleId ?? this.saleId,
        orderNumber: orderNumber ?? this.orderNumber,
        reservationId: reservationId ?? this.reservationId,
        createdAt: createdAt,
        syncedAt: syncedAt ?? this.syncedAt,
      );
}

class OfflineSaleItem {
  const OfflineSaleItem({
    required this.productVariantId,
    required this.quantity,
    required this.unitPrice,
  });

  final int productVariantId;
  final int quantity;
  final double unitPrice;

  factory OfflineSaleItem.fromJson(Map<String, dynamic> json) =>
      OfflineSaleItem(
        productVariantId: json['product_variant_id'] as int,
        quantity: json['quantity'] as int,
        unitPrice: double.parse('${json['unit_price']}'),
      );

  Map<String, dynamic> toJson() => {
        'product_variant_id': productVariantId,
        'quantity': quantity,
        'unit_price': unitPrice,
      };
}

class OfflineCustomerRecord {
  const OfflineCustomerRecord({
    required this.id,
    required this.fullName,
    required this.nitCi,
    this.phone,
    this.email,
    required this.updatedAt,
  });

  final String id;
  final String fullName;
  final String nitCi;
  final String? phone;
  final String? email;
  final String updatedAt;

  factory OfflineCustomerRecord.fromMap(Map<String, dynamic> map) =>
      OfflineCustomerRecord(
        id: map['id'] as String,
        fullName: map['full_name'] as String,
        nitCi: map['nit_ci'] as String,
        phone: map['phone'] as String?,
        email: map['email'] as String?,
        updatedAt: map['updated_at'] as String,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'full_name': fullName,
        'nit_ci': nitCi,
        'phone': phone,
        'email': email,
        'updated_at': updatedAt,
      };
}

class OfflineSalePayload {
  const OfflineSalePayload({
    this.customerName,
    this.customerNit,
    this.customerPhone,
    required this.items,
    required this.total,
    this.discount = 0.0,
    this.notes,
  });

  final String? customerName;
  final String? customerNit;
  final String? customerPhone;
  final List<OfflineSaleItem> items;
  final double total;
  final double discount;
  final String? notes;

  factory OfflineSalePayload.fromJson(Map<String, dynamic> json) =>
      OfflineSalePayload(
        customerName: json['customer_name'] as String?,
        customerNit: json['customer_nit'] as String?,
        customerPhone: json['customer_phone'] as String?,
        items: (json['items'] as List<dynamic>)
            .map((e) => OfflineSaleItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        total: double.parse('${json['total']}'),
        discount: json['discount'] != null
            ? double.parse('${json['discount']}')
            : 0.0,
        notes: json['notes'] as String?,
      );

  Map<String, dynamic> toJson() => {
        if (customerName != null) 'customer_name': customerName,
        if (customerNit != null) 'customer_nit': customerNit,
        if (customerPhone != null) 'customer_phone': customerPhone,
        'items': items.map((e) => e.toJson()).toList(),
        'total': total,
        'discount': discount,
        if (notes != null) 'notes': notes,
      };
}

class OfflineReservationItem {
  const OfflineReservationItem({
    required this.productVariantId,
    required this.quantity,
  });

  final int productVariantId;
  final int quantity;

  factory OfflineReservationItem.fromJson(Map<String, dynamic> json) =>
      OfflineReservationItem(
        productVariantId: json['product_variant_id'] as int,
        quantity: json['quantity'] as int,
      );

  Map<String, dynamic> toJson() => {
        'product_variant_id': productVariantId,
        'quantity': quantity,
      };
}

class OfflineReservationPayload {
  const OfflineReservationPayload({
    required this.customerName,
    this.customerNit,
    this.customerPhone,
    required this.items,
    this.notes,
  });

  final String customerName;
  final String? customerNit;
  final String? customerPhone;
  final List<OfflineReservationItem> items;
  final String? notes;

  factory OfflineReservationPayload.fromJson(Map<String, dynamic> json) =>
      OfflineReservationPayload(
        customerName: json['customer_name'] as String,
        customerNit: json['customer_nit'] as String?,
        customerPhone: json['customer_phone'] as String?,
        items: (json['items'] as List<dynamic>)
            .map((e) =>
                OfflineReservationItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        notes: json['notes'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'customer_name': customerName,
        if (customerNit != null) 'customer_nit': customerNit,
        if (customerPhone != null) 'customer_phone': customerPhone,
        'items': items.map((e) => e.toJson()).toList(),
        if (notes != null) 'notes': notes,
      };
}

class SyncConflictDetail {
  const SyncConflictDetail({
    required this.code,
    required this.message,
    this.availableStock,
    this.requestedQuantity,
    this.variantId,
  });

  final String code;
  final String message;
  final int? availableStock;
  final int? requestedQuantity;
  final int? variantId;

  factory SyncConflictDetail.fromJson(Map<String, dynamic> json) =>
      SyncConflictDetail(
        code: json['code'] as String? ?? 'CONFLICT',
        message: json['message'] as String? ?? 'Conflict detected',
        availableStock: json['available_stock'] as int?,
        requestedQuantity: json['requested_quantity'] as int?,
        variantId: json['variant_id'] as int?,
      );

  Map<String, dynamic> toJson() => {
        'code': code,
        'message': message,
        'available_stock': availableStock,
        'requested_quantity': requestedQuantity,
        'variant_id': variantId,
      };
}

class SyncTransactionItemResult {
  const SyncTransactionItemResult({
    required this.clientOperationId,
    required this.operationType,
    required this.status,
    this.saleId,
    this.orderNumber,
    this.reservationId,
    this.conflict,
    required this.processedAt,
  });

  final String clientOperationId;
  final String operationType;
  final String status;
  final int? saleId;
  final String? orderNumber;
  final int? reservationId;
  final SyncConflictDetail? conflict;
  final String processedAt;

  factory SyncTransactionItemResult.fromJson(Map<String, dynamic> json) =>
      SyncTransactionItemResult(
        clientOperationId: json['client_operation_id'] as String,
        operationType: json['operation_type'] as String,
        status: json['status'] as String,
        saleId: json['sale_id'] as int?,
        orderNumber: json['order_number'] as String?,
        reservationId: json['reservation_id'] as int?,
        conflict: json['conflict'] != null
            ? SyncConflictDetail.fromJson(
                json['conflict'] as Map<String, dynamic>)
            : null,
        processedAt: json['processed_at'] as String? ?? '',
      );
}

class SyncTransactionBatchResponse {
  const SyncTransactionBatchResponse({
    required this.processedCount,
    required this.confirmedCount,
    required this.conflictCount,
    required this.results,
  });

  final int processedCount;
  final int confirmedCount;
  final int conflictCount;
  final List<SyncTransactionItemResult> results;

  factory SyncTransactionBatchResponse.fromJson(Map<String, dynamic> json) =>
      SyncTransactionBatchResponse(
        processedCount: json['processed_count'] as int? ?? 0,
        confirmedCount: json['confirmed_count'] as int? ?? 0,
        conflictCount: json['conflict_count'] as int? ?? 0,
        results: (json['results'] as List<dynamic>? ?? [])
            .map((e) =>
                SyncTransactionItemResult.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
