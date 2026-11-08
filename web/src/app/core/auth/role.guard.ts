import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

import { AuthService } from './auth.service';

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) return router.createUrlTree(['/login']);
  const role = auth.currentUser()?.role;
  if (role === 'PLATFORM_ADMIN') return router.createUrlTree(['/platform']);
  return role === 'ADMIN' ? true : router.createUrlTree(['/catalog']);
};

export const platformAdminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) return router.createUrlTree(['/login']);
  return auth.currentUser()?.role === 'PLATFORM_ADMIN' ? true : router.createUrlTree([auth.defaultHomeRoute()]);
};

export const permissionGuard = (permission: string): CanActivateFn => () => {
  const auth = inject(AuthService);
  return auth.hasPermission(permission) ? true : inject(Router).createUrlTree(['/catalog']);
};

