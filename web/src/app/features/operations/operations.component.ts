import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, timeout } from 'rxjs';

import { AdminService } from '../../core/admin/admin.service';
import { AuthService } from '../../core/auth/auth.service';
import { InventoryMovement, InventoryMovementType, InventoryRow } from '../../core/models/admin.models';

@Component({
  standalone: true,
  imports: [DatePipe, FormsModule],
  template: `
    <section class="operations-page">
      <div class="admin-heading"><div><p class="eyebrow">Operación</p><h2>Inventario asignado</h2><p class="admin-subtitle">Consulta existencias, registra movimientos y conserva el historial de tus sucursales.</p></div><span class="status-pill active">{{ canAdjust ? 'Edición habilitada' : 'Solo lectura' }}</span></div>
      @if (error) { <p class="error admin-alert">{{ error }}</p> }
      @if (loading) { <p class="loading page-message">Cargando inventario...</p> }
      @if (!loading && !error && !items.length) { <p class="empty page-message">No hay existencias registradas en tus sucursales.</p> }
       @if (!loading && items.length) { <div class="operations-table-card"><div class="table-wrap"><table><thead><tr><th>Producto</th><th>Variante</th><th>Sucursal</th><th>Stock físico</th><th>Reservado</th><th>Disponible</th><th>Estado</th><th></th></tr></thead><tbody>@for (item of items; track item.id) { <tr><td><strong>{{ item.product_name }}</strong><small>{{ item.sku }}</small></td><td>{{ item.size_name }} · {{ item.color_name }}</td><td>{{ item.branch_name }}</td><td>@if (canAdjust) { <input class="stock-input" type="number" min="0" [value]="draftValue(item)" (input)="setDraft(item.id, $any($event.target).value)"> } @else { <strong>{{ item.stock_quantity }}</strong> }</td><td>{{ item.reserved_quantity }}</td><td><strong>{{ item.available_quantity }}</strong></td><td><span class="status-pill" [class.active]="item.available_quantity > 0">{{ item.available_quantity > 0 ? 'Disponible' : 'Agotado' }}</span></td><td>@if (canAdjust) { <button class="small-button" type="button" (click)="save(item)">Guardar</button> }</td></tr> }</tbody></table></div></div> }
      @if (!loading && canAdjust) { <div class="operations-forms"><form class="admin-panel movement-form" (ngSubmit)="createMovement()"><div class="form-step"><span>01</span><div><strong>Registrar movimiento</strong><small>Entrada, salida o devolución de una variante.</small></div></div><label>Inventario<select [(ngModel)]="movementInventoryId" name="inventory"><option [ngValue]="null">Selecciona un inventario</option>@for (item of items; track item.id) { <option [ngValue]="item.id">{{ item.product_name }} · {{ item.branch_name }} · {{ item.sku }}</option> }</select></label><div class="location-form-grid"><label>Tipo<select [(ngModel)]="movementType" name="type"><option value="IN">Entrada</option><option value="OUT">Salida</option><option value="RETURN">Devolución</option></select></label><label>Cantidad<input [(ngModel)]="movementQuantity" name="quantity" type="number" min="1"></label></div><label>Motivo<input [(ngModel)]="movementReason" name="reason" maxlength="255" placeholder="Ej. Recepción de proveedor"></label><button class="button button-dark" type="submit" [disabled]="savingMovement">{{ savingMovement ? 'Guardando...' : 'Registrar movimiento' }}</button></form></div> }
       @if (!loading) { <div class="operations-history"><div class="admin-heading"><div><p class="eyebrow">Trazabilidad</p><h3>Historial de movimientos</h3></div><div class="movement-filters"><select [(ngModel)]="historyInventoryId" (change)="historyPage = 1; loadMovements()"><option [ngValue]="null">Todos los inventarios</option>@for (item of items; track item.id) { <option [ngValue]="item.id">{{ item.product_name }} · {{ item.branch_name }}</option> }</select><select [(ngModel)]="historyType" (change)="historyPage = 1; loadMovements()"><option value="">Todos los tipos</option><option value="IN">Entradas</option><option value="OUT">Salidas</option><option value="RETURN">Devoluciones</option><option value="RESERVE">Reservas</option><option value="RELEASE">Liberaciones</option><option value="SALE">Ventas</option></select></div></div>@if (!movements.length) { <p class="empty page-message">No hay movimientos para los filtros seleccionados.</p> } @if (movements.length) { <div class="table-wrap"><table><thead><tr><th>Fecha</th><th>Producto</th><th>Sucursal</th><th>Tipo</th><th>Cantidad</th><th>Stock</th><th>Referencia</th><th>Motivo</th></tr></thead><tbody>@for (movement of movements; track movement.id) { <tr><td>{{ movement.created_at | date:'short' }}</td><td>#{{ movement.inventory_id }}</td><td>{{ movement.branch_name }}</td><td><span class="status-pill" [class.active]="movement.movement_type === 'IN' || movement.movement_type === 'RETURN'">{{ movementLabel(movement.movement_type) }}</span></td><td>{{ movement.quantity }}</td><td>{{ movement.stock_before }} → {{ movement.stock_after }}</td><td>{{ movement.reference_type ? movement.reference_type + ' #' + movement.reference_id : 'Manual' }}</td><td>{{ movement.reason || 'Sin motivo' }}</td></tr> }</tbody></table></div> }<div class="inventory-pagination">@if (historyPages > 1) { <button class="small-button" type="button" [disabled]="historyPage === 1" (click)="historyPage = historyPage - 1; loadMovements()">Anterior</button><span>Página {{ historyPage }} de {{ historyPages }}</span><button class="small-button" type="button" [disabled]="historyPage === historyPages" (click)="historyPage = historyPage + 1; loadMovements()">Siguiente</button> }</div></div> }
       @if (!loading && inventoryPages > 1) { <div class="inventory-pagination"><button class="small-button" type="button" [disabled]="inventoryPage === 1" (click)="inventoryPage = inventoryPage - 1; load()">Anterior</button><span>Página {{ inventoryPage }} de {{ inventoryPages }}</span><button class="small-button" type="button" [disabled]="inventoryPage === inventoryPages" (click)="inventoryPage = inventoryPage + 1; load()">Siguiente</button></div> }
    </section>
  `,
})
export class OperationsComponent {
  private readonly api = inject(AdminService);
  private readonly auth = inject(AuthService);
  private readonly cdr = inject(ChangeDetectorRef);
  items: InventoryRow[] = [];
  drafts: Record<number, number> = {};
  loading = true;
  inventoryPage = 1;
  inventoryPages = 1;
  error = '';
  movements: InventoryMovement[] = [];
  movementInventoryId: number | null = null;
  movementType: InventoryMovementType = 'IN';
  movementQuantity = 1;
  movementReason = '';
  savingMovement = false;
  historyInventoryId: number | null = null;
  historyType = '';
  historyPage = 1;
  historyPages = 1;
  readonly canAdjust = this.auth.hasPermission('inventory.adjust');

  constructor() { this.load(); }

  setDraft(id: number, value: string): void { this.drafts[id] = Math.max(0, Number(value) || 0); }
  draftValue(item: InventoryRow): number { return this.drafts[item.id] ?? item.stock_quantity; }

   save(item: InventoryRow): void {
   const value = this.drafts[item.id] ?? item.stock_quantity;
      this.api.updateInventory(item.id, value).subscribe({ next: (updated) => { Object.assign(item, updated); delete this.drafts[item.id]; this.loadMovements(); }, error: (response) => this.showError(response) });
   }

    load(): void {
      this.loading = true;
      this.cdr.markForCheck();
      this.api.inventoryAll(undefined, this.inventoryPage, 25).pipe(timeout({ each: 10000 }), finalize(() => { this.loading = false; this.cdr.markForCheck(); })).subscribe({ next: (page) => { this.items = page.items; this.inventoryPages = page.total_pages; this.loadMovements(); this.cdr.markForCheck(); }, error: (response) => { this.showError(response); this.cdr.markForCheck(); } });
   }

   loadMovements(): void { this.api.inventoryMovements(this.historyInventoryId ?? undefined, this.historyType || undefined, this.historyPage, 25).pipe(timeout({ each: 10000 })).subscribe({ next: (page) => { this.movements = page.items; this.historyPages = page.total_pages; this.cdr.markForCheck(); }, error: (response) => { this.showError(response); this.cdr.markForCheck(); } }); }
  createMovement(): void { if (!this.movementInventoryId || this.movementQuantity < 1 || this.movementReason.trim().length < 2) { this.error = 'Selecciona inventario y completa una cantidad y motivo válidos.'; return; } this.savingMovement = true; this.api.createInventoryMovement({ inventory_id: this.movementInventoryId, movement_type: this.movementType, quantity: this.movementQuantity, reason: this.movementReason.trim() }).subscribe({ next: () => { this.savingMovement = false; this.movementQuantity = 1; this.movementReason = ''; this.load(); }, error: (response) => { this.savingMovement = false; this.showError(response); } }); }
  movementLabel(type: InventoryMovementType): string { return ({ IN: 'Entrada', OUT: 'Salida', RETURN: 'Devolución', RESERVE: 'Reserva', RELEASE: 'Liberación', SALE: 'Venta' } as Record<InventoryMovementType, string>)[type]; }
  private showError(response: { error?: { detail?: { message?: string } } }): void { this.error = response.error?.detail?.message || 'No se pudo completar la operación de inventario.'; }
}
