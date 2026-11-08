import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { of, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { vi } from 'vitest';

import { AuthService } from '../../core/auth/auth.service';
import { PaidCheckoutReturnComponent } from './paid-checkout-return.component';

describe('PaidCheckoutReturnComponent', () => {
  let fixture: ComponentFixture<PaidCheckoutReturnComponent>;
  let component: PaidCheckoutReturnComponent;
  let auth: { getPaidCheckoutStatus: ReturnType<typeof vi.fn> };
  let location: { replaceState: ReturnType<typeof vi.fn>; path: ReturnType<typeof vi.fn> };
  let route: { snapshot: { queryParamMap: Map<string, string>; data?: Record<string, string> } };

  beforeEach(async () => {
    auth = { getPaidCheckoutStatus: vi.fn(() => of({ status: 'COMPLETED' })) };
    location = { replaceState: vi.fn(), path: vi.fn(() => '/subscription/success?session_id=cs_test') };
    route = { snapshot: { queryParamMap: new Map([['session_id', 'cs_test']]) } };
    await TestBed.configureTestingModule({
      imports: [PaidCheckoutReturnComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Location, useValue: location },
        { provide: ActivatedRoute, useValue: route },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(PaidCheckoutReturnComponent);
    component = fixture.componentInstance;
  });

  it('looks up the session and exposes the completed state without creating auth', () => {
    fixture.detectChanges();
    expect(auth.getPaidCheckoutStatus).toHaveBeenCalledWith('cs_test');
    expect(component.status).toBe('COMPLETED');
    expect(location.replaceState).toHaveBeenCalledWith('/subscription/success');
    expect(fixture.nativeElement.textContent).toContain('cuenta está activa');
    expect(fixture.nativeElement.textContent).toContain('correo de confirmación está en camino');
    expect(fixture.nativeElement.textContent).toContain('email y contraseña de registro');
    expect(fixture.nativeElement.querySelector('a[routerLink="/login"]')).not.toBeNull();
  });

  it('polls while the webhook is pending and stops after completion', async () => {
    vi.useFakeTimers();
    auth.getPaidCheckoutStatus.mockReset();
    auth.getPaidCheckoutStatus.mockReturnValueOnce(of({ status: 'CHECKOUT_CREATED' })).mockReturnValueOnce(of({ status: 'COMPLETED' }));
    fixture.detectChanges();
    await vi.advanceTimersByTimeAsync(2000);

    expect(auth.getPaidCheckoutStatus).toHaveBeenCalledTimes(2);
    expect(component.status).toBe('COMPLETED');
    vi.useRealTimers();
  });

  it('exposes an actionable email conflict state', () => {
    auth.getPaidCheckoutStatus.mockReturnValue(of({ status: 'EMAIL_CONFLICT' }));
    fixture.detectChanges();

    expect(component.status).toBe('EMAIL_CONFLICT');
    expect(fixture.nativeElement.textContent).toContain('correo');
  });

  it.each([
    ['EXPIRED', 'Checkout vencido'],
    ['NOT_FOUND', 'Checkout no encontrado'],
    ['UNAVAILABLE', 'Servicio no disponible'],
    ['ERROR', 'No pudimos confirmar el checkout'],
  ] as const)('renders %s explicitly', (status, eyebrow) => {
    auth.getPaidCheckoutStatus.mockReturnValue(of({ status }));
    fixture.detectChanges();

    expect(component.status).toBe(status);
    expect(fixture.nativeElement.textContent).toContain(eyebrow);
  });

  it('renders TIMEOUT after the bounded polling window', async () => {
    vi.useFakeTimers();
    auth.getPaidCheckoutStatus.mockReturnValue(of({ status: 'PENDING' }));
    fixture.detectChanges();
    await vi.advanceTimersByTimeAsync(28_000);

    expect(auth.getPaidCheckoutStatus).toHaveBeenCalledTimes(15);
    expect(component.status).toBe('TIMEOUT');
    vi.useRealTimers();
  });

  it('retries status for unavailable state without creating a checkout', () => {
    auth.getPaidCheckoutStatus.mockReturnValueOnce(throwError(() => new HttpErrorResponse({ status: 503 })));
    fixture.detectChanges();
    expect(component.status).toBe('UNAVAILABLE');

    component.retryStatus();

    expect(auth.getPaidCheckoutStatus).toHaveBeenCalledTimes(2);
    expect(auth.getPaidCheckoutStatus).toHaveBeenLastCalledWith('cs_test');
  });

  it('does not query without a session_id', () => {
    route.snapshot.queryParamMap = new Map();
    fixture.detectChanges();

    expect(auth.getPaidCheckoutStatus).not.toHaveBeenCalled();
    expect(component.status).toBe('NOT_FOUND');
  });

  it('maps HTTP errors to distinct unavailable and not-found states', () => {
    auth.getPaidCheckoutStatus.mockReturnValueOnce(throwError(() => new HttpErrorResponse({ status: 404 })));
    fixture.detectChanges();
    expect(component.status).toBe('NOT_FOUND');

    fixture = TestBed.createComponent(PaidCheckoutReturnComponent);
    component = fixture.componentInstance;
    auth.getPaidCheckoutStatus.mockReturnValueOnce(throwError(() => new HttpErrorResponse({ status: 503 })));
    fixture.detectChanges();
    expect(component.status).toBe('UNAVAILABLE');
  });
});
