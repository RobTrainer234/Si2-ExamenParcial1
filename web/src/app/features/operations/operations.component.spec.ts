import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { OperationsComponent } from './operations.component';
import { AdminService } from '../../core/admin/admin.service';
import { AuthService } from '../../core/auth/auth.service';
import { QuarantineItem } from '../../core/models/admin.models';

describe('OperationsComponent quarantine inspection (CU13-8b)', () => {
  let fixture: ComponentFixture<OperationsComponent>;
  let component: OperationsComponent;
  let admin: {
    inventoryAll: ReturnType<typeof vi.fn>;
    inventoryMovements: ReturnType<typeof vi.fn>;
    quarantineList: ReturnType<typeof vi.fn>;
    inspectQuarantine: ReturnType<typeof vi.fn>;
  };
  let currentRole: string;
  let permissions: string[];

  const pendingRow: QuarantineItem = {
    id: 15,
    tenant_id: 1,
    branch_id: 3,
    inventory_id: 4,
    product_variant_id: 9,
    exchange_item_id: 2,
    quantity: 1,
    status: 'PENDING',
    inspected_by: null,
    inspection_reason: null,
    inspected_at: null,
    created_at: '2030-01-01T00:00:00Z',
  };

  function createComponent(): void {
    fixture = TestBed.createComponent(OperationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  beforeEach(async () => {
    currentRole = 'BRANCH_MANAGER';
    permissions = ['inventory.read', 'inventory.adjust'];
    admin = {
      inventoryAll: vi.fn(() => of({ items: [{ id: 4, branch_id: 3, branch_name: 'Central', product_variant_id: 9, product_id: 1, product_name: 'Camisa Atelier', sku: 'CAM-M-AZUL', size_id: 1, size_name: 'M', size_type: 'ALPHA', size_sort_order: 1, color_id: 1, color_name: 'Azul', stock_quantity: 5, reserved_quantity: 0, available_quantity: 5, available: true }], page: 1, page_size: 25, total: 1, total_pages: 1 })),
      inventoryMovements: vi.fn(() => of({ items: [], page: 1, page_size: 25, total: 0, total_pages: 1 })),
      quarantineList: vi.fn(() => of({ items: [{ ...pendingRow }], page: 1, page_size: 25, total: 1, total_pages: 1 })),
      inspectQuarantine: vi.fn((id: number, body: { decision: string; reason: string }) =>
        of({ ...pendingRow, id, status: body.decision === 'RELEASE' ? 'RELEASED' : 'REJECTED', inspected_by: 7, inspection_reason: body.reason, inspected_at: '2030-01-01T02:00:00Z' }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [OperationsComponent],
      providers: [
        { provide: AdminService, useValue: admin },
        {
          provide: AuthService,
          useValue: {
            currentUser: () => ({ id: 7, role: currentRole, permissions }),
            hasPermission: (p: string) => currentRole === 'ADMIN' || permissions.includes(p),
          },
        },
      ],
    }).compileComponents();
  });

  it('loads pending quarantine queue and allows BRANCH_MANAGER to release or reject with reason validation', () => {
    createComponent();

    expect(component.canInspectQuarantine).toBe(true);
    expect(admin.quarantineList).toHaveBeenCalledWith('PENDING', 1, 25);
    expect(component.quarantineItems.length).toBe(1);
    expect(fixture.nativeElement.textContent).toContain('Camisa Atelier');

    // Requires a reason with at least 2 characters
    component.quarantineReasons[15] = ' ';
    component.submitQuarantineDecision(component.quarantineItems[0], 'RELEASE');
    expect(admin.inspectQuarantine).not.toHaveBeenCalled();
    expect(component.quarantineMessage).toContain('motivo');

    // Valid RELEASE decision reloads inventory, quarantine, and movements
    component.quarantineReasons[15] = 'Prenda sin daños y con etiqueta';
    component.submitQuarantineDecision(component.quarantineItems[0], 'RELEASE');
    expect(admin.inspectQuarantine).toHaveBeenCalledWith(15, {
      decision: 'RELEASE',
      reason: 'Prenda sin daños y con etiqueta',
    });

    // Valid REJECT decision
    component.quarantineReasons[15] = 'Mancha irreversible en cuello';
    component.submitQuarantineDecision({ ...pendingRow }, 'REJECT');
    expect(admin.inspectQuarantine).toHaveBeenCalledWith(15, {
      decision: 'REJECT',
      reason: 'Mancha irreversible en cuello',
    });
  });

  it('blocks quarantine inspection actions for non-manager roles even with inventory permissions', () => {
    currentRole = 'CASHIER';
    permissions = ['inventory.read', 'inventory.adjust'];
    createComponent();

    expect(component.canInspectQuarantine).toBe(false);
    component.quarantineReasons[15] = 'Intento cajero';
    component.submitQuarantineDecision({ ...pendingRow }, 'RELEASE');
    expect(admin.inspectQuarantine).not.toHaveBeenCalled();
  });

  it('surfaces backend error message when inspection fails', () => {
    admin.inspectQuarantine.mockReturnValue(throwError(() => ({ error: { detail: { message: 'La cuarentena ya fue inspeccionada con otra decisión.' } } })));
    createComponent();

    component.quarantineReasons[15] = 'Reintento conflictivo';
    component.submitQuarantineDecision(component.quarantineItems[0], 'REJECT');
    expect(component.error).toContain('ya fue inspeccionada');
  });
});
