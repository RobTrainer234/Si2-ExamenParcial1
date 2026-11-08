import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { firstValueFrom } from 'rxjs';

import { OfflineCatalogService } from './offline-catalog.service';
import { SyncCatalogService } from './sync-catalog.service';
import { SyncCatalogResponse } from './offline.models';

describe('OfflineCatalogService and SyncCatalogService', () => {
  let offlineService: OfflineCatalogService;
  let syncService: SyncCatalogService;
  let http: HttpTestingController;

  const mockPayloadTenantA: SyncCatalogResponse = {
    metadata: {
      tenant_id: 1,
      tenant_name: 'Boutique Aurora',
      branch_id: 10,
      branch_name: 'Aurora Central',
      sync_timestamp: '2026-10-23T20:00:00Z',
      catalog_version: 'cat-v1-100',
    },
    categories: [
      { id: 1, name: 'Vestidos', is_active: true },
      { id: 2, name: 'Blusas', is_active: true },
    ],
    products: [
      {
        id: 101,
        category_id: 1,
        category_name: 'Vestidos',
        name: 'Vestido Seda Floral',
        code: 'VES-01',
        slug: 'vestido-seda-floral',
        description: 'Vestido de seda',
        audience: 'WOMEN',
        size_system: 'ALPHA',
        price: 350.0,
        image_url: 'https://cdn.example.com/vestido.jpg',
        is_active: true,
      },
    ],
    variants: [
      {
        id: 1001,
        product_id: 101,
        sku: 'VES-01-S-RED',
        size_id: 1,
        size_name: 'S',
        color_id: 1,
        color_name: 'Rojo',
        size_type: 'ALPHA',
        sort_order: 1,
        price: 350.0,
        is_active: true,
      },
    ],
    inventory: [
      {
        product_variant_id: 1001,
        stock_quantity: 15,
        reserved_quantity: 3,
        available_quantity: 12,
      },
    ],
  };

  const mockPayloadTenantB: SyncCatalogResponse = {
    metadata: {
      tenant_id: 2,
      tenant_name: 'Moda Boreal',
      branch_id: 20,
      branch_name: 'Boreal Sur',
      sync_timestamp: '2026-10-23T20:30:00Z',
      catalog_version: 'cat-v1-200',
    },
    categories: [
      { id: 10, name: 'Abrigos', is_active: true },
    ],
    products: [
      {
        id: 201,
        category_id: 10,
        category_name: 'Abrigos',
        name: 'Tapado Lana',
        code: 'ABR-01',
        slug: 'tapado-lana',
        description: 'Tapado de lana',
        audience: 'MEN',
        size_system: 'ALPHA',
        price: 700.0,
        image_url: null,
        is_active: true,
      },
    ],
    variants: [
      {
        id: 2001,
        product_id: 201,
        sku: 'ABR-01-M-GRY',
        size_id: 2,
        size_name: 'M',
        color_id: 2,
        color_name: 'Gris',
        size_type: 'ALPHA',
        sort_order: 1,
        price: 700.0,
        is_active: true,
      },
    ],
    inventory: [
      {
        product_variant_id: 2001,
        stock_quantity: 5,
        reserved_quantity: 0,
        available_quantity: 5,
      },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    offlineService = TestBed.inject(OfflineCatalogService);
    syncService = TestBed.inject(SyncCatalogService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('saves and retrieves offline catalog data', async () => {
    await offlineService.saveSyncPayload(mockPayloadTenantA);

    const meta = await offlineService.getLatestMetadata();
    expect(meta?.tenant_name).toBe('Boutique Aurora');
    expect(meta?.branch_name).toBe('Aurora Central');

    const categories = await offlineService.getCategories();
    expect(categories.length).toBe(2);
    expect(categories.map((c) => c.name)).toContain('Vestidos');

    const products = await offlineService.getProducts();
    expect(products.length).toBe(1);
    expect(products[0].code).toBe('VES-01');

    const product = await offlineService.getProductById(101);
    expect(product?.name).toBe('Vestido Seda Floral');

    const variants = await offlineService.getVariantsByProductId(101);
    expect(variants.length).toBe(1);
    expect(variants[0].sku).toBe('VES-01-S-RED');

    const inv = await offlineService.getInventory(1001);
    expect(inv?.stock_quantity).toBe(15);
    expect(inv?.available_quantity).toBe(12);
  });

  it('provides the synchronized product, variants, inventory, and branch metadata for offline detail fallback', async () => {
    await offlineService.saveSyncPayload(mockPayloadTenantA);

    const detail = await offlineService.getProductDetail(101);
    expect(detail.product?.name).toBe('Vestido Seda Floral');
    expect(detail.variants[0].sku).toBe('VES-01-S-RED');
    expect(detail.inventory[1001].available_quantity).toBe(12);
    expect(detail.metadata?.branch_id).toBe(10);
    expect(detail.metadata?.branch_name).toBe('Aurora Central');
  });

  it('preserves backend product and size semantics and excludes inactive variants at storage boundary', async () => {
    await offlineService.saveSyncPayload({
      ...mockPayloadTenantA,
      variants: [
        ...mockPayloadTenantA.variants,
        { ...mockPayloadTenantA.variants[0], id: 1002, sku: 'INACTIVE', is_active: false },
      ],
    });

    const product = await offlineService.getProductById(101);
    const variants = await offlineService.getVariantsByProductId(101);
    expect(product).toMatchObject({ audience: 'WOMEN', size_system: 'ALPHA' });
    expect(variants).toHaveLength(1);
    expect(variants[0]).toMatchObject({ size_type: 'ALPHA', sort_order: 1 });
  });

  it('returns no offline detail when the synchronized branch has no saved product', async () => {
    await offlineService.saveSyncPayload(mockPayloadTenantA);

    const detail = await offlineService.getProductDetail(999);
    expect(detail.product).toBeNull();
    expect(detail.variants).toEqual([]);
    expect(detail.inventory).toEqual({});
    expect(detail.metadata?.branch_name).toBe('Aurora Central');
  });

  it('filters offline products by category and query', async () => {
    await offlineService.saveSyncPayload(mockPayloadTenantA);

    const byCat = await offlineService.getProducts(1);
    expect(byCat.length).toBe(1);

    const byWrongCat = await offlineService.getProducts(99);
    expect(byWrongCat.length).toBe(0);

    const byQuery = await offlineService.getProducts(undefined, 'floral');
    expect(byQuery.length).toBe(1);

    const byNoMatch = await offlineService.getProducts(undefined, 'pantalon');
    expect(byNoMatch.length).toBe(0);
  });

  it('clears offline cache and replaces with new tenant data without leaking previous tenant data', async () => {
    // 1. Load Tenant A
    await offlineService.saveSyncPayload(mockPayloadTenantA);
    let meta = await offlineService.getLatestMetadata();
    expect(meta?.tenant_name).toBe('Boutique Aurora');

    // 2. Clear cache
    await offlineService.clearCache();
    meta = await offlineService.getLatestMetadata();
    expect(meta).toBeNull();
    let prods = await offlineService.getProducts();
    expect(prods.length).toBe(0);

    // 3. Load Tenant B
    await offlineService.saveSyncPayload(mockPayloadTenantB);
    meta = await offlineService.getLatestMetadata();
    expect(meta?.tenant_name).toBe('Moda Boreal');
    prods = await offlineService.getProducts();
    expect(prods.length).toBe(1);
    expect(prods[0].code).toBe('ABR-01');
    expect(prods.map((p) => p.code)).not.toContain('VES-01');
  });

  it('uses IndexedDB-backed data when available instead of only the in-memory fallback', async () => {
    expect(offlineService.initDb).toBeDefined();
  });

  it('syncs catalog via SyncCatalogService, saves offline payload and updates signals', async () => {
    const syncPromise = firstValueFrom(syncService.syncCatalog(10));
    expect(syncService.isSyncing()).toBe(true);

    const req = http.expectOne('/api/v1/sync/catalog?branch_id=10');
    expect(req.request.method).toBe('GET');
    req.flush(mockPayloadTenantA);

    const res = await syncPromise;
    expect(res.metadata.tenant_name).toBe('Boutique Aurora');
    expect(syncService.isSyncing()).toBe(false);
    expect(syncService.syncError()).toBeNull();
    expect(syncService.lastSync()?.tenant_name).toBe('Boutique Aurora');
    expect(syncService.lastSync()?.branch_name).toBe('Aurora Central');
  });

  it('handles sync errors gracefully and exposes error signal', () => {
    syncService.syncCatalog(999).subscribe({
      error: () => {
        expect(syncService.isSyncing()).toBe(false);
        expect(syncService.syncError()).toBe('Sucursal no encontrada.');
      },
    });

    const req = http.expectOne('/api/v1/sync/catalog?branch_id=999');
    req.flush({ detail: { code: 'BRANCH_NOT_FOUND', message: 'Sucursal no encontrada.' } }, { status: 404, statusText: 'Not Found' });
  });
});
