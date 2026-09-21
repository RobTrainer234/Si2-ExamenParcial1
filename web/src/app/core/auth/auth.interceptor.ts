import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';

import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, tap, throwError } from 'rxjs';

import { NotificationService } from '../notifications/notification.service';
import { AuthService } from './auth.service';

const MUTATING_METHODS = new Set(['POST', 'PATCH', 'DELETE']);
const AUTH_ENDPOINT_PATHS = ['/auth/login', '/auth/register', '/auth/refresh'];
const SESSION_EXPIRED_MESSAGE = 'Tu sesión expiró. Vuelve a iniciar sesión.';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  if (isAuthEndpoint(request.url)) {
    return next(request);
  }

  const auth = inject(AuthService);
  const notifications = inject(NotificationService);
  const router = inject(Router);
  const token = auth.accessToken();
  const handledRequest = token ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : request;
  const isMutating = MUTATING_METHODS.has(handledRequest.method.toUpperCase());

  return next(handledRequest).pipe(
    tap((event) => {
      if (event instanceof HttpResponse && isMutating) {
        notifications.success(successMessage(handledRequest.method));
      }
    }),
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse) {
        if (error.status === 401) {
          auth.clearSession();
          notifications.error(SESSION_EXPIRED_MESSAGE);
          router.navigateByUrl('/login');
        } else {
          notifications.error(errorMessage(error));
        }
      }
      return throwError(() => error);
    }),
  );
};

function isAuthEndpoint(url: string): boolean {
  return AUTH_ENDPOINT_PATHS.some((path) => url.includes(path));
}

function successMessage(method: string): string {
  switch (method.toUpperCase()) {
    case 'POST':
      return 'Operación creada correctamente.';
    case 'PATCH':
      return 'Cambios guardados correctamente.';
    case 'DELETE':
      return 'Elemento eliminado correctamente.';
    default:
      return 'Operación completada correctamente.';
  }
}

function errorMessage(error: HttpErrorResponse): string {
  const detail = error.error?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message) return detail.message;
  return 'No se pudo completar la solicitud.';
}
