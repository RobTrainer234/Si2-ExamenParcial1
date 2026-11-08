import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { LandingComponent } from './landing.component';

describe('LandingComponent', () => {
  let fixture: ComponentFixture<LandingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LandingComponent],
      providers: [provideRouter([]), provideHttpClient()],
    }).compileComponents();

    fixture = TestBed.createComponent(LandingComponent);
    fixture.detectChanges();
  });

  it('explains FashionStore for clothing businesses with verified capabilities and official plans without inventing prices', () => {
    const host: HTMLElement = fixture.nativeElement;

    expect(host.querySelector('h1')?.textContent).toContain('FashionStore');
    expect(host.textContent).toContain('Catálogo');
    expect(host.textContent).toContain('Operaciones');
    expect(host.textContent).toContain('Modo offline');
    expect(host.textContent).toContain('Básico');
    expect(host.textContent).toContain('Profesional');
    expect(host.textContent).toContain('2 sucursales activas');
    expect(host.textContent).toContain('10 sucursales activas');
    expect(host.textContent).not.toContain('USD');
    expect(host.textContent).toContain('Bs');
    expect(host.textContent).toContain('199');
    expect(host.textContent).toContain('499');

    // Toggle to annual billing
    fixture.componentInstance.billingPeriod = 'annual';
    fixture.detectChanges();
    expect(host.textContent).toContain('1990');
    expect(host.textContent).toContain('4990');
    expect(host.textContent).toContain('Ahorra 2 meses');
    expect(host.textContent).toContain('Ahorras Bs 398');
    expect(host.textContent).toContain('Ahorras Bs 998');
  });

  it('distinguishes paid plans from the separate free-trial offer', () => {
    const host: HTMLElement = fixture.nativeElement;
    const paidPlanFootnotes = Array.from(host.querySelectorAll('.plan-footer .plan-footnote'))
      .map((element) => element.textContent?.trim() ?? '')
      .join(' ');

    expect(paidPlanFootnotes).not.toContain('14 días de prueba');
    expect(paidPlanFootnotes).toContain('El acceso se habilita después de confirmar el pago.');
    expect(host.textContent).toContain('14 días de prueba');
  });

  it('enables the self-service company trial CTA to /register-company alongside catalog and login navigation', () => {
    const host: HTMLElement = fixture.nativeElement;
    const catalogLink = host.querySelector('a[href="/catalog"]');
    const loginLink = host.querySelector('a[href="/login"]');
    const companyTrialLink = host.querySelector('a[href^="/register-company"]');

    expect(catalogLink).not.toBeNull();
    expect(loginLink).not.toBeNull();
    expect(companyTrialLink).not.toBeNull();
    expect(companyTrialLink?.textContent).toMatch(/prueba|empresa/i);
  });

  it('renders the detailed feature comparison matrix and allows toggling it', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.textContent).toContain('Matriz comparativa de capacidades');
    expect(host.querySelector('.comparison-table')).not.toBeNull();

    // Toggle comparison visibility off
    fixture.componentInstance.showComparison = false;
    fixture.detectChanges();
    expect(host.querySelector('.comparison-table')).toBeNull();

    // Toggle back on
    fixture.componentInstance.showComparison = true;
    fixture.detectChanges();
    expect(host.querySelector('.comparison-table')).not.toBeNull();
  });

  it('renders interactive pricing FAQs and toggles answers', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.textContent).toContain('Preguntas frecuentes sobre planes y facturación');
    expect(host.textContent).toContain('¿Tengo que ingresar tarjeta de crédito');

    // First FAQ is open by default
    expect(fixture.componentInstance.openFaqIndex).toBe(0);
    expect(host.textContent).toContain('100% gratuita y no solicita datos de tarjeta');

    // Toggle off
    fixture.componentInstance.toggleFaq(0);
    fixture.detectChanges();
    expect(fixture.componentInstance.openFaqIndex).toBeNull();
  });
});

