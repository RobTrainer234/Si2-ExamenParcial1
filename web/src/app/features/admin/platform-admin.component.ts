import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';

import { AdminService } from '../../core/admin/admin.service';
import { PlatformTenant, SubscriptionPlan, SubscriptionRecord } from '../../core/models/admin.models';
import { NotificationService } from '../../core/notifications/notification.service';

@Component({
  selector: 'app-platform-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="platform-shell">
      <header class="platform-hero">
        <div class="hero-content">
          <p class="eyebrow">Gobernanza Multi-Tenant · Superadmin SaaS</p>
          <h1>Consola de Plataforma FashionStore Cloud</h1>
          <p class="subtitle">
            Supervisa empresas contratantes, configura el catálogo de planes comerciales y administra el ciclo de vida, vigencia y renovaciones de suscripciones.
          </p>
        </div>
        <div class="platform-kpis">
          <div class="kpi-pill">
            <strong>{{ tenants.length }}</strong>
            <small>Empresas</small>
          </div>
          <div class="kpi-pill">
            <strong class="text-success">{{ activeTenantsCount }}</strong>
            <small>Activas</small>
          </div>
          <div class="kpi-pill">
            <strong [class.text-amber]="trialTenantsCount > 0">{{ trialTenantsCount }}</strong>
            <small>En Prueba</small>
          </div>
          <div class="kpi-pill">
            <strong [class.text-accent]="reactivationRequestsCount > 0">{{ reactivationRequestsCount }}</strong>
            <small>Solicitudes</small>
          </div>
          <div class="kpi-pill">
            <strong>{{ plans.length }}</strong>
            <small>Planes</small>
          </div>
        </div>
      </header>

      @if (error) {
        <div class="alert-box error-alert" role="alert">
          <span class="material-symbols-outlined" aria-hidden="true">error</span>
          <span>{{ error }}</span>
          <button type="button" class="close-alert-btn" (click)="error = ''" aria-label="Cerrar error">×</button>
        </div>
      }

      <div class="platform-tabs" role="tablist" aria-label="Secciones de plataforma SaaS">
        <button type="button" [class.active]="tab === 'tenants'" (click)="tab = 'tenants'">
          <span class="material-symbols-outlined" aria-hidden="true">domain</span>
          <span>Empresas y Suscripciones</span>
          <span class="tab-badge">{{ tenants.length }}</span>
        </button>
        <button type="button" [class.active]="tab === 'plans'" (click)="tab = 'plans'">
          <span class="material-symbols-outlined" aria-hidden="true">workspace_premium</span>
          <span>Catálogo de Planes</span>
          <span class="tab-badge">{{ plans.length }}</span>
        </button>
      </div>

      @if (tab === 'tenants') {
        <section class="platform-section" aria-label="Gestión de empresas y suscripciones">
          <!-- Main Toolbar: Header + Search + Filters -->
          <div class="section-toolbar-panel">
            <div class="toolbar-title-group">
              <div>
                <h2>Empresas registradas</h2>
                <p class="muted">Supervisa vigencia de suscripciones, asigna planes comerciales y atiende solicitudes.</p>
              </div>
              <button class="button button-dark btn-register-toggle" type="button" (click)="showTenantForm = !showTenantForm">
                <span class="material-symbols-outlined" aria-hidden="true">{{ showTenantForm ? 'close' : 'add' }}</span>
                <span>{{ showTenantForm ? 'Cerrar formulario' : 'Registrar nueva empresa' }}</span>
              </button>
            </div>

            <!-- Interactive Search & Filter Controls -->
            <div class="interactive-filter-row">
              <div class="search-input-wrapper">
                <span class="material-symbols-outlined search-icon" aria-hidden="true">search</span>
                <input
                  type="text"
                  [(ngModel)]="searchQuery"
                  placeholder="Buscar empresa por nombre o ID..."
                  aria-label="Buscar empresa"
                />
                @if (searchQuery) {
                  <button type="button" class="clear-search-btn" (click)="searchQuery = ''" aria-label="Borrar búsqueda">
                    <span class="material-symbols-outlined" aria-hidden="true">clear</span>
                  </button>
                }
              </div>

              <div class="filter-chips-group" role="group" aria-label="Filtros rápidos por estado">
                <button
                  type="button"
                  class="filter-chip"
                  [class.active]="statusFilter === 'ALL'"
                  (click)="statusFilter = 'ALL'"
                >
                  Todas ({{ tenants.length }})
                </button>
                <button
                  type="button"
                  class="filter-chip"
                  [class.active]="statusFilter === 'ACTIVE'"
                  (click)="statusFilter = 'ACTIVE'"
                >
                  <span class="chip-dot dot-active"></span>
                  Activas ({{ activeTenantsCount }})
                </button>
                <button
                  type="button"
                  class="filter-chip"
                  [class.active]="statusFilter === 'TRIAL'"
                  (click)="statusFilter = 'TRIAL'"
                >
                  <span class="chip-dot dot-trial"></span>
                  En Prueba ({{ trialTenantsCount }})
                </button>
                @if (reactivationRequestsCount > 0) {
                  <button
                    type="button"
                    class="filter-chip chip-requests"
                    [class.active]="statusFilter === 'REQUESTS'"
                    (click)="statusFilter = 'REQUESTS'"
                  >
                    ★ Solicitudes ({{ reactivationRequestsCount }})
                  </button>
                }
                @if (suspendedTenantsCount > 0) {
                  <button
                    type="button"
                    class="filter-chip"
                    [class.active]="statusFilter === 'SUSPENDED'"
                    (click)="statusFilter = 'SUSPENDED'"
                  >
                    <span class="chip-dot dot-suspended"></span>
                    Inactivas ({{ suspendedTenantsCount }})
                  </button>
                }
              </div>
            </div>
          </div>

          @if (showTenantForm) {
            <form [formGroup]="tenantForm" (ngSubmit)="createTenant()" class="platform-card form-card">
              <div class="form-header">
                <div>
                  <h3>Alta administrativa de empresa</h3>
                  <p class="muted">Registra un nuevo inquilino con su administrador inicial y plan comercial asignado.</p>
                </div>
                <button type="button" class="btn-close-form" (click)="showTenantForm = false">✕</button>
              </div>

              <div class="form-grid-3">
                <label>
                  <span>Nombre de empresa *</span>
                  <input formControlName="name" placeholder="Ej. Boutique Andina" />
                </label>
                <label>
                  <span>Plan inicial *</span>
                  <select formControlName="plan_code">
                    @for (p of plans; track p.code) {
                      <option [value]="p.code">{{ p.name }} (Límite: {{ p.max_active_branches }} suc.)</option>
                    }
                  </select>
                </label>
                <label>
                  <span>Correo del administrador</span>
                  <input type="email" formControlName="admin_email" placeholder="admin@empresa.bo" />
                </label>
                <label>
                  <span>Nombre admin</span>
                  <input formControlName="admin_first_name" placeholder="Ej. Carlos" />
                </label>
                <label>
                  <span>Apellido admin</span>
                  <input formControlName="admin_last_name" placeholder="Ej. Miranda" />
                </label>
                <label>
                  <span>Contraseña inicial</span>
                  <input type="password" formControlName="admin_password" placeholder="AdminSeed123!" />
                </label>
              </div>
              <div class="form-actions">
                <button class="button button-light" type="button" (click)="showTenantForm = false">
                  Cancelar
                </button>
                <button class="button button-dark" type="submit" [disabled]="tenantForm.invalid || loading">
                  <span class="material-symbols-outlined" aria-hidden="true">domain_add</span>
                  <span>{{ loading ? 'Registrando...' : 'Registrar empresa' }}</span>
                </button>
              </div>
            </form>
          }

          <!-- Grid of Tenant Cards (Clean, Responsive, No-Overflow) -->
          <div class="tenants-grid">
            @for (tenant of filteredTenants; track tenant.id) {
              <article class="platform-card tenant-card" [class.reactivation-highlight]="tenant.reactivation_requested">
                <!-- Card Header with Avatar & Status -->
                <div class="tenant-card-header">
                  <div class="tenant-avatar" [attr.aria-hidden]="true">
                    {{ getInitials(tenant.name) }}
                  </div>
                  <div class="tenant-identity">
                    <div class="tenant-title-row">
                      <h3 class="tenant-name" [title]="tenant.name">{{ tenant.name }}</h3>
                      <span
                        class="status-pill"
                        [class.active]="tenant.status === 'ACTIVE' && !tenant.is_expired"
                        [class.suspended]="tenant.status !== 'ACTIVE' || tenant.is_expired"
                      >
                        <span class="status-dot"></span>
                        {{ tenant.status === 'ACTIVE' ? (tenant.is_expired ? 'Vencida' : 'Activa') : 'Suspendida' }}
                      </span>
                    </div>

                    <div class="tenant-meta-badges">
                      <span class="tenant-id-tag">ID #{{ tenant.id }}</span>
                      <span class="tenant-date-tag">Alta: {{ tenant.created_at | date:'dd/MM/yyyy' }}</span>
                      @if (tenant.is_trial) {
                        <span class="trial-pill">⏱ Prueba 14 días</span>
                      }
                      @if (tenant.is_cancelled) {
                        <span class="cancelled-pill" [title]="'Cancelación programada: ' + (tenant.cancellation_reason || 'Sin motivo especificado')">
                          ⚠️ Cancelación programada
                        </span>
                      }
                      @if (tenant.reactivation_requested) {
                        <span class="request-pill">★ Solicitud: {{ tenant.requested_plan_code || 'BASIC' }}</span>
                      }
                    </div>
                  </div>
                </div>

                <!-- Info Metrics Box -->
                <div class="tenant-sub-box">
                  <div class="sub-stat-item">
                    <span class="meta-label">Plan actual</span>
                    <div class="sub-stat-val">
                      <span class="plan-chip" [class.pro]="tenant.active_subscription?.plan?.code === 'PROFESSIONAL'">
                        {{ tenant.active_subscription?.plan?.name || 'Sin suscripción' }}
                      </span>
                    </div>
                  </div>
                  <div class="sub-stat-item">
                    <span class="meta-label">Límite sucursales</span>
                    <div class="sub-stat-val">
                      <span class="branch-count-badge">
                        <span class="material-symbols-outlined icon-inline" aria-hidden="true">store</span>
                        <strong>{{ tenant.active_subscription?.plan?.max_active_branches ?? '-' }}</strong> suc.
                      </span>
                    </div>
                  </div>
                  <div class="sub-stat-item">
                    <span class="meta-label">Vigencia</span>
                    <div class="sub-stat-val vigencia-val" [title]="tenant.active_subscription?.valid_until ? (tenant.active_subscription?.valid_until | date:'medium') : 'Indefinida'">
                      <span class="material-symbols-outlined icon-inline" aria-hidden="true">event</span>
                      <span>{{ tenant.active_subscription?.valid_until ? (tenant.active_subscription?.valid_until | date:'dd/MM/yyyy') : 'Activa' }}</span>
                    </div>
                  </div>
                </div>

                <!-- Plan Management Panel (No Overflow, 2-Tier Balanced Layout) -->
                <div class="plan-management-box">
                  <div class="plan-select-wrapper">
                    <label class="compact-label" [for]="'plan-select-' + tenant.id">
                      <span>Asignar o Cambiar Plan Comercial:</span>
                    </label>
                    <div class="select-container">
                      <select
                        [id]="'plan-select-' + tenant.id"
                        [ngModel]="selectedPlanByTenant[tenant.id] || tenant.requested_plan_code || tenant.active_subscription?.plan?.code || 'BASIC'"
                        (ngModelChange)="selectedPlanByTenant[tenant.id] = $event"
                        [attr.aria-label]="'Seleccionar plan para ' + tenant.name"
                      >
                        @for (p of plans; track p.code) {
                          <option [value]="p.code">{{ p.name }} ({{ p.max_active_branches }} suc. max)</option>
                        }
                      </select>
                    </div>
                  </div>

                  <div class="plan-action-buttons">
                    <button
                      type="button"
                      class="btn-action-primary"
                      (click)="assignPlan(tenant)"
                      [title]="'Aplicar plan a ' + tenant.name"
                    >
                      <span class="material-symbols-outlined" aria-hidden="true">swap_horiz</span>
                      <span>{{ tenant.reactivation_requested || tenant.is_expired ? 'Reactivar Plan' : 'Cambiar Plan' }}</span>
                    </button>
                    <button
                      type="button"
                      class="btn-action-secondary"
                      (click)="renewSubscription(tenant)"
                      [title]="'Extender vigencia 30 días para ' + tenant.name"
                    >
                      <span class="material-symbols-outlined" aria-hidden="true">update</span>
                      <span>Renovar 30 días</span>
                    </button>
                  </div>
                </div>

                <!-- Secondary Actions Toolbar -->
                <div class="secondary-actions-toolbar">
                  <button
                    type="button"
                    class="btn-tool"
                    (click)="viewHistory(tenant)"
                    title="Ver historial de suscripciones auditadas"
                  >
                    <span class="material-symbols-outlined" aria-hidden="true">history</span>
                    <span>Historial</span>
                  </button>

                  @if (tenant.active_subscription?.status === 'PAUSED') {
                    <button
                      type="button"
                      class="btn-tool btn-resume"
                      (click)="resumeSubscription(tenant)"
                      title="Reanudar suscripción pausada"
                    >
                      <span class="material-symbols-outlined" aria-hidden="true">play_circle</span>
                      <span>Reanudar</span>
                    </button>
                  } @else {
                    <button
                      type="button"
                      class="btn-tool"
                      (click)="pauseSubscription(tenant)"
                      title="Pausar temporalmente el servicio"
                    >
                      <span class="material-symbols-outlined" aria-hidden="true">pause_circle</span>
                      <span>Pausar suscripción</span>
                    </button>
                  }

                  <button
                    type="button"
                    class="btn-tool"
                    [class.btn-danger]="tenant.status === 'ACTIVE'"
                    [class.btn-activate]="tenant.status !== 'ACTIVE'"
                    (click)="toggleTenantStatus(tenant)"
                    [title]="tenant.status === 'ACTIVE' ? 'Suspender empresa' : 'Activar empresa'"
                  >
                    <span class="material-symbols-outlined" aria-hidden="true">{{ tenant.status === 'ACTIVE' ? 'block' : 'check_circle' }}</span>
                    <span>{{ tenant.status === 'ACTIVE' ? 'Suspender empresa' : 'Activar empresa' }}</span>
                  </button>
                </div>
              </article>
            } @empty {
              <div class="empty-filter-state">
                <span class="material-symbols-outlined empty-icon" aria-hidden="true">storefront</span>
                <h4>No se encontraron empresas</h4>
                <p class="muted">No hay empresas que coincidan con "{{ searchQuery }}" y el filtro seleccionado.</p>
                <button class="button button-light" type="button" (click)="searchQuery = ''; statusFilter = 'ALL'">
                  Restablecer filtros
                </button>
              </div>
            }
          </div>

          <!-- Subscription History Modal / Drawer -->
          @if (selectedHistoryTenant) {
            <div class="history-overlay" (click)="selectedHistoryTenant = null">
              <div class="history-modal" (click)="$event.stopPropagation()">
                <div class="history-modal-header">
                  <div>
                    <span class="eyebrow">Auditoría de Suscripciones</span>
                    <h3>{{ selectedHistoryTenant.name }}</h3>
                    <small class="muted">{{ historyRecords.length }} registro(s) histórico(s) auditados</small>
                  </div>
                  <button type="button" class="btn-close-modal" (click)="selectedHistoryTenant = null" aria-label="Cerrar modal">✕</button>
                </div>

                <div class="history-list-container">
                  @for (rec of historyRecords; track rec.id) {
                    <div class="history-row-item">
                      <div class="history-plan-info">
                        <strong>{{ rec.plan.name }} ({{ rec.plan.code }})</strong>
                        <span class="status-pill" [class.active]="rec.status === 'ACTIVE'">
                          <span class="status-dot"></span>
                          {{ rec.status }}
                        </span>
                      </div>
                      <div class="history-dates">
                        <small><strong>Desde:</strong> {{ rec.valid_from | date:'dd/MM/yyyy HH:mm' }}</small>
                        <small><strong>Hasta:</strong> {{ rec.valid_until ? (rec.valid_until | date:'dd/MM/yyyy HH:mm') : 'Vigente' }}</small>
                      </div>
                    </div>
                  } @empty {
                    <p class="muted text-center py-4">No hay registros históricos de suscripción para esta empresa.</p>
                  }
                </div>

                <div class="history-modal-footer">
                  <button type="button" class="button button-dark" (click)="selectedHistoryTenant = null">Entendido</button>
                </div>
              </div>
            </div>
          }
        </section>
      }

      @if (tab === 'plans') {
        <section class="platform-section" aria-label="Gestión de planes de suscripción">
          <div class="section-toolbar-panel">
            <div class="toolbar-title-group">
              <div>
                <h2>Catálogo de Planes de Suscripción</h2>
                <p class="muted">Configura precios, límites de sucursales activas y acceso a módulos de Inteligencia Artificial.</p>
              </div>
              <button class="button button-dark" type="button" (click)="showPlanForm = !showPlanForm">
                <span class="material-symbols-outlined" aria-hidden="true">{{ showPlanForm ? 'close' : 'add' }}</span>
                <span>{{ showPlanForm ? 'Cerrar formulario' : 'Crear nuevo plan' }}</span>
              </button>
            </div>
          </div>

          @if (showPlanForm) {
            <form [formGroup]="planForm" (ngSubmit)="createPlan()" class="platform-card form-card">
              <div class="form-header">
                <div>
                  <h3>Nuevo plan comercial de suscripción</h3>
                  <p class="muted">Establece el código, nombre y límites para los inquilinos que contraten este plan.</p>
                </div>
                <button type="button" class="btn-close-form" (click)="showPlanForm = false">✕</button>
              </div>

              <div class="form-grid-3">
                <label>
                  <span>Código único (mayúsculas) *</span>
                  <input formControlName="code" placeholder="Ej. ENTERPRISE" />
                </label>
                <label>
                  <span>Nombre visible *</span>
                  <input formControlName="name" placeholder="Ej. Empresarial Corporativo" />
                </label>
                <label>
                  <span>Máximo de sucursales activas *</span>
                  <input type="number" min="1" formControlName="max_active_branches" />
                </label>
                <label>
                  <span>Precio mensual (Bs) *</span>
                  <input type="number" min="0" step="1" formControlName="price_monthly" />
                </label>
                <label>
                  <span>Precio anual (Bs) *</span>
                  <input type="number" min="0" step="1" formControlName="price_annual" />
                </label>
              </div>
              <label class="checkbox-row">
                <input type="checkbox" formControlName="generative_reports_enabled" />
                <span>Habilitar Reportes Generativos con IA y Analítica Predictiva ML</span>
              </label>
              <div class="form-actions">
                <button class="button button-light" type="button" (click)="showPlanForm = false">
                  Cancelar
                </button>
                <button class="button button-dark" type="submit" [disabled]="planForm.invalid || loading">
                  <span class="material-symbols-outlined" aria-hidden="true">save</span>
                  <span>{{ loading ? 'Guardando...' : 'Guardar plan' }}</span>
                </button>
              </div>
            </form>
          }

          <div class="plans-admin-grid">
            @for (plan of plans; track plan.id) {
              <article class="platform-card plan-admin-card" [class.plan-pro]="plan.code === 'PROFESSIONAL'">
                <!-- Plan Header -->
                <div class="plan-card-top">
                  <div class="badge-row">
                    <span class="status-pill" [class.active]="plan.is_active">
                      <span class="status-dot"></span>
                      {{ plan.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                    <span class="code-tag">{{ plan.code }}</span>
                    <span class="audience-badge" [class.pro-audience]="plan.code === 'PROFESSIONAL'">
                      {{ getPlanAudience(plan.code) }}
                    </span>
                  </div>
                  <h3>Plan {{ plan.name }}</h3>
                  <p class="plan-desc-text">{{ getPlanDescription(plan.code) }}</p>
                </div>

                <!-- Price Hero Banner -->
                <div class="plan-price-hero">
                  <div class="price-main-row">
                    <span class="price-amount">Bs {{ plan.price_monthly || 0 }}</span>
                    <span class="price-period">/ mes</span>
                  </div>
                  <div class="price-annual-sub">
                    <span class="material-symbols-outlined annual-icon" aria-hidden="true">savings</span>
                    <span>Bs {{ plan.price_annual || 0 }} facturado anual (Ahorro del 17%)</span>
                  </div>
                </div>

                <!-- Feature Matrix -->
                <div class="plan-details-matrix">
                  <!-- Block 1: Retail & Store Operations -->
                  <div class="matrix-section">
                    <div class="matrix-section-header">
                      <span class="material-symbols-outlined section-icon" aria-hidden="true">storefront</span>
                      <h4>Capacidades de Tienda & Retail</h4>
                    </div>
                    <ul class="feature-checklist">
                      <li class="feature-item">
                        <span class="material-symbols-outlined item-check" aria-hidden="true">check_circle</span>
                        <span>Hasta <strong>{{ plan.max_active_branches }}</strong> sucursal{{ plan.max_active_branches > 1 ? 'es' : '' }} activas simultáneamente</span>
                      </li>
                      <li class="feature-item">
                        <span class="material-symbols-outlined item-check" aria-hidden="true">check_circle</span>
                        <span>Punto de Venta (POS) presencial y catálogo web público</span>
                      </li>
                      <li class="feature-item">
                        <span class="material-symbols-outlined item-check" aria-hidden="true">check_circle</span>
                        <span>Modo Offline resiliente (IndexedDB en Web y SQLite en Móvil)</span>
                      </li>
                      <li class="feature-item">
                        <span class="material-symbols-outlined item-check" aria-hidden="true">check_circle</span>
                        <span>Traspasos de stock entre sucursales en 2 fases con verificación</span>
                      </li>
                      <li class="feature-item">
                        <span class="material-symbols-outlined item-check" aria-hidden="true">check_circle</span>
                        <span>Cambios de prenda y notas de crédito (30 días de garantía)</span>
                      </li>
                      <li class="feature-item">
                        <span class="material-symbols-outlined item-check" aria-hidden="true">check_circle</span>
                        <span>Gestión de personal (Encargados y Cajeros independientes)</span>
                      </li>
                    </ul>
                  </div>

                  <!-- Block 2: AI & Analytics -->
                  <div class="matrix-section">
                    <div class="matrix-section-header">
                      <span class="material-symbols-outlined section-icon" [class.ai-accent]="plan.generative_reports_enabled" aria-hidden="true">psychology</span>
                      <h4>Inteligencia Artificial & Analítica</h4>
                    </div>
                    <ul class="feature-checklist">
                      <li class="feature-item" [class.item-disabled]="!plan.generative_reports_enabled">
                        <span class="material-symbols-outlined" [class.item-check]="plan.generative_reports_enabled" [class.item-cross]="!plan.generative_reports_enabled" aria-hidden="true">
                          {{ plan.generative_reports_enabled ? 'check_circle' : 'cancel' }}
                        </span>
                        <span>
                          <strong>Asistente Sofía IA:</strong> Consultas analíticas en lenguaje natural por texto y voz (Text-to-SQL)
                        </span>
                      </li>
                      <li class="feature-item" [class.item-disabled]="!plan.generative_reports_enabled">
                        <span class="material-symbols-outlined" [class.item-check]="plan.generative_reports_enabled" [class.item-cross]="!plan.generative_reports_enabled" aria-hidden="true">
                          {{ plan.generative_reports_enabled ? 'check_circle' : 'cancel' }}
                        </span>
                        <span>
                          <strong>Predicción ML:</strong> Pronóstico supervisado de demanda y stock crítico
                        </span>
                      </li>
                      <li class="feature-item" [class.item-disabled]="!plan.generative_reports_enabled">
                        <span class="material-symbols-outlined" [class.item-check]="plan.generative_reports_enabled" [class.item-cross]="!plan.generative_reports_enabled" aria-hidden="true">
                          {{ plan.generative_reports_enabled ? 'check_circle' : 'cancel' }}
                        </span>
                        <span>
                          <strong>Segmentación K-Means:</strong> Clustering de hábitos y clientes de alto valor
                        </span>
                      </li>
                      <li class="feature-item" [class.item-disabled]="!plan.generative_reports_enabled">
                        <span class="material-symbols-outlined" [class.item-check]="plan.generative_reports_enabled" [class.item-cross]="!plan.generative_reports_enabled" aria-hidden="true">
                          {{ plan.generative_reports_enabled ? 'check_circle' : 'cancel' }}
                        </span>
                        <span>
                          <strong>Exportación Ejecutiva:</strong> Balances y reportes en formato PDF y Excel (.xlsx)
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>

                <div class="plan-admin-actions">
                  <button type="button" class="btn-plan-tool" (click)="togglePlanAI(plan)" [title]="'Alternar soporte de IA'">
                    <span class="material-symbols-outlined" aria-hidden="true">psychology</span>
                    <span>{{ plan.generative_reports_enabled ? 'Quitar IA' : 'Activar IA' }}</span>
                  </button>
                  <button type="button" class="btn-plan-tool" (click)="bumpPlanBranches(plan, 1)" [title]="'Aumentar 1 sucursal'">
                    <span class="material-symbols-outlined" aria-hidden="true">add</span>
                    <span>+1 Sucursal</span>
                  </button>
                  <button
                    type="button"
                    class="btn-plan-tool"
                    [class.btn-plan-danger]="plan.is_active"
                    (click)="togglePlanActive(plan)"
                    [title]="plan.is_active ? 'Desactivar plan' : 'Activar plan'"
                  >
                    <span class="material-symbols-outlined" aria-hidden="true">{{ plan.is_active ? 'visibility_off' : 'visibility' }}</span>
                    <span>{{ plan.is_active ? 'Desactivar' : 'Activar' }}</span>
                  </button>
                </div>
              </article>
            }
          </div>
        </section>
      }
    </div>
  `,
  styles: [`
    .platform-shell {
      margin: 0 auto;
      max-width: 1360px;
      padding: 32px 24px 72px;
      box-sizing: border-box;
    }

    /* Hero Section */
    .platform-hero {
      align-items: center;
      background: linear-gradient(135deg, #1b1c1a 0%, #2b2824 100%);
      border-radius: 20px;
      color: #f7efe5;
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      justify-content: space-between;
      margin-bottom: 24px;
      padding: 32px 36px;
      box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.2);
    }
    .hero-content {
      max-width: 680px;
    }
    .platform-hero .eyebrow {
      color: #d9b69f;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      margin: 0 0 8px;
      text-transform: uppercase;
    }
    .platform-hero h1 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(1.8rem, 3vw, 2.4rem);
      font-weight: 500;
      margin: 0 0 10px;
      line-height: 1.2;
    }
    .platform-hero .subtitle {
      color: #d8d2ca;
      font-size: 0.92rem;
      line-height: 1.55;
      margin: 0;
    }
    .platform-kpis {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }
    .kpi-pill {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      min-width: 90px;
      padding: 12px 16px;
      text-align: center;
      backdrop-filter: blur(8px);
    }
    .kpi-pill strong {
      display: block;
      font-size: 1.45rem;
      color: #ffffff;
    }
    .kpi-pill strong.text-success { color: #86efac; }
    .kpi-pill strong.text-amber { color: #fde047; }
    .kpi-pill strong.text-accent { color: #fca5a5; }
    .kpi-pill small {
      color: #d9b69f;
      font-size: 0.68rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      font-weight: 600;
    }

    /* Alerts */
    .alert-box {
      align-items: center;
      border-radius: 12px;
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      padding: 14px 18px;
      font-size: 0.88rem;
    }
    .error-alert {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
    }
    .close-alert-btn {
      margin-left: auto;
      background: transparent;
      border: 0;
      font-size: 1.2rem;
      color: inherit;
      cursor: pointer;
    }

    /* Tabs */
    .platform-tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--line, #e5e0d8);
      padding-bottom: 12px;
    }
    .platform-tabs button {
      align-items: center;
      background: #ffffff;
      border: 1px solid var(--line, #e5e0d8);
      border-radius: 10px;
      color: var(--muted, #756f68);
      display: inline-flex;
      font-size: 0.74rem;
      font-weight: 700;
      gap: 8px;
      letter-spacing: 0.06em;
      padding: 11px 18px;
      text-transform: uppercase;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    .platform-tabs button:hover {
      background: #f7f5f1;
      color: #1b1c1a;
    }
    .platform-tabs button.active {
      background: #1b1c1a;
      border-color: #1b1c1a;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(27, 28, 26, 0.15);
    }
    .tab-badge {
      background: rgba(0, 0, 0, 0.08);
      border-radius: 999px;
      font-size: 0.65rem;
      padding: 2px 7px;
    }
    .platform-tabs button.active .tab-badge {
      background: rgba(255, 255, 255, 0.2);
    }

    /* Toolbar Panel */
    .section-toolbar-panel {
      background: #ffffff;
      border: 1px solid var(--line, #e5e0d8);
      border-radius: 16px;
      padding: 20px 24px;
      margin-bottom: 22px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }
    .toolbar-title-group {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }
    .toolbar-title-group h2 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.55rem;
      margin: 0 0 4px;
      color: #1b1c1a;
    }
    .btn-register-toggle {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 18px;
      font-size: 0.74rem;
    }

    /* Interactive Filters & Search */
    .interactive-filter-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      border-top: 1px solid #f0ede6;
      padding-top: 16px;
    }
    .search-input-wrapper {
      position: relative;
      flex: 1;
      min-width: 280px;
      max-width: 480px;
    }
    .search-input-wrapper .search-icon {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: #9ca3af;
      font-size: 19px;
      pointer-events: none;
    }
    .search-input-wrapper input {
      width: 100%;
      padding: 10px 36px 10px 38px;
      border-radius: 10px;
      border: 1px solid var(--line, #e5e0d8);
      background: #fbf9f6;
      font-size: 0.88rem;
      box-sizing: border-box;
      transition: all 0.2s;
    }
    .search-input-wrapper input:focus {
      background: #ffffff;
      border-color: #8f6d2d;
      box-shadow: 0 0 0 3px rgba(143, 109, 45, 0.12);
    }
    .clear-search-btn {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      background: transparent;
      border: 0;
      color: #9ca3af;
      cursor: pointer;
      display: flex;
      padding: 2px;
    }
    .clear-search-btn:hover { color: #1b1c1a; }

    .filter-chips-group {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .filter-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #f7f5f1;
      border: 1px solid #e5e0d8;
      border-radius: 999px;
      padding: 7px 14px;
      font-size: 0.72rem;
      font-weight: 600;
      color: #555;
      cursor: pointer;
      transition: all 0.2s;
    }
    .filter-chip:hover {
      background: #eeebe5;
      color: #1b1c1a;
    }
    .filter-chip.active {
      background: #1b1c1a;
      border-color: #1b1c1a;
      color: #ffffff;
    }
    .chip-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
    }
    .dot-active { background: #16a34a; }
    .dot-trial { background: #d97706; }
    .dot-suspended { background: #dc2626; }
    .filter-chip.active .chip-dot { background: #ffffff; }
    .chip-requests {
      color: #991b1b;
      background: #fef2f2;
      border-color: #fecaca;
    }
    .chip-requests.active {
      background: #b91c1c;
      border-color: #b91c1c;
      color: #ffffff;
    }

    /* Common Card */
    .platform-card {
      background: #ffffff;
      border: 1px solid var(--line, #e5e0d8);
      border-radius: 16px;
      padding: 22px;
      box-sizing: border-box;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
    }

    /* Form Card */
    .form-card {
      margin-bottom: 24px;
      border: 1px solid #d5cec4;
      background: #fbf9f6;
    }
    .form-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
      border-bottom: 1px solid #eeebe5;
      padding-bottom: 12px;
    }
    .form-header h3 {
      font-family: 'Playfair Display', Georgia, serif;
      margin: 0 0 4px;
      font-size: 1.35rem;
    }
    .btn-close-form {
      background: transparent;
      border: 0;
      font-size: 1.2rem;
      cursor: pointer;
      color: var(--muted);
    }
    .form-grid-3 {
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      margin-bottom: 16px;
    }
    .checkbox-row {
      align-items: center;
      display: inline-flex;
      flex-direction: row;
      gap: 10px;
      margin-bottom: 16px;
      text-transform: none;
      cursor: pointer;
      font-size: 0.82rem;
      font-weight: 500;
    }
    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }

    /* Tenants Grid: Responsive & Clean */
    .tenants-grid {
      display: grid;
      gap: 20px;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    }

    /* Tenant Card (NO OVERFLOW) */
    .tenant-card {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
      overflow: hidden;
    }
    .tenant-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 24px -8px rgba(27, 28, 26, 0.1);
      border-color: #d1c9be;
    }
    .tenant-card.reactivation-highlight {
      border-color: #8d4d38;
      box-shadow: 0 8px 24px -6px rgba(141, 77, 56, 0.25);
    }

    /* Card Top / Identity */
    .tenant-card-header {
      display: flex;
      gap: 14px;
      align-items: flex-start;
      margin-bottom: 14px;
    }
    .tenant-avatar {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #1b1c1a 0%, #3d3b37 100%);
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.92rem;
      flex-shrink: 0;
      letter-spacing: 0.05em;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    .tenant-identity {
      flex: 1;
      min-width: 0;
    }
    .tenant-title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 6px;
    }
    .tenant-name {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
      color: #1b1c1a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tenant-meta-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }
    .tenant-id-tag, .tenant-date-tag {
      font-size: 0.68rem;
      color: var(--muted, #756f68);
      background: #f7f5f1;
      padding: 2px 7px;
      border-radius: 6px;
      font-weight: 500;
    }

    /* Status Pills */
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 3px 9px;
      border-radius: 999px;
      flex-shrink: 0;
    }
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }
    .status-pill.active { background: #dcfce7; color: #15803d; }
    .status-pill.suspended { background: #fee2e2; color: #b91c1c; }
    .trial-pill {
      background: #fef3c7;
      color: #92400e;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .request-pill {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .cancelled-pill {
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #b45309;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
    }

    /* Sub-box Specs Panel */
    .tenant-sub-box {
      background: #fbf9f6;
      border: 1px solid #eeebe5;
      border-radius: 12px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      padding: 12px;
      margin: 12px 0 16px;
      box-sizing: border-box;
    }
    .sub-stat-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }
    .meta-label {
      color: var(--muted, #756f68);
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .sub-stat-val {
      font-size: 0.82rem;
      font-weight: 600;
      color: #1b1c1a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .plan-chip {
      background: #f0ede6;
      color: #1b1c1a;
      padding: 2px 7px;
      border-radius: 6px;
      font-size: 0.74rem;
      font-weight: 700;
    }
    .plan-chip.pro {
      background: #fef3c7;
      color: #78350f;
    }
    .branch-count-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .icon-inline {
      font-size: 15px;
      color: var(--muted);
      vertical-align: middle;
    }
    .vigencia-val {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.76rem;
    }

    /* Plan Management Box (FIX FOR OVERFLOW) */
    .plan-management-box {
      background: #f8f6f2;
      border: 1px solid #e7e2d8;
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 14px;
      box-sizing: border-box;
    }
    .compact-label {
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--muted);
      margin-bottom: 6px;
      display: block;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .select-container {
      width: 100%;
    }
    .select-container select {
      width: 100%;
      box-sizing: border-box;
      padding: 9px 12px;
      font-size: 0.82rem;
      border: 1px solid #d5cec4;
      border-radius: 8px;
      background: #ffffff;
      color: #1b1c1a;
      font-weight: 500;
    }
    .select-container select:focus {
      border-color: #8f6d2d;
      outline: none;
    }
    .plan-action-buttons {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }
    .btn-action-primary {
      background: #1b1c1a;
      color: #ffffff;
      border: none;
      border-radius: 8px;
      padding: 9px 10px;
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      cursor: pointer;
      transition: background 0.2s ease, transform 0.1s ease;
      white-space: nowrap;
    }
    .btn-action-primary:hover {
      background: #8f6d2d;
    }
    .btn-action-primary .material-symbols-outlined {
      font-size: 16px;
    }

    .btn-action-secondary {
      background: #ffffff;
      color: #1b1c1a;
      border: 1px solid #d5cec4;
      border-radius: 8px;
      padding: 9px 10px;
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .btn-action-secondary:hover {
      background: #f0ede6;
      border-color: #b8b0a2;
    }
    .btn-action-secondary .material-symbols-outlined {
      font-size: 16px;
    }

    /* Secondary Actions Toolbar */
    .secondary-actions-toolbar {
      display: flex;
      gap: 6px;
      box-sizing: border-box;
    }
    .btn-tool {
      flex: 1;
      padding: 8px 10px;
      font-size: 0.68rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      background: #ffffff;
      border: 1px solid #e5e0d8;
      border-radius: 8px;
      color: #555555;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .btn-tool .material-symbols-outlined {
      font-size: 16px;
    }
    .btn-tool:hover {
      background: #f7f5f1;
      border-color: #d1c9be;
      color: #1b1c1a;
    }
    .btn-tool.btn-danger:hover {
      background: #fef2f2;
      border-color: #fca5a5;
      color: #b91c1c;
    }
    .btn-tool.btn-activate:hover, .btn-tool.btn-resume:hover {
      background: #f0fdf4;
      border-color: #86efac;
      color: #15803d;
    }

    /* Empty state */
    .empty-filter-state {
      grid-column: 1 / -1;
      text-align: center;
      padding: 48px 24px;
      background: #ffffff;
      border: 1px dashed #ded8ce;
      border-radius: 16px;
    }
    .empty-icon {
      font-size: 48px;
      color: #9ca3af;
      margin-bottom: 12px;
    }
    .empty-filter-state h4 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.3rem;
      margin: 0 0 6px;
    }

    /* History Modal Overlay */
    .history-overlay {
      position: fixed;
      inset: 0;
      background: rgba(27, 28, 26, 0.6);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
      box-sizing: border-box;
      animation: fadeIn 0.2s ease-out;
    }
    .history-modal {
      background: #ffffff;
      border-radius: 20px;
      width: 100%;
      max-width: 580px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
      padding: 28px;
      box-sizing: border-box;
      animation: slideUp 0.25s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

    .history-modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 18px;
      border-bottom: 1px solid #f0ede6;
      padding-bottom: 14px;
    }
    .history-modal-header h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.45rem;
      margin: 4px 0 2px;
    }
    .btn-close-modal {
      background: transparent;
      border: 0;
      font-size: 1.3rem;
      cursor: pointer;
      color: var(--muted);
      padding: 4px;
    }
    .btn-close-modal:hover { color: #1b1c1a; }
    .history-list-container {
      max-height: 380px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-bottom: 20px;
    }
    .history-row-item {
      background: #fbf9f6;
      border: 1px solid #eeebe5;
      border-radius: 12px;
      padding: 12px 16px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    .history-plan-info {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .history-dates {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 0.78rem;
      color: var(--muted);
    }
    .history-modal-footer {
      display: flex;
      justify-content: flex-end;
      border-top: 1px solid #f0ede6;
      padding-top: 16px;
    }

    /* Plan Admin Tab Styling */
    .plans-admin-grid {
      display: grid;
      gap: 24px;
      grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    }
    .plan-admin-card {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px solid #e7e2d8;
      border-radius: 16px;
      padding: 24px;
      background: #ffffff;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
      transition: all 0.25s ease;
    }
    .plan-admin-card:hover {
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    }
    .plan-admin-card.plan-pro {
      border: 2px solid #8f6d2d;
      background: linear-gradient(180deg, #ffffff 0%, #fdfbf7 100%);
      box-shadow: 0 8px 24px -8px rgba(143, 109, 45, 0.22);
    }
    .plan-card-top h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.55rem;
      margin: 10px 0 6px;
      color: #1b1c1a;
      letter-spacing: -0.01em;
    }
    .badge-row {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .code-tag {
      background: #f0ede6;
      color: #1b1c1a;
      border-radius: 6px;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 3px 8px;
      letter-spacing: 0.04em;
    }
    .audience-badge {
      background: #f4ede4;
      color: #6b5839;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      letter-spacing: 0.03em;
    }
    .audience-badge.pro-audience {
      background: #fef3c7;
      color: #92400e;
    }
    .plan-desc-text {
      font-size: 0.84rem;
      color: var(--muted);
      line-height: 1.45;
      margin: 6px 0 16px;
    }

    /* Price Hero Banner */
    .plan-price-hero {
      background: #fbf9f6;
      border: 1px solid #eeebe5;
      border-radius: 14px;
      padding: 16px 18px;
      margin-bottom: 20px;
    }
    .price-main-row {
      display: flex;
      align-items: baseline;
      gap: 4px;
    }
    .price-amount {
      font-size: 1.85rem;
      font-weight: 800;
      color: #1b1c1a;
      letter-spacing: -0.02em;
    }
    .price-period {
      font-size: 0.92rem;
      color: var(--muted);
      font-weight: 500;
    }
    .price-annual-sub {
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 0.76rem;
      color: #4b5563;
      margin-top: 6px;
      font-weight: 500;
    }
    .annual-icon {
      font-size: 16px;
      color: #16a34a;
    }

    /* Detailed Feature Matrix */
    .plan-details-matrix {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 22px;
      flex-grow: 1;
    }
    .matrix-section {
      background: #fdfcfb;
      border: 1px solid #eeebe5;
      border-radius: 12px;
      padding: 14px 16px;
    }
    .matrix-section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      border-bottom: 1px solid #f0ede6;
      padding-bottom: 8px;
    }
    .matrix-section-header h4 {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #1b1c1a;
      margin: 0;
    }
    .section-icon {
      font-size: 18px;
      color: #8f6d2d;
    }
    .section-icon.ai-accent {
      color: #9333ea;
    }
    .feature-checklist {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 9px;
    }
    .feature-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      font-size: 0.82rem;
      line-height: 1.35;
      color: #2c2a27;
    }
    .item-check {
      font-size: 17px;
      color: #16a34a;
      flex-shrink: 0;
      margin-top: 1px;
    }
    .item-cross {
      font-size: 17px;
      color: #9ca3af;
      flex-shrink: 0;
      margin-top: 1px;
    }
    .feature-item.item-disabled {
      color: #9ca3af;
    }
    .feature-item.item-disabled strong {
      color: #6b7280;
    }

    /* Actions Toolbar */
    .plan-admin-actions {
      display: flex;
      gap: 8px;
      padding-top: 12px;
      border-top: 1px solid #f0ede6;
    }
    .btn-plan-tool {
      flex: 1;
      padding: 10px 8px;
      font-size: 0.68rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      background: #ffffff;
      border: 1px solid #e5e0d8;
      border-radius: 8px;
      color: #333;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .btn-plan-tool .material-symbols-outlined {
      font-size: 16px;
    }
    .btn-plan-tool:hover {
      background: #f7f5f1;
      border-color: #d1c9be;
    }
    .btn-plan-tool.btn-plan-danger:hover {
      background: #fef2f2;
      border-color: #fca5a5;
      color: #b91c1c;
    }
  `],
})
export class PlatformAdminComponent implements OnInit {
  private readonly admin = inject(AdminService);
  private readonly notifications = inject(NotificationService);
  private readonly fb = inject(FormBuilder);

  tab: 'tenants' | 'plans' = 'tenants';
  tenants: PlatformTenant[] = [];
  plans: SubscriptionPlan[] = [];
  selectedPlanByTenant: Record<number, string> = {};
  selectedHistoryTenant: PlatformTenant | null = null;
  historyRecords: SubscriptionRecord[] = [];

  showTenantForm = false;
  showPlanForm = false;
  loading = false;
  error = '';

  // Interactive Search & Filter state
  searchQuery = '';
  statusFilter: 'ALL' | 'ACTIVE' | 'TRIAL' | 'SUSPENDED' | 'REQUESTS' = 'ALL';

  readonly tenantForm = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    plan_code: ['BASIC', [Validators.required]],
    admin_email: ['', [Validators.email]],
    admin_first_name: [''],
    admin_last_name: [''],
    admin_password: [''],
  });

  readonly planForm = this.fb.nonNullable.group({
    code: ['', [Validators.required, Validators.minLength(2)]],
    name: ['', [Validators.required, Validators.minLength(2)]],
    price_monthly: [199, [Validators.required, Validators.min(0)]],
    price_annual: [1990, [Validators.required, Validators.min(0)]],
    max_active_branches: [2, [Validators.required, Validators.min(1)]],
    generative_reports_enabled: [false],
    is_active: [true],
  });

  get activeTenantsCount(): number {
    return this.tenants.filter((t) => t.status === 'ACTIVE' && !t.is_expired).length;
  }

  get trialTenantsCount(): number {
    return this.tenants.filter((t) => t.is_trial).length;
  }

  get suspendedTenantsCount(): number {
    return this.tenants.filter((t) => t.status === 'SUSPENDED' || t.is_expired).length;
  }

  get reactivationRequestsCount(): number {
    return this.tenants.filter((t) => t.reactivation_requested).length;
  }

  get filteredTenants(): PlatformTenant[] {
    const q = this.searchQuery.trim().toLowerCase();
    return this.tenants.filter((t) => {
      const matchesSearch =
        !q ||
        t.name.toLowerCase().includes(q) ||
        t.id.toString().includes(q) ||
        (t.active_subscription?.plan?.name && t.active_subscription.plan.name.toLowerCase().includes(q));

      if (!matchesSearch) return false;

      if (this.statusFilter === 'ALL') return true;
      if (this.statusFilter === 'ACTIVE') return t.status === 'ACTIVE' && !t.is_expired;
      if (this.statusFilter === 'TRIAL') return !!t.is_trial;
      if (this.statusFilter === 'SUSPENDED') return t.status === 'SUSPENDED' || t.is_expired;
      if (this.statusFilter === 'REQUESTS') return !!t.reactivation_requested;

      return true;
    });
  }

  getInitials(name: string): string {
    if (!name) return 'FS';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.admin.platformPlans().subscribe({
      next: (res) => {
        this.plans = res.items || [];
      },
      error: () => undefined,
    });
    this.admin.platformTenants().subscribe({
      next: (res) => {
        this.tenants = res.items || [];
      },
      error: () => undefined,
    });
  }

  createTenant(): void {
    if (this.tenantForm.invalid) return;
    this.loading = true;
    const raw = this.tenantForm.getRawValue();
    this.admin
      .createPlatformTenant({
        name: raw.name.trim(),
        plan_code: raw.plan_code,
        admin_email: raw.admin_email.trim() || undefined,
        admin_first_name: raw.admin_first_name.trim() || undefined,
        admin_last_name: raw.admin_last_name.trim() || undefined,
        admin_password: raw.admin_password || undefined,
      })
      .subscribe({
        next: () => {
          this.loading = false;
          this.showTenantForm = false;
          this.tenantForm.reset({ name: '', plan_code: 'BASIC', admin_email: '', admin_first_name: '', admin_last_name: '', admin_password: '' });
          this.notifications.success('Empresa registrada correctamente.');
          this.loadAll();
        },
        error: (err: unknown) => {
          this.loading = false;
          this.error = this.extractError(err, 'No se pudo registrar la empresa.');
        },
      });
  }

  assignPlan(tenant: PlatformTenant): void {
    const planCode =
      this.selectedPlanByTenant[tenant.id] ||
      tenant.requested_plan_code ||
      tenant.active_subscription?.plan?.code ||
      'BASIC';
    this.admin.assignPlatformSubscription(tenant.id, planCode).subscribe({
      next: () => {
        this.notifications.success(`Suscripción ${planCode} activada para ${tenant.name}.`);
        this.loadAll();
      },
      error: (err: unknown) => {
        this.error = this.extractError(err, 'No se pudo actualizar la suscripción.');
      },
    });
  }

  renewSubscription(tenant: PlatformTenant): void {
    this.admin.renewPlatformSubscription(tenant.id).subscribe({
      next: () => {
        this.notifications.success(`Suscripción de ${tenant.name} renovada por 30 días.`);
        this.loadAll();
      },
      error: (err: unknown) => {
        this.error = this.extractError(err, 'No se pudo renovar la suscripción.');
      },
    });
  }

  pauseSubscription(tenant: PlatformTenant): void {
    this.admin.pausePlatformSubscription(tenant.id).subscribe({
      next: () => {
        this.notifications.success(`Suscripción de ${tenant.name} pausada.`);
        this.loadAll();
      },
      error: (err: unknown) => {
        this.error = this.extractError(err, 'No se pudo pausar la suscripción.');
      },
    });
  }

  resumeSubscription(tenant: PlatformTenant): void {
    this.admin.resumePlatformSubscription(tenant.id).subscribe({
      next: () => {
        this.notifications.success(`Suscripción de ${tenant.name} reanudada.`);
        this.loadAll();
      },
      error: (err: unknown) => {
        this.error = this.extractError(err, 'No se pudo reanudar la suscripción.');
      },
    });
  }

  toggleTenantStatus(tenant: PlatformTenant): void {
    const nextStatus = tenant.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE';
    this.admin.updatePlatformTenantStatus(tenant.id, nextStatus).subscribe({
      next: () => {
        this.notifications.success(`Estado de ${tenant.name} cambiado a ${nextStatus}.`);
        this.loadAll();
      },
      error: (err: unknown) => {
        this.error = this.extractError(err, 'No se pudo cambiar el estado de la empresa.');
      },
    });
  }

  viewHistory(tenant: PlatformTenant): void {
    this.selectedHistoryTenant = tenant;
    this.admin.platformTenantSubscriptionHistory(tenant.id).subscribe({
      next: (res) => {
        this.historyRecords = res.items || [];
      },
      error: () => {
        this.historyRecords = [];
      },
    });
  }

  createPlan(): void {
    if (this.planForm.invalid) return;
    this.loading = true;
    const raw = this.planForm.getRawValue();
    this.admin.createPlatformPlan(raw).subscribe({
      next: () => {
        this.loading = false;
        this.showPlanForm = false;
        this.planForm.reset({ code: '', name: '', max_active_branches: 2, generative_reports_enabled: false, is_active: true });
        this.notifications.success('Plan creado correctamente.');
        this.loadAll();
      },
      error: (err: unknown) => {
        this.loading = false;
        this.error = this.extractError(err, 'No se pudo crear el plan.');
      },
    });
  }

  togglePlanAI(plan: SubscriptionPlan): void {
    this.admin.updatePlatformPlan(plan.id, { generative_reports_enabled: !plan.generative_reports_enabled }).subscribe({
      next: () => {
        this.notifications.success(`Plan ${plan.name} actualizado.`);
        this.loadAll();
      },
    });
  }

  bumpPlanBranches(plan: SubscriptionPlan, delta: number): void {
    this.admin.updatePlatformPlan(plan.id, { max_active_branches: Math.max(1, plan.max_active_branches + delta) }).subscribe({
      next: () => {
        this.notifications.success(`Límite de sucursales actualizado para ${plan.name}.`);
        this.loadAll();
      },
    });
  }

  togglePlanActive(plan: SubscriptionPlan): void {
    this.admin.updatePlatformPlan(plan.id, { is_active: !plan.is_active }).subscribe({
      next: () => {
        this.notifications.success(`Estado del plan ${plan.name} actualizado.`);
        this.loadAll();
      },
    });
  }

  getPlanAudience(code: string): string {
    switch (code?.toUpperCase()) {
      case 'BASIC':
        return 'Boutiques & Retail Local';
      case 'PROFESSIONAL':
        return 'Cadenas & Franquicias';
      case 'ENTERPRISE':
        return 'Grandes Corporativos';
      default:
        return 'Plan Comercial';
    }
  }

  getPlanDescription(code: string): string {
    switch (code?.toUpperCase()) {
      case 'BASIC':
        return 'Ideal para boutiques y tiendas de moda independientes que requieren control ágil de inventario físico, ventas POS y catálogo web.';
      case 'PROFESSIONAL':
        return 'Para marcas consolidadas y cadenas que requieren analítica predictiva de demanda, segmentación de clientes y Asistente IA Sofía.';
      default:
        return 'Plan comercial diseñado para operaciones y requerimientos específicos de escala.';
    }
  }

  private extractError(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const detail = error.error?.detail;
      if (typeof detail === 'string') return detail;
      if (typeof detail?.message === 'string') return detail.message;
    }
    return fallback;
  }
}
