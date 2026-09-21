import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { AdminService } from './admin.service';

describe('AdminService inventory movements', () => {
  let service: AdminService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(AdminService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('requests filtered inventory movements', () => {
    service.inventoryMovements(4, 'OUT').subscribe((page) => expect(page.items.length).toBe(1));
    const request = http.expectOne((item) => item.url === '/api/v1/inventory/movements');
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('inventory_id')).toBe('4');
    expect(request.request.params.get('movement_type')).toBe('OUT');
    request.flush({ items: [{ id: 1 }], page: 1, page_size: 100, total: 1, total_pages: 1 });
  });

  it('creates an inventory movement', () => {
    const payload = { inventory_id: 4, movement_type: 'IN', quantity: 3, reason: 'Recepción de proveedor' };
    service.createInventoryMovement(payload).subscribe((movement) => expect(movement.id).toBe(8));
    const request = http.expectOne('/api/v1/inventory/movements');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(payload);
    request.flush({ ...payload, id: 8 });
  });

  it('loads cycle 3 dashboard with filters and promotions', () => {
    service.dashboard({ branch_id: 3, start_date: '2030-01-01', end_date: '2030-01-31' }).subscribe((dashboard) => expect(dashboard.revenue.sales_count).toBe(2));
    const dashboard = http.expectOne((item) => item.url === '/api/v1/reports/dashboard');
    expect(dashboard.request.method).toBe('GET');
    expect(dashboard.request.params.get('branch_id')).toBe('3');
    expect(dashboard.request.params.get('date_from')).toBe('2030-01-01');
    expect(dashboard.request.params.get('date_to')).toBe('2030-01-31');
    dashboard.flush({ revenue: { sales_count: 2, subtotal: '200.00', discount: '20.00', total: '180.00' }, sales_by_branch: [], top_products: [], low_stock: [], reservations: [], sales_by_channel: [] });

    service.promotions().subscribe((page) => expect(page.total).toBe(1));
    const promotions = http.expectOne((item) => item.url === '/api/v1/promotions');
    expect(promotions.request.method).toBe('GET');
    promotions.flush({ items: [], page: 1, page_size: 100, total: 1, total_pages: 1 });
  });

  it('updates promotion state and product assignments', () => {
    service.setPromotionActive(7, false).subscribe((promotion) => expect(promotion.is_active).toBe(false));
    const deactivate = http.expectOne('/api/v1/promotions/7/deactivate');
    expect(deactivate.request.method).toBe('PATCH');
    deactivate.flush({ id: 7, name: 'Promo', description: null, discount_type: 'PERCENT', discount_value: 10, starts_at: '2030-01-01', ends_at: '2030-01-31', is_active: false, product_ids: [] });

    service.setPromotionProducts(7, [1, 2]).subscribe((promotion) => expect(promotion.product_ids).toEqual([1, 2]));
    const products = http.expectOne('/api/v1/promotions/7/products');
    expect(products.request.method).toBe('POST');
    expect(products.request.body).toEqual({ product_ids: [1, 2] });
    products.flush({ id: 7, name: 'Promo', description: null, discount_type: 'PERCENT', discount_value: 10, starts_at: '2030-01-01', ends_at: '2030-01-31', is_active: true, product_ids: [1, 2] });
  });
});
