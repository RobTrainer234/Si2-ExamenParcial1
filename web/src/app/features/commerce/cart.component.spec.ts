import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { CatalogService } from '../../core/catalog/catalog.service';
import { CommerceService } from '../../core/commerce/commerce.service';
import { CartComponent } from './cart.component';

describe('CartComponent delivery checkout', () => {
  let fixture: ComponentFixture<CartComponent>;
  let commerce: { cart: ReturnType<typeof vi.fn>; digitalPurchase: ReturnType<typeof vi.fn> };

  const createComponent = async () => {
    commerce = {
      cart: vi.fn(() => of({ id: 1, customer_id: 1, status: 'ACTIVE', items: [], subtotal: 100, total: 100, updated_at: '2030-01-01T00:00:00Z' })),
      digitalPurchase: vi.fn(() => of({ id: 9, order_number: 'FS-9', customer_id: 1, branch_id: 2, cashier_id: null, channel: 'DIGITAL', status: 'PENDING', subtotal: 100, discount: 0, total: 100, created_at: '2030-01-01T00:00:00Z', items: [], payments: [] })),
    };

    await TestBed.configureTestingModule({
      imports: [CartComponent],
      providers: [
        provideRouter([]),
        { provide: CommerceService, useValue: commerce },
        { provide: CatalogService, useValue: { filters: vi.fn(() => of({ branches: [{ id: 2, name: 'Central' }], categories: [], sizes: [], colors: [], audiences: [] })) } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CartComponent);
    fixture.detectChanges();
  };

  it('defaults to pickup and builds the legacy pickup purchase payload', async () => {
    await createComponent();
    const component = fixture.componentInstance;
    component.branchId = 2;

    expect(component.fulfillmentType).toBe('PICKUP');
    expect(component.buildDigitalPurchaseOptions()).toEqual(undefined);
  });

  it('requires every structured shipping field before delivery checkout', async () => {
    await createComponent();
    const component = fixture.componentInstance;
    component.branchId = 2;
    component.fulfillmentType = 'DELIVERY';
    component.shippingDetails = {
      recipient_name: 'Ana Pérez',
      recipient_ci: '',
      recipient_phone: '70000000',
      department_or_city: 'Santa Cruz',
      zone: 'Equipetrol',
      street: 'Av. San Martín',
      house_number: '55',
      reference: 'Portón negro',
    };

    expect(component.validateCheckout()).toBe(false);
    expect(component.message).toContain('CI');
  });

  it('builds delivery payload without changing the checkout total', async () => {
    await createComponent();
    const component = fixture.componentInstance;
    component.branchId = 2;
    component.fulfillmentType = 'DELIVERY';
    component.shippingDetails = {
      recipient_name: 'Ana Pérez',
      recipient_ci: '1234567',
      recipient_phone: '70000000',
      department_or_city: 'Santa Cruz',
      zone: 'Equipetrol',
      street: 'Av. San Martín',
      house_number: '55',
      reference: 'Portón negro',
    };

    expect(component.validateCheckout()).toBe(true);
    expect(component.buildDigitalPurchaseOptions()).toEqual({
      fulfillment_type: 'DELIVERY',
      shipping_details: component.shippingDetails,
    });
    expect(component.cart?.total).toBe(100);
  });
});
