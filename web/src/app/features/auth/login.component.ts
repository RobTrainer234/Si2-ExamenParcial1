import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';
import { NotificationService } from '../../core/notifications/notification.service';

@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-page-shell">
      <section class="auth-card">
        <div class="auth-brand-badge">
          <span class="auth-monogram">F</span>
          <div class="auth-brand-text">
            <strong>FashionStore</strong>
            <small>Atelier & Boutique</small>
          </div>
        </div>
        <p class="eyebrow">Tu armario, tu ritmo</p>
        <h1>Bienvenido de vuelta</h1>
        <p class="muted">Inicia sesión para consultar tu experiencia FashionStore.</p>
        <form [formGroup]="form" (ngSubmit)="submit()">
          <label>
            <span class="label-text">Correo electrónico</span>
            <input
              type="text"
              id="email"
              name="username"
              formControlName="email"
              autocomplete="username email"
              placeholder="admin@fashionstore.com"
            >
          </label>
          <label>
            <span class="label-text">Contraseña</span>
            <div class="auth-input-wrapper">
              <input
                [type]="showPassword ? 'text' : 'password'"
                id="password"
                name="password"
                formControlName="password"
                autocomplete="current-password"
                placeholder="••••••••••••"
                (keydown)="checkCapsLock($event)"
                (keyup)="checkCapsLock($event)"
              >
              <button
                type="button"
                class="password-toggle-btn"
                (click)="showPassword = !showPassword"
                [attr.aria-label]="showPassword ? 'Ocultar contraseña' : 'Ver contraseña'"
              >
                <span class="material-symbols-outlined">{{ showPassword ? 'visibility_off' : 'visibility' }}</span>
              </button>
            </div>
          </label>
          @if (capsLockOn) {
            <div class="caps-lock-warning" role="alert">
              <span class="material-symbols-outlined">warning</span>
              <span>El bloqueo de mayúsculas (Bloq Mayús) está activado</span>
            </div>
          }
          @if (error) { <p class="error">{{ error }}</p> }
          <button class="button button-dark auth-submit-btn" type="submit" [disabled]="form.invalid || loading">
            {{ loading ? 'Ingresando...' : 'Iniciar sesión' }}
          </button>
        </form>
        <p class="form-footer">¿Todavía no tienes cuenta? <a routerLink="/register">Regístrate como cliente</a></p>
        <p class="form-footer" style="margin-top: 8px; font-size: 0.76rem;">
          ¿Buscas usar FashionStore en tu empresa? <a routerLink="/register-company">Prueba gratis por 14 días</a>
        </p>
      </section>
    </div>
  `,
  styles: [`
    .auth-input-wrapper {
      position: relative;
      width: 100%;
      display: flex;
      align-items: center;
    }
    .auth-input-wrapper input {
      width: 100%;
      box-sizing: border-box;
      padding-right: 48px !important;
    }
    .password-toggle-btn {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      background: none !important;
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
      color: #7d7567;
      cursor: pointer;
      padding: 6px;
      margin: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      transition: color 0.2s, background-color 0.2s;
      z-index: 2;
    }
    .password-toggle-btn:hover {
      color: #1b1c1a;
      background-color: rgba(0, 0, 0, 0.06) !important;
    }
    .password-toggle-btn .material-symbols-outlined {
      font-size: 20px;
      display: block;
    }
    .caps-lock-warning {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #fefce8;
      border: 1px solid #fde047;
      color: #854d0e;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 500;
      margin-top: 4px;
    }
    .caps-lock-warning .material-symbols-outlined {
      font-size: 16px;
      color: #ca8a04;
    }
  `],
})
export class LoginComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notifications = inject(NotificationService);

  readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required]],
    password: ['', Validators.required],
  });

  loading = false;
  error = '';
  showPassword = false;
  capsLockOn = false;

  ngOnInit(): void {
    if (typeof window !== 'undefined' && window.sessionStorage) {
      const savedEmail = window.sessionStorage.getItem('fashionstore_last_email');
      if (savedEmail && !this.form.controls.email.value) {
        this.form.controls.email.setValue(savedEmail);
      }
    }
  }

  checkCapsLock(event: KeyboardEvent): void {
    if (typeof event.getModifierState === 'function') {
      this.capsLockOn = event.getModifierState('CapsLock');
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    const { email, password } = this.form.getRawValue();
    this.auth.login(email.trim(), password).pipe(finalize(() => { this.loading = false; })).subscribe({
      next: () => {
        this.notifications.success('Inicio de sesión correcto.');
        const targetRoute = this.auth.defaultHomeRoute();
        void this.router.navigateByUrl(targetRoute).catch(() => {
          this.notifications.error('No se pudo abrir la pantalla inicial.');
        });
      },
      error: (error: unknown) => {
        this.error = this.messageFromError(error, 'Correo o contraseña incorrectos.');
        this.notifications.error(this.error);
      },
    });
  }

  private messageFromError(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const detail = error.error?.detail;
      if (typeof detail === 'string') return detail;
      if (typeof detail?.message === 'string') return detail.message;
      if (typeof error.error?.message === 'string') return error.error.message;
    }
    return fallback;
  }
}
