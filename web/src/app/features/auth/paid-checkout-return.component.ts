import { CommonModule, Location } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, concat, of, timer } from 'rxjs';
import { finalize, switchMap, take, takeWhile } from 'rxjs/operators';

import { AuthService, PaidCheckoutStatusResponse } from '../../core/auth/auth.service';

type CheckoutStatus = PaidCheckoutStatusResponse['status'] | 'EMAIL_CONFLICT' | 'NOT_FOUND' | 'UNAVAILABLE' | 'TIMEOUT';
const MAX_STATUS_POLLS = 15;
const STATUS_POLL_INTERVAL_MS = 2000;

@Component({
  selector: 'app-paid-checkout-return',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="auth-page-shell">
      <section class="auth-card" aria-live="polite">
        @if (isCancel) {
          <p class="eyebrow">Checkout cancelado</p>
          <h1>No se activó ningún acceso</h1>
          <p class="muted">No se realizó el pago y tu empresa no fue activada. Podés volver a elegir el plan cuando quieras.</p>
          <a class="button button-dark" routerLink="/">Volver a los planes</a>
        } @else if (status === 'COMPLETED') {
          <p class="eyebrow">Pago confirmado</p>
          <h1>Tu cuenta está activa</h1>
          <p class="muted">El pago fue confirmado y el correo de confirmación está en camino. Iniciá sesión con el email y contraseña de registro.</p>
          <a class="button button-dark" routerLink="/login">Ir a iniciar sesión</a>
        } @else if (status === 'PENDING' || status === 'CHECKOUT_CREATED') {
          <p class="eyebrow">Pago recibido</p>
          <h1>Estamos confirmando tu pago</h1>
          <p class="muted">Todavía no hay confirmación del webhook. Seguimos consultando; el acceso se habilitará cuando Stripe confirme el pago.</p>
        } @else if (status === 'EMAIL_CONFLICT') {
          <p class="eyebrow">Necesitamos revisar tu registro</p>
          <h1>El correo ya está asociado a una cuenta</h1>
          <p class="muted">No creamos una cuenta nueva ni mostramos datos de la cuenta existente. Iniciá sesión con ese correo o contactá a soporte para completar el pago.</p>
          <a class="button button-dark" routerLink="/login">Ir a iniciar sesión</a>
        } @else if (status === 'EXPIRED') {
          <p class="eyebrow">Checkout vencido</p>
          <h1>El enlace de pago venció</h1>
          <p class="muted">No se habilitó ningún acceso. Volvé a los planes para iniciar un checkout nuevo.</p>
          <a class="button button-dark" routerLink="/">Volver a los planes</a>
        } @else if (status === 'TIMEOUT') {
          <p class="eyebrow">Confirmación pendiente</p>
          <h1>Todavía no podemos confirmar tu pago</h1>
          <p class="muted">La confirmación está tardando más de lo esperado. Revisá nuevamente más tarde o contactá a soporte; no vuelvas a enviar tus datos.</p>
          <button class="button button-dark" type="button" (click)="retryStatus()">Revisar estado nuevamente</button>
        } @else if (status === 'NOT_FOUND') {
          <p class="eyebrow">Checkout no encontrado</p>
          <h1>No pudimos encontrar esta sesión</h1>
          <p class="muted">El enlace no es válido o ya no está disponible. No se habilitó ningún acceso.</p>
          <a class="button button-dark" routerLink="/">Volver a los planes</a>
        } @else if (status === 'UNAVAILABLE') {
          <p class="eyebrow">Servicio no disponible</p>
          <h1>No pudimos consultar el pago</h1>
          <p class="muted">Hay un problema temporal. Intentá nuevamente más tarde o contactá a soporte.</p>
          <button class="button button-dark" type="button" (click)="retryStatus()">Revisar estado nuevamente</button>
        } @else if (status === 'ERROR') {
          <p class="eyebrow">No pudimos confirmar el checkout</p>
          <h1>Revisá el estado de tu pago</h1>
          <p class="muted">No se habilitó ningún acceso desde esta página. Si completaste el pago, esperá la confirmación o contactá a soporte.</p>
          <a class="button button-dark" routerLink="/">Volver a los planes</a>
        }
      </section>
    </div>
  `,
})
export class PaidCheckoutReturnComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly location = inject(Location);

  readonly isCancel = this.route.snapshot.data?.['checkoutState'] === 'cancel';
  status: CheckoutStatus = 'ERROR';
  private sessionId: string | null = null;

  ngOnInit(): void {
    if (this.isCancel) return;
    this.sessionId = this.route.snapshot.queryParamMap.get('session_id');
    if (!this.sessionId) {
      this.status = 'NOT_FOUND';
      return;
    }
    this.location.replaceState(this.location.path().split('?')[0]);
    this.pollStatus();
  }

  retryStatus(): void {
    if (!this.sessionId || !['TIMEOUT', 'UNAVAILABLE'].includes(this.status)) return;
    this.pollStatus();
  }

  private pollStatus(): void {
    if (!this.sessionId) return;
    let completed = false;
    concat(of(0), timer(STATUS_POLL_INTERVAL_MS, STATUS_POLL_INTERVAL_MS)).pipe(
      switchMap(() => this.auth.getPaidCheckoutStatus(this.sessionId as string)),
      takeWhile((result) => {
        const nextStatus = result.status as CheckoutStatus;
        completed = nextStatus !== 'PENDING' && nextStatus !== 'CHECKOUT_CREATED';
        this.status = nextStatus;
        return !completed;
      }, true),
      take(MAX_STATUS_POLLS),
      catchError((error: HttpErrorResponse) => {
        this.status = error?.status === 404 ? 'NOT_FOUND' : 'UNAVAILABLE';
        return of(null);
      }),
      finalize(() => {
        if (!completed && (this.status === 'PENDING' || this.status === 'CHECKOUT_CREATED')) this.status = 'TIMEOUT';
      }),
    ).subscribe();
  }
}
