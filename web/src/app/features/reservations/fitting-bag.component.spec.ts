import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { CatalogDetail, CatalogVariant } from '../../core/models/api.models';
import { OfflineTransactionService } from '../../core/offline/offline-transaction.service';
import { FittingBagService } from '../../core/reservations/fitting-bag.service';
import { ReservationService } from '../../core/reservations/reservation.service';
import { FittingBagComponent } from './fitting-bag.component';

describe('FittingBagComponent', () => {
  let fixture: ComponentFixture<FittingBagComponent>;
  let component: FittingBagComponent;
  let bag: FittingBagService;
  let reservations: { create: ReturnType<typeof vi.fn> };
  let offlineTx: { recordOfflineReservation: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    localStorage.clear();
    reservations = { create: vi.fn(() => of({ id: 42 } as any)) };
    offlineTx = {
      recordOfflineReservation: vi.fn(() =>
        Promise.resolve({
          client_operation_id: 'op-web-res-001',
          operation_type: 'RESERVATION',
          status: 'PENDING_SYNC',
        } as any),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [FittingBagComponent],
      providers: [
        provideRouter([]),
        { provide: ReservationService, useValue: reservations },
        { provide: OfflineTransactionService, useValue: offlineTx },
      ],
    }).compileComponents();

    bag = TestBed.inject(FittingBagService);
    bag.clear();
    fixture = TestBed.createComponent(FittingBagComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    bag.clear();
    localStorage.clear();
  });

  it('keeps one row per variant and submits one reservation with every item', () => {
    bag.add(product(1, 'Camisa Lino'), variant(11, 'S', 'Blanco'), [availableBranch(7, 4)]);
    bag.add(product(1, 'Camisa Lino'), variant(11, 'S', 'Blanco'), [availableBranch(7, 4)]);
    bag.add(product(2, 'Pantalón Recto'), variant(22, 'M', 'Negro'), [availableBranch(7, 3), availableBranch(8, 3)]);

    expect(bag.items()).toHaveLength(2);
    expect(bag.items()[0].quantity).toBe(2);

    component.selectedBranchId = 7;
    component.visitDate = component.minimumReservationDate;
    component.submit();

    expect(reservations.create).toHaveBeenCalledTimes(1);
    expect(reservations.create).toHaveBeenCalledWith({
      branch_id: 7,
      scheduled_for: `${component.minimumReservationDate}T10:00:00`,
      items: [
        { product_variant_id: 11, quantity: 2 },
        { product_variant_id: 22, quantity: 1 },
      ],
    });
  });

  it('requires a branch shared by all garments before submitting', () => {
    bag.add(product(1, 'Camisa Lino'), variant(11, 'S', 'Blanco'), [availableBranch(7, 1)]);
    bag.add(product(2, 'Pantalón Recto'), variant(22, 'M', 'Negro'), [availableBranch(8, 1)]);

    component.selectedBranchId = 7;
    component.visitDate = component.minimumReservationDate;
    component.submit();

    expect(bag.sharedBranches()).toEqual([]);
    expect(reservations.create).not.toHaveBeenCalled();
  });

  it('records an offline reservation in IndexedDB when offline (CU-09)', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    bag.add(product(1, 'Camisa Lino'), variant(11, 'S', 'Blanco'), [availableBranch(7, 4)]);

    component.selectedBranchId = 7;
    component.visitDate = component.minimumReservationDate;
    component.customerName = 'Lucía Vargas';
    component.customerNit = '8492013';
    component.customerPhone = '71029384';
    component.submit();

    await Promise.resolve();
    await Promise.resolve();

    expect(reservations.create).not.toHaveBeenCalled();
    expect(offlineTx.recordOfflineReservation).toHaveBeenCalledTimes(1);
    expect(offlineTx.recordOfflineReservation).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        customer_name: 'Lucía Vargas',
        customer_nit: '8492013',
        customer_phone: '71029384',
        items: [{ product_variant_id: 11, quantity: 1 }],
      }),
    );
    expect(component.offlineReservationId).toBe('op-web-res-001');
  });
});

function product(id: number, name: string): CatalogDetail {
  return {
    id,
    category_id: 1,
    category_name: 'Camisas',
    audience: 'UNISEX',
    code: `P-${id}`,
    name,
    slug: name.toLowerCase().replace(/\s+/g, '-'),
    price: 120,
    image_url: null,
    size_system: 'ALPHA',
    description: null,
    images: [],
    variants: [],
  };
}

function variant(id: number, size: string, color: string): CatalogVariant {
  return {
    id,
    size_id: id,
    size_name: size,
    size_type: 'ALPHA',
    sort_order: 1,
    color_id: id,
    color_name: color,
    sku: `SKU-${id}`,
    stock_total: 4,
    available: true,
  };
}

function availableBranch(id: number, stock: number) {
  return { branch_id: id, branch_name: `Sucursal ${id}`, city_name: 'La Paz', address: 'Centro', available: true, stock };
}
