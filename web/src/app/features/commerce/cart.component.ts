import { CurrencyPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { CommerceService } from '../../core/commerce/commerce.service';
import { AdminService } from '../../core/admin/admin.service';
import { Branch, Cart } from '../../core/models/admin.models';

@Component({
  standalone: true,
  imports: [CurrencyPipe, FormsModule],
  template: `
    <section class="operations-page commerce-page"><div class="admin-heading"><div><p class="eyebrow">Tu selección</p><h2>Carrito de compras</h2><p class="admin-subtitle">Revisa tus prendas y elige la sucursal para iniciar el pago.</p></div></div>
    @if (message) { <p class="admin-alert">{{ message }}</p> } @if (loading) { <p class="loading page-message">Cargando carrito...</p> } @if (!loading && cart && !cart.items.length) { <p class="empty page-message">Tu carrito está vacío.</p> }
    @if (!loading && cart?.items?.length) { <div class="operations-table-card"><div class="table-wrap"><table><thead><tr><th>Producto</th><th>Precio</th><th>Cantidad</th><th>Total</th><th></th></tr></thead><tbody>@for (item of cart!.items; track item.id) { <tr><td><strong>{{ item.product_name }}</strong><small>{{ item.size_name }} · {{ item.color_name }} · {{ item.sku }}</small></td><td>{{ item.unit_price | currency:'BOB':'symbol':'1.2-2' }}</td><td><input class="stock-input" type="number" min="1" [value]="item.quantity" (change)="update(item.id, $any($event.target).value)"></td><td>{{ item.line_total | currency:'BOB':'symbol':'1.2-2' }}</td><td><button class="small-button" type="button" (click)="remove(item.id)">Eliminar</button></td></tr> }</tbody></table></div><div class="commerce-checkout"><strong>Total: {{ cart!.total | currency:'BOB':'symbol':'1.2-2' }}</strong><label>Sucursal de retiro<select [(ngModel)]="branchId"><option [ngValue]="null">Selecciona una sucursal</option>@for (branch of branches; track branch.id) { <option [ngValue]="branch.id">{{ branch.name }} · {{ branch.city_name }}</option> }</select></label><button class="button button-dark" type="button" [disabled]="!branchId || paying" (click)="checkout()">{{ paying ? 'Procesando...' : 'Pagar en sandbox' }}</button></div></div> }
    </section>
  `,
})
export class CartComponent {
  private readonly commerce = inject(CommerceService);
  private readonly admin = inject(AdminService);
  cart: Cart | null = null;
  branches: Branch[] = [];
  branchId: number | null = null;
  loading = true;
  paying = false;
  message = '';

  constructor() { this.load(); this.admin.branches().subscribe({ next: (page) => this.branches = page.items }); }
  load(): void { this.commerce.cart().subscribe({ next: (cart) => { this.cart = cart; this.loading = false; }, error: () => { this.message = 'Debes iniciar sesión para consultar tu carrito.'; this.loading = false; } }); }
  update(id: number, quantity: string): void { this.commerce.updateCartItem(id, Math.max(1, Number(quantity) || 1)).subscribe({ next: (cart) => this.cart = cart, error: () => this.message = 'No se pudo actualizar la cantidad.' }); }
  remove(id: number): void { this.commerce.removeCartItem(id).subscribe({ next: (cart) => this.cart = cart, error: () => this.message = 'No se pudo eliminar el artículo.' }); }
  checkout(): void { if (!this.branchId || !this.cart) return; this.paying = true; this.commerce.digitalPurchase(this.branchId).subscribe({ next: (sale) => this.commerce.electronicPayment(sale.id, `web-${sale.id}-${Date.now()}`).subscribe({ next: (payment) => this.commerce.approveSandbox(payment.transaction_reference!, Number(sale.total)).subscribe({ next: () => { this.message = `Compra ${sale.order_number} confirmada.`; this.paying = false; this.load(); }, error: () => this.fail() }), error: () => this.fail() }), error: (error) => { this.message = error.error?.detail?.message || 'No se pudo iniciar la compra.'; this.paying = false; } }); }
  private fail(): void { this.message = 'El pago no pudo completarse.'; this.paying = false; }
}
