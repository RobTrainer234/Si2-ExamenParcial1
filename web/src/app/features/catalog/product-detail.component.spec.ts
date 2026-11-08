import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { CatalogService } from '../../core/catalog/catalog.service';
import { CommerceService } from '../../core/commerce/commerce.service';
import { FittingBagService } from '../../core/reservations/fitting-bag.service';
import { ProductDetailComponent } from './product-detail.component';

const localProduct = {
  id: 101, category_id: 1, category_name: 'Vestidos', audience: 'UNISEX' as const, code: 'D-101', name: 'Vestido local', slug: 'vestido-local', price: 350,
  description: 'Detalle guardado', size_system: 'ALPHA' as const, images: [],
  variants: [{ id: 1001, size_id: 1, size_name: 'S', size_type: 'ALPHA' as const, sort_order: 0, color_id: 2, color_name: 'Rojo', sku: 'D-101-S', stock_total: 3, available: true }],
};

describe('ProductDetailComponent offline detail availability', () => {
  let fixture: ComponentFixture<ProductDetailComponent>;
  let catalog: { detail: ReturnType<typeof vi.fn>; availability: ReturnType<typeof vi.fn>; lastDetailWasOffline: ReturnType<typeof vi.fn>; lastAvailabilityWasOffline: ReturnType<typeof vi.fn>; lastOfflineBranchName: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    catalog = {
      detail: vi.fn(() => of(localProduct)),
      availability: vi.fn(() => of([{ branch_id: 10, branch_name: 'Central', city_name: '', address: '', available: true, stock: 3 }])),
      lastDetailWasOffline: vi.fn(() => true),
      lastAvailabilityWasOffline: vi.fn(() => true),
      lastOfflineBranchName: vi.fn(() => 'Central'),
    };
    await TestBed.configureTestingModule({
      imports: [ProductDetailComponent],
      providers: [
        provideRouter([]),
        { provide: CatalogService, useValue: catalog },
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => '101' } } } },
        { provide: CommerceService, useValue: { addToCart: vi.fn(() => of({})), startVirtualFitting: vi.fn(() => of({ product_name: 'Vestido local' })) } },
        { provide: FittingBagService, useValue: { count: () => 0, add: vi.fn() } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ProductDetailComponent);
    fixture.detectChanges();
  });

  it('shows a clear offline status and synchronized branch availability', () => {
    const host = fixture.nativeElement as HTMLElement;
    expect(host.textContent).toContain('Vestido local');
    expect(host.textContent).toContain('Central');
    expect(host.textContent).toContain('Disponibilidad local');
    expect(host.textContent).toContain('pueden estar desactualizados');
  });

  it('does not crash when no saved product or selected variant exists', () => {
    fixture.componentInstance.product = null;
    fixture.componentInstance.selectedVariant = null;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('undefined');
  });
});
