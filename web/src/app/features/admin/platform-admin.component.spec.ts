import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AdminService } from '../../core/admin/admin.service';
import { NotificationService } from '../../core/notifications/notification.service';
import { PlatformTenant } from '../../core/models/admin.models';
import { PlatformAdminComponent } from './platform-admin.component';

describe('subscription renewal pause service URLs', () => {
  let service: AdminService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(AdminService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('exposes distinct renewal, pause, and resume service URLs', () => {
    service.renewPlatformSubscription(7).subscribe();
    expect(http.expectOne('/api/v1/platform/tenants/7/subscriptions/renew').request.method).toBe('POST');
    service.pausePlatformSubscription(7).subscribe();
    expect(http.expectOne('/api/v1/platform/tenants/7/subscriptions/pause').request.method).toBe('POST');
    service.resumePlatformSubscription(7).subscribe();
    expect(http.expectOne('/api/v1/platform/tenants/7/subscriptions/resume').request.method).toBe('POST');
  });
});

describe('PlatformAdminComponent subscription renewal pause', () => {
  let fixture: ComponentFixture<PlatformAdminComponent>;
  let component: PlatformAdminComponent;
  let service: Record<string, ReturnType<typeof vi.fn>>;

  const tenant: PlatformTenant = {
    id: 7,
    name: 'Acme',
    status: 'ACTIVE',
    created_at: '2025-01-01T00:00:00Z',
    active_subscription: {
      id: 9,
      tenant_id: 7,
      plan: { id: 1, code: 'BASIC', name: 'Basic', max_active_branches: 2, generative_reports_enabled: false, is_active: true },
      status: 'ACTIVE',
      valid_from: '2025-01-01T00:00:00Z',
      valid_until: '2025-02-01T00:00:00Z',
    },
  };

  beforeEach(async () => {
    service = {
      platformPlans: vi.fn(() => of({ items: [] })),
      platformTenants: vi.fn(() => of({ items: [tenant] })),
      renewPlatformSubscription: vi.fn(() => of({})),
      pausePlatformSubscription: vi.fn(() => of({})),
      resumePlatformSubscription: vi.fn(() => of({})),
      updatePlatformTenantStatus: vi.fn(() => of({})),
    };
    await TestBed.configureTestingModule({
      imports: [PlatformAdminComponent],
      providers: [
        { provide: AdminService, useValue: service },
        { provide: NotificationService, useValue: { success: vi.fn() } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(PlatformAdminComponent);
    component = fixture.componentInstance;
    component.tenants = [tenant];
    fixture.detectChanges();
  });

  it('renders distinct renewal, pause/resume, and tenant suspension actions', () => {
    const buttons = Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[];
    const visibleLabel = (button: HTMLButtonElement) =>
      button.querySelector<HTMLElement>(':scope > span:not(.material-symbols-outlined)')?.textContent?.trim();
    const labels = buttons.map(visibleLabel);
    const findButtonByLabel = (label: string) => buttons.find((button) => visibleLabel(button)?.includes(label));

    expect(labels).toContain('Renovar 30 días');
    expect(labels).toContain('Pausar suscripción');
    expect(labels).toContain('Suspender empresa');

    findButtonByLabel('Renovar')?.click();
    findButtonByLabel('Pausar')?.click();
    findButtonByLabel('Suspender')?.click();

    expect(service['renewPlatformSubscription']).toHaveBeenCalledWith(7);
    expect(service['pausePlatformSubscription']).toHaveBeenCalledWith(7);
    expect(service['updatePlatformTenantStatus']).toHaveBeenCalledWith(7, 'SUSPENDED');
    expect(service['resumePlatformSubscription']).not.toHaveBeenCalled();

    tenant.active_subscription!.status = 'PAUSED';
    fixture.detectChanges();
    const resumeButton = (Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[])
      .find((button) => visibleLabel(button)?.includes('Reanudar'));
    resumeButton?.click();

    expect(service['resumePlatformSubscription']).toHaveBeenCalledWith(7);
    expect(service['updatePlatformTenantStatus']).toHaveBeenCalledWith(7, 'SUSPENDED');
  });
});
