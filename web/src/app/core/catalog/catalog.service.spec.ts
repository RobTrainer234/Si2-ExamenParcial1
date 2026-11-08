import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { firstValueFrom } from 'rxjs';
import { vi } from 'vitest';

import { CatalogService } from './catalog.service';
import { OfflineCatalogService } from '../offline/offline-catalog.service';

describe('CatalogService', () => {
  let service: CatalogService;
  let http: HttpTestingController;
  let offline: { getProductDetail: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    offline = { getProductDetail: vi.fn(() => Promise.resolve({ product: null, variants: [], inventory: {}, metadata: null })) };
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting(), { provide: OfflineCatalogService, useValue: offline }] });
    service = TestBed.inject(CatalogService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('sends catalog filters as query parameters', () => {
    service.list({ page: 2, page_size: 12, q: 'camisa', category_id: 3 }).subscribe((response) => expect(response.total).toBe(1));
    const request = http.expectOne((item) => item.url === '/api/v1/catalog');
    expect(request.request.params.get('q')).toBe('camisa');
    expect(request.request.params.get('category_id')).toBe('3');
    request.flush({ items: [], page: 2, page_size: 12, total: 1, total_pages: 1 });
  });

  it('keeps HTTP detail as the priority source', () => {
    service.detail(101).subscribe((detail) => expect(detail.name).toBe('Online product'));
    const request = http.expectOne('/api/v1/catalog/101');
    request.flush({ id: 101, name: 'Online product', variants: [], images: [] });
    expect(offline.getProductDetail).not.toHaveBeenCalled();
    expect(service.lastDetailWasOffline()).toBe(false);
  });

  it('falls back to the synchronized local product and derives variant stock and branch availability', async () => {
    offline.getProductDetail.mockResolvedValue({
      product: { id: 101, category_id: 1, category_name: 'Vestidos', name: 'Local dress', code: 'D-101', slug: 'local-dress', description: null, audience: 'WOMEN', size_system: 'NUMERIC', price: 350, image_url: '/dress.jpg', is_active: true },
      variants: [{ id: 1001, product_id: 101, sku: 'D-101-S', size_id: 1, size_name: 'S', size_type: 'ONE_SIZE', sort_order: 9, color_id: 2, color_name: 'Rojo', price: 350, is_active: true }],
      inventory: { 1001: { product_variant_id: 1001, stock_quantity: 4, reserved_quantity: 1, available_quantity: 3 } },
      metadata: { tenant_id: 1, tenant_name: 'Aurora', branch_id: 10, branch_name: 'Central', sync_timestamp: '2026-01-01', catalog_version: 'v1' },
    });

    const detailPromise = firstValueFrom(service.detail(101));
    http.expectOne('/api/v1/catalog/101').flush({}, { status: 503, statusText: 'Offline' });
    const detail = await detailPromise;
    expect(detail.name).toBe('Local dress');
    expect(detail.audience).toBe('WOMEN');
    expect(detail.size_system).toBe('NUMERIC');
    expect(detail.variants[0]).toMatchObject({ id: 1001, size_type: 'ONE_SIZE', sort_order: 9, available: true, stock_total: 3 });
    expect(service.lastDetailWasOffline()).toBe(true);

    const availabilityPromise = firstValueFrom(service.availability(101, 1, 2));
    http.expectOne('/api/v1/catalog/101/availability?size_id=1&color_id=2').flush({}, { status: 503, statusText: 'Offline' });
    const availability = await availabilityPromise;
    expect(availability).toEqual([{ branch_id: 10, branch_name: 'Central', city_name: '', address: '', available: true, stock: 3 }]);
    expect(service.lastAvailabilityWasOffline()).toBe(true);
  });

  it('handles missing local product and sold-out local variants gracefully', async () => {
    offline.getProductDetail.mockResolvedValue({ product: null, variants: [], inventory: {}, metadata: { branch_id: 10, branch_name: 'Central' } });
    const missingPromise = firstValueFrom(service.detail(999));
    http.expectOne('/api/v1/catalog/999').flush({}, { status: 503, statusText: 'Offline' });
    await expect(missingPromise).rejects.toBeTruthy();

    offline.getProductDetail.mockResolvedValue({
      product: { id: 101, category_id: 1, category_name: 'Vestidos', name: 'Sold out', code: 'D-101', slug: 'sold-out', description: null, price: 350, image_url: null, is_active: true },
      variants: [{ id: 1001, product_id: 101, sku: 'D-101-S', size_id: 1, size_name: 'S', color_id: 2, color_name: 'Rojo', price: 350, is_active: true }],
      inventory: { 1001: { product_variant_id: 1001, stock_quantity: 0, reserved_quantity: 0, available_quantity: 0 } },
      metadata: { branch_id: 10, branch_name: 'Central' },
    });
    const soldOutPromise = firstValueFrom(service.detail(101));
    http.expectOne('/api/v1/catalog/101').flush({}, { status: 503, statusText: 'Offline' });
    const soldOut = await soldOutPromise;
    expect(soldOut.variants[0]).toMatchObject({ available: false, stock_total: 0 });
  });

  it('does not claim offline availability without metadata or a matching local variant', async () => {
    offline.getProductDetail.mockResolvedValue({
      product: { id: 101, category_id: 1, category_name: 'Vestidos', name: 'Incomplete', code: 'D-101', slug: 'incomplete', description: null, audience: 'WOMEN', size_system: 'NUMERIC', price: 350, image_url: null, is_active: true },
      variants: [],
      inventory: {},
      metadata: null,
    });
    const noMetadata = firstValueFrom(service.availability(101, 1, 2));
    http.expectOne('/api/v1/catalog/101/availability?size_id=1&color_id=2').flush({}, { status: 503, statusText: 'Offline' });
    await expect(noMetadata).resolves.toEqual([]);
    expect(service.lastAvailabilityWasOffline()).toBe(false);

    offline.getProductDetail.mockResolvedValue({
      product: { id: 101, category_id: 1, category_name: 'Vestidos', name: 'No variant', code: 'D-101', slug: 'no-variant', description: null, audience: 'WOMEN', size_system: 'NUMERIC', price: 350, image_url: null, is_active: true },
      variants: [{ id: 1001, product_id: 101, sku: 'D-101-S', size_id: 1, size_name: 'S', size_type: 'ONE_SIZE', sort_order: 9, color_id: 2, color_name: 'Rojo', price: 350, is_active: true }],
      inventory: {},
      metadata: { branch_id: 10, branch_name: 'Central' },
    });
    const noInventory = firstValueFrom(service.availability(101, 99, 99));
    http.expectOne('/api/v1/catalog/101/availability?size_id=99&color_id=99').flush({}, { status: 503, statusText: 'Offline' });
    await expect(noInventory).resolves.toEqual([]);
    expect(service.lastAvailabilityWasOffline()).toBe(false);
  });

  it('requests availability with the selected variant', () => {
    service.availability(8, 4, 2).subscribe((items) => expect(items.length).toBe(1));
    const request = http.expectOne('/api/v1/catalog/8/availability?size_id=4&color_id=2');
    expect(request.request.method).toBe('GET');
    request.flush([{ branch_id: 1, branch_name: 'Centro', city_name: 'Santa Cruz', address: 'Centro 1', available: true, stock: 2 }]);
  });
});
