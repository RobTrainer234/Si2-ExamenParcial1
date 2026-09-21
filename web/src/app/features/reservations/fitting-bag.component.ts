import { CurrencyPipe } from '@angular/common';
import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';

import { FittingBagItem, FittingBagService } from '../../core/reservations/fitting-bag.service';
import { ReservationService } from '../../core/reservations/reservation.service';

@Component({
  standalone: true,
  imports: [CurrencyPipe, FormsModule, RouterLink],
  template: `
    <section class="fitting-bag-page" aria-labelledby="fitting-bag-title">
      <a class="back-link" routerLink="/catalog"><span class="material-symbols-outlined" aria-hidden="true">arrow_back</span> Seguir explorando</a>
      <header class="fitting-bag-hero">
        <div>
          <p class="eyebrow">Reserva en tienda</p>
          <h1 id="fitting-bag-title">Bolsa de probador</h1>
          <p>Armá una sola visita con todas las prendas que querés probar. Elegimos una sucursal disponible para toda la bolsa y enviamos una única reserva.</p>
        </div>
        <div class="fitting-bag-counter" aria-live="polite"><strong>{{ bag.count() }}</strong><span>{{ bag.count() === 1 ? 'prenda' : 'prendas' }}</span></div>
      </header>

      @if (message) { <p class="admin-alert" [class.error]="messageError" role="status">{{ message }}</p> }

      @if (!bag.items().length) {
        <section class="fitting-bag-empty">
          <span class="material-symbols-outlined" aria-hidden="true">shopping_bag</span>
          <h2>Tu bolsa está vacía</h2>
          <p>Desde el detalle de una prenda consultá disponibilidad y agregala a esta bolsa antes de reservar.</p>
          <a class="button button-dark" routerLink="/catalog">Ver catálogo</a>
        </section>
      } @else {
        <div class="fitting-bag-layout">
          <section class="fitting-bag-items" aria-labelledby="bag-items-title">
            <div class="section-heading-row"><div><p class="eyebrow">Paso 1</p><h2 id="bag-items-title">Revisá las prendas</h2></div><button class="small-button" type="button" (click)="clear()">Vaciar bolsa</button></div>
            @for (item of bag.items(); track item.product_variant_id) {
              <article class="fitting-bag-item">
                <img [src]="item.image_url || placeholder" [alt]="item.product_name">
                <div class="fitting-bag-item-copy">
                  <span class="category-label">{{ item.product_code }}</span>
                  <h3>{{ item.product_name }}</h3>
                  <p>{{ item.size_name }} · {{ item.color_name }} · SKU {{ item.sku }}</p>
                  <strong>{{ item.unit_price | currency:'BOB':'symbol':'1.2-2' }}</strong>
                </div>
                <label>Cantidad
                  <input type="number" min="1" [max]="maxQuantity(item)" [ngModel]="item.quantity" (ngModelChange)="setQuantity(item, $event)" [attr.aria-label]="'Cantidad para ' + item.product_name">
                </label>
                <button class="small-button remove-button" type="button" (click)="remove(item.product_variant_id)" [attr.aria-label]="'Quitar ' + item.product_name">Quitar</button>
              </article>
            }
          </section>

          <aside class="fitting-bag-summary" aria-labelledby="bag-summary-title">
            <p class="eyebrow">Paso 2</p>
            <h2 id="bag-summary-title">Programá la visita</h2>
            <p class="muted">La reserva usa una sola sucursal y una sola fecha para toda la bolsa.</p>
            <label>Sucursal disponible
              <select [(ngModel)]="selectedBranchId">
                <option [ngValue]="null">Selecciona una sucursal</option>
                @for (branch of bag.sharedBranches(); track branch.branch_id) {
                  <option [ngValue]="branch.branch_id">{{ branch.branch_name }} · {{ branch.city_name }}</option>
                }
              </select>
            </label>
            @if (!bag.sharedBranches().length) { <p class="error">No hay una sucursal común con stock para todas las cantidades. Ajustá la bolsa o quitá una prenda.</p> }
            @if (selectedBranch) { <p class="branch-note"><strong>{{ selectedBranch.address }}</strong><span>{{ selectedBranch.stock }} unidades disponibles en la combinación más limitada.</span></p> }
            <label>Fecha de visita
              <input type="date" [(ngModel)]="visitDate" [min]="minimumReservationDate">
            </label>
            <section class="fitting-bag-review" aria-labelledby="bag-review-title">
              <h3 id="bag-review-title">Resumen</h3>
              @for (item of bag.items(); track item.product_variant_id) { <span>{{ item.quantity }}× {{ item.product_name }} <small>{{ item.size_name }} · {{ item.color_name }}</small></span> }
            </section>
            <button class="button button-dark" type="button" [disabled]="!canSubmit" (click)="submit()">{{ submitting ? 'Reservando...' : 'Confirmar reserva de probador' }}</button>
            <p class="summary-footnote">Al confirmar se crea una única reserva con {{ bag.itemCount() }} {{ bag.itemCount() === 1 ? 'variante' : 'variantes' }}.</p>
          </aside>
        </div>
      }
    </section>
  `,
})
export class FittingBagComponent {
  readonly bag = inject(FittingBagService);
  private readonly reservations = inject(ReservationService);
  private readonly router = inject(Router);
  private readonly changeDetector = inject(ChangeDetectorRef);
  selectedBranchId: number | null = null;
  visitDate = this.minimumReservationDate;
  submitting = false;
  message = '';
  messageError = false;
  readonly placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160"%3E%3Crect width="120" height="160" fill="%23eee9e1"/%3E%3Ctext x="60" y="84" text-anchor="middle" fill="%2390887e" font-size="12"%3EFashionStore%3C/text%3E%3C/svg%3E';

  get minimumReservationDate(): string { const date = new Date(); date.setDate(date.getDate() + 1); return date.toISOString().slice(0, 10); }
  get selectedBranch() { return this.bag.sharedBranches().find((branch) => branch.branch_id === this.selectedBranchId) || null; }
  get canSubmit(): boolean { return !!this.bag.items().length && !!this.selectedBranch && !!this.visitDate && this.visitDate >= this.minimumReservationDate && !this.submitting; }

  maxQuantity(item: FittingBagItem): number { return Math.max(...item.available_branches.map((branch) => branch.stock)); }
  setQuantity(item: FittingBagItem, value: string | number): void { const quantity = Number(value) || 1; this.bag.setQuantity(item.product_variant_id, quantity); this.ensureSelectedBranchAvailable(); }
  remove(productVariantId: number): void { this.bag.remove(productVariantId); this.ensureSelectedBranchAvailable(); }
  clear(): void { this.bag.clear(); this.selectedBranchId = null; }

  submit(): void {
    if (!this.canSubmit || !this.selectedBranchId) return;
    this.submitting = true;
    this.message = '';
    this.messageError = false;
    this.reservations.create({
      branch_id: this.selectedBranchId,
      scheduled_for: `${this.visitDate}T10:00:00`,
      items: this.bag.items().map((item) => ({ product_variant_id: item.product_variant_id, quantity: item.quantity })),
    }).pipe(
      timeout({ each: 10000 }),
      finalize(() => { this.submitting = false; this.changeDetector.detectChanges(); }),
    ).subscribe({
      next: (reservation) => { this.bag.clear(); this.message = 'Reserva creada. Te llevamos al detalle para seguir el estado.'; void this.router.navigate(['/my-reservations', reservation.id]); },
      error: () => { this.messageError = true; this.message = 'No se pudo crear la reserva. Revisá la disponibilidad o intentá nuevamente.'; },
    });
  }

  private ensureSelectedBranchAvailable(): void {
    if (this.selectedBranchId && !this.selectedBranch) this.selectedBranchId = null;
  }
}
