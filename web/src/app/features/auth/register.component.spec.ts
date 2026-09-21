import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { vi } from 'vitest';

import { AuthService } from '../../core/auth/auth.service';
import { NotificationService } from '../../core/notifications/notification.service';
import { RegisterComponent } from './register.component';

const validPayload = {
  first_name: 'Ana',
  last_name: 'Lopez',
  email: 'ana@example.com',
  phone: '70000000',
  password: 'Secure123!',
};

const validFormValue = {
  ...validPayload,
  confirm_password: 'Secure123!',
};

describe('RegisterComponent', () => {
  let fixture: ComponentFixture<RegisterComponent>;
  let component: RegisterComponent;
  let register$: Subject<unknown>;
  let auth: { register: ReturnType<typeof vi.fn> };
  let router: { navigateByUrl: ReturnType<typeof vi.fn> };
  let notifications: { success: ReturnType<typeof vi.fn>; error: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    register$ = new Subject<unknown>();
    auth = { register: vi.fn(() => register$.asObservable()) };
    router = { navigateByUrl: vi.fn(() => Promise.resolve(true)) };
    notifications = { success: vi.fn(), error: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: router },
        { provide: NotificationService, useValue: notifications },
      ],
    })
      .overrideComponent(RegisterComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    component.form.setValue(validFormValue);
  });

  it('clears loading and navigates after the register observable completes', () => {
    component.submit();

    expect(component.loading).toBe(true);
    expect(auth.register).toHaveBeenCalledWith(validPayload);

    register$.next({});
    register$.complete();

    expect(component.loading).toBe(false);
    expect(notifications.success).toHaveBeenCalledWith('Cuenta creada correctamente.');
    expect(router.navigateByUrl).toHaveBeenCalledWith('/catalog');
  });

  it('does not submit if passwords do not match', () => {
    component.form.patchValue({ confirm_password: 'MismatchPassword!' });
    component.submit();

    expect(component.loading).toBe(false);
    expect(auth.register).not.toHaveBeenCalled();
  });

  it('clears loading and shows backend errors when registration fails', () => {
    component.submit();

    register$.error(new HttpErrorResponse({ error: { detail: { message: 'El correo ya existe.' } }, status: 400 }));

    expect(component.loading).toBe(false);
    expect(component.error).toBe('El correo ya existe.');
    expect(notifications.error).toHaveBeenCalledWith('El correo ya existe.');
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });

  it('clears loading and shows a fallback message for unexpected errors', () => {
    component.submit();

    register$.error(new Error('offline'));

    expect(component.loading).toBe(false);
    expect(component.error).toBe('No se pudo crear la cuenta. Verifica los datos.');
    expect(notifications.error).toHaveBeenCalledWith('No se pudo crear la cuenta. Verifica los datos.');
  });
});
