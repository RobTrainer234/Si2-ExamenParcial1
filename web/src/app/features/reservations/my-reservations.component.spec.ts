import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, Subject } from 'rxjs';
import { vi } from 'vitest';

import { ReservationService } from '../../core/reservations/reservation.service';
import { Reservation } from '../../core/models/admin.models';
import { MyReservationsComponent } from './my-reservations.component';

const reservation = (overrides: Partial<Reservation> = {}): Reservation => ({
  id: 11,
  customer_id: 3,
  customer_name: 'Cliente Moda',
  branch_id: 2,
  branch_name: 'Sucursal Centro',
  branch_city_name: 'Santa Cruz',
  branch_address: 'Av. Moda 123',
  branch_phone: '70000000',
  branch_latitude: -17.783333,
  branch_longitude: -63.182125,
  scheduled_for: '2026-02-10T15:30:00Z',
  status: 'PENDING',
  notes: null,
  expires_at: '2026-02-12T15:30:00Z',
  created_at: '2026-02-01T12:00:00Z',
  items: [
    { id: 1, product_variant_id: 8, product_id: 7, product_name: 'Blazer Jacinta', sku: 'BLA-M-NEG', size_name: 'M', color_name: 'Negro', quantity: 1, unit_price: 320 },
    { id: 2, product_variant_id: 9, product_id: 8, product_name: 'Pantalón Sastre', sku: 'PAN-40-BEI', size_name: '40', color_name: 'Beige', quantity: 2, unit_price: 260 },
  ],
  ...overrides,
});

describe('MyReservationsComponent customer presentation', () => {
  let fixture: ComponentFixture<MyReservationsComponent>;
  let reservationService: { mine: ReturnType<typeof vi.fn>; get: ReturnType<typeof vi.fn>; cancel: ReturnType<typeof vi.fn> };

  const createComponent = async (routeId: string | null = null, reservations: Reservation[] = [reservation()], delayedDetail?: Subject<Reservation>) => {
    TestBed.resetTestingModule();
    reservationService = {
      mine: vi.fn(() => of({ items: reservations, page: 1, page_size: 100, total: reservations.length, total_pages: 1 })),
      get: vi.fn((id: number) => delayedDetail?.asObservable() ?? of(reservations.find((item) => item.id === id) ?? reservation({ id }))),
      cancel: vi.fn((id: number) => of(reservation({ id, status: 'CANCELLED' }))),
    };

    await TestBed.configureTestingModule({
      imports: [MyReservationsComponent],
      providers: [
        provideRouter([]),
        { provide: ReservationService, useValue: reservationService },
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap(routeId ? { id: routeId } : {}) } } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MyReservationsComponent);
    fixture.detectChanges();
  };

  it('renders a customer summary and readable reservation cards with branch data and reservation code', async () => {
    await createComponent(null, [reservation(), reservation({ id: 12, status: 'ATTENDED', branch_name: 'Sucursal Norte' })]);

    const host: HTMLElement = fixture.nativeElement;

    expect(host.querySelector('.customer-reservations-hero')?.textContent).toContain('Mis reservas');
    expect(host.querySelector('.reservation-summary-strip')?.textContent).toContain('2');
    expect(host.querySelectorAll('a.customer-reservation-card')).toHaveLength(2);
    expect(host.textContent).toContain('FS-000011');
    expect(host.textContent).toContain('Sucursal Centro');
    expect(host.textContent).toContain('Av. Moda 123');
    expect(host.textContent).toContain('70000000');
    expect(host.textContent).toContain('2 ítems');
    expect(host.textContent).toContain('Blazer Jacinta');
    expect(host.textContent).toContain('Ver detalle');
  });

  it('renders selected reservation detail with item rows and keeps cancellation only for pending states', async () => {
    await createComponent('11', [reservation()]);

    const host: HTMLElement = fixture.nativeElement;

    expect(reservationService.get).toHaveBeenCalledWith(11);
    expect(host.querySelector('.customer-reservation-detail')?.textContent).toContain('Reserva FS-000011');
    expect(host.querySelector('.customer-reservation-detail')?.textContent).toContain('Sucursal Centro');
    expect(host.querySelector('.customer-reservation-detail')?.textContent).toContain('-17.783333, -63.182125');
    expect(host.querySelectorAll('.reservation-detail-item')).toHaveLength(2);
    expect(host.textContent).toContain('Bs 320');
    expect(Array.from(host.querySelectorAll('button')).some((button) => button.textContent?.includes('Cancelar reserva'))).toBe(true);
  });

  it('updates the detail article when detail loading completes after the list render pass', async () => {
    const delayedDetail = new Subject<Reservation>();
    await createComponent('11', [reservation()], delayedDetail);

    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.customer-reservation-detail')).toBeNull();

    delayedDetail.next(reservation());

    expect(host.querySelector('.customer-reservation-detail')?.textContent).toContain('Reserva FS-000011');
  });

  it('updates the visible error when delayed detail loading fails', async () => {
    const delayedDetail = new Subject<Reservation>();
    await createComponent('11', [reservation()], delayedDetail);

    const host: HTMLElement = fixture.nativeElement;

    delayedDetail.error(new Error('detail failed'));

    expect(host.querySelector('.admin-alert')?.textContent).toContain('No se pudo cargar el detalle de la reserva.');
  });

  it('hides cancellation for historical reservation states', async () => {
    await createComponent('11', [reservation({ status: 'ATTENDED' })]);

    const host: HTMLElement = fixture.nativeElement;

    expect(host.querySelector('.customer-reservation-detail')?.textContent).toContain('Atendida');
    expect(Array.from(host.querySelectorAll('button')).some((button) => button.textContent?.includes('Cancelar reserva'))).toBe(false);
  });

  it('filters loaded reservations with counts without changing the mine request', async () => {
    await createComponent(null, [
      reservation({ id: 11, status: 'PENDING' }),
      reservation({ id: 12, status: 'READY' }),
      reservation({ id: 13, status: 'ATTENDED' }),
      reservation({ id: 14, status: 'CANCELLED' }),
    ]);

    const host: HTMLElement = fixture.nativeElement;
    const buttons = Array.from(host.querySelectorAll('.reservation-filter-bar button')) as HTMLButtonElement[];

    expect(buttons.map((button) => button.textContent?.replace(/\s+/g, ' ').trim())).toEqual(['Todas4', 'Activas2', 'Historial1', 'Canceladas1']);

    buttons[1].click();
    fixture.detectChanges();

    expect(reservationService.mine).toHaveBeenCalledWith();
    expect(host.querySelectorAll('a.customer-reservation-card')).toHaveLength(2);
    expect(host.textContent).toContain('FS-000011');
    expect(host.textContent).toContain('FS-000012');
    expect(host.textContent).not.toContain('FS-000013');
  });

  it('renders a progress timeline and a terminal state message', async () => {
    await createComponent('11', [reservation({ status: 'READY' })]);

    let host: HTMLElement = fixture.nativeElement;
    expect(host.querySelectorAll('.reservation-timeline li.done')).toHaveLength(3);
    expect(host.querySelector('.reservation-timeline li.current')?.textContent).toContain('Lista');

    await createComponent('11', [reservation({ status: 'EXPIRED' })]);
    host = fixture.nativeElement;

    expect(host.querySelector('.reservation-terminal-state')?.textContent).toContain('Reserva vencida');
    expect(host.querySelector('.reservation-timeline')).toBeNull();
  });

  it('opens an accessible confirmation dialog before cancelling and disables actions while cancelling', async () => {
    const pendingCancel = new Subject<Reservation>();
    await createComponent('11', [reservation()]);
    reservationService.cancel.mockReturnValue(pendingCancel.asObservable());

    const host: HTMLElement = fixture.nativeElement;
    const cancelButton = Array.from(host.querySelectorAll('button')).find((button) => button.textContent?.includes('Cancelar reserva')) as HTMLButtonElement;

    cancelButton.click();
    fixture.detectChanges();

    const dialog = host.querySelector('[role="dialog"]');
    expect(dialog?.textContent).toContain('Cancelar reserva FS-000011');
    expect(reservationService.cancel).not.toHaveBeenCalled();

    const confirmButton = Array.from(host.querySelectorAll('.reservation-dialog-actions button')).find((button) => button.textContent?.includes('Sí, cancelar')) as HTMLButtonElement;
    confirmButton.click();
    fixture.detectChanges();

    expect(reservationService.cancel).toHaveBeenCalledWith(11);
    expect(confirmButton.disabled).toBe(true);

    pendingCancel.next(reservation({ status: 'CANCELLED' }));
    pendingCancel.complete();
    fixture.detectChanges();

    expect(host.querySelector('[role="dialog"]')).toBeNull();
  });
});
