import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';

import { NotificationService } from '../notifications/notification.service';
import { AuthService } from './auth.service';
import { authInterceptor } from './auth.interceptor';

const session = {
  access_token: 'stale-access-token',
  refresh_token: 'refresh-token',
  token_type: 'bearer',
  user: { id: 1, first_name: 'Ana', last_name: 'Lopez', email: 'admin@example.com', phone: '70000000', role: 'ADMIN', is_active: true },
};

describe('authInterceptor', () => {
  let client: HttpClient;
  let http: HttpTestingController;
  let auth: AuthService;
  let notifications: NotificationService;
  let router: { navigateByUrl: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('fashionstore_session', JSON.stringify(session));
    router = { navigateByUrl: vi.fn() };
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: Router, useValue: router },
      ],
    });
    client = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
    notifications = TestBed.inject(NotificationService);
  });

  afterEach(() => http.verify());

  it('clears a stale session and redirects to login when a protected API request returns 401', () => {
    client.post('/api/v1/users', { email: 'new@example.com' }).subscribe({ error: () => undefined });
    const request = http.expectOne('/api/v1/users');
    expect(request.request.headers.get('Authorization')).toBe('Bearer stale-access-token');

    request.flush({ detail: 'Not authenticated' }, { status: 401, statusText: 'Unauthorized' });

    expect(auth.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('fashionstore_session')).toBeNull();
    expect(router.navigateByUrl).toHaveBeenCalledWith('/login');
    expect(notifications.messages().at(-1)?.message).toBe('Tu sesión expiró. Vuelve a iniciar sesión.');
  });

  it.each(['/api/v1/auth/login', '/api/v1/auth/register', '/api/v1/auth/refresh'])('does not attach the stale token or clear the session for %s', (url) => {
    client.post(url, {}).subscribe({ error: () => undefined });
    const request = http.expectOne(url);
    expect(request.request.headers.has('Authorization')).toBe(false);

    request.flush({ detail: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });

    expect(auth.isAuthenticated()).toBe(true);
    expect(router.navigateByUrl).not.toHaveBeenCalled();
    expect(notifications.messages()).toEqual([]);
  });

  it('keeps backend validation messages visible for admin create-user errors', () => {
    client.post('/api/v1/users', { email: 'taken@example.com' }).subscribe({ error: () => undefined });
    const request = http.expectOne('/api/v1/users');

    request.flush({ detail: 'El correo ya está registrado.' }, { status: 400, statusText: 'Bad Request' });

    expect(auth.isAuthenticated()).toBe(true);
    expect(router.navigateByUrl).not.toHaveBeenCalled();
    expect(notifications.messages().at(-1)?.message).toBe('El correo ya está registrado.');
  });
});
