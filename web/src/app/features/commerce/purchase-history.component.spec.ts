import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { CommerceService } from '../../core/commerce/commerce.service';
import { PurchaseHistoryComponent } from './purchase-history.component';

describe('PurchaseHistoryComponent fulfillment summary', () => {
  it('distinguishes pickup and delivery details for the purchaser', async () => {
    await TestBed.configureTestingModule({
      imports: [PurchaseHistoryComponent],
      providers: [{ provide: CommerceService, useValue: { purchaseHistory: vi.fn(() => of({ items: [], page: 1, page_size: 20, total: 0, total_pages: 0 })), purchaseDetail: vi.fn() } }],
    }).compileComponents();

    const fixture = TestBed.createComponent(PurchaseHistoryComponent);
    const component = fixture.componentInstance;

    expect(component.fulfillmentLabel({ fulfillment_type: 'PICKUP' } as any)).toBe('Retiro en tienda');
    expect(component.fulfillmentLabel({ fulfillment_type: 'DELIVERY' } as any)).toBe('Delivery');
    expect(component.shippingSummary({
      fulfillment_type: 'DELIVERY',
      shipping_details: {
        recipient_name: 'Ana Pérez',
        recipient_ci: '1234567',
        recipient_phone: '70000000',
        department_or_city: 'Santa Cruz',
        zone: 'Equipetrol',
        street: 'Av. San Martín',
        house_number: '55',
        reference: 'Portón negro',
      },
    } as any)).toContain('Ana Pérez · Av. San Martín 55, Equipetrol, Santa Cruz');
  });
});
