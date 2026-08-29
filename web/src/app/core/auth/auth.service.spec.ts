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
});
