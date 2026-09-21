import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { CatalogService } from '../../core/catalog/catalog.service';
import { CatalogItem } from '../../core/models/api.models';
import { CatalogComponent } from './catalog.component';

const product = (id: number, name: string, imageUrl: string | null = null): CatalogItem => ({
  id,
  category_id: 1,
  category_name: 'Abrigos',
  audience: 'WOMEN',
  code: `PRO-${id}`,
  name,
  slug: name.toLowerCase().replaceAll(' ', '-'),
  price: 120 + id,
  image_url: imageUrl,
});

const filters = {
  categories: [{ id: 1, name: 'Abrigos' }],
  sizes: [{ id: 2, name: 'M' }],
  colors: [{ id: 3, name: 'Negro', hex_code: '#111111' }],
  branches: [{ id: 4, name: 'Central' }],
  audiences: [{ code: 'WOMEN' as const, name: 'Mujer', product_count: 2 }],
};

describe('CatalogComponent collection browser', () => {
  let fixture: ComponentFixture<CatalogComponent>;
  let catalogService: { filters: ReturnType<typeof vi.fn>; list: ReturnType<typeof vi.fn>; navigation: ReturnType<typeof vi.fn> };

  const navigation = {
    audiences: [{ code: 'WOMEN' as const, name: 'Mujer', product_count: 2 }],
    categories: filters.categories,
    seasons: [{ id: 5, name: 'Verano 2026', collections: [{ id: 8, name: 'Resort Urbano', product_count: 2 }] }],
    branches: filters.branches,
  };

  const createComponent = async (items: CatalogItem[] = [product(1, 'Abrigo Alba'), product(2, 'Camisa Noche')], navigationFails = false) => {
    catalogService = {
      filters: vi.fn(() => of(filters)),
      list: vi.fn(() => of({ items, page: 1, page_size: 12, total: items.length, total_pages: 1 })),
      navigation: vi.fn(() => navigationFails ? throwError(() => new Error('navigation unavailable')) : of(navigation)),
    };

    await TestBed.configureTestingModule({
      imports: [CatalogComponent],
      providers: [
        provideRouter([]),
        { provide: CatalogService, useValue: catalogService },
        { provide: ActivatedRoute, useValue: { queryParamMap: of(convertToParamMap({ audience: 'WOMEN', season_id: '5', collection_id: '8' })) } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogComponent);
    fixture.detectChanges();
  };

  it('renders navigation names for the active collection context instead of raw query ids', async () => {
    await createComponent();

    const host: HTMLElement = fixture.nativeElement;

    expect(catalogService.navigation).toHaveBeenCalled();
    expect(host.textContent).toContain('FashionStore / Catálogo / Resort Urbano');
    expect(host.textContent).toContain('Prendas para Mujer');
    expect(host.textContent).toContain('Temporada: Verano 2026');
    expect(host.textContent).toContain('Colección: Resort Urbano');
    expect(host.textContent).toContain('Público: Mujer');
    expect(host.textContent).not.toContain('Colección 8');
    expect(host.textContent).not.toContain('Temporada 5');
  });

  it('falls back to neutral collection labels when navigation is unavailable', async () => {
    await createComponent([product(1, 'Abrigo Alba')], true);

    const host: HTMLElement = fixture.nativeElement;

    expect(host.textContent).toContain('FashionStore / Catálogo / Colección seleccionada');
    expect(host.textContent).toContain('Temporada seleccionada');
    expect(host.textContent).toContain('Colección seleccionada');
    expect(host.textContent).toContain('Público: Mujer');
    expect(host.textContent).not.toContain('Colección 8');
    expect(host.textContent).not.toContain('Temporada 5');
  });

  it('uses one ordered product grid without featured duplication or editorial labels', async () => {
    await createComponent([product(10, 'Primera Prenda'), product(11, 'Segunda Prenda'), product(12, 'Tercera Prenda')]);

    const host: HTMLElement = fixture.nativeElement;
    const cards = Array.from(host.querySelectorAll('a.product-card'));

    expect(cards).toHaveLength(3);
    expect(cards.map((card) => card.textContent?.trim())).toEqual([
      expect.stringContaining('Primera Prenda'),
      expect.stringContaining('Segunda Prenda'),
      expect.stringContaining('Tercera Prenda'),
    ]);
    expect(host.querySelector('.featured-products')).toBeNull();
    expect(host.querySelector('.featured-grid')).toBeNull();
    expect(host.textContent).not.toContain('Piezas destacadas');
    expect(host.textContent).not.toContain('Selección principal');
  });


  it('renders the restored toolbar, filter ribbon, active chips, and ordered grid structure', async () => {
    await createComponent([product(20, 'Vestido Lino', '/assets/vestido.jpg')]);

    const host: HTMLElement = fixture.nativeElement;

    expect(host.querySelector('.collection-hero-image')).toBeNull();
    expect(host.querySelector('.catalog-sidebar')).toBeNull();
    expect(host.querySelector('.catalog-toolbar')?.textContent).toContain('Categoría');
    expect(host.querySelector('.catalog-toolbar')?.textContent).toContain('Sucursal');
    expect(host.querySelector('.catalog-toolbar')?.textContent).toContain('Ordenar por');
    expect(host.querySelector('.catalog-toolbar .button')?.textContent).toContain('Aplicar filtros');
    expect(host.querySelector('.catalog-filters')?.textContent).toContain('Categorías');
    expect(host.querySelector('.catalog-filters')?.textContent).toContain('Tallas');
    expect(host.querySelector('.catalog-filters')?.textContent).toContain('Colores');
    expect(host.querySelectorAll('.product-grid .product-card')).toHaveLength(1);
  });

  it('keeps search, category, branch, and sort controls in the toolbar query', async () => {
    await createComponent();
    const component = fixture.componentInstance;

    component.filters.patchValue({ q: 'abrigo', category_id: '1', branch_id: '4', sort: 'newest' });
    component.search();

    expect(catalogService.list).toHaveBeenLastCalledWith(expect.objectContaining({
      q: 'abrigo',
      category_id: 1,
      branch_id: 4,
      sort: 'newest',
    }));
  });
});
