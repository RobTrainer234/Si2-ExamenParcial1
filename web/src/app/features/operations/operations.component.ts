import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, timeout } from 'rxjs';

import { AdminService } from '../../core/admin/admin.service';
import { AuthService } from '../../core/auth/auth.service';
import { InventoryMovement, InventoryMovementType, InventoryRow, QuarantineDecision, QuarantineItem, QuarantineStatus } from '../../core/models/admin.models';

@Component({
  standalone: true,
  imports: [DatePipe, FormsModule],
  template: `
    <section class="operations-page">
      <div class="admin-heading"><div><p class="eyebrow">Operación</p><h2>Inventario asignado</h2><p class="admin-subtitle">Consulta existencias, inspecciona prendas en cuarentena por cambio, registra movimientos y conserva el historial de tus sucursales.</p></div><span class="status-pill active">{{ canAdjust ? 'Edición habilitada' : 'Solo lectura' }}</span></div>
      @if (error) { <p class="error admin-alert">{{ error }}</p> }
      @if (quarantineMessage) { <p class="admin-alert" role="status" [style.background]="quarantineMessageError ? '#fef2f2' : '#ecfdf5'" [style.color]="quarantineMessageError ? '#991b1b' : '#065f46'" style="border: 1px solid currentColor; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;">{{ quarantineMessage }}</p> }
      @if (loading) { <p class="loading page-message">Cargando inventario...</p> }
      @if (!loading && !error && !items.length) { <p class="empty page-message">No hay existencias registradas en tus sucursales.</p> }
      @if (!loading && items.length) { <div class="operations-table-card"><div class="table-wrap"><table><thead><tr><th>Producto</th><th>Variante</th><th>Sucursal</th><th>Stock físico</th><th>Reservado</th><th>Disponible</th><th>Estado</th><th></th></tr></thead><tbody>@for (item of items; track item.id) { <tr><td><strong>{{ item.product_name }}</strong><small>{{ item.sku }}</small></td><td>{{ item.size_name }} · {{ item.color_name }}</td><td>{{ item.branch_name }}</td><td>@if (canAdjust) { <input class="stock-input" type="number" min="0" [value]="draftValue(item)" (input)="setDraft(item.id, $any($event.target).value)"> } @else { <strong>{{ item.stock_quantity }}</strong> }</td><td>{{ item.reserved_quantity }}</td><td><strong>{{ item.available_quantity }}</strong></td><td><span class="status-pill" [class.active]="item.available_quantity > 0">{{ item.available_quantity > 0 ? 'Disponible' : 'Agotado' }}</span></td><td>@if (canAdjust) { <button class="small-button" type="button" (click)="save(item)">Guardar</button> }</td></tr> }</tbody></table></div></div> }

      @if (!loading) {
        <div class="operations-history" style="margin-top: 1.5rem;">
          <div class="admin-heading">
            <div>
              <p class="eyebrow">Control de Calidad</p>
              <h3>Bandeja de Cuarentena por Cambio de Prenda</h3>
              <p class="admin-subtitle">Las prendas devueltas en un cambio permanecen fuera del stock vendible hasta que un Encargado o Administrador las inspeccione.</p>
            </div>
            <div class="movement-filters">
              <label style="display: flex; align-items: center; gap: 6px; font-size: 0.85rem;">
                <span>Estado cuarentena</span>
                <select [(ngModel)]="quarantineStatusFilter" (change)="quarantinePage = 1; loadQuarantine()" aria-label="Filtrar estado de cuarentena">
                  <option value="PENDING">Pendientes de inspección</option>
                  <option value="RELEASED">Liberadas a stock</option>
                  <option value="REJECTED">Rechazadas (no vendibles)</option>
                  <option value="">Todas</option>
                </select>
              </label>
            </div>
          </div>

          @if (!canInspectQuarantine) {
            <p class="page-message" style="margin-bottom: 10px; font-size: 0.85rem;">Vista de solo lectura: únicamente Encargados de Sucursal o Administradores pueden liberar o rechazar prendas en cuarentena.</p>
          }

          @if (!quarantineItems.length) {
            <p class="empty page-message">No hay prendas en cuarentena para el filtro seleccionado.</p>
          } @else {
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Prenda / Variante</th>
                    <th>Sucursal</th>
                    <th>Cantidad</th>
                    <th>Estado</th>
                    <th>Ingreso</th>
                    <th>Inspección / Acción</th>
                  </tr>
                </thead>
                <tbody>
                  @for (q of quarantineItems; track q.id) {
                    <tr>
                      <td><strong>#{{ q.id }}</strong></td>
                      <td>
                        <strong>{{ quarantineProductLabel(q) }}</strong>
                        <small style="display: block;">{{ quarantineVariantLabel(q) }}</small>
                      </td>
                      <td>{{ quarantineBranchLabel(q) }}</td>
                      <td><strong>{{ q.quantity }}</strong></td>
                      <td>
                        <span class="status-pill" [class.active]="q.status === 'RELEASED'">{{ quarantineStatusLabel(q.status) }}</span>
                      </td>
                      <td>{{ q.created_at | date:'short' }}</td>
                      <td>
                        @if (q.status === 'PENDING' && canInspectQuarantine) {
                          <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
                            <input
                              [(ngModel)]="quarantineReasons[q.id]"
                              maxlength="255"
                              placeholder="Motivo de inspección (mín. 2 caracteres)"
                              [attr.aria-label]="'Motivo de inspección cuarentena #' + q.id"
                              style="min-width: 210px; padding: 5px 8px; font-size: 0.82rem;"
                              [disabled]="inspectingQuarantineId === q.id"
                            >
                            <button
                              type="button"
                              class="small-button"
                              style="background: #065f46; color: #fff;"
                              [disabled]="inspectingQuarantineId === q.id"
                              (click)="submitQuarantineDecision(q, 'RELEASE')"
                            >
                              {{ inspectingQuarantineId === q.id ? 'Procesando...' : 'Liberar a stock' }}
                            </button>
                            <button
                              type="button"
                              class="small-button"
                              style="color: #991b1b;"
                              [disabled]="inspectingQuarantineId === q.id"
                              (click)="submitQuarantineDecision(q, 'REJECT')"
                            >
                              Rechazar
                            </button>
                          </div>
                        } @else if (q.status !== 'PENDING') {
                          <small>{{ q.inspection_reason || 'Inspeccionada' }} @if (q.inspected_at) { ({{ q.inspected_at | date:'short' }}) }</small>
                        } @else {
                          <small>Pendiente de encargado</small>
                        }
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }
          <div class="inventory-pagination">
            @if (quarantinePages > 1) {
              <button class="small-button" type="button" [disabled]="quarantinePage === 1" (click)="quarantinePage = quarantinePage - 1; loadQuarantine()">Anterior</button>
              <span>Página {{ quarantinePage }} de {{ quarantinePages }}</span>
              <button class="small-button" type="button" [disabled]="quarantinePage === quarantinePages" (click)="quarantinePage = quarantinePage + 1; loadQuarantine()">Siguiente</button>
            }
          </div>
        </div>
      }

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

  quarantineItems: QuarantineItem[] = [];
  quarantineStatusFilter: QuarantineStatus | '' = 'PENDING';
  quarantinePage = 1;
  quarantinePages = 1;
  quarantineReasons: Record<number, string> = {};
  inspectingQuarantineId: number | null = null;
  quarantineMessage = '';
  quarantineMessageError = false;

  readonly canAdjust = this.auth.hasPermission('inventory.adjust');

  get canInspectQuarantine(): boolean {
    const role = this.auth.currentUser?.()?.role ?? '';
    return this.canAdjust && (role === 'ADMIN' || role === 'BRANCH_MANAGER');
  }

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
    this.api.inventoryAll(undefined, this.inventoryPage, 25).pipe(timeout({ each: 10000 }), finalize(() => { this.loading = false; this.cdr.markForCheck(); })).subscribe({
      next: (page) => {
        this.items = page.items;
        this.inventoryPages = page.total_pages;
        this.loadMovements();
        this.loadQuarantine();
        this.cdr.markForCheck();
      },
      error: (response) => {
        this.showError(response);
        this.cdr.markForCheck();
      },
    });
  }

  loadMovements(): void {
    this.api.inventoryMovements(this.historyInventoryId ?? undefined, this.historyType || undefined, this.historyPage, 25).pipe(timeout({ each: 10000 })).subscribe({
      next: (page) => { this.movements = page.items; this.historyPages = page.total_pages; this.cdr.markForCheck(); },
      error: (response) => { this.showError(response); this.cdr.markForCheck(); },
    });
  }

  loadQuarantine(): void {
    if (!this.api.quarantineList) return;
    this.api.quarantineList(this.quarantineStatusFilter, this.quarantinePage, 25).pipe(timeout({ each: 10000 })).subscribe({
      next: (page) => {
        this.quarantineItems = page.items || [];
        this.quarantinePages = page.total_pages || 1;
        this.cdr.markForCheck();
      },
      error: (response) => {
        this.showError(response);
        this.cdr.markForCheck();
      },
    });
  }

  submitQuarantineDecision(item: QuarantineItem, decision: QuarantineDecision): void {
    this.error = '';
    this.quarantineMessage = '';
    this.quarantineMessageError = false;
    if (!this.canInspectQuarantine) {
      this.quarantineMessageError = true;
      this.quarantineMessage = 'Solo Encargado de Sucursal o Administrador pueden inspeccionar cuarentena.';
      return;
    }
    const reason = (this.quarantineReasons[item.id] || '').trim();
    if (reason.length < 2) {
      this.quarantineMessageError = true;
      this.quarantineMessage = 'Ingresá un motivo válido (mínimo 2 caracteres) antes de confirmar la inspección.';
      this.cdr.markForCheck();
      return;
    }
    this.inspectingQuarantineId = item.id;
    this.api.inspectQuarantine(item.id, { decision, reason }).pipe(
      timeout({ each: 10000 }),
      finalize(() => {
        this.inspectingQuarantineId = null;
        this.cdr.markForCheck();
      }),
    ).subscribe({
      next: (updated) => {
        delete this.quarantineReasons[item.id];
        this.quarantineMessageError = false;
        this.quarantineMessage = updated.status === 'RELEASED'
          ? `Cuarentena #${updated.id} liberada: las unidades se reincorporaron al stock vendible.`
          : `Cuarentena #${updated.id} rechazada: la prenda permanece fuera del stock vendible.`;
        this.load();
      },
      error: (response) => {
        this.showError(response);
        this.cdr.markForCheck();
      },
    });
  }

  quarantineProductLabel(q: QuarantineItem): string {
    const match = this.items.find((i) => i.id === q.inventory_id || (i.branch_id === q.branch_id && i.product_variant_id === q.product_variant_id));
    return match ? match.product_name : `Inventario #${q.inventory_id}`;
  }

  quarantineVariantLabel(q: QuarantineItem): string {
    const match = this.items.find((i) => i.id === q.inventory_id || (i.branch_id === q.branch_id && i.product_variant_id === q.product_variant_id));
    return match ? `${match.sku} · ${match.size_name} / ${match.color_name}` : `Variante #${q.product_variant_id}`;
  }

  quarantineBranchLabel(q: QuarantineItem): string {
    const match = this.items.find((i) => i.branch_id === q.branch_id);
    return match ? match.branch_name : `Sucursal #${q.branch_id}`;
  }

  quarantineStatusLabel(status: QuarantineStatus): string {
    return ({ PENDING: 'Pendiente', RELEASED: 'Liberada a stock', REJECTED: 'Rechazada' } as Record<QuarantineStatus, string>)[status] || status;
  }

  createMovement(): void { if (!this.movementInventoryId || this.movementQuantity < 1 || this.movementReason.trim().length < 2) { this.error = 'Selecciona inventario y completa una cantidad y motivo válidos.'; return; } this.savingMovement = true; this.api.createInventoryMovement({ inventory_id: this.movementInventoryId, movement_type: this.movementType, quantity: this.movementQuantity, reason: this.movementReason.trim() }).subscribe({ next: () => { this.savingMovement = false; this.movementQuantity = 1; this.movementReason = ''; this.load(); }, error: (response) => { this.savingMovement = false; this.showError(response); } }); }
  movementLabel(type: InventoryMovementType): string { return ({ IN: 'Entrada', OUT: 'Salida', RETURN: 'Devolución', RESERVE: 'Reserva', RELEASE: 'Liberación', SALE: 'Venta' } as Record<InventoryMovementType, string>)[type]; }
  private showError(response: { error?: { detail?: { message?: string } } }): void { this.error = response.error?.detail?.message || 'No se pudo completar la operación de inventario.'; }
}
