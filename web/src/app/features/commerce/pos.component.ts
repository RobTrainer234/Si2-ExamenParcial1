import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { CommerceService } from '../../core/commerce/commerce.service';

@Component({
  standalone: true,
  imports: [FormsModule],
  template: `
    <section class="operations-page"><div class="admin-heading"><div><p class="eyebrow">Caja</p><h2>Punto de venta</h2><p class="admin-subtitle">Registra una venta presencial y confirma el pago en la sucursal.</p></div></div>
    @if (message) { <p class="admin-alert">{{ message }}</p> }
    <div class="admin-panel"><label>ID de sucursal<input type="number" min="1" [(ngModel)]="branchId"></label><label>ID de variante<input type="number" min="1" [(ngModel)]="variantId"></label><label>Cantidad<input type="number" min="1" [(ngModel)]="quantity"></label><label>Total recibido<input type="number" min="0.01" step="0.01" [(ngModel)]="amount"></label><button class="button button-dark" type="button" [disabled]="busy || !valid" (click)="create()">{{ busy ? 'Procesando...' : 'Cobrar venta' }}</button></div>
  </section>
  `,
})
export class PosComponent {
  private readonly commerce = inject(CommerceService);
  branchId = 0;
  variantId = 0;
  quantity = 1;
  amount = 0;
  busy = false;
  message = '';
  get valid(): boolean { return this.branchId > 0 && this.variantId > 0 && this.quantity > 0 && this.amount > 0; }
  create(): void {
    if (!this.valid) return;
    this.busy = true;
    this.commerce.physicalSale({ branch_id: this.branchId, items: [{ product_variant_id: this.variantId, quantity: this.quantity }] }).subscribe({
      next: (sale) => this.commerce.cashPayment(sale.id, this.amount).subscribe({ next: (paid) => { this.message = `Venta ${paid.order_number} confirmada.`; this.busy = false; }, error: () => this.fail() }),
      error: (error) => { this.message = error.error?.detail?.message || 'No se pudo crear la venta.'; this.busy = false; },
    });
  }
  private fail(): void { this.message = 'No se pudo confirmar el pago.'; this.busy = false; }
}
