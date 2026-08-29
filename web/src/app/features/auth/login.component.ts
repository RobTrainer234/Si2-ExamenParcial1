import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="auth-card">
      <p class="eyebrow">Tu armario, tu ritmo</p>
      <h1>Bienvenido de vuelta</h1>
      <p class="muted">Inicia sesión para consultar tu experiencia FashionStore.</p>
      <form [formGroup]="form" (ngSubmit)="submit()">
        <label>Correo electrónico<input type="email" formControlName="email" autocomplete="email"></label>
        <label>Contraseña<input type="password" formControlName="password" autocomplete="current-password"></label>
        @if (error) { <p class="error">{{ error }}</p> }
        <button class="button button-dark" type="submit" [disabled]="form.invalid || loading">{{ loading ? 'Ingresando...' : 'Iniciar sesión' }}</button>
      </form>
      <p class="form-footer">¿Todavía no tienes cuenta? <a routerLink="/register">Regístrate</a></p>
    </section>
  `,
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly form = inject(FormBuilder).nonNullable.group({ email: ['', [Validators.required, Validators.email]], password: ['', Validators.required] });
  loading = false;
  error = '';

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    const { email, password } = this.form.getRawValue();
    this.auth.login(email, password).subscribe({ next: () => this.router.navigateByUrl('/catalog'), error: () => { this.error = 'Correo o contraseña incorrectos.'; this.loading = false; } });
  }
}
