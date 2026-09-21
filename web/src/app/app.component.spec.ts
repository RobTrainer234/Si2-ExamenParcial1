import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AppComponent } from './app.component';
import { AuthService } from './core/auth/auth.service';
import { CatalogService } from './core/catalog/catalog.service';
import { CatalogNavigation } from './core/models/api.models';
import { NotificationService } from './core/notifications/notification.service';

const navigation: CatalogNavigation = {
  audiences: [
    { code: 'WOMEN', name: 'Mujer', product_count: 12 },
    { code: 'MEN', name: 'Hombre', product_count: 7 },
    { code: 'UNISEX', name: 'Unisex', product_count: 3 },
  ],
  categories: [
    { id: 1, name: 'Abrigos' },
    { id: 2, name: 'Camisas' },
  ],
  seasons: [
    {
      id: 9,
      name: 'Invierno',
      collections: [
        { id: 11, name: 'Essential', product_count: 4 },
        { id: 12, name: 'Atelier', product_count: 6 },
      ],
    },
  ],
  branches: [],
};

describe('AppComponent catalog menu', () => {
  let fixture: ComponentFixture<AppComponent>;
  let component: AppComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        { provide: CatalogService, useValue: { navigation: () => of(navigation) } },
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => false,
            currentUser: () => null,
            hasPermission: () => false,
            logout: vi.fn(),
          },
        },
        { provide: NotificationService, useValue: { messages: () => [], dismiss: vi.fn() } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('renders the catalog menu as a labelled dialog with the expected groups', () => {
    component.openMenu();
    fixture.detectChanges();

    const host: HTMLElement = fixture.nativeElement;
    const dialog = host.querySelector('[role="dialog"]');

    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(host.querySelector('#catalog-menu-title')?.textContent).toContain('Explorar FashionStore');
    expect(host.textContent).toContain('Explorar');
    expect(host.textContent).toContain('Todo el catálogo');
    expect(host.textContent).toContain('Novedades');
    expect(host.textContent).toContain('Disponible en sucursales');
    expect(host.textContent).toContain('Colecciones');
    expect(host.textContent).toContain('Categorías');
    expect(host.textContent).toContain('10 prendas');
  });

  it('closes the menu with Escape', () => {
    component.openMenu();
    fixture.detectChanges();

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    fixture.detectChanges();

    expect(component.menuOpen).toBe(false);
  });
});
