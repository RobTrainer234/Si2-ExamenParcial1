import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { ReservationService } from './reservation.service';

describe('ReservationService', () => {
  let service: ReservationService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(ReservationService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('loads the customer reservations', () => {
    service.mine().subscribe((page) => expect(page.total).toBe(1));
    const request = http.expectOne((item) => item.url === '/api/v1/reservations/mine');
    expect(request.request.params.get('page_size')).toBe('100');
    request.flush({ items: [], page: 1, page_size: 100, total: 1, total_pages: 1 });
  });

  it('creates and cancels a reservation', () => {
    const payload = { branch_id: 2, scheduled_for: '2030-01-02T10:00:00', items: [{ product_variant_id: 8, quantity: 1 }] };
    service.create(payload).subscribe();
    const createRequest = http.expectOne('/api/v1/reservations');
    expect(createRequest.request.method).toBe('POST');
    expect(createRequest.request.body).toEqual(payload);
    createRequest.flush({});

    service.cancel(4).subscribe();
    const cancelRequest = http.expectOne('/api/v1/reservations/4/cancel');
    expect(cancelRequest.request.method).toBe('PATCH');
    cancelRequest.flush({});
  });
});
