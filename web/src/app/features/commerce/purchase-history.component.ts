import { Component, inject, OnInit } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';

import { CommerceService } from '../../core/commerce/commerce.service';
import { Sale } from '../../core/models/admin.models';

@Component({
  standalone: true,
  imports: [CurrencyPipe, DatePipe],
  template: `
    <section class="operations-page">
      <div class="admin-heading pos-heading">
        <div><p class="eyebrow">Cliente · Ciclo 3</p><h2>Historial de compras</h2><p class="admin-subtitle">Consulta tus compras digitales y presenciales asociadas a tu cuenta.</p></div>
        <button class="button button-light" type="button" (click)="load()">Actualizar</button>
      </div>
      @if (message) { <p class="pos-feedback" [class.pos-feedback-error]="messageType === 'error'">{{ message }}</p> }
      <div class="pos-layout">
        <div class="operations-table-card"><div class="table-wrap"><table><thead><tr><th>Orden</th><th>Fecha</th><th>Canal</th><th>Estado</th><th>Total</th><th>Detalle</th></tr></thead><tbody>
          @for (sale of purchases; track sale.id) {
            <tr [class.selected-row]="selectedSale?.id === sale.id">
              <td><strong>{{ sale.order_number }}</strong><small>{{ sale.items.length }} item(s)</small></td>
              <td>{{ sale.created_at | date:'short' }}</td><td>{{ sale.channel }}</td><td>{{ sale.status }}</td><td>{{ sale.total | currency:'BOB':'symbol':'1.2-2' }}</td>
              <td><button class="small-button" type="button" (click)="selectSale(sale)">{{ selectedSale?.id === sale.id ? 'Actualizar' : 'Ver detalle' }}</button></td>
            </tr>
          }
          @empty { <tr><td colspan="6">Todavía no tenés compras registradas.</td></tr> }
        </tbody></table></div></div>
        <aside class="pos-summary">
          <span class="panel-index">Detalle</span>
          @if (detailLoading) { <p>Cargando detalle...</p> }
          @else if (selectedSale) {
            <h3>{{ selectedSale.order_number }}</h3>
            <div class="pos-summary-row"><span>Subtotal</span><strong>{{ selectedSale.subtotal | currency:'BOB':'symbol':'1.2-2' }}</strong></div>
            <div class="pos-summary-row"><span>Descuento</span><strong>{{ selectedSale.discount | currency:'BOB':'symbol':'1.2-2' }}</strong></div>
            <div class="pos-summary-row"><span>Total</span><strong>{{ selectedSale.total | currency:'BOB':'symbol':'1.2-2' }}</strong></div>
            <div class="pos-summary-row"><span>Pagos</span><strong>{{ selectedSale.payments.length || 0 }}</strong></div>
            <div class="pos-summary-row"><span>Entrega</span><strong>{{ fulfillmentLabel(selectedSale) }}</strong></div>
            @if (selectedSale.fulfillment_type === 'DELIVERY') {
              <div class="pos-summary-note"><span class="material-symbols-outlined">local_shipping</span><small>{{ shippingSummary(selectedSale) }}</small></div>
            } @else {
              <div class="pos-summary-note"><span class="material-symbols-outlined">storefront</span><small>Retiro en sucursal seleccionada.</small></div>
            }
            <div class="pos-summary-note"><span class="material-symbols-outlined">receipt_long</span><small>{{ detailItemsLabel }}</small></div>
          } @else {
            <h3>Seleccioná una compra</h3>
            <p>El detalle muestra líneas, descuentos y pagos de la orden elegida.</p>
          }
        </aside>
      </div>
      @if (selectedSale) {
        <section class="operations-table-card operations-history">
          <div class="reservation-queue-header"><div><p class="eyebrow">Detalle de compra</p><h3>Productos y pagos</h3></div></div>
          <div class="split-panels">
            <div class="table-wrap"><table><thead><tr><th>Producto</th><th>SKU</th><th>Cantidad</th><th>Descuento</th><th>Total</th></tr></thead><tbody>
              @for (item of selectedSale.items; track item.id) { <tr><td>{{ item.product_name }}</td><td>{{ item.sku }}</td><td>{{ item.quantity }}</td><td>{{ item.discount | currency:'BOB':'symbol':'1.2-2' }}</td><td>{{ item.line_total | currency:'BOB':'symbol':'1.2-2' }}</td></tr> }
              @empty { <tr><td colspan="5">Sin líneas registradas.</td></tr> }
            </tbody></table></div>
            <div class="table-wrap"><table><thead><tr><th>Método</th><th>Proveedor</th><th>Estado</th><th>Monto</th></tr></thead><tbody>
              @for (payment of selectedSale.payments; track payment.id) { <tr><td>{{ payment.method }}</td><td>{{ payment.provider || 'Interno' }}</td><td>{{ payment.status }}</td><td>{{ payment.amount | currency:'BOB':'symbol':'1.2-2' }}</td></tr> }
              @empty { <tr><td colspan="4">Sin pagos registrados.</td></tr> }
            </tbody></table></div>
          </div>
        </section>
      }
    </section>
  `,
})
export class PurchaseHistoryComponent implements OnInit {
  private readonly commerce = inject(CommerceService);
  purchases: Sale[] = [];
  selectedSale: Sale | null = null;
  detailLoading = false;
  message = '';
  messageType: 'success' | 'error' = 'success';

  ngOnInit(): void { this.load(); }

  get detailItemsLabel(): string { return this.selectedSale?.items.map((item) => `${item.quantity}× ${item.product_name}`).join(' · ') || 'Sin productos.'; }

  fulfillmentLabel(sale: Sale): string { return sale.fulfillment_type === 'DELIVERY' ? 'Delivery' : 'Retiro en tienda'; }

  shippingSummary(sale: Sale): string {
    const details = sale.shipping_details;
    if (!details) return 'Delivery solicitado sin dirección disponible.';
    return `${details.recipient_name} · ${details.street} ${details.house_number}, ${details.zone}, ${details.department_or_city}. Tel: ${details.recipient_phone}. Ref: ${details.reference}.`;
  }

  load(): void {
    this.commerce.purchaseHistory().subscribe({
      next: (page) => { this.purchases = page.items; this.message = page.total ? '' : 'Todavía no tenés compras registradas.'; if (this.selectedSale && !this.purchases.some((sale) => sale.id === this.selectedSale?.id)) this.selectedSale = null; },
      error: () => { this.message = 'No se pudo cargar el historial.'; this.messageType = 'error'; },
    });
  }

  selectSale(sale: Sale): void {
    this.detailLoading = true;
    this.message = '';
    this.commerce.purchaseDetail(sale.id).subscribe({
      next: (detail) => { this.selectedSale = detail; this.detailLoading = false; },
      error: () => { this.selectedSale = sale; this.detailLoading = false; this.message = 'No se pudo cargar el detalle actualizado; se muestra el resumen.'; this.messageType = 'error'; },
    });
  }
}
