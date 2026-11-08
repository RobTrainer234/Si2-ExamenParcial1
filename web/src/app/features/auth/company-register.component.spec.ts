import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { NEVER, of } from 'rxjs';
import { vi } from 'vitest';

import { AuthService } from '../../core/auth/auth.service';
import { NotificationService } from '../../core/notifications/notification.service';
import { CompanyRegisterComponent } from './company-register.component';

describe('CompanyRegisterComponent paid registration', () => {
  let fixture: ComponentFixture<CompanyRegisterComponent>;
  let component: CompanyRegisterComponent;
  let auth: {
    registerCompanyTrial: ReturnType<typeof vi.fn>;
    startEmailVerification: ReturnType<typeof vi.fn>;
    verifyEmail: ReturnType<typeof vi.fn>;
    registerPaidCheckout: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    auth = {
      registerCompanyTrial: vi.fn(() => of({})),
      startEmailVerification: vi.fn(() => of({ accepted: true, email_sent: true })),
      verifyEmail: vi.fn(() => of({ verified: true, checkout_capability: 'capability-token' })),
      registerPaidCheckout: vi.fn(() => NEVER),
    };
    await TestBed.configureTestingModule({
      imports: [CompanyRegisterComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: new Map([['plan', 'BASIC'], ['billing', 'annual']]) } } },
        { provide: Router, useValue: { navigateByUrl: vi.fn() } },
        { provide: NotificationService, useValue: { success: vi.fn(), error: vi.fn() } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(CompanyRegisterComponent);
    component = fixture.componentInstance;
    component.form.setValue({
      company_name: 'Acme', first_name: 'Ada', last_name: 'Lovelace', phone: '70000000',
      email: 'ada@example.com', password: 'StrongPass1!', confirm_password: 'StrongPass1!',
    });
  });

  it('sends a verification code before creating hosted checkout', () => {
    component.submit();

    expect(auth.startEmailVerification).toHaveBeenCalledWith('ada@example.com');
    expect(auth.registerPaidCheckout).not.toHaveBeenCalled();
    expect(component.verificationStep).toBe('code');
  });

  it('accepts exactly six digits, retains plan and billing, and propagates capability to checkout', () => {
    component.submit();
    component.verificationCode = '123456';
    component.verifyCode();

    expect(auth.verifyEmail).toHaveBeenCalledWith('ada@example.com', '123456');
    expect(auth.registerPaidCheckout).toHaveBeenCalledWith(expect.objectContaining({
      company_name: 'Acme', plan_code: 'BASIC', billing_interval: 'annual', checkout_capability: 'capability-token',
    }));
  });

  it('retains capability for a checkout retry without requesting another code', () => {
    component.submit();
    component.verificationCode = '123456';
    auth.registerPaidCheckout.mockReset();
    auth.registerPaidCheckout.mockReturnValueOnce(NEVER);
    component.verifyCode();
    component.retryCheckout();

    expect(auth.startEmailVerification).toHaveBeenCalledTimes(1);
    expect(auth.verifyEmail).toHaveBeenCalledTimes(1);
    expect(auth.registerPaidCheckout).toHaveBeenCalledTimes(2);
  });

  it('immediately resets verification when the email changes and supports resending', () => {
    component.submit();
    expect(component.verificationStep).toBe('code');
    component.verificationCode = '123456';
    component.checkoutCapability = 'capability-token';
    component.form.controls.email.setValue('new@example.com');

    expect(component.verificationStep).toBe('details');
    expect(component.verificationCode).toBe('');
    expect(component.checkoutCapability).toBeNull();

    component.resendCode();
    expect(auth.startEmailVerification).toHaveBeenLastCalledWith('new@example.com');
  });

  it('keeps free trial registration unchanged and never calls verification APIs', async () => {
    const freeRoute = { snapshot: { queryParamMap: new Map([['plan', 'TRIAL']]) } };
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [CompanyRegisterComponent],
      providers: [
        { provide: AuthService, useValue: auth }, { provide: ActivatedRoute, useValue: freeRoute },
        { provide: Router, useValue: { navigateByUrl: vi.fn() } },
        { provide: NotificationService, useValue: { success: vi.fn(), error: vi.fn() } },
      ],
    }).compileComponents();
    const freeComponent = TestBed.createComponent(CompanyRegisterComponent).componentInstance;
    freeComponent.form.setValue({
      company_name: 'Acme', first_name: 'Ada', last_name: 'Lovelace', phone: '70000000',
      email: 'ada@example.com', password: 'StrongPass1!', confirm_password: 'StrongPass1!',
    });
    freeComponent.submit();

    expect(auth.registerCompanyTrial).toHaveBeenCalled();
    expect(auth.startEmailVerification).not.toHaveBeenCalled();
    expect(auth.verifyEmail).not.toHaveBeenCalled();
  });

  it('recognizes a paid plan from the landing query string', () => {
    expect(component.isPaidPlan).toBe(true);
    expect(component.selectedBilling).toBe('annual');
  });
});
