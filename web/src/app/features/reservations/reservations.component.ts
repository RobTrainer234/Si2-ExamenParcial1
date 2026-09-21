import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { AdminService } from '../../core/admin/admin.service';
import { Branch, Reservation, ReservationStatus } from '../../core/models/admin.models';

@Component({
  standalone: true,
  imports: [DatePipe, FormsModule],
  template: `
    <section class="operations-page">
      <div class="admin-heading"><div><p class="eyebrow">Sucursal</p><h2>Atención de reservas</h2><p class="admin-subtitle">Prepara las prendas y registra el resultado de cada visita.</p></div></div>
      <label class="location-search">Sucursal<select [(ngModel)]="selectedBranchId" (change)="load()"><option [ngValue]="null">Selecciona una sucursal</option>@for (branch of branches; track branch.id) { <option [ngValue]="branch.id">{{ branch.name }}</option> }</select></label>
      @if (error) { <p class="error admin-alert">No se pudieron cargar las reservas.</p> }
      @if (loading) { <p class="loading page-message">Cargando reservas...</p> }
      @if (!loading && selectedBranchId && !reservations.length) { <p class="empty page-message">No hay reservas para esta sucursal.</p> }
       @if (!loading && reservations.length) { <div class="reservation-queue"><div class="reservation-queue-header"><div><span class="panel-index">COLA ACTIVA</span><h3>{{ reservations.length }} {{ reservations.length === 1 ? 'reserva pendiente' : 'reservas pendientes' }}</h3></div><span class="queue-indicator"><i></i> Atención requerida</span></div>@for (reservation of reservations; track reservation.id) { <article class="reservation-card"><div class="reservation-card-top"><div class="reservation-number"><span>RESERVA</span><strong>#{{ reservation.id }}</strong></div><span class="status-pill" [class.active]="reservation.status === 'READY' || reservation.status === 'ATTENDED'" [class.status-preparing]="reservation.status === 'PREPARING'">{{ statusLabel(reservation.status) }}</span></div><div class="reservation-card-info"><div class="reservation-person"><span class="reservation-icon material-symbols-outlined">person</span><div><span>Cliente</span><strong>{{ reservation.customer_name }}</strong></div></div><div class="reservation-visit"><span class="reservation-icon material-symbols-outlined">event</span><div><span>Visita programada</span><strong>{{ reservation.scheduled_for ? (reservation.scheduled_for | date:'EEE, d MMM · h:mm a') : 'Sin horario' }}</strong></div></div></div><div class="reservation-items"><span class="reservation-items-label">Prendas reservadas</span><div>@for (item of reservation.items; track item.id) { <span class="reservation-item"><b>{{ item.quantity }}×</b>{{ item.product_name }}<small>{{ item.size_name }} · {{ item.color_name }}</small></span> }</div></div><div class="reservation-card-footer"><span class="reservation-reference">Sucursal · {{ reservation.branch_name }}</span><div class="reservation-actions">@if (nextStatus(reservation.status); as next) { <button class="button button-dark" type="button" (click)="changeStatus(reservation, next)">{{ statusLabel(next) }} <span class="material-symbols-outlined">arrow_forward</span></button> } @if (canCancel(reservation.status)) { <button class="reservation-text-action" type="button" (click)="changeStatus(reservation, 'CANCELLED')">Cancelar</button> } @if (canExpire(reservation)) { <button class="reservation-text-action" type="button" (click)="changeStatus(reservation, 'EXPIRED')">Vencer</button> }</div></div></article> }</div> }
    </section>
  `,
})
export class ReservationsComponent {
  private readonly api = inject(AdminService);
  branches: Branch[] = [];
  reservations: Reservation[] = [];
  selectedBranchId: number | null = null;
  loading = false;
  error = false;

  constructor() {
    this.api.reservationBranches().subscribe({ next: (page) => { this.branches = page.items; }, error: () => this.error = true });
  }

  load(): void {
    if (!this.selectedBranchId) { this.reservations = []; return; }
    this.loading = true;
    this.api.reservations(this.selectedBranchId).subscribe({ next: (page) => { this.reservations = page.items; this.loading = false; }, error: () => { this.error = true; this.loading = false; } });
  }

  nextStatus(status: ReservationStatus): ReservationStatus | null {
    return ({ PENDING: 'PREPARING', PREPARING: 'READY', READY: 'ATTENDED' } as Partial<Record<ReservationStatus, ReservationStatus>>)[status] ?? null;
  }

  canCancel(status: ReservationStatus): boolean { return status === 'PENDING' || status === 'PREPARING' || status === 'READY'; }
  canExpire(reservation: Reservation): boolean { return this.canCancel(reservation.status) && !!reservation.expires_at && new Date(reservation.expires_at) <= new Date(); }

  statusLabel(status: ReservationStatus): string { return ({ PENDING: 'Pendiente', PREPARING: 'En preparación', READY: 'Lista', ATTENDED: 'Atendida', CANCELLED: 'Cancelada', EXPIRED: 'Vencida' } as Record<ReservationStatus, string>)[status]; }

  changeStatus(reservation: Reservation, status: ReservationStatus): void { this.api.updateReservationStatus(reservation.id, status).subscribe({ next: (updated) => Object.assign(reservation, updated), error: () => this.error = true }); }
}
