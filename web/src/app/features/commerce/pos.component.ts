import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, switchMap, timeout } from 'rxjs';

import { CommerceService } from '../../core/commerce/commerce.service';
import { AuthService } from '../../core/auth/auth.service';
import { CatalogService } from '../../core/catalog/catalog.service';
import { AdminService } from '../../core/admin/admin.service';
import { InventoryRow } from '../../core/models/admin.models';
import { CatalogItem } from '../../core/models/api.models';

@Component({
  standalone: true,
  imports: [FormsModule],
  template: `
    <section class="operations-page pos-workspace">
      <div class="admin-heading pos-heading">
        <div>
          <p class="eyebrow">Caja · Venta y Devolución</p>
          <h2>Punto de venta (POS)</h2>
          <p class="admin-subtitle">Registra ventas presenciales en caja o procesa devoluciones con reingreso automático a inventario.</p>
        </div>
        <div class="pos-status">
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'SALE'" (click)="mode = 'SALE'; message = ''">
            <span class="material-symbols-outlined">point_of_sale</span>
            Nueva venta
          </button>
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'RETURN'" (click)="mode = 'RETURN'; message = ''">
            <span class="material-symbols-outlined">assignment_return</span>
            Devolución
          </button>
        </div>
      </div>

      @if (message) {
        <p class="pos-feedback" [class.pos-feedback-error]="message.includes('No se') || message.includes('no puede') || message.includes('suficiente') || message.includes('inválido') || message.includes('Error')">
          {{ message }}
        </p>
      }

      @if (mode === 'SALE') {
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div><span class="panel-index">NUEVA OPERACIÓN EN CAJA</span><h3>Registrar venta presencial</h3></div>
              <span class="material-symbols-outlined">receipt_long</span>
            </div>

            <div class="pos-form-grid">
              <!-- Sucursal -->
              <label>
                <span>Sucursal</span>
                <small>Tienda donde se realiza el cobro</small>
                @if (branches.length > 0 && !manualMode) {
                  <select [(ngModel)]="branchId" (ngModelChange)="onBranchChange($event)">
                    @for (b of branches; track b.id) {
                      <option [value]="b.id">{{ b.name }} (ID: {{ b.id }})</option>
                    }
                  </select>
                } @else {
                  <input type="number" min="1" [(ngModel)]="branchId" (ngModelChange)="onBranchChange($event)" placeholder="Ej. 5">
                }
              </label>

              <!-- Prenda / Variante -->
              <label>
                <span>Prenda / Variante</span>
                <small>{{ loadingInventory ? 'Cargando existencias en tienda...' : 'Selecciona una prenda con stock disponible' }}</small>
                @if (!manualMode && inventoryItems.length > 0) {
                  <select [(ngModel)]="variantId" (ngModelChange)="onVariantChange($event)">
                    @for (item of inventoryItems; track item.product_variant_id) {
                      <option [value]="item.product_variant_id">
                        {{ item.product_name }} - {{ item.size_name }} / {{ item.color_name }} (Disp: {{ item.available_quantity }})
                      </option>
                    }
                  </select>
                } @else {
                  <input type="number" min="1" [(ngModel)]="variantId" (ngModelChange)="onVariantChange($event)" placeholder="Ej. 29">
                }
                <div style="margin-top: 6px;">
                  <button type="button" style="font-size: 0.72rem; color: var(--accent, #9b724c); cursor: pointer; background: none; border: none; text-decoration: underline; padding: 0;" (click)="manualMode = !manualMode">
                    {{ manualMode ? '← Usar selector visual de productos' : 'Modo manual: ingresar IDs numéricos' }}
                  </button>
                </div>
              </label>

              <!-- Cantidad -->
              <label>
                <span>Cantidad</span>
                <small>Unidades a registrar</small>
                <input type="number" min="1" [max]="selectedVariant?.available_quantity || 999" [(ngModel)]="quantity" (ngModelChange)="onQuantityChange()">
              </label>

              <!-- Método de pago -->
              <label>
                <span>Método de pago</span>
                <small>Forma en la que abona el cliente</small>
                <select [(ngModel)]="paymentMethod">
                  <option value="CASH">Efectivo</option>
                  <option value="CARD">Tarjeta de débito/crédito</option>
                  <option value="QR">QR / Transferencia en caja</option>
                </select>
              </label>

              <!-- Referencia de pago -->
              <label>
                <span>Referencia de pago</span>
                <small>{{ paymentMethod === 'CASH' ? 'Opcional para efectivo' : 'Obligatoria para tarjeta / QR' }}</small>
                <input [(ngModel)]="transactionReference" [placeholder]="paymentMethod === 'CASH' ? 'Opcional' : 'Ej. POS-000123 o REF-9876'">
              </label>

              <!-- Total recibido -->
              <label>
                <span>Total recibido</span>
                <small>{{ paymentMethod === 'CASH' ? 'Importe entregado por el cliente' : 'Monto exacto cobrado' }}</small>
                <div class="pos-amount-input">
                  <b>Bs</b>
                  <input type="number" min="0.01" step="0.01" [(ngModel)]="amount" placeholder="0.00">
                </div>
              </label>
            </div>

            <button class="button button-dark pos-submit" type="button" [disabled]="busy || !valid" (click)="create()">
              <span class="material-symbols-outlined">payments</span>
              {{ busy ? 'Procesando venta...' : 'Cobrar venta' }}
              <span class="material-symbols-outlined pos-submit-arrow">arrow_forward</span>
            </button>
          </div>

          <aside class="pos-summary">
            <span class="panel-index">02 · RESUMEN DE VENTA</span>
            <h3>Operación rápida</h3>
            <p>Verifica los datos antes de confirmar. La venta descontará existencias del inventario de la sucursal seleccionada y aplicará promociones vigentes.</p>
            
            <div class="pos-summary-row"><span>Sucursal</span><strong>{{ selectedBranchName }}</strong></div>
            @if (selectedVariant) {
              <div class="pos-summary-row">
                <span>Prenda seleccionada</span>
                <strong>{{ selectedVariant.product_name }}</strong>
                <small style="color: rgba(255,255,255,0.7); font-size: 0.72rem;">{{ selectedVariant.size_name }} · {{ selectedVariant.color_name }} · SKU: {{ selectedVariant.sku }}</small>
              </div>
              <div class="pos-summary-row">
                <span>Stock en tienda</span>
                <strong>{{ selectedVariant.available_quantity }} disponibles</strong>
              </div>
            }
            <div class="pos-summary-row"><span>Forma de pago</span><strong>{{ paymentMethodLabel }}</strong></div>
            <div class="pos-summary-row"><span>Importe a registrar</span><strong>Bs {{ amount.toFixed(2) }}</strong></div>

            @if (lastTotal > 0) {
              <div class="pos-summary-row" style="background: rgba(255,255,255,0.08); padding: 12px; border-radius: 4px; margin-top: 8px;">
                <span>Total confirmado</span>
                <strong style="color: #9fe2bf; font-size: 1.1rem;">Bs {{ lastTotal.toFixed(2) }}</strong>
              </div>
              @if (paymentMethod === 'CASH') {
                <div class="pos-summary-row" style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 4px;">
                  <span>Cambio a devolver</span>
                  <strong style="font-size: 1rem;">{{ change > 0 ? 'Bs ' + change.toFixed(2) : 'Bs 0.00' }}</strong>
                </div>
              }
            }

            <div class="pos-summary-note">
              <span class="material-symbols-outlined">info</span>
              <small>{{ paymentMethod === 'CASH' ? 'En efectivo, si el cliente paga con un billete mayor, el sistema calcula el cambio exacto.' : 'La referencia y comprobante quedan registrados y auditables en la orden.' }}</small>
            </div>
          </aside>
        </div>
      } @else {
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div><span class="panel-index">GESTIÓN DE DEVOLUCIÓN</span><h3>Reingreso de prendas a inventario</h3></div>
              <span class="material-symbols-outlined">published_with_changes</span>
            </div>
            <p style="margin: 0 0 16px; font-size: 0.85rem; color: var(--muted);">
              Ingresa el ID de la venta completada. Las prendas se reintegrarán automáticamente al inventario físico de la sucursal y se generará el movimiento Kárdex respectivo.
            </p>
            <div class="pos-form-grid">
              <label>
                <span>ID de la venta / Orden</span>
                <small>Número identificador de la orden confirmada</small>
                <input type="number" min="1" [(ngModel)]="returnSaleId" placeholder="Ej. 12">
              </label>
              <label class="full" style="grid-column: 1 / -1;">
                <span>Motivo de la devolución</span>
                <small>Razón detallada para la bitácora y auditoría</small>
                <input [(ngModel)]="returnReason" placeholder="Ej. Talla incorrecta o cambio solicitado por el cliente">
              </label>
            </div>
            <button class="button button-dark pos-submit" type="button" [disabled]="busy || !returnValid" (click)="processReturn()">
              <span class="material-symbols-outlined">undo</span>
              {{ busy ? 'Procesando devolución...' : 'Confirmar devolución y reingreso' }}
              <span class="material-symbols-outlined pos-submit-arrow">arrow_forward</span>
            </button>
          </div>
          <aside class="pos-summary">
            <span class="panel-index">AUDITORÍA Y KÁRDEX</span>
            <h3>Impacto de devolución</h3>
            <p>Al procesar la devolución:</p>
            <div class="pos-summary-row"><span>Estado orden</span><strong>RETURNED</strong></div>
            <div class="pos-summary-row"><span>Kárdex</span><strong>RETURN (+stock)</strong></div>
            <div class="pos-summary-row"><span>Auditoría</span><strong>Bitácora actualizada</strong></div>
            <div class="pos-summary-note">
              <span class="material-symbols-outlined">verified</span>
              <small>Garantiza consistencia física y contable del inventario por sucursal.</small>
            </div>
          </aside>
        </div>
      }
    </section>
  `,
})
export class PosComponent implements OnInit {
  private readonly commerce = inject(CommerceService);
  private readonly auth = inject(AuthService);
  private readonly catalog = inject(CatalogService);
  private readonly admin = inject(AdminService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  mode: 'SALE' | 'RETURN' = 'SALE';

  // Sale fields
  branchId = 0;
  variantId = 0;
  quantity = 1;
  amount = 0;
  paymentMethod: 'CASH' | 'CARD' | 'QR' = 'CASH';
  transactionReference = '';
  lastTotal = 0;
  change = 0;

  // Enhancements
  branches: { id: number; name: string }[] = [];
  inventoryItems: InventoryRow[] = [];
  catalogProducts: CatalogItem[] = [];
  selectedVariant: InventoryRow | null = null;
  manualMode = false;
  loadingInventory = false;

  // Return fields
  returnSaleId: number | null = null;
  returnReason = 'Talla incorrecta o cambio solicitado por el cliente';

  busy = false;
  message = '';

  get valid(): boolean {
    return this.branchId > 0 && this.variantId > 0 && this.quantity > 0 && this.amount > 0 && (this.paymentMethod === 'CASH' || this.transactionReference.trim().length >= 3);
  }

  get returnValid(): boolean {
    return Boolean(this.returnSaleId && this.returnSaleId > 0 && this.returnReason.trim().length >= 3);
  }

  get paymentMethodLabel(): string {
    return ({ CASH: 'Efectivo', CARD: 'Tarjeta', QR: 'QR' } as Record<typeof this.paymentMethod, string>)[this.paymentMethod];
  }

  get selectedBranchName(): string {
    const branch = this.branches.find((b) => b.id === Number(this.branchId));
    return branch ? branch.name : (this.branchId > 0 ? `Sucursal #${this.branchId}` : 'No seleccionada');
  }

  ngOnInit(): void {
    const user = this.auth.currentUser();
    if (user?.branches && user.branches.length > 0) {
      this.branches = [...user.branches];
      this.branchId = this.branches[0].id;
    }

    this.catalog.filters().subscribe({
      next: (filters) => {
        if (filters.branches && filters.branches.length > 0) {
          if (this.branches.length === 0 || this.auth.currentUser()?.role === 'ADMIN') {
            this.branches = filters.branches.map((b) => ({ id: b.id, name: b.name }));
            if (!this.branchId && this.branches.length > 0) {
              this.branchId = this.branches[0].id;
            }
          }
        }
        if (this.branchId > 0) {
          this.loadBranchInventory();
        }
        this.changeDetector.detectChanges();
      },
      error: () => {
        if (this.branchId > 0) {
          this.loadBranchInventory();
        }
      },
    });

    this.catalog.list({ page: 1, page_size: 100 }).subscribe({
      next: (page) => {
        this.catalogProducts = page.items || [];
        this.updateSuggestedAmount();
      },
      error: () => undefined,
    });
  }

  loadBranchInventory(): void {
    if (!this.branchId || this.branchId <= 0) return;
    this.loadingInventory = true;
    this.admin.inventoryAll(Number(this.branchId), 1, 100).subscribe({
      next: (res) => {
        this.inventoryItems = res.items || [];
        this.loadingInventory = false;
        if (this.inventoryItems.length > 0) {
          const match = this.inventoryItems.find((i) => i.product_variant_id === Number(this.variantId)) || this.inventoryItems[0];
          this.onVariantChange(match.product_variant_id);
        }
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.loadingInventory = false;
        this.changeDetector.detectChanges();
      },
    });
  }

  onBranchChange(newBranchId: number): void {
    this.branchId = Number(newBranchId);
    this.variantId = 0;
    this.selectedVariant = null;
    this.loadBranchInventory();
  }

  onVariantChange(newVariantId: number): void {
    this.variantId = Number(newVariantId);
    this.selectedVariant = this.inventoryItems.find((i) => i.product_variant_id === this.variantId) || null;
    this.updateSuggestedAmount();
    this.changeDetector.detectChanges();
  }

  onQuantityChange(): void {
    if (this.quantity < 1) this.quantity = 1;
    this.updateSuggestedAmount();
  }

  private updateSuggestedAmount(): void {
    if (!this.selectedVariant) return;
    const prod = this.catalogProducts.find((p) => p.id === this.selectedVariant?.product_id);
    if (prod && prod.price > 0) {
      this.amount = Number((prod.price * this.quantity).toFixed(2));
    }
  }

  create(): void {
    if (!this.valid || this.busy) return;
    this.busy = true;
    this.message = '';
    this.commerce.physicalSale({ branch_id: Number(this.branchId), items: [{ product_variant_id: Number(this.variantId), quantity: this.quantity }] }).pipe(
      switchMap((sale) => this.commerce.cashPayment(sale.id, this.amount, this.paymentMethod, this.transactionReference.trim() || undefined)),
      timeout({ each: 10000 }),
      finalize(() => { this.busy = false; this.changeDetector.detectChanges(); }),
    ).subscribe({
      next: (paid) => {
        this.lastTotal = Number(paid.total);
        this.change = this.paymentMethod === 'CASH' ? Math.max(0, this.amount - this.lastTotal) : 0;
        this.message = `Venta ${paid.order_number} confirmada exitosamente. Total: Bs ${this.lastTotal.toFixed(2)}.`;
        this.quantity = 1;
        this.loadBranchInventory();
        this.changeDetector.detectChanges();
      },
      error: (error: { error?: { detail?: { message?: string } } }) => {
        this.message = error.error?.detail?.message || 'No se pudo confirmar la venta.';
        this.changeDetector.detectChanges();
      }
    });
  }

  processReturn(): void {
    if (!this.returnValid || this.busy || !this.returnSaleId) return;
    this.busy = true;
    this.message = '';
    this.commerce.returnSale(this.returnSaleId, this.returnReason.trim()).pipe(
      timeout({ each: 10000 }),
      finalize(() => { this.busy = false; this.changeDetector.detectChanges(); }),
    ).subscribe({
      next: (sale) => {
        this.message = `Devolución de la venta ${sale.order_number} procesada con éxito. Stock de prendas reingresado a inventario.`;
        this.returnSaleId = null;
        this.loadBranchInventory();
        this.changeDetector.detectChanges();
      },
      error: (error: { error?: { detail?: { message?: string } } }) => {
        this.message = error.error?.detail?.message || 'No se pudo procesar la devolución.';
        this.changeDetector.detectChanges();
      }
    });
  }
}
