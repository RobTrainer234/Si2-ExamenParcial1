import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { OfflineTransactionService } from '../../core/offline/offline-transaction.service';
import { SyncTransactionService } from '../../core/offline/sync-transaction.service';
import { OfflineOperationRecord } from '../../core/offline/offline.models';

type FilterType = 'ALL' | 'PENDING' | 'CONFIRMED' | 'CONFLICT';

@Component({
  selector: 'app-offline-transactions-tray',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section class="operations-page offline-tray-container">
      <!-- Encabezado principal -->
      <div class="tray-header">
        <div class="tray-header-info">
          <div class="tray-eyebrow">
            <span class="material-symbols-outlined eyebrow-icon">cloud_sync</span>
            <span>OPERACIONES OFFLINE · PERSISTENCIA OUTBOX</span>
          </div>
          <h2 class="tray-title">Bandeja de Operaciones Pendientes</h2>
          <p class="tray-subtitle">
            Monitorea transacciones registradas localmente en tienda sin conexión y sincronízalas de forma idempotente con el servidor central.
          </p>
        </div>

        <div class="tray-actions">
          <button
            type="button"
            class="button button-refresh"
            (click)="loadOperations()"
            title="Refrescar lista local"
          >
            <span class="material-symbols-outlined">refresh</span>
            <span>Actualizar</span>
          </button>

          <button
            type="button"
            class="button button-sync"
            [disabled]="syncService.isSyncing() || syncService.pendingCount() === 0"
            (click)="syncNow()"
          >
            <span class="material-symbols-outlined" [class.spinning]="syncService.isSyncing()">
              sync
            </span>
            <span>
              {{ syncService.isSyncing() ? 'Sincronizando lote...' : 'Sincronizar ahora (' + syncService.pendingCount() + ' pendientes)' }}
            </span>
          </button>
        </div>
      </div>

      <!-- Alertas de sincronización y estado -->
      @if (syncService.syncError()) {
        <div class="sync-banner banner-error">
          <span class="material-symbols-outlined banner-icon">error</span>
          <div class="banner-content">
            <strong>Error de comunicación:</strong> {{ syncService.syncError() }}
          </div>
        </div>
      }

      @if (syncMessage()) {
        <div class="sync-banner" [ngClass]="conflictCount() > 0 ? 'banner-warning' : 'banner-success'">
          <span class="material-symbols-outlined banner-icon">
            {{ conflictCount() > 0 ? 'warning' : 'check_circle' }}
          </span>
          <div class="banner-content">
            {{ syncMessage() }}
          </div>
          <button type="button" class="banner-close" (click)="syncMessage.set(null)">✕</button>
        </div>
      }

      <!-- Tarjetas de métricas KPI Outbox -->
      <div class="kpi-grid">
        <div class="kpi-card" [class.active-kpi]="activeFilter() === 'ALL'" (click)="setFilter('ALL')">
          <div class="kpi-icon-wrap kpi-all">
            <span class="material-symbols-outlined">receipt_long</span>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">TOTAL OPERACIONES</span>
            <span class="kpi-value">{{ totalCount() }}</span>
            <span class="kpi-caption">Registradas en este dispositivo</span>
          </div>
        </div>

        <div class="kpi-card" [class.active-kpi]="activeFilter() === 'PENDING'" (click)="setFilter('PENDING')">
          <div class="kpi-icon-wrap kpi-pending">
            <span class="material-symbols-outlined">hourglass_top</span>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">PENDIENTES DE ENVÍO</span>
            <span class="kpi-value text-amber">{{ pendingCount() }}</span>
            <span class="kpi-caption">En cola local IndexedDB</span>
          </div>
        </div>

        <div class="kpi-card" [class.active-kpi]="activeFilter() === 'CONFIRMED'" (click)="setFilter('CONFIRMED')">
          <div class="kpi-icon-wrap kpi-confirmed">
            <span class="material-symbols-outlined">check_circle</span>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">CONFIRMADAS</span>
            <span class="kpi-value text-emerald">{{ confirmedCount() }}</span>
            <span class="kpi-caption">Asentadas en PostgreSQL</span>
          </div>
        </div>

        <div class="kpi-card" [class.active-kpi]="activeFilter() === 'CONFLICT'" [class.kpi-alert-pulse]="conflictCount() > 0" (click)="setFilter('CONFLICT')">
          <div class="kpi-icon-wrap kpi-conflict">
            <span class="material-symbols-outlined">report</span>
          </div>
          <div class="kpi-data">
            <div class="kpi-label-row">
              <span class="kpi-label">CONFLICTOS / SOBREVENTA</span>
              @if (conflictCount() > 0) {
                <span class="badge-attn">¡Atención!</span>
              }
            </div>
            <span class="kpi-value text-rose">{{ conflictCount() }}</span>
            <span class="kpi-caption">{{ conflictCount() > 0 ? 'Requieren resolución comercial' : 'Sin discrepancias' }}</span>
          </div>
        </div>
      </div>

      <!-- Panel principal y tabla de operaciones -->
      <div class="tray-panel">
        <div class="panel-header">
          <div class="panel-title-group">
            <h3 class="panel-title">
              Historial de Operaciones Locales ({{ operations().length }})
            </h3>
            <span class="panel-subtitle">Auditoría detallada del almacenamiento local Outbox</span>
          </div>

          <!-- Filtros de pestaña -->
          <div class="filter-tabs">
            <button
              type="button"
              class="filter-tab"
              [class.active]="activeFilter() === 'ALL'"
              (click)="setFilter('ALL')"
            >
              Todas ({{ totalCount() }})
            </button>
            <button
              type="button"
              class="filter-tab"
              [class.active]="activeFilter() === 'PENDING'"
              (click)="setFilter('PENDING')"
            >
              Pendientes ({{ pendingCount() }})
            </button>
            <button
              type="button"
              class="filter-tab"
              [class.active]="activeFilter() === 'CONFIRMED'"
              (click)="setFilter('CONFIRMED')"
            >
              Confirmadas ({{ confirmedCount() }})
            </button>
            <button
              type="button"
              class="filter-tab tab-conflict"
              [class.active]="activeFilter() === 'CONFLICT'"
              (click)="setFilter('CONFLICT')"
            >
              Conflictos ({{ conflictCount() }})
            </button>
          </div>
        </div>

        @if (filteredOperations().length === 0) {
          <div class="empty-state">
            <div class="empty-icon-wrap">
              <span class="material-symbols-outlined">inbox</span>
            </div>
            <h4>Sin operaciones en este filtro</h4>
            <p>
              @if (activeFilter() === 'ALL') {
                No hay operaciones offline registradas en este dispositivo.
              } @else if (activeFilter() === 'CONFLICT') {
                Excelente: no hay conflictos de stock ni transacciones rechazadas en este equipo.
              } @else {
                No hay transacciones en el filtro seleccionado ({{ activeFilter() }}).
              }
            </p>
          </div>
        } @else {
          <div class="table-responsive">
            <table class="tray-table">
              <thead>
                <tr>
                  <th>TIPO</th>
                  <th>ID DE OPERACIÓN</th>
                  <th>SUCURSAL</th>
                  <th>CLIENTE</th>
                  <th>MONTO / ITEMS</th>
                  <th>ESTADO</th>
                  <th>RESULTADO / CONFLICTO</th>
                  <th>FECHA LOCAL</th>
                </tr>
              </thead>
              <tbody>
                @for (op of filteredOperations(); track op.client_operation_id) {
                  <tr class="tray-row" [class.row-conflict]="op.status === 'CONFLICT'">
                    <!-- Tipo de Operación -->
                    <td>
                      @if (op.operation_type === 'SALE') {
                        <span class="badge-type badge-type-sale">
                          <span class="material-symbols-outlined badge-mini-icon">shopping_bag</span>
                          VENTA
                        </span>
                      } @else {
                        <span class="badge-type badge-type-reservation">
                          <span class="material-symbols-outlined badge-mini-icon">bookmark</span>
                          RESERVA
                        </span>
                      }
                    </td>

                    <!-- ID Único de Operación -->
                    <td>
                      <span class="op-id-chip" [title]="op.client_operation_id">
                        {{ op.client_operation_id }}
                      </span>
                    </td>

                    <!-- Sucursal -->
                    <td>
                      <span class="branch-tag">#{{ op.branch_id }}</span>
                    </td>

                    <!-- Datos del Cliente -->
                    <td>
                      @if (op.operation_type === 'SALE' && op.sale_payload) {
                        <div class="customer-cell">
                          <div class="customer-avatar">
                            {{ getCustomerInitials(op.sale_payload.customer_name) }}
                          </div>
                          <div class="customer-info">
                            <div class="customer-name">{{ op.sale_payload.customer_name || 'Consumidor Final' }}</div>
                            <div class="customer-meta">
                              CI/NIT: {{ op.sale_payload.customer_nit || '0' }}{{ op.sale_payload.customer_phone ? ' · Tel: ' + op.sale_payload.customer_phone : '' }}
                            </div>
                          </div>
                        </div>
                      } @else if (op.operation_type === 'RESERVATION' && op.reservation_payload) {
                        <div class="customer-cell">
                          <div class="customer-avatar avatar-reservation">
                            {{ getCustomerInitials(op.reservation_payload.customer_name) }}
                          </div>
                          <div class="customer-info">
                            <div class="customer-name">{{ op.reservation_payload.customer_name || 'Cliente Reserva' }}</div>
                            <div class="customer-meta">
                              {{ op.reservation_payload.customer_nit ? 'CI/NIT: ' + op.reservation_payload.customer_nit + ' · ' : '' }}{{ op.reservation_payload.customer_phone ? 'Tel: ' + op.reservation_payload.customer_phone : '' }}
                            </div>
                          </div>
                        </div>
                      } @else {
                        <span class="text-muted">-</span>
                      }
                    </td>

                    <!-- Monto / Prendas -->
                    <td>
                      @if (op.operation_type === 'SALE' && op.sale_payload) {
                        <div class="amount-main">Bs {{ op.sale_payload.total | number:'1.2-2' }}</div>
                        <div class="amount-sub">({{ op.sale_payload.items.length }} items)</div>
                      } @else if (op.operation_type === 'RESERVATION' && op.reservation_payload) {
                        <div class="amount-main">{{ op.reservation_payload.items.length }} prendas</div>
                        <div class="amount-sub">Apartadas en tienda</div>
                      }
                    </td>

                    <!-- Estado de Sincronización -->
                    <td>
                      @if (op.status === 'PENDING_SYNC') {
                        <span class="status-pill status-pending">
                          <span class="pulse-dot"></span>
                          Pendiente
                        </span>
                      } @else if (op.status === 'CONFIRMED') {
                        <span class="status-pill status-confirmed">
                          <span class="material-symbols-outlined status-icon">check</span>
                          Confirmada
                        </span>
                      } @else if (op.status === 'CONFLICT') {
                        <span class="status-pill status-conflict">
                          <span class="material-symbols-outlined status-icon">warning</span>
                          Conflicto
                        </span>
                      } @else {
                        <span class="status-pill status-neutral">
                          {{ op.status }}
                        </span>
                      }
                    </td>

                    <!-- Resultado Central / Conflicto -->
                    <td>
                      @if (op.order_number) {
                        <div class="server-ref ref-sale">
                          <span class="material-symbols-outlined ref-icon">task_alt</span>
                          <span>Venta: {{ op.order_number }}</span>
                        </div>
                      } @else if (op.reservation_id) {
                        <div class="server-ref ref-res">
                          <span class="material-symbols-outlined ref-icon">task_alt</span>
                          <span>Reserva #{{ op.reservation_id }}</span>
                        </div>
                      } @else if (op.conflict_detail) {
                        <div class="conflict-card-enhanced">
                          <div class="conflict-header-pill">
                            <span class="material-symbols-outlined conflict-alert-icon">report_problem</span>
                            <span class="conflict-code">{{ op.conflict_detail.code }}</span>
                          </div>
                          <div class="conflict-msg-box">
                            {{ op.conflict_detail.message }}
                          </div>
                          <button
                            type="button"
                            class="btn-conflict-action"
                            (click)="selectedConflict.set(op)"
                          >
                            <span class="material-symbols-outlined btn-icon">support_agent</span>
                            <span>Protocolo de Resolución</span>
                          </button>
                        </div>
                      } @else {
                        <span class="text-muted">-</span>
                      }
                    </td>

                    <!-- Fecha local -->
                    <td>
                      <span class="date-tag">{{ op.created_at | date:'short' }}</span>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      </div>

      <!-- Modal de Protocolo de Resolución de Conflictos Comerciales -->
      @if (selectedConflict()) {
        <div class="modal-backdrop" (click)="selectedConflict.set(null)">
          <div class="modal-dialog" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <div class="modal-header-icon">
                <span class="material-symbols-outlined">gavel</span>
              </div>
              <div>
                <h3 class="modal-title">Protocolo de Resolución de Conflicto</h3>
                <p class="modal-subtitle">Directrices Comerciales para Sobreventa Offline (Pliego Parcial 2)</p>
              </div>
              <button type="button" class="modal-close-btn" (click)="selectedConflict.set(null)">✕</button>
            </div>

            <div class="modal-body">
              <!-- Alerta de diagnóstico -->
              <div class="modal-alert-box">
                <span class="material-symbols-outlined alert-box-icon">warning</span>
                <div>
                  <strong>Diagnóstico de Consistencia:</strong>
                  <p class="mb-0">
                    {{ selectedConflict()?.conflict_detail?.message || 'Stock central insuficiente para la variante solicitada.' }}
                  </p>
                </div>
              </div>

              <!-- Ficha de la transacción -->
              <div class="modal-details-grid">
                <div class="detail-item">
                  <span class="detail-label">ID de Operación</span>
                  <span class="detail-value font-mono">{{ selectedConflict()?.client_operation_id }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Sucursal Emisora</span>
                  <span class="detail-value">Sucursal #{{ selectedConflict()?.branch_id }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Cliente Asociado</span>
                  <span class="detail-value">
                    {{ selectedConflict()?.sale_payload?.customer_name || selectedConflict()?.reservation_payload?.customer_name || 'Consumidor Final' }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Contacto / Teléfono</span>
                  <span class="detail-value">
                    {{ selectedConflict()?.sale_payload?.customer_phone || selectedConflict()?.reservation_payload?.customer_phone || 'Sin teléfono' }}
                  </span>
                </div>
              </div>

              <!-- Planes de acción comercial según pliego del parcial -->
              <h4 class="action-plans-title">Opciones de Resolución Comercial (Cajero / Administrador):</h4>

              <div class="resolution-options">
                <div class="resolution-option-card">
                  <div class="option-icon-box icon-transfer">
                    <span class="material-symbols-outlined">local_shipping</span>
                  </div>
                  <div class="option-content">
                    <h5>1. Traslado Inter-Sucursal</h5>
                    <p>Solicitar transferencia inmediata de la prenda desde otra sucursal de la empresa que cuente con existencias centrales.</p>
                  </div>
                </div>

                <div class="resolution-option-card">
                  <div class="option-icon-box icon-exchange">
                    <span class="material-symbols-outlined">swap_horiz</span>
                  </div>
                  <div class="option-content">
                    <h5>2. Cambio por Prenda Equivalente</h5>
                    <p>Contactar al cliente y ofrecerle una variante del mismo valor o prenda de la nueva colección de temporada.</p>
                    <button type="button" class="btn-res-link" (click)="goToExchange()">
                      <span class="material-symbols-outlined btn-mini">swap_horiz</span>
                      Ir al Módulo de Cambios
                    </button>
                  </div>
                </div>

                <div class="resolution-option-card">
                  <div class="option-icon-box icon-credit">
                    <span class="material-symbols-outlined">receipt</span>
                  </div>
                  <div class="option-content">
                    <h5>3. Emisión de Nota de Crédito / Reembolso</h5>
                    <p>Generar nota de crédito con código de canje para futuras compras o reintegrar el efectivo recibido.</p>
                    <button type="button" class="btn-res-link" (click)="goToPos()">
                      <span class="material-symbols-outlined btn-mini">point_of_sale</span>
                      Ir al POS para Emitir Nota
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="button button-outline" (click)="selectedConflict.set(null)">
                Cerrar
              </button>
              <button
                type="button"
                class="button button-resolve"
                (click)="resolveAndArchiveConflict(selectedConflict()!)"
              >
                <span class="material-symbols-outlined">archive</span>
                Marcar como Resuelto y Archivar
              </button>
            </div>
          </div>
        </div>
      }
    </section>
  `,
  styles: [`
    .offline-tray-container {
      padding: 2rem 1.5rem;
      max-width: 1320px;
      margin: 0 auto;
      font-family: inherit;
    }

    /* Encabezado */
    .tray-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 2rem;
      gap: 1.5rem;
      flex-wrap: wrap;
    }
    .tray-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      color: #b8924a;
      text-transform: uppercase;
      margin-bottom: 0.35rem;
    }
    .eyebrow-icon {
      font-size: 1rem;
    }
    .tray-title {
      font-size: 2.2rem;
      font-family: 'Playfair Display', Georgia, serif;
      font-weight: 700;
      color: #0f172a;
      margin: 0 0 0.5rem 0;
      letter-spacing: -0.02em;
    }
    .tray-subtitle {
      color: #64748b;
      font-size: 0.95rem;
      max-width: 650px;
      line-height: 1.5;
      margin: 0;
    }

    /* Acciones superiores */
    .tray-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .button-refresh {
      background: #ffffff;
      color: #334155;
      border: 1px solid #cbd5e1;
      padding: 0.65rem 1.1rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .button-refresh:hover {
      background: #f8fafc;
      border-color: #94a3b8;
    }
    .button-sync {
      background: #0f172a;
      color: #ffffff;
      border: 1px solid #b8924a;
      padding: 0.65rem 1.3rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
      transition: all 0.2s ease;
    }
    .button-sync:hover:not(:disabled) {
      background: #1e293b;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(15, 23, 42, 0.2);
    }
    .button-sync:disabled {
      opacity: 0.55;
      cursor: not-allowed;
      box-shadow: none;
    }
    .spinning {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    /* Banners de estado */
    .sync-banner {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1rem 1.25rem;
      border-radius: 10px;
      margin-bottom: 1.5rem;
      font-size: 0.9rem;
      animation: fadeIn 0.3s ease;
    }
    .banner-success {
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      color: #065f46;
    }
    .banner-warning {
      background: #fff1f2;
      border: 1px solid #fecdd3;
      color: #9f1239;
    }
    .banner-error {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
    }
    .banner-icon {
      font-size: 1.35rem;
      flex-shrink: 0;
    }
    .banner-content {
      flex: 1;
      line-height: 1.4;
    }
    .banner-close {
      background: transparent;
      border: none;
      color: inherit;
      font-size: 1.1rem;
      cursor: pointer;
      opacity: 0.7;
    }
    .banner-close:hover {
      opacity: 1;
    }

    /* Tarjetas KPI */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.2rem;
      margin-bottom: 1.8rem;
    }
    .kpi-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.2rem 1.25rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .kpi-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07);
      border-color: #cbd5e1;
    }
    .active-kpi {
      border-color: #0f172a;
      box-shadow: 0 0 0 2px #0f172a;
    }
    .kpi-alert-pulse {
      border-color: #f43f5e;
      background: #fff5f5;
      box-shadow: 0 0 0 2px rgba(244, 63, 94, 0.2);
    }
    .kpi-icon-wrap {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .kpi-all { background: #f1f5f9; color: #334155; }
    .kpi-pending { background: #fffbeb; color: #b45309; }
    .kpi-confirmed { background: #ecfdf5; color: #047857; }
    .kpi-conflict { background: #fef2f2; color: #b91c1c; }

    .kpi-data {
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    .kpi-label-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .kpi-label {
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      color: #64748b;
      margin-bottom: 0.15rem;
    }
    .badge-attn {
      background: #e11d48;
      color: #ffffff;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
      letter-spacing: 0.02em;
    }
    .kpi-value {
      font-size: 1.7rem;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.1;
      font-family: 'Playfair Display', Georgia, serif;
    }
    .kpi-caption {
      font-size: 0.75rem;
      color: #94a3b8;
      margin-top: 0.2rem;
    }
    .text-amber { color: #b45309; }
    .text-emerald { color: #047857; }
    .text-rose { color: #b91c1c; }

    /* Panel Principal */
    .tray-panel {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
      overflow: hidden;
    }
    .panel-header {
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid #f1f5f9;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .panel-title {
      font-size: 1.25rem;
      font-family: 'Playfair Display', Georgia, serif;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
    }
    .panel-subtitle {
      font-size: 0.8rem;
      color: #64748b;
      display: block;
      margin-top: 0.15rem;
    }

    /* Pestañas de filtro */
    .filter-tabs {
      display: flex;
      background: #f1f5f9;
      padding: 0.25rem;
      border-radius: 8px;
      gap: 0.2rem;
    }
    .filter-tab {
      background: transparent;
      border: none;
      padding: 0.4rem 0.85rem;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      color: #64748b;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .filter-tab:hover {
      color: #0f172a;
    }
    .filter-tab.active {
      background: #ffffff;
      color: #0f172a;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }
    .tab-conflict.active {
      background: #fff1f2;
      color: #be123c;
    }

    /* Tabla */
    .table-responsive {
      overflow-x: auto;
    }
    .tray-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.86rem;
    }
    .tray-table thead tr {
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
    }
    .tray-table th {
      padding: 0.85rem 1rem;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #64748b;
      white-space: nowrap;
    }
    .tray-row {
      border-bottom: 1px solid #f1f5f9;
      transition: background 0.15s ease;
    }
    .tray-row:hover {
      background: #fafaf9;
    }
    .row-conflict {
      background: #fffbfb;
    }
    .row-conflict:hover {
      background: #fff1f2;
    }
    .tray-table td {
      padding: 1rem;
      vertical-align: middle;
    }

    /* Tipo de operación */
    .badge-type {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.3rem 0.65rem;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.74rem;
      letter-spacing: 0.03em;
    }
    .badge-type-sale {
      background: #0f172a;
      color: #ffffff;
    }
    .badge-type-reservation {
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fde68a;
    }
    .badge-mini-icon {
      font-size: 0.95rem;
    }

    /* Chips e identificadores */
    .op-id-chip {
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 0.78rem;
      background: #f8fafc;
      color: #334155;
      padding: 0.25rem 0.5rem;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      display: inline-block;
      max-width: 170px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .branch-tag {
      background: #f1f5f9;
      color: #475569;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
      font-size: 0.8rem;
    }

    /* Celda de Cliente */
    .customer-cell {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .customer-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #f5efe6;
      color: #8c6d33;
      border: 1px solid #e3d3be;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.75rem;
      flex-shrink: 0;
    }
    .avatar-reservation {
      background: #fef3c7;
      color: #92400e;
      border-color: #fde68a;
    }
    .customer-info {
      display: flex;
      flex-direction: column;
    }
    .customer-name {
      font-weight: 600;
      color: #0f172a;
    }
    .customer-meta {
      font-size: 0.75rem;
      color: #64748b;
    }

    /* Monto */
    .amount-main {
      font-weight: 700;
      color: #0f172a;
    }
    .amount-sub {
      font-size: 0.75rem;
      color: #64748b;
    }

    /* Pills de Estado */
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.3rem 0.75rem;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.76rem;
      white-space: nowrap;
    }
    .status-pending {
      background: #fffbeb;
      color: #b45309;
      border: 1px solid #fde68a;
    }
    .pulse-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #d97706;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }
    .status-confirmed {
      background: #ecfdf5;
      color: #047857;
      border: 1px solid #a7f3d0;
    }
    .status-conflict {
      background: #fff1f2;
      color: #be123c;
      border: 1px solid #fecdd3;
    }
    .status-neutral {
      background: #f1f5f9;
      color: #475569;
    }
    .status-icon {
      font-size: 0.95rem;
    }

    /* Referencias del Servidor */
    .server-ref {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-weight: 600;
      font-size: 0.82rem;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
    }
    .ref-sale {
      background: #f0fdf4;
      color: #15803d;
      border: 1px solid #bbf7d0;
    }
    .ref-res {
      background: #f0fdf4;
      color: #15803d;
      border: 1px solid #bbf7d0;
    }
    .ref-icon {
      font-size: 1rem;
    }

    /* Tarjeta de Conflicto Mejorada */
    .conflict-card-enhanced {
      background: #fff1f2;
      border: 1px solid #fecdd3;
      border-radius: 8px;
      padding: 0.5rem 0.65rem;
      max-width: 320px;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }
    .conflict-header-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
    }
    .conflict-alert-icon {
      font-size: 1rem;
      color: #e11d48;
    }
    .conflict-code {
      font-weight: 700;
      font-size: 0.72rem;
      color: #be123c;
      letter-spacing: 0.04em;
    }
    .conflict-msg-box {
      font-size: 0.75rem;
      color: #881337;
      line-height: 1.35;
    }
    .btn-conflict-action {
      background: #ffffff;
      border: 1px solid #f43f5e;
      color: #be123c;
      padding: 0.25rem 0.5rem;
      border-radius: 5px;
      font-size: 0.72rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      cursor: pointer;
      align-self: flex-start;
      margin-top: 0.2rem;
      transition: all 0.15s ease;
    }
    .btn-conflict-action:hover {
      background: #be123c;
      color: #ffffff;
    }
    .btn-icon {
      font-size: 0.9rem;
    }

    .date-tag {
      font-size: 0.8rem;
      color: #64748b;
      white-space: nowrap;
    }
    .text-muted {
      color: #94a3b8;
    }

    /* Empty state */
    .empty-state {
      padding: 3.5rem 1.5rem;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .empty-icon-wrap {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #f1f5f9;
      color: #94a3b8;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1rem;
    }
    .empty-state h4 {
      margin: 0 0 0.4rem 0;
      font-size: 1.1rem;
      color: #1e293b;
      font-family: 'Playfair Display', Georgia, serif;
    }
    .empty-state p {
      margin: 0;
      font-size: 0.88rem;
      color: #64748b;
      max-width: 400px;
    }

    /* Modal de Protocolo de Resolución */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 1.5rem;
      animation: fadeIn 0.2s ease;
    }
    .modal-dialog {
      background: #ffffff;
      border-radius: 16px;
      max-width: 640px;
      width: 100%;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
      overflow: hidden;
      animation: scaleUp 0.2s ease;
    }
    .modal-header {
      padding: 1.25rem 1.5rem;
      background: #0f172a;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 1rem;
      position: relative;
    }
    .modal-header-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: #b8924a;
      color: #0f172a;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .modal-title {
      font-size: 1.25rem;
      font-family: 'Playfair Display', Georgia, serif;
      margin: 0;
      font-weight: 700;
      color: #ffffff;
    }
    .modal-subtitle {
      font-size: 0.8rem;
      color: #cbd5e1;
      margin: 0.2rem 0 0 0;
    }
    .modal-close-btn {
      position: absolute;
      right: 1.25rem;
      top: 1.25rem;
      background: transparent;
      border: none;
      color: #94a3b8;
      font-size: 1.3rem;
      cursor: pointer;
    }
    .modal-close-btn:hover {
      color: #ffffff;
    }
    .modal-body {
      padding: 1.5rem;
      max-height: 70vh;
      overflow-y: auto;
    }
    .modal-alert-box {
      background: #fff1f2;
      border: 1px solid #fecdd3;
      border-radius: 10px;
      padding: 0.9rem 1rem;
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
      color: #881337;
      font-size: 0.88rem;
      margin-bottom: 1.25rem;
    }
    .alert-box-icon {
      font-size: 1.4rem;
      color: #e11d48;
      flex-shrink: 0;
    }
    .modal-details-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.85rem;
      background: #f8fafc;
      padding: 1rem;
      border-radius: 10px;
      border: 1px solid #e2e8f0;
      margin-bottom: 1.5rem;
    }
    .detail-item {
      display: flex;
      flex-direction: column;
    }
    .detail-label {
      font-size: 0.72rem;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .detail-value {
      font-size: 0.88rem;
      font-weight: 600;
      color: #0f172a;
    }
    .font-mono {
      font-family: monospace;
      font-size: 0.78rem;
    }
    .action-plans-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: #0f172a;
      margin: 0 0 0.85rem 0;
    }
    .resolution-options {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .resolution-option-card {
      display: flex;
      gap: 0.85rem;
      align-items: flex-start;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 0.85rem 1rem;
      transition: all 0.15s ease;
    }
    .resolution-option-card:hover {
      border-color: #b8924a;
      background: #faf8f5;
    }
    .option-icon-box {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .icon-transfer { background: #e0f2fe; color: #0284c7; }
    .icon-exchange { background: #fef3c7; color: #b45309; }
    .icon-credit { background: #f3e8ff; color: #7e22ce; }
    .option-content h5 {
      margin: 0 0 0.2rem 0;
      font-size: 0.86rem;
      font-weight: 700;
      color: #0f172a;
    }
    .option-content p {
      margin: 0;
      font-size: 0.8rem;
      color: #64748b;
      line-height: 1.35;
    }
    .btn-res-link {
      margin-top: 0.5rem;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      color: #0f172a;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-res-link:hover {
      background: #0f172a;
      color: #ffffff;
      border-color: #0f172a;
    }
    .btn-mini {
      font-size: 0.95rem;
    }
    .modal-footer {
      padding: 1rem 1.5rem;
      background: #f8fafc;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
    }
    .button-outline {
      background: #ffffff;
      color: #475569;
      border: 1px solid #cbd5e1;
      padding: 0.6rem 1.1rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
    }
    .button-outline:hover {
      background: #f1f5f9;
    }
    .button-resolve {
      background: #047857;
      color: #ffffff;
      border: 1px solid #059669;
      padding: 0.6rem 1.25rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      cursor: pointer;
    }
    .button-resolve:hover {
      background: #065f46;
    }
    .button-primary {
      background: #0f172a;
      color: #ffffff;
      border: 1px solid #b8924a;
      padding: 0.6rem 1.25rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
    }
    .button-primary:hover {
      background: #1e293b;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes scaleUp {
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
  `],
})
export class OfflineTransactionsTrayComponent implements OnInit {
  private router = inject(Router);
  private offlineTx = inject(OfflineTransactionService);
  readonly syncService = inject(SyncTransactionService);

  readonly operations = signal<OfflineOperationRecord[]>([]);
  readonly syncMessage = signal<string | null>(null);
  readonly activeFilter = signal<FilterType>('ALL');
  readonly selectedConflict = signal<OfflineOperationRecord | null>(null);

  readonly totalCount = computed(() => this.operations().length);
  readonly pendingCount = computed(() => this.operations().filter((o) => o.status === 'PENDING_SYNC').length);
  readonly confirmedCount = computed(() => this.operations().filter((o) => o.status === 'CONFIRMED').length);
  readonly conflictCount = computed(() => this.operations().filter((o) => o.status === 'CONFLICT').length);

  readonly filteredOperations = computed(() => {
    const filter = this.activeFilter();
    const ops = this.operations();
    if (filter === 'PENDING') return ops.filter((o) => o.status === 'PENDING_SYNC');
    if (filter === 'CONFIRMED') return ops.filter((o) => o.status === 'CONFIRMED');
    if (filter === 'CONFLICT') return ops.filter((o) => o.status === 'CONFLICT');
    return ops;
  });

  ngOnInit(): void {
    this.loadOperations();
  }

  setFilter(filter: FilterType): void {
    this.activeFilter.set(filter);
  }

  getCustomerInitials(name?: string | null): string {
    if (!name || !name.trim()) return 'CF';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  async loadOperations(): Promise<void> {
    const list = await this.offlineTx.listOperations();
    this.operations.set(list);
    await this.syncService.refreshPendingCount();
  }

  goToExchange(): void {
    this.selectedConflict.set(null);
    this.router.navigate(['/pos'], { queryParams: { mode: 'EXCHANGE' } });
  }

  goToPos(): void {
    this.selectedConflict.set(null);
    this.router.navigate(['/pos']);
  }

  async resolveAndArchiveConflict(op: OfflineOperationRecord): Promise<void> {
    if (!op) return;
    await this.offlineTx.deleteOperation(op.client_operation_id);
    this.selectedConflict.set(null);
    this.syncMessage.set(`✓ Conflicto de la operación ${op.client_operation_id} marcado como resuelto y archivado del Outbox.`);
    await this.loadOperations();
  }

  async syncNow(): Promise<void> {
    this.syncMessage.set(null);
    const res = await this.syncService.syncPendingTransactions();
    if (res) {
      if (res.conflict_count > 0) {
        this.syncMessage.set(
          `Sincronización completada: ${res.confirmed_count} confirmadas, ${res.conflict_count} con CONFLICTO por stock insuficiente. Revisa las operaciones marcadas para su resolución comercial.`
        );
      } else {
        this.syncMessage.set(
          `Sincronización completada: ${res.confirmed_count} confirmadas, 0 en conflicto/rechazadas.`
        );
      }
    }
    await this.loadOperations();
  }
}
