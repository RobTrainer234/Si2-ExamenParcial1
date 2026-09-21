import { Component, inject, OnInit } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, forkJoin, switchMap } from 'rxjs';

import { AdminService } from '../../core/admin/admin.service';
import { DashboardFilters, DashboardReport, ProductSummary, Promotion, PromotionInput, ReportAssistantIntent, ReportAssistantResponse, ReportExportFormat } from '../../core/models/admin.models';

export interface AssistantInsightCard {
  title: string;
  primaryMetric: string;
  secondaryMetric?: string;
  badge?: string;
  badgeType?: 'gold' | 'emerald' | 'blue' | 'purple' | 'amber' | 'critical';
  icon: string;
}

export interface ChannelDonutSlice {
  channel: string;
  label: string;
  share: number;
  color: string;
  dashArray: string;
  dashOffset: string;
}

@Component({
  standalone: true,
  imports: [CurrencyPipe, DatePipe, FormsModule],
  template: `
    <section class="operations-page analytics-dashboard">
      <!-- Encabezado Principal del Dashboard -->
      <div class="dashboard-header-banner">
        <div class="dashboard-header-text">
          <div class="dashboard-tag">
            <span class="material-symbols-outlined">insights</span>
            <span>Panel Ejecutivo · Ciclo 3</span>
          </div>
          <h2>Dashboard Comercial & Inteligencia de Negocio</h2>
          <p class="dashboard-subtitle">
            Monitoreo en tiempo real de ingresos, ticket promedio, inventario multi-sucursal y análisis predictivo con Sofía IA Copilot.
          </p>
        </div>
        <div class="dashboard-header-actions">
          <button class="button button-dark refresh-btn" (click)="reload()" [disabled]="isLoadingPage">
            <span class="material-symbols-outlined" [class.spinning]="isLoadingPage">sync</span>
            {{ isLoadingPage ? 'Cargando datos…' : 'Actualizar métricas' }}
          </button>
        </div>
      </div>

      @if (message) {
        <div class="dashboard-alert-banner" [class.alert-error]="messageType === 'error'" [class.alert-success]="messageType === 'success'">
          <span class="material-symbols-outlined">{{ messageType === 'error' ? 'error' : 'check_circle' }}</span>
          <span>{{ message }}</span>
        </div>
      }

      <!-- Barra de Filtros y Presets de Tiempo -->
      <section class="dashboard-filter-card">
        <div class="filter-top-row">
          <div class="filter-preset-group" role="group" aria-label="Presets rápidos de tiempo">
            <span class="preset-label">Periodo:</span>
            <button type="button" class="preset-chip" [class.active]="activePreset === 'all'" (click)="setPreset('all')">
              <span class="material-symbols-outlined">history</span> Todo
            </button>
            <button type="button" class="preset-chip" [class.active]="activePreset === 'today'" (click)="setPreset('today')">
              <span class="material-symbols-outlined">today</span> Hoy
            </button>
            <button type="button" class="preset-chip" [class.active]="activePreset === 'week'" (click)="setPreset('week')">
              <span class="material-symbols-outlined">date_range</span> Últimos 7 días
            </button>
            <button type="button" class="preset-chip" [class.active]="activePreset === 'month'" (click)="setPreset('month')">
              <span class="material-symbols-outlined">calendar_month</span> Este mes
            </button>
          </div>

          <div class="export-button-group">
            <span class="export-label">Exportar:</span>
            <button class="export-btn" type="button" (click)="downloadReport('xlsx')" [disabled]="isExporting" title="Descargar reporte en formato Excel">
              <span class="material-symbols-outlined xls-icon">table_view</span>
              <span>{{ exportLabel('xlsx') }}</span>
            </button>
            <button class="export-btn" type="button" (click)="downloadReport('pdf')" [disabled]="isExporting" title="Descargar informe ejecutivo en PDF">
              <span class="material-symbols-outlined pdf-icon">picture_as_pdf</span>
              <span>{{ exportLabel('pdf') }}</span>
            </button>
          </div>
        </div>

        <form class="custom-filters-form" (ngSubmit)="reloadDashboard()">
          <div class="filter-field">
            <label for="filterStartDate">Desde</label>
            <input id="filterStartDate" type="date" name="startDate" [(ngModel)]="filters.start_date" (change)="activePreset = 'all'" [disabled]="isLoadingDashboard">
          </div>
          <div class="filter-field">
            <label for="filterEndDate">Hasta</label>
            <input id="filterEndDate" type="date" name="endDate" [(ngModel)]="filters.end_date" (change)="activePreset = 'all'" [disabled]="isLoadingDashboard">
          </div>
          <div class="filter-field">
            <label for="filterBranch">Sucursal</label>
            <select id="filterBranch" name="branchId" [(ngModel)]="filters.branch_id" [disabled]="isLoadingDashboard">
              <option [ngValue]="0">Todas las sucursales</option>
              @for (branch of branches; track branch.id) {
                <option [ngValue]="branch.id">{{ branch.name }}</option>
              }
            </select>
          </div>
          <div class="filter-action">
            <button class="button button-dark apply-filter-btn" type="submit" [disabled]="isLoadingDashboard">
              <span class="material-symbols-outlined">filter_alt</span>
              {{ isLoadingDashboard ? 'Aplicando…' : 'Aplicar filtros' }}
            </button>
          </div>
        </form>
      </section>

      <!-- Estado de Carga / Error de Métricas -->
      @if (isLoadingPage && !dashboard) {
        <div class="dashboard-state dashboard-state-loading">
          <span class="material-symbols-outlined spinning">query_stats</span>
          <strong>Cargando métricas e indicadores de negocio…</strong>
          <small>Sincronizando reportes de ventas, inventario y sucursales.</small>
        </div>
      } @else if (!dashboard && dashboardLoadFailed) {
        <div class="dashboard-state dashboard-state-error">
          <span class="material-symbols-outlined">error</span>
          <strong>No se pudieron cargar los datos del dashboard.</strong>
          <small>Revisa la conexión o intenta actualizar nuevamente.</small>
        </div>
      } @else if (dashboard) {
        <!-- Tarjetas KPI Principales de Alto Nivel -->
        <section class="kpi-metrics-grid" aria-label="Indicadores clave de rendimiento">
          <!-- KPI 1: Ingresos Totales -->
          <div class="kpi-luxury-card">
            <div class="kpi-card-header">
              <div class="kpi-icon-wrap revenue-icon">
                <span class="material-symbols-outlined">payments</span>
              </div>
              <span class="kpi-badge-tag">Ingresos</span>
            </div>
            <div class="kpi-value-block">
              <span class="kpi-number">{{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</span>
              <span class="kpi-caption">Neto después de promociones</span>
            </div>
            <div class="kpi-footer-metric">
              <span>Subtotal: {{ dashboard.revenue.subtotal | currency:'BOB':'symbol':'1.0-0' }}</span>
              <span class="kpi-discount-pill">-{{ discountPercent }}% desc.</span>
            </div>
          </div>

          <!-- KPI 2: Ventas / Órdenes -->
          <div class="kpi-luxury-card">
            <div class="kpi-card-header">
              <div class="kpi-icon-wrap orders-icon">
                <span class="material-symbols-outlined">receipt_long</span>
              </div>
              <span class="kpi-badge-tag">Transacciones</span>
            </div>
            <div class="kpi-value-block">
              <span class="kpi-number">{{ dashboard.revenue.sales_count }}</span>
              <span class="kpi-caption">Órdenes confirmadas</span>
            </div>
            <div class="kpi-footer-metric">
              <span>Periodo: {{ dashboardRangeLabel }}</span>
            </div>
          </div>

          <!-- KPI 3: Ticket Promedio -->
          <div class="kpi-luxury-card">
            <div class="kpi-card-header">
              <div class="kpi-icon-wrap ticket-icon">
                <span class="material-symbols-outlined">trending_up</span>
              </div>
              <span class="kpi-badge-tag">Ticket Promedio</span>
            </div>
            <div class="kpi-value-block">
              <span class="kpi-number">{{ averageTicket | currency:'BOB':'symbol':'1.2-2' }}</span>
              <span class="kpi-caption">Promedio por compra</span>
            </div>
            <div class="kpi-footer-metric">
              <span>Rentabilidad comercial</span>
            </div>
          </div>

          <!-- KPI 4: Alertas de Inventario Crítico -->
          <div class="kpi-luxury-card" [class.has-critical]="criticalStockCount > 0">
            <div class="kpi-card-header">
              <div class="kpi-icon-wrap stock-icon">
                <span class="material-symbols-outlined">warning</span>
              </div>
              <span class="kpi-badge-tag">Inventario</span>
            </div>
            <div class="kpi-value-block">
              <span class="kpi-number">{{ dashboard.low_stock.length }}</span>
              <span class="kpi-caption">Productos bajo umbral</span>
            </div>
            <div class="kpi-footer-metric">
              <span class="stock-critical-pill">{{ criticalStockCount }} en stock crítico (≤ 2 un.)</span>
            </div>
          </div>
        </section>

        <!-- Copilot IA: Asistente Sofía para Análisis Comercial -->
        <section class="copilot-ai-panel" aria-labelledby="copilot-title">
          <div class="copilot-panel-header">
            <div class="copilot-header-brand">
              <div class="copilot-avatar">
                <span class="material-symbols-outlined">auto_awesome</span>
              </div>
              <div>
                <h3 id="copilot-title">Sofía Copilot IA · Inteligencia de Negocio</h3>
                <p>Formula preguntas en lenguaje natural o por voz para obtener diagnósticos y recomendaciones de abastecimiento.</p>
              </div>
            </div>
            <div class="copilot-status-badge">
              <span class="live-dot"></span>
              <span>{{ assistantResult ? assistantProviderLabel : 'Motor Inteligente Local · En línea' }}</span>
            </div>
          </div>

          <!-- Chips de Consulta Rápida -->
          <div class="quick-prompts-container">
            <span class="quick-prompts-title">Consultas rápidas recomendadas:</span>
            <div class="quick-prompts-chips">
              @for (prompt of quickPrompts; track prompt) {
                <button type="button" class="quick-prompt-chip" (click)="askQuickPrompt(prompt)" [disabled]="isAssistantLoading">
                  <span class="material-symbols-outlined">chat</span>
                  <span>{{ prompt }}</span>
                </button>
              }
            </div>
          </div>

          <!-- Formulario de Consulta Copilot -->
          <form class="copilot-form" (ngSubmit)="askAssistant()">
            <div class="copilot-input-wrapper">
              <textarea
                id="copilotPrompt"
                name="copilotPrompt"
                rows="3"
                [(ngModel)]="assistantPrompt"
                [disabled]="isAssistantLoading"
                placeholder="Escribe tu consulta ejecutiva o selecciona una de las consultas rápidas de arriba..."
              ></textarea>
            </div>

            <div class="copilot-actions-bar">
              <div class="copilot-actions-left">
                @if (isListeningVoice) {
                  <div class="voice-listening-wave">
                    <span class="wave-bar"></span>
                    <span class="wave-bar"></span>
                    <span class="wave-bar"></span>
                    <span>Escuchando dictado de voz...</span>
                  </div>
                } @else {
                  <small class="copilot-tip">El asistente analiza ingresos, canales, reservas y bajo stock según tus filtros actuales.</small>
                }
              </div>

              <div class="copilot-actions-right">
                @if (isVoiceSupported) {
                  <button
                    type="button"
                    class="voice-command-btn"
                    [class.listening]="isListeningVoice"
                    (click)="toggleVoiceCommand()"
                    title="Dictar consulta por micrófono"
                  >
                    <span class="material-symbols-outlined">{{ isListeningVoice ? 'mic' : 'mic_none' }}</span>
                    <span>{{ isListeningVoice ? 'Detener dictado' : 'Dictar por voz' }}</span>
                  </button>
                }
                <button class="button button-dark copilot-submit-btn" type="submit" [disabled]="isAssistantLoading || !assistantPrompt.trim()">
                  <span class="material-symbols-outlined" [class.spinning]="isAssistantLoading">auto_awesome</span>
                  {{ isAssistantLoading ? 'Analizando datos…' : 'Consultar a Sofía IA' }}
                </button>
              </div>
            </div>
          </form>

          @if (assistantError) {
            <div class="dashboard-alert-banner alert-error">
              <span class="material-symbols-outlined">error</span>
              <span>{{ assistantError }}</span>
            </div>
          }

          @if (isAssistantLoading) {
            <div class="copilot-loading-card">
              <span class="material-symbols-outlined spinning">psychology</span>
              <strong>Generando síntesis y análisis ejecutivo…</strong>
              <small>Sofía IA está cruzando ventas, inventario y métricas para formular recomendaciones.</small>
            </div>
          } @else if (assistantResult) {
            <div class="copilot-result-card">
              <div class="copilot-narrative-box">
                <div class="narrative-icon">
                  <span class="material-symbols-outlined">psychology</span>
                </div>
                <div class="narrative-body">
                  <h4>Diagnóstico Ejecutivo</h4>
                  <p>{{ assistantResult.narrative }}</p>
                </div>
              </div>

              <div class="copilot-meta-row">
                <span class="meta-tag">Intención: <strong>{{ assistantIntentLabel(assistantResult.intent) }}</strong></span>
                <span class="meta-tag">Modo: <strong>{{ assistantResult.fallback_used ? 'Fallback usado' : 'Proveedor principal' }}</strong></span>
              </div>

              @if (assistantCards.length) {
                <div class="copilot-cards-grid">
                  @for (card of assistantCards; track card.title + $index) {
                    <div class="copilot-insight-card">
                      <div class="insight-card-top">
                        <div class="insight-icon-bubble">
                          <span class="material-symbols-outlined">{{ card.icon }}</span>
                        </div>
                        @if (card.badge) {
                          <span class="insight-badge" [class]="'badge-' + (card.badgeType || 'gold')">{{ card.badge }}</span>
                        }
                      </div>
                      <div class="insight-card-content">
                        <span class="insight-title">{{ card.title }}</span>
                        <strong class="insight-primary-value">{{ card.primaryMetric }}</strong>
                        @if (card.secondaryMetric) {
                          <span class="insight-secondary-value">{{ card.secondaryMetric }}</span>
                        }
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
          }
        </section>

        <!-- Visualizaciones Analíticas & Gráficos -->
        @if (hasDashboardData) {
          <section class="analytics-visual-grid">
            <!-- Tarjeta: Composición de Ventas (Medidor Radial Semi-Circular de Lujo) -->
            <article class="visual-card financial-gauge-card">
              <div class="visual-card-heading">
                <div>
                  <span class="card-eyebrow">Finanzas</span>
                  <h3>Composición de ventas</h3>
                </div>
                <span class="card-chip">{{ dashboard.revenue.sales_count }} ventas</span>
              </div>

              <div class="financial-showcase-layout">
                <!-- SVG Radial Semi-Circle Gauge -->
                <div class="radial-gauge-container">
                  <svg class="radial-gauge-svg" viewBox="0 0 160 92" width="160" height="92" aria-label="Medidor de margen comercial">
                    <defs>
                      <linearGradient id="financialGaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#b8924a"/>
                        <stop offset="60%" stop-color="#d4af37"/>
                        <stop offset="100%" stop-color="#10b981"/>
                      </linearGradient>
                    </defs>
                    <path
                      d="M 15 80 A 65 65 0 0 1 145 80"
                      fill="none"
                      stroke="rgba(229, 224, 216, 0.35)"
                      stroke-width="16"
                      stroke-linecap="round"
                    />
                    <path
                      d="M 15 80 A 65 65 0 0 1 145 80"
                      fill="none"
                      stroke="url(#financialGaugeGrad)"
                      stroke-width="16"
                      stroke-linecap="round"
                      stroke-dasharray="204.2"
                      [attr.stroke-dashoffset]="gaugeArcOffset"
                      class="gauge-active-arc"
                    />
                  </svg>
                  <div class="gauge-center-stat">
                    <strong>{{ revenueNetPercent }}%</strong>
                    <small>Margen Neto</small>
                  </div>
                </div>

                <div class="gauge-metrics-sidebar">
                  <div class="revenue-big-display">
                    <strong>{{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</strong>
                    <small>Ingreso neto recaudado</small>
                  </div>
                  <div class="visual-progress-track" role="progressbar" [attr.aria-valuenow]="revenueNetPercent" aria-valuemin="0" aria-valuemax="100">
                    <span class="progress-fill-net" [style.width.%]="revenueNetPercent" title="Ingreso neto"></span>
                    <span class="progress-fill-discount" [style.width.%]="discountPercent" title="Descuentos aplicados"></span>
                  </div>
                  <div class="progress-legend">
                    <div class="legend-item"><span class="legend-dot dot-net"></span><span>Ingreso Neto ({{ revenueNetPercent }}%)</span></div>
                    <div class="legend-item"><span class="legend-dot dot-discount"></span><span>Descuentos ({{ discountPercent }}%)</span></div>
                  </div>
                </div>
              </div>
            </article>

            <!-- Tarjeta: Canales de Venta (Gráfico Donut Radial de Omnicanalidad) -->
            <article class="visual-card omnichannel-donut-card">
              <div class="visual-card-heading">
                <div>
                  <span class="card-eyebrow">Omnicanalidad</span>
                  <h3>Participación de venta</h3>
                </div>
                <span class="card-chip">{{ dashboard.sales_by_channel.length }} canales</span>
              </div>

              <div class="donut-chart-showcase">
                <!-- SVG Donut Chart -->
                <div class="donut-svg-wrapper">
                  <svg class="donut-chart-svg" viewBox="0 0 160 160" width="160" height="160" aria-label="Gráfico circular de distribución de ventas">
                    <circle
                      cx="80"
                      cy="80"
                      r="60"
                      fill="none"
                      stroke="rgba(229, 224, 216, 0.35)"
                      stroke-width="18"
                    />
                    @for (slice of channelDonutSlices; track slice.channel) {
                      <circle
                        cx="80"
                        cy="80"
                        r="60"
                        fill="none"
                        [attr.stroke]="slice.color"
                        stroke-width="18"
                        stroke-linecap="round"
                        [attr.stroke-dasharray]="slice.dashArray"
                        [attr.stroke-dashoffset]="slice.dashOffset"
                        transform="rotate(-90 80 80)"
                        class="donut-slice"
                      />
                    }
                  </svg>
                  <div class="donut-center-badge">
                    <span class="material-symbols-outlined donut-center-icon">hub</span>
                    <strong>{{ dominantChannelShare }}%</strong>
                    <small>{{ dominantChannelName }}</small>
                  </div>
                </div>

                <!-- Channel Metric Breakdown Cards -->
                <div class="channel-breakdown-list">
                  @for (item of dashboard.sales_by_channel; track item.channel) {
                    <div class="channel-breakdown-row" [class.highlighted]="item.channel === dominantChannelCode">
                      <div class="channel-main-info">
                        <span class="channel-color-dot" [style.background]="getChannelColor(item.channel)"></span>
                        <span class="material-symbols-outlined channel-glyph">{{ channelIcon(item.channel) }}</span>
                        <div>
                          <strong>Canal {{ channelLabel(item.channel) }}</strong>
                          <small>{{ item.sales_count }} ventas concretadas</small>
                        </div>
                      </div>
                      <div class="channel-share-block">
                        <span class="channel-percent-pill">{{ percent(item.total, dashboard.revenue.total) }}%</span>
                        <strong>{{ item.total | currency:'BOB':'symbol':'1.0-0' }}</strong>
                      </div>
                    </div>
                  }
                  @empty {
                    <p class="empty-notice">No se registran ventas por canal en el periodo seleccionado.</p>
                  }
                </div>
              </div>
            </article>

            <!-- Tarjeta: Ventas por Sucursal -->
            <article class="visual-card">
              <div class="visual-card-heading">
                <div>
                  <span class="card-eyebrow">Puntos de Venta</span>
                  <h3>Ventas por sucursal</h3>
                </div>
              </div>
              <div class="branch-bars-list">
                @for (item of dashboard.sales_by_branch; track item.branch_id || item.branch_name) {
                  <div class="branch-bar-row">
                    <div class="branch-label-wrap">
                      <span class="material-symbols-outlined">store</span>
                      <strong>{{ item.branch_name }}</strong>
                    </div>
                    <div class="branch-bar-container">
                      <div class="branch-bar-track">
                        <div class="branch-bar-fill" [style.width.%]="percent(item.total, branchMaxTotal)"></div>
                      </div>
                      <span class="branch-total-badge">{{ item.total | currency:'BOB':'symbol':'1.0-0' }}</span>
                    </div>
                  </div>
                }
                @empty {
                  <p class="empty-notice">Sin ventas registradas por sucursal.</p>
                }
              </div>
            </article>

            <!-- Tarjeta: Estado de Reservas de Probador -->
            <article class="visual-card">
              <div class="visual-card-heading">
                <div>
                  <span class="card-eyebrow">Probador Virtual</span>
                  <h3>Estado de reservas</h3>
                </div>
                <span class="card-chip">{{ totalReservations }} reservas totales</span>
              </div>
              <div class="reservations-funnel-list">
                @for (item of dashboard.reservations; track item.status) {
                  <div class="funnel-row">
                    <div class="funnel-label">
                      <span class="status-indicator" [class]="'indicator-' + item.status.toLowerCase()"></span>
                      <span>{{ reservationStatusLabel(item.status) }}</span>
                    </div>
                    <div class="funnel-bar-container">
                      <div class="funnel-bar-fill" [class]="'fill-' + item.status.toLowerCase()" [style.width.%]="percent(item.count, reservationMaxCount)"></div>
                    </div>
                    <strong class="funnel-count">{{ item.count }}</strong>
                  </div>
                }
                @empty {
                  <p class="empty-notice">Sin reservas de probador en este periodo.</p>
                }
              </div>
            </article>

            <!-- Tarjeta: Top 5 Productos Más Vendidos -->
            <article class="visual-card full-width-card">
              <div class="visual-card-heading">
                <div>
                  <span class="card-eyebrow">Ranking Comercial</span>
                  <h3>Productos más vendidos</h3>
                </div>
              </div>
              <div class="top-products-grid">
                @for (item of dashboard.top_products.slice(0, 5); track item.product_id; let i = $index) {
                  <div class="top-product-luxury-card">
                    <div class="rank-medal" [class.rank-gold]="i === 0" [class.rank-silver]="i === 1" [class.rank-bronze]="i === 2">
                      {{ i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '#' + (i + 1) }}
                    </div>
                    <div class="top-product-details">
                      <strong>{{ item.product_name }}</strong>
                      <div class="top-product-metrics">
                        <span>{{ item.units_sold }} prendas vendidas</span>
                        <span class="metric-separator">·</span>
                        <strong>{{ item.revenue | currency:'BOB':'symbol':'1.0-0' }}</strong>
                      </div>
                      <div class="top-product-track">
                        <div class="top-product-fill" [style.width.%]="percent(item.units_sold, topProductMaxUnits)"></div>
                      </div>
                    </div>
                  </div>
                }
                @empty {
                  <p class="empty-notice">No se registraron ventas de productos en el periodo.</p>
                }
              </div>
            </article>

            <!-- Tarjeta: Alertas de Stock Semáforo -->
            <article class="visual-card full-width-card">
              <div class="visual-card-heading">
                <div>
                  <span class="card-eyebrow">Control de Almacén</span>
                  <h3>Alertas de Inventario y Reposición</h3>
                </div>
                <span class="card-chip chip-critical">{{ criticalStockCount }} productos críticos</span>
              </div>
              <div class="stock-alerts-table-wrap">
                <table class="luxury-table">
                  <thead>
                    <tr>
                      <th>Estado</th>
                      <th>Producto</th>
                      <th>SKU</th>
                      <th>Sucursal</th>
                      <th>Stock Disponible</th>
                      <th>Nivel de Alerta</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (item of dashboard.low_stock.slice(0, 6); track item.inventory_id) {
                      <tr>
                        <td>
                          <span class="stock-status-pill" [class]="stockBadgeClass(item.available_quantity)">
                            {{ stockStatusLabel(item.available_quantity) }}
                          </span>
                        </td>
                        <td><strong>{{ item.product_name }}</strong></td>
                        <td><code>{{ item.sku }}</code></td>
                        <td>{{ item.branch_name }}</td>
                        <td><strong class="stock-qty-num">{{ item.available_quantity }} un.</strong></td>
                        <td>
                          @if (item.available_quantity <= 2) {
                            <span class="alert-text-critical">Reposición inmediata requerida</span>
                          } @else {
                            <span class="alert-text-warning">Stock preventivo</span>
                          }
                        </td>
                      </tr>
                    }
                    @empty {
                      <tr>
                        <td colspan="6" class="text-center empty-notice">Todos los productos cuentan con inventario suficiente.</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </article>
          </section>

          <!-- Centro de Exportación & Previsualización de Maquetas Ejecutivas -->
          <section class="report-export-center">
            <div class="report-export-header">
              <div class="export-header-info">
                <div class="dashboard-tag">
                  <span class="material-symbols-outlined">description</span>
                  <span>Documentos Oficiales · Alta Fidelidad</span>
                </div>
                <h3>Centro de Exportación &amp; Maqueta de Informes</h3>
                <p>
                  Previsualiza la maqueta exacta de tu documento antes de descargarlo. Diseñado con tipografía editorial, monograma institucional de la boutique y validación contable.
                </p>
              </div>

              <div class="mockup-format-switcher" role="tablist" aria-label="Selector de maqueta de reporte">
                <button
                  type="button"
                  class="mockup-tab-btn"
                  [class.active]="activeReportMockup === 'pdf'"
                  (click)="setReportMockup('pdf')"
                >
                  <span class="material-symbols-outlined">picture_as_pdf</span>
                  <span>Maqueta PDF Ejecutivo</span>
                </button>
                <button
                  type="button"
                  class="mockup-tab-btn"
                  [class.active]="activeReportMockup === 'xlsx'"
                  (click)="setReportMockup('xlsx')"
                >
                  <span class="material-symbols-outlined">table_view</span>
                  <span>Maqueta Libro Excel (XLSX)</span>
                </button>
              </div>
            </div>

            <!-- CONTENIDO DE LA MAQUETA EN VIVO -->
            <div class="mockup-display-stage">
              @if (activeReportMockup === 'pdf') {
                <!-- VISTA MAQUETA PDF A4 -->
                <div class="pdf-sheet-mockup">
                  <!-- Banner Superior Oscuro -->
                  <div class="pdf-mockup-banner">
                    <div class="pdf-banner-brand">
                      <div class="pdf-brand-medallion">F</div>
                      <div>
                        <h4 class="pdf-brand-title">FASHIONSTORE ATELIER &amp; BOUTIQUE</h4>
                        <p class="pdf-brand-subtitle">INFORME EJECUTIVO DE RENDIMIENTO COMERCIAL &middot; CICLO 3</p>
                      </div>
                    </div>
                    <div class="pdf-banner-metadata">
                      <div><strong>PERIODO:</strong> {{ dashboardRangeLabel }}</div>
                      <div><strong>SUCURSAL:</strong> {{ branchFilterName }}</div>
                      <div><strong>MONEDA:</strong> Bolivianos (BOB)</div>
                      <div><strong>DOCUMENTO:</strong> Reporte Confidencial</div>
                    </div>
                  </div>

                  <!-- 4 Cajas KPI de Resumen -->
                  <div class="pdf-mockup-kpis">
                    <div class="pdf-kpi-card">
                      <span class="pdf-kpi-lbl">INGRESOS NETOS</span>
                      <strong class="pdf-kpi-val">{{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</strong>
                      <small class="pdf-kpi-sub">Subtotal: {{ dashboard.revenue.subtotal | currency:'BOB':'symbol':'1.2-2' }}</small>
                    </div>
                    <div class="pdf-kpi-card">
                      <span class="pdf-kpi-lbl">TRANSACCIONES</span>
                      <strong class="pdf-kpi-val">{{ dashboard.revenue.sales_count }}</strong>
                      <small class="pdf-kpi-sub">Ticket Prom: {{ averageTicket | currency:'BOB':'symbol':'1.2-2' }}</small>
                    </div>
                    <div class="pdf-kpi-card">
                      <span class="pdf-kpi-lbl">DESCUENTOS</span>
                      <strong class="pdf-kpi-val">{{ dashboard.revenue.discount | currency:'BOB':'symbol':'1.2-2' }}</strong>
                      <small class="pdf-kpi-sub">Tasa aplicada: {{ discountRate }}%</small>
                    </div>
                    <div class="pdf-kpi-card">
                      <span class="pdf-kpi-lbl">MARGEN COMERCIAL</span>
                      <strong class="pdf-kpi-val">{{ revenueNetPercent }}%</strong>
                      <small class="pdf-kpi-sub">Rendimiento neto</small>
                    </div>
                  </div>

                  <!-- Tablas de Ejemplo Estilizadas -->
                  <div class="pdf-mockup-section-heading">PRODUCTOS MÁS VENDIDOS (TOP PRODUCTOS)</div>
                  <div class="pdf-mockup-table-wrap">
                    <table class="pdf-mockup-table">
                      <thead>
                        <tr>
                          <th style="width: 40px; text-align: center;">#</th>
                          <th>PRENDA / ARTÍCULO</th>
                          <th style="text-align: right;">UNIDADES</th>
                          <th style="text-align: right;">TOTAL FACTURADO</th>
                          <th style="text-align: right;">CUOTA</th>
                        </tr>
                      </thead>
                      <tbody>
                        @for (p of dashboard.top_products.slice(0, 4); track p.product_id; let idx = $index) {
                          <tr>
                            <td style="text-align: center; font-weight: 700;">{{ idx === 0 ? '1 🏆' : (idx + 1) }}</td>
                            <td><strong>{{ p.product_name }}</strong></td>
                            <td style="text-align: right;">{{ p.units_sold }} unid.</td>
                            <td style="text-align: right; font-weight: 600;">{{ p.revenue | currency:'BOB':'symbol':'1.2-2' }}</td>
                            <td style="text-align: right;">{{ percent(p.revenue, dashboard.revenue.total) }}%</td>
                          </tr>
                        }
                        @empty {
                          <tr>
                            <td colspan="5" class="text-center">Sin ventas registradas en el período.</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>

                  <!-- Footer de Hoja -->
                  <div class="pdf-mockup-footer">
                    <span>FashionStore Atelier &amp; Boutique &middot; Documento de Control Confidencial</span>
                    <span>Página 1 de 1</span>
                  </div>
                </div>
              } @else {
                <!-- VISTA MAQUETA EXCEL 365 ALTA FIDELIDAD -->
                <div class="excel-workbook-mockup">
                  <!-- Barra de Título Superior de Aplicación Excel -->
                  <div class="excel-window-titlebar">
                    <div class="excel-title-left">
                      <span class="excel-app-icon">📊</span>
                      <span class="excel-file-title">FashionStore_Informe_Ejecutivo_2026.xlsx - Excel</span>
                      <span class="excel-save-badge">Guardado</span>
                    </div>
                    <div class="excel-window-controls">
                      <span>—</span>
                      <span>🗖</span>
                      <span class="excel-close-btn">✕</span>
                    </div>
                  </div>

                  <!-- Cinta de Opciones / Pestañas de Menú Excel -->
                  <div class="excel-ribbon-bar">
                    <span class="ribbon-tab active-ribbon">Inicio</span>
                    <span class="ribbon-tab">Insertar</span>
                    <span class="ribbon-tab">Disposición de página</span>
                    <span class="ribbon-tab">Fórmulas</span>
                    <span class="ribbon-tab">Datos</span>
                    <span class="ribbon-tab">Revisar</span>
                    <span class="ribbon-tab">Vista</span>
                  </div>

                  <!-- Barra de Fórmulas Dinámica de Excel -->
                  <div class="excel-formula-bar">
                    <div class="excel-name-box">
                      <span>{{ activeExcelCellName }}</span>
                      <span class="name-box-arrow">▾</span>
                    </div>
                    <div class="excel-formula-actions">
                      <span class="fx-action-btn cancel">✕</span>
                      <span class="fx-action-btn enter">✓</span>
                      <span class="excel-fx">fx</span>
                    </div>
                    <div class="excel-formula-input">
                      {{ activeExcelFormula }}
                    </div>
                  </div>

                  <!-- Cuadrícula de Celdas (Spreadsheet Grid) Reactiva por Hoja -->
                  <div class="excel-grid-container">
                    @if (activeExcelSheet === 'top_products') {
                      <!-- HOJA: Top Products -->
                      <table class="excel-mockup-table">
                        <thead>
                          <tr class="excel-header-letters">
                            <th class="excel-corner">◢</th>
                            <th class="excel-col-head">A</th>
                            <th class="excel-col-head">B</th>
                            <th class="excel-col-head">C</th>
                            <th class="excel-col-head">D</th>
                            <th class="excel-col-head">E</th>
                          </tr>
                          <tr class="excel-main-header">
                            <td class="excel-row-num">1</td>
                            <th style="text-align: center;">ID Producto</th>
                            <th>Producto / Prenda</th>
                            <th style="text-align: right;">Unidades Vendidas</th>
                            <th style="text-align: right;">Ingresos (BOB)</th>
                            <th style="text-align: right;">Cuota %</th>
                          </tr>
                        </thead>
                        <tbody>
                          @for (p of dashboard.top_products.slice(0, 5); track p.product_id; let idx = $index) {
                            <tr [class.excel-zebra]="idx % 2 === 1">
                              <td class="excel-row-num">{{ idx + 2 }}</td>
                              <td class="excel-cell excel-id-cell">{{ p.product_id }}</td>
                              <td class="excel-cell" [class.excel-active-cell]="idx === 0">
                                <strong>{{ p.product_name }}</strong>
                                @if (idx === 0) { <span class="excel-cell-handle"></span> }
                              </td>
                              <td class="excel-cell excel-qty-cell">{{ p.units_sold }}</td>
                              <td class="excel-cell excel-money-cell">{{ p.revenue | currency:'BOB':'symbol':'1.2-2' }}</td>
                              <td class="excel-cell excel-qty-cell">{{ percent(p.revenue, dashboard.revenue.total) }}%</td>
                            </tr>
                          }
                          <tr class="excel-total-row">
                            <td class="excel-row-num">{{ dashboard.top_products.slice(0, 5).length + 2 }}</td>
                            <td class="excel-cell excel-id-cell"></td>
                            <td class="excel-cell" style="font-weight: 700;">TOTAL</td>
                            <td class="excel-cell excel-qty-cell" style="font-weight: 700;">=SUM(C2:C{{ dashboard.top_products.slice(0, 5).length + 1 }})</td>
                            <td class="excel-cell excel-money-cell" style="font-weight: 700;">{{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</td>
                            <td class="excel-cell excel-qty-cell" style="font-weight: 700;">100%</td>
                          </tr>
                        </tbody>
                      </table>
                    } @else if (activeExcelSheet === 'summary') {
                      <!-- HOJA: Summary -->
                      <table class="excel-mockup-table">
                        <thead>
                          <tr class="excel-header-letters">
                            <th class="excel-corner">◢</th>
                            <th class="excel-col-head">A</th>
                            <th class="excel-col-head">B</th>
                            <th class="excel-col-head">C</th>
                            <th class="excel-col-head">D</th>
                          </tr>
                          <tr class="excel-main-header">
                            <td class="excel-row-num">1</td>
                            <th>Métrica / Indicador</th>
                            <th style="text-align: right;">Valor Registrado</th>
                            <th style="text-align: center;">Unidad</th>
                            <th>Descripción del Indicador</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td class="excel-row-num">2</td>
                            <td class="excel-cell"><strong>Total Ventas (Órdenes)</strong></td>
                            <td class="excel-cell excel-qty-cell">{{ dashboard.revenue.sales_count }}</td>
                            <td class="excel-cell" style="text-align: center;">Órdenes</td>
                            <td class="excel-cell">Total de compras confirmadas en el período auditado</td>
                          </tr>
                          <tr class="excel-zebra">
                            <td class="excel-row-num">3</td>
                            <td class="excel-cell"><strong>Subtotal Facturado Bruto</strong></td>
                            <td class="excel-cell excel-money-cell">{{ dashboard.revenue.subtotal | currency:'BOB':'symbol':'1.2-2' }}</td>
                            <td class="excel-cell" style="text-align: center;">BOB</td>
                            <td class="excel-cell">Facturación comercial bruta antes de promociones y descuentos</td>
                          </tr>
                          <tr>
                            <td class="excel-row-num">4</td>
                            <td class="excel-cell"><strong>Descuentos Promocionales</strong></td>
                            <td class="excel-cell excel-money-cell">{{ dashboard.revenue.discount | currency:'BOB':'symbol':'1.2-2' }}</td>
                            <td class="excel-cell" style="text-align: center;">BOB</td>
                            <td class="excel-cell">Ahorro total otorgado a clientes mediante promociones (CU20)</td>
                          </tr>
                          <tr class="excel-total-row">
                            <td class="excel-row-num">5</td>
                            <td class="excel-cell" style="color:#8f6d2d;"><strong>Total Ingresos Netos</strong></td>
                            <td class="excel-cell excel-money-cell excel-active-cell" style="color:#1b1c1a; font-weight:700;">
                              {{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}
                              <span class="excel-cell-handle"></span>
                            </td>
                            <td class="excel-cell" style="text-align: center; font-weight: 700;">BOB</td>
                            <td class="excel-cell" style="font-weight:700; color:#8f6d2d;">Ingresos netos consolidados efectivamente liquidados</td>
                          </tr>
                          <tr>
                            <td class="excel-row-num">6</td>
                            <td class="excel-cell"><strong>Ticket Promedio</strong></td>
                            <td class="excel-cell excel-money-cell">{{ averageTicket | currency:'BOB':'symbol':'1.2-2' }}</td>
                            <td class="excel-cell" style="text-align: center;">BOB</td>
                            <td class="excel-cell">Monto promedio facturado por transacción</td>
                          </tr>
                          <tr class="excel-zebra">
                            <td class="excel-row-num">7</td>
                            <td class="excel-cell">Fecha Desde (Filtro)</td>
                            <td class="excel-cell">{{ filters.start_date || 'Todas (Todo el historial)' }}</td>
                            <td class="excel-cell" style="text-align: center;">Filtro</td>
                            <td class="excel-cell">Límite inferior del rango de fechas evaluado</td>
                          </tr>
                          <tr>
                            <td class="excel-row-num">8</td>
                            <td class="excel-cell">Fecha Hasta (Filtro)</td>
                            <td class="excel-cell">{{ filters.end_date || 'Todas (Todo el historial)' }}</td>
                            <td class="excel-cell" style="text-align: center;">Filtro</td>
                            <td class="excel-cell">Límite superior del rango de fechas evaluado</td>
                          </tr>
                          <tr class="excel-zebra">
                            <td class="excel-row-num">9</td>
                            <td class="excel-cell">Sucursal Auditada</td>
                            <td class="excel-cell">{{ filters.branch_id || 'Todas las sucursales' }}</td>
                            <td class="excel-cell" style="text-align: center;">Filtro</td>
                            <td class="excel-cell">Alcance de sucursales físicas y digitales evaluadas</td>
                          </tr>
                        </tbody>
                      </table>
                    } @else if (activeExcelSheet === 'branches') {
                      <!-- HOJA: Branches -->
                      <table class="excel-mockup-table">
                        <thead>
                          <tr class="excel-header-letters">
                            <th class="excel-corner">◢</th>
                            <th class="excel-col-head">A</th>
                            <th class="excel-col-head">B</th>
                            <th class="excel-col-head">C</th>
                            <th class="excel-col-head">D</th>
                          </tr>
                          <tr class="excel-main-header">
                            <td class="excel-row-num">1</td>
                            <th style="text-align: center;">ID Sucursal</th>
                            <th>Sucursal</th>
                            <th style="text-align: right;">Total Ventas (Órdenes)</th>
                            <th style="text-align: right;">Facturación (BOB)</th>
                          </tr>
                        </thead>
                        <tbody>
                          @for (b of dashboard.sales_by_branch; track b.branch_id; let idx = $index) {
                            <tr [class.excel-zebra]="idx % 2 === 1">
                              <td class="excel-row-num">{{ idx + 2 }}</td>
                              <td class="excel-cell excel-id-cell">{{ b.branch_id }}</td>
                              <td class="excel-cell"><strong>{{ b.branch_name }}</strong></td>
                              <td class="excel-cell excel-qty-cell">{{ b.sales_count }}</td>
                              <td class="excel-cell excel-money-cell">{{ b.total | currency:'BOB':'symbol':'1.2-2' }}</td>
                            </tr>
                          }
                          <tr class="excel-total-row">
                            <td class="excel-row-num">{{ dashboard.sales_by_branch.length + 2 }}</td>
                            <td class="excel-cell excel-id-cell"></td>
                            <td class="excel-cell" style="font-weight: 700;">TOTAL</td>
                            <td class="excel-cell excel-qty-cell" style="font-weight: 700;">=SUM(C2:C{{ dashboard.sales_by_branch.length + 1 }})</td>
                            <td class="excel-cell excel-money-cell" style="font-weight: 700;">{{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    } @else if (activeExcelSheet === 'channels') {
                      <!-- HOJA: Channels -->
                      <table class="excel-mockup-table">
                        <thead>
                          <tr class="excel-header-letters">
                            <th class="excel-corner">◢</th>
                            <th class="excel-col-head">A</th>
                            <th class="excel-col-head">B</th>
                            <th class="excel-col-head">C</th>
                          </tr>
                          <tr class="excel-main-header">
                            <td class="excel-row-num">1</td>
                            <th>Canal de Venta</th>
                            <th style="text-align: right;">Total Ventas (Órdenes)</th>
                            <th style="text-align: right;">Facturación (BOB)</th>
                          </tr>
                        </thead>
                        <tbody>
                          @for (c of dashboard.sales_by_channel; track c.channel; let idx = $index) {
                            <tr [class.excel-zebra]="idx % 2 === 1">
                              <td class="excel-row-num">{{ idx + 2 }}</td>
                              <td class="excel-cell"><strong>{{ channelLabel(c.channel) }} ({{ c.channel }})</strong></td>
                              <td class="excel-cell excel-qty-cell">{{ c.sales_count }}</td>
                              <td class="excel-cell excel-money-cell">{{ c.total | currency:'BOB':'symbol':'1.2-2' }}</td>
                            </tr>
                          }
                          <tr class="excel-total-row">
                            <td class="excel-row-num">{{ dashboard.sales_by_channel.length + 2 }}</td>
                            <td class="excel-cell" style="font-weight: 700;">TOTAL</td>
                            <td class="excel-cell excel-qty-cell" style="font-weight: 700;">=SUM(B2:B{{ dashboard.sales_by_channel.length + 1 }})</td>
                            <td class="excel-cell excel-money-cell" style="font-weight: 700;">{{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    } @else if (activeExcelSheet === 'reservations') {
                      <!-- HOJA: Reservations -->
                      <table class="excel-mockup-table">
                        <thead>
                          <tr class="excel-header-letters">
                            <th class="excel-corner">◢</th>
                            <th class="excel-col-head">A</th>
                            <th class="excel-col-head">B</th>
                          </tr>
                          <tr class="excel-main-header">
                            <td class="excel-row-num">1</td>
                            <th>Estado de Reserva</th>
                            <th style="text-align: right;">Cantidad Registrada</th>
                          </tr>
                        </thead>
                        <tbody>
                          @for (r of dashboard.reservations; track r.status; let idx = $index) {
                            <tr [class.excel-zebra]="idx % 2 === 1">
                              <td class="excel-row-num">{{ idx + 2 }}</td>
                              <td class="excel-cell"><strong>{{ reservationStatusLabel(r.status) }} ({{ r.status }})</strong></td>
                              <td class="excel-cell excel-qty-cell">{{ r.count }}</td>
                            </tr>
                          }
                          <tr class="excel-total-row">
                            <td class="excel-row-num">{{ dashboard.reservations.length + 2 }}</td>
                            <td class="excel-cell" style="font-weight: 700;">TOTAL RESERVAS</td>
                            <td class="excel-cell excel-qty-cell" style="font-weight: 700;">=SUM(B2:B{{ dashboard.reservations.length + 1 }})</td>
                          </tr>
                        </tbody>
                      </table>
                    } @else if (activeExcelSheet === 'low_stock') {
                      <!-- HOJA: Low Stock -->
                      <table class="excel-mockup-table">
                        <thead>
                          <tr class="excel-header-letters">
                            <th class="excel-corner">◢</th>
                            <th class="excel-col-head">A</th>
                            <th class="excel-col-head">B</th>
                            <th class="excel-col-head">C</th>
                            <th class="excel-col-head">D</th>
                            <th class="excel-col-head">E</th>
                          </tr>
                          <tr class="excel-main-header">
                            <td class="excel-row-num">1</td>
                            <th style="text-align: center;">ID Inventario</th>
                            <th>Sucursal</th>
                            <th>Producto / Prenda</th>
                            <th>Código SKU</th>
                            <th style="text-align: right;">Stock Disponible</th>
                          </tr>
                        </thead>
                        <tbody>
                          @for (item of dashboard.low_stock.slice(0, 6); track item.inventory_id; let idx = $index) {
                            <tr [class.excel-zebra]="idx % 2 === 1">
                              <td class="excel-row-num">{{ idx + 2 }}</td>
                              <td class="excel-cell excel-id-cell">{{ item.inventory_id }}</td>
                              <td class="excel-cell">{{ item.branch_name }}</td>
                              <td class="excel-cell"><strong>{{ item.product_name }}</strong></td>
                              <td class="excel-cell" style="font-family: Consolas, monospace;">{{ item.sku }}</td>
                              <td class="excel-cell excel-qty-cell" [style.background]="item.available_quantity <= 2 ? '#fee2e2' : '#fef3c7'" [style.color]="item.available_quantity <= 2 ? '#991b1b' : '#92400e'" style="font-weight: 700;">
                                {{ item.available_quantity }} unid.
                              </td>
                            </tr>
                          }
                        </tbody>
                      </table>
                    }
                  </div>

                  <!-- Pestañas de Hojas Inferiores con Selector Interactivo y Código de Color -->
                  <div class="excel-sheet-tabs-bar">
                    <div class="sheet-tabs-scroll-controls">
                      <span class="tab-scroll-arrow">◀</span>
                      <span class="tab-scroll-arrow">▶</span>
                    </div>
                    <div class="sheet-tabs-list">
                      <button type="button" class="sheet-tab tab-summary" [class.active-sheet]="activeExcelSheet === 'summary'" (click)="setExcelSheet('summary')">
                        <span class="tab-indicator" style="background:#b8924a;"></span>
                        <span>Summary</span>
                      </button>
                      <button type="button" class="sheet-tab tab-products" [class.active-sheet]="activeExcelSheet === 'top_products'" (click)="setExcelSheet('top_products')">
                        <span class="tab-indicator" style="background:#1b1c1a;"></span>
                        <span>Top Products</span>
                      </button>
                      <button type="button" class="sheet-tab tab-branches" [class.active-sheet]="activeExcelSheet === 'branches'" (click)="setExcelSheet('branches')">
                        <span class="tab-indicator" style="background:#2e75b6;"></span>
                        <span>Branches</span>
                      </button>
                      <button type="button" class="sheet-tab tab-channels" [class.active-sheet]="activeExcelSheet === 'channels'" (click)="setExcelSheet('channels')">
                        <span class="tab-indicator" style="background:#107c41;"></span>
                        <span>Channels</span>
                      </button>
                      <button type="button" class="sheet-tab tab-reservations" [class.active-sheet]="activeExcelSheet === 'reservations'" (click)="setExcelSheet('reservations')">
                        <span class="tab-indicator" style="background:#7030a0;"></span>
                        <span>Reservations</span>
                      </button>
                      <button type="button" class="sheet-tab tab-stock" [class.active-sheet]="activeExcelSheet === 'low_stock'" (click)="setExcelSheet('low_stock')">
                        <span class="tab-indicator" style="background:#c00000;"></span>
                        <span>Low Stock</span>
                      </button>
                    </div>
                    <span class="tab-new-icon" title="Agregar hoja">＋</span>
                  </div>

                  <!-- Barra de Estado Inferior de Excel -->
                  <div class="excel-status-bar">
                    <div class="status-bar-left">
                      <span class="status-ready">LISTO</span>
                      <span class="status-calc">Cálculo contable exacto</span>
                    </div>
                    <div class="status-bar-right">
                      <span>RECUENTO: {{ currentSheetRowCount }}</span>
                      @if (activeExcelSheet !== 'reservations' && activeExcelSheet !== 'low_stock') {
                        <span>SUMA: {{ dashboard.revenue.total | currency:'BOB':'symbol':'1.2-2' }}</span>
                      }
                      <span class="status-zoom">100%</span>
                    </div>
                  </div>
                </div>
              }

              <!-- Barra de Acciones de Descarga de la Maqueta -->
              <div class="mockup-action-panel">
                <div class="action-panel-notice">
                  <span class="material-symbols-outlined notice-icon">verified</span>
                  <div class="notice-text">
                    <strong class="notice-title">Documento listo para generar</strong>
                    <small class="notice-subtitle">La descarga se procesa en el servidor con fuentes vectoriales y cálculo contable exacto.</small>
                  </div>
                </div>

                <div class="action-panel-buttons">
                  @if (activeReportMockup === 'pdf') {
                    <button
                      type="button"
                      class="button button-dark download-cta-btn"
                      (click)="downloadReport('pdf')"
                      [disabled]="isExporting"
                    >
                      <span class="material-symbols-outlined" [class.spinning]="isExporting && exportingFormat === 'pdf'">picture_as_pdf</span>
                      {{ isExporting && exportingFormat === 'pdf' ? 'Generando PDF Oficial…' : 'Descargar Informe PDF Oficial' }}
                    </button>
                  } @else {
                    <button
                      type="button"
                      class="button button-dark download-cta-btn"
                      (click)="downloadReport('xlsx')"
                      [disabled]="isExporting"
                    >
                      <span class="material-symbols-outlined" [class.spinning]="isExporting && exportingFormat === 'xlsx'">table_view</span>
                      {{ isExporting && exportingFormat === 'xlsx' ? 'Generando Libro Excel…' : 'Descargar Libro Excel (XLSX)' }}
                    </button>
                  }
                </div>
              </div>
            </div>
          </section>
        } @else {
          <div class="dashboard-state operations-forms">
            <span class="material-symbols-outlined">monitoring</span>
            <strong>Sin datos para visualizar en este periodo.</strong>
            <small>Ajusta los filtros de fecha o sucursal para consultar otros periodos.</small>
          </div>
        }
      }

      <!-- Módulo de Gestión de Promociones y Descuentos -->
      <section class="promotions-management-section">
        <div class="section-banner">
          <div>
            <span class="card-eyebrow">Estrategia de Ventas</span>
            <h3>Gestión de Promociones Comerciales</h3>
            <p>Crea campañas de descuento por porcentaje o monto fijo y asigna prendas del catálogo.</p>
          </div>
        </div>

        <div class="pos-layout operations-forms">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div>
                <span class="panel-index">01</span>
                <h3>Nueva Promoción</h3>
              </div>
              <span class="material-symbols-outlined">sell</span>
            </div>
            <div class="pos-form-grid">
              <label>
                <span>Nombre de la promoción</span>
                <input [(ngModel)]="form.name" name="promotionName" placeholder="Ej. Temporada Denim 2026">
              </label>
              <label>
                <span>Tipo de descuento</span>
                <select [(ngModel)]="form.discount_type" name="discountType">
                  <option value="PERCENT">Porcentaje (%)</option>
                  <option value="FIXED">Monto fijo (Bs.)</option>
                </select>
              </label>
              <label>
                <span>Valor del descuento</span>
                <input type="number" min="1" [(ngModel)]="form.discount_value" name="discountValue">
              </label>
              <label>
                <span>Fecha de inicio</span>
                <input type="date" [(ngModel)]="form.starts_on" name="startsOn">
              </label>
              <label>
                <span>Fecha de fin</span>
                <input type="date" [(ngModel)]="form.ends_on" name="endsOn">
              </label>
              <label>
                <span>Producto inicial a incluir</span>
                <select [(ngModel)]="selectedProductId" name="initialProduct">
                  <option [ngValue]="0">Seleccionar producto</option>
                  @for (product of products; track product.id) {
                    <option [ngValue]="product.id">{{ product.name }}</option>
                  }
                </select>
              </label>
            </div>
            <label class="operations-forms">
              <span>Descripción y condiciones</span>
              <textarea rows="3" [(ngModel)]="form.description" name="promotionDescription" placeholder="Condiciones comerciales visibles en tienda"></textarea>
            </label>
            <button class="button button-dark pos-submit" (click)="createPromotion()">
              <span class="material-symbols-outlined">add</span>
              Crear y Activar Promoción
            </button>
          </div>

          <aside class="pos-summary">
            <span class="panel-index">02</span>
            <h3>Resumen de Campañas</h3>
            <p>Las promociones activas se aplican automáticamente en el módulo de ventas POS y en el carrito web.</p>
            <div class="pos-summary-row">
              <span>Total registradas</span>
              <strong>{{ promotions.length }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Campañas activas</span>
              <strong><i class="active-dot"></i>{{ activePromotions }}</strong>
            </div>
            <div class="pos-summary-note">
              <span class="material-symbols-outlined">verified</span>
              <small>El cálculo de descuentos se ejecuta de forma segura desde el backend.</small>
            </div>
          </aside>
        </div>

        <div class="operations-table-card operations-history">
          <div class="reservation-queue-header">
            <div>
              <p class="eyebrow">Campañas Vigentes</p>
              <h3>Listado de Promociones y Productos Vinculados</h3>
            </div>
          </div>
          <div class="table-wrap">
            <table class="luxury-table">
              <thead>
                <tr>
                  <th>Promoción</th>
                  <th>Descuento</th>
                  <th>Vigencia</th>
                  <th>Productos Asociados</th>
                  <th>Vincular Prenda</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                @for (promotion of promotions; track promotion.id) {
                  <tr>
                    <td>
                      <strong>{{ promotion.name }}</strong>
                      <small>{{ promotion.description || 'Sin descripción' }}</small>
                    </td>
                    <td>
                      <span class="promo-discount-badge">
                        {{ promotion.discount_type === 'PERCENT' ? promotion.discount_value + '%' : (promotion.discount_value | currency:'BOB':'symbol':'1.0-0') }}
                      </span>
                    </td>
                    <td>{{ promotion.starts_at | date:'dd/MM/yy' }} → {{ promotion.ends_at | date:'dd/MM/yy' }}</td>
                    <td>
                      <small>{{ productNames(promotion.product_ids) }}</small>
                    </td>
                    <td>
                      <select (change)="assignProduct(promotion, $any($event.target).value)" class="assign-product-select">
                        <option value="">+ Añadir producto</option>
                        @for (product of products; track product.id) {
                          <option [value]="product.id">{{ product.name }}</option>
                        }
                      </select>
                    </td>
                    <td>
                      <button
                        type="button"
                        class="toggle-status-btn"
                        [class.btn-active]="promotion.is_active"
                        (click)="togglePromotion(promotion)"
                      >
                        {{ promotion.is_active ? 'Activa' : 'Inactiva' }}
                      </button>
                    </td>
                  </tr>
                }
                @empty {
                  <tr>
                    <td colspan="6" class="text-center empty-notice">No hay promociones configuradas aún.</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </section>
  `,
  styles: [`
    .report-export-center {
      background: #ffffff;
      border: 1px solid var(--line, #e5e0d8);
      border-radius: 16px;
      padding: 28px 32px;
      margin-top: 32px;
      box-shadow: 0 8px 32px rgba(27, 28, 26, 0.05);
    }
    .report-export-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 20px;
      flex-wrap: wrap;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--line, #e5e0d8);
      padding-bottom: 20px;
    }
    .export-header-info .dashboard-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #8f6d2d;
      background: rgba(184, 146, 74, 0.12);
      padding: 4px 10px;
      border-radius: 20px;
      margin-bottom: 8px;
    }
    .export-header-info h3 {
      font-size: 1.25rem;
      font-weight: 700;
      margin: 0 0 6px 0;
      color: var(--ink, #1b1c1a);
    }
    .export-header-info p {
      font-size: 0.85rem;
      color: var(--muted, #666);
      max-width: 640px;
      margin: 0;
      line-height: 1.45;
    }
    .mockup-format-switcher {
      display: inline-flex;
      background: var(--panel, #f4f2ee);
      padding: 5px;
      border-radius: 12px;
      gap: 6px;
      border: 1px solid var(--line, #e5e0d8);
    }
    .mockup-tab-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 18px;
      border: none;
      border-radius: 8px;
      background: transparent;
      color: var(--muted, #666);
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .mockup-tab-btn:hover {
      color: var(--ink, #1b1c1a);
    }
    .mockup-tab-btn.active {
      background: #ffffff;
      color: var(--ink, #1b1c1a);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      font-weight: 700;
    }
    .mockup-display-stage {
      background: #f4f2ee;
      border-radius: 12px;
      padding: 24px;
      border: 1px solid var(--line, #e5e0d8);
      overflow: hidden;
    }
    /* PDF MOCKUP */
    .pdf-sheet-mockup {
      background: #ffffff;
      border-radius: 8px;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
      max-width: 840px;
      margin: 0 auto;
      padding: 28px 32px;
      border: 1px solid rgba(0, 0, 0, 0.06);
      font-family: 'Plus Jakarta Sans', Arial, sans-serif;
    }
    .pdf-mockup-banner {
      background: #1b1c1a;
      color: #ffffff;
      border-radius: 6px;
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      border-bottom: 3px solid #b8924a;
    }
    .pdf-banner-brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .pdf-brand-medallion {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: #b8924a;
      color: #1b1c1a;
      font-size: 1.2rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .pdf-brand-title {
      margin: 0;
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: #ffffff;
    }
    .pdf-brand-subtitle {
      margin: 2px 0 0 0;
      font-size: 0.62rem;
      letter-spacing: 0.12em;
      color: #b8924a;
      font-weight: 600;
    }
    .pdf-banner-metadata {
      font-size: 0.68rem;
      line-height: 1.5;
      color: #d0c8be;
      text-align: right;
    }
    .pdf-mockup-kpis {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 20px 0 24px 0;
    }
    .pdf-kpi-card {
      background: #faf8f5;
      border: 1px solid var(--line, #e5e0d8);
      border-radius: 6px;
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
    }
    .pdf-kpi-lbl {
      font-size: 0.6rem;
      font-weight: 700;
      color: #8f6d2d;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .pdf-kpi-val {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--ink, #1b1c1a);
      margin: 4px 0;
    }
    .pdf-kpi-sub {
      font-size: 0.65rem;
      color: var(--muted, #666);
    }
    .pdf-mockup-section-heading {
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      color: #1b1c1a;
      border-bottom: 2px solid #b8924a;
      padding-bottom: 6px;
      margin-bottom: 12px;
      text-transform: uppercase;
    }
    .pdf-mockup-table-wrap {
      overflow-x: auto;
      margin-bottom: 20px;
    }
    .pdf-mockup-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.76rem;
    }
    .pdf-mockup-table th {
      background: #1b1c1a;
      color: #ffffff;
      padding: 8px 12px;
      font-weight: 700;
      font-size: 0.65rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .pdf-mockup-table td {
      padding: 9px 12px;
      border-bottom: 1px solid #f0ede6;
      color: var(--ink, #1b1c1a);
    }
    .pdf-mockup-table tbody tr:nth-child(even) {
      background: #faf8f5;
    }
    .pdf-mockup-footer {
      border-top: 1px solid var(--line, #e5e0d8);
      padding-top: 12px;
      display: flex;
      justify-content: space-between;
      font-size: 0.64rem;
      color: var(--muted, #666);
      font-style: italic;
    }

    /* EXCEL WORKBOOK 365 MOCKUP */
    .excel-workbook-mockup {
      background: #ffffff;
      border-radius: 10px;
      box-shadow: 0 14px 36px rgba(0, 0, 0, 0.12);
      max-width: 880px;
      margin: 0 auto;
      overflow: hidden;
      border: 1px solid #107c41;
      font-family: 'Segoe UI', Arial, sans-serif;
    }
    .excel-window-titlebar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #107c41;
      color: #ffffff;
      padding: 8px 14px;
      font-size: 0.72rem;
    }
    .excel-title-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .excel-app-icon {
      font-size: 1rem;
    }
    .excel-file-title {
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .excel-save-badge {
      background: rgba(255, 255, 255, 0.2);
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 0.62rem;
      font-weight: 500;
    }
    .excel-window-controls {
      display: flex;
      gap: 14px;
      opacity: 0.9;
      font-size: 0.75rem;
    }
    .excel-close-btn {
      color: #ffffff;
      cursor: pointer;
    }
    .excel-ribbon-bar {
      display: flex;
      background: #f3f2f1;
      border-bottom: 1px solid #d4d0c8;
      padding: 0 12px;
      gap: 4px;
      font-size: 0.7rem;
      color: #323130;
    }
    .ribbon-tab {
      padding: 7px 12px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      font-weight: 500;
      user-select: none;
    }
    .ribbon-tab.active-ribbon {
      font-weight: 700;
      color: #107c41;
      border-bottom: 2px solid #107c41;
      background: #ffffff;
    }
    .excel-formula-bar {
      display: flex;
      align-items: center;
      background: #f9f9f9;
      border-bottom: 1px solid #d4d0c8;
      padding: 6px 12px;
      gap: 8px;
      font-size: 0.75rem;
    }
    .excel-name-box {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #ffffff;
      border: 1px solid #c8c6c4;
      border-radius: 3px;
      padding: 3px 10px;
      font-weight: 700;
      color: #323130;
      min-width: 58px;
    }
    .name-box-arrow {
      font-size: 0.65rem;
      color: #605e5c;
      margin-left: 6px;
    }
    .excel-formula-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #a19f9d;
      font-weight: 700;
      user-select: none;
    }
    .fx-action-btn {
      font-size: 0.75rem;
      cursor: default;
    }
    .fx-action-btn.enter {
      color: #107c41;
    }
    .excel-fx {
      font-style: italic;
      font-weight: 800;
      color: #107c41;
      font-size: 0.85rem;
    }
    .excel-formula-input {
      flex: 1;
      background: #ffffff;
      border: 1px solid #c8c6c4;
      border-radius: 3px;
      padding: 3px 10px;
      color: #201f1e;
      font-family: Consolas, monospace;
      font-size: 0.78rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .excel-grid-container {
      overflow-x: auto;
      background: #ffffff;
      min-height: 250px;
    }
    .excel-mockup-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.74rem;
    }
    .excel-corner {
      width: 36px;
      background: #e1dfdd;
      border: 1px solid #c8c6c4;
      text-align: center;
      font-size: 0.65rem;
      color: #605e5c;
    }
    .excel-col-head {
      background: #f3f2f1;
      border: 1px solid #d4d0c8;
      padding: 5px 8px;
      text-align: center;
      font-weight: 600;
      color: #605e5c;
      font-size: 0.68rem;
      user-select: none;
    }
    .excel-row-num {
      width: 36px;
      background: #f3f2f1;
      border: 1px solid #d4d0c8;
      text-align: center;
      color: #605e5c;
      font-weight: 600;
      font-size: 0.68rem;
      user-select: none;
    }
    .excel-main-header th {
      background: #1b1c1a;
      color: #ffffff;
      font-weight: 700;
      border: 1px solid #323130;
      border-bottom: 2px solid #b8924a;
      padding: 9px 12px;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .excel-cell {
      border: 1px solid #e1dfdd;
      padding: 7px 10px;
      color: #201f1e;
    }
    .excel-zebra {
      background: #fbf9f5;
    }
    .excel-total-row td {
      background: #fff9eb;
      font-weight: 700;
      border-top: 1px solid #b8924a;
      border-bottom: 3px double #1b1c1a;
    }
    .excel-active-cell {
      outline: 2px solid #107c41;
      outline-offset: -1px;
      position: relative;
    }
    .excel-cell-handle {
      position: absolute;
      bottom: -3px;
      right: -3px;
      width: 6px;
      height: 6px;
      background: #107c41;
      border: 1px solid #ffffff;
      border-radius: 1px;
    }
    .excel-money-cell {
      font-family: Consolas, monospace;
      font-weight: 600;
      text-align: right;
    }
    .excel-qty-cell {
      text-align: right;
    }
    .excel-id-cell {
      text-align: center;
    }
    .excel-sheet-tabs-bar {
      display: flex;
      align-items: center;
      background: #e1dfdd;
      border-top: 1px solid #c8c6c4;
      padding: 4px 8px 0 8px;
      gap: 4px;
      overflow-x: auto;
    }
    .sheet-tabs-scroll-controls {
      display: flex;
      gap: 4px;
      color: #605e5c;
      font-size: 0.65rem;
      padding: 0 4px;
    }
    .tab-scroll-arrow {
      cursor: pointer;
      user-select: none;
    }
    .sheet-tabs-list {
      display: flex;
      gap: 3px;
      flex: 1;
    }
    .sheet-tab {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #f3f2f1;
      border: 1px solid #c8c6c4;
      border-bottom: none;
      padding: 7px 14px;
      font-size: 0.7rem;
      font-weight: 600;
      color: #605e5c;
      border-radius: 5px 5px 0 0;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    .sheet-tab:hover {
      background: #ffffff;
      color: #1b1c1a;
    }
    .sheet-tab.active-sheet {
      background: #ffffff;
      color: #107c41;
      border-color: #a19f9d;
      font-weight: 700;
      border-top: 2px solid #107c41;
      box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.05);
    }
    .tab-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }
    .tab-new-icon {
      color: #605e5c;
      font-size: 0.85rem;
      cursor: pointer;
      padding: 0 6px;
      user-select: none;
    }
    .excel-status-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #107c41;
      color: #ffffff;
      padding: 5px 14px;
      font-size: 0.65rem;
      font-weight: 500;
    }
    .status-bar-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .status-ready {
      font-weight: 700;
      letter-spacing: 0.05em;
    }
    .status-calc {
      opacity: 0.9;
    }
    .status-bar-right {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .status-zoom {
      background: rgba(255, 255, 255, 0.2);
      padding: 1px 6px;
      border-radius: 3px;
    }

    /* ACTION PANEL */
    .mockup-action-panel {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid var(--line, #e5e0d8);
    }
    .action-panel-notice {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .notice-icon {
      color: #107c41;
      font-size: 24px;
    }
    .notice-text {
      display: flex;
      flex-direction: column;
    }
    .notice-title {
      display: block;
      color: var(--ink, #1b1c1a);
      font-size: 0.85rem;
      font-weight: 700;
      margin-bottom: 2px;
    }
    .notice-subtitle {
      display: block;
      color: var(--muted, #666);
      font-size: 0.74rem;
    }
    .action-panel-buttons {
      display: flex;
      gap: 12px;
    }
    .download-cta-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 0.78rem;
      padding: 12px 26px;
      border-radius: 999px;
      box-shadow: 0 4px 14px rgba(27, 28, 26, 0.15);
      cursor: pointer;
    }
    @media (max-width: 768px) {
      .report-export-header {
        flex-direction: column;
        align-items: stretch;
      }
      .pdf-mockup-kpis {
        grid-template-columns: repeat(2, 1fr);
      }
      .pdf-mockup-banner {
        flex-direction: column;
        align-items: flex-start;
      }
      .mockup-action-panel {
        flex-direction: column;
        align-items: stretch;
      }
      .download-cta-btn {
        width: 100%;
        justify-content: center;
      }
    }
  `],
})
export class Cycle3AdminComponent implements OnInit {
  private readonly admin = inject(AdminService);
  dashboard: DashboardReport | null = null;
  promotions: Promotion[] = [];
  products: ProductSummary[] = [];
  branches: { id: number; name: string }[] = [];
  selectedProductId = 0;
  message = '';
  messageType: 'success' | 'error' = 'success';
  isLoadingPage = false;
  isLoadingDashboard = false;
  isExporting = false;
  exportingFormat: ReportExportFormat | null = null;
  isAssistantLoading = false;
  dashboardLoadFailed = false;

  activePreset: 'all' | 'today' | 'week' | 'month' = 'all';

  assistantPrompt = 'Resumí ventas, bajo stock y acciones recomendadas para este periodo.';
  assistantResult: ReportAssistantResponse | null = null;
  assistantError = '';
  assistantPreviewRows: { label: string; value: string }[] = [];
  assistantCards: AssistantInsightCard[] = [];
  filters: { branch_id: number; start_date: string; end_date: string } = { branch_id: 0, start_date: '', end_date: '' };
  form = { name: '', description: '', discount_type: 'PERCENT' as PromotionInput['discount_type'], discount_value: 10, starts_on: this.today(), ends_on: this.futureDate(30) };
  activeReportMockup: 'pdf' | 'xlsx' = 'pdf';
  activeExcelSheet: 'summary' | 'top_products' | 'branches' | 'channels' | 'reservations' | 'low_stock' = 'top_products';

  isListeningVoice = false;
  isVoiceSupported = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
  private speechRecognition: any = null;

  readonly quickPrompts = [
    '¿Qué sucursal vendió más y cuál es el producto estrella?',
    '¿Cuáles productos tienen bajo stock y requieren reposición urgente?',
    'Resumen ejecutivo de ingresos, descuentos y ticket promedio',
    'Comparativa de ventas Tienda física vs Online y recomendaciones',
  ];

  ngOnInit(): void {
    this.reload();
  }

  setPreset(preset: 'all' | 'today' | 'week' | 'month'): void {
    this.activePreset = preset;
    if (preset === 'all') {
      this.filters.start_date = '';
      this.filters.end_date = '';
    } else if (preset === 'today') {
      this.filters.start_date = this.today();
      this.filters.end_date = this.today();
    } else if (preset === 'week') {
      const d = new Date();
      d.setDate(d.getDate() - 7);
      this.filters.start_date = d.toISOString().slice(0, 10);
      this.filters.end_date = this.today();
    } else if (preset === 'month') {
      const d = new Date();
      d.setDate(1);
      this.filters.start_date = d.toISOString().slice(0, 10);
      this.filters.end_date = this.today();
    }
    this.reloadDashboard();
  }

  get averageTicket(): number {
    if (!this.dashboard || !this.dashboard.revenue.sales_count) return 0;
    return this.dashboard.revenue.total / this.dashboard.revenue.sales_count;
  }

  askQuickPrompt(promptText: string): void {
    this.assistantPrompt = promptText;
    this.askAssistant();
  }

  stockBadgeClass(qty: number): string {
    if (qty <= 2) return 'stock-badge-critical';
    if (qty <= 5) return 'stock-badge-warning';
    return 'stock-badge-normal';
  }

  stockStatusLabel(qty: number): string {
    if (qty <= 2) return 'Crítico';
    if (qty <= 5) return 'Bajo';
    return 'Óptimo';
  }

  channelIcon(channel: string): string {
    const c = channel?.toUpperCase();
    if (c === 'POS') return 'storefront';
    if (c === 'ONLINE' || c === 'WEB') return 'shopping_bag';
    return 'language';
  }

  get activePromotions(): number {
    return this.promotions.filter((promotion) => promotion.is_active).length;
  }

  get dashboardRangeLabel(): string {
    return this.filters.start_date || this.filters.end_date
      ? `${this.filters.start_date || 'inicio'} → ${this.filters.end_date || 'hoy'}`
      : 'Todo el periodo';
  }

  get branchFilterName(): string {
    if (!this.filters.branch_id) return 'Todas las sucursales';
    const b = this.branches.find((item) => item.id === this.filters.branch_id);
    return b ? b.name : `Sucursal #${this.filters.branch_id}`;
  }

  setReportMockup(mockup: 'pdf' | 'xlsx'): void {
    this.activeReportMockup = mockup;
  }

  setExcelSheet(sheet: 'summary' | 'top_products' | 'branches' | 'channels' | 'reservations' | 'low_stock'): void {
    this.activeExcelSheet = sheet;
  }

  get activeExcelCellName(): string {
    if (!this.dashboard) return 'A1';
    switch (this.activeExcelSheet) {
      case 'summary': return 'B5';
      case 'top_products': return 'D' + (Math.min(this.dashboard.top_products.length, 5) + 2);
      case 'branches': return 'D' + (Math.min(this.dashboard.sales_by_branch.length, 5) + 2);
      case 'channels': return 'C' + (Math.min(this.dashboard.sales_by_channel.length, 5) + 2);
      case 'reservations': return 'B' + (Math.min(this.dashboard.reservations.length, 5) + 2);
      case 'low_stock': return 'E2';
      default: return 'B2';
    }
  }

  get activeExcelFormula(): string {
    if (!this.dashboard) return '';
    switch (this.activeExcelSheet) {
      case 'summary':
        return `=B3-B4  (Ingresos Netos: Bs ${this.dashboard.revenue.total.toFixed(2)})`;
      case 'top_products': {
        const rows = Math.min(this.dashboard.top_products.length, 5);
        return `=SUM(D2:D${rows + 1})`;
      }
      case 'branches': {
        const rows = Math.min(this.dashboard.sales_by_branch.length, 5);
        return `=SUM(D2:D${rows + 1})`;
      }
      case 'channels': {
        const rows = Math.min(this.dashboard.sales_by_channel.length, 5);
        return `=SUM(C2:C${rows + 1})`;
      }
      case 'reservations': {
        const rows = Math.min(this.dashboard.reservations.length, 5);
        return `=SUM(B2:B${rows + 1})`;
      }
      case 'low_stock':
        return `=IF(E2<=2, "ALERTA_CRITICA", "STOCK_OPTIMO")`;
      default:
        return `${this.dashboard.revenue.total}`;
    }
  }

  get currentSheetRowCount(): number {
    if (!this.dashboard) return 0;
    switch (this.activeExcelSheet) {
      case 'summary': return 7;
      case 'top_products': return this.dashboard.top_products.length;
      case 'branches': return this.dashboard.sales_by_branch.length;
      case 'channels': return this.dashboard.sales_by_channel.length;
      case 'reservations': return this.dashboard.reservations.length;
      case 'low_stock': return this.dashboard.low_stock.length;
      default: return 0;
    }
  }

  get branchMaxTotal(): number {
    return Math.max(0, ...this.dashboardItems('sales_by_branch').map((item) => item.total));
  }

  get topProductMaxUnits(): number {
    return Math.max(0, ...this.dashboardItems('top_products').map((item) => item.units_sold));
  }

  get channelMaxTotal(): number {
    return Math.max(0, ...this.dashboardItems('sales_by_channel').map((item) => item.total));
  }

  get reservationMaxCount(): number {
    return Math.max(0, ...this.dashboardItems('reservations').map((item) => item.count));
  }

  get totalReservations(): number {
    return this.dashboardItems('reservations').reduce((total, item) => total + item.count, 0);
  }

  get criticalStockCount(): number {
    return this.dashboardItems('low_stock').filter((item) => item.available_quantity <= 2).length;
  }

  get discountPercent(): number {
    return this.percent(this.dashboard?.revenue.discount || 0, this.dashboard?.revenue.subtotal || 0);
  }

  get revenueNetPercent(): number {
    return Math.max(0, 100 - this.discountPercent);
  }

  get discountRate(): number {
    return this.discountPercent;
  }

  get gaugeArcLength(): number {
    return 204.2;
  }

  get gaugeArcOffset(): number {
    const pct = Math.max(0, Math.min(100, this.revenueNetPercent));
    return Number((204.2 * (1 - pct / 100)).toFixed(2));
  }

  get channelDonutSlices(): ChannelDonutSlice[] {
    const channels = this.dashboard?.sales_by_channel || [];
    const totalRev = channels.reduce((acc, c) => acc + (c.total || 0), 0);
    const totalCount = channels.reduce((acc, c) => acc + (c.sales_count || 0), 0);
    const circumference = 376.99;

    let currentOffset = 0;
    return channels.map((item) => {
      let share = 0;
      if (totalRev > 0) {
        share = (item.total / totalRev) * 100;
      } else if (totalCount > 0) {
        share = (item.sales_count / totalCount) * 100;
      } else if (channels.length > 0) {
        share = 100 / channels.length;
      }
      const strokeLen = (share / 100) * circumference;
      const slice: ChannelDonutSlice = {
        channel: item.channel,
        label: this.channelLabel(item.channel),
        share: Math.round(share),
        color: this.getChannelColor(item.channel),
        dashArray: `${strokeLen.toFixed(1)} ${circumference.toFixed(1)}`,
        dashOffset: `${(-currentOffset).toFixed(1)}`,
      };
      currentOffset += strokeLen;
      return slice;
    });
  }

  get dominantChannelItem(): { channel: string; sales_count: number; total: number } | null {
    const channels = this.dashboard?.sales_by_channel || [];
    if (!channels.length) return null;
    return [...channels].sort((a, b) => b.total - a.total)[0];
  }

  get dominantChannelShare(): number {
    const channels = this.dashboard?.sales_by_channel || [];
    const total = channels.reduce((sum, c) => sum + c.total, 0);
    const dominant = this.dominantChannelItem;
    if (!dominant || total <= 0) return 0;
    return Math.round((dominant.total / total) * 100);
  }

  get dominantChannelName(): string {
    const dominant = this.dominantChannelItem;
    return dominant ? this.channelLabel(dominant.channel) : 'Sin datos';
  }

  get dominantChannelCode(): string {
    return this.dominantChannelItem?.channel || '';
  }

  getChannelColor(channel: string): string {
    const c = channel?.toUpperCase();
    if (c === 'POS') return '#b8924a';
    if (c === 'ONLINE' || c === 'WEB') return '#10b981';
    if (c === 'MOBILE') return '#6366f1';
    return '#d4af37';
  }

  get assistantProviderLabel(): string {
    if (!this.assistantResult) return 'Motor Inteligente Local · En línea';
    const prov = (this.assistantResult.provider || '').toLowerCase();
    if (prov === 'local') return 'Motor Inteligente Local · Activo';
    return `${this.assistantResult.provider}${this.assistantResult.fallback_used ? ' · fallback' : ''}`;
  }

  get hasDashboardData(): boolean {
    if (!this.dashboard) return false;
    return (
      this.dashboard.revenue.sales_count > 0 ||
      this.dashboard.top_products.length > 0 ||
      this.dashboard.sales_by_branch.length > 0 ||
      this.dashboard.low_stock.length > 0 ||
      this.dashboard.reservations.length > 0 ||
      this.dashboard.sales_by_channel.length > 0
    );
  }

  reload(): void {
    this.isLoadingPage = true;
    this.dashboardLoadFailed = false;
    forkJoin({
      dashboard: this.admin.dashboard(this.dashboardFilters()),
      promotions: this.admin.promotions(),
      products: this.admin.products(),
      branches: this.admin.branches(),
    })
      .pipe(finalize(() => (this.isLoadingPage = false)))
      .subscribe({
        next: ({ dashboard, promotions, products, branches }) => {
          this.dashboard = dashboard;
          this.promotions = promotions.items;
          this.products = products.items;
          this.branches = branches.items;
        },
        error: () => {
          this.dashboardLoadFailed = true;
          this.setMessage('No se pudo cargar la información del ciclo 3.', 'error');
        },
      });
  }

  reloadDashboard(): void {
    this.isLoadingDashboard = true;
    this.dashboardLoadFailed = false;
    this.admin
      .dashboard(this.dashboardFilters())
      .pipe(finalize(() => (this.isLoadingDashboard = false)))
      .subscribe({
        next: (dashboard) => {
          this.dashboard = dashboard;
          this.setMessage('Dashboard actualizado.', 'success');
        },
        error: () => {
          this.dashboardLoadFailed = true;
          this.setMessage('No se pudo actualizar el dashboard.', 'error');
        },
      });
  }

  downloadReport(format: ReportExportFormat): void {
    this.isExporting = true;
    this.exportingFormat = format;
    this.admin
      .exportReport(format, this.dashboardFilters())
      .pipe(
        finalize(() => {
          this.isExporting = false;
          this.exportingFormat = null;
        }),
      )
      .subscribe({
        next: (blob) => {
          this.saveBlob(blob, this.reportFileName(format));
          this.setMessage(`Reporte ${this.exportName(format)} descargado.`, 'success');
        },
        error: () => this.setMessage(`No se pudo descargar el reporte ${this.exportName(format)}.`, 'error'),
      });
  }

  askAssistant(): void {
    const prompt = this.assistantPrompt.trim();
    if (!prompt) {
      this.assistantError = 'Escribe una pregunta para generar el reporte.';
      return;
    }
    this.isAssistantLoading = true;
    this.assistantError = '';
    this.admin
      .reportAssistant(this.reportAssistantRequest(prompt))
      .pipe(finalize(() => (this.isAssistantLoading = false)))
      .subscribe({
        next: (result) => {
          this.assistantResult = result;
          this.assistantCards = this.buildAssistantCards(result.data);
          this.assistantPreviewRows = this.buildAssistantPreview(result.data);
          this.setMessage('Reporte inteligente generado.', 'success');
        },
        error: () => {
          this.assistantError = 'No se pudo generar el reporte inteligente. Intenta de nuevo.';
        },
      });
  }

  toggleVoiceCommand(): void {
    if (!this.isVoiceSupported) {
      this.assistantError = 'El reconocimiento de voz no está soportado en este navegador.';
      return;
    }
    if (this.isListeningVoice) {
      this.speechRecognition?.stop();
      this.isListeningVoice = false;
      return;
    }

    try {
      const SpeechRecognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      this.speechRecognition = new SpeechRecognitionClass();
      this.speechRecognition.lang = 'es-BO';
      this.speechRecognition.continuous = false;
      this.speechRecognition.interimResults = false;
      this.isListeningVoice = true;
      this.assistantError = '';

      this.speechRecognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          this.assistantPrompt = transcript;
          this.isListeningVoice = false;
          this.askAssistant();
        }
      };

      this.speechRecognition.onerror = (event: any) => {
        this.isListeningVoice = false;
        this.assistantError = `Error en comando de voz: ${event.error}`;
      };

      this.speechRecognition.onend = () => {
        this.isListeningVoice = false;
      };

      this.speechRecognition.start();
    } catch (err: any) {
      this.isListeningVoice = false;
      this.assistantError = 'No se pudo iniciar el reconocimiento de voz.';
    }
  }

  createPromotion(): void {
    if (!this.form.name || !this.selectedProductId) {
      this.setMessage('Completa el nombre y selecciona un producto.', 'error');
      return;
    }
    if (!this.form.starts_on || !this.form.ends_on) {
      this.setMessage('Completa la vigencia de la promoción.', 'error');
      return;
    }
    const payload: PromotionInput = {
      name: this.form.name,
      description: this.form.description || null,
      discount_type: this.form.discount_type,
      discount_value: Number(this.form.discount_value),
      starts_at: `${this.form.starts_on}T00:00:00`,
      ends_at: `${this.form.ends_on}T23:59:59`,
    };
    this.admin
      .createPromotion(payload)
      .pipe(switchMap((promotion) => this.admin.setPromotionProducts(promotion.id, [this.selectedProductId])))
      .subscribe({
        next: () => {
          this.setMessage('Promoción creada y producto asignado.', 'success');
          this.resetForm();
          this.reload();
        },
        error: () => this.setMessage('No se pudo crear la promoción.', 'error'),
      });
  }

  assignProduct(promotion: Promotion, productIdValue: string): void {
    const productId = Number(productIdValue);
    if (!productId) return;
    const productIds = Array.from(new Set([...promotion.product_ids, productId]));
    this.admin.setPromotionProducts(promotion.id, productIds).subscribe({
      next: () => {
        this.setMessage('Producto asignado a la promoción.', 'success');
        this.reload();
      },
      error: () => this.setMessage('No se pudo asignar el producto.', 'error'),
    });
  }

  togglePromotion(promotion: Promotion): void {
    this.admin.setPromotionActive(promotion.id, !promotion.is_active).subscribe({
      next: () => {
        this.setMessage(promotion.is_active ? 'Promoción desactivada.' : 'Promoción activada.', 'success');
        this.reload();
      },
      error: () => this.setMessage('No se pudo cambiar el estado de la promoción.', 'error'),
    });
  }

  productNames(ids: number[]): string {
    if (!ids.length) return 'Sin productos asignados';
    const names = ids.map((id) => this.products.find((product) => product.id === id)?.name || `#${id}`);
    return names.slice(0, 3).join(', ') + (names.length > 3 ? ` +${names.length - 3}` : '');
  }

  percent(value: number, max: number): number {
    if (!max || max <= 0) return 0;
    return Math.min(100, Math.round((Number(value || 0) / Number(max)) * 100));
  }

  exportLabel(format: ReportExportFormat): string {
    if (this.exportingFormat === format) return 'Descargando…';
    const labels: Record<ReportExportFormat, string> = {
      xlsx: 'Descargar Excel',
      pdf: 'Descargar PDF',
      pptx: 'Descargar PowerPoint',
    };
    return labels[format];
  }

  assistantIntentLabel(intent: ReportAssistantResponse['intent'] | string): string {
    const labels: Record<string, string> = {
      dashboard: 'Dashboard',
      top_products: 'Productos más vendidos',
      sales_by_branch: 'Ventas por sucursal',
      summary: 'Resumen',
      sales: 'Ventas',
      inventory: 'Inventario',
      promotions: 'Promociones',
      reservations: 'Reservas',
      branches: 'Sucursales',
      recommendations: 'Recomendaciones',
    };
    const kind = typeof intent === 'string' ? intent : (intent as ReportAssistantIntent | null | undefined)?.kind;
    if (!kind) return 'General';
    return labels[kind.toLowerCase()] || kind;
  }

  channelLabel(channel: string): string {
    const labels: Record<string, string> = {
      POS: 'Tienda',
      ONLINE: 'Online',
      WEB: 'Web',
      MOBILE: 'Móvil',
    };
    return labels[channel?.toUpperCase()] || channel;
  }

  reservationStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      PENDING: 'Pendientes',
      PREPARING: 'Preparando',
      READY: 'Listas',
      ATTENDED: 'Atendidas',
      CANCELLED: 'Canceladas',
      EXPIRED: 'Expiradas',
    };
    return labels[status?.toUpperCase()] || status;
  }

  private dashboardFilters(): DashboardFilters {
    return {
      branch_id: this.filters.branch_id || undefined,
      start_date: this.filters.start_date || undefined,
      end_date: this.filters.end_date || undefined,
    };
  }

  private reportAssistantRequest(prompt: string): { prompt: string; date_from?: string; date_to?: string; branch_id?: number } {
    const filters = this.dashboardFilters();
    return { prompt, date_from: filters.start_date, date_to: filters.end_date, branch_id: filters.branch_id };
  }

  private exportName(format: ReportExportFormat): string {
    return ({ xlsx: 'Excel', pdf: 'PDF', pptx: 'PowerPoint' })[format];
  }

  private reportFileName(format: ReportExportFormat): string {
    const range = [this.filters.start_date, this.filters.end_date].filter(Boolean).join('_a_') || 'todo_el_periodo';
    return `reporte-ejecutivo-${range}.${format}`;
  }

  private saveBlob(blob: Blob, fileName: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.rel = 'noopener';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  private buildAssistantPreview(data: unknown): { label: string; value: string }[] {
    if (Array.isArray(data)) {
      return data.slice(0, 4).map((item, index) => {
        if (item && typeof item === 'object') {
          const obj = item as Record<string, any>;
          if (obj['available_quantity'] != null) {
            return {
              label: String(obj['product_name'] || `Ítem ${index + 1}`),
              value: `${obj['available_quantity']} disp. (${obj['branch_name'] || 'Almacén'})`,
            };
          }
          if (obj['units_sold'] != null) {
            return {
              label: String(obj['product_name'] || `Ítem ${index + 1}`),
              value: `${obj['units_sold']} un. (Bs ${obj['revenue'] ?? 0})`,
            };
          }
          if (obj['branch_name'] && obj['total'] != null) {
            return {
              label: String(obj['branch_name']),
              value: `Bs ${Number(obj['total']).toFixed(2)} (${obj['sales_count'] ?? 0} ventas)`,
            };
          }
          if (obj['status'] && obj['count'] != null) {
            return {
              label: `Reservas ${this.humanize(String(obj['status']))}`,
              value: `${obj['count']} registro(s)`,
            };
          }
        }
        return {
          label: `Métrica ${index + 1}`,
          value: this.previewValue(item),
        };
      });
    }
    if (data && typeof data === 'object') {
      const obj = data as Record<string, any>;
      // Si el objeto representa un consolidado / dashboard con submódulos
      if ('revenue' in obj || 'sales_by_channel' in obj || 'top_products' in obj || 'sales_by_branch' in obj) {
        const rows: { label: string; value: string }[] = [];
        if (obj['revenue']) {
          rows.push({
            label: 'Facturación Total',
            value: this.formatCurrency(Number(obj['revenue'].total || 0)),
          });
          rows.push({
            label: 'Ventas Confirmadas',
            value: `${obj['revenue'].sales_count || 0} operaciones`,
          });
        }
        if (Array.isArray(obj['sales_by_channel']) && obj['sales_by_channel'].length > 0) {
          const topCh = obj['sales_by_channel'][0];
          rows.push({
            label: `Canal ${this.channelLabel(String(topCh.channel))}`,
            value: this.formatCurrency(Number(topCh.total || 0)),
          });
        }
        if (Array.isArray(obj['top_products']) && obj['top_products'].length > 0) {
          rows.push({
            label: 'Prenda Estrella',
            value: `${obj['top_products'][0].product_name} (${obj['top_products'][0].units_sold} un.)`,
          });
        }
        if (rows.length > 0) {
          return rows.slice(0, 4);
        }
      }

      return Object.entries(data as Record<string, unknown>)
        .slice(0, 4)
        .map(([label, value]) => ({
          label: this.humanize(label),
          value: this.previewValue(value),
        }));
    }
    return data == null ? [] : [{ label: 'Resultado', value: this.previewValue(data) }];
  }

  private buildAssistantCards(data: unknown): AssistantInsightCard[] {
    if (Array.isArray(data)) {
      return data.slice(0, 8).map((item, index) => {
        if (item && typeof item === 'object') {
          const obj = item as Record<string, any>;

          // 1. Alertas de inventario / bajo stock
          if (obj['available_quantity'] != null || obj['stock'] != null) {
            const qty = Number(obj['available_quantity'] ?? obj['stock']);
            const prodName = String(obj['product_name'] || 'Alerta de Stock');
            const branchText = obj['branch_name'] ? `Sucursal ${obj['branch_name']}` : '';
            const skuText = obj['sku'] ? `SKU: ${obj['sku']}` : '';
            const secondary = [branchText, skuText].filter(Boolean).join(' · ') || undefined;
            return {
              title: prodName,
              primaryMetric: `${qty} un. disponible${qty === 1 ? '' : 's'}`,
              secondaryMetric: secondary,
              badge: qty <= 2 ? 'Crítico ⚠️' : 'Bajo Stock',
              badgeType: qty <= 2 ? 'critical' : 'amber',
              icon: 'warning',
            };
          }

          // 2. Ranking de productos más vendidos / estrella
          if ((obj['units_sold'] != null || obj['revenue'] != null) && (obj['product_name'] || obj['name'])) {
            const name = String(obj['product_name'] || obj['name']);
            const units = obj['units_sold'] ?? obj['units'] ?? obj['quantity'];
            const rev = obj['revenue'] ?? obj['total'];
            let primary = '';
            let secondary: string | undefined = undefined;
            if (rev != null) {
              primary = this.formatCurrency(Number(rev));
              if (units != null) secondary = `${units} unidades vendidas`;
            } else if (units != null) {
              primary = `${units} unidades`;
            }
            return {
              title: name,
              primaryMetric: primary || 'Registrado',
              secondaryMetric: secondary,
              badge: index === 0 ? 'Top #1 🏆' : `Top #${index + 1}`,
              badgeType: index === 0 ? 'gold' : 'blue',
              icon: index === 0 ? 'trophy' : (index === 1 ? 'workspace_premium' : 'sell'),
            };
          }

          // 3. Ventas por sucursal
          if (obj['branch_name'] && (obj['total'] != null || obj['sales_count'] != null)) {
            const total = obj['total'] != null ? this.formatCurrency(Number(obj['total'])) : `${obj['sales_count'] ?? 0} ventas`;
            return {
              title: String(obj['branch_name']),
              primaryMetric: total,
              secondaryMetric: obj['sales_count'] ? `${obj['sales_count']} ventas realizadas` : undefined,
              badge: `Sucursal #${index + 1}`,
              badgeType: 'purple',
              icon: 'storefront',
            };
          }

          // 4. Reservas de probador
          if (obj['status'] && obj['count'] != null) {
            return {
              title: `Vestidores: ${this.humanize(String(obj['status']))}`,
              primaryMetric: `${obj['count']} reservas`,
              secondaryMetric: 'Estado de atención en tienda',
              badge: String(obj['status']).toUpperCase(),
              badgeType: 'blue',
              icon: 'event_seat',
            };
          }

          // 5. Canales de venta
          if (obj['channel']) {
            return {
              title: `Canal ${this.channelLabel(String(obj['channel']))}`,
              primaryMetric: obj['total'] != null ? this.formatCurrency(Number(obj['total'])) : `${obj['sales_count']} ventas`,
              secondaryMetric: `${obj['sales_count'] ?? 0} operaciones`,
              badge: String(obj['channel']),
              badgeType: 'emerald',
              icon: this.channelIcon(String(obj['channel'])),
            };
          }

          // 6. Genérico con nombre de producto
          if (obj['product_name'] || obj['name']) {
            const name = String(obj['product_name'] || obj['name']);
            return {
              title: name,
              primaryMetric: 'Registrado',
              badge: `Ítem #${index + 1}`,
              badgeType: 'blue',
              icon: 'sell',
            };
          }

          const firstKey = Object.keys(obj)[0] || `Métrica ${index + 1}`;
          return {
            title: this.humanize(String(obj['title'] || obj['label'] || firstKey)),
            primaryMetric: String(obj['value'] ?? obj['total'] ?? obj[firstKey]),
            icon: 'analytics',
          };
        }
        return {
          title: `Métrica ${index + 1}`,
          primaryMetric: String(item),
          icon: 'analytics',
        };
      });
    }

    if (data && typeof data === 'object') {
      const obj = data as Record<string, any>;
      const isDashboard = 'revenue' in obj || 'sales_by_channel' in obj || 'top_products' in obj || 'sales_by_branch' in obj;

      if (isDashboard) {
        const cards: AssistantInsightCard[] = [];

        // A. Finanzas / Ingresos Totales
        if (obj['revenue']) {
          const rev = obj['revenue'];
          const total = Number(rev.total || 0);
          const count = Number(rev.sales_count || 0);
          const avg = count > 0 ? total / count : 0;
          cards.push({
            title: 'Ingresos Totales',
            primaryMetric: this.formatCurrency(total),
            secondaryMetric: `${count} ventas · Ticket prom: ${this.formatCurrency(avg)}`,
            badge: 'Finanzas',
            badgeType: 'emerald',
            icon: 'payments',
          });
        }

        // B. Desglose y Comparativa de Canales (Física vs Online)
        if (Array.isArray(obj['sales_by_channel']) && obj['sales_by_channel'].length > 0) {
          const channels = obj['sales_by_channel'];
          const totalChRev = channels.reduce((sum: number, c: any) => sum + Number(c.total || 0), 0);
          for (const ch of channels) {
            const chName = this.channelLabel(String(ch.channel));
            const chTotal = Number(ch.total || 0);
            const chCount = Number(ch.sales_count || 0);
            const share = totalChRev > 0 ? Math.round((chTotal / totalChRev) * 100) : 0;
            cards.push({
              title: `Canal ${chName}`,
              primaryMetric: this.formatCurrency(chTotal),
              secondaryMetric: `${chCount} ventas confirmadas (${share}% de la facturación)`,
              badge: `${share}% Cuota`,
              badgeType: 'emerald',
              icon: this.channelIcon(String(ch.channel)),
            });
          }
        }

        // C. Prenda Estrella (Top Product)
        if (Array.isArray(obj['top_products']) && obj['top_products'].length > 0) {
          const top = obj['top_products'][0];
          cards.push({
            title: String(top.product_name),
            primaryMetric: `${top.units_sold} prendas vendidas`,
            secondaryMetric: `Recaudación: ${this.formatCurrency(Number(top.revenue || 0))} (Prenda #1)`,
            badge: 'Top #1 🏆',
            badgeType: 'gold',
            icon: 'trophy',
          });
        }

        // D. Sucursal Destacada (Top Branch)
        if (Array.isArray(obj['sales_by_branch']) && obj['sales_by_branch'].length > 0) {
          const sortedBranches = [...obj['sales_by_branch']].sort((a: any, b: any) => Number(b.total || 0) - Number(a.total || 0));
          const topB = sortedBranches[0];
          cards.push({
            title: String(topB.branch_name),
            primaryMetric: this.formatCurrency(Number(topB.total || 0)),
            secondaryMetric: `${topB.sales_count || 0} ventas confirmadas`,
            badge: 'Sede Líder',
            badgeType: 'purple',
            icon: 'storefront',
          });
        }

        // E. Alerta de Stock Crítico
        if (Array.isArray(obj['low_stock']) && obj['low_stock'].length > 0) {
          const low = obj['low_stock'];
          const critical = low.filter((i: any) => Number(i.available_quantity) <= 2);
          cards.push({
            title: critical.length > 0 ? `${critical.length} prendas en Stock Crítico` : 'Inventario Bajo',
            primaryMetric: `${low.length} alertas activas`,
            secondaryMetric: critical.length > 0 ? `Urgente: ${critical[0].product_name} (${critical[0].available_quantity} un.)` : 'Reposición preventiva recomendada',
            badge: critical.length > 0 ? 'Crítico ⚠️' : 'Bajo Stock',
            badgeType: critical.length > 0 ? 'critical' : 'amber',
            icon: 'warning',
          });
        }

        // F. Reservas de Probador
        if (Array.isArray(obj['reservations']) && obj['reservations'].length > 0) {
          const totalRes = obj['reservations'].reduce((acc: number, item: any) => acc + Number(item.count || 0), 0);
          cards.push({
            title: 'Reservas de Probador',
            primaryMetric: `${totalRes} registradas`,
            secondaryMetric: 'Tráfico de vestidores en sucursales',
            badge: 'Vestidor',
            badgeType: 'blue',
            icon: 'event_seat',
          });
        }

        return cards;
      }

      // Si es otro objeto genérico
      const entries = Object.entries(obj).slice(0, 8);
      return entries.map(([key, val]) => {
        const title = this.humanize(key);
        let primaryMetric = '';
        let secondaryMetric: string | undefined = undefined;
        let badge: string | undefined = undefined;
        let badgeType: AssistantInsightCard['badgeType'] = 'gold';
        let icon = 'insights';

        const lowerKey = key.toLowerCase();

        if (typeof val === 'number') {
          if (lowerKey.includes('total') || lowerKey.includes('ingreso') || lowerKey.includes('revenue') || lowerKey.includes('monto')) {
            primaryMetric = this.formatCurrency(val);
          } else {
            primaryMetric = String(val);
          }
        } else if (typeof val === 'string') {
          primaryMetric = val;
        } else if (Array.isArray(val)) {
          primaryMetric = `${val.length} registros`;
          if (val.length > 0 && typeof val[0] === 'object') {
            const first = val[0] as Record<string, any>;
            secondaryMetric = String(first['name'] || first['product_name'] || first['branch_name'] || first['channel'] || 'Muestra analítica');
          }
        } else if (val && typeof val === 'object') {
          const sub = val as Record<string, any>;
          if (sub['total'] != null) {
            primaryMetric = this.formatCurrency(Number(sub['total']));
            if (sub['sales_count'] != null) secondaryMetric = `${sub['sales_count']} ventas`;
          } else if (sub['count'] != null) {
            primaryMetric = `${sub['count']} items`;
          } else {
            primaryMetric = this.humanize(Object.keys(sub)[0] || 'Dato');
          }
        } else {
          primaryMetric = String(val ?? '—');
        }

        if (lowerKey.includes('venta') || lowerKey.includes('sales')) {
          icon = 'shopping_bag';
          badgeType = 'emerald';
        } else if (lowerKey.includes('alerta') || lowerKey.includes('stock') || lowerKey.includes('critico')) {
          icon = 'warning';
          badge = 'Atención';
          badgeType = 'critical';
        } else if (lowerKey.includes('sucursal') || lowerKey.includes('branch')) {
          icon = 'storefront';
          badgeType = 'purple';
        } else if (lowerKey.includes('producto') || lowerKey.includes('top')) {
          icon = 'workspace_premium';
          badgeType = 'gold';
        }

        return {
          title,
          primaryMetric,
          secondaryMetric,
          badge,
          badgeType,
          icon,
        };
      });
    }

    return [];
  }

  private formatCurrency(value: number): string {
    return `Bs ${Number(value || 0).toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  private previewValue(value: unknown): string {
    if (value == null) return 'Sin dato';
    if (typeof value === 'number') return String(value);
    if (typeof value === 'string') return value;
    if (typeof value === 'object') {
      const obj = value as Record<string, any>;
      if (obj['total'] != null) return this.formatCurrency(Number(obj['total']));
      if (obj['sales_count'] != null) return `${obj['sales_count']} ventas`;
      if (obj['count'] != null) return `${obj['count']} unidades`;
      if (obj['available_quantity'] != null) return `${obj['available_quantity']} disp.`;
      if (Array.isArray(value)) return `${value.length} registros`;
      const firstVal = Object.values(obj)[0];
      if (firstVal != null && typeof firstVal !== 'object') return String(firstVal);
      return 'Datos consolidados';
    }
    return String(value);
  }

  private humanize(value: string): string {
    return value.replace(/_/g, ' ').replace(/^./, (letter) => letter.toUpperCase());
  }

  private setMessage(message: string, type: 'success' | 'error'): void {
    this.message = message;
    this.messageType = type;
  }

  private resetForm(): void {
    this.form = {
      name: '',
      description: '',
      discount_type: 'PERCENT',
      discount_value: 10,
      starts_on: this.today(),
      ends_on: this.futureDate(30),
    };
    this.selectedProductId = 0;
  }

  private today(): string {
    return new Date().toISOString().slice(0, 10);
  }

  private futureDate(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date.toISOString().slice(0, 10);
  }

  private dashboardItems<K extends keyof DashboardReport>(key: K): DashboardReport[K] {
    return (this.dashboard?.[key] || []) as DashboardReport[K];
  }
}
