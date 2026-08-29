import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';

import { adminGuard } from './role.guard';

const session = (role: string) => JSON.stringify({
  access_token: 'access',
  refresh_token: 'refresh',
  token_type: 'bearer',
  user: { id: 1, first_name: 'Test', last_name: 'User', email: 'test@example.com', phone: '70000000', role, is_active: true },
});

describe('adminGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
  });

  it('allows administrators', () => {
    localStorage.setItem('fashionstore_session', session('ADMIN'));
    const result = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(result).toBe(true);
  });

  it('redirects clients to the catalog', () => {
    localStorage.setItem('fashionstore_session', session('CLIENT'));
    const result = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/catalog');
  });
});
