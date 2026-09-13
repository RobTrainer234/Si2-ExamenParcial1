import { Component, inject } from '@angular/core';

import { AdminService } from '../../core/admin/admin.service';
import { AuthService } from '../../core/auth/auth.service';
import { InventoryRow } from '../../core/models/admin.models';

@Component({
  standalone: true,
  template: `
    <section class="operations-page">
      <div class="admin-heading"><div><p class="eyebrow">Operación</p><h2>Inventario asignado</h2><p class="admin-subtitle">Consulta las existencias de tus sucursales y ajusta cantidades cuando tengas autorización.</p></div><span class="status-pill active">{{ canAdjust ? 'Edición habilitada' : 'Solo lectura' }}</span></div>
      @if (error) { <p class="error admin-alert">No se pudo cargar el inventario.</p> }
      @if (loading) { <p class="loading page-message">Cargando inventario...</p> }
      @if (!loading && !error && !items.length) { <p class="empty page-message">No hay existencias registradas en tus sucursales.</p> }
       @if (!loading && items.length) { <div class="operations-table-card"><div class="table-wrap"><table><thead><tr><th>Producto</th><th>Variante</th><th>Sucursal</th><th>Stock físico</th><th>Reservado</th><th>Disponible</th><th>Estado</th><th></th></tr></thead><tbody>@for (item of items; track item.id) { <tr><td><strong>{{ item.product_name }}</strong><small>{{ item.sku }}</small></td><td>{{ item.size_name }} · {{ item.color_name }}</td><td>{{ item.branch_name }}</td><td>@if (canAdjust) { <input class="stock-input" type="number" min="0" [value]="draftValue(item)" (input)="setDraft(item.id, $any($event.target).value)"> } @else { <strong>{{ item.stock_quantity }}</strong> }</td><td>{{ item.reserved_quantity }}</td><td><strong>{{ item.available_quantity }}</strong></td><td><span class="status-pill" [class.active]="item.available_quantity > 0">{{ item.available_quantity > 0 ? 'Disponible' : 'Agotado' }}</span></td><td>@if (canAdjust) { <button class="small-button" type="button" (click)="save(item)">Guardar</button> }</td></tr> }</tbody></table></div></div> }
    </section>
  `,
})
export class OperationsComponent {
  private readonly api = inject(AdminService);
  private readonly auth = inject(AuthService);
  items: InventoryRow[] = [];
  drafts: Record<number, number> = {};
  loading = true;
  error = false;
  readonly canAdjust = this.auth.hasPermission('inventory.adjust');

  constructor() { this.load(); }

  setDraft(id: number, value: string): void { this.drafts[id] = Math.max(0, Number(value) || 0); }
  draftValue(item: InventoryRow): number { return this.drafts[item.id] ?? item.stock_quantity; }

   save(item: InventoryRow): void {
   const value = this.drafts[item.id] ?? item.stock_quantity;
     this.api.updateInventory(item.id, value).subscribe({ next: (updated) => { Object.assign(item, updated); delete this.drafts[item.id]; }, error: () => this.error = true });
  }

  private load(): void {
    this.api.inventoryAll().subscribe({ next: (page) => { this.items = page.items; this.loading = false; }, error: () => { this.error = true; this.loading = false; } });
  }
}
