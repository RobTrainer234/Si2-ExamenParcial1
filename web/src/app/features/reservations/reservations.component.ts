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
      @if (!loading && reservations.length) { <div class="operations-table-card"><div class="table-wrap"><table><thead><tr><th>Cliente</th><th>Visita</th><th>Prendas</th><th>Estado</th><th>Acción</th></tr></thead><tbody>@for (reservation of reservations; track reservation.id) { <tr><td><strong>{{ reservation.customer_name }}</strong><small>Reserva #{{ reservation.id }}</small></td><td>{{ reservation.scheduled_for ? (reservation.scheduled_for | date:'short') : 'Sin horario' }}</td><td>@for (item of reservation.items; track item.id) { <small>{{ item.quantity }} × {{ item.product_name }} ({{ item.size_name }} · {{ item.color_name }})</small> }</td><td><span class="status-pill" [class.active]="reservation.status === 'READY' || reservation.status === 'ATTENDED'">{{ statusLabel(reservation.status) }}</span></td><td>@if (nextStatus(reservation.status); as next) { <button class="small-button" type="button" (click)="changeStatus(reservation, next)">{{ statusLabel(next) }}</button> }</td></tr> }</tbody></table></div></div> }
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
    this.api.branches().subscribe({ next: (page) => { this.branches = page.items; }, error: () => this.error = true });
  }

  load(): void {
    if (!this.selectedBranchId) { this.reservations = []; return; }
    this.loading = true;
    this.api.reservations(this.selectedBranchId).subscribe({ next: (page) => { this.reservations = page.items; this.loading = false; }, error: () => { this.error = true; this.loading = false; } });
  }

  nextStatus(status: ReservationStatus): ReservationStatus | null {
    return ({ PENDING: 'PREPARING', PREPARING: 'READY', READY: 'ATTENDED' } as Partial<Record<ReservationStatus, ReservationStatus>>)[status] ?? null;
  }

  statusLabel(status: ReservationStatus): string { return ({ PENDING: 'Pendiente', PREPARING: 'En preparación', READY: 'Lista', ATTENDED: 'Atendida', CANCELLED: 'Cancelada', EXPIRED: 'Vencida' } as Record<ReservationStatus, string>)[status]; }

  changeStatus(reservation: Reservation, status: ReservationStatus): void { this.api.updateReservationStatus(reservation.id, status).subscribe({ next: (updated) => Object.assign(reservation, updated), error: () => this.error = true }); }
}
