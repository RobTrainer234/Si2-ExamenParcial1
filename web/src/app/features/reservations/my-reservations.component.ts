import { DatePipe } from '@angular/common';
import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';

import { ReservationService } from '../../core/reservations/reservation.service';
import { Reservation, ReservationStatus } from '../../core/models/admin.models';

type ReservationFilter = 'all' | 'active' | 'history' | 'cancelled';

@Component({
  standalone: true,
  imports: [DatePipe, RouterLink],
  template: `
    <section class="operations-page customer-reservations" aria-labelledby="my-reservations-title">
      <header class="customer-reservations-hero">
        <div>
          <p class="eyebrow">Tu cuenta</p>
          <h2 id="my-reservations-title">Mis reservas</h2>
          <p class="admin-subtitle">Seguimos tus prendas apartadas, la visita a sucursal y el estado de cada reserva.</p>
        </div>
      </header>

      @if (error) { <p class="error admin-alert" role="alert">{{ error }}</p> }
      @if (loading) { <p class="loading page-message" aria-live="polite">Cargando reservas...</p> }
      @if (!loading && !reservations.length) { <p class="empty page-message">Todavía no tienes reservas.</p> }

      @if (!loading && reservations.length) {
        <section class="reservation-summary-strip" aria-label="Resumen de reservas">
          <div>
            <span>Total</span>
            <strong>{{ reservations.length }}</strong>
            <small>reservas registradas</small>
          </div>
          <div>
            <span>Activas</span>
            <strong>{{ filterCount('active') }}</strong>
            <small>Pendientes, en preparación o listas para visita</small>
          </div>
          <div>
            <span>Historial</span>
            <strong>{{ filterCount('history') }}</strong>
            <small>Atendidas o vencidas quedan como referencia</small>
          </div>
        </section>

        <div class="reservation-filter-bar" aria-label="Filtros de reservas">
          @for (option of filterOptions; track option.value) {
            <button type="button" [class.selected]="filter === option.value" [attr.aria-pressed]="filter === option.value" (click)="setFilter(option.value)">
              <span>{{ option.label }}</span>
              <strong>{{ filterCount(option.value) }}</strong>
            </button>
          }
        </div>

        @if (!filteredReservations.length) {
          <p class="empty page-message">No hay reservas para este filtro.</p>
        } @else {
          <section class="reservation-list" aria-label="Listado de reservas">
            @for (reservation of filteredReservations; track reservation.id) {
              <a class="reservation-card customer-reservation-card" [routerLink]="['/my-reservations', reservation.id]" [attr.aria-label]="'Ver detalle de reserva ' + reservationCode(reservation)">
                <div class="reservation-card-top">
                  <div class="reservation-number">
                    <span>Código</span>
                    <strong>{{ reservationCode(reservation) }}</strong>
                  </div>
                  <span class="status-pill" [class.active]="isActiveStatus(reservation.status)" [class.status-preparing]="reservation.status === 'PREPARING'">{{ statusLabel(reservation.status) }}</span>
                </div>

                <div class="customer-reservation-grid">
                  <div>
                    <span class="reservation-field-label">Sucursal</span>
                    <strong>{{ reservation.branch_name }}</strong>
                    <small class="reservation-field-note">{{ branchLocation(reservation) }}</small>
                  </div>
                  <div>
                    <span class="reservation-field-label">Visita programada</span>
                    <strong>{{ reservation.scheduled_for ? (reservation.scheduled_for | date:'medium') : 'Sin horario' }}</strong>
                  </div>
                  <div>
                    <span class="reservation-field-label">Contacto sucursal</span>
                    <strong>{{ reservation.branch_phone || 'Teléfono no informado' }}</strong>
                  </div>
                  <div>
                    <span class="reservation-field-label">Prendas</span>
                    <strong>{{ reservation.items.length }} {{ reservation.items.length === 1 ? 'ítem' : 'ítems' }}</strong>
                  </div>
                </div>

                <div class="customer-reservation-items" aria-label="Prendas reservadas">
                  @for (item of reservation.items.slice(0, 3); track item.id) {
                    <span>{{ item.quantity }}× {{ item.product_name }} <small>{{ item.size_name }} · {{ item.color_name }}</small></span>
                  }
                  @if (reservation.items.length > 3) { <span>+{{ reservation.items.length - 3 }} más</span> }
                </div>

                <div class="reservation-card-footer">
                  <span class="reservation-reference">Creada el {{ reservation.created_at | date:'mediumDate' }}</span>
                  <span class="reservation-detail-link">Ver detalle</span>
                </div>
              </a>
            }
          </section>
        }
      }

      @if (selected) {
        <article class="reservation-detail customer-reservation-detail" aria-labelledby="reservation-detail-title">
          <div class="reservation-detail-heading">
            <div>
              <p class="eyebrow">Detalle</p>
              <h3 id="reservation-detail-title">Reserva {{ reservationCode(selected) }}</h3>
              <div class="reservation-code-actions">
                <span>Código para retiro: <strong>{{ reservationCode(selected) }}</strong></span>
                <button class="small-button" type="button" (click)="copyReservationCode(selected)">Copiar código</button>
                @if (copyFeedback) { <small aria-live="polite">{{ copyFeedback }}</small> }
              </div>
            </div>
            <span class="status-pill" [class.active]="isActiveStatus(selected.status)">{{ statusLabel(selected.status) }}</span>
          </div>

          <div class="reservation-detail-grid" aria-label="Datos de la reserva">
            <div><span>Sucursal</span><strong>{{ selected.branch_name }}</strong><small>{{ branchLocation(selected) }}</small></div>
            <div><span>Visita</span><strong>{{ selected.scheduled_for ? (selected.scheduled_for | date:'medium') : 'Sin horario' }}</strong></div>
            <div><span>Vencimiento</span><strong>{{ selected.expires_at ? (selected.expires_at | date:'medium') : 'Sin fecha' }}</strong></div>
            <div><span>Estado</span><strong>{{ statusLabel(selected.status) }}</strong></div>
            <div><span>Teléfono</span><strong>{{ selected.branch_phone || 'No informado' }}</strong></div>
            <div><span>Coordenadas</span><strong>{{ coordinatesLabel(selected) }}</strong></div>
          </div>

          <section class="reservation-status-section" aria-labelledby="reservation-status-title">
            <h4 id="reservation-status-title">Línea de estado</h4>
            @if (isTerminalStatus(selected.status)) {
              <p class="reservation-terminal-state" role="status">{{ terminalStatusMessage(selected.status) }}</p>
            } @else {
              <ol class="reservation-timeline" aria-label="Progreso de reserva">
                @for (step of timelineSteps(selected.status); track step.status) {
                  <li [class.done]="step.done" [class.current]="step.current">
                    <span aria-hidden="true"></span>
                    <div>
                      <strong>{{ step.label }}</strong>
                      <small>{{ step.description }}</small>
                    </div>
                  </li>
                }
              </ol>
            }
          </section>

          <section class="reservation-detail-items" aria-labelledby="reservation-items-title">
            <h4 id="reservation-items-title">Prendas reservadas</h4>
            @for (item of selected.items; track item.id) {
              <div class="reservation-detail-item">
                <div>
                  <strong>{{ item.quantity }} × {{ item.product_name }}</strong>
                  <small>{{ item.size_name }} · {{ item.color_name }}</small>
                </div>
                <span>Bs {{ item.unit_price }}</span>
              </div>
            }
          </section>

          @if (selected.status === 'PENDING' || selected.status === 'PREPARING') {
            <button class="button button-dark" type="button" [disabled]="cancelling" (click)="requestCancel()">{{ cancelling ? 'Cancelando...' : 'Cancelar reserva' }}</button>
          }
        </article>
      }

      @if (showCancelDialog && selected) {
        <div class="reservation-dialog-backdrop" role="presentation">
          <section class="reservation-dialog" role="dialog" aria-modal="true" aria-labelledby="cancel-dialog-title" aria-describedby="cancel-dialog-copy">
            <p class="eyebrow">Confirmación</p>
            <h3 id="cancel-dialog-title">Cancelar reserva {{ reservationCode(selected) }}</h3>
            <p id="cancel-dialog-copy">Esta acción liberará las prendas apartadas y conservará la reserva en tu historial. No cambiaremos otros estados del flujo.</p>
            <div class="reservation-dialog-actions">
              <button class="button button-light" type="button" [disabled]="cancelling" (click)="closeCancelDialog()">Volver</button>
              <button class="button button-dark" type="button" [disabled]="cancelling" (click)="confirmCancel()">{{ cancelling ? 'Cancelando...' : 'Sí, cancelar' }}</button>
            </div>
          </section>
        </div>
      }
    </section>
  `,
})
export class MyReservationsComponent {
  private readonly api = inject(ReservationService);
  private readonly route = inject(ActivatedRoute);
  private readonly changeDetector = inject(ChangeDetectorRef);
  reservations: Reservation[] = [];
  selected: Reservation | null = null;
  loading = true;
  cancelling = false;
  error = '';
  filter: ReservationFilter = 'all';
  showCancelDialog = false;
  copyFeedback = '';
  readonly filterOptions: { value: ReservationFilter; label: string }[] = [
    { value: 'all', label: 'Todas' },
    { value: 'active', label: 'Activas' },
    { value: 'history', label: 'Historial' },
    { value: 'cancelled', label: 'Canceladas' },
  ];

  constructor() { this.load(); }

  get filteredReservations(): Reservation[] { return this.reservations.filter((reservation) => this.matchesFilter(reservation, this.filter)); }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api.mine().pipe(
      timeout({ each: 10000 }),
      finalize(() => { this.loading = false; this.changeDetector.detectChanges(); }),
    ).subscribe({ next: (page) => { this.reservations = page.items; const id = Number(this.route.snapshot.paramMap.get('id')); if (id) this.loadDetail(id); }, error: () => { this.error = 'No se pudieron cargar tus reservas. Intenta nuevamente.'; } });
  }

  loadDetail(id: number): void { this.api.get(id).subscribe({ next: (reservation) => { this.selected = reservation; this.copyFeedback = ''; this.changeDetector.detectChanges(); }, error: () => { this.error = 'No se pudo cargar el detalle de la reserva.'; this.changeDetector.detectChanges(); } }); }

  requestCancel(): void { this.showCancelDialog = true; this.error = ''; }
  closeCancelDialog(): void { if (!this.cancelling) this.showCancelDialog = false; }
  confirmCancel(): void { this.cancel(); }
  cancel(): void { if (!this.selected) return; this.cancelling = true; this.api.cancel(this.selected.id).subscribe({ next: (reservation) => { this.selected = reservation; this.cancelling = false; this.showCancelDialog = false; this.load(); }, error: (response) => { this.error = response.error?.detail?.message || 'No se pudo cancelar la reserva.'; this.cancelling = false; this.changeDetector.detectChanges(); } }); }

  setFilter(filter: ReservationFilter): void { this.filter = filter; }
  filterCount(filter: ReservationFilter): number { return this.reservations.filter((reservation) => this.matchesFilter(reservation, filter)).length; }
  matchesFilter(reservation: Reservation, filter: ReservationFilter): boolean {
    if (filter === 'active') return this.isActiveStatus(reservation.status);
    if (filter === 'history') return reservation.status === 'ATTENDED' || reservation.status === 'EXPIRED';
    if (filter === 'cancelled') return reservation.status === 'CANCELLED';
    return true;
  }
  isActiveStatus(status: ReservationStatus): boolean { return status === 'PENDING' || status === 'PREPARING' || status === 'READY'; }
  isTerminalStatus(status: ReservationStatus): boolean { return status === 'CANCELLED' || status === 'EXPIRED'; }
  reservationCode(reservation: Reservation): string { return `FS-${String(reservation.id).padStart(6, '0')}`; }
  statusLabel(status: string): string { return ({ PENDING: 'Pendiente', PREPARING: 'En preparación', READY: 'Lista', ATTENDED: 'Atendida', CANCELLED: 'Cancelada', EXPIRED: 'Vencida' } as Record<string, string>)[status] || status; }
  branchLocation(reservation: Reservation): string { return [reservation.branch_address, reservation.branch_city_name].filter(Boolean).join(' · ') || 'Dirección no informada'; }
  coordinatesLabel(reservation: Reservation): string { return reservation.branch_latitude != null && reservation.branch_longitude != null ? `${reservation.branch_latitude}, ${reservation.branch_longitude}` : 'No informadas'; }
  terminalStatusMessage(status: ReservationStatus): string { return status === 'CANCELLED' ? 'Reserva cancelada. Las prendas fueron liberadas y el registro queda en tu historial.' : 'Reserva vencida. El tiempo de apartado terminó y las prendas volvieron a disponibilidad.'; }
  timelineSteps(status: ReservationStatus): { status: ReservationStatus; label: string; description: string; done: boolean; current: boolean }[] {
    const order: ReservationStatus[] = ['PENDING', 'PREPARING', 'READY', 'ATTENDED'];
    const currentIndex = order.indexOf(status);
    const descriptions: Record<string, string> = {
      PENDING: 'Recibimos tu solicitud y validamos disponibilidad.',
      PREPARING: 'La sucursal está preparando las prendas.',
      READY: 'Tu reserva está lista para la visita.',
      ATTENDED: 'La atención en sucursal fue registrada.',
    };
    return order.map((step, index) => ({ status: step, label: this.statusLabel(step), description: descriptions[step], done: currentIndex >= index, current: currentIndex === index }));
  }
  copyReservationCode(reservation: Reservation): void {
    const code = this.reservationCode(reservation);
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(code).then(() => { this.copyFeedback = 'Código copiado.'; this.changeDetector.detectChanges(); }).catch(() => { this.copyFeedback = 'No se pudo copiar automáticamente.'; this.changeDetector.detectChanges(); });
      return;
    }
    this.copyFeedback = code;
  }
}
