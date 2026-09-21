import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { appConfig } from '../config/app-config';
import { CommerceService } from './commerce.service';

describe('CommerceService', () => {
  let service: CommerceService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(CommerceService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('sends sandbox signature when approving demo electronic payment', () => {
    service.approveSandbox('SANDBOX-1', 200).subscribe((response) => expect(response.status).toBe('APPROVED'));

    const request = http.expectOne('/api/v1/payments/electronic/notification');
    expect(request.request.method).toBe('POST');
    expect(request.request.headers.get('X-Sandbox-Signature')).toBe(appConfig.sandboxPaymentWebhookSecret);
    expect(request.request.body).toEqual({ transaction_reference: 'SANDBOX-1', amount: 200, status: 'APPROVED' });
    request.flush({ id: 1, sale_id: 2, method: 'CARD', provider: 'SANDBOX', transaction_reference: 'SANDBOX-1', status: 'APPROVED', amount: '200.00', received_amount: null, change_amount: null, paid_at: '2030-01-01T00:00:00Z' });
  });

  it('keeps pickup digital purchase payload compatible by default', () => {
    service.digitalPurchase(3).subscribe((sale) => expect(sale.id).toBe(10));

    const request = http.expectOne('/api/v1/purchases/digital');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ branch_id: 3 });
    request.flush({ id: 10, order_number: 'FS-10', customer_id: 1, branch_id: 3, cashier_id: null, channel: 'DIGITAL', status: 'PENDING', subtotal: '100.00', discount: '0.00', total: '100.00', created_at: '2030-01-01T00:00:00Z', items: [], payments: [], fulfillment_type: 'PICKUP', shipping_details: null });
  });

  it('sends delivery fulfillment details additively for digital purchase', () => {
    service.digitalPurchase(4, {
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
    }).subscribe((sale) => expect(sale.id).toBe(11));

    const request = http.expectOne('/api/v1/purchases/digital');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      branch_id: 4,
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
    });
    request.flush({ id: 11, order_number: 'FS-11', customer_id: 1, branch_id: 4, cashier_id: null, channel: 'DIGITAL', status: 'PENDING', subtotal: '100.00', discount: '0.00', total: '100.00', created_at: '2030-01-01T00:00:00Z', items: [], payments: [], fulfillment_type: 'DELIVERY', shipping_details: null });
  });

  it('loads cycle 3 customer surfaces', () => {
    service.purchaseHistory().subscribe((page) => expect(page.total).toBe(1));
    const history = http.expectOne('/api/v1/purchases/mine');
    expect(history.request.method).toBe('GET');
    history.flush({ items: [], page: 1, page_size: 20, total: 1, total_pages: 1 });

    service.purchaseDetail(5).subscribe((sale) => expect(sale.id).toBe(5));
    const detail = http.expectOne('/api/v1/purchases/mine/5');
    expect(detail.request.method).toBe('GET');
    detail.flush({ id: 5, order_number: 'ORD-5', customer_id: 1, branch_id: null, cashier_id: null, channel: 'DIGITAL', status: 'PAID', subtotal: '100.00', discount: '0.00', total: '100.00', created_at: '2030-01-01T00:00:00Z', items: [], payments: [] });

    service.recommendations().subscribe((response) => expect(response.items.length).toBe(1));
    const recommendations = http.expectOne('/api/v1/recommendations/mine');
    expect(recommendations.request.method).toBe('GET');
    recommendations.flush({ items: [{ product_id: 1, product_name: 'Camisa', category_name: 'Camisas', price: '100.00', image_url: null, score: '0.8', reason: 'Disponible' }] });

    service.startVirtualFitting(1).subscribe((session) => expect(session.status).toBe('STARTED'));
    const fitting = http.expectOne('/api/v1/virtual-fitting/sessions');
    expect(fitting.request.method).toBe('POST');
    expect(fitting.request.body.product_id).toBe(1);
    fitting.flush({ id: 1, customer_id: 2, product_id: 1, product_name: 'Camisa', image_url: null, status: 'STARTED', device_info: 'web-preview', started_at: '2030-01-01T00:00:00Z', ended_at: null });
  });

  it('manages stripe payment intent and confirmation', () => {
    service.stripePaymentIntent(10, 'key-123').subscribe((res) => {
      expect(res.payment_intent_id).toBe('pi_123');
      expect(res.client_secret).toBe('pi_123_secret_xyz');
    });
    const intentReq = http.expectOne('/api/v1/payments/stripe/intent');
    expect(intentReq.request.method).toBe('POST');
    expect(intentReq.request.body).toEqual({ sale_id: 10, idempotency_key: 'key-123', method: 'CARD' });
    intentReq.flush({
      payment_id: 1,
      sale_id: 10,
      provider: 'STRIPE',
      payment_intent_id: 'pi_123',
      client_secret: 'pi_123_secret_xyz',
      amount: 150,
      currency: 'BOB',
      status: 'PENDING',
    });

    service.confirmStripePayment('pi_123').subscribe((sale) => {
      expect(sale.status).toBe('CONFIRMED');
    });
    const confirmReq = http.expectOne('/api/v1/payments/stripe/confirm');
    expect(confirmReq.request.method).toBe('POST');
    expect(confirmReq.request.body).toEqual({ payment_intent_id: 'pi_123' });
    confirmReq.flush({
      id: 10,
      order_number: 'ORD-10',
      status: 'CONFIRMED',
      total: 150,
      items: [],
      payments: [],
    });
  });

  it('generates QR payment and simulates bank transfer', () => {
    service.generateQrPayment(20).subscribe((res) => {
      expect(res.transaction_reference).toBe('QR-REF-1');
      expect(res.amount).toBe(200);
    });
    const qrReq = http.expectOne('/api/v1/payments/qr/generate');
    expect(qrReq.request.method).toBe('POST');
    expect(qrReq.request.body).toEqual({ sale_id: 20 });
    qrReq.flush({
      payment_id: 2,
      sale_id: 20,
      order_number: 'ORD-20',
      amount: 200,
      currency: 'BOB',
      qr_data: 'data',
      qr_image_url: 'https://example.com/qr.png',
      business_name: 'FashionStore',
      nit: '123',
      bank_name: 'BNB',
      transaction_reference: 'QR-REF-1',
      expires_at: '2030-01-01T00:00:00Z',
      status: 'PENDING',
    });

    service.simulateQrPayment('QR-REF-1', 200).subscribe((sale) => {
      expect(sale.status).toBe('CONFIRMED');
    });
    const simReq = http.expectOne('/api/v1/payments/qr/simulate');
    expect(simReq.request.method).toBe('POST');
    expect(simReq.request.body).toEqual({ transaction_reference: 'QR-REF-1', amount: 200 });
    simReq.flush({
      id: 20,
      order_number: 'ORD-20',
      status: 'CONFIRMED',
      total: 200,
      items: [],
      payments: [],
    });
  });
});


