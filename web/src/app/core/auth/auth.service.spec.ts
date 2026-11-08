import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('stores the session after login', () => {
    service.login('client@example.com', 'Secure123!').subscribe();
    const request = http.expectOne('/api/v1/auth/login');
    expect(request.request.method).toBe('POST');
    request.flush({
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
      user: { id: 1, first_name: 'Ana', last_name: 'Lopez', email: 'client@example.com', phone: '70000000', role: 'CLIENT', is_active: true },
    });

    expect(service.isAuthenticated()).toBe(true);
    expect(service.currentUser()?.role).toBe('CLIENT');
    expect(service.accessToken()).toBe('access-token');
  });

  it('clears the session on logout', () => {
    service.login('client@example.com', 'Secure123!').subscribe();
    const loginRequest = http.expectOne('/api/v1/auth/login');
    loginRequest.flush({
      access_token: 'access',
      refresh_token: 'refresh',
      token_type: 'bearer',
      user: { id: 1, first_name: 'Ana', last_name: 'Lopez', email: 'client@example.com', phone: '70000000', role: 'CLIENT', is_active: true },
    });

    service.logout();
    const request = http.expectOne('/api/v1/auth/logout');
    expect(request.request.body).toEqual({ refresh_token: 'refresh' });
    request.flush(null);
    expect(service.isAuthenticated()).toBe(false);
  });

  it('starts email verification with the exact email payload', () => {
    service.startEmailVerification('ada@example.com').subscribe();

    const request = http.expectOne('/api/v1/subscriptions/email-verification/start');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ email: 'ada@example.com' });
    request.flush({ accepted: true, email_sent: true });
  });

  it('verifies the code with the exact payload and returns checkout capability', () => {
    service.verifyEmail('ada@example.com', '123456').subscribe((response) => {
      expect(response).toEqual({ verified: true, checkout_capability: 'capability-token' });
    });

    const request = http.expectOne('/api/v1/subscriptions/email-verification/verify');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ email: 'ada@example.com', code: '123456' });
    request.flush({ verified: true, checkout_capability: 'capability-token' });
  });

  it('requires checkout capability in paid checkout payload', () => {
    service.registerPaidCheckout({
      company_name: 'Acme', first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com',
      phone: '70000000', password: 'StrongPass1!', plan_code: 'BASIC', billing_interval: 'annual',
      checkout_capability: 'capability-token',
    }).subscribe();

    const request = http.expectOne('/api/v1/subscriptions/paid-checkout');
    expect(request.request.body).toEqual(expect.objectContaining({
      plan_code: 'BASIC', billing_interval: 'annual', checkout_capability: 'capability-token',
    }));
    request.flush({ session_id: 'cs_test', session_url: 'https://checkout.test' });
  });

  it('clears the local session without calling logout', () => {
    service.login('client@example.com', 'Secure123!').subscribe();
    const loginRequest = http.expectOne('/api/v1/auth/login');
    loginRequest.flush({
      access_token: 'access',
      refresh_token: 'refresh',
      token_type: 'bearer',
      user: { id: 1, first_name: 'Ana', last_name: 'Lopez', email: 'client@example.com', phone: '70000000', role: 'CLIENT', is_active: true },
    });

    service.clearSession();

    expect(service.isAuthenticated()).toBe(false);
    expect(service.accessToken()).toBeNull();
    expect(localStorage.getItem('fashionstore_session')).toBeNull();
  });
});
