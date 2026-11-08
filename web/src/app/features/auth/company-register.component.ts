import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';
import { PasswordRequirementsComponent } from '../../core/auth/password-requirements.component';
import { passwordPolicyValidator } from '../../core/auth/password-security.helper';
import { NotificationService } from '../../core/notifications/notification.service';

@Component({
  selector: 'app-company-register',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink, PasswordRequirementsComponent],
  template: `
    <div class="auth-page-shell">
      <section class="auth-card wide company-trial-card">
        <div class="auth-brand-badge">
          <span class="auth-monogram">F</span>
          <div class="auth-brand-text">
            <strong>FashionStore Cloud</strong>
            <small>Alta Self-Service para Empresas</small>
          </div>
        </div>

        <p class="eyebrow">{{ isPaidPlan ? 'Checkout seguro con Stripe' : 'Prueba gratuita · 14 días sin tarjeta' }}</p>
        <h1>Registra tu empresa de indumentaria</h1>
        <p class="muted">
          {{ isPaidPlan ? 'Verificá el correo del administrador antes de continuar al checkout. El acceso se habilita únicamente después de confirmar el pago.' : 'Obtén acceso inmediato a tu espacio empresarial aislado con hasta 2 sucursales activas y funciones operativas completas.' }}
        </p>

        @if (selectedPlanCode === 'PROFESSIONAL') {
          <div class="selected-plan-notice pro-notice" role="status">
            <span class="material-symbols-outlined notice-icon" aria-hidden="true">workspace_premium</span>
            <div class="notice-body">
              <strong>Plan de interés: Profesional (hasta 10 sucursales + Sofía IA)</strong>
              <p>Facturación {{ selectedBilling === 'annual' ? 'anual' : 'mensual' }}. El acceso se activa únicamente después de confirmar el pago.</p>
            </div>
            <a routerLink="/" fragment="planes" class="notice-change-link">Cambiar plan</a>
          </div>
        } @else if (selectedPlanCode === 'BASIC') {
          <div class="selected-plan-notice basic-notice" role="status">
            <span class="material-symbols-outlined notice-icon" aria-hidden="true">storefront</span>
            <div class="notice-body">
              <strong>Plan de interés: Básico (hasta 2 sucursales)</strong>
              <p>Facturación {{ selectedBilling === 'annual' ? 'anual' : 'mensual' }}. El acceso se activa únicamente después de confirmar el pago.</p>
            </div>
            <a routerLink="/" fragment="planes" class="notice-change-link">Cambiar plan</a>
          </div>
        } @else if (selectedPlanCode === 'ENTERPRISE') {
          <div class="selected-plan-notice enterprise-notice" role="status">
            <span class="material-symbols-outlined notice-icon" aria-hidden="true">apartment</span>
            <div class="notice-body">
              <strong>Plan Corporativo / Cadena (>10 sucursales)</strong>
              <p>Facturación {{ selectedBilling === 'annual' ? 'anual' : 'mensual' }}. El acceso se activa únicamente después de confirmar el pago.</p>
            </div>
            <a routerLink="/" fragment="planes" class="notice-change-link">Cambiar plan</a>
          </div>
        }

        @if (!isPaidPlan) {
        <div class="trial-policy-summary" aria-label="Resumen de condiciones de prueba">
          <div>
            <span class="material-symbols-outlined" aria-hidden="true">bolt</span>
            <span>Acceso inmediato sin aprobación humana</span>
          </div>
          <div>
            <span class="material-symbols-outlined" aria-hidden="true">storefront</span>
            <span>Hasta 2 sucursales activas · Sin reportes IA en prueba</span>
          </div>
          <div>
            <span class="material-symbols-outlined" aria-hidden="true">inventory</span>
            <span>Modo consulta y exportación por 90 días al vencer</span>
          </div>
        </div>
        }

        <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
          <label class="full">
            <span class="label-text">Nombre de tu empresa o boutique</span>
            <input
              id="company-name"
              name="organization"
              formControlName="company_name"
              autocomplete="organization"
              placeholder="Ej. Atelier Solaris"
            />
          </label>

          <label>
            <span class="label-text">Nombres del administrador</span>
            <input
              id="admin-first-name"
              name="given-name"
              formControlName="first_name"
              autocomplete="given-name"
              placeholder="Valeria"
            />
          </label>

          <label>
            <span class="label-text">Apellidos</span>
            <input
              id="admin-last-name"
              name="family-name"
              formControlName="last_name"
              autocomplete="family-name"
              placeholder="Mendoza"
            />
          </label>

          <label>
            <span class="label-text">Teléfono corporativo</span>
            <input
              id="admin-phone"
              name="phone"
              formControlName="phone"
              autocomplete="tel"
              placeholder="70000000"
            />
          </label>

          <label>
            <span class="label-text">Correo del administrador</span>
            <input
              type="email"
              id="admin-email"
              name="username"
              formControlName="email"
              autocomplete="username email"
              placeholder="admin@tuempresa.bo"
              [readonly]="loading"
            />
            @if (form.controls.email.dirty && form.controls.email.touched) {
              @if (form.controls.email.valid) {
                <small class="field-feedback valid"><span class="check-dot">✔</span> {{ isPaidPlan ? 'Recibirás un código de verificación' : 'Correo válido' }}</small>
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
                id="company-password"
                name="new-password"
                formControlName="password"
                autocomplete="new-password"
                placeholder="••••••••"
              />
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
                id="company-confirm-password"
                name="confirm-password"
                formControlName="confirm_password"
                autocomplete="new-password"
                placeholder="••••••••"
              />
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

          @if (isPaidPlan && verificationStep === 'code') {
            <label class="full">
              <span class="label-text">Código de verificación</span>
              <input type="text" id="verification-code" name="verification-code" [(ngModel)]="verificationCode" [ngModelOptions]="{standalone: true}" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" placeholder="123456" />
              <small class="field-feedback">Enviamos un código de seis dígitos a {{ verifiedEmail }}.</small>
            </label>
          }

          @if (error) {
            <p class="error full" role="alert">{{ error }}</p>
          }

          <button class="button button-dark full auth-submit-btn" type="submit" [disabled]="(verificationStep === 'code' ? !isCodeValid : form.invalid || !passwordsMatch) || loading">
            {{ loading ? (verificationStep === 'code' ? 'Verificando...' : (isPaidPlan ? 'Enviando código...' : 'Configurando tu empresa...')) : (verificationStep === 'code' ? 'Verificar y continuar al checkout' : (isPaidPlan ? 'Recibir código de verificación' : 'Iniciar prueba gratuita de 14 días')) }}
          </button>

          @if (isPaidPlan && verificationStep === 'code') {
            <button type="button" class="button full" (click)="resendCode()" [disabled]="loading">Reenviar código</button>
            <button type="button" class="button full" (click)="resetVerification()" [disabled]="loading">Cambiar correo</button>
            @if (checkoutCapability) {
              <button type="button" class="button full" (click)="retryCheckout()" [disabled]="loading">Reintentar checkout</button>
            }
          }
        </form>

        <div class="company-register-links">
          <p class="form-footer">¿Ya tienes cuenta de equipo? <a routerLink="/login">Inicia sesión</a></p>
          <p class="form-footer buyer-switch">
            ¿Solo buscas comprar prendas en la tienda? <a routerLink="/register">Crea una cuenta de cliente</a>
          </p>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .company-trial-card {
      max-width: 660px;
    }
    .trial-policy-summary {
      background: #faf7f2;
      border: 1px solid var(--line);
      border-radius: 12px;
      display: grid;
      gap: 8px;
      margin: 0 0 22px;
      padding: 14px 16px;
      text-align: left;
    }
    .trial-policy-summary div {
      align-items: center;
      color: var(--ink);
      display: flex;
      font-size: 0.78rem;
      gap: 8px;
    }
    .trial-policy-summary .material-symbols-outlined {
      color: var(--accent);
      font-size: 18px;
    }
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
    }
    .company-register-links {
      border-top: 1px solid var(--line);
      margin-top: 18px;
      padding-top: 12px;
    }
    .buyer-switch {
      margin-top: 6px;
      font-size: 0.76rem;
    }

    /* SELECTED PLAN NOTICE */
    .selected-plan-notice {
      align-items: center;
      border-radius: 12px;
      display: flex;
      gap: 14px;
      margin: 0 0 20px;
      padding: 14px 18px;
      text-align: left;
    }
    .selected-plan-notice.pro-notice {
      background: #211f1d;
      border: 1px solid #383531;
      color: #f7efe5;
    }
    .selected-plan-notice.pro-notice .notice-icon {
      color: #d9b69f;
    }
    .selected-plan-notice.pro-notice p {
      color: #d8d2ca;
    }
    .selected-plan-notice.basic-notice {
      background: #f7f4ee;
      border: 1px solid var(--line);
      color: var(--ink);
    }
    .selected-plan-notice.basic-notice .notice-icon {
      color: var(--accent);
    }
    .selected-plan-notice.enterprise-notice {
      background: #1e241c;
      border: 1px solid #2f382a;
      color: #e8f0e5;
    }
    .selected-plan-notice.enterprise-notice .notice-icon {
      color: #86efac;
    }
    .notice-icon {
      font-size: 28px;
      flex-shrink: 0;
    }
    .notice-body {
      flex: 1;
    }
    .notice-body strong {
      display: block;
      font-size: 0.92rem;
      margin-bottom: 2px;
    }
    .notice-body p {
      font-size: 0.8rem;
      line-height: 1.45;
      margin: 0;
    }
    .notice-change-link {
      color: inherit;
      flex-shrink: 0;
      font-size: 0.78rem;
      font-weight: 600;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
  `],
})
export class CompanyRegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly notifications = inject(NotificationService);

  readonly selectedPlanCode = (this.route.snapshot.queryParamMap.get('plan') || '').toUpperCase();
  readonly selectedBilling = this.route.snapshot.queryParamMap.get('billing') || 'monthly';
  readonly isPaidPlan = Boolean(this.selectedPlanCode && this.selectedPlanCode !== 'TRIAL');

  readonly form = inject(FormBuilder).nonNullable.group({
    company_name: ['', [Validators.required, Validators.minLength(2)]],
    first_name: ['', [Validators.required, Validators.minLength(2)]],
    last_name: ['', [Validators.required, Validators.minLength(2)]],
    phone: ['', [Validators.required, Validators.minLength(7)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8), passwordPolicyValidator]],
    confirm_password: ['', [Validators.required]],
  });

  loading = false;
  error = '';
  verificationStep: 'details' | 'code' = 'details';
  verificationCode = '';
  verifiedEmail = '';
  checkoutCapability: string | null = null;
  private registrationPayload: {
    company_name: string; first_name: string; last_name: string; email: string; phone: string; password: string;
  } | null = null;
  showPassword = false;
  showConfirmPassword = false;
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    this.form.controls.email.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((email) => {
        const normalizedEmail = email.trim().toLowerCase();
        if (this.verificationStep === 'code' && this.verifiedEmail && normalizedEmail !== this.verifiedEmail.trim().toLowerCase()) {
          this.resetVerification();
        }
      });
  }

  get isCodeValid(): boolean {
    return /^\d{6}$/.test(this.verificationCode);
  }

  get passwordsMatch(): boolean {
    const pwd = this.form.controls.password.value;
    const confirm = this.form.controls.confirm_password.value;
    return Boolean(confirm && pwd === confirm);
  }

  submit(): void {
    if (this.isPaidPlan && this.verificationStep === 'code') {
      const currentEmail = this.form.controls.email.value.trim();
      if (currentEmail !== this.verifiedEmail) {
        this.resetVerification();
        this.form.controls.email.setValue(currentEmail);
        this.registrationPayload = { ...this.form.getRawValue(), company_name: this.form.controls.company_name.value.trim(), first_name: this.form.controls.first_name.value.trim(), last_name: this.form.controls.last_name.value.trim(), email: currentEmail, phone: this.form.controls.phone.value.trim() };
        this.startVerification();
        return;
      }
      if (this.checkoutCapability) this.createCheckout();
      else this.verifyCode();
      return;
    }
    if (this.form.invalid || !this.passwordsMatch) return;
    this.error = '';
    if (this.isPaidPlan && !['BASIC', 'PROFESSIONAL', 'ENTERPRISE'].includes(this.selectedPlanCode)) {
      this.error = 'El plan seleccionado no está disponible. Volvé a la página de planes e intentá nuevamente.';
      this.notifications.error(this.error);
      return;
    }
    if (this.isPaidPlan && !['monthly', 'annual'].includes(this.selectedBilling)) {
      this.error = 'El intervalo de facturación seleccionado no es válido.';
      this.notifications.error(this.error);
      return;
    }
    const raw = this.form.getRawValue();
    this.registrationPayload = {
      company_name: raw.company_name.trim(), first_name: raw.first_name.trim(), last_name: raw.last_name.trim(),
      email: raw.email.trim(), phone: raw.phone.trim(), password: raw.password,
    };
    if (this.isPaidPlan) {
      this.startVerification();
      return;
    }
    this.loading = true;
    this.auth.registerCompanyTrial(this.registrationPayload).pipe(finalize(() => { this.loading = false; })).subscribe({
      next: () => {
        this.notifications.success(`¡Bienvenido a FashionStore! Tu prueba de 14 días para ${this.registrationPayload?.company_name} está activa.`);
        void this.router.navigateByUrl('/admin');
      },
      error: (error: unknown) => this.showError(error, 'No se pudo registrar la empresa. Verifica los datos ingresados.'),
    });
  }

  startVerification(): void {
    const email = this.registrationPayload?.email ?? this.form.controls.email.value.trim();
    this.loading = true;
    this.auth.startEmailVerification(email).pipe(finalize(() => { this.loading = false; })).subscribe({
      next: () => { this.verifiedEmail = email; this.verificationStep = 'code'; this.verificationCode = ''; },
      error: (error: unknown) => this.showError(error, 'No se pudo enviar el código de verificación.'),
    });
  }

  resendCode(): void {
    this.resetVerification();
    this.startVerification();
  }

  verifyCode(): void {
    if (!this.isCodeValid || !this.verifiedEmail) return;
    this.loading = true;
    this.auth.verifyEmail(this.verifiedEmail, this.verificationCode).pipe(finalize(() => { this.loading = false; })).subscribe({
      next: (response) => {
        if (!response.verified) { this.showError(null, 'No se pudo verificar el código.'); return; }
        this.checkoutCapability = response.checkout_capability;
        this.createCheckout();
      },
      error: (error: unknown) => this.showError(error, 'El código no es válido o ya venció.'),
    });
  }

  retryCheckout(): void {
    if (this.checkoutCapability) this.createCheckout();
  }

  resetVerification(): void {
    this.verificationStep = 'details';
    this.verificationCode = '';
    this.verifiedEmail = '';
    this.checkoutCapability = null;
    this.registrationPayload = null;
    this.error = '';
  }

  private createCheckout(): void {
    if (!this.registrationPayload || !this.checkoutCapability) return;
    this.loading = true;
    this.auth.registerPaidCheckout({ ...this.registrationPayload, plan_code: this.selectedPlanCode, billing_interval: this.selectedBilling as 'monthly' | 'annual', checkout_capability: this.checkoutCapability })
      .pipe(finalize(() => { this.loading = false; }))
      .subscribe({
        next: (response) => window.location.assign(response.session_url),
        error: (error: unknown) => this.showError(error, 'No se pudo crear el checkout. Podés reintentarlo sin solicitar otro código.'),
      });
  }

  private showError(error: unknown, fallback: string): void {
    this.error = this.messageFromError(error, fallback);
    this.notifications.error(this.error);
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
