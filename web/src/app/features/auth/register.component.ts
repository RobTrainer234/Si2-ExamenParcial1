import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="auth-card wide">
      <p class="eyebrow">Una nueva forma de elegir</p>
      <h1>Crea tu cuenta</h1>
      <p class="muted">Guarda tus preferencias y consulta prendas disponibles cerca de ti.</p>
      <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
        <label>Nombres<input formControlName="first_name" autocomplete="given-name"></label>
        <label>Apellidos<input formControlName="last_name" autocomplete="family-name"></label>
        <label>Correo electrónico<input type="email" formControlName="email" autocomplete="email"></label>
        <label>Teléfono<input formControlName="phone" autocomplete="tel"></label>
        <label class="full">Contraseña<input type="password" formControlName="password" autocomplete="new-password"><small>Usa mayúsculas, minúsculas, números y un carácter especial.</small></label>
        @if (error) { <p class="error full">{{ error }}</p> }
        <button class="button button-dark full" type="submit" [disabled]="form.invalid || loading">{{ loading ? 'Creando cuenta...' : 'Crear cuenta' }}</button>
      </form>
      <p class="form-footer">¿Ya tienes cuenta? <a routerLink="/login">Inicia sesión</a></p>
    </section>
  `,
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly form = inject(FormBuilder).nonNullable.group({ first_name: ['', [Validators.required, Validators.minLength(2)]], last_name: ['', [Validators.required, Validators.minLength(2)]], email: ['', [Validators.required, Validators.email]], phone: ['', [Validators.required, Validators.minLength(7)]], password: ['', [Validators.required, Validators.minLength(8)]] });
  loading = false;
  error = '';

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    this.auth.register(this.form.getRawValue()).subscribe({ next: () => this.router.navigateByUrl('/catalog'), error: () => { this.error = 'No se pudo crear la cuenta. Verifica los datos.'; this.loading = false; } });
  }
}
