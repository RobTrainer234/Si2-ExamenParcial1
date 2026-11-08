import { routes } from './app.routes';

describe('application routes', () => {
  it('serves the public landing at the root and includes self-service company trial and platform admin routes while preserving existing routes', () => {
    const rootRoute = routes.find((route) => route.path === '');
    const allPaths = routes.map((route) => route.path);

    expect(rootRoute?.pathMatch).toBe('full');
    expect(rootRoute?.redirectTo).toBeUndefined();
    expect(rootRoute?.loadComponent).toBeDefined();
    expect(allPaths).toEqual(
      expect.arrayContaining(['catalog', 'login', 'register', 'register-company', 'platform', 'admin']),
    );
  });
});

