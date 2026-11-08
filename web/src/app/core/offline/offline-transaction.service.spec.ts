import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { OfflineCatalogService } from './offline-catalog.service';
import { OfflineTransactionService } from './offline-transaction.service';
import { SyncTransactionService } from './sync-transaction.service';
import { SyncCatalogResponse, SyncTransactionBatchResponse } from './offline.models';

describe('OfflineTransactionService and SyncTransactionService', () => {
  let catalogService: OfflineCatalogService;
  let txService: OfflineTransactionService;
  let syncService: SyncTransactionService;
  let http: HttpTestingController;

  const mockCatalogPayload: SyncCatalogResponse = {
    metadata: {
      tenant_id: 1,
      tenant_name: 'Boutique Aurora',
      branch_id: 10,
      branch_name: 'Aurora Central',
      sync_timestamp: '2026-10-23T20:00:00Z',
      catalog_version: 'cat-v1-100',
    },
    categories: [{ id: 1, name: 'Pantalones', is_active: true }],
    products: [
      {
        id: 101,
        category_id: 1,
        category_name: 'Pantalones',
        name: 'Jeans Slim',
        code: 'JNS-01',
        slug: 'jeans-slim',
        description: 'Jeans',
        price: 150.0,
        image_url: null,
        is_active: true,
      },
    ],
    variants: [
      {
        id: 1001,
        product_id: 101,
        sku: 'JNS-01-30',
        size_id: 1,
        size_name: '30',
        color_id: 1,
        color_name: 'Negro',
        price: 150.0,
        is_active: true,
      },
    ],
    inventory: [
      {
        product_variant_id: 1001,
        stock_quantity: 10,
        reserved_quantity: 0,
        available_quantity: 10,
      },
    ],
  };

  beforeEach(async () => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        OfflineCatalogService,
        OfflineTransactionService,
        SyncTransactionService,
      ],
    });

    catalogService = TestBed.inject(OfflineCatalogService);
    txService = TestBed.inject(OfflineTransactionService);
    syncService = TestBed.inject(SyncTransactionService);
    http = TestBed.inject(HttpTestingController);

    await catalogService.clearCache();
    await txService.clearAllOperations();
    await catalogService.saveSyncPayload(JSON.parse(JSON.stringify(mockCatalogPayload)));
  });

  afterEach(() => {
    http.verify();
  });

  it('records an offline sale, deducts local inventory and lists pending operation', async () => {
    const record = await txService.recordOfflineSale(10, {
      items: [{ product_variant_id: 1001, quantity: 2, unit_price: 150.0 }],
      total: 300.0,
      discount: 0,
    });

    expect(record.client_operation_id).toContain('op-web-');
    expect(record.status).toBe('PENDING_SYNC');
    expect(record.operation_type).toBe('SALE');

    // Local inventory check
    const inv = await catalogService.getInventory(1001);
    expect(inv).not.toBeNull();
    expect(inv!.stock_quantity).toBe(8);
    expect(inv!.available_quantity).toBe(8);

    // List pending
    const pending = await txService.listOperations('PENDING_SYNC');
    expect(pending.length).toBe(1);
    expect(pending[0].client_operation_id).toBe(record.client_operation_id);
  });

  it('records an offline reservation and updates local reserved quantity', async () => {
    const record = await txService.recordOfflineReservation(10, {
      customer_name: 'Ana Suarez',
      items: [{ product_variant_id: 1001, quantity: 3 }],
    });

    expect(record.operation_type).toBe('RESERVATION');
    expect(record.status).toBe('PENDING_SYNC');

    const inv = await catalogService.getInventory(1001);
    expect(inv!.reserved_quantity).toBe(3);
    expect(inv!.available_quantity).toBe(7);
  });

  it('syncs pending transactions to backend and updates confirmation / conflict statuses', async () => {
    const saleRecord = await txService.recordOfflineSale(10, {
      items: [{ product_variant_id: 1001, quantity: 1, unit_price: 150.0 }],
      total: 150.0,
    });

    const syncPromise = syncService.syncPendingTransactions();
    // Allow IndexedDB read to resolve so HTTP call is triggered
    await Promise.resolve();
    await Promise.resolve();

    const req = http.expectOne('/api/v1/sync/transactions');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.operations.length).toBe(1);
    expect(req.request.body.operations[0].client_operation_id).toBe(saleRecord.client_operation_id);

    const mockResponse: SyncTransactionBatchResponse = {
      processed_count: 1,
      confirmed_count: 1,
      conflict_count: 0,
      results: [
        {
          client_operation_id: saleRecord.client_operation_id,
          operation_type: 'SALE',
          status: 'CONFIRMED',
          sale_id: 42,
          order_number: 'OFF-1700-CONF',
          processed_at: new Date().toISOString(),
        },
      ],
    };

    req.flush(mockResponse);

    const res = await syncPromise;
    expect(res).not.toBeNull();
    expect(res!.confirmed_count).toBe(1);

    const updated = await txService.getOperation(saleRecord.client_operation_id);
    expect(updated?.status).toBe('CONFIRMED');
    expect(updated?.sale_id).toBe(42);
    expect(updated?.order_number).toBe('OFF-1700-CONF');

    const remainingPending = await txService.listOperations('PENDING_SYNC');
    expect(remainingPending.length).toBe(0);
  });

  it('retains pending transactions in storage when network sync encounters an error', async () => {
    const record = await txService.recordOfflineSale(10, {
      items: [{ product_variant_id: 1001, quantity: 1, unit_price: 150.0 }],
      total: 150.0,
    });

    const syncPromise = syncService.syncPendingTransactions();
    // Allow IndexedDB read to resolve so HTTP call is triggered
    await Promise.resolve();
    await Promise.resolve();

    const req = http.expectOne('/api/v1/sync/transactions');
    req.flush({ detail: { message: 'Server unavailable' } }, { status: 503, statusText: 'Service Unavailable' });

    const res = await syncPromise;
    expect(res).toBeNull();
    expect(syncService.syncError()).toBe('Server unavailable');

    // Operation must NOT be deleted!
    const pending = await txService.listOperations('PENDING_SYNC');
    expect(pending.length).toBe(1);
    expect(pending[0].client_operation_id).toBe(record.client_operation_id);
  });

  it('CU-22: saves, lists, filters, and auto-persists minimal offline customer records', async () => {
    const saved = await txService.saveCustomer({
      full_name: 'Carlos Mendoza',
      nit_ci: '5678901',
      phone: '70011223',
    });
    expect(saved.id).toContain('cust-nit-5678901');
    expect(saved.full_name).toBe('Carlos Mendoza');

    // Auto-persist when recording an offline sale with customer data
    await txService.recordOfflineSale(10, {
      customer_name: 'Patricia Vega',
      customer_nit: '9988776',
      customer_phone: '75544332',
      items: [{ product_variant_id: 1001, quantity: 1, unit_price: 150.0 }],
      total: 150.0,
    });

    const allCustomers = await txService.listCustomers();
    expect(allCustomers.length).toBe(2);

    const filtered = await txService.listCustomers('9988776');
    expect(filtered.length).toBe(1);
    expect(filtered[0].full_name).toBe('Patricia Vega');

    await txService.deleteCustomer(saved.id);
    const remaining = await txService.listCustomers();
    expect(remaining.length).toBe(1);
  });
});
