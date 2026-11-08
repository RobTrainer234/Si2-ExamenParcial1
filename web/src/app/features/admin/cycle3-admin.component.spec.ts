import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { AdminService } from '../../core/admin/admin.service';
import {
  CustomerSegmentationResponse,
  DashboardReport,
  DemandForecastResponse,
  MLTrainingResponse,
  ReportAssistantResponse,
} from '../../core/models/admin.models';
import { Cycle3AdminComponent } from './cycle3-admin.component';

const emptyPage = { items: [], page: 1, page_size: 100, total: 0, total_pages: 0 };

const assistantResponse: ReportAssistantResponse = {
  intent: {
    kind: 'revenue_by_category',
    filters: { branch_id: 1, date_from: '2030-01-01', date_to: '2030-01-31' },
    chart_type: 'pie',
    reasoning: 'Category revenue prompt',
  },
  filters: { branch_id: 1, date_from: '2030-01-01', date_to: '2030-01-31' },
  data: [
    { category_id: 1, category_name: 'Vestidos Fiesta', units_sold: 15, total_revenue: 3500 },
    { category_id: 2, category_name: 'Pantalones Lino', units_sold: 10, total_revenue: 1800 },
  ],
  narrative: 'La categoría Vestidos Fiesta lidera la facturación del período.',
  provider: 'gemini',
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

const mockDemandForecast: DemandForecastResponse = {
  target: 'ventas_semanales',
  branch_id: 1,
  branch_name: 'Central',
  metrics: {
    model_name: 'Ridge Regression',
    model_type: 'supervised',
    mae: 2.5,
    rmse: 3.1,
    r2_score: 0.88,
    samples_count: 60,
    real_samples_count: 45,
    synthetic_samples_count: 15,
    trained_at: '2026-10-24T03:00:00Z',
  },
  forecast: [
    { period: '2026-W44', predicted_units: 45, predicted_revenue: 5400, confidence_lower: 38, confidence_upper: 52 },
    { period: '2026-W45', predicted_units: 50, predicted_revenue: 6000, confidence_lower: 42, confidence_upper: 58 },
  ],
  narrative: 'Proyección supervisada con tendencia creciente del 11%.',
};

const mockCustomerSegments: CustomerSegmentationResponse = {
  algorithm: 'K-Means RFM',
  clusters_count: 4,
  silhouette_score: 0.42,
  inertia: 120.5,
  metrics: {
    model_name: 'K-Means RFM',
    model_type: 'unsupervised',
    silhouette_score: 0.42,
    inertia: 120.5,
    samples_count: 100,
    real_samples_count: 75,
    synthetic_samples_count: 25,
    trained_at: '2026-10-24T03:00:00Z',
  },
  segments: [
    {
      segment_id: 0,
      name: 'Clientes VIP / Champions',
      description: 'Clientes de alto valor y compra frecuente.',
      customer_count: 25,
      percentage: 25.0,
      avg_recency_days: 5,
      avg_frequency: 12,
      avg_monetary: 4500,
      suggested_action: 'Programa de lealtad exclusiva',
    },
    {
      segment_id: 1,
      name: 'Clientes Leales',
      description: 'Clientes recurrentes con potencial de crecimiento.',
      customer_count: 35,
      percentage: 35.0,
      avg_recency_days: 15,
      avg_frequency: 6,
      avg_monetary: 1800,
      suggested_action: 'Campañas de cross-selling',
    },
  ],
  narrative: 'Segmentación completada con 4 perfiles estratégicos.',
  anomalies: [{ recency_days: 2, frequency: 1, monetary: 120, anomaly_score: 0.91, data_source: 'synthetic' }],
  anomalies_count: 1,
};

const mockTrainingResponse: MLTrainingResponse = {
  status: 'SUCCESS',
  message: 'Modelos de Machine Learning reentrenados exitosamente.',
  supervised_metrics: {
    model_name: 'Ridge Regression',
    model_type: 'supervised',
    mae: 2.4,
    rmse: 3.0,
    r2_score: 0.89,
    samples_count: 60,
    trained_at: '2026-10-24T03:00:00Z',
  },
  unsupervised_metrics: {
    model_name: 'K-Means RFM',
    model_type: 'unsupervised',
    silhouette_score: 0.44,
    inertia: 115.0,
    samples_count: 100,
    trained_at: '2026-10-24T03:00:00Z',
  },
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
    exportAssistantReport: ReturnType<typeof vi.fn>;
    getDemandForecast: ReturnType<typeof vi.fn>;
    getCustomerSegments: ReturnType<typeof vi.fn>;
    trainMLModels: ReturnType<typeof vi.fn>;
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
      exportAssistantReport: vi.fn(() => of(new Blob(['assistant-report']))),
      getDemandForecast: vi.fn(() => of(mockDemandForecast)),
      getCustomerSegments: vi.fn(() => of(mockCustomerSegments)),
      trainMLModels: vi.fn(() => of(mockTrainingResponse)),
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
    expect(text).toContain('La categoría Vestidos Fiesta lidera la facturación');
    expect(text).toContain('Exportar reporte IA a Excel');
    expect(text).toContain('Exportar reporte IA a PDF');
  });

  it('safely renders legacy string and object assistant intent values', () => {
    expect(component.assistantIntentLabel({ kind: 'inventory', filters: {}, reasoning: 'Stock request' })).toBe('Inventario');
    expect(component.assistantIntentLabel('recommendations')).toBe('Recomendaciones');
    expect(component.assistantIntentLabel('revenue_by_category')).toBe('Ingresos por categoría');
    expect(component.assistantIntentLabel({ kind: 'custom_insight' })).toBe('custom_insight');
  });

  it('renders bar values proportionally, sorted by magnitude, and exposes rows accessibly', () => {
    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'bar' },
      data: [
        { category_name: 'Pequeña', total_revenue: 10 },
        { category_name: 'Grande', total_revenue: 40 },
      ],
    }));

    component.askAssistant();
    fixture.detectChanges();

    const rows = [...fixture.nativeElement.querySelectorAll('.bar-breakdown-item')] as HTMLElement[];
    expect(rows.map((row) => row.textContent?.trim())).toEqual([
      expect.stringContaining('Grande'),
      expect.stringContaining('Pequeña'),
    ]);
    expect((rows[0].querySelector('.bar-fill-line') as HTMLElement).style.width).toBe('100%');
    expect((rows[1].querySelector('.bar-fill-line') as HTMLElement).style.width).toBe('25%');
    expect(rows[0].querySelector('.bar-fill-line')?.getAttribute('aria-label')).toContain('40');
    expect(rows[0].getAttribute('tabindex')).toBe('0');
  });

  it('renders pie proportions and a textual accessible fallback from actual values', () => {
    component.askAssistant();
    fixture.detectChanges();

    const pie = fixture.nativeElement.querySelector('.copilot-pie-chart') as HTMLElement;
    expect(pie).toBeTruthy();
    expect(pie.getAttribute('role')).toBe('img');
    expect(pie.getAttribute('aria-label')).toContain('Vestidos Fiesta');
    expect(pie.style.backgroundImage).toContain('conic-gradient');
    expect(fixture.nativeElement.querySelectorAll('.pie-breakdown-row').length).toBe(2);
    expect(fixture.nativeElement.querySelector('.pie-breakdown-row')?.getAttribute('tabindex')).toBe('0');
  });

  it('supports line and KPI chart types with readable values', () => {
    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'line' },
      data: [
        { date: '2030-01-01', value: 12 },
        { date: '2030-01-02', value: 18 },
      ],
    }));
    component.askAssistant();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.copilot-line-chart')).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('2030-01-01');
    expect(fixture.nativeElement.textContent).toContain('18');

    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'kpi' },
      data: { revenue: 900, sales_count: 8 },
    }));
    component.askAssistant();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('.copilot-kpi-card').length).toBe(2);
    expect(fixture.nativeElement.textContent).toContain('900');
  });

  it('gives every assistant chart visible geometry and responsive layout styles', () => {
    component.askAssistant();
    fixture.detectChanges();
    const pie = fixture.nativeElement.querySelector('.copilot-pie-chart') as HTMLElement;
    expect(pie.getAttribute('style')).toMatch(/width:\s*min\(/);
    expect(pie.getAttribute('style')).toContain('aspect-ratio');

    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'bar' },
      data: [{ category_name: 'A', total_revenue: 10 }],
    }));
    component.askAssistant();
    fixture.detectChanges();
    const bar = fixture.nativeElement.querySelector('.copilot-bar-breakdown') as HTMLElement;
    expect(bar.getAttribute('style')).toContain('width: 100%');
    expect(bar.getAttribute('style')).toContain('min-width: 0');

    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'line' },
      data: [{ date: '2030-01-01', value: 12 }, { date: '2030-01-02', value: 18 }],
    }));
    component.askAssistant();
    fixture.detectChanges();
    const line = fixture.nativeElement.querySelector('.copilot-line-chart') as HTMLElement;
    const path = fixture.nativeElement.querySelector('.copilot-line-path') as SVGPathElement;
    expect(line.getAttribute('style')).toContain('min-height');
    expect(path).toBeTruthy();
    expect(path.getAttribute('d')).toMatch(/^M\s*\d/);
    expect(path.getAttribute('d')).toContain('L');

    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'kpi' },
      data: { revenue: 900, sales_count: 8 },
    }));
    component.askAssistant();
    fixture.detectChanges();
    const kpiGrid = fixture.nativeElement.querySelector('.copilot-kpi-grid') as HTMLElement;
    expect(kpiGrid.getAttribute('style')).toContain('display: grid');
    expect(kpiGrid.getAttribute('style')).toContain('minmax');
  });

  it('falls back to an accessible table for empty, malformed, or unsupported report data', () => {
    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'line' },
      data: [],
    }));
    component.askAssistant();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.copilot-fallback-table')).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('No hay datos suficientes');

    service.reportAssistant.mockReturnValueOnce(of({
      ...assistantResponse,
      intent: { ...assistantResponse.intent, chart_type: 'table' },
      data: [{ unexpected: { nested: true } }],
    }));
    component.askAssistant();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.copilot-fallback-table')).toBeTruthy();
  });

  it('renders ML predictive dashboard with demand forecast and customer segments', () => {
    const text = fixture.nativeElement.textContent as string;

    expect(text).toContain('Analítica Predictiva & Segmentación Inteligente');
    expect(text).toContain('Proyección de Demanda Semanal');
    expect(text).toContain('MAE: 2.5');
    expect(text).toContain('RMSE: 3.1');
    expect(text).toContain('R²: 0.88');
    expect(text).toContain('2026-W44');
    expect(text).toContain('Bs 5,400.00');
    expect(text).toContain('38');
    expect(text).toContain('52');
    expect(text).toContain('Segmentación de Clientes');
    expect(text).toContain('Silhouette: 0.42');
    expect(text).toContain('Clientes VIP / Champions');
    expect(text).toContain('Clientes de alto valor y compra frecuente.');
    expect(text).toContain('Programa de lealtad exclusiva');
    expect(text).toContain('1 casos atípicos');
    expect(text).toContain('Sintético');
    expect(text).not.toContain('customer_id');
    expect(text).toContain('45 Observaciones Reales');
    expect(text).toContain('15 Muestras Sintéticas');
  });

  it('triggers ML retraining and renders backend training message metrics', () => {
    component.trainML();
    fixture.detectChanges();

    expect(service.trainMLModels).toHaveBeenCalled();
    expect(component.message).toContain(mockTrainingResponse.message);
    expect(component.message).toContain('MAE: 2.4');
    expect(component.message).toContain('Silhouette: 0.44');
  });

  it('handles 403 FEATURE_NOT_IN_PLAN with subscription upgrade message', () => {
    service.reportAssistant.mockReturnValueOnce(
      throwError(() => ({
        status: 403,
        error: { detail: { code: 'FEATURE_NOT_IN_PLAN', message: 'Los reportes con IA no están incluidos en su plan.' } },
      }))
    );

    component.assistantPrompt = 'Genera reporte IA';
    component.askAssistant();

    expect(component.assistantError).toContain('Plan Básico');
    expect(component.assistantError).toContain('Plan Profesional');
  });

  it('creates and configures browser speech recognition for Bolivian Spanish', () => {
    const recognition: any = { start: vi.fn(), stop: vi.fn() };
    const Recognition = vi.fn(function(this: any) { Object.assign(this, recognition); });
    Object.defineProperty(window, 'SpeechRecognition', { configurable: true, value: Recognition });
    component.isVoiceSupported = true;

    component.toggleVoiceCommand();
    const instance = Recognition.mock.instances[0] as any;

    expect(Recognition).toHaveBeenCalledOnce();
    expect(instance.lang).toBe('es-BO');
    expect(instance.continuous).toBe(false);
    expect(instance.interimResults).toBe(false);
    expect(instance.start).toHaveBeenCalledOnce();
  });

  it('shows listening state while speech recognition is active', () => {
    const recognition: any = { start: vi.fn(), stop: vi.fn() };
    Object.defineProperty(window, 'SpeechRecognition', { configurable: true, value: vi.fn(function(this: any) { Object.assign(this, recognition); }) });
    component.isVoiceSupported = true;

    component.toggleVoiceCommand();
    fixture.detectChanges();

    expect(component.isListeningVoice).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Detener dictado');
  });

  it('transcribes a voice result and submits it to the assistant', () => {
    const recognition: any = { start: vi.fn(), stop: vi.fn() };
    const Recognition = vi.fn(function(this: any) { Object.assign(this, recognition); });
    Object.defineProperty(window, 'SpeechRecognition', { configurable: true, value: Recognition });
    component.isVoiceSupported = true;
    component.filters = { branch_id: 1, start_date: '2030-01-01', end_date: '2030-01-31' };

    component.toggleVoiceCommand();
    const instance = Recognition.mock.instances[0] as any;
    instance.onresult({ results: [[{ transcript: '¿Qué productos tienen bajo stock?' }]] });

    expect(component.assistantPrompt).toBe('¿Qué productos tienen bajo stock?');
    expect(component.isListeningVoice).toBe(false);
    expect(service.reportAssistant).toHaveBeenCalledWith({
      prompt: '¿Qué productos tienen bajo stock?',
      date_from: '2030-01-01',
      date_to: '2030-01-31',
      branch_id: 1,
    });
  });

  it('clears listening state and reports recognition errors or completion', () => {
    const recognition: any = { start: vi.fn(), stop: vi.fn() };
    const Recognition = vi.fn(function(this: any) { Object.assign(this, recognition); });
    Object.defineProperty(window, 'SpeechRecognition', { configurable: true, value: Recognition });
    component.isVoiceSupported = true;

    component.toggleVoiceCommand();
    const instance = Recognition.mock.instances[0] as any;
    instance.onerror({ error: 'not-allowed' });
    expect(component.isListeningVoice).toBe(false);
    expect(component.assistantError).toBe('Error en comando de voz: not-allowed');

    component.toggleVoiceCommand();
    const secondInstance = Recognition.mock.instances[1] as any;
    secondInstance.onend();
    expect(component.isListeningVoice).toBe(false);
  });

  it('shows an unsupported-browser message when voice recognition is unavailable', () => {
    component.isVoiceSupported = false;

    component.toggleVoiceCommand();

    expect(component.assistantError).toBe('El reconocimiento de voz no está soportado en este navegador.');
  });
});
