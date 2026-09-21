import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';
import { NotificationService } from '../../core/notifications/notification.service';
import { PasswordRequirementsComponent } from '../../core/auth/password-requirements.component';
import { passwordPolicyValidator } from '../../core/auth/password-security.helper';

@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, PasswordRequirementsComponent],
  template: `
    <div class="auth-page-shell">
      <section class="auth-card wide">
        <div class="auth-brand-badge">
          <span class="auth-monogram">F</span>
          <div class="auth-brand-text">
            <strong>FashionStore</strong>
            <small>Atelier & Boutique</small>
          </div>
        </div>
        <p class="eyebrow">Una nueva forma de elegir</p>
        <h1>Crea tu cuenta</h1>
        <p class="muted">Guarda tus preferencias y consulta prendas disponibles cerca de ti.</p>
        <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
          <label>
            <span class="label-text">Nombres</span>
            <input formControlName="first_name" name="given-name" autocomplete="given-name" placeholder="Ana">
          </label>
          <label>
            <span class="label-text">Apellidos</span>
            <input formControlName="last_name" name="family-name" autocomplete="family-name" placeholder="Lopez">
          </label>
          <label>
            <span class="label-text">Teléfono</span>
            <input id="register-phone" name="phone" formControlName="phone" autocomplete="tel" placeholder="70000000">
          </label>
          <label>
            <span class="label-text">Correo electrónico</span>
            <input
              type="email"
              id="register-email"
              name="username"
              formControlName="email"
              autocomplete="username email"
              placeholder="ana@example.com"
            >
            @if (form.controls.email.dirty && form.controls.email.touched) {
              @if (form.controls.email.valid) {
                <small class="field-feedback valid"><span class="check-dot">✔</span> Correo electrónico válido</small>
              } @else {
                <small class="field-feedback invalid">Formato de correo no válido</small>
              }
            }
          </label>
          <label class="full">
            <span class="label-text">Contraseña</span>
            <div class="auth-input-wrapper">
              <input
                [type]="showPassword ? 'text' : 'password'"
                id="register-password"
                name="new-password"
                formControlName="password"
                autocomplete="new-password"
                placeholder="••••••••"
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
            <app-password-requirements [password]="form.controls.password.value" />
          </label>
          <label class="full">
            <span class="label-text">Confirmar contraseña</span>
            <div class="auth-input-wrapper">
              <input
                [type]="showConfirmPassword ? 'text' : 'password'"
                id="register-confirm-password"
                name="confirm-password"
                formControlName="confirm_password"
                autocomplete="new-password"
                placeholder="••••••••"
              >
              <button
                type="button"
                class="password-toggle-btn"
                (click)="showConfirmPassword = !showConfirmPassword"
                [attr.aria-label]="showConfirmPassword ? 'Ocultar confirmación' : 'Ver confirmación'"
              >
                <span class="material-symbols-outlined">{{ showConfirmPassword ? 'visibility_off' : 'visibility' }}</span>
              </button>
            </div>
            @if (form.controls.confirm_password.value) {
              @if (passwordsMatch) {
                <small class="field-feedback valid"><span class="check-dot">✔</span> Las contraseñas coinciden</small>
              } @else {
                <small class="field-feedback invalid">Las contraseñas no coinciden</small>
              }
            }
          </label>
          @if (error) { <p class="error full">{{ error }}</p> }
          <button
            class="button button-dark full auth-submit-btn"
            type="submit"
            [disabled]="form.invalid || !passwordsMatch || loading"
          >
            {{ loading ? 'Creando cuenta...' : 'Crear cuenta' }}
          </button>
        </form>
        <p class="form-footer">¿Ya tienes cuenta? <a routerLink="/login">Inicia sesión</a></p>
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
  `],
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notifications = inject(NotificationService);

  readonly form = inject(FormBuilder).nonNullable.group({
    first_name: ['', [Validators.required, Validators.minLength(2)]],
    last_name: ['', [Validators.required, Validators.minLength(2)]],
    phone: ['', [Validators.required, Validators.minLength(7)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8), passwordPolicyValidator]],
    confirm_password: ['', [Validators.required]],
  });

  loading = false;
  error = '';
  showPassword = false;
  showConfirmPassword = false;

  get passwordsMatch(): boolean {
    const pwd = this.form.controls.password.value;
    const confirm = this.form.controls.confirm_password.value;
    return Boolean(confirm && pwd === confirm);
  }

  submit(): void {
    if (this.form.invalid || !this.passwordsMatch) return;
    this.loading = true;
    this.error = '';
    const raw = this.form.getRawValue();
    const payload = {
      first_name: raw.first_name,
      last_name: raw.last_name,
      email: raw.email,
      phone: raw.phone,
      password: raw.password,
    };
    this.auth.register(payload).pipe(finalize(() => { this.loading = false; })).subscribe({
      next: () => {
        if (typeof window !== 'undefined' && window.sessionStorage) {
          window.sessionStorage.setItem('fashionstore_last_email', payload.email);
        }
        this.notifications.success('Cuenta creada correctamente.');
        void this.router.navigateByUrl('/catalog').catch(() => {
          this.notifications.error('No se pudo abrir el catálogo.');
        });
      },
      error: (error: unknown) => {
        this.error = this.messageFromError(error, 'No se pudo crear la cuenta. Verifica los datos.');
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
