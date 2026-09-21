import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AdminService } from '../../core/admin/admin.service';
import { ProductSummary } from '../../core/models/admin.models';
import { AdminComponent } from './admin.component';

const emptyPage = { items: [], page: 1, page_size: 20, total: 0, total_pages: 0 };

const product = (data: Partial<ProductSummary>): ProductSummary => ({
  id: data.id ?? 1,
  category_id: data.category_id ?? 1,
  category_name: data.category_name ?? 'Abrigos',
  audience: data.audience ?? 'UNISEX',
  size_system: data.size_system ?? 'ALPHA',
  code: data.code ?? 'PRO-001',
  name: data.name ?? 'Producto',
  slug: data.slug ?? 'producto',
  price: data.price ?? 100,
  is_active: data.is_active ?? true,
  variant_count: data.variant_count ?? 0,
});

describe('AdminComponent product identifier suggestions', () => {
  let fixture: ComponentFixture<AdminComponent>;
  let component: AdminComponent;

  const createComponent = async (products: ProductSummary[] = []) => {
    const service = {
      users: vi.fn(() => of(emptyPage)),
      cities: vi.fn(() => of(emptyPage)),
      branches: vi.fn(() => of(emptyPage)),
      categories: vi.fn(() => of(emptyPage)),
      sizes: vi.fn(() => of(emptyPage)),
      colors: vi.fn(() => of(emptyPage)),
      suppliers: vi.fn(() => of(emptyPage)),
      seasons: vi.fn(() => of(emptyPage)),
      collections: vi.fn(() => of(emptyPage)),
      products: vi.fn(() => of({ ...emptyPage, items: products })),
    };

    await TestBed.configureTestingModule({
      imports: [AdminComponent],
      providers: [{ provide: AdminService, useValue: service }],
    })
      .overrideComponent(AdminComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(AdminComponent);
    component = fixture.componentInstance;
  };

  it('suggests a normalized slug and the next available product code from the name', async () => {
    await createComponent([
      product({ id: 1, code: 'CHA-001' }),
      product({ id: 2, code: 'CHA-002' }),
      product({ id: 3, code: 'ZAP-010' }),
    ]);

    component.productForm.controls.name.setValue('Cháqueta Atelier!!!');

    expect(component.productForm.controls.slug.value).toBe('chaqueta-atelier');
    expect(component.productForm.controls.code.value).toBe('CHA-003');
  });

  it('keeps manually edited code and slug values when the name changes again', async () => {
    await createComponent([product({ code: 'CHA-001' })]);

    component.productForm.controls.name.setValue('Cháqueta Atelier');
    component.productForm.controls.code.setValue('MANUAL-9');
    component.productForm.controls.slug.setValue('mi-url-manual');
    component.productForm.controls.name.setValue('Vestido de Noche');

    expect(component.productForm.controls.code.value).toBe('MANUAL-9');
    expect(component.productForm.controls.slug.value).toBe('mi-url-manual');
  });

  it('does not regenerate identifiers from name changes while editing an existing product', async () => {
    await createComponent([product({ id: 7, code: 'OLD-001', slug: 'old-product' })]);
    component.editingProduct = product({ id: 7, code: 'OLD-001', slug: 'old-product' });
    component.productForm.patchValue({ name: 'Producto actual', code: 'OLD-001', slug: 'old-product' });

    component.productForm.controls.name.setValue('Cháqueta Nueva');

    expect(component.productForm.controls.code.value).toBe('OLD-001');
    expect(component.productForm.controls.slug.value).toBe('old-product');
  });

  it('resets manual identifier tracking when a new product form starts', async () => {
    await createComponent();
    component.startProduct();
    component.productForm.controls.name.setValue('Cháqueta Atelier');
    component.productForm.controls.code.setValue('MANUAL-9');
    component.productForm.controls.slug.setValue('manual-slug');

    component.startProduct();
    component.startProduct();
    component.productForm.controls.name.setValue('Blusa Seda');

    expect(component.productForm.controls.code.value).toBe('BLU-001');
    expect(component.productForm.controls.slug.value).toBe('blusa-seda');
  });

  it('detects numeric size metadata from numeric names', async () => {
    await createComponent();

    expect(component.inferSizeMetadata('32')).toEqual({ size_type: 'NUMERIC', sort_order: 32 });
  });

  it('detects alpha size metadata and stable order for common letter names', async () => {
    await createComponent();

    expect(component.inferSizeMetadata('XL')).toEqual({ size_type: 'ALPHA', sort_order: 8 });
    expect(component.inferSizeMetadata('XXL')).toEqual({ size_type: 'ALPHA', sort_order: 9 });
  });

  it('detects one-size metadata from Spanish and English aliases', async () => {
    await createComponent();

    expect(component.inferSizeMetadata('Única')).toEqual({ size_type: 'ONE_SIZE', sort_order: 0 });
    expect(component.inferSizeMetadata('One size')).toEqual({ size_type: 'ONE_SIZE', sort_order: 0 });
    expect(component.inferSizeMetadata('OS')).toEqual({ size_type: 'ONE_SIZE', sort_order: 0 });
  });

  it('uses alpha metadata with fallback order for unknown values', async () => {
    await createComponent();

    expect(component.inferSizeMetadata('Tall')).toEqual({ size_type: 'ALPHA', sort_order: 100 });
  });
});
