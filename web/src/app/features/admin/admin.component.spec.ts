import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { AdminService } from '../../core/admin/admin.service';
import { AdminUser, Branch, City, ProductSummary } from '../../core/models/admin.models';
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

describe('AdminComponent branch assignment', () => {
  let fixture: ComponentFixture<AdminComponent>;
  let component: AdminComponent;
  let service: Record<string, ReturnType<typeof vi.fn>>;

  const user = (data: Partial<AdminUser> = {}): AdminUser => ({
    id: data.id ?? 7,
    first_name: data.first_name ?? 'Ana',
    last_name: data.last_name ?? 'Encargada',
    email: data.email ?? 'ana@tenant.test',
    phone: data.phone ?? '70000000',
    role: data.role ?? 'BRANCH_MANAGER',
    is_active: data.is_active ?? true,
    branch_ids: data.branch_ids ?? [],
    supplier_id: data.supplier_id ?? null,
  });

  const branch = (data: Partial<Branch> = {}): Branch => ({
    id: data.id ?? 11,
    city_id: data.city_id ?? 3,
    city_name: data.city_name ?? 'Santa Cruz',
    name: data.name ?? 'Sucursal Centro',
    address: data.address ?? 'Av. Principal 123',
    phone: data.phone ?? '70000001',
    latitude: data.latitude ?? null,
    longitude: data.longitude ?? null,
    is_active: data.is_active ?? true,
  });

  const city = (data: Partial<City> = {}): City => ({
    id: data.id ?? 3,
    name: data.name ?? 'Santa Cruz',
    is_active: data.is_active ?? true,
  });

  const createComponent = async (users: AdminUser[] = [], branches: Branch[] = []) => {
    service = {
      users: vi.fn(() => of({ ...emptyPage, items: users })),
      cities: vi.fn(() => of({ ...emptyPage, items: [city()] })),
      branches: vi.fn(() => of({ ...emptyPage, items: branches })),
      categories: vi.fn(() => of(emptyPage)), sizes: vi.fn(() => of(emptyPage)), colors: vi.fn(() => of(emptyPage)),
      suppliers: vi.fn(() => of(emptyPage)), seasons: vi.fn(() => of(emptyPage)), collections: vi.fn(() => of(emptyPage)), products: vi.fn(() => of(emptyPage)),
      createBranch: vi.fn(), updateUser: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [AdminComponent],
      providers: [{ provide: AdminService, useValue: service }],
    })
      .overrideComponent(AdminComponent, { set: { template: `
        @if (section === 'users' && branchAssignableUsers.length) {
          <section class="branch-assignment-panel">
            <select [value]="branchAssignmentUserId" (change)="selectBranchAssignmentUser($any($event.target).value)">
              @for (user of branchAssignableUsers; track user.id) { <option [value]="user.id">{{ user.first_name }} {{ user.last_name }}</option> }
            </select>
            @for (branch of activeBranches; track branch.id) {
              <label><input type="checkbox" [checked]="branchAssignmentIds.includes(branch.id)" (change)="toggleBranchAssignment(branch.id)">{{ branch.name }}</label>
            }
            <button type="button" (click)="saveBranchAssignment()">Guardar asignación</button>
          </section>
        }
        @if (section === 'locations' && showBranchForm) {
          <form [formGroup]="branchForm" (ngSubmit)="createBranch()">
            <select formControlName="city_id"><option value="3">Santa Cruz</option></select>
            <input formControlName="name"><input formControlName="address"><input formControlName="phone">
            <button type="submit">Añadir sucursal</button>
          </form>
        }
        @if (error) { <p class="error admin-alert">{{ error }}</p> }
      ` } })
      .compileComponents();

    fixture = TestBed.createComponent(AdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  };

  it('shows only active tenant branches when assigning an employee', async () => {
    await createComponent([user({ branch_ids: [11] })], [branch({ id: 11, name: 'Sucursal Centro' }), branch({ id: 12, name: 'Sucursal Cerrada', is_active: false })]);

    component.section = 'users';
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.branch-assignment-panel')?.textContent).toContain('Sucursal Centro');
    expect(fixture.nativeElement.querySelector('.branch-assignment-panel')?.textContent).not.toContain('Sucursal Cerrada');
    expect(component.branchAssignableUsers).toEqual([expect.objectContaining({ id: 7 })]);
  });

  it('saves the selected employee branch assignment and updates the tenant user state', async () => {
    const updated = user({ branch_ids: [11, 13] });
    await createComponent([user({ branch_ids: [11] })], [branch({ id: 11 }), branch({ id: 13, name: 'Sucursal Norte' })]);
    service['updateUser'].mockReturnValue(of(updated));

    component.selectBranchAssignmentUser('7');
    component.toggleBranchAssignment(13);
    component.saveBranchAssignment();

    expect(service['updateUser']).toHaveBeenCalledWith(7, { branch_ids: [11, 13] });
    expect(component.users).toEqual([updated]);
    expect(component.error).toBe('');
  });

  it('shows Spanish error feedback when branch assignment cannot be saved', async () => {
    await createComponent([user()], [branch()]);
    service['updateUser'].mockReturnValue(throwError(() => new Error('network')));

    component.selectBranchAssignmentUser('7');
    component.saveBranchAssignment();

    expect(component.error).toBe('No se pudo completar la operación. Verifica los datos.');
  });

  it('saves a new branch and keeps the returned branch in the tenant branch list', async () => {
    const created = branch({ id: 21, name: 'Sucursal Norte' });
    await createComponent([], [branch()]);
    service['createBranch'].mockReturnValue(of(created));

    component.showBranchForm = true;
    component.section = 'locations';
    component.branchForm.setValue({ city_id: '3', name: 'Sucursal Norte', address: created.address, phone: created.phone });
    component.createBranch();

    expect(service['createBranch']).toHaveBeenCalledWith({ city_id: 3, name: 'Sucursal Norte', address: created.address, phone: created.phone });
    expect(component.branches).toContain(created);
    expect(component.error).toBe('');
  });

  it('shows Spanish error feedback when a new branch cannot be saved', async () => {
    await createComponent([], []);
    service['createBranch'].mockReturnValue(throwError(() => new Error('network')));

    component.branchForm.setValue({ city_id: '3', name: 'Sucursal Norte', address: 'Av. Principal 123', phone: '70000001' });
    component.createBranch();

    expect(component.error).toBe('No se pudo completar la operación. Verifica los datos.');
  });

  it('shows the exact branch quota message when BRANCH_LIMIT_EXCEEDED is returned', async () => {
    await createComponent([], []);
    service['createBranch'].mockReturnValue(throwError(() => new HttpErrorResponse({
      status: 409,
      error: {
        detail: {
          code: 'BRANCH_LIMIT_EXCEEDED',
          message: "Se ha alcanzado el límite de 2 sucursales activas permitido por el plan 'BASIC'.",
        },
      },
    })));

    component.branchForm.setValue({ city_id: '3', name: 'Sucursal Norte', address: 'Av. Principal 123', phone: '70000001' });
    component.createBranch();

    expect(component.error).toBe("Se ha alcanzado el límite de 2 sucursales activas permitido por el plan 'BASIC'.");
  });
});
