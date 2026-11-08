import 'dart:math';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../features/catalog/data/catalog_models.dart';
import 'offline_models.dart';

class OfflineDatabase {
  OfflineDatabase({
    this.inMemory = false,
    this.databasePath,
    this.customFactory,
  });

  final bool inMemory;
  final String? databasePath;
  final DatabaseFactory? customFactory;

  Database? _db;

  static const String databaseName = 'fashionstore_offline.db';
  static const int databaseVersion = 3;

  static const String tableMetadata = 'metadata';
  static const String tableCategories = 'categories';
  static const String tableProducts = 'products';
  static const String tableVariants = 'variants';
  static const String tableInventory = 'inventory';
  static const String tableOfflineOperations = 'offline_operations';
  static const String tableOfflineCustomers = 'offline_customers';

  DatabaseFactory get _factory => customFactory ?? databaseFactory;

  Future<Database> get database async {
    if (_db != null && _db!.isOpen) {
      return _db!;
    }
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final String path;
    if (inMemory) {
      path = inMemoryDatabasePath;
    } else if (databasePath != null) {
      path = databasePath!;
    } else {
      final dbFolder = await _factory.getDatabasesPath();
      path = p.join(dbFolder, databaseName);
    }

    return await _factory.openDatabase(
      path,
      options: OpenDatabaseOptions(
        version: databaseVersion,
        onCreate: _onCreate,
        onUpgrade: _onUpgrade,
      ),
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE $tableMetadata (
        branch_id INTEGER PRIMARY KEY,
        tenant_id INTEGER NOT NULL,
        tenant_name TEXT NOT NULL,
        branch_name TEXT NOT NULL,
        sync_timestamp TEXT NOT NULL,
        catalog_version TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE $tableCategories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1
      )
    ''');

    await db.execute('''
      CREATE TABLE $tableProducts (
        id INTEGER PRIMARY KEY,
        category_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        slug TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
      )
    ''');

    await db.execute('''
      CREATE INDEX idx_products_category ON $tableProducts(category_id)
    ''');
    await db.execute('''
      CREATE INDEX idx_products_name ON $tableProducts(name)
    ''');

    await db.execute('''
      CREATE TABLE $tableVariants (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        sku TEXT NOT NULL,
        size_id INTEGER NOT NULL,
        size_name TEXT NOT NULL,
        color_id INTEGER NOT NULL,
        color_name TEXT NOT NULL,
        price REAL NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1
      )
    ''');

    await db.execute('''
      CREATE INDEX idx_variants_product ON $tableVariants(product_id)
    ''');
    await db.execute('''
      CREATE INDEX idx_variants_sku ON $tableVariants(sku)
    ''');

    await db.execute('''
      CREATE TABLE $tableInventory (
        product_variant_id INTEGER PRIMARY KEY,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        reserved_quantity INTEGER NOT NULL DEFAULT 0,
        available_quantity INTEGER NOT NULL DEFAULT 0
      )
    ''');

    await _createOfflineOperationsTable(db);
    await _createOfflineCustomersTable(db);
  }

  Future<void> _createOfflineOperationsTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS $tableOfflineOperations (
        client_operation_id TEXT PRIMARY KEY,
        branch_id INTEGER NOT NULL,
        operation_type TEXT NOT NULL,
        status TEXT NOT NULL,
        payload TEXT NOT NULL,
        conflict_detail TEXT,
        sale_id INTEGER,
        order_number TEXT,
        reservation_id INTEGER,
        created_at TEXT NOT NULL,
        synced_at TEXT
      )
    ''');

    await db.execute('''
      CREATE INDEX IF NOT EXISTS idx_offline_ops_status ON $tableOfflineOperations(status)
    ''');
    await db.execute('''
      CREATE INDEX IF NOT EXISTS idx_offline_ops_branch ON $tableOfflineOperations(branch_id)
    ''');
    await db.execute('''
      CREATE INDEX IF NOT EXISTS idx_offline_ops_created ON $tableOfflineOperations(created_at)
    ''');
  }

  Future<void> _createOfflineCustomersTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS $tableOfflineCustomers (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        nit_ci TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        updated_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE INDEX IF NOT EXISTS idx_offline_customers_nit ON $tableOfflineCustomers(nit_ci)
    ''');
    await db.execute('''
      CREATE INDEX IF NOT EXISTS idx_offline_customers_name ON $tableOfflineCustomers(full_name)
    ''');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await _createOfflineOperationsTable(db);
    }
    if (oldVersion < 3) {
      await _createOfflineCustomersTable(db);
    }
  }

  Future<void> saveCatalogSync(SyncCatalogResponse syncData) async {
    final db = await database;
    await db.transaction((txn) async {
      // Purge prior data to guarantee atomicity and avoid stale leftovers
      await txn.delete(tableInventory);
      await txn.delete(tableVariants);
      await txn.delete(tableProducts);
      await txn.delete(tableCategories);
      await txn.delete(tableMetadata);

      // Save metadata
      await txn.insert(
        tableMetadata,
        syncData.metadata.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );

      final batch = txn.batch();

      for (final cat in syncData.categories) {
        batch.insert(
          tableCategories,
          cat.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      for (final prod in syncData.products) {
        batch.insert(
          tableProducts,
          prod.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      for (final variant in syncData.variants) {
        batch.insert(
          tableVariants,
          variant.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      for (final inv in syncData.inventory) {
        batch.insert(
          tableInventory,
          inv.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      await batch.commit(noResult: true);
    });
  }

  Future<bool> hasOfflineData() async {
    final db = await database;
    final count = Sqflite.firstIntValue(
          await db.rawQuery('SELECT COUNT(*) FROM $tableMetadata'),
        ) ??
        0;
    return count > 0;
  }

  Future<SyncMetadata?> getMetadata() async {
    final db = await database;
    final rows = await db.query(tableMetadata, limit: 1);
    if (rows.isEmpty) return null;
    return SyncMetadata.fromMap(rows.first);
  }

  Future<List<SyncCategory>> getCategories() async {
    final db = await database;
    final rows = await db.query(
      tableCategories,
      where: 'is_active = 1',
      orderBy: 'name ASC',
    );
    return rows.map((r) => SyncCategory.fromMap(r)).toList();
  }

  Future<CatalogPage> listProducts({
    String query = '',
    int? categoryId,
    int page = 1,
    int pageSize = 20,
  }) async {
    final db = await database;

    final whereClauses = <String>['is_active = 1'];
    final whereArgs = <dynamic>[];

    if (categoryId != null) {
      whereClauses.add('category_id = ?');
      whereArgs.add(categoryId);
    }

    if (query.trim().isNotEmpty) {
      whereClauses.add(
        '(name LIKE ? OR code LIKE ? OR category_name LIKE ?)',
      );
      final searchPattern = '%${query.trim()}%';
      whereArgs.addAll([searchPattern, searchPattern, searchPattern]);
    }

    final whereString = whereClauses.join(' AND ');

    // Total count for pagination
    final countResult = await db.rawQuery(
      'SELECT COUNT(*) FROM $tableProducts WHERE $whereString',
      whereArgs,
    );
    final totalCount = Sqflite.firstIntValue(countResult) ?? 0;
    final totalPages = max(1, (totalCount / pageSize).ceil());

    final offset = max(0, (page - 1) * pageSize);
    final rows = await db.query(
      tableProducts,
      where: whereString,
      whereArgs: whereArgs,
      orderBy: 'name ASC',
      limit: pageSize,
      offset: offset,
    );

    final items = rows.map((r) {
      return CatalogItem(
        id: r['id'] as int,
        name: r['name'] as String,
        categoryName: r['category_name'] as String,
        price: (r['price'] as num).toDouble(),
        imageUrl: r['image_url'] as String?,
      );
    }).toList();

    return CatalogPage(items, totalPages, isOffline: true);
  }

  Future<CatalogDetail?> getProductDetail(int productId) async {
    final db = await database;
    final productRows = await db.query(
      tableProducts,
      where: 'id = ? AND is_active = 1',
      whereArgs: [productId],
      limit: 1,
    );
    if (productRows.isEmpty) return null;

    final pRow = productRows.first;

    final variantRows = await db.query(
      tableVariants,
      where: 'product_id = ? AND is_active = 1',
      whereArgs: [productId],
      orderBy: 'id ASC',
    );

    final variants = variantRows.map((v) {
      return CatalogVariant(
        id: v['id'] as int,
        sizeId: v['size_id'] as int,
        sizeName: v['size_name'] as String,
        colorId: v['color_id'] as int,
        colorName: v['color_name'] as String,
      );
    }).toList();

    return CatalogDetail(
      id: pRow['id'] as int,
      name: pRow['name'] as String,
      categoryName: pRow['category_name'] as String,
      price: (pRow['price'] as num).toDouble(),
      imageUrl: pRow['image_url'] as String?,
      description: null,
      variants: variants,
    );
  }

  Future<List<AvailabilityItem>> getVariantAvailability(
    int productId,
    CatalogVariant variant,
  ) async {
    final db = await database;
    final meta = await getMetadata();
    final branchId = meta?.branchId ?? 0;
    final branchName = meta?.branchName ?? 'Sucursal local';

    final invRows = await db.query(
      tableInventory,
      where: 'product_variant_id = ?',
      whereArgs: [variant.id],
      limit: 1,
    );

    final stock = invRows.isNotEmpty
        ? (invRows.first['available_quantity'] as int? ?? 0)
        : 0;

    return [
      AvailabilityItem(
        branchId: branchId,
        branchName: branchName,
        cityName: '',
        address: '',
        available: stock > 0,
        stock: stock,
      ),
    ];
  }

  Future<void> insertOperation(OfflineOperationRecord op) async {
    final db = await database;
    await db.insert(
      tableOfflineOperations,
      op.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> updateOperation(OfflineOperationRecord op) async {
    final db = await database;
    await db.update(
      tableOfflineOperations,
      op.toMap(),
      where: 'client_operation_id = ?',
      whereArgs: [op.clientOperationId],
    );
  }

  Future<OfflineOperationRecord?> getOperation(String clientOperationId) async {
    final db = await database;
    final rows = await db.query(
      tableOfflineOperations,
      where: 'client_operation_id = ?',
      whereArgs: [clientOperationId],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return OfflineOperationRecord.fromMap(rows.first);
  }

  Future<List<OfflineOperationRecord>> listOperations({String? status}) async {
    final db = await database;
    final List<Map<String, dynamic>> rows;
    if (status != null) {
      rows = await db.query(
        tableOfflineOperations,
        where: 'status = ?',
        whereArgs: [status],
        orderBy: 'created_at ASC',
      );
    } else {
      rows = await db.query(
        tableOfflineOperations,
        orderBy: 'created_at ASC',
      );
    }
    return rows.map((r) => OfflineOperationRecord.fromMap(r)).toList();
  }

  Future<int> countPendingOperations() async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) FROM $tableOfflineOperations WHERE status = ?',
      ['PENDING_SYNC'],
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  Future<void> decrementLocalInventory(
      int productVariantId, int quantity) async {
    final db = await database;
    await db.transaction((txn) async {
      final rows = await txn.query(
        tableInventory,
        where: 'product_variant_id = ?',
        whereArgs: [productVariantId],
        limit: 1,
      );
      if (rows.isNotEmpty) {
        final currentStock = rows.first['stock_quantity'] as int? ?? 0;
        final currentAvail = rows.first['available_quantity'] as int? ?? 0;
        final newStock = max(0, currentStock - quantity);
        final newAvail = max(0, currentAvail - quantity);
        await txn.update(
          tableInventory,
          {
            'stock_quantity': newStock,
            'available_quantity': newAvail,
          },
          where: 'product_variant_id = ?',
          whereArgs: [productVariantId],
        );
      }
    });
  }

  Future<void> reserveLocalInventory(
      int productVariantId, int quantity) async {
    final db = await database;
    await db.transaction((txn) async {
      final rows = await txn.query(
        tableInventory,
        where: 'product_variant_id = ?',
        whereArgs: [productVariantId],
        limit: 1,
      );
      if (rows.isNotEmpty) {
        final currentReserved =
            rows.first['reserved_quantity'] as int? ?? 0;
        final currentAvail = rows.first['available_quantity'] as int? ?? 0;
        final newReserved = currentReserved + quantity;
        final newAvail = max(0, currentAvail - quantity);
        await txn.update(
          tableInventory,
          {
            'reserved_quantity': newReserved,
            'available_quantity': newAvail,
          },
          where: 'product_variant_id = ?',
          whereArgs: [productVariantId],
        );
      }
    });
  }

  Future<OfflineCustomerRecord> saveCustomer({
    String? id,
    required String fullName,
    required String nitCi,
    String? phone,
    String? email,
  }) async {
    final db = await database;
    final cleanNit = nitCi.trim();
    final now = DateTime.now().toUtc().toIso8601String();
    final recordId = (id != null && id.trim().isNotEmpty)
        ? id.trim()
        : (cleanNit.isNotEmpty
            ? 'cust-nit-$cleanNit'
            : 'cust-mob-${DateTime.now().millisecondsSinceEpoch}');
    final record = OfflineCustomerRecord(
      id: recordId,
      fullName: fullName.trim(),
      nitCi: cleanNit,
      phone: phone != null && phone.trim().isNotEmpty ? phone.trim() : null,
      email: email != null && email.trim().isNotEmpty ? email.trim() : null,
      updatedAt: now,
    );

    await db.insert(
      tableOfflineCustomers,
      record.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    return record;
  }

  Future<List<OfflineCustomerRecord>> listCustomers({String query = ''}) async {
    final db = await database;
    final List<Map<String, dynamic>> rows;
    if (query.trim().isNotEmpty) {
      final pattern = '%${query.trim()}%';
      rows = await db.query(
        tableOfflineCustomers,
        where: 'full_name LIKE ? OR nit_ci LIKE ? OR phone LIKE ?',
        whereArgs: [pattern, pattern, pattern],
        orderBy: 'updated_at DESC',
      );
    } else {
      rows = await db.query(
        tableOfflineCustomers,
        orderBy: 'updated_at DESC',
      );
    }
    return rows.map((r) => OfflineCustomerRecord.fromMap(r)).toList();
  }

  Future<void> deleteCustomer(String id) async {
    final db = await database;
    await db.delete(
      tableOfflineCustomers,
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> clearOperations() async {
    final db = await database;
    await db.delete(tableOfflineOperations);
  }

  Future<void> clearAll() async {
    final db = await database;
    await db.transaction((txn) async {
      await txn.delete(tableOfflineCustomers);
      await txn.delete(tableOfflineOperations);
      await txn.delete(tableInventory);
      await txn.delete(tableVariants);
      await txn.delete(tableProducts);
      await txn.delete(tableCategories);
      await txn.delete(tableMetadata);
    });
  }

  Future<void> close() async {
    if (_db != null && _db!.isOpen) {
      await _db!.close();
      _db = null;
    }
  }
}
