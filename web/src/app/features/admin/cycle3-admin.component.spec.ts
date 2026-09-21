import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AdminService } from '../../core/admin/admin.service';
import { DashboardReport, ReportAssistantResponse } from '../../core/models/admin.models';
import { Cycle3AdminComponent } from './cycle3-admin.component';

const emptyPage = { items: [], page: 1, page_size: 100, total: 0, total_pages: 0 };

const assistantResponse: ReportAssistantResponse = {
  intent: { kind: 'sales', filters: { branch_id: 1, date_from: '2030-01-01', date_to: '2030-01-31' }, reasoning: 'Sales-focused prompt' },
  filters: { branch_id: 1, date_from: '2030-01-01', date_to: '2030-01-31' },
  data: { ventas: 8, alerta: 'Reponer Blazer Noir' },
  narrative: 'Central lidera las ventas y conviene reponer Blazer Noir.',
  provider: 'openai',
  fallback_used: false,
};

const dashboard: DashboardReport = {
  revenue: { sales_count: 8, subtotal: 1000, discount: 100, total: 900 },
  sales_by_branch: [
    { branch_id: 1, branch_name: 'Central', sales_count: 5, total: 600 },
    { branch_id: 2, branch_name: 'Norte', sales_count: 3, total: 300 },
  ],
  top_products: [
    { product_id: 1, product_name: 'Blazer Noir', units_sold: 6, revenue: 540 },
    { product_id: 2, product_name: 'Denim Atelier', units_sold: 3, revenue: 360 },
  ],
  low_stock: [{ inventory_id: 7, branch_id: 1, branch_name: 'Central', product_id: 1, product_name: 'Blazer Noir', sku: 'BLA-001-M', available_quantity: 2 }],
  reservations: [{ status: 'PENDING', count: 4 }, { status: 'READY', count: 2 }],
  sales_by_channel: [{ channel: 'POS', sales_count: 5, total: 650 }, { channel: 'ONLINE', sales_count: 3, total: 250 }],
};

describe('Cycle3AdminComponent analytics dashboard', () => {
  let fixture: ComponentFixture<Cycle3AdminComponent>;
  let component: Cycle3AdminComponent;
  let service: {
    dashboard: ReturnType<typeof vi.fn>;
    promotions: ReturnType<typeof vi.fn>;
    products: ReturnType<typeof vi.fn>;
    branches: ReturnType<typeof vi.fn>;
    createPromotion: ReturnType<typeof vi.fn>;
    setPromotionProducts: ReturnType<typeof vi.fn>;
    setPromotionActive: ReturnType<typeof vi.fn>;
    exportReport: ReturnType<typeof vi.fn>;
    reportAssistant: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    service = {
      dashboard: vi.fn(() => of(dashboard)),
      promotions: vi.fn(() => of(emptyPage)),
      products: vi.fn(() => of(emptyPage)),
      branches: vi.fn(() => of({ ...emptyPage, items: [{ id: 1, name: 'Central' }] })),
      createPromotion: vi.fn(),
      setPromotionProducts: vi.fn(),
      setPromotionActive: vi.fn(),
      exportReport: vi.fn(() => of(new Blob(['report']))),
      reportAssistant: vi.fn(() => of(assistantResponse)),
    };

    await TestBed.configureTestingModule({
      imports: [Cycle3AdminComponent],
      providers: [{ provide: AdminService, useValue: service }],
    }).compileComponents();

    fixture = TestBed.createComponent(Cycle3AdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('renders KPI cards and visual chart sections from the dashboard contract', () => {
    const text = fixture.nativeElement.textContent as string;

    expect(text).toContain('Composición de ventas');
    expect(text).toContain('Ventas por sucursal');
    expect(text).toContain('Productos más vendidos');
    expect(text).toContain('Participación de venta');
    expect(text).toContain('Estado de reservas');
    expect(text).toContain('Blazer Noir');
  });

  it('derives safe percentages and localized labels for chart rendering', () => {
    expect(component.percent(50, 200)).toBe(25);
    expect(component.percent(10, 0)).toBe(0);
    expect(component.discountRate).toBe(10);
    expect(component.revenueNetPercent).toBe(90);
    expect(component.channelLabel('POS')).toBe('Tienda');
    expect(component.reservationStatusLabel('READY')).toBe('Listas');
  });

  it('keeps report filters compatible with the existing dashboard endpoint', () => {
    component.filters = { branch_id: 1, start_date: '2030-01-01', end_date: '2030-01-31' };

    component.reloadDashboard();

    expect(service.dashboard).toHaveBeenLastCalledWith({ branch_id: 1, start_date: '2030-01-01', end_date: '2030-01-31' });
  });

  it('renders export actions and sends assistant requests with backend-compatible flat filters', () => {
    component.filters = { branch_id: 1, start_date: '2030-01-01', end_date: '2030-01-31' };
    component.assistantPrompt = 'Resumí ventas y stock';

    component.askAssistant();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;

    expect(text).toContain('Descargar Excel');
    expect(text).toContain('Descargar PDF');
    expect(text).not.toContain('Descargar PowerPoint');
    expect(service.reportAssistant).toHaveBeenCalledWith({ prompt: 'Resumí ventas y stock', date_from: '2030-01-01', date_to: '2030-01-31', branch_id: 1 });
    expect(service.reportAssistant).not.toHaveBeenCalledWith(expect.objectContaining({ filters: expect.anything() }));
    expect(text).toContain('Central lidera las ventas');
    expect(text).toContain('Proveedor principal');
    expect(text).toContain('Ventas');
  });

  it('safely renders legacy string and object assistant intent values', () => {
    expect(component.assistantIntentLabel({ kind: 'inventory', filters: {}, reasoning: 'Stock request' })).toBe('Inventario');
    expect(component.assistantIntentLabel('recommendations')).toBe('Recomendaciones');
    expect(component.assistantIntentLabel({ kind: 'custom_insight' })).toBe('custom_insight');
  });
});
