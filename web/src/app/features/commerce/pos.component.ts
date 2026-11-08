import { ChangeDetectorRef, Component, ElementRef, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { catchError, finalize, switchMap, timeout, throwError } from 'rxjs';

import { CommerceService } from '../../core/commerce/commerce.service';
import { AuthService } from '../../core/auth/auth.service';
import { CatalogService } from '../../core/catalog/catalog.service';
import { AdminService } from '../../core/admin/admin.service';
import { CreditNoteBalanceLookup, CreditNoteSettlementRequest, CreditNoteSettlementResponse, ExchangeFinalizeInput, ExchangeFinalizeResponse, ExchangeQuote, ExchangeSaleItem, ExchangeSaleLookup, InventoryRow, ReturnCustomer, ReturnLookupResponse, ReturnRequest, ReturnResponse, Sale } from '../../core/models/admin.models';
import { CatalogItem } from '../../core/models/api.models';
import { OfflineCustomerRecord } from '../../core/offline/offline.models';
import { OfflineCatalogService } from '../../core/offline/offline-catalog.service';
import { OfflineTransactionService } from '../../core/offline/offline-transaction.service';
import { SyncTransactionService } from '../../core/offline/sync-transaction.service';
import { SyncCatalogService } from '../../core/offline/sync-catalog.service';

export interface PosCartItem {
  product_variant_id: number;
  product_id: number;
  product_name: string;
  sku: string;
  size_name: string;
  color_name: string;
  unit_price: number;
  quantity: number;
  available_quantity: number;
}

export interface PosInvoiceReceipt {
  invoice_number: string;
  control_code: string;
  is_offline: boolean;
  issued_at: string;
  tenant_name: string;
  branch_name: string;
  cashier_name: string;
  customer_name: string;
  customer_nit: string;
  customer_phone: string;
  payment_method: string;
  items: {
    sku: string;
    description: string;
    quantity: number;
    unit_price: number;
    subtotal: number;
  }[];
  subtotal: number;
  discount: number;
  total: number;
  amount_received: number;
  change_returned: number;
  qr_payload: string;
}

export interface PosLabelBatchItem {
  variant_id: number;
  sku: string;
  product_name: string;
  size_name: string;
  color_name: string;
  unit_price: number;
  copies: number;
}

export interface PosCashCloseReport {
  report_code: string;
  closed_at: string;
  branch_name: string;
  cashier_name: string;
  shift_label: string;
  opening_float: number;
  cash_sales_total: number;
  qr_sales_total: number;
  card_sales_total: number;
  exchange_cash_in: number;
  refunds_cash_out: number;
  expected_cash_in_drawer: number;
  counted_cash_in_drawer: number;
  discrepancy: number;
  status: 'EXACT' | 'SURPLUS' | 'SHORTAGE';
  transactions_count: number;
  notes: string;
  denominations: { label: string; value: number; count: number; subtotal: number }[];
}

@Component({
  standalone: true,
  imports: [FormsModule, DatePipe],
  template: `
    <section class="operations-page pos-workspace">
      <div class="admin-heading pos-heading">
        <div>
          <p class="eyebrow">Caja · Escáner de Código de Barras, Venta Multilínea y Facturación</p>
          <h2>Punto de venta (POS)</h2>
          <p class="admin-subtitle">Escanea prendas con código de barras o cámara, arma el ticket de compra, emite factura con QR o procesa devoluciones.</p>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap;">
          @if (syncCatalog.lastSync()) {
            <span style="font-size: 0.74rem; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 9999px; padding: 2px 10px; display: inline-flex; align-items: center; gap: 5px;">
              <span class="material-symbols-outlined" style="font-size: 14px;">cloud_done</span>
              Catálogo offline sincronizado ({{ syncCatalog.lastSync()?.sync_timestamp | date:'shortTime' }})
            </span>
          }
          @if (remoteScannerListening) {
            <span style="font-size: 0.74rem; color: #2e6f40; background: #e7f3eb; border: 1px solid #c2e2cc; border-radius: 9999px; padding: 2px 10px; display: inline-flex; align-items: center; gap: 5px;">
              <span class="material-symbols-outlined" style="font-size: 14px;">smartphone</span>
              Escáner móvil sincronizado (Sucursal #{{ branchId }})
            </span>
          }
        </div>
        <!-- GAFETE DE IDENTIFICACIÓN: CAJERO RESPONSABLE Y TURNO HORARIO EN VIVO -->
        <div style="background: #ffffff; border: 1.5px solid #e5e0d8; border-left: 4px solid #8f6d2d; border-radius: 10px; padding: 10px 16px; margin: 10px 0 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; box-shadow: 0 2px 8px rgba(20, 19, 18, 0.04);">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; border-radius: 50%; background: #1b1c1a; color: #d4b26f; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.05em; border: 1.5px solid #8f6d2d;">
              {{ getCashierInitials() }}
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                <strong style="font-size: 0.92rem; color: #1b1c1a;">{{ activeCashierName }}</strong>
                <span style="font-size: 0.65rem; font-weight: 800; text-transform: uppercase; background: #e7f3eb; color: #2e6f40; padding: 2px 7px; border-radius: 4px;">
                  CAJERO EN SESIÓN ACTIVA
                </span>
              </div>
              <small style="color: #6c6a64; font-size: 0.75rem; display: block;">
                {{ activeCashierEmail }} · Rol: {{ activeCashierRole }} · {{ selectedBranchName }}
              </small>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
            <div style="text-align: right;">
              <span style="font-size: 0.64rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #8f6d2d; display: block;">TURNO Y HORARIO ASIGNADO</span>
              <strong style="font-size: 0.84rem; color: #1b1c1a;">{{ cashCloseShiftLabel }}</strong>
            </div>
            <div style="text-align: right; border-left: 1px solid #eae4d8; padding-left: 14px;">
              <span style="font-size: 0.64rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6c6a64; display: block;">INICIO DE CAJA</span>
              <span style="font-size: 0.82rem; font-weight: 700; color: #1b1c1a;">{{ sessionStartTime | date:'HH:mm' }} hrs</span>
            </div>
          </div>
        </div>

        <div class="pos-status">
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'SALE'" (click)="mode = 'SALE'; message = ''">
            <span class="material-symbols-outlined">point_of_sale</span>
            Nueva venta
          </button>
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'CUSTOMERS'" (click)="mode = 'CUSTOMERS'; message = ''; loadOfflineCustomers()">
            <span class="material-symbols-outlined">badge</span>
            Clientes Offline ({{ offlineCustomers.length }})
          </button>
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'RETURN'" (click)="mode = 'RETURN'; message = ''">
            <span class="material-symbols-outlined">assignment_return</span>
            Devolución
          </button>
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'EXCHANGE'" (click)="mode = 'EXCHANGE'; message = ''">
            <span class="material-symbols-outlined">swap_horiz</span>
            Cambio
          </button>
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'LABELS'" (click)="openLabelsMode()">
            <span class="material-symbols-outlined">sell</span>
            Etiquetas
          </button>
          <button type="button" class="pos-mode-tab" [class.active]="mode === 'CASH_CLOSE'" (click)="openCashCloseMode()">
            <span class="material-symbols-outlined">account_balance_wallet</span>
            Cierre de Caja
          </button>
        </div>
      </div>

      @if (syncTx.pendingCount() > 0) {
        <div class="pos-feedback" style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span>
            <strong>Modo Offline:</strong> Hay {{ syncTx.pendingCount() }} operación(es) pendiente(s) de sincronización.
          </span>
          <button type="button" style="font-size: 0.75rem; padding: 0.3rem 0.6rem; background: #92400e; color: #fff; border: none; border-radius: 4px; cursor: pointer;" [disabled]="syncTx.isSyncing()" (click)="syncTx.syncPendingTransactions()">
            {{ syncTx.isSyncing() ? 'Sincronizando...' : 'Sincronizar ahora' }}
          </button>
        </div>
      }

      @if (message) {
        <p class="pos-feedback" [class.pos-feedback-error]="message.includes('No se') || message.includes('no puede') || message.includes('suficiente') || message.includes('inválido') || message.includes('Error')">
          {{ message }}
        </p>
      }

      @if (mode === 'SALE') {
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div><span class="panel-index">TERMINAL DE ESCANEO Y FACTURACIÓN</span><h3>Registrar venta presencial</h3></div>
              <span class="material-symbols-outlined">barcode_scanner</span>
            </div>

            <!-- TERMINAL DE ESCANEO RÁPIDO (MINIMALISTA Y VELOZ) -->
            <div style="margin-bottom: 18px; padding: 16px; border-radius: 12px; border: 1.5px solid #e7e2da; background: #ffffff; box-shadow: 0 1px 4px rgba(27, 28, 26, 0.04);">
              
              <!-- BARRA PRINCIPAL DE ESCANEO / BÚSQUEDA -->
              <div style="display: flex; gap: 8px; align-items: stretch;">
                <div style="position: relative; flex: 1; display: flex; align-items: center;">
                  <span class="material-symbols-outlined" style="position: absolute; left: 12px; font-size: 21px; color: #8f6d2d; pointer-events: none;">barcode_scanner</span>
                  <input
                    type="text"
                    [(ngModel)]="barcodeQuery"
                    (keyup.enter)="scanBarcode()"
                    placeholder="Escanear código de barras (pistola láser) o escribir SKU / prenda..."
                    aria-label="Escanear código de barras o SKU"
                    style="width: 100%; height: 44px; padding: 0 46px 0 42px; font-size: 0.92rem; border: 1.5px solid #dcd7cf; border-radius: 8px; background: #faf8f5; color: #1b1c1a; outline: none; box-sizing: border-box; transition: border-color 0.15s, background 0.15s;"
                    onfocus="this.style.borderColor='#8f6d2d'; this.style.background='#ffffff'"
                    onblur="this.style.borderColor='#dcd7cf'; this.style.background='#faf8f5'"
                  >
                  <!-- Botón de cámara discreto integrado dentro del campo de texto -->
                  <label title="Escanear etiqueta con la cámara" style="position: absolute; right: 6px; width: 32px; height: 32px; border-radius: 6px; background: #ede7df; color: #1b1c1a; display: flex; align-items: center; justify-content: center; cursor: pointer; margin: 0; transition: background 0.15s;" onmouseover="this.style.background='#dfd8ce'" onmouseout="this.style.background='#ede7df'">
                    <span class="material-symbols-outlined" style="font-size: 19px;">photo_camera</span>
                    <input type="file" accept="image/*" capture="environment" style="display: none;" (change)="onBarcodePhotoCaptured($event)">
                  </label>
                </div>

                <!-- Botón de acción principal: Agregar al Ticket -->
                <button type="button" class="button button-dark" style="height: 44px; padding: 0 20px; font-size: 0.88rem; font-weight: 600; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; background: #1b1c1a; color: #fff;" (click)="scanBarcode()">
                  <span class="material-symbols-outlined" style="font-size: 18px;">add_shopping_cart</span>
                  <span>+ Agregar</span>
                </button>
              </div>

              <!-- BARRA INFERIOR DISCRETA: ESTADO Y ACCIONES SECUNDARIAS -->
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 10px; padding-top: 8px; border-top: 1px solid #f2eee9;">
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: #6c6a64;">
                  <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #16a34a;"></span>
                  <span>Lector activo · Pistola láser USB y Celular sincronizados (Sucursal #{{ branchId }})</span>
                </div>

                <div style="display: flex; align-items: center; gap: 10px; font-size: 0.74rem;">
                  <button type="button" style="background: none; border: none; font-size: 0.74rem; color: #8f6d2d; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; padding: 2px 4px; text-decoration: underline;" (click)="toggleMobileGunPanel()">
                    <span class="material-symbols-outlined" style="font-size: 15px;">smartphone</span>
                    {{ showMobileGunPanel ? 'Ocultar conexión móvil' : 'Vincular celular' }}
                  </button>
                  
                  <span style="color: #dcd7cf;">•</span>
                  <button type="button" style="background: none; border: none; font-size: 0.74rem; color: #6c6a64; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; padding: 2px 4px;" (click)="showBarcodeSheet = !showBarcodeSheet">
                    <span class="material-symbols-outlined" style="font-size: 15px;">sell</span>
                    {{ showBarcodeSheet ? 'Ocultar catálogo' : 'Catálogo de etiquetas' }}
                  </button>
                </div>
              </div>

              <!-- FEEDBACK INSTANTÁNEO DE ESCANEO (SLIM & MINIMALISTA) -->
              @if (scannerFeedback) {
                <div role="status" [style.background]="scannerFeedbackError ? '#fef2f2' : '#f0fdf4'" [style.color]="scannerFeedbackError ? '#991b1b' : '#166534'" [style.borderColor]="scannerFeedbackError ? '#fecaca' : '#bbf7d0'" style="margin-top: 10px; padding: 8px 12px; border-radius: 6px; border: 1px solid; font-size: 0.82rem; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span class="material-symbols-outlined" style="font-size: 17px;">{{ scannerFeedbackError ? 'warning' : 'check_circle' }}</span>
                    <span>{{ scannerFeedback }}</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    @if (lastScannedItem && !scannerFeedbackError) {
                      <span style="font-weight: 700; font-family: monospace; background: #166534; color: #fff; padding: 1px 7px; border-radius: 4px; font-size: 0.75rem;">
                        Bs {{ lastScannedItem.unit_price.toFixed(2) }} (x{{ lastScannedItem.quantity }})
                      </span>
                    }
                    <button type="button" style="background: none; border: none; font-size: 1rem; color: inherit; cursor: pointer; line-height: 1; padding: 0 4px;" (click)="scannerFeedback = ''" title="Cerrar aviso">×</button>
                  </div>
                </div>
              }

              <!-- GUÍA COMPACTA DE VINCULACIÓN CON CELULAR (DESPLEGABLE LIMPIO) -->
              @if (showMobileGunPanel) {
                <div style="margin-top: 12px; padding: 14px 16px; background: #faf8f5; border: 1px solid #e7e2da; border-radius: 8px; color: #2c251f;">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 260px;">
                      <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                        <span class="material-symbols-outlined" style="font-size: 19px; color: #8f6d2d;">smartphone</span>
                        <strong style="font-size: 0.85rem;">Cómo usar tu celular como pistola escáner</strong>
                      </div>
                      <ol style="margin: 0; padding-left: 20px; font-size: 0.77rem; color: #57534e; line-height: 1.5;">
                        <li>Abre <strong>http://192.168.0.4:4201/pos</strong> en el navegador de tu celular con tu misma cuenta.</li>
                        <li>Toca el ícono de la cámara 📸 en la barra de escaneo de tu celular.</li>
                        <li>Toma foto al código de barras o QR: ¡la prenda se sumará automáticamente a esta pantalla!</li>
                      </ol>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end;">
                      <label class="button button-dark" style="cursor: pointer; font-size: 0.75rem; padding: 6px 12px; margin: 0; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; background: #8f6d2d; color: #fff;">
                        <span class="material-symbols-outlined" style="font-size: 16px;">photo_camera</span>
                        Probar cámara aquí
                        <input type="file" accept="image/*" capture="environment" style="display: none;" (change)="onBarcodePhotoCaptured($event)">
                      </label>
                      <button type="button" class="small-button" style="font-size: 0.72rem; padding: 3px 8px;" (click)="showMobileGunPanel = false">
                        Ocultar guía
                      </button>
                    </div>
                  </div>
                </div>
              }

              <!-- CATÁLOGO DE ETIQUETAS DEMO (COLAPSIBLE) -->
              @if (showBarcodeSheet) {
                <div style="margin-top: 12px; padding: 12px; background: #faf8f5; border: 1px dashed #dcd7cf; border-radius: 8px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                    <div>
                      <strong style="font-size: 0.82rem; color: #1b1c1a;">🏷️ Catálogo de Prendas con Código de Barras y QR</strong>
                      <small style="display: block; color: #6c6a64; font-size: 0.74rem;">
                        Haz clic en "+ Agregar (+1)" o apunta con la cámara de tu celular a la etiqueta.
                      </small>
                    </div>
                    <button type="button" class="small-button" style="font-size: 0.72rem; padding: 2px 8px;" (click)="showBarcodeSheet = false">
                      ✕ Cerrar
                    </button>
                  </div>
                  @if (inventoryItems.length === 0) {
                    <p style="font-size: 0.8rem; color: var(--muted); margin: 0;">No hay inventario cargado en esta sucursal.</p>
                  } @else {
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 10px; max-height: 280px; overflow-y: auto; padding: 4px;">
                      @for (item of inventoryItems; track item.product_variant_id) {
                        <div style="border: 1px solid #e7e2da; border-radius: 6px; padding: 8px 10px; background: #ffffff; display: flex; flex-direction: column; justify-content: space-between; gap: 6px;">
                          <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 4px;">
                              <strong style="font-size: 0.78rem; color: #1c1917; line-height: 1.2;">{{ item.product_name }}</strong>
                              <span style="font-size: 0.76rem; font-weight: 800; color: #8f6d2d; white-space: nowrap;">Bs {{ getVariantPrice(item).toFixed(2) }}</span>
                            </div>
                            <small style="font-size: 0.71rem; color: #6c6a64; display: block;">Talla: {{ item.size_name }} · Color: {{ item.color_name }} · Stock: {{ item.available_quantity }}</small>
                          </div>
                          <!-- Etiqueta Dual: Código de Barras 1D + Código QR 2D Oficial -->
                          <div style="background: #faf8f5; padding: 6px 8px; border: 1px solid #ede7df; border-radius: 6px; display: flex; align-items: center; gap: 8px;">
                            <div style="flex: 1; text-align: center; min-width: 0;">
                              <img [src]="'/api/v1/barcode-svg?text=' + encodeURIComponent(item.sku) + '&format=code128'" style="width: 100%; height: 30px; object-fit: contain; display: block;" [alt]="item.sku">
                              <small style="font-family: monospace; font-size: 0.68rem; font-weight: 700; color: #1c1917; display: block; margin-top: 1px;">{{ item.sku }}</small>
                            </div>
                            <div style="border-left: 1px dashed #dcd7cf; padding-left: 8px; flex-shrink: 0; text-align: center;">
                              <img [src]="'/api/v1/barcode-svg?text=' + encodeURIComponent(item.sku) + '&format=qr'" style="width: 44px; height: 44px; display: block; border-radius: 4px; border: 1px solid #ede7df;" [alt]="'QR ' + item.sku">
                              <span style="font-size: 0.55rem; color: #8f6d2d; font-weight: 800; display: block; text-transform: uppercase;">QR</span>
                            </div>
                          </div>
                          <button type="button" class="small-button" [disabled]="item.available_quantity < 1" style="width: 100%; font-size: 0.72rem; padding: 5px 8px; background: #1b1c1a; color: #fff; display: inline-flex; justify-content: center; align-items: center; gap: 4px;" (click)="scanBarcode(item.sku)">
                            <span class="material-symbols-outlined" style="font-size: 14px;">add_shopping_cart</span>
                            {{ item.available_quantity > 0 ? '+ Agregar (+1)' : 'Agotado' }}
                          </button>
                        </div>
                      }
                    </div>
                  }
                </div>
              }
            </div>

            <!-- TICKET MULTILÍNEA DE PRENDAS ESCANEADAS -->
            @if (cartItems.length > 0) {
              <div style="margin-bottom: 16px; padding: 14px; border-radius: 8px; border: 1.5px solid #9b724c; background: #fff;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                  <div>
                    <span style="font-size: 0.74rem; font-weight: 800; letter-spacing: 0.06em; color: #2c251f; text-transform: uppercase;">
                      🛒 Lista de Prendas en el Ticket Actual ({{ totalCartUnits }} {{ totalCartUnits === 1 ? 'unidad' : 'unidades' }})
                    </span>
                    <small style="display: block; color: var(--muted, #6b7280); font-size: 0.76rem;">
                      Escanea más prendas para seguir sumando a la factura o ajusta las cantidades.
                    </small>
                  </div>
                  <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 8px; color: #991b1b;" (click)="clearCart()">
                    Vaciar ticket
                  </button>
                </div>

                <div style="overflow-x: auto;">
                  <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
                    <thead>
                      <tr style="border-bottom: 2px solid #e5ded6; text-align: left; color: #57534e;">
                        <th style="padding: 6px;">Prenda / Variante</th>
                        <th style="padding: 6px;">SKU</th>
                        <th style="padding: 6px; text-align: right;">P. Unit.</th>
                        <th style="padding: 6px; text-align: center;">Cantidad</th>
                        <th style="padding: 6px; text-align: right;">Subtotal</th>
                        <th style="padding: 6px; text-align: center;">Quitar</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (line of cartItems; track line.product_variant_id) {
                        <tr style="border-bottom: 1px solid #f3f0ec;">
                          <td style="padding: 8px 6px;">
                            <strong style="display: block; color: #1c1917;">{{ line.product_name }}</strong>
                            <small style="color: #6b7280;">Talla: {{ line.size_name }} · Color: {{ line.color_name }} (Disp: {{ line.available_quantity }})</small>
                          </td>
                          <td style="padding: 8px 6px; font-family: monospace; font-size: 0.76rem;">{{ line.sku }}</td>
                          <td style="padding: 8px 6px; text-align: right;">Bs {{ line.unit_price.toFixed(2) }}</td>
                          <td style="padding: 8px 6px; text-align: center;">
                            <div style="display: inline-flex; align-items: center; gap: 4px;">
                              <button type="button" class="small-button" style="padding: 2px 7px; font-weight: 700;" (click)="updateCartItemQty(line.product_variant_id, -1)">-</button>
                              <span style="min-width: 24px; text-align: center; font-weight: 700;">{{ line.quantity }}</span>
                              <button type="button" class="small-button" style="padding: 2px 7px; font-weight: 700;" [disabled]="line.quantity >= line.available_quantity" (click)="updateCartItemQty(line.product_variant_id, 1)">+</button>
                            </div>
                          </td>
                          <td style="padding: 8px 6px; text-align: right; font-weight: 700; color: #1c1917;">
                            Bs {{ (line.unit_price * line.quantity).toFixed(2) }}
                          </td>
                          <td style="padding: 8px 6px; text-align: center;">
                            <button type="button" style="background: none; border: none; color: #991b1b; cursor: pointer; font-size: 1rem; font-weight: 700;" title="Eliminar línea" (click)="removeCartItem(line.product_variant_id)">×</button>
                          </td>
                        </tr>
                      }
                    </tbody>
                    <tfoot>
                      <tr style="border-top: 2px solid #2c251f; background: #faf8f5;">
                        <td colspan="4" style="padding: 10px 6px; font-weight: 800; text-align: right; text-transform: uppercase; font-size: 0.8rem;">
                          Total a Pagar ({{ totalCartUnits }} {{ totalCartUnits === 1 ? 'prenda' : 'prendas' }}):
                        </td>
                        <td style="padding: 10px 6px; text-align: right; font-weight: 900; font-size: 1.05rem; color: #15803d;">
                          Bs {{ cartTotal.toFixed(2) }}
                        </td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            }

            <!-- PASO 1 (OPCIONAL): BÚSQUEDA MANUAL DE PRENDAS SIN CÓDIGO DE BARRAS -->
            <div style="margin-bottom: 16px;">
              <button
                type="button"
                style="background: none; border: none; font-size: 0.78rem; color: #8f6d2d; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; padding: 4px 0; text-decoration: underline;"
                (click)="showManualPicker = !showManualPicker"
              >
                <span class="material-symbols-outlined" style="font-size: 17px;">search</span>
                {{ showManualPicker ? 'Ocultar selector manual de prendas' : '¿Prenda sin código de barras? Buscar manualmente en inventario' }}
              </button>

              @if (showManualPicker) {
                <div style="margin-top: 8px; padding: 14px; border-radius: 8px; border: 1px solid #e7e2da; background: #faf8f5;">
                  <span style="font-size: 0.76rem; font-weight: 700; color: #1b1c1a; display: block; margin-bottom: 8px;">
                    Seleccionar prenda del inventario de {{ selectedBranchName }}:
                  </span>
                  <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: flex-end;">
                    <div style="flex: 2; min-width: 220px;">
                      <input
                        type="text"
                        [(ngModel)]="itemFilterTerm"
                        placeholder="🔍 Filtrar lista por nombre, talla, color o SKU..."
                        style="width: 100%; margin-bottom: 6px; padding: 6px 10px; font-size: 0.8rem; border: 1px solid #dcd7cf; border-radius: 6px;"
                      >
                      <select [(ngModel)]="variantId" (ngModelChange)="onVariantChange($event)" style="width: 100%; padding: 7px 10px; font-size: 0.84rem; border: 1px solid #dcd7cf; border-radius: 6px;">
                        @for (item of filteredInventoryItems; track item.product_variant_id) {
                          <option [value]="item.product_variant_id">
                            {{ item.product_name }} - {{ item.size_name }} / {{ item.color_name }} · Bs {{ getVariantPrice(item).toFixed(2) }} (Disp: {{ item.available_quantity }})
                          </option>
                        }
                      </select>
                    </div>

                    <div style="width: 80px;">
                      <label style="font-size: 0.7rem; font-weight: 600; display: block; margin-bottom: 2px;">Cantidad:</label>
                      <input type="number" min="1" [max]="selectedVariant?.available_quantity || 99" [(ngModel)]="quantity" (ngModelChange)="onQuantityChange()" style="width: 100%; padding: 7px 8px; font-size: 0.85rem; border: 1px solid #dcd7cf; border-radius: 6px;">
                    </div>

                    <button type="button" class="button button-dark" style="height: 38px; padding: 0 14px; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 5px;" (click)="addCurrentSelectionToCart()">
                      <span class="material-symbols-outlined" style="font-size: 16px;">add_shopping_cart</span>
                      + Al ticket
                    </button>
                  </div>
                </div>
              }
            </div>

            <!-- PASO 2: DATOS DE FACTURACIÓN (RÁPIDO, CLARO Y SIN CONFUSIONES) -->
            <div style="margin-bottom: 18px; padding: 16px; border-radius: 10px; border: 1.5px solid #e7e2da; background: #ffffff; box-shadow: 0 1px 4px rgba(27, 28, 26, 0.03);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="material-symbols-outlined" style="font-size: 20px; color: #8f6d2d;">badge</span>
                  <strong style="font-size: 0.88rem; color: #1b1c1a;">Datos de Facturación</strong>
                </div>

                <!-- Toggle Rápido: Consumidor Final (Predeterminado) vs Factura con NIT -->
                <div style="display: flex; gap: 6px; background: #f3f0ec; padding: 3px; border-radius: 8px;">
                  <button
                    type="button"
                    [style.background]="!wantsInvoiceWithNit ? '#1b1c1a' : 'transparent'"
                    [style.color]="!wantsInvoiceWithNit ? '#ffffff' : '#6c6a64'"
                    style="border: none; padding: 5px 12px; font-size: 0.74rem; font-weight: 700; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: all 0.15s;"
                    (click)="setFinalConsumer()"
                  >
                    <span class="material-symbols-outlined" style="font-size: 15px;">person_off</span>
                    Consumidor Final (S/N)
                  </button>
                  <button
                    type="button"
                    [style.background]="wantsInvoiceWithNit ? '#1b1c1a' : 'transparent'"
                    [style.color]="wantsInvoiceWithNit ? '#ffffff' : '#6c6a64'"
                    style="border: none; padding: 5px 12px; font-size: 0.74rem; font-weight: 700; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: all 0.15s;"
                    (click)="wantsInvoiceWithNit = true"
                  >
                    <span class="material-symbols-outlined" style="font-size: 15px;">receipt</span>
                    Factura con NIT / Nombre
                  </button>
                </div>
              </div>

              <!-- SI ES CONSUMIDOR FINAL (90% DE LAS VENTAS) -->
              @if (!wantsInvoiceWithNit) {
                <div style="padding: 10px 14px; background: #faf8f5; border-radius: 6px; border: 1px dashed #dcd7cf; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                  <div style="display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: #57534e;">
                    <span class="material-symbols-outlined" style="color: #15803d; font-size: 18px;">check_circle</span>
                    <span>Factura emitida a <strong>Consumidor Final</strong> (CI/NIT: 0). Listo para cobro rápido.</span>
                  </div>
                  <button type="button" style="background: none; border: none; font-size: 0.74rem; color: #8f6d2d; cursor: pointer; text-decoration: underline;" (click)="wantsInvoiceWithNit = true">
                    Ingresar NIT del cliente →
                  </button>
                </div>
              }

              <!-- SI REQUIERE FACTURA PERSONALIZADA -->
              @if (wantsInvoiceWithNit) {
                <div>
                  @if (offlineCustomers.length > 0) {
                    <div style="margin-bottom: 10px;">
                      <select
                        [(ngModel)]="selectedOfflineCustomerId"
                        (ngModelChange)="onSelectOfflineCustomer($event)"
                        style="width: 100%; padding: 7px 10px; font-size: 0.8rem; border: 1px solid #dcd7cf; border-radius: 6px; background: #faf8f5;"
                      >
                        <option value="">-- Autocompletar con cliente frecuente o escribir abajo --</option>
                        @for (c of offlineCustomers; track c.id) {
                          <option [value]="c.id">👤 {{ c.full_name }} · CI/NIT: {{ c.nit_ci }}{{ c.phone ? ' · Tel: ' + c.phone : '' }}</option>
                        }
                      </select>
                    </div>
                  }

                  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">
                    <div>
                      <label style="font-size: 0.72rem; font-weight: 700; color: #292524; display: block; margin-bottom: 3px;">
                        CI o NIT Fiscal *
                      </label>
                      <input
                        type="text"
                        [(ngModel)]="customerNit"
                        placeholder="Ej. 4829104 o 0"
                        style="width: 100%; padding: 8px 10px; border-radius: 6px; border: 1.5px solid #dcd7cf; font-size: 0.88rem; font-family: monospace; font-weight: 700;"
                      >
                    </div>

                    <div>
                      <label style="font-size: 0.72rem; font-weight: 700; color: #292524; display: block; margin-bottom: 3px;">
                        Nombre o Razón Social *
                      </label>
                      <input
                        type="text"
                        [(ngModel)]="customerName"
                        placeholder="Ej. Ana María Gómez"
                        style="width: 100%; padding: 8px 10px; border-radius: 6px; border: 1.5px solid #dcd7cf; font-size: 0.88rem; font-weight: 600;"
                      >
                    </div>

                    <div>
                      <label style="font-size: 0.72rem; font-weight: 700; color: #292524; display: block; margin-bottom: 3px;">
                        Teléfono / WhatsApp (Opcional)
                      </label>
                      <input
                        type="text"
                        [(ngModel)]="customerPhone"
                        placeholder="Ej. 70012345"
                        style="width: 100%; padding: 8px 10px; border-radius: 6px; border: 1.5px solid #dcd7cf; font-size: 0.88rem;"
                      >
                    </div>
                  </div>

                  <div style="margin-top: 8px; display: flex; justify-content: flex-end; gap: 8px;">
                    <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 8px;" (click)="saveCurrentCustomerLocally()">
                      💾 Guardar en clientes frecuentes
                    </button>
                  </div>
                </div>
              }
            </div>

            <!-- PASO 3: COBRO EN EFECTIVO -->
            <div style="margin-bottom: 20px; padding: 16px; border-radius: 10px; border: 1.5px solid #e7e2da; background: #ffffff; box-shadow: 0 1px 4px rgba(27, 28, 26, 0.03);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="material-symbols-outlined" style="font-size: 20px; color: #8f6d2d;">payments</span>
                  <strong style="font-size: 0.88rem; color: #1b1c1a;">Cobro en Efectivo</strong>
                </div>

                <span style="font-size: 0.72rem; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 2px 10px; border-radius: 9999px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                  <span class="material-symbols-outlined" style="font-size: 14px;">check_circle</span>
                  Efectivo en Caja
                </span>
              </div>

              <div style="background: #faf8f5; padding: 14px; border-radius: 8px; border: 1px solid #ebd9c8;">
                <div style="display: flex; gap: 14px; align-items: stretch; flex-wrap: wrap;">
                  <!-- Monto entregado por el cliente -->
                  <div style="flex: 1; min-width: 220px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                      <label style="font-size: 0.74rem; font-weight: 700; color: #292524; display: block; margin-bottom: 5px;">
                        Efectivo entregado por el cliente:
                      </label>
                      <div style="display: flex; align-items: center; background: #ffffff; border: 1.5px solid #dcd7cf; border-radius: 8px; height: 44px; overflow: hidden; box-sizing: border-box;">
                        <span style="font-size: 0.95rem; font-weight: 800; color: #8f6d2d; padding: 0 12px; user-select: none;">Bs</span>
                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          [(ngModel)]="amount"
                          placeholder="0.00"
                          style="font-size: 1.15rem; font-weight: 800; color: #1b1c1a; width: 100%; height: 100%; border: none !important; border-radius: 0 !important; outline: none !important; background: transparent !important; padding: 0 10px !important; box-shadow: none !important;"
                        >
                      </div>
                    </div>

                    <!-- Billetes rápidos con 1 clic -->
                    <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 10px;">
                      <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 9px; background: #fff; border: 1px solid #dcd7cf; font-weight: 600;" (click)="amount = effectiveSaleTotal">
                        Exacto (Bs {{ effectiveSaleTotal.toFixed(2) }})
                      </button>
                      <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 9px; background: #fff; border: 1px solid #dcd7cf;" (click)="amount = 50">Bs 50</button>
                      <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 9px; background: #fff; border: 1px solid #dcd7cf;" (click)="amount = 100">Bs 100</button>
                      <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 9px; background: #fff; border: 1px solid #dcd7cf;" (click)="amount = 200">Bs 200</button>
                      <button type="button" class="small-button" style="font-size: 0.72rem; padding: 4px 9px; background: #fff; border: 1px solid #dcd7cf;" (click)="amount = Number((amount + 50).toFixed(2))">+Bs 50</button>
                    </div>
                  </div>

                  <!-- Tarjeta destacada de CAMBIO A DEVOLVER -->
                  <div style="flex: 1; min-width: 180px; background: #ffffff; padding: 14px; border-radius: 8px; border: 1.5px solid #c2e2cc; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <span style="font-size: 0.68rem; font-weight: 800; color: #15803d; text-transform: uppercase; letter-spacing: 0.05em; display: block;">
                      Cambio a devolver al cliente
                    </span>
                    <strong style="font-size: 1.8rem; color: #15803d; display: block; margin: 6px 0; font-family: monospace;">
                      Bs {{ liveChange.toFixed(2) }}
                    </strong>
                    <small style="font-size: 0.72rem; color: #6c6a64;">
                      {{ amount < effectiveSaleTotal ? '⚠️ Monto insuficiente para cubrir el total' : 'Calculado automáticamente' }}
                    </small>
                  </div>
                </div>
              </div>
            </div>

            <!-- PASO 4: ACCIONES FINALES DE COBRO Y RESERVA -->
            <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 14px;">
              <button
                class="button button-dark pos-submit"
                style="margin-top: 0; width: 100%; height: 50px; font-size: 1rem; font-weight: 700; justify-content: center;"
                type="button"
                [disabled]="busy || !valid"
                (click)="create()"
              >
                <span class="material-symbols-outlined">receipt_long</span>
                {{ busy ? 'Procesando venta y factura...' : 'Cobrar y Emitir Factura (Bs ' + effectiveSaleTotal.toFixed(2) + ')' }}
                <span class="material-symbols-outlined pos-submit-arrow">arrow_forward</span>
              </button>

              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <button
                  class="button button-light"
                  type="button"
                  style="font-size: 0.78rem; padding: 8px 14px; border: 1px solid #dcd7cf; color: #57534e; background: #fff;"
                  [disabled]="busy || !canReserveInPos"
                  (click)="reserveFromPos()"
                >
                  <span class="material-symbols-outlined" style="font-size: 16px; color: #8f6d2d;">bookmark_add</span>
                  Reservar / Apartar Prendas
                </button>

                <!-- Acordeón Nota de Crédito (Discreto) -->
                <details style="border: none; background: none; margin: 0;">
                  <summary style="font-size: 0.74rem; color: #8f6d2d; cursor: pointer; text-decoration: underline;">
                    ¿Canjear saldo de Nota de Crédito?
                  </summary>
                  <div style="margin-top: 8px; padding: 10px; background: #faf8f5; border: 1px dashed #dcd7cf; border-radius: 6px;">
                    <input [(ngModel)]="creditNoteCode" (blur)="lookupCreditNote()" placeholder="Código NC-2026-XXXX" style="padding: 6px 10px; font-size: 0.8rem; width: 100%;">
                    @if (creditNoteBalance) {
                      <small style="color: #15803d; display: block; margin-top: 4px;">Saldo: Bs {{ creditNoteBalance.available_balance }}</small>
                    }
                  </div>
                </details>
              </div>
            </div></div>

          <aside class="pos-summary">
            <span class="panel-index">02 · RESUMEN Y FACTURACIÓN</span>
            <h3>Ticket en Caja</h3>
            <p>Verifica las prendas escaneadas y el cambio antes de confirmar. Al cobrar se emitirá la Factura Comercial con código QR.</p>
            
            <div class="pos-summary-row"><span>Sucursal</span><strong>{{ selectedBranchName }}</strong></div>
            <div class="pos-summary-row">
              <span>Cliente (Factura)</span>
              <strong>{{ customerName.trim() || 'Consumidor Final' }}</strong>
              <small style="color: rgba(255,255,255,0.75); font-size: 0.72rem;">CI/NIT: {{ customerNit.trim() || '0' }}{{ customerPhone.trim() ? ' · Tel: ' + customerPhone.trim() : '' }}</small>
            </div>
            @if (cartItems.length > 0) {
              <div class="pos-summary-row">
                <span>Prendas en ticket</span>
                <strong>{{ cartItems.length }} línea(s) ({{ totalCartUnits }} ud.)</strong>
                <small style="color: rgba(255,255,255,0.75); font-size: 0.72rem;">
                  @for (c of cartItems; track c.product_variant_id) {
                    <span style="display: block;">• {{ c.quantity }}x {{ c.product_name }} ({{ c.size_name }}/{{ c.color_name }}) — Bs {{ (c.unit_price * c.quantity).toFixed(2) }}</span>
                  }
                </small>
              </div>
            } @else if (selectedVariant) {
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
            <div class="pos-summary-row"><span>Total a cobrar</span><strong style="color: #fde68a;">Bs {{ effectiveSaleTotal.toFixed(2) }}</strong></div>
            <div class="pos-summary-row"><span>Efectivo recibido</span><strong>Bs {{ amount.toFixed(2) }}</strong></div>
            @if (paymentMethod === 'CASH') {
              <div class="pos-summary-row" style="background: rgba(255,255,255,0.08); padding: 10px; border-radius: 6px; margin-top: 6px;">
                <span>Cambio estimado a devolver</span>
                <strong style="color: #9fe2bf; font-size: 1.05rem;">Bs {{ liveChange.toFixed(2) }}</strong>
              </div>
            }

            @if (lastInvoice) {
              <div style="margin-top: 14px;">
                <button type="button" class="button button-light" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 6px; font-size: 0.82rem; background: #10b981; color: #fff; border: none;" (click)="showInvoiceModal = true">
                  <span class="material-symbols-outlined" style="font-size: 18px;">print</span>
                  Ver / Imprimir Factura ({{ lastInvoice.invoice_number }})
                </button>
              </div>
            }

            <div class="pos-summary-note">
              <span class="material-symbols-outlined">info</span>
              <small>{{ paymentMethod === 'CASH' ? 'En efectivo, si el cliente paga con un billete mayor, el sistema calcula el cambio exacto.' : 'La referencia y comprobante quedan registrados y auditables en la orden.' }}</small>
            </div>
          </aside>
        </div>
      } @else if (mode === 'CUSTOMERS') {
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div><span class="panel-index">GESTIÓN DE DATOS MÍNIMOS DE CLIENTES OFFLINE</span><h3>Padrón Local de Clientes (IndexedDB)</h3></div>
              <span class="material-symbols-outlined">person_add</span>
            </div>
            <p style="margin: 0 0 16px; font-size: 0.85rem; color: var(--muted);">
              Registra o consulta datos mínimos de clientes en el almacenamiento local del navegador (IndexedDB) para emitir comprobantes de venta o reservas cuando la tienda opere sin conexión a Internet.
            </p>

            <div class="pos-form-grid">
              <label>
                <span>Nombre completo / Razón Social *</span>
                <small>Nombre fiscal para el comprobante o reserva</small>
                <input [(ngModel)]="newCustName" placeholder="Ej. Carlos Alberto Rojas">
              </label>
              <label>
                <span>CI / NIT *</span>
                <small>Documento de identidad o NIT tributario</small>
                <input [(ngModel)]="newCustNit" placeholder="Ej. 5928371015">
              </label>
              <label>
                <span>Teléfono / Celular</span>
                <small>Contacto para reservas o notificaciones</small>
                <input [(ngModel)]="newCustPhone" placeholder="Ej. 72194850">
              </label>
              <label>
                <span>Correo electrónico</span>
                <small>Opcional para envío posterior de recibo</small>
                <input [(ngModel)]="newCustEmail" placeholder="Ej. cliente@correo.com">
              </label>
            </div>

            <button class="button button-dark pos-submit" type="button" [disabled]="!newCustName.trim() || !newCustNit.trim()" (click)="createOfflineCustomer()">
              <span class="material-symbols-outlined">save</span>
              Guardar cliente en IndexedDB
              <span class="material-symbols-outlined pos-submit-arrow">arrow_forward</span>
            </button>

            <div style="margin-top: 24px; border-top: 1px solid var(--border, #e5ded6); padding-top: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px;">
                <h4 style="margin: 0;">Clientes almacenados localmente ({{ filteredOfflineCustomers.length }})</h4>
                <input
                  [(ngModel)]="customerSearchQuery"
                  (ngModelChange)="filterOfflineCustomers()"
                  placeholder="Buscar por nombre, CI/NIT o teléfono..."
                  style="max-width: 280px; padding: 6px 10px; font-size: 0.82rem;"
                >
              </div>

              @if (filteredOfflineCustomers.length === 0) {
                <p style="padding: 24px; text-align: center; color: var(--muted, #6b7280); background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px dashed #d6c5b3;">
                  No hay clientes registrados en el padrón local con ese criterio de búsqueda.
                </p>
              } @else {
                <div style="overflow-x: auto;">
                  <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                    <thead>
                      <tr style="border-bottom: 2px solid var(--border, #e5ded6); text-align: left; color: #57534e;">
                        <th style="padding: 10px 8px;">Cliente</th>
                        <th style="padding: 10px 8px;">CI / NIT</th>
                        <th style="padding: 10px 8px;">Teléfono</th>
                        <th style="padding: 10px 8px; text-align: right;">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (c of filteredOfflineCustomers; track c.id) {
                        <tr style="border-bottom: 1px solid rgba(0,0,0,0.06); transition: background 0.15s ease;">
                          <td style="padding: 10px 8px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                              <div style="width: 32px; height: 32px; border-radius: 50%; background: #2c251f; color: #f5eedf; display: flex; align-items: center; justify-content: center; font-size: 0.76rem; font-weight: 700; flex-shrink: 0;">
                                {{ getCustomerInitials(c.full_name) }}
                              </div>
                              <div>
                                <strong style="display: block; color: #1c1917; line-height: 1.2;">{{ c.full_name }}</strong>
                                @if (c.email) {
                                  <small style="color: #78716c; font-size: 0.72rem;">{{ c.email }}</small>
                                }
                              </div>
                            </div>
                          </td>
                          <td style="padding: 10px 8px;">
                            <span style="font-family: monospace; font-size: 0.82rem; font-weight: 700; background: #f5f2ed; padding: 2px 6px; border-radius: 4px; border: 1px solid #e2dad0;">
                              {{ c.nit_ci }}
                            </span>
                          </td>
                          <td style="padding: 10px 8px; color: #44403c; font-size: 0.82rem;">
                            {{ c.phone || 'Sin teléfono' }}
                          </td>
                          <td style="padding: 10px 8px; text-align: right; vertical-align: middle;">
                            <div style="display: inline-flex; gap: 6px; justify-content: flex-end;">
                              <button
                                type="button"
                                class="small-button"
                                style="font-size: 0.74rem; font-weight: 700; padding: 5px 10px; background: #2c251f; color: #fff; border-radius: 5px; display: inline-flex; align-items: center; gap: 4px;"
                                (click)="useCustomerForSale(c)"
                              >
                                <span class="material-symbols-outlined" style="font-size: 14px;">point_of_sale</span>
                                Usar en Venta
                              </button>
                              <button
                                type="button"
                                class="small-button"
                                style="font-size: 0.74rem; padding: 5px 8px; color: #991b1b; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 5px;"
                                title="Eliminar del padrón local"
                                (click)="removeOfflineCustomer(c.id)"
                              >
                                <span class="material-symbols-outlined" style="font-size: 14px;">delete</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            </div>
          </div>

          <aside class="pos-summary">
            <span class="panel-index">PERSISTENCIA LOCAL</span>
            <h3>Padrón Offline IndexedDB</h3>
            <p>Los datos mínimos de clientes persisten en el almacén <code>offline_customers</code> de IndexedDB, sobreviviendo al cierre del navegador o cortes de energía.</p>
            <div class="pos-summary-row"><span>Almacén local</span><strong>offline_customers</strong></div>
            <div class="pos-summary-row"><span>Total registrados</span><strong>{{ offlineCustomers.length }} cliente(s)</strong></div>
            <div class="pos-summary-row"><span>Cliente activo en caja</span><strong>{{ customerName || 'Consumidor Final' }}</strong></div>
            <div class="pos-summary-note">
              <span class="material-symbols-outlined">offline_pin</span>
              <small>Al registrar una venta o reserva sin red, los datos del cliente viajan en el payload outbox hacia el servidor.</small>
            </div>
          </aside>
        </div>
      } @else if (mode === 'EXCHANGE') {
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div>
                <span class="panel-index">ATELIER · GESTIÓN DE CAMBIO DE PRENDAS</span>
                <h3>Cambio de prenda en tienda</h3>
              </div>
              <span class="material-symbols-outlined">swap_horiz</span>
            </div>

            <!-- Stepper visual de 3 pasos -->
            <div class="exchange-stepper">
              <div class="exchange-step-item" [class.active]="!exchangeSale" [class.completed]="!!exchangeSale">
                <span class="step-num">1</span>
                <span>Búsqueda & Política</span>
              </div>
              <span class="material-symbols-outlined exchange-step-arrow">chevron_right</span>
              <div class="exchange-step-item" [class.active]="exchangeSale && !exchangeQuote" [class.completed]="!!exchangeQuote">
                <span class="step-num">2</span>
                <span>Inspección & Selección</span>
              </div>
              <span class="material-symbols-outlined exchange-step-arrow">chevron_right</span>
              <div class="exchange-step-item" [class.active]="!!exchangeQuote" [class.completed]="!!exchangeSuccess">
                <span class="step-num">3</span>
                <span>Cotización & Liquidación</span>
              </div>
            </div>

            @if (!isOnline) {
              <p class="pos-feedback pos-feedback-error" role="alert">
                <span class="material-symbols-outlined" style="vertical-align: middle; margin-right: 4px;">wifi_off</span>
                Los cambios se validan y cotizan exclusivamente online contra el stock central de la sucursal. Conectate a Internet para continuar.
              </p>
            }

            <!-- Paso 1: Búsqueda del comprobante -->
            <div class="pos-form-grid" style="align-items: flex-end;">
              <label>
                <span>Número de orden o comprobante</span>
                <small>Ingresá el número de ticket de venta (ej. ORD-42 o FS-20261107-...)</small>
                <input [(ngModel)]="exchangeOrderNumber" (blur)="exchangeLookupTouched = true" (ngModelChange)="onExchangeOrderNumberChange($event)" [disabled]="!!exchangePendingRetry" placeholder="Ej. ORD-42" aria-label="Número de orden o comprobante">
              </label>
              <div style="display:flex; align-items:center; gap: 8px;">
                <button type="button" class="button button-dark" style="height: 42px; display: inline-flex; align-items: center; gap: 6px;" [disabled]="exchangeBusy || !isOnline || !!exchangePendingRetry || !exchangeOrderNumber.trim()" (click)="lookupExchangeSale()">
                  <span class="material-symbols-outlined" style="font-size: 18px;">search</span>
                  {{ exchangeBusy ? 'Consultando...' : 'Buscar venta' }}
                </button>
                @if (exchangeSale || exchangeSuccess) {
                  <button type="button" class="small-button" style="height: 42px; padding: 0 14px;" [disabled]="exchangeBusy || !!exchangePendingRetry" (click)="resetExchangeFlow()">
                    <span class="material-symbols-outlined" style="font-size: 16px; vertical-align: middle;">restart_alt</span>
                    Nuevo cambio
                  </button>
                }
              </div>
            </div>
            @if (exchangeLookupTouched && !exchangeOrderNumber.trim()) {
              <small role="alert" style="color: #991b1b; display: block; margin-top: 6px;">Ingresá un número de orden o comprobante válido.</small>
            }

            <!-- Tarjeta de Política y Datos de la Venta Encontrada -->
            @if (exchangeSale) {
              <div class="exchange-policy-card" style="margin-top: 18px;">
                <div class="exchange-policy-header">
                  <div>
                    <strong style="font-size: 1rem; color: #0f172a;">Comprobante: {{ exchangeSale.order_number }}</strong>
                    <small style="display: block; color: var(--muted, #64748b); margin-top: 2px;">
                      Emisión: {{ exchangeSale.sale_date | date:'dd/MM/yyyy HH:mm' }} · Sucursal #{{ exchangeSale.branch_id }} · Estado: {{ exchangeSale.status }}
                    </small>
                  </div>
                  <div class="exchange-policy-badge" [class.badge-valid]="exchangeSale.is_within_policy" [class.badge-expired]="!exchangeSale.is_within_policy">
                    <span class="material-symbols-outlined" style="font-size: 14px;">{{ exchangeSale.is_within_policy ? 'verified' : 'history_toggle_off' }}</span>
                    {{ exchangeSale.is_within_policy ? ('En plazo de política · Día ' + (exchangeSale.days_elapsed || 0) + ' de ' + (exchangeSale.store_policy_days || 30)) : 'Plazo expirado' }}
                  </div>
                </div>
                <div style="font-size: 0.76rem; color: #475569; background: #fff; padding: 8px 12px; border-radius: 6px; border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 6px;">
                  <span class="material-symbols-outlined" style="font-size: 16px; color: var(--accent, #b8924a);">info</span>
                  <span>{{ exchangeSale.policy_summary || 'Política de tienda: 30 días para prendas generales. Gala: 15 días. Ropa íntima: Sin cambios.' }}</span>
                </div>
              </div>

              <!-- Paso 2: Inspección y Selección Dual (Prenda a devolver vs Prenda de reemplazo) -->
              <div class="exchange-dual-grid">
                <!-- Columna Izquierda: Prenda Recibida e Inspección Física -->
                <div class="exchange-column-card">
                  <h4 class="exchange-column-title">
                    <span class="material-symbols-outlined">assignment_return</span>
                    1. Prenda a recibir del cliente
                  </h4>

                  <label>
                    <span>Prenda adquirida</span>
                    <small>Seleccioná el artículo del ticket que el cliente desea cambiar</small>
                    <select [(ngModel)]="exchangeReturnedVariantId" (ngModelChange)="onExchangeSelectionChange('returnedVariant', $event)" [disabled]="!!exchangePendingRetry">
                      <option [ngValue]="0">Seleccioná una prenda</option>
                      @for (item of exchangeSale.items; track item.id) {
                        <option [ngValue]="item.variant_id" [disabled]="item.remaining_exchangeable_quantity < 1 || !item.is_exchangeable">
                          {{ item.name }} · {{ item.sku }} · Bs {{ item.net_paid_line_total }} (Restan {{ item.remaining_exchangeable_quantity }} de {{ item.purchased_quantity }})
                          @if (!item.is_exchangeable) { [NO DISPONIBLE PARA CAMBIO] }
                        </option>
                      }
                    </select>
                  </label>

                  @if (selectedReturnedItem) {
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; font-size: 0.74rem;">
                      <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>Regla de cambio:</span>
                        <strong style="color: #0f172a;">{{ selectedReturnedItem.policy_note || 'Plazo estándar de 30 días' }}</strong>
                      </div>
                      <div style="display: flex; justify-content: space-between;">
                        <span>Días transcurridos:</span>
                        <strong [style.color]="selectedReturnedItemWithinPolicy ? '#047857' : '#991b1b'">
                          {{ exchangeSale.days_elapsed || 0 }} de {{ selectedReturnedItemPolicyDays }} días permitidos
                        </strong>
                      </div>
                    </div>
                  }

                  <label>
                    <span>Cantidad a devolver</span>
                    <small>Unidades recibidas físicamente en mostrador</small>
                    <input type="number" min="1" [(ngModel)]="exchangeReturnedQuantity" (ngModelChange)="onExchangeSelectionChange('returnedQuantity', $event)" (blur)="exchangeQuantityTouched = true" [disabled]="!!exchangePendingRetry">
                    @if (exchangeQuantityTouched && exchangeReturnedVariantId > 0 && !exchangeReturnedQuantityValid) {
                      <small role="alert" style="color: #991b1b;">La cantidad debe estar entre 1 y las unidades restantes disponibles.</small>
                    }
                  </label>

                  <!-- Criterios de Inspección Física y Políticas de Devolución -->
                  <div>
                    <span style="display: block; font-size: 0.72rem; font-weight: 600; margin-bottom: 2px;">Estado físico de la prenda (Inspección en mostrador)</span>
                    <small style="color: var(--muted, #64748b); font-size: 0.65rem; display: block; margin-bottom: 8px;">Debe cumplir con las normas de higiene y preservación de la tienda</small>

                    <div class="condition-pill-group">
                      <div class="condition-pill" [class.active]="exchangeItemCondition === 'EXCELLENT'" (click)="exchangeItemCondition = 'EXCELLENT'; invalidateExchangeQuote()">
                        <strong>Excelente</strong>
                        <small>Con etiquetas originales, sin uso</small>
                      </div>
                      <div class="condition-pill" [class.active]="exchangeItemCondition === 'GOOD'" (click)="exchangeItemCondition = 'GOOD'; invalidateExchangeQuote()">
                        <strong>Bueno</strong>
                        <small>Sin etiquetas, impecable</small>
                      </div>
                      <div class="condition-pill" [class.active]="exchangeItemCondition === 'MINOR_DETAIL'" (click)="exchangeItemCondition = 'MINOR_DETAIL'; invalidateExchangeQuote()">
                        <strong>Detalle Menor</strong>
                        <small>Arruga leve, vaporizado</small>
                      </div>
                      <div class="condition-pill pill-reject" [class.active]="exchangeItemCondition === 'REJECTED'" (click)="exchangeItemCondition = 'REJECTED'; invalidateExchangeQuote()">
                        <strong style="color: #991b1b;">Rechazada</strong>
                        <small>Manchas, olor o daños (No apta)</small>
                      </div>
                    </div>
                  </div>

                  <!-- Checklist de Políticas de Devolución -->
                  <div class="inspection-checklist">
                    <span style="font-size: 0.7rem; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.04em;">Checklist de cumplimiento de políticas:</span>
                    <label class="inspection-check-item">
                      <input type="checkbox" [(ngModel)]="exchangeCheckClean" (change)="invalidateExchangeQuote()">
                      <span>Prenda limpia, libre de manchas, transpiración o perfumes</span>
                    </label>
                    <label class="inspection-check-item">
                      <input type="checkbox" [(ngModel)]="exchangeCheckUnworn" (change)="invalidateExchangeQuote()">
                      <span>Sin evidencias de uso, lavado, descosidos ni alteraciones</span>
                    </label>
                    <label class="inspection-check-item">
                      <input type="checkbox" [(ngModel)]="exchangeCheckTags" (change)="invalidateExchangeQuote()">
                      <span>Etiquetas de marca y código de barras legibles</span>
                    </label>
                    <label class="inspection-check-item">
                      <input type="checkbox" [(ngModel)]="exchangeCheckReceipt" (change)="invalidateExchangeQuote()">
                      <span>Comprobante de venta y plazo vigente dentro de la política</span>
                    </label>
                  </div>

                  @if (exchangeItemCondition === 'REJECTED') {
                    <div style="background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 10px 12px; border-radius: 6px; font-size: 0.74rem;">
                      <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle; margin-right: 4px;">warning</span>
                      <strong>Prenda no apta:</strong> El estado clasificado como Rechazada impide realizar el cambio según las políticas de calidad de la tienda.
                    </div>
                  } @else if (!exchangeChecklistValid) {
                    <div style="background: #fffbeb; border: 1px solid #fde68a; color: #92400e; padding: 8px 12px; border-radius: 6px; font-size: 0.74rem;">
                      <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle; margin-right: 4px;">info</span>
                      Verificá que se cumplan las condiciones indispensables de la política para habilitar la cotización.
                    </div>
                  }

                  <label>
                    <span>Observaciones de inspección (opcional)</span>
                    <input [(ngModel)]="exchangeConditionNotes" maxlength="255" [disabled]="!!exchangePendingRetry" placeholder="Ej. Prenda recibida en empaque original">
                  </label>
                </div>

                <!-- Columna Derecha: Prenda de Reemplazo Solicitada -->
                <div class="exchange-column-card">
                  <h4 class="exchange-column-title">
                    <span class="material-symbols-outlined">add_shopping_cart</span>
                    2. Prenda de reemplazo a entregar
                  </h4>

                  <label>
                    <span>Variante disponible en sucursal</span>
                    <small>Catálogo con stock verificado en la sucursal de la venta</small>
                    <select [(ngModel)]="exchangeNewVariantId" (ngModelChange)="onExchangeSelectionChange('newVariant', $event)" [disabled]="!!exchangePendingRetry">
                      <option [ngValue]="0">Seleccioná una variante de reemplazo</option>
                      @for (item of exchangeInventoryItems; track item.product_variant_id) {
                        <option [ngValue]="item.product_variant_id" [disabled]="item.available_quantity < 1">
                          {{ item.product_name }} · {{ item.size_name }} / {{ item.color_name }} · Disponible: {{ item.available_quantity }} un.
                        </option>
                      }
                    </select>
                  </label>

                  <label>
                    <span>Cantidad nueva a entregar</span>
                    <small>Unidades de la nueva variante</small>
                    <input type="number" min="1" [(ngModel)]="exchangeNewQuantity" (ngModelChange)="onExchangeSelectionChange('newQuantity', $event)" [disabled]="!!exchangePendingRetry">
                    @if (exchangeNewVariantId > 0 && !exchangeNewQuantityValid) {
                      <small role="alert" style="color: #991b1b;">La cantidad supera el stock vendible disponible en la sucursal.</small>
                    }
                  </label>

                  <label>
                    <span>Motivo u observación del cambio</span>
                    <small>Razón para la bitácora y auditoría de inventario</small>
                    <input [(ngModel)]="exchangeReason" maxlength="255" [disabled]="!!exchangePendingRetry" placeholder="Ej. Cambio de talla solicitado por el cliente">
                  </label>

                  <div style="margin-top: auto; padding-top: 14px;">
                    <button type="button" class="button button-dark" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;" [disabled]="exchangeBusy || !isOnline || !!exchangePendingRetry || !exchangeSelectionValid" (click)="requestExchangeQuote()">
                      <span class="material-symbols-outlined" style="font-size: 18px;">request_quote</span>
                      {{ exchangeBusy ? 'Cotizando en servidor...' : (exchangeQuote ? 'Actualizar cotización oficial' : 'Solicitar cotización oficial') }}
                    </button>
                    @if (!selectedReturnedItemWithinPolicy && selectedReturnedItem) {
                      <small role="alert" style="color: #991b1b; display: block; margin-top: 8px; text-align: center;">
                        El plazo para cambiar esta prenda ha vencido según la política de la tienda.
                      </small>
                    }
                  </div>
                </div>
              </div>
            }

            @if (exchangePendingRetry) {
              <p class="pos-feedback" role="alert" style="margin-top: 18px;">
                La confirmación anterior tuvo una respuesta incierta del servidor. Se congelaron los datos de la operación; reintentá para verificar el resultado exacto sin duplicar movimientos.
              </p>
            }

            <!-- Paso 3: Cotización Autenticada y Liquidación de Diferencia -->
            @if (exchangeQuote) {
              <div class="exchange-quote-card" role="status">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #cbd5e1; padding-bottom: 10px;">
                  <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.15rem; color: #0f172a;">
                    Cotización oficial autenticada
                  </strong>
                  <span style="font-size: 0.72rem; color: #64748b;">
                    Firma digital SHA-256 ✓ · Vigente hasta {{ exchangeQuote.expires_at | date:'HH:mm:ss' }}
                  </span>
                </div>

                <div class="exchange-quote-grid">
                  <div class="exchange-quote-item">
                    <span>Valor recibido (abono)</span>
                    <strong>Bs {{ exchangeQuote.returned_value }}</strong>
                  </div>
                  <div class="exchange-quote-item">
                    <span>Precio unitario reemplazo</span>
                    <strong>Bs {{ exchangeQuote.replacement_unit_price }}</strong>
                  </div>
                  <div class="exchange-quote-item">
                    <span>Total a entregar</span>
                    <strong>Bs {{ exchangeQuote.delivered_value }}</strong>
                  </div>
                  <div class="exchange-quote-item">
                    <span>Stock en sucursal</span>
                    <strong style="color: #047857;">{{ exchangeQuote.available_stock }} disponible</strong>
                  </div>
                </div>

                <!-- Banner de Liquidación según Diferencia -->
                @if (exchangeDifference > 0) {
                  <div class="exchange-settlement-banner settlement-charge">
                    <div>
                      <span>Diferencia a cobrar al cliente:</span>
                      <strong style="font-size: 1.1rem; margin-left: 6px;">+Bs {{ exchangeDifference.toFixed(2) }}</strong>
                    </div>
                    <span style="font-size: 0.76rem; color: #1e40af;">Requiere pago de diferencia en caja</span>
                  </div>
                  @if (exchangeQuote.cash_settlement_eligible) {
                    <label style="margin-top: 14px; display: block;">
                      <span style="font-weight: 600;">Efectivo recibido en caja (Bs)</span>
                      <input type="number" min="0" step="0.01" [(ngModel)]="exchangeCashTendered" (blur)="exchangeTenderTouched = true" [disabled]="!!exchangePendingRetry" placeholder="Monto entregado por el cliente">
                      <small style="display: block; margin-top: 4px;">Debe cubrir Bs {{ exchangeDifference.toFixed(2) }}. Cambio a devolver: <strong>Bs {{ exchangeChange.toFixed(2) }}</strong></small>
                      @if (exchangeTenderTouched && exchangeCashTendered < exchangeDifference) {
                        <small role="alert" style="color: #991b1b; display: block; margin-top: 4px;">El efectivo recibido es insuficiente para cubrir la diferencia.</small>
                      }
                    </label>
                  } @else {
                    <p role="alert" style="color: #991b1b; margin-top: 10px; font-size: 0.82rem;">
                      No se puede liquidar diferencia monetaria porque la venta original no fue en efectivo.
                    </p>
                  }
                } @else if (exchangeDifference < 0) {
                  <div class="exchange-settlement-banner settlement-refund">
                    <div>
                      <span>Saldo a favor del cliente (reembolso):</span>
                      <strong style="font-size: 1.1rem; margin-left: 6px;">-Bs {{ (-exchangeDifference).toFixed(2) }}</strong>
                    </div>
                    <span style="font-size: 0.76rem; color: #065f46;">Devolución de efectivo en mostrador</span>
                  </div>
                  @if (exchangeQuote.cash_settlement_eligible) {
                    <label style="margin-top: 14px; display: flex; align-items: center; gap: 10px; font-size: 0.84rem; cursor: pointer;">
                      <input type="checkbox" [(ngModel)]="exchangeCashierConfirmed" [disabled]="!!exchangePendingRetry" style="width: 17px; height: 17px;">
                      <span>Confirmo haber entregado en efectivo al cliente el reembolso por <strong>Bs {{ (-exchangeDifference).toFixed(2) }}</strong></span>
                    </label>
                  }
                } @else {
                  <div class="exchange-settlement-banner settlement-even">
                    <div>
                      <span>Canje parejo 1 a 1:</span>
                      <strong style="font-size: 1.1rem; margin-left: 6px;">Bs 0.00</strong>
                    </div>
                    <span style="font-size: 0.76rem; color: #475569;">Valores equivalentes · Sin cobro ni reembolso</span>
                  </div>
                }

                @if (!exchangeQuoteFresh) {
                  <p role="alert" style="color: #991b1b; margin-top: 10px; font-size: 0.8rem;">
                    La cotización ha expirado o cambió la selección de prendas. Solicitá una nueva cotización antes de confirmar.
                  </p>
                }

                <div style="margin-top: 18px;">
                  <button class="button button-dark pos-submit" type="button" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; margin: 0;" [disabled]="exchangeBusy || !isOnline || (!exchangePendingRetry && !exchangeConfirmValid)" (click)="finalizeExchange()">
                    <span class="material-symbols-outlined">verified</span>
                    {{ exchangeBusy ? 'Registrando cambio en el servidor...' : (exchangePendingRetry ? 'Reintentar confirmación exacta' : 'Confirmar cambio de prenda online') }}
                  </button>
                </div>
              </div>
            }

            <!-- Comprobante de Cambio Confirmado (Atelier Receipt) -->
            @if (exchangeSuccess) {
              <div class="exchange-receipt-card" role="status">
                <div class="exchange-receipt-header">
                  <span class="material-symbols-outlined">check_circle</span>
                  <div>
                    <h4>Comprobante de Cambio Confirmado</h4>
                    <small style="color: #047857;">Operación procesada y asentada exitosamente en el servidor central</small>
                  </div>
                </div>

                <div class="exchange-receipt-details">
                  <div>
                    <span>Venta de origen</span>
                    <strong>{{ exchangeSuccess.order_number || exchangeSale?.order_number }}</strong>
                  </div>
                  <div>
                    <span>Estado del cambio</span>
                    <strong style="color: #047857;">{{ exchangeSuccess.status }}</strong>
                  </div>
                  <div>
                    <span>Recepción cuarentena</span>
                    <strong>
                      {{ exchangeSuccess.quarantine_status || 'PENDING' }}
                      @if (exchangeSuccess.quarantine_id) { (#{{ exchangeSuccess.quarantine_id }}) }
                    </strong>
                  </div>
                  <div>
                    <span>Condición física</span>
                    <strong>{{ exchangeSuccess.item_condition || exchangeItemCondition }}</strong>
                  </div>
                  <div>
                    <span>Valor devuelto</span>
                    <strong>Bs {{ exchangeSuccess.returned_value }}</strong>
                  </div>
                  <div>
                    <span>Valor entregado</span>
                    <strong>Bs {{ exchangeSuccess.delivered_value }}</strong>
                  </div>
                  @if (exchangeSuccess.difference !== undefined) {
                    <div>
                      <span>Diferencia liquidada</span>
                      <strong>Bs {{ exchangeSuccess.difference }}</strong>
                    </div>
                  }
                  @if (exchangeSuccess.cash_tendered) {
                    <div>
                      <span>Efectivo cobrado</span>
                      <strong>Bs {{ exchangeSuccess.cash_tendered }} (Cambio: Bs {{ exchangeSuccess.cash_change || '0.00' }})</strong>
                    </div>
                  }
                  @if (exchangeSuccess.cash_refunded) {
                    <div>
                      <span>Efectivo reembolsado</span>
                      <strong>Bs {{ exchangeSuccess.cash_refunded }}</strong>
                    </div>
                  }
                </div>

                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 10px 14px; font-size: 0.78rem; color: #166534; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                  <span>
                    <strong>Protocolo de cuarentena:</strong> La prenda recibida ha sido asignada a cuarentena con estado PENDING para revisión física del encargado antes de retornar a stock comercial.
                  </span>
                  <button type="button" class="button button-dark" style="font-size: 0.78rem; padding: 6px 14px;" (click)="resetExchangeFlow()">
                    Realizar nuevo cambio
                  </button>
                </div>
              </div>
            }
          </div>

          <aside class="pos-summary">
            <span class="panel-index">CONTROL ONLINE</span>
            <h3>Reglas de cambio</h3>
            <p>Los cambios de prendas se procesan en línea con validación de política, inspección física y registro en cuarentena.</p>

            <div class="pos-summary-row">
              <span>Conexión al servidor</span>
              <strong>{{ isOnline ? 'Online · Conectado' : 'Offline' }}</strong>
            </div>

            @if (exchangeSale) {
              <div class="pos-summary-row">
                <span>Comprobante analizado</span>
                <strong>{{ exchangeSale.order_number }}</strong>
              </div>
              <div class="pos-summary-row">
                <span>Política de tienda</span>
                <strong>{{ exchangeSale.store_policy_days || 30 }} días generales</strong>
              </div>
              <div class="pos-summary-row">
                <span>Días transcurridos</span>
                <strong>{{ exchangeSale.days_elapsed || 0 }} días</strong>
              </div>
            }

            <div class="pos-summary-row">
              <span>Inspección física</span>
              <strong>{{ exchangeItemCondition }}</strong>
            </div>

            @if (exchangeQuote) {
              <div class="pos-summary-row">
                <span>Diferencia financiera</span>
                <strong>{{ exchangeDifferenceLabel }}</strong>
              </div>
            }

            @if (exchangeSuccess) {
              <div class="pos-summary-row">
                <span>Último cambio</span>
                <strong style="color: #8fc19e;">{{ exchangeSuccess.status }}</strong>
              </div>
              <div class="pos-summary-row">
                <span>Registro cuarentena</span>
                <strong>#{{ exchangeSuccess.quarantine_id || '-' }} ({{ exchangeSuccess.quarantine_status || 'PENDING' }})</strong>
              </div>
            }

            <div class="pos-summary-note">
              <span class="material-symbols-outlined">verified_user</span>
              <small>La prenda devuelta ingresa al inventario en estado de cuarentena (<code>PENDING</code>). No se suma al stock vendible hasta su inspección definitiva.</small>
            </div>
          </aside>
        </div>
      } @else if (mode === 'RETURN') {
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div><span class="panel-index">GESTIÓN DE DEVOLUCIÓN</span><h3>Reingreso de prendas a inventario</h3></div>
              <span class="material-symbols-outlined">published_with_changes</span>
            </div>
            <p style="margin: 0 0 16px; font-size: 0.85rem; color: var(--muted);">
              Buscá el comprobante online. Seleccioná cantidades, condición y beneficiario; las devoluciones nunca se encolan offline.
            </p>
            <div class="pos-form-grid">
              <label>
                <span>Número de orden o recibo</span>
                <small>Consulta online las líneas y cantidades restantes</small>
                <input [(ngModel)]="returnOrderNumber" (blur)="returnLookupTouched = true" [disabled]="!!returnPendingRetry" placeholder="Ej. FS-20261107-AB12" aria-label="Número de orden o recibo">
                <button type="button" class="small-button" [disabled]="returnBusy || !isOnline || !!returnPendingRetry || !returnOrderNumber.trim()" (click)="lookupReturn()">{{ returnBusy ? 'Buscando...' : 'Buscar devolución' }}</button>
              </label>
              <label class="full" style="grid-column: 1 / -1;">
                <span>Motivo de la devolución</span>
                <small>Razón detallada para la bitácora y auditoría</small>
                <input [(ngModel)]="returnReason" (ngModelChange)="message = ''" placeholder="Ej. Talla incorrecta o cambio solicitado por el cliente">
              </label>
            </div>
            @if (!isOnline) { <p class="pos-feedback pos-feedback-error" role="alert">La devolución requiere conexión online. No se puede consultar ni enviar offline.</p> }
            @if (returnSale) { <div style="margin: 10px 0 16px; overflow-x:auto;"><strong>Venta {{ returnSale.order_number }}</strong><table style="width:100%;"><thead><tr><th>Artículo</th><th>Restantes</th><th>Cantidad</th><th>Condición</th></tr></thead><tbody>@for (item of returnSale.items; track item.id) { <tr><td>{{ item.name }} · {{ item.sku }}</td><td>{{ item.remaining_returnable_quantity }}</td><td><input type="number" min="0" [max]="item.remaining_returnable_quantity" [disabled]="!!returnPendingRetry" [ngModel]="returnItems[item.id]?.quantity || 0" (ngModelChange)="setReturnQuantity(item.id, $event)"></td><td><select [disabled]="!!returnPendingRetry || !returnItems[item.id]?.quantity" [ngModel]="returnItems[item.id]?.condition || 'SELLABLE'" (ngModelChange)="setReturnCondition(item.id, $event)"><option value="SELLABLE">SELLABLE</option><option value="DAMAGED">DAMAGED</option></select></td></tr> }</tbody></table></div>
            }
            <div style="margin: 10px 0 16px;">
              <small style="color: var(--muted); display: block; margin-bottom: 6px; font-weight: 600;">Beneficiario y motivo de la devolución:</small>
                @if (returnSale?.customer_id === null) { <input [(ngModel)]="returnCustomerQuery" (ngModelChange)="searchReturnCustomers()" placeholder="Buscar cliente beneficiario"><select [(ngModel)]="returnBeneficiaryCustomerId"><option [ngValue]="null">Seleccioná un cliente</option>@for (customer of returnCustomers; track customer.id) { <option [ngValue]="customer.id">{{ customer.name }}{{ customer.email ? ' · ' + customer.email : '' }}</option> }</select> }
                @if (returnPendingRetry) { <p class="pos-feedback" role="alert">Respuesta incierta: se congeló la selección. Reintentá exactamente la misma solicitud.</p> }
            </div>
            <button class="button button-dark pos-submit" type="button" [disabled]="busy || !returnValid" (click)="processReturn()">
              <span class="material-symbols-outlined">undo</span>
              {{ busy ? 'Procesando devolución...' : (returnPendingRetry ? 'Reintentar devolución exacta' : 'Confirmar devolución') }}
              <span class="material-symbols-outlined pos-submit-arrow">arrow_forward</span>
            </button>
            @if (returnSuccess) { <div class="pos-feedback" role="status"><strong>Nota de crédito {{ returnSuccess.credit_note_code }}</strong><br>Importe: Bs {{ returnSuccess.credit_note_amount }}. Solo SELLABLE vuelve a stock; DAMAGED queda como RETURN sin stock disponible.</div> }
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
      } @else if (mode === 'LABELS') {
        <!-- =====================================================================
             CU-28: GENERAR E IMPRIMIR ETIQUETAS COLGANTES CON CÓDIGO DE BARRAS
             ===================================================================== -->
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div>
                <span class="panel-index">IDENTIFICACIÓN FÍSICA DE PRENDAS</span>
                <h3>Generador e Impresión de Etiquetas Colgantes (Hangtags)</h3>
              </div>
              <span class="material-symbols-outlined">sell</span>
            </div>

            <p style="margin: 0 0 16px; font-size: 0.84rem; color: var(--muted);">
              Selecciona las prendas del inventario de la sucursal para generar etiquetas colgantes con código de barras <code>Code-128</code>, código QR, talla, color y precio oficial listas para imprimir y escanear en caja.
            </p>

            <!-- Barra de Configuración de Formato de Etiqueta -->
            <div style="background: #fbf9f6; border: 1px solid #eae4d8; border-radius: 10px; padding: 14px 16px; margin-bottom: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
                <div>
                  <span style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #8f6d2d; display: block;">FORMATO Y OPCIONES DE IMPRESIÓN</span>
                  <strong style="font-size: 0.9rem; color: #1b1c1a;">Personalización de Etiqueta Atelier</strong>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                  <button type="button" class="small-button" style="background: #1b1c1a; color: #fff; font-size: 0.74rem; padding: 6px 12px;" (click)="loadDefaultLabelBatch()">
                    + Cargar Lote Sugerido (6 prendas)
                  </button>
                  <button type="button" class="small-button" style="background: #8f6d2d; color: #fff; font-size: 0.74rem; padding: 6px 12px;" (click)="syncLabelCopiesToStock()">
                    📦 Igualar Cantidad al Stock de Tienda
                  </button>
                  <button type="button" class="small-button" style="font-size: 0.74rem; padding: 6px 12px;" (click)="clearLabelBatch()">
                    Limpiar Lote
                  </button>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items: center;">
                <label style="margin: 0;">
                  <span style="font-size: 0.74rem; font-weight: 600;">Estilo de Etiqueta</span>
                  <select [(ngModel)]="labelFormat" style="padding: 7px 10px; font-size: 0.8rem;">
                    <option value="HANGTAG">Colgante Boutique Vertical (50×85 mm)</option>
                    <option value="THERMAL">Adhesivo Térmico Rollo (60×40 mm)</option>
                  </select>
                </label>

                <label style="margin: 0;">
                  <span style="font-size: 0.74rem; font-weight: 600;">Leyenda de Colección</span>
                  <input type="text" [(ngModel)]="labelCollectionTag" placeholder="Ej. Colección Otoño-Invierno" style="padding: 7px 10px; font-size: 0.8rem;" />
                </label>

                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 0.78rem; padding-top: 8px;">
                  <label style="display: flex; align-items: center; gap: 6px; margin: 0; cursor: pointer;">
                    <input type="checkbox" [(ngModel)]="labelShowPrice" />
                    <span>Imprimir precio público (Bs)</span>
                  </label>
                  <label style="display: flex; align-items: center; gap: 6px; margin: 0; cursor: pointer;">
                    <input type="checkbox" [(ngModel)]="labelShowQr" />
                    <span>Incluir mini QR de trazabilidad</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Selector de Prendas del Inventario para añadir al Lote -->
            <div style="margin-bottom: 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap;">
                <strong style="font-size: 0.84rem; color: #1b1c1a;">Catálogo de Sucursal ({{ selectedBranchName }})</strong>
                <input
                  type="text"
                  [(ngModel)]="labelSearchTerm"
                  placeholder="Filtrar por nombre, SKU, talla o color..."
                  style="max-width: 280px; padding: 6px 10px; font-size: 0.78rem; border: 1px solid #d6d3d1; border-radius: 6px;"
                />
              </div>

              <div style="max-height: 220px; overflow-y: auto; border: 1px solid #eae4d8; border-radius: 8px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.78rem;">
                  <thead>
                    <tr style="background: #fbf9f6; border-bottom: 1px solid #eae4d8; text-align: left;">
                      <th style="padding: 8px 10px;">Prenda</th>
                      <th style="padding: 8px 10px;">SKU</th>
                      <th style="padding: 8px 10px;">Talla / Color</th>
                      <th style="padding: 8px 10px; text-align: right;">Precio</th>
                      <th style="padding: 8px 10px; text-align: center;">Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (item of filteredLabelInventory; track item.product_variant_id) {
                      <tr style="border-bottom: 1px solid #f4f1ea;">
                        <td style="padding: 7px 10px; font-weight: 600;">{{ item.product_name }}</td>
                        <td style="padding: 7px 10px; font-family: monospace; font-size: 0.74rem;">{{ item.sku }}</td>
                        <td style="padding: 7px 10px;">{{ item.size_name }} · {{ item.color_name }}</td>
                        <td style="padding: 7px 10px; text-align: right; font-weight: 700;">Bs {{ getVariantPrice(item).toFixed(2) }}</td>
                        <td style="padding: 7px 10px; text-align: center;">
                          <button type="button" class="small-button" style="padding: 4px 10px; font-size: 0.72rem; background: #1b1c1a; color: #fff;" (click)="addVariantToLabelBatch(item)">
                            + Añadir Etiqueta
                          </button>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Planilla / Vista Previa de Etiquetas Colgantes -->
            <div style="background: #fbf9f6; border: 1px solid #eae4d8; border-radius: 12px; padding: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #eae4d8;">
                <div>
                  <span style="font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #8f6d2d; display: block;">VISTA PREVIA DE IMPRESIÓN</span>
                  <strong style="font-size: 0.95rem; color: #1b1c1a;">Planilla de Etiquetas ({{ totalLabelCopies }} etiquetas de {{ labelBatch.length }} variantes)</strong>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                  <button type="button" class="button button-dark" style="padding: 8px 16px; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 6px;" [disabled]="labelBatch.length === 0" (click)="showLabelSheetModal = true">
                    <span class="material-symbols-outlined" style="font-size: 17px;">print</span>
                    Vista Imprimible / Descargar PDF
                  </button>
                </div>
              </div>

              @if (labelBatch.length === 0) {
                <p style="text-align: center; color: var(--muted); font-size: 0.82rem; padding: 24px 0; margin: 0;">
                  No hay etiquetas en el lote actual. Pulsa "+ Añadir Etiqueta" o "Cargar Lote Sugerido".
                </p>
              } @else {
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(195px, 1fr)); gap: 14px;">
                  @for (tag of labelBatch; track tag.variant_id) {
                    <div class="editorial-hangtag-card" style="background: #ffffff; border: 1.5px solid #d8d0c2; border-radius: 12px; padding: 12px 14px 14px; position: relative; box-shadow: 0 4px 12px rgba(20, 19, 18, 0.05); display: flex; flex-direction: column; justify-content: space-between; gap: 8px;">
                      <!-- Perforación de Etiqueta Colgante (Hangtag Hole) -->
                      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #e5e0d8; padding-bottom: 8px;">
                        <span style="font-size: 0.62rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; color: #8f6d2d;">FASHIONSTORE</span>
                        <span style="width: 12px; height: 12px; border-radius: 50%; background: #f4f1ea; border: 2px solid #8f6d2d; display: inline-block;" title="Ojal de etiqueta colgante"></span>
                        <span style="font-size: 0.62rem; font-weight: 700; color: #6c6a64;">{{ labelCollectionTag }}</span>
                      </div>

                      <!-- Datos de Prenda, Talla y Color -->
                      <div>
                        <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 0.92rem; color: #1b1c1a; display: block; line-height: 1.25; margin-bottom: 4px;">
                          {{ tag.product_name }}
                        </strong>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                          <span style="font-size: 0.68rem; font-weight: 700; background: #1b1c1a; color: #fff; padding: 2px 7px; border-radius: 4px;">
                            TALLA {{ tag.size_name }}
                          </span>
                          <span style="font-size: 0.68rem; font-weight: 600; background: #f4f1ea; color: #52504b; padding: 2px 7px; border-radius: 4px; border: 1px solid #e2dcd0;">
                            {{ tag.color_name }}
                          </span>
                        </div>
                      </div>

                      <!-- Código de Barras Vectorial Code-128 + Mini QR -->
                      <div style="background: #ffffff; border: 1px solid #eae4d8; border-radius: 6px; padding: 6px; display: flex; align-items: center; gap: 6px;">
                        <div style="flex: 1; text-align: center;">
                          <svg viewBox="0 0 180 36" style="width: 100%; height: 34px; display: block;">
                            @for (bar of getBarcodeBars(tag.sku); track $index) {
                              @if (bar.dark) {
                                <rect [attr.x]="bar.x" y="0" [attr.width]="bar.w" height="25" fill="#111827"></rect>
                              }
                            }
                            <text x="90" y="34" text-anchor="middle" fill="#111827" font-size="8" font-family="monospace" font-weight="bold">{{ tag.sku }}</text>
                          </svg>
                        </div>
                        @if (labelShowQr) {
                          <div style="width: 52px; height: 52px; border: 1px solid #d6d3d1; border-radius: 4px; padding: 2px; flex-shrink: 0; background: #fff; text-align: center;">
                            <img [src]="'/api/v1/barcode-svg?text=' + encodeURIComponent(tag.sku) + '&format=qr'" style="width: 100%; height: 100%; object-fit: contain; display: block;" [alt]="'QR ' + tag.sku">
                          </div>
                        }
                      </div>

                      <!-- Pie de Etiqueta: Precio y Control de Copias -->
                      <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 6px; border-top: 1px solid #f2eee7;">
                        @if (labelShowPrice) {
                          <div>
                            <span style="font-size: 0.6rem; color: #6c6a64; display: block; text-transform: uppercase; font-weight: 700;">PRECIO</span>
                            <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.05rem; color: #1b1c1a;">Bs {{ tag.unit_price.toFixed(2) }}</strong>
                          </div>
                        } @else {
                          <span style="font-size: 0.7rem; color: #6c6a64;">Sin precio visible</span>
                        }

                        <div style="display: flex; align-items: center; gap: 4px;">
                          <button type="button" class="small-button" style="padding: 2px 7px; font-size: 0.72rem;" (click)="updateLabelCopies(tag.variant_id, -1)">-</button>
                          <input
                            type="number"
                            min="1"
                            max="100"
                            [(ngModel)]="tag.copies"
                            (change)="onLabelCopiesInputChange(tag)"
                            style="width: 44px; padding: 2px 4px; font-size: 0.76rem; font-weight: 700; text-align: center; border: 1px solid #d8d0c2; border-radius: 4px;"
                            title="Escribe la cantidad exacta de etiquetas a imprimir para esta prenda"
                          />
                          <button type="button" class="small-button" style="padding: 2px 7px; font-size: 0.72rem;" (click)="updateLabelCopies(tag.variant_id, 1)">+</button>
                        </div>
                      </div>

                      <button type="button" class="small-button" style="width: 100%; font-size: 0.71rem; padding: 4px 8px; background: #f4f1ea; color: #1b1c1a; border: 1px solid #d8d0c2;" (click)="scanFromLabelToPos(tag.sku)">
                        Probar lectura en Caja POS →
                      </button>
                    </div>
                  }
                </div>
              }
            </div>
          </div>

          <aside class="pos-summary">
            <span class="panel-index">RESUMEN DE ETIQUETADO</span>
            <h3>Control de Impresión</h3>
            <p>Genera etiquetas físicas estandarizadas para prendas nuevas o reingresadas de cuarentena.</p>

            <div class="pos-summary-row">
              <span>Sucursal activa</span>
              <strong>{{ selectedBranchName }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Formato seleccionado</span>
              <strong>{{ labelFormat === 'HANGTAG' ? 'Colgante 50×85mm' : 'Térmico 60×40mm' }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Variantes en lote</span>
              <strong>{{ labelBatch.length }} prendas</strong>
            </div>
            <div class="pos-summary-row">
              <span>Total etiquetas a imprimir</span>
              <strong style="color: #fde68a; font-size: 1.05rem;">{{ totalLabelCopies }} etiquetas</strong>
            </div>
            <div class="pos-summary-row">
              <span>Simbología</span>
              <strong>Code-128 + QR ISO</strong>
            </div>

            <div style="margin-top: 14px;">
              <button type="button" class="button button-light" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 6px; font-size: 0.82rem; background: #8f6d2d; color: #fff; border: none;" [disabled]="labelBatch.length === 0" (click)="showLabelSheetModal = true">
                <span class="material-symbols-outlined" style="font-size: 18px;">print</span>
                Abrir Planilla Imprimible
              </button>
            </div>

            <div class="pos-summary-note" style="margin-top: 14px;">
              <span class="material-symbols-outlined">verified</span>
              <small>Cada etiqueta impresa contiene el SKU único compatible con lectores láser USB y con el Punto de Venta.</small>
            </div>
          </aside>
        </div>
      } @else if (mode === 'CASH_CLOSE') {
        <!-- =====================================================================
             CU-29: ARQUEO Y CIERRE DE CAJA POR TURNO (REPORTE Z IMPRIMIBLE)
             ===================================================================== -->
        <div class="pos-layout">
          <div class="admin-panel pos-form-panel">
            <div class="pos-panel-heading">
              <div>
                <span class="panel-index">CONTROL FINANCIERO Y AUDITORÍA DE TURNO</span>
                <h3>Arqueo Físico y Cierre de Caja por Turno (Reporte Z)</h3>
              </div>
              <span class="material-symbols-outlined">account_balance_wallet</span>
            </div>

            <p style="margin: 0 0 16px; font-size: 0.84rem; color: var(--muted);">
              Realiza el conteo físico de billetes y monedas en gaveta, concilia las ventas por Efectivo, QR y Tarjeta junto con devoluciones del turno, y emite el Reporte Z oficial firmado.
            </p>

            <!-- Franja de 4 KPIs Financieros del Turno -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; background: #fbf9f6; border: 1px solid #eae4d8; border-radius: 10px; padding: 14px 16px; margin-bottom: 16px;">
              <div style="border-right: 1px solid #eae4d8; padding-right: 10px;">
                <span style="font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6c6a64; display: block;">FONDO DE APERTURA</span>
                <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.15rem; color: #1b1c1a;">Bs {{ cashCloseOpeningFloat.toFixed(2) }}</strong>
                <small style="display: block; font-size: 0.68rem; color: #8f6d2d; font-weight: 600;">Efectivo inicial en caja</small>
              </div>
              <div style="border-right: 1px solid #eae4d8; padding-right: 10px;">
                <span style="font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6c6a64; display: block;">VENTAS EN EFECTIVO</span>
                <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.15rem; color: #1b1c1a;">Bs {{ cashCloseCashSales.toFixed(2) }}</strong>
                <small style="display: block; font-size: 0.68rem; color: #2e6f40; font-weight: 600;">+Bs {{ cashCloseExchangeIn.toFixed(2) }} cambios</small>
              </div>
              <div style="border-right: 1px solid #eae4d8; padding-right: 10px;">
                <span style="font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6c6a64; display: block;">COBROS QR + TARJETA</span>
                <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.15rem; color: #1b1c1a;">Bs {{ (cashCloseQrSales + cashCloseCardSales).toFixed(2) }}</strong>
                <small style="display: block; font-size: 0.68rem; color: #6c6a64;">QR: Bs {{ cashCloseQrSales.toFixed(0) }} · Tarj: Bs {{ cashCloseCardSales.toFixed(0) }}</small>
              </div>
              <div>
                <span style="font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #8f6d2d; display: block;">EFECTIVO ESPERADO</span>
                <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.2rem; color: #1b1c1a;">Bs {{ expectedCashInDrawer.toFixed(2) }}</strong>
                <small style="display: block; font-size: 0.68rem; color: #8d4d38; font-weight: 600;">-Bs {{ cashCloseRefundsOut.toFixed(2) }} reembolsos</small>
              </div>
            </div>

            <!-- Parámetros del Turno y Conciliación del Sistema -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
              <div style="background: #ffffff; border: 1px solid #eae4d8; border-radius: 10px; padding: 14px 16px;">
                <span style="font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #8f6d2d; display: block; margin-bottom: 8px;">1 · DATOS DEL TURNO Y CAJA</span>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                  <label style="margin: 0;">
                    <span style="font-size: 0.74rem; font-weight: 600;">Turno de Trabajo</span>
                    <select [(ngModel)]="cashCloseShiftLabel" style="padding: 7px 10px; font-size: 0.8rem;">
                      <option value="Turno Mañana (08:00 - 16:00)">Turno Mañana (08:00 - 16:00)</option>
                      <option value="Turno Tarde/Noche (16:00 - 22:00)">Turno Tarde/Noche (16:00 - 22:00)</option>
                      <option value="Jornada Completa (09:00 - 21:00)">Jornada Completa (09:00 - 21:00)</option>
                    </select>
                  </label>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <label style="margin: 0;">
                      <span style="font-size: 0.74rem; font-weight: 600;">Fondo Fijo Inicial (Bs)</span>
                      <input type="number" min="0" step="10" [(ngModel)]="cashCloseOpeningFloat" style="padding: 7px 10px; font-size: 0.82rem;" />
                    </label>
                    <label style="margin: 0;">
                      <span style="font-size: 0.74rem; font-weight: 600;">Reembolsos Efectivo (Bs)</span>
                      <input type="number" min="0" step="10" [(ngModel)]="cashCloseRefundsOut" style="padding: 7px 10px; font-size: 0.82rem;" />
                    </label>
                  </div>
                  <label style="margin: 0;">
                    <span style="font-size: 0.74rem; font-weight: 600;">Observaciones de Cierre / Novedades</span>
                    <input type="text" [(ngModel)]="cashCloseNotes" placeholder="Ej. Sin novedades, arqueo verificado con supervisor de tienda" style="padding: 7px 10px; font-size: 0.8rem;" />
                  </label>
                </div>
              </div>

              <!-- Conteo Físico de Billetes y Monedas (Arqueo Ciego) -->
              <div style="background: #ffffff; border: 1px solid #eae4d8; border-radius: 10px; padding: 14px 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span style="font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #8f6d2d;">2 · ARQUEO FÍSICO DE BILLETES Y MONEDAS</span>
                  <button type="button" class="small-button" style="font-size: 0.7rem; padding: 3px 8px; background: #f4f1ea; color: #1b1c1a; border: 1px solid #d8d0c2;" (click)="autoFillExactCashCount()">
                    Autocompletar Cuadre Exacto
                  </button>
                </div>

                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
                  @for (denom of cashDenominations; track denom.value) {
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 6px; background: #fbf9f6; border: 1px solid #eae4d8; border-radius: 6px; padding: 5px 8px;">
                      <span style="font-size: 0.74rem; font-weight: 700; color: #1b1c1a; min-width: 58px;">{{ denom.label }}</span>
                      <input
                        type="number"
                        min="0"
                        [(ngModel)]="denom.count"
                        style="width: 56px; padding: 4px 6px; font-size: 0.78rem; text-align: center; border: 1px solid #d6d3d1; border-radius: 4px;"
                        [attr.aria-label]="'Cantidad de ' + denom.label"
                      />
                      <span style="font-size: 0.74rem; font-weight: 700; color: #6c6a64; min-width: 62px; text-align: right;">
                        Bs {{ (denom.value * (denom.count || 0)).toFixed(0) }}
                      </span>
                    </div>
                  }
                </div>
              </div>
            </div>

            <!-- Banner de Resultado de Conciliación (Cuadre Exacto / Sobrante / Faltante) -->
            <div
              style="border-radius: 10px; padding: 14px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; border: 1.5px solid;"
              [style.background]="cashCloseDiscrepancy === 0 ? '#e7f3eb' : (cashCloseDiscrepancy > 0 ? '#fdf3e1' : '#fae8e8')"
              [style.borderColor]="cashCloseDiscrepancy === 0 ? '#2e6f40' : (cashCloseDiscrepancy > 0 ? '#b8924a' : '#9e2a2b')"
              [style.color]="cashCloseDiscrepancy === 0 ? '#1b4326' : (cashCloseDiscrepancy > 0 ? '#784f10' : '#7f1d1d')"
            >
              <div>
                <span style="font-size: 0.66rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; display: block;">
                  ESTADO DE CONCILIACIÓN DE GAVETA
                </span>
                <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.15rem;">
                  @if (cashCloseDiscrepancy === 0) {
                    ✓ Cuadre Exacto de Caja (Sin Diferencias)
                  } @else if (cashCloseDiscrepancy > 0) {
                    ▲ Sobrante de Efectivo en Gaveta (+Bs {{ cashCloseDiscrepancy.toFixed(2) }})
                  } @else {
                    ▼ Faltante de Efectivo en Gaveta (Bs {{ cashCloseDiscrepancy.toFixed(2) }})
                  }
                </strong>
              </div>
              <div style="display: flex; gap: 18px; align-items: baseline;">
                <div style="text-align: right;">
                  <span style="font-size: 0.66rem; text-transform: uppercase; font-weight: 700; display: block;">Efectivo Contado</span>
                  <strong style="font-size: 1.1rem;">Bs {{ countedCashInDrawer.toFixed(2) }}</strong>
                </div>
                <div style="text-align: right;">
                  <span style="font-size: 0.66rem; text-transform: uppercase; font-weight: 700; display: block;">Efectivo Esperado</span>
                  <strong style="font-size: 1.1rem;">Bs {{ expectedCashInDrawer.toFixed(2) }}</strong>
                </div>
              </div>
            </div>

            <button type="button" class="button button-dark pos-submit" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 8px;" (click)="submitCashCloseReport()">
              <span class="material-symbols-outlined">lock_clock</span>
              Cerrar Turno Oficialmente y Emitir Reporte Z Imprimible
            </button>

            <!-- Historial de Cierres de Caja (Reportes Z) -->
            @if (cashCloseHistory.length > 0) {
              <div style="margin-top: 20px; border-top: 1px solid #eae4d8; padding-top: 14px;">
                <strong style="font-size: 0.84rem; color: #1b1c1a; display: block; margin-bottom: 8px;">Historial de Cierres de Turno en Sucursal (Reportes Z)</strong>
                <div style="border: 1px solid #eae4d8; border-radius: 8px; overflow: hidden;">
                  <table style="width: 100%; border-collapse: collapse; font-size: 0.76rem;">
                    <thead>
                      <tr style="background: #fbf9f6; border-bottom: 1px solid #eae4d8; text-align: left;">
                        <th style="padding: 7px 10px;">Folio Z</th>
                        <th style="padding: 7px 10px;">Fecha / Turno</th>
                        <th style="padding: 7px 10px; text-align: right;">Esperado</th>
                        <th style="padding: 7px 10px; text-align: right;">Contado</th>
                        <th style="padding: 7px 10px; text-align: center;">Estado</th>
                        <th style="padding: 7px 10px; text-align: center;">Comprobante</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (rep of cashCloseHistory; track rep.report_code) {
                        <tr style="border-bottom: 1px solid #f4f1ea;">
                          <td style="padding: 7px 10px; font-family: monospace; font-weight: 700;">{{ rep.report_code }}</td>
                          <td style="padding: 7px 10px;">{{ rep.closed_at | date:'dd/MM HH:mm' }} · {{ rep.shift_label }}</td>
                          <td style="padding: 7px 10px; text-align: right;">Bs {{ rep.expected_cash_in_drawer.toFixed(2) }}</td>
                          <td style="padding: 7px 10px; text-align: right; font-weight: 700;">Bs {{ rep.counted_cash_in_drawer.toFixed(2) }}</td>
                          <td style="padding: 7px 10px; text-align: center;">
                            <span
                              style="font-size: 0.66rem; font-weight: 700; padding: 2px 7px; border-radius: 999px;"
                              [style.background]="rep.status === 'EXACT' ? '#e7f3eb' : (rep.status === 'SURPLUS' ? '#fdf3e1' : '#fae8e8')"
                              [style.color]="rep.status === 'EXACT' ? '#2e6f40' : (rep.status === 'SURPLUS' ? '#9c6615' : '#9e2a2b')"
                            >
                              {{ rep.status === 'EXACT' ? 'CUADRE EXACTO' : (rep.status === 'SURPLUS' ? 'SOBRANTE' : 'FALTANTE') }}
                            </span>
                          </td>
                          <td style="padding: 7px 10px; text-align: center;">
                            <button type="button" class="small-button" style="padding: 3px 9px; font-size: 0.7rem;" (click)="viewZReport(rep)">
                              Ver / Imprimir Z
                            </button>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </div>
            }
          </div>

          <aside class="pos-summary">
            <span class="panel-index">REPORTE Z DE CAJA</span>
            <h3>Resumen de Cierre</h3>
            <p>Consolida todos los cobros presenciales y movimientos de efectivo antes del relevo de turno.</p>

            <div class="pos-summary-row">
              <span>Sucursal</span>
              <strong>{{ selectedBranchName }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Total Facturado Turno</span>
              <strong>Bs {{ (cashCloseCashSales + cashCloseQrSales + cashCloseCardSales).toFixed(2) }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Efectivo Esperado</span>
              <strong>Bs {{ expectedCashInDrawer.toFixed(2) }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Efectivo Físico Contado</span>
              <strong style="color: #fde68a;">Bs {{ countedCashInDrawer.toFixed(2) }}</strong>
            </div>
            <div class="pos-summary-row">
              <span>Diferencia de Arqueo</span>
              <strong>{{ cashCloseDiscrepancy >= 0 ? '+' : '' }}Bs {{ cashCloseDiscrepancy.toFixed(2) }}</strong>
            </div>

            @if (activeZReport) {
              <div style="margin-top: 14px;">
                <button type="button" class="button button-light" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 6px; font-size: 0.82rem; background: #2e6f40; color: #fff; border: none;" (click)="showZReportModal = true">
                  <span class="material-symbols-outlined" style="font-size: 18px;">print</span>
                  Ver / Imprimir Reporte Z ({{ activeZReport.report_code }})
                </button>
              </div>
            }

            <div class="pos-summary-note" style="margin-top: 14px;">
              <span class="material-symbols-outlined">verified_user</span>
              <small>El Reporte Z deja constancia auditada de los billetes declarados, ventas por canal y firmas de conformidad.</small>
            </div>
          </aside>
        </div>
      }

      <!-- MODAL IMPRIMIBLE DE PLANILLA DE ETIQUETAS COLGANTES -->
      @if (showLabelSheetModal) {
        <div role="dialog" aria-modal="true" aria-label="Planilla Imprimible de Etiquetas Colgantes" style="position: fixed; inset: 0; background: rgba(17, 24, 39, 0.72); z-index: 9999; display: flex; justify-content: center; align-items: center; padding: 16px; overflow-y: auto;">
          <div style="background: #ffffff; color: #1b1c1a; width: 100%; max-width: 780px; border-radius: 12px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45); overflow: hidden; border: 1px solid #d8d0c2;">
            <div style="background: #1b1c1a; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="material-symbols-outlined" style="color: #d4b26f;">sell</span>
                <strong style="font-size: 0.92rem;">Planilla Oficial de Etiquetas Colgantes con Código de Barras ({{ totalLabelCopies }} etiquetas)</strong>
              </div>
              <button type="button" style="background: none; border: none; color: #fff; font-size: 1.25rem; cursor: pointer;" (click)="showLabelSheetModal = false">×</button>
            </div>

            <div style="padding: 20px 24px; max-height: 72vh; overflow-y: auto; background: #fbf9f6;">
              <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
                @for (tag of expandedLabelSheet; track $index) {
                  <div style="background: #ffffff; border: 1.5px dashed #8f6d2d; border-radius: 10px; padding: 12px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; gap: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.6rem; font-weight: 800; color: #8f6d2d; letter-spacing: 0.1em;">
                      <span>FASHIONSTORE</span>
                      <span style="width: 10px; height: 10px; border-radius: 50%; border: 1.5px solid #8f6d2d; display: inline-block;"></span>
                      <span>{{ selectedBranchName }}</span>
                    </div>
                    <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 0.85rem; color: #1b1c1a;">{{ tag.product_name }}</strong>
                    <div style="font-size: 0.68rem; font-weight: 700; color: #52504b;">
                      TALLA: {{ tag.size_name }} · COLOR: {{ tag.color_name }}
                    </div>
                    <div style="background: #fff; padding: 4px; border: 1px solid #eae4d8; border-radius: 4px;">
                      <svg viewBox="0 0 180 34" style="width: 100%; height: 30px; display: block;">
                        @for (bar of getBarcodeBars(tag.sku); track $index) {
                          @if (bar.dark) {
                            <rect [attr.x]="bar.x" y="0" [attr.width]="bar.w" height="23" fill="#111827"></rect>
                          }
                        }
                        <text x="90" y="32" text-anchor="middle" fill="#111827" font-size="7.5" font-family="monospace" font-weight="bold">{{ tag.sku }}</text>
                      </svg>
                    </div>
                    @if (labelShowPrice) {
                      <strong style="font-family: 'Playfair Display', Georgia, serif; font-size: 1rem; color: #1b1c1a;">Bs {{ tag.unit_price.toFixed(2) }}</strong>
                    }
                  </div>
                }
              </div>
            </div>

            <div style="background: #f4f1ea; padding: 12px 20px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #e2dcd0;">
              <button type="button" class="small-button" style="padding: 8px 14px;" (click)="showLabelSheetModal = false">Cerrar</button>
              <button type="button" class="button button-dark" style="padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px;" (click)="printInvoice()">
                <span class="material-symbols-outlined" style="font-size: 18px;">print</span>
                Imprimir Planilla de Etiquetas / Guardar PDF
              </button>
            </div>
          </div>
        </div>
      }

      <!-- MODAL IMPRIMIBLE DEL REPORTE Z DE CIERRE DE CAJA -->
      @if (showZReportModal && activeZReport) {
        <div role="dialog" aria-modal="true" aria-label="Reporte Z de Cierre de Caja" style="position: fixed; inset: 0; background: rgba(17, 24, 39, 0.72); z-index: 9999; display: flex; justify-content: center; align-items: center; padding: 16px; overflow-y: auto;">
          <div style="background: #fff; color: #111827; width: 100%; max-width: 540px; border-radius: 10px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45); overflow: hidden; border: 1px solid #d6d3d1;">
            <div style="background: #1b1c1a; color: #fff; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="material-symbols-outlined" style="color: #d4b26f;">fact_check</span>
                <strong style="font-size: 0.92rem;">Reporte Z de Arqueo y Cierre de Turno ({{ activeZReport.report_code }})</strong>
              </div>
              <button type="button" style="background: none; border: none; color: #fff; font-size: 1.2rem; cursor: pointer;" (click)="showZReportModal = false">×</button>
            </div>

            <div style="padding: 20px 24px; font-family: 'Courier New', Courier, monospace; font-size: 0.8rem; line-height: 1.45; color: #111827;">
              <div style="text-align: center; border-bottom: 1.5px dashed #111827; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="margin: 0; font-size: 1.1rem; font-weight: 900; text-transform: uppercase;">FASHIONSTORE · REPORTE Z DE CAJA</h3>
                <div style="font-weight: 700;">{{ activeZReport.branch_name }}</div>
                <div>FOLIO: {{ activeZReport.report_code }} · FECHA: {{ activeZReport.closed_at | date:'dd/MM/yyyy HH:mm' }}</div>
                <div>TURNO: {{ activeZReport.shift_label }}</div>
                <div>CAJERO(A): {{ activeZReport.cashier_name }}</div>
              </div>

              <div style="border-bottom: 1.5px dashed #111827; padding-bottom: 8px; margin-bottom: 10px;">
                <div style="font-weight: 700; margin-bottom: 4px;">1. RESUMEN DE VENTAS Y FLUJO DE CAJA</div>
                <div style="display: flex; justify-content: space-between;"><span>(+) Fondo Fijo de Apertura:</span><strong>Bs {{ activeZReport.opening_float.toFixed(2) }}</strong></div>
                <div style="display: flex; justify-content: space-between;"><span>(+) Ventas en Efectivo:</span><strong>Bs {{ activeZReport.cash_sales_total.toFixed(2) }}</strong></div>
                <div style="display: flex; justify-content: space-between;"><span>(+) Cobros por Cambio de Prenda:</span><strong>Bs {{ activeZReport.exchange_cash_in.toFixed(2) }}</strong></div>
                <div style="display: flex; justify-content: space-between;"><span>(-) Reembolsos / Devoluciones:</span><strong>-Bs {{ activeZReport.refunds_cash_out.toFixed(2) }}</strong></div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dotted #111827; margin-top: 4px; padding-top: 4px;">
                  <span>(=) EFECTIVO ESPERADO EN GAVETA:</span><strong>Bs {{ activeZReport.expected_cash_in_drawer.toFixed(2) }}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>(•) Ventas por QR Interbancario:</span><span>Bs {{ activeZReport.qr_sales_total.toFixed(2) }}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>(•) Ventas con Tarjeta (POS/Stripe):</span><span>Bs {{ activeZReport.card_sales_total.toFixed(2) }}</span></div>
              </div>

              <div style="border-bottom: 1.5px dashed #111827; padding-bottom: 8px; margin-bottom: 10px;">
                <div style="font-weight: 700; margin-bottom: 4px;">2. CONTEO FÍSICO DE BILLETES Y MONEDAS</div>
                @for (d of activeZReport.denominations; track d.label) {
                  @if (d.count > 0) {
                    <div style="display: flex; justify-content: space-between;">
                      <span>{{ d.label }} × {{ d.count }} ud.</span>
                      <span>Bs {{ d.subtotal.toFixed(2) }}</span>
                    </div>
                  }
                }
                <div style="display: flex; justify-content: space-between; border-top: 1px solid #111827; margin-top: 4px; padding-top: 4px; font-size: 0.88rem;">
                  <strong>EFECTIVO FÍSICO CONTADO:</strong>
                  <strong>Bs {{ activeZReport.counted_cash_in_drawer.toFixed(2) }}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 700;">
                  <span>DIFERENCIA DE ARQUEO:</span>
                  <span>{{ activeZReport.discrepancy >= 0 ? '+' : '' }}Bs {{ activeZReport.discrepancy.toFixed(2) }} ({{ activeZReport.status === 'EXACT' ? 'CUADRE EXACTO' : (activeZReport.status === 'SURPLUS' ? 'SOBRANTE' : 'FALTANTE') }})</span>
                </div>
              </div>

              @if (activeZReport.notes) {
                <div style="margin-bottom: 12px; font-size: 0.75rem;">
                  <strong>OBSERVACIONES:</strong> {{ activeZReport.notes }}
                </div>
              }

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 28px; text-align: center; font-size: 0.72rem;">
                <div style="border-top: 1px solid #111827; padding-top: 4px;">FIRMA CAJERO(A) RESPONSABLE</div>
                <div style="border-top: 1px solid #111827; padding-top: 4px;">CONFORMIDAD SUPERVISOR / ADMIN</div>
              </div>
            </div>

            <div style="background: #f5f5f4; padding: 12px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #e7e5e4;">
              <button type="button" class="small-button" style="padding: 8px 14px;" (click)="showZReportModal = false">Cerrar</button>
              <button type="button" class="button button-dark" style="padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px;" (click)="printInvoice()">
                <span class="material-symbols-outlined" style="font-size: 18px;">print</span>
                Imprimir Reporte Z / Guardar PDF
              </button>
            </div>
          </div>
        </div>
      }

      <!-- MODAL DE FACTURA COMERCIAL / COMPROBANTE DE VENTA IMPRIMIBLE -->
      @if (showInvoiceModal && lastInvoice) {
        <div role="dialog" aria-modal="true" aria-label="Factura Comercial de Venta" style="position: fixed; inset: 0; background: rgba(17, 24, 39, 0.72); z-index: 9999; display: flex; justify-content: center; align-items: center; padding: 16px; overflow-y: auto;">
          <div style="background: #fff; color: #111827; width: 100%; max-width: 520px; border-radius: 10px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45); overflow: hidden; border: 1px solid #d6d3d1;">
            <!-- Cabecera del Modal -->
            <div style="background: #1c1917; color: #fff; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="material-symbols-outlined" style="color: #10b981;">receipt_long</span>
                <strong style="font-size: 0.92rem;">{{ lastInvoice.is_offline ? 'Comprobante de Contingencia Offline' : 'Factura Comercial Emitida' }}</strong>
              </div>
              <button type="button" style="background: none; border: none; color: #fff; font-size: 1.2rem; cursor: pointer;" (click)="showInvoiceModal = false">×</button>
            </div>

            <!-- Cuerpo de la Factura (Formato Ticket / Factura Fiscal) -->
            <div id="printable-pos-invoice" style="padding: 20px 24px; font-family: 'Courier New', Courier, monospace; font-size: 0.82rem; line-height: 1.45; color: #111827;">
              <div style="text-align: center; border-bottom: 1.5px dashed #111827; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 900; letter-spacing: 0.04em; text-transform: uppercase;">{{ lastInvoice.tenant_name }}</h3>
                <div style="font-size: 0.78rem; font-weight: 700;">{{ lastInvoice.branch_name }}</div>
                <div style="font-size: 0.74rem;">NIT EMISOR: 1029485021 · FACTURA N° {{ lastInvoice.invoice_number }}</div>
                <div style="font-size: 0.72rem;">CÓD. CONTROL: {{ lastInvoice.control_code }}</div>
                @if (lastInvoice.is_offline) {
                  <div style="margin-top: 4px; background: #fef3c7; color: #92400e; padding: 2px 6px; font-size: 0.7rem; font-weight: 700; border-radius: 4px; display: inline-block;">
                    EMITIDO EN CONTINGENCIA OFFLINE · PENDIENTE DE SINCRONIZACIÓN
                  </div>
                }
              </div>

              <div style="border-bottom: 1.5px dashed #111827; padding-bottom: 8px; margin-bottom: 10px; font-size: 0.78rem;">
                <div><strong>FECHA Y HORA:</strong> {{ lastInvoice.issued_at | date:'dd/MM/yyyy HH:mm:ss' }}</div>
                <div><strong>NOMBRE / RAZÓN SOCIAL:</strong> {{ lastInvoice.customer_name }}</div>
                <div><strong>NIT / CI / CEX:</strong> {{ lastInvoice.customer_nit }}</div>
                @if (lastInvoice.customer_phone) {
                  <div><strong>TELÉFONO:</strong> {{ lastInvoice.customer_phone }}</div>
                }
                <div><strong>CAJERO(A):</strong> {{ lastInvoice.cashier_name }}</div>
                <div><strong>FORMA DE PAGO:</strong> {{ lastInvoice.payment_method }}</div>
              </div>

              <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 0.77rem;">
                <thead>
                  <tr style="border-bottom: 1px solid #111827; text-align: left;">
                    <th style="padding: 4px 0;">CANT</th>
                    <th style="padding: 4px;">DETALLE / SKU</th>
                    <th style="padding: 4px; text-align: right;">P.UNIT</th>
                    <th style="padding: 4px 0; text-align: right;">SUBTOTAL</th>
                  </tr>
                </thead>
                <tbody>
                  @for (item of lastInvoice.items; track $index) {
                    <tr style="border-bottom: 1px dotted #d6d3d1;">
                      <td style="padding: 5px 0; vertical-align: top; font-weight: 700;">{{ item.quantity }}</td>
                      <td style="padding: 5px 4px;">
                        <div style="font-weight: 700;">{{ item.description }}</div>
                        <div style="font-size: 0.7rem; color: #57534e;">SKU: {{ item.sku }}</div>
                      </td>
                      <td style="padding: 5px 4px; text-align: right; vertical-align: top;">{{ item.unit_price.toFixed(2) }}</td>
                      <td style="padding: 5px 0; text-align: right; vertical-align: top; font-weight: 700;">{{ item.subtotal.toFixed(2) }}</td>
                    </tr>
                  }
                </tbody>
              </table>

              <div style="border-top: 1.5px dashed #111827; padding-top: 8px; margin-bottom: 12px; font-size: 0.82rem;">
                <div style="display: flex; justify-content: space-between;">
                  <span>SUBTOTAL Bs:</span>
                  <strong>{{ lastInvoice.subtotal.toFixed(2) }}</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span>DESCUENTO Bs:</span>
                  <strong>{{ lastInvoice.discount.toFixed(2) }}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.96rem; margin-top: 4px; padding-top: 4px; border-top: 1px solid #111827;">
                  <strong>TOTAL A PAGAR Bs:</strong>
                  <strong>{{ lastInvoice.total.toFixed(2) }}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                  <span>IMPORTE RECIBIDO Bs:</span>
                  <span>{{ lastInvoice.amount_received.toFixed(2) }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 700;">
                  <span>CAMBIO DEVUELTO Bs:</span>
                  <span>{{ lastInvoice.change_returned.toFixed(2) }}</span>
                </div>
              </div>

              <!-- Código QR de Verificación Fiscal -->
              <div style="display: flex; align-items: center; gap: 12px; border-top: 1.5px dashed #111827; padding-top: 10px;">
                <div style="background: #fff; border: 1px solid #111827; padding: 4px; width: 78px; height: 78px; flex-shrink: 0;">
                  <svg viewBox="0 0 21 21" style="width: 100%; height: 100%; display: block;" aria-label="Código QR de la factura">
                    @for (cell of getInvoiceQrMatrix(lastInvoice.qr_payload); track $index) {
                      @if (cell.dark) {
                        <rect [attr.x]="cell.x" [attr.y]="cell.y" width="1" height="1" fill="#111827"></rect>
                      }
                    }
                  </svg>
                </div>
                <div style="font-size: 0.68rem; line-height: 1.35; color: #374151;">
                  <strong>ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS.</strong><br>
                  Ley N° 453: Tienes derecho a recibir información sobre las características y contenidos de los productos que consumes.<br>
                  <span style="font-family: monospace;">{{ lastInvoice.qr_payload }}</span>
                </div>
              </div>
            </div>

            <!-- Botones de Acción de la Factura -->
            <div style="background: #f5f5f4; padding: 12px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #e7e5e4;">
              <button type="button" class="small-button" style="padding: 8px 14px;" (click)="showInvoiceModal = false">
                Cerrar y Seguir Vendiendo
              </button>
              <button type="button" class="button button-dark" style="padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px;" (click)="printInvoice()">
                <span class="material-symbols-outlined" style="font-size: 18px;">print</span>
                Imprimir Factura / Guardar PDF
              </button>
            </div>
          </div>
        </div>
      }
    </section>
  `,
})
export class PosComponent implements OnInit, OnDestroy {
  @ViewChild('scannerVideo') scannerVideoRef?: ElementRef<HTMLVideoElement>;

  private readonly commerce = inject(CommerceService);
  private readonly auth = inject(AuthService);
  private readonly catalog = inject(CatalogService);
  private readonly admin = inject(AdminService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly offlineCatalog = inject(OfflineCatalogService);
  private readonly offlineTx = inject(OfflineTransactionService);
  readonly syncTx = inject(SyncTransactionService);
  readonly syncCatalog = inject(SyncCatalogService);

  mode: 'SALE' | 'CUSTOMERS' | 'RETURN' | 'EXCHANGE' | 'LABELS' | 'CASH_CLOSE' = 'SALE';

  // Control de Cajero y Turno Activo
  sessionStartTime = new Date();

  get activeCashierName(): string {
    const u = this.auth.currentUser();
    if (!u) return 'Cajero de Sucursal';
    const fullName = `${u.first_name || ''} ${u.last_name || ''}`.trim();
    return fullName || u.email || 'Cajero de Sucursal';
  }

  get activeCashierEmail(): string {
    return this.auth.currentUser()?.email || 'cajero@fashionstore.com';
  }

  get activeCashierRole(): string {
    const role = this.auth.currentUser()?.role;
    if (role === 'ADMIN') return 'Administrador / Supervisor';
    if (role === 'EMPLOYEE') return 'Cajero Titular';
    return role || 'Personal de Tienda';
  }

  getCashierInitials(): string {
    const parts = this.activeCashierName.split(' ').filter(Boolean);
    if (parts.length === 0) return 'CJ';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  // CU-28: Hangtag / Barcode Label Generator fields
  labelFormat: 'HANGTAG' | 'THERMAL' = 'HANGTAG';
  labelCollectionTag = 'Atelier Edition';
  labelShowPrice = true;
  labelShowQr = true;
  labelSearchTerm = '';
  labelBatch: PosLabelBatchItem[] = [];
  showLabelSheetModal = false;

  // CU-29: Cash Register Shift Close (Arqueo & Reporte Z) fields
  cashCloseShiftLabel = 'Turno Mañana (08:00 - 16:00)';
  cashCloseOpeningFloat = 500;
  cashCloseCashSales = 1840;
  cashCloseQrSales = 960;
  cashCloseCardSales = 650;
  cashCloseExchangeIn = 120;
  cashCloseRefundsOut = 80;
  cashCloseNotes = 'Arqueo verificado sin diferencias al cierre de turno.';
  cashDenominations: { label: string; value: number; count: number }[] = [
    { label: 'Bs 200', value: 200, count: 6 },
    { label: 'Bs 100', value: 100, count: 8 },
    { label: 'Bs 50', value: 50, count: 5 },
    { label: 'Bs 20', value: 20, count: 5 },
    { label: 'Bs 10', value: 10, count: 2 },
    { label: 'Monedas', value: 1, count: 10 },
  ];
  cashCloseHistory: PosCashCloseReport[] = [];
  activeZReport: PosCashCloseReport | null = null;
  showZReportModal = false;

  // Sale fields
  branchId = 0;
  variantId = 0;
  quantity = 1;
  amount = 0;
  paymentMethod: 'CASH' = 'CASH';
  transactionReference = '';
  lastTotal = 0;
  change = 0;

  // CU-27: Barcode Scanner, Multi-line Cart & Invoice fields
  barcodeQuery = '';
  itemFilterTerm = '';
  scannerFeedback = '';
  scannerFeedbackError = false;
  lastScannedItem: PosCartItem | null = null;
  cartItems: PosCartItem[] = [];
  showManualPicker = false;
  wantsInvoiceWithNit = false;
  showBarcodeSheet = false;
  showMobileGunPanel = false;
  remoteScannerListening = false;
  mobileSenderMode = false;
  cameraActive = false;
  cameraError = '';
  lastInvoice: PosInvoiceReceipt | null = null;
  showInvoiceModal = false;

  private cameraStream: MediaStream | null = null;
  private cameraScanTimer: ReturnType<typeof setInterval> | null = null;
  private remotePollTimer: ReturnType<typeof setInterval> | null = null;
  private broadcastChannel: BroadcastChannel | null = null;
  private lastCameraCode = '';
  private lastCameraCodeTime = 0;

  // CU-22: Customer minimal data fields
  customerName = '';
  customerNit = '';
  customerPhone = '';
  selectedOfflineCustomerId = '';
  offlineCustomers: OfflineCustomerRecord[] = [];
  filteredOfflineCustomers: OfflineCustomerRecord[] = [];
  customerSearchQuery = '';
  newCustName = '';
  newCustNit = '';
  newCustPhone = '';
  newCustEmail = '';

  // Enhancements
  branches: { id: number; name: string }[] = [];
  inventoryItems: InventoryRow[] = [];
  catalogProducts: CatalogItem[] = [];
  selectedVariant: InventoryRow | null = null;
  manualMode = false;
  loadingInventory = false;

  // CU26 return and credit-note fields
  returnSaleId: number | null = null;
  returnOrderNumber = '';
  returnSale: ReturnLookupResponse | null = null;
  returnReason = 'Talla incorrecta o cambio solicitado por el cliente';
  returnReasonTouched = false;
  returnLookupTouched = false;
  returnItems: Record<number, { quantity: number; condition: 'SELLABLE' | 'DAMAGED' }> = {};
  returnBeneficiaryCustomerId: number | null = null;
  returnCustomers: ReturnCustomer[] = [];
  returnCustomerQuery = '';
  returnBusy = false;
  returnSuccess: ReturnResponse | null = null;
  returnPendingRetry: { saleId: number; request: ReturnRequest } | null = null;
  creditNoteCode = '';
  creditNoteBalance: CreditNoteBalanceLookup | null = null;
  selectedRegisteredCustomerId: number | null = null;
  registeredCustomerQuery = '';
  registeredCustomers: ReturnCustomer[] = [];
  creditSettlementPendingRetry: { saleId: number; request: CreditNoteSettlementRequest } | null = null;
  pendingCreditSale: { id: number; order_number?: string; total: number; customer_id: number | null } | null = null;
  creditSettlementSuccess: CreditNoteSettlementResponse | null = null;

  // CU13-8 exchange fields
  exchangeOrderNumber = '';
  exchangeSale: ExchangeSaleLookup | null = null;
  exchangeInventoryItems: InventoryRow[] = [];
  exchangeReturnedVariantId = 0;
  exchangeReturnedQuantity = 1;
  exchangeNewVariantId = 0;
  exchangeNewQuantity = 1;
  exchangeItemCondition: 'EXCELLENT' | 'GOOD' | 'MINOR_DETAIL' | 'REJECTED' = 'EXCELLENT';
  exchangeCheckClean = true;
  exchangeCheckUnworn = true;
  exchangeCheckTags = true;
  exchangeCheckReceipt = true;
  exchangeConditionNotes = '';
  private _exchangeQuote: ExchangeQuote | null = null;
  get exchangeQuote(): ExchangeQuote | null { return this._exchangeQuote; }
  set exchangeQuote(value: ExchangeQuote | null) {
    this._exchangeQuote = value;
    if (value) {
      this.exchangeQuotedReturnedVariantId = this.exchangeReturnedVariantId;
      this.exchangeQuotedReturnedQuantity = this.exchangeReturnedQuantity;
      this.exchangeQuotedNewVariantId = this.exchangeNewVariantId;
      this.exchangeQuotedNewQuantity = this.exchangeNewQuantity;
    }
  }
  exchangeSuccess: ExchangeFinalizeResponse | null = null;
  exchangeCashTendered = 0;
  exchangeCashierConfirmed = false;
  exchangeReason = '';
  exchangeLookupTouched = false;
  exchangeQuantityTouched = false;
  exchangeTenderTouched = false;
  exchangeBusy = false;
  exchangeIdempotencyKey = '';
  exchangePendingRetry: { saleId: number; input: ExchangeFinalizeInput } | null = null;
  private exchangeFrozenOrderNumber = '';

  busy = false;
  message = '';

  readonly Number = Number;

  get filteredInventoryItems(): InventoryRow[] {
    const q = this.itemFilterTerm.trim().toLowerCase();
    if (!q) return this.inventoryItems;
    return this.inventoryItems.filter(
      (i) =>
        i.product_name.toLowerCase().includes(q) ||
        i.sku.toLowerCase().includes(q) ||
        i.size_name.toLowerCase().includes(q) ||
        i.color_name.toLowerCase().includes(q)
    );
  }

  get cartTotal(): number {
    return Number(
      this.cartItems.reduce((sum, item) => sum + item.unit_price * item.quantity, 0).toFixed(2)
    );
  }

  get totalCartUnits(): number {
    return this.cartItems.reduce((sum, item) => sum + item.quantity, 0);
  }

  get effectiveSaleTotal(): number {
    if (this.cartItems.length > 0) {
      return this.cartTotal;
    }
    return this.saleTotalEstimate;
  }

  get liveChange(): number {
    if (this.paymentMethod !== 'CASH') return 0;
    return Math.max(0, Number((Number(this.amount || 0) - this.effectiveSaleTotal).toFixed(2)));
  }

  get valid(): boolean {
    const hasCreditNote = this.creditNoteCode.trim().length > 0;
    const due = this.creditNoteRemainingDue;
    const ordinary = this.paymentMethod === 'CASH'
      ? this.amount >= (hasCreditNote ? due : 0)
      : this.amount === (hasCreditNote ? due : this.amount) && this.transactionReference.trim().length >= 3;
    const creditReady = !hasCreditNote || (this.isOnline && !!this.creditNoteBalance && this.creditNoteBalance.customer_id === this.selectedRegisteredCustomerId && this.selectedRegisteredCustomerId != null && (due === 0 || ordinary));
    const hasItems = this.cartItems.length > 0 || (this.variantId > 0 && this.quantity > 0);
    return this.branchId > 0 && hasItems && (hasCreditNote ? ordinary : this.amount > 0 && ordinary) && creditReady;
  }

  get canReserveInPos(): boolean {
    const hasItems = this.cartItems.length > 0 || (this.variantId > 0 && this.quantity > 0);
    return this.branchId > 0 && hasItems;
  }

  get isFinalConsumerActive(): boolean {
    const name = this.customerName.trim().toLowerCase();
    const nit = this.customerNit.trim();
    return (name.includes('consumidor final') || name.includes('s/n') || name === 'sin nombre') && (nit === '0' || nit === '');
  }

  getCustomerInitials(name: string): string {
    const parts = (name || '').trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'CL';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  get returnValid(): boolean {
    const selected = Object.entries(this.returnItems).filter(([, item]) => item.quantity > 0);
    const beneficiaryValid = this.returnSale?.customer_id != null || Number(this.returnBeneficiaryCustomerId) > 0;
    return Boolean(this.returnSale && selected.length > 0 && this.returnReason.trim().length >= 3 && beneficiaryValid);
  }
  get saleTotalEstimate(): number {
    if (this.pendingCreditSale) return this.pendingCreditSale.total;
    if (this.cartItems.length > 0) return this.cartTotal;
    const product = this.selectedVariant && this.catalogProducts.find((item) => item.id === this.selectedVariant?.product_id);
    return product ? Number((product.price * this.quantity).toFixed(2)) : Number(this.amount || 0);
  }
  get creditNoteAppliedAmount(): number { return Math.min(Number(this.creditNoteBalance?.available_balance || 0), this.saleTotalEstimate); }
  get creditNoteRemainingDue(): number { return Math.max(0, this.saleTotalEstimate - this.creditNoteAppliedAmount); }

  get isOnline(): boolean { return typeof navigator === 'undefined' || navigator.onLine; }
  get exchangeReturnedQuantityValid(): boolean {
    const returned = this.exchangeSale?.items.find((item) => item.variant_id === Number(this.exchangeReturnedVariantId));
    return Boolean(returned && this.exchangeReturnedQuantity > 0 && this.exchangeReturnedQuantity <= returned.remaining_exchangeable_quantity);
  }
  get exchangeNewQuantityValid(): boolean {
    const replacement = this.exchangeInventoryItems.find((item) => item.product_variant_id === Number(this.exchangeNewVariantId));
    return Boolean(replacement && replacement.available_quantity > 0 && this.exchangeNewQuantity > 0 && this.exchangeNewQuantity <= replacement.available_quantity);
  }
  get selectedReturnedItem(): ExchangeSaleItem | undefined {
    return this.exchangeSale?.items.find((i) => i.variant_id === Number(this.exchangeReturnedVariantId));
  }

  get selectedReturnedItemPolicyDays(): number {
    return this.selectedReturnedItem?.exchange_days ?? this.exchangeSale?.store_policy_days ?? 30;
  }

  get selectedReturnedItemWithinPolicy(): boolean {
    if (!this.selectedReturnedItem) return true;
    if (this.selectedReturnedItem.is_exchangeable !== undefined) {
      return this.selectedReturnedItem.is_exchangeable;
    }
    const daysElapsed = this.exchangeSale?.days_elapsed ?? 0;
    return this.selectedReturnedItemPolicyDays > 0 && daysElapsed <= this.selectedReturnedItemPolicyDays;
  }

  get exchangeChecklistValid(): boolean {
    return (
      this.exchangeItemCondition !== 'REJECTED' &&
      this.exchangeCheckClean &&
      this.exchangeCheckUnworn &&
      this.exchangeCheckReceipt
    );
  }

  get exchangeSelectionValid(): boolean {
    return (
      this.exchangeReturnedQuantityValid &&
      this.exchangeNewVenueMatches() &&
      this.exchangeChecklistValid &&
      this.selectedReturnedItemWithinPolicy
    );
  }
  private exchangeNewVenueMatches(): boolean {
    return this.exchangeNewVariantId > 0 && this.exchangeNewQuantityValid;
  }
  get exchangeDifference(): number { return Number(this.exchangeQuote?.difference || 0); }
  get exchangeDifferenceLabel(): string { return `${this.exchangeDifference >= 0 ? '+' : ''}Bs ${this.exchangeDifference.toFixed(2)}`; }
  get exchangeChange(): number { return Math.max(0, Number(this.exchangeCashTendered || 0) - this.exchangeDifference); }
  get exchangeQuoteFresh(): boolean { return Boolean(this.exchangeQuote && new Date(this.exchangeQuote.expires_at).getTime() > Date.now() && this.exchangeQuoteSelectionMatches); }
  get exchangeQuoteSelectionMatches(): boolean {
    return Boolean(this.exchangeQuote && this.exchangeReturnedVariantId === this.exchangeQuotedReturnedVariantId && this.exchangeReturnedQuantity === this.exchangeQuotedReturnedQuantity && this.exchangeNewVariantId === this.exchangeQuotedNewVariantId && this.exchangeNewQuantity === this.exchangeQuotedNewQuantity);
  }
  private exchangeQuotedReturnedVariantId = 0;
  private exchangeQuotedReturnedQuantity = 0;
  private exchangeQuotedNewVariantId = 0;
  private exchangeQuotedNewQuantity = 0;
  get exchangeConfirmValid(): boolean {
    if (!this.isOnline || !this.exchangeQuoteFresh || !this.exchangeQuote?.cash_settlement_eligible) return false;
    if (this.exchangeDifference > 0) return Number(this.exchangeCashTendered) >= this.exchangeDifference;
    if (this.exchangeDifference < 0) return this.exchangeCashierConfirmed;
    return true;
  }

  get paymentMethodLabel(): string {
    return ({ CASH: 'Efectivo', CARD: 'Tarjeta', QR: 'QR' } as Record<typeof this.paymentMethod, string>)[this.paymentMethod];
  }

  get selectedBranchName(): string {
    const branch = this.branches.find((b) => b.id === Number(this.branchId));
    return branch ? branch.name : (this.branchId > 0 ? `Sucursal #${this.branchId}` : 'No seleccionada');
  }

  ngOnInit(): void {
    this.initBroadcastScannerChannel();
    this.loadOfflineCustomers();
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
          this.syncCatalog.autoSync(Number(this.branchId));
        }
        this.changeDetector.detectChanges();
      },
      error: () => {
        if (this.branchId > 0) {
          this.loadBranchInventory();
          this.syncCatalog.autoSync(Number(this.branchId));
        }
      },
    });

    this.catalog.list({ page: 1, page_size: 100 }).subscribe({
      next: (page) => {
        this.catalogProducts = page.items || [];
        this.updateSuggestedAmount();
      },
      error: () => {
        this.loadOfflineCatalogProductsFallback();
      },
    });
  }

  ngOnDestroy(): void {
    this.stopRemoteScannerListening();
    if (this.broadcastChannel) {
      this.broadcastChannel.close();
      this.broadcastChannel = null;
    }
  }

  private initBroadcastScannerChannel(): void {
    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      try {
        this.broadcastChannel = new BroadcastChannel('fashionstore_pos_scanner');
        this.broadcastChannel.onmessage = (event) => {
          const data = event.data;
          if (data && data.barcode && (!data.branchId || Number(data.branchId) === Number(this.branchId))) {
            this.scanBarcode(String(data.barcode), false);
          }
        };
      } catch {
        // Ignore if BroadcastChannel is restricted
      }
    }
  }

  loadBranchInventory(): void {
    if (!this.branchId || this.branchId <= 0) return;
    if (!this.remoteScannerListening) {
      this.toggleRemoteScannerListening();
    }
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
        this.loadOfflineBranchInventoryFallback();
      },
    });
  }

  private async loadOfflineCatalogProductsFallback(): Promise<void> {
    try {
      const prods = await this.offlineCatalog.getProducts();
      if (prods.length > 0) {
        this.catalogProducts = prods.map((p) => ({
          id: p.id,
          category_id: p.category_id,
          category_name: p.category_name,
          audience: p.audience || 'UNISEX',
          code: p.code,
          name: p.name,
          slug: p.slug,
          price: p.price,
          image_url: p.image_url,
        }));
        this.updateSuggestedAmount();
        this.changeDetector.detectChanges();
      }
    } catch {
      // Ignore if offline DB is empty
    }
  }

  private async loadOfflineBranchInventoryFallback(): Promise<void> {
    try {
      const [prods, meta] = await Promise.all([
        this.offlineCatalog.getProducts(),
        this.offlineCatalog.getLatestMetadata(),
      ]);
      const rows: InventoryRow[] = [];
      for (const prod of prods) {
        const variants = await this.offlineCatalog.getVariantsByProductId(prod.id);
        for (const v of variants) {
          const inv = await this.offlineCatalog.getInventory(v.id);
          const avail = inv ? inv.available_quantity : 0;
          rows.push({
            id: v.id,
            branch_id: meta?.branch_id || Number(this.branchId),
            branch_name: meta?.branch_name || this.selectedBranchName,
            product_variant_id: v.id,
            product_id: prod.id,
            product_name: prod.name,
            sku: v.sku,
            size_id: v.size_id || 0,
            size_name: v.size_name || 'Única',
            size_type: v.size_type || 'ALPHA',
            size_sort_order: v.sort_order || 0,
            color_id: v.color_id || 0,
            color_name: v.color_name || 'Estándar',
            stock_quantity: inv?.stock_quantity || avail,
            reserved_quantity: inv?.reserved_quantity || 0,
            available_quantity: avail,
            available: avail > 0,
          });
        }
      }
      if (rows.length > 0) {
        this.inventoryItems = rows;
        const match = this.inventoryItems.find((i) => i.product_variant_id === Number(this.variantId)) || this.inventoryItems[0];
        this.onVariantChange(match.product_variant_id);
      }
    } catch {
      // Ignore
    } finally {
      this.loadingInventory = false;
      this.changeDetector.detectChanges();
    }
  }

  getVariantPrice(item: InventoryRow | null): number {
    if (!item) return 0;
    const prod = this.catalogProducts.find((p) => p.id === item.product_id);
    return prod && prod.price > 0 ? Number(prod.price) : 120;
  }

  // CU-27: Barcode / SKU Scanning & Multi-line Cart Logic
  scanBarcode(rawInput?: string, broadcastIfSender = true): void {
    const query = (rawInput !== undefined ? rawInput : this.barcodeQuery).trim();
    if (!query) return;

    if (this.mobileSenderMode && broadcastIfSender) {
      this.sendRemoteScanToPc(query);
      this.barcodeQuery = '';
      return;
    }

    const qLower = query.toLowerCase();
    const match =
      this.inventoryItems.find((i) => i.sku.toLowerCase() === qLower) ||
      this.inventoryItems.find((i) => String(i.product_variant_id) === qLower) ||
      this.inventoryItems.find((i) => i.sku.toLowerCase().includes(qLower) || i.product_name.toLowerCase().includes(qLower));

    if (!match) {
      this.playBeep(false);
      this.scannerFeedbackError = true;
      this.scannerFeedback = `No se encontró ninguna prenda con el código o nombre "${query}" en esta sucursal.`;
      this.changeDetector.detectChanges();
      return;
    }

    this.addVariantRowToCart(match, 1);
    this.barcodeQuery = '';
  }

  addCurrentSelectionToCart(): void {
    if (!this.selectedVariant) return;
    this.addVariantRowToCart(this.selectedVariant, Math.max(1, this.quantity));
  }

  private addVariantRowToCart(row: InventoryRow, qtyToAdd: number): void {
    const existing = this.cartItems.find((c) => c.product_variant_id === row.product_variant_id);
    const currentInCart = existing ? existing.quantity : 0;

    if (row.available_quantity < currentInCart + qtyToAdd) {
      this.playBeep(false);
      this.scannerFeedbackError = true;
      this.scannerFeedback = `Stock insuficiente para "${row.product_name}" (${row.size_name}/${row.color_name}). Disponibles: ${row.available_quantity}.`;
      this.changeDetector.detectChanges();
      return;
    }

    const unitPrice = this.getVariantPrice(row);
    if (existing) {
      existing.quantity += qtyToAdd;
      existing.available_quantity = row.available_quantity;
      this.lastScannedItem = existing;
    } else {
      const newItem: PosCartItem = {
        product_variant_id: row.product_variant_id,
        product_id: row.product_id,
        product_name: row.product_name,
        sku: row.sku,
        size_name: row.size_name,
        color_name: row.color_name,
        unit_price: unitPrice,
        quantity: qtyToAdd,
        available_quantity: row.available_quantity,
      };
      this.cartItems = [...this.cartItems, newItem];
      this.lastScannedItem = newItem;
    }

    this.variantId = row.product_variant_id;
    this.selectedVariant = row;
    this.amount = this.cartTotal;
    this.scannerFeedbackError = false;
    this.scannerFeedback = `${row.product_name} · Talla ${row.size_name} / ${row.color_name} (SKU: ${row.sku}) sumada al ticket.`;
    this.playBeep(true);
    this.changeDetector.detectChanges();
  }

  updateCartItemQty(variantId: number, delta: number): void {
    const idx = this.cartItems.findIndex((c) => c.product_variant_id === variantId);
    if (idx < 0) return;
    const item = this.cartItems[idx];
    const nextQty = item.quantity + delta;
    if (nextQty <= 0) {
      this.removeCartItem(variantId);
      return;
    }
    if (nextQty > item.available_quantity) {
      this.scannerFeedbackError = true;
      this.scannerFeedback = `Solo hay ${item.available_quantity} unidades disponibles de ${item.product_name}.`;
      return;
    }
    item.quantity = nextQty;
    this.cartItems = [...this.cartItems];
    this.amount = this.cartTotal;
    this.changeDetector.detectChanges();
  }

  removeCartItem(variantId: number): void {
    this.cartItems = this.cartItems.filter((c) => c.product_variant_id !== variantId);
    if (this.cartItems.length > 0) {
      this.amount = this.cartTotal;
    } else {
      this.updateSuggestedAmount();
    }
    this.changeDetector.detectChanges();
  }

  clearCart(): void {
    this.cartItems = [];
    this.lastScannedItem = null;
    this.scannerFeedback = '';
    this.updateSuggestedAmount();
    this.changeDetector.detectChanges();
  }

  // Web Audio API Cashier Laser Beep
  private playBeep(success: boolean): void {
    try {
      const AudioCtx = typeof window !== 'undefined' ? (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext) : null;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = success ? 'sine' : 'sawtooth';
      osc.frequency.value = success ? 1420 : 280;
      gain.gain.value = 0.12;
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      setTimeout(() => {
        osc.stop();
        ctx.close().catch(() => undefined);
      }, success ? 85 : 220);
    } catch {
      // Ignore audio errors when blocked by browser autoplay policy
    }
  }

  // Camera Barcode Scanner
  async toggleCameraScanner(): Promise<void> {
    if (this.cameraActive) {
      return;
    }
    this.cameraError = '';
    this.cameraActive = true;
    this.changeDetector.detectChanges();

    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      this.cameraError = 'El navegador no permite acceso directo a la cámara en este contexto. Usa el botón "Capturar etiqueta enfocada" o las Etiquetas de Prueba.';
      this.changeDetector.detectChanges();
      return;
    }

    try {
      this.cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      setTimeout(() => {
        const videoEl = this.scannerVideoRef?.nativeElement;
        if (videoEl && this.cameraStream) {
          videoEl.srcObject = this.cameraStream;
          videoEl.play().catch(() => undefined);
          this.startNativeBarcodeDetection(videoEl);
        }
      }, 100);
    } catch {
      this.cameraError = 'No se pudo abrir la cámara (verifica permisos). Puedes usar "Capturar etiqueta enfocada" o "Etiquetas de Prueba".';
      this.changeDetector.detectChanges();
    }
  }

  private startNativeBarcodeDetection(videoEl: HTMLVideoElement): void {
    const BarcodeDetectorCtor = typeof window !== 'undefined' ? (window as unknown as { BarcodeDetector?: new (opts: { formats: string[] }) => { detect: (el: HTMLVideoElement) => Promise<{ rawValue: string }[]> } }).BarcodeDetector : undefined;
    if (!BarcodeDetectorCtor) return;
    try {
      const detector = new BarcodeDetectorCtor({
        formats: ['code_128', 'ean_13', 'ean_8', 'qr_code', 'code_39', 'upc_a'],
      });
      this.cameraScanTimer = setInterval(async () => {
        if (!this.cameraActive || videoEl.readyState < 2) return;
        try {
          const codes = await detector.detect(videoEl);
          if (codes && codes.length > 0 && codes[0].rawValue) {
            const raw = codes[0].rawValue.trim();
            const now = Date.now();
            if (raw !== this.lastCameraCode || now - this.lastCameraCodeTime > 1800) {
              this.lastCameraCode = raw;
              this.lastCameraCodeTime = now;
              this.scanBarcode(raw);
            }
          }
        } catch {
          // Ignore frame detection error
        }
      }, 350);
    } catch {
      // Ignore if BarcodeDetector format unsupported
    }
  }

  triggerCameraSimulatedCapture(): void {
    const target = this.selectedVariant || this.inventoryItems.find((i) => i.available_quantity > 0);
    if (!target) {
      this.scannerFeedbackError = true;
      this.scannerFeedback = 'No hay prendas con stock en la sucursal para capturar.';
      return;
    }
    this.scanBarcode(target.sku);
  }

  stopCameraScanner(): void {
    if (this.cameraScanTimer) {
      clearInterval(this.cameraScanTimer);
      this.cameraScanTimer = null;
    }
    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach((t) => t.stop());
      this.cameraStream = null;
    }
    this.cameraActive = false;
    this.cameraError = '';
  }

  // Mobile Phone -> PC Wireless Barcode Gun Relay
  toggleMobileGunPanel(): void {
    this.showMobileGunPanel = !this.showMobileGunPanel;
    if (this.showMobileGunPanel && !this.remoteScannerListening) {
      this.toggleRemoteScannerListening();
    }
  }

  toggleRemoteScannerListening(): void {
    if (this.remoteScannerListening) {
      this.stopRemoteScannerListening();
      return;
    }
    this.remoteScannerListening = true;
    this.remotePollTimer = setInterval(() => {
      if (!this.remoteScannerListening || !this.isOnline || this.branchId <= 0) return;
      this.commerce.popScannerRelay(Number(this.branchId)).subscribe({
        next: (res) => {
          if (res?.items && res.items.length > 0) {
            res.items.forEach((entry) => {
              if (entry.barcode) {
                this.scanBarcode(entry.barcode, false);
              }
            });
          }
        },
        error: () => undefined,
      });
    }, 1200);
  }

  stopRemoteScannerListening(): void {
    if (this.remotePollTimer) {
      clearInterval(this.remotePollTimer);
      this.remotePollTimer = null;
    }
    this.remoteScannerListening = false;
  }

  onBarcodePhotoCaptured(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    this.scannerFeedback = 'Procesando foto de la etiqueta con decodificador inteligente...';
    this.scannerFeedbackError = false;
    this.changeDetector.detectChanges();

    this.commerce.scanImage(Number(this.branchId), file).subscribe({
      next: (res) => {
        if (res.success && res.barcode) {
          this.playBeep(true);
          this.scannerFeedbackError = false;
          this.scannerFeedback = `¡Código detectado con éxito! "${res.barcode}" (${res.format || 'Código de barras'}). Enviado a la caja.`;
          if (!this.mobileSenderMode) {
            this.scanBarcode(res.barcode, false);
          }
        } else {
          this.playBeep(false);
          this.scannerFeedbackError = true;
          this.scannerFeedback = res.error || 'No se detectó el código de barras en la foto. Enfoca más cerca y con buena iluminación.';
        }
        input.value = '';
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.playBeep(false);
        this.scannerFeedbackError = true;
        this.scannerFeedback = 'Error de comunicación al decodificar la foto.';
        input.value = '';
        this.changeDetector.detectChanges();
      },
    });
  }

  encodeURIComponent(val: string): string {
    return encodeURIComponent(val || '');
  }

  sendRemoteScanToPc(sku: string): void {
    const clean = sku.trim();
    if (!clean) return;
    this.playBeep(true);
    if (this.broadcastChannel) {
      try {
        this.broadcastChannel.postMessage({ branchId: Number(this.branchId), barcode: clean });
      } catch {
        // Ignore
      }
    }
    if (this.isOnline && this.branchId > 0) {
      this.commerce.pushScannerRelay(Number(this.branchId), clean).subscribe({
        next: () => {
          this.scannerFeedbackError = false;
          this.scannerFeedback = `Código "${clean}" disparado desde el celular hacia la Caja PC (Sucursal #${this.branchId}).`;
          this.changeDetector.detectChanges();
        },
        error: () => {
          this.scanBarcode(clean, false);
        },
      });
    } else {
      this.scanBarcode(clean, false);
    }
  }

  // Visual 1D Barcode & 2D QR SVG Generators (Zero external dependencies)
  getBarcodeBars(sku: string): { x: number; w: number; dark: boolean }[] {
    const bars: { x: number; w: number; dark: boolean }[] = [];
    const text = (sku || 'SKU-001').toUpperCase();
    let cursor = 8;
    // Start guard
    bars.push({ x: cursor, w: 2, dark: true });
    cursor += 4;
    bars.push({ x: cursor, w: 1.5, dark: true });
    cursor += 3.5;

    for (let i = 0; i < text.length && cursor < 164; i++) {
      const code = text.charCodeAt(i);
      const w1 = (code % 3) + 1.2;
      const s1 = ((code >> 2) % 2) + 1.2;
      const w2 = ((code >> 3) % 2) + 1.2;
      const s2 = ((code >> 4) % 2) + 1.2;
      bars.push({ x: cursor, w: w1, dark: true });
      cursor += w1 + s1;
      bars.push({ x: cursor, w: w2, dark: true });
      cursor += w2 + s2;
    }
    // End guard
    bars.push({ x: cursor, w: 2, dark: true });
    cursor += 3.5;
    bars.push({ x: cursor, w: 1.5, dark: true });
    return bars;
  }

  getInvoiceQrMatrix(payload: string): { x: number; y: number; dark: boolean }[] {
    const size = 21;
    const cells: { x: number; y: number; dark: boolean }[] = [];
    const isFinder = (r: number, c: number, top: number, left: number): boolean => {
      const dr = r - top;
      const dc = c - left;
      if (dr < 0 || dr > 6 || dc < 0 || dc > 6) return false;
      if (dr === 0 || dr === 6 || dc === 0 || dc === 6) return true;
      if (dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4) return true;
      return false;
    };
    const inFinderZone = (r: number, c: number): boolean =>
      (r <= 7 && c <= 7) || (r <= 7 && c >= size - 8) || (r >= size - 8 && c <= 7);

    let hash = 2166136261;
    for (let i = 0; i < payload.length; i++) {
      hash ^= payload.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        let dark = false;
        if (inFinderZone(r, c)) {
          dark = isFinder(r, c, 0, 0) || isFinder(r, c, 0, size - 7) || isFinder(r, c, size - 7, 0);
        } else if (r === 6 || c === 6) {
          dark = (r + c) % 2 === 0;
        } else {
          const idx = r * size + c;
          const charCode = payload.charCodeAt(idx % Math.max(1, payload.length)) || 70;
          dark = ((charCode + idx * 17 + Math.abs(hash)) % 3) !== 0;
        }
        cells.push({ x: c, y: r, dark });
      }
    }
    return cells;
  }

  private buildInvoiceReceipt(orderNumber: string, isOffline: boolean, totalConfirmed: number, changeReturned: number): PosInvoiceReceipt {
    const user = this.auth.currentUser();
    const tenantName = this.syncCatalog.lastSync()?.tenant_name || 'FashionStore SaaS';
    const cashierName = user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email : 'Cajero de Tienda';
    const custName = this.customerName.trim() || 'Sin Nombre (Consumidor Final)';
    const custNit = this.customerNit.trim() || '0';
    const custPhone = this.customerPhone.trim() || '';

    const itemsSnapshot =
      this.cartItems.length > 0
        ? this.cartItems.map((c) => ({
            sku: c.sku,
            description: `${c.product_name} (${c.size_name}/${c.color_name})`,
            quantity: c.quantity,
            unit_price: c.unit_price,
            subtotal: Number((c.unit_price * c.quantity).toFixed(2)),
          }))
        : [
            {
              sku: this.selectedVariant?.sku || `VAR-${this.variantId}`,
              description: this.selectedVariant
                ? `${this.selectedVariant.product_name} (${this.selectedVariant.size_name}/${this.selectedVariant.color_name})`
                : `Prenda Variante #${this.variantId}`,
              quantity: this.quantity,
              unit_price: this.quantity > 0 ? Number((totalConfirmed / this.quantity).toFixed(2)) : totalConfirmed,
              subtotal: totalConfirmed,
            },
          ];

    const subtotal = Number(itemsSnapshot.reduce((s, i) => s + i.subtotal, 0).toFixed(2));
    const discount = Math.max(0, Number((subtotal - totalConfirmed).toFixed(2)));
    const hexPart = Math.abs(orderNumber.split('').reduce((a, ch) => (a << 5) - a + ch.charCodeAt(0), 0))
      .toString(16)
      .toUpperCase()
      .padStart(8, 'A');
    const controlCode = `${hexPart.slice(0, 2)}-${hexPart.slice(2, 4)}-${hexPart.slice(4, 6)}-${hexPart.slice(6, 8)}`;
    const nowIso = new Date().toISOString();
    const qrPayload = `1029485021|${orderNumber}|${nowIso.slice(0, 10)}|${totalConfirmed.toFixed(2)}|${controlCode}|${custNit}`;

    return {
      invoice_number: orderNumber,
      control_code: controlCode,
      is_offline: isOffline,
      issued_at: nowIso,
      tenant_name: tenantName,
      branch_name: this.selectedBranchName,
      cashier_name: cashierName,
      customer_name: custName,
      customer_nit: custNit,
      customer_phone: custPhone,
      payment_method: this.paymentMethodLabel,
      items: itemsSnapshot,
      subtotal,
      discount,
      total: totalConfirmed,
      amount_received: Number(this.amount || totalConfirmed),
      change_returned: changeReturned,
      qr_payload: qrPayload,
    };
  }

  printInvoice(): void {
    if (typeof window !== 'undefined' && typeof window.print === 'function') {
      window.print();
    }
  }

  onBranchChange(newBranchId: number): void {
    this.branchId = Number(newBranchId);
    this.variantId = 0;
    this.selectedVariant = null;
    this.cartItems = [];
    this.loadBranchInventory();
    this.syncCatalog.autoSync(Number(newBranchId));
  }

  onVariantChange(newVariantId: number): void {
    this.variantId = Number(newVariantId);
    this.selectedVariant = this.inventoryItems.find((i) => i.product_variant_id === this.variantId) || null;
    if (this.cartItems.length === 0) {
      this.updateSuggestedAmount();
    }
    this.changeDetector.detectChanges();
  }

  onQuantityChange(): void {
    if (this.quantity < 1) this.quantity = 1;
    if (this.cartItems.length === 0) {
      this.updateSuggestedAmount();
    }
  }

  private updateSuggestedAmount(): void {
    if (this.cartItems.length > 0) {
      this.amount = this.cartTotal;
      return;
    }
    if (!this.selectedVariant) return;
    const prod = this.catalogProducts.find((p) => p.id === this.selectedVariant?.product_id);
    if (prod && prod.price > 0) {
      this.amount = Number((prod.price * this.quantity).toFixed(2));
    }
  }

  create(): void {
    if (this.busy) return;
    if (this.creditSettlementPendingRetry) { this.submitCreditSettlement(this.creditSettlementPendingRetry.saleId, this.creditSettlementPendingRetry.request); return; }
    if (this.pendingCreditSale && this.creditNoteCode.trim()) { this.submitCreditSettlement(this.pendingCreditSale.id, this.buildCreditSettlementRequest()); return; }
    if (!this.valid) return;
    this.busy = true; this.message = '';
    if (typeof navigator !== 'undefined' && !navigator.onLine) { if (this.creditNoteCode.trim()) { this.message = 'Las ventas con nota de crédito requieren conexión online.'; this.busy = false; return; } this.recordOfflineSaleFallback(); return; }
    const saleItems = this.cartItems.length > 0
      ? this.cartItems.map((c) => ({ product_variant_id: Number(c.product_variant_id), quantity: c.quantity }))
      : [{ product_variant_id: Number(this.variantId), quantity: this.quantity }];
    const saleRequest = { branch_id: Number(this.branchId), ...(this.selectedRegisteredCustomerId ? { customer_id: this.selectedRegisteredCustomerId } : {}), items: saleItems };
    this.commerce.physicalSale(saleRequest).pipe(timeout({ each: 10000 }), switchMap((sale: Sale) => {
      if (!this.creditNoteCode.trim()) return this.commerce.cashPayment(sale.id, this.amount, this.paymentMethod, this.transactionReference.trim() || undefined);
      this.pendingCreditSale = { id: sale.id, order_number: sale.order_number, total: Number(sale.total), customer_id: sale.customer_id };
      return this.submitCreditSettlement$(sale.id);
    }), finalize(() => { this.busy = false; this.changeDetector.detectChanges(); })).subscribe({
      next: (paid: Sale | CreditNoteSettlementResponse) => {
        this.lastTotal = Number(paid.total);
        let orderCode = '';
        if (this.creditNoteCode.trim()) {
          const settlement = paid as CreditNoteSettlementResponse;
          this.creditSettlementPendingRetry = null;
          this.creditSettlementSuccess = settlement;
          this.change = Number(settlement.cash_change || 0);
          orderCode = String(settlement.order_number || settlement.id);
          this.message = `Venta ${orderCode} confirmada con nota de crédito. Aplicado: Bs ${settlement.applied_amount}. Saldo posterior: Bs ${settlement.post_redemption_balance}. Cambio exacto: Bs ${this.change.toFixed(2)}.`;
          this.pendingCreditSale = null;
        } else {
          const salePaid = paid as Sale;
          orderCode = salePaid.order_number || `ORD-${salePaid.id}`;
          this.change = this.paymentMethod === 'CASH' ? Math.max(0, this.amount - this.lastTotal) : 0;
          this.message = `Venta ${orderCode} confirmada exitosamente. Total: Bs ${this.lastTotal.toFixed(2)}. Factura emitida.`;
        }
        this.lastInvoice = this.buildInvoiceReceipt(orderCode, false, this.lastTotal, this.change);
        this.showInvoiceModal = true;
        this.cartItems = [];
        this.quantity = 1;
        this.loadBranchInventory();
        this.syncCatalog.autoSync(Number(this.branchId));
      },
      error: (error: { status?: number; name?: string; error?: { detail?: { message?: string } } }) => { if (this.creditNoteCode.trim()) { if (this.isAmbiguousCreditError(error)) this.message = 'La liquidación quedó incierta. La solicitud está congelada; reintentá exactamente la misma operación.'; else { this.creditSettlementPendingRetry = null; this.message = error.error?.detail?.message || 'No se pudo liquidar la nota de crédito.'; } } else if (error?.status === 0 || error?.name === 'TimeoutError' || (typeof navigator !== 'undefined' && !navigator.onLine)) this.recordOfflineSaleFallback(); else this.message = error.error?.detail?.message || 'No se pudo confirmar la venta.'; }
    });
  }

  private submitCreditSettlement$(saleId: number) {
    const request = this.buildCreditSettlementRequest();
    return this.commerce.settleCreditNote(saleId, request).pipe(
      timeout({ each: 10000 }),
      catchError((error) => { if (this.isAmbiguousCreditError(error)) this.creditSettlementPendingRetry = { saleId, request: { ...request } }; return throwError(() => error); }),
      finalize(() => undefined),
    );
  }

  private buildCreditSettlementRequest(): CreditNoteSettlementRequest {
    const request: CreditNoteSettlementRequest = { credit_note_code: this.creditNoteCode.trim(), idempotency_key: this.creditSettlementPendingRetry?.request.idempotency_key || `credit-settlement-${Date.now()}-${Math.random().toString(36).slice(2)}` };
    if (this.creditNoteRemainingDue > 0) { request.method = this.paymentMethod; request.amount = this.amount; if (this.transactionReference.trim()) request.transaction_reference = this.transactionReference.trim(); }
    return request;
  }

  private submitCreditSettlement(saleId: number, request: CreditNoteSettlementRequest): void {
    if (!this.isOnline) { this.message = 'La liquidación de nota de crédito requiere conexión online.'; return; }
    this.busy = true; this.commerce.settleCreditNote(saleId, request).pipe(finalize(() => { this.busy = false; this.changeDetector.detectChanges(); })).subscribe({ next: (result: CreditNoteSettlementResponse) => { this.creditSettlementPendingRetry = null; this.pendingCreditSale = null; this.creditSettlementSuccess = result; this.change = Number(result.cash_change || 0); this.message = `Liquidación confirmada. Aplicado: Bs ${result.applied_amount}. Saldo posterior: Bs ${result.post_redemption_balance}.`; }, error: (error: { status?: number; name?: string; error?: { detail?: { message?: string } } }) => { if (this.isAmbiguousCreditError(error)) { this.creditSettlementPendingRetry = { saleId, request: { ...request } }; this.message = 'La respuesta fue incierta; reintentá exactamente la misma liquidación.'; } else { this.creditSettlementPendingRetry = null; this.message = error.error?.detail?.message || 'No se pudo liquidar la nota de crédito.'; } } });
  }

  private isAmbiguousCreditError(error: { status?: number; name?: string }): boolean { return error?.status === 0 || error?.name === 'TimeoutError' || error?.status === 408 || Number(error?.status) >= 500; }

  loadOfflineCustomers(): void {
    this.offlineTx.listCustomers().then((list) => {
      this.offlineCustomers = list;
      this.filterOfflineCustomers();
      this.changeDetector.detectChanges();
    }).catch(() => undefined);
  }

  filterOfflineCustomers(): void {
    const q = this.customerSearchQuery.trim().toLowerCase();
    if (!q) {
      this.filteredOfflineCustomers = [...this.offlineCustomers];
      return;
    }
    this.filteredOfflineCustomers = this.offlineCustomers.filter(
      (c) =>
        c.full_name.toLowerCase().includes(q) ||
        c.nit_ci.toLowerCase().includes(q) ||
        (c.phone || '').toLowerCase().includes(q)
    );
  }

  onSelectOfflineCustomer(customerId: string): void {
    const found = this.offlineCustomers.find((c) => c.id === customerId);
    if (!found) return;
    this.customerName = found.full_name;
    this.customerNit = found.nit_ci;
    this.customerPhone = found.phone || '';
    this.changeDetector.detectChanges();
  }

  setFinalConsumer(): void {
    this.wantsInvoiceWithNit = false;
    this.selectedOfflineCustomerId = '';
    this.customerName = 'Sin Nombre (Consumidor Final)';
    this.customerNit = '0';
    this.customerPhone = '';
    this.changeDetector.detectChanges();
  }

  saveCurrentCustomerLocally(): void {
    if (!this.customerName.trim() || !this.customerNit.trim()) {
      this.message = 'Ingresa al menos Nombre/Razón Social y CI/NIT para guardar el cliente en el padrón local.';
      this.changeDetector.detectChanges();
      return;
    }
    this.offlineTx.saveCustomer({
      full_name: this.customerName.trim(),
      nit_ci: this.customerNit.trim(),
      phone: this.customerPhone.trim() || null,
    }).then((saved) => {
      this.selectedOfflineCustomerId = saved.id;
      this.message = `Cliente "${saved.full_name}" (CI/NIT: ${saved.nit_ci}) guardado en IndexedDB para operaciones offline.`;
      this.loadOfflineCustomers();
    }).catch(() => {
      this.message = 'Error al guardar el cliente en IndexedDB.';
      this.changeDetector.detectChanges();
    });
  }

  createOfflineCustomer(): void {
    if (!this.newCustName.trim() || !this.newCustNit.trim()) return;
    this.offlineTx.saveCustomer({
      full_name: this.newCustName.trim(),
      nit_ci: this.newCustNit.trim(),
      phone: this.newCustPhone.trim() || null,
      email: this.newCustEmail.trim() || null,
    }).then((saved) => {
      this.message = `Cliente "${saved.full_name}" registrado en el padrón local offline (IndexedDB).`;
      this.newCustName = '';
      this.newCustNit = '';
      this.newCustPhone = '';
      this.newCustEmail = '';
      this.loadOfflineCustomers();
    });
  }

  useCustomerForSale(customer: OfflineCustomerRecord): void {
    this.selectedOfflineCustomerId = customer.id;
    this.customerName = customer.full_name;
    this.customerNit = customer.nit_ci;
    this.customerPhone = customer.phone || '';
    this.mode = 'SALE';
    this.message = `Cliente "${customer.full_name}" seleccionado para el comprobante de venta.`;
    this.changeDetector.detectChanges();
  }

  removeOfflineCustomer(id: string): void {
    this.offlineTx.deleteCustomer(id).then(() => {
      if (this.selectedOfflineCustomerId === id) {
        this.selectedOfflineCustomerId = '';
      }
      this.loadOfflineCustomers();
    });
  }

  private recordOfflineSaleFallback(): void {
    const saleTotal = this.effectiveSaleTotal > 0 ? this.effectiveSaleTotal : this.amount;
    const offlineItems =
      this.cartItems.length > 0
        ? this.cartItems.map((c) => ({
            product_variant_id: Number(c.product_variant_id),
            quantity: c.quantity,
            unit_price: c.unit_price,
          }))
        : [
            {
              product_variant_id: Number(this.variantId),
              quantity: this.quantity,
              unit_price: this.quantity > 0 ? Number((saleTotal / this.quantity).toFixed(2)) : saleTotal,
            },
          ];

    this.offlineTx.recordOfflineSale(Number(this.branchId), {
      customer_name: this.customerName.trim() || 'Consumidor Final',
      customer_nit: this.customerNit.trim() || '0',
      customer_phone: this.customerPhone.trim() || null,
      items: offlineItems,
      total: saleTotal,
      discount: 0,
      payment_method: 'CASH',
    }).then((rec) => {
      this.lastTotal = saleTotal;
      this.change = Math.max(0, Number((this.amount - this.lastTotal).toFixed(2)));
      this.lastInvoice = this.buildInvoiceReceipt(rec.client_operation_id, true, this.lastTotal, this.change);
      this.showInvoiceModal = true;
      this.cartItems = [];
      this.message = `(Modo Offline) Venta registrada localmente en espera de sincronización. ID: ${rec.client_operation_id}. Comprobante emitido.`;
      this.syncTx.refreshPendingCount();
      this.loadOfflineCustomers();
      this.loadBranchInventory();
      this.quantity = 1;
      this.busy = false;
      this.changeDetector.detectChanges();
    }).catch(() => {
      this.message = 'Error al registrar la venta en almacenamiento local.';
      this.busy = false;
      this.changeDetector.detectChanges();
    });
  }

  reserveFromPos(): void {
    if (this.busy || !this.canReserveInPos) return;
    this.busy = true;
    this.message = '';

    const reserveItems =
      this.cartItems.length > 0
        ? this.cartItems.map((c) => ({
            product_variant_id: Number(c.product_variant_id),
            quantity: c.quantity,
          }))
        : [
            {
              product_variant_id: Number(this.variantId),
              quantity: this.quantity,
            },
          ];

    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    this.offlineTx
      .recordOfflineReservation(Number(this.branchId), {
        customer_name: this.customerName.trim() || 'Cliente Reserva en Tienda',
        customer_nit: this.customerNit.trim() || '0',
        customer_phone: this.customerPhone.trim() || null,
        items: reserveItems,
        scheduled_for: expiresAt,
        notes: 'Reserva de prendas registrada desde Caja / Punto de Venta',
      })
      .then((rec) => {
        this.cartItems = [];
        this.quantity = 1;
        this.message = `Reserva de prendas registrada localmente en espera de sincronización. ID: ${rec.client_operation_id}. Stock apartado por 24 horas.`;
        this.syncTx.refreshPendingCount();
        this.loadOfflineCustomers();
        this.loadBranchInventory();
        this.busy = false;
        this.changeDetector.detectChanges();
      })
      .catch(() => {
        this.message = 'Error al registrar la reserva de prendas en almacenamiento local.';
        this.busy = false;
        this.changeDetector.detectChanges();
      });
  }

  clearExchangeState(): void { this.message = ''; this.exchangeQuote = null; this.exchangeSuccess = null; }

  onExchangeOrderNumberChange(value: string): void {
    if (this.exchangePendingRetry) {
      this.exchangeOrderNumber = this.exchangeFrozenOrderNumber;
      this.message = 'La confirmación incierta está congelada; reintentá la misma operación antes de cambiar el comprobante.';
      return;
    }
    this.exchangeOrderNumber = value;
    this.exchangeSale = null;
    this.exchangeInventoryItems = [];
    this.exchangeReturnedVariantId = 0;
    this.exchangeReturnedQuantity = 1;
    this.exchangeNewVariantId = 0;
    this.exchangeNewQuantity = 1;
    this.exchangeQuote = null;
    this.exchangeSuccess = null;
    this.exchangeCashTendered = 0;
    this.exchangeCashierConfirmed = false;
    this.exchangeIdempotencyKey = '';
    this.message = '';
  }

  onExchangeSelectionChange(field: 'returnedVariant' | 'returnedQuantity' | 'newVariant' | 'newQuantity', value: number): void {
    if (this.exchangePendingRetry) {
      if (field === 'returnedVariant') this.exchangeReturnedVariantId = this.exchangePendingRetry.input.returned_variant_id;
      if (field === 'returnedQuantity') this.exchangeReturnedQuantity = this.exchangePendingRetry.input.returned_quantity;
      if (field === 'newVariant') this.exchangeNewVariantId = this.exchangePendingRetry.input.new_variant_id;
      if (field === 'newQuantity') this.exchangeNewQuantity = this.exchangePendingRetry.input.new_quantity;
      this.message = 'La confirmación incierta está congelada; no se puede cambiar la selección durante el reintento.';
      return;
    }
    if (field === 'returnedVariant') this.exchangeReturnedVariantId = Number(value);
    if (field === 'returnedQuantity') this.exchangeReturnedQuantity = Number(value);
    if (field === 'newVariant') this.exchangeNewVariantId = Number(value);
    if (field === 'newQuantity') this.exchangeNewQuantity = Number(value);
    this.invalidateExchangeQuote();
  }

  invalidateExchangeQuote(): void { this.exchangeQuote = null; this.exchangeSuccess = null; }

  resetExchangeFlow(): void {
    if (this.exchangePendingRetry || this.exchangeBusy) return;
    this.exchangeOrderNumber = '';
    this.exchangeSale = null;
    this.exchangeInventoryItems = [];
    this.exchangeReturnedVariantId = 0;
    this.exchangeReturnedQuantity = 1;
    this.exchangeNewVariantId = 0;
    this.exchangeNewQuantity = 1;
    this.exchangeQuote = null;
    this.exchangeSuccess = null;
    this.exchangeCashTendered = 0;
    this.exchangeCashierConfirmed = false;
    this.exchangeReason = '';
    this.exchangeItemCondition = 'EXCELLENT';
    this.exchangeCheckClean = true;
    this.exchangeCheckUnworn = true;
    this.exchangeCheckTags = true;
    this.exchangeCheckReceipt = true;
    this.exchangeConditionNotes = '';
    this.exchangeLookupTouched = false;
    this.exchangeQuantityTouched = false;
    this.exchangeTenderTouched = false;
    this.exchangeIdempotencyKey = '';
    this.message = '';
  }

  lookupExchangeSale(): void {
    this.exchangeLookupTouched = true;
    if (!this.isOnline) {
      this.message = 'La búsqueda de ventas para cambio requiere conexión online.';
      return;
    }
    if (this.exchangePendingRetry) {
      this.message = 'La confirmación incierta está congelada; primero reintentá la misma operación.';
      return;
    }
    if (!this.exchangeOrderNumber.trim() || this.exchangeBusy) return;
    this.exchangeBusy = true; this.message = ''; this.exchangeSale = null; this.exchangeQuote = null; this.exchangeSuccess = null;
    this.commerce.lookupSaleForExchange(this.exchangeOrderNumber.trim()).pipe(finalize(() => { this.exchangeBusy = false; this.changeDetector.detectChanges(); })).subscribe({
      next: (sale) => { this.exchangeSale = sale; this.loadExchangeInventory(sale.branch_id); this.message = `Venta ${sale.order_number} encontrada.`; },
      error: (error) => { this.message = error.error?.detail?.message || 'No se pudo consultar la venta.'; },
    });
  }

  private loadExchangeInventory(branchId: number): void {
    this.admin.inventoryAll(branchId, 1, 100).subscribe({ next: (res) => { this.exchangeInventoryItems = res.items || []; this.changeDetector.detectChanges(); }, error: () => { this.message = 'No se pudo cargar el inventario de la sucursal de la venta.'; } });
  }

  requestExchangeQuote(): void {
    if (!this.isOnline) {
      this.message = 'La cotización de cambio requiere conexión online.';
      return;
    }
    if (!this.exchangeSale || !this.exchangeSelectionValid || this.exchangeBusy || this.exchangePendingRetry) return;
    this.exchangeBusy = true; this.exchangeSuccess = null; this.message = '';
    const input = { returned_variant_id: Number(this.exchangeReturnedVariantId), returned_quantity: Number(this.exchangeReturnedQuantity), new_variant_id: Number(this.exchangeNewVariantId), new_quantity: Number(this.exchangeNewQuantity) };
    this.commerce.exchangeQuote(this.exchangeSale.sale_id, input).pipe(finalize(() => { this.exchangeBusy = false; this.changeDetector.detectChanges(); })).subscribe({
      next: (quote) => { this.exchangeQuote = quote; this.exchangeQuotedReturnedVariantId = this.exchangeReturnedVariantId; this.exchangeQuotedReturnedQuantity = this.exchangeReturnedQuantity; this.exchangeQuotedNewVariantId = this.exchangeNewVariantId; this.exchangeQuotedNewQuantity = this.exchangeNewQuantity; this.exchangeCashTendered = 0; this.exchangeCashierConfirmed = false; },
      error: (error) => { this.message = error.error?.detail?.message || 'No se pudo cotizar el cambio. Revisá la selección e intentá nuevamente.'; },
    });
  }

  finalizeExchange(): void {
    if (this.exchangeBusy) return;
    if (!this.isOnline) {
      this.message = 'El cambio solo puede confirmarse online. Conectate a Internet antes de confirmar o reintentar.';
      return;
    }
    if (this.exchangePendingRetry) {
      this.submitExchangeFinalize(this.exchangePendingRetry.saleId, this.exchangePendingRetry.input);
      return;
    }
    if (!this.exchangeSale || !this.exchangeQuote) return;
    if (!this.exchangeQuoteFresh) { this.message = 'La cotización está vencida. Solicitá una nueva cotización antes de confirmar.'; return; }
    if (!this.exchangeConfirmValid) return;
    if (!this.exchangeIdempotencyKey) this.exchangeIdempotencyKey = `exchange-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const checklist: string[] = [];
    if (this.exchangeCheckClean) checklist.push('Limpia sin manchas ni olores');
    if (this.exchangeCheckUnworn) checklist.push('Sin señales de uso o lavado');
    if (this.exchangeCheckTags) checklist.push('Etiquetas originales intactas');
    if (this.exchangeCheckReceipt) checklist.push('Comprobante dentro de política');
    const input: ExchangeFinalizeInput = {
      returned_variant_id: this.exchangeReturnedVariantId,
      returned_quantity: this.exchangeReturnedQuantity,
      new_variant_id: this.exchangeNewVariantId,
      new_quantity: this.exchangeNewQuantity,
      quote_fingerprint: this.exchangeQuote.quote_fingerprint,
      quote_expires_at: this.exchangeQuote.expires_at,
      idempotency_key: this.exchangeIdempotencyKey,
      item_condition: this.exchangeItemCondition,
      inspection_checklist: checklist,
      condition_notes: this.exchangeConditionNotes.trim() || undefined,
    };
    if (this.exchangeReason.trim()) input.reason = this.exchangeReason.trim();
    if (this.exchangeDifference > 0) input.cash_tendered = Number(this.exchangeCashTendered);
    if (this.exchangeDifference < 0) input.cashier_confirmed = true;
    this.submitExchangeFinalize(this.exchangeSale.sale_id, input);
  }

  private submitExchangeFinalize(saleId: number, input: ExchangeFinalizeInput): void {
    this.exchangeBusy = true; this.message = '';
    this.commerce.finalizeExchange(saleId, input).pipe(finalize(() => { this.exchangeBusy = false; this.changeDetector.detectChanges(); })).subscribe({
      next: (result) => {
        this.exchangeSuccess = result;
        this.exchangePendingRetry = null;
        this.exchangeQuote = null;
        this.exchangeIdempotencyKey = '';
        if (this.exchangeSale) {
          const line = this.exchangeSale.items.find((i) => i.variant_id === Number(input.returned_variant_id));
          if (line) {
            line.remaining_exchangeable_quantity = Math.max(0, line.remaining_exchangeable_quantity - Number(input.returned_quantity));
          }
          this.loadExchangeInventory(this.exchangeSale.branch_id);
        }
        this.message = `Cambio confirmado por el servidor. Estado: ${result.status}.`;
      },
      error: (error) => {
        if (this.isAmbiguousExchangeError(error)) {
          this.exchangePendingRetry = { saleId, input: { ...input } };
          this.exchangeFrozenOrderNumber = this.exchangeOrderNumber || this.exchangeSale?.order_number || '';
          this.exchangeIdempotencyKey = input.idempotency_key;
          this.message = 'La respuesta del servidor fue incierta. La operación quedó congelada; reintentá con la misma clave para verificar el resultado.';
        } else {
          this.exchangePendingRetry = null;
          this.exchangeIdempotencyKey = '';
          this.exchangeQuote = null;
          this.message = error.error?.detail?.message || 'No se pudo confirmar el cambio. Solicitá una nueva cotización.';
        }
      },
    });
  }

  private isAmbiguousExchangeError(error: { status?: number; name?: string }): boolean {
    return error?.status === 0 || error?.name === 'TimeoutError' || error?.status === 408 || Number(error?.status) >= 500;
  }

  setReturnQuantity(itemId: number, quantity: number): void { if (this.returnPendingRetry) return; const item = this.returnSale?.items.find((line) => line.id === itemId); const max = item?.remaining_returnable_quantity || 0; this.returnItems[itemId] = { quantity: Math.max(0, Math.min(Number(quantity) || 0, max)), condition: this.returnItems[itemId]?.condition || 'SELLABLE' }; }
  setReturnCondition(itemId: number, condition: 'SELLABLE' | 'DAMAGED'): void { if (this.returnPendingRetry) return; this.returnItems[itemId] = { quantity: this.returnItems[itemId]?.quantity || 0, condition }; }
  lookupReturn(): void {
    if (!this.isOnline) { this.message = 'La búsqueda de devoluciones requiere conexión online.'; return; }
    if (this.returnPendingRetry || !this.returnOrderNumber.trim() || this.returnBusy) return;
    this.returnBusy = true; this.message = ''; this.returnSuccess = null;
    this.commerce.lookupReturn(this.returnOrderNumber.trim()).pipe(finalize(() => { this.returnBusy = false; this.changeDetector.detectChanges(); })).subscribe({ next: (sale) => { this.returnSale = sale; this.returnSaleId = sale.sale_id; this.returnBeneficiaryCustomerId = sale.customer_id; this.returnItems = {}; this.message = `Venta ${sale.order_number} encontrada.`; }, error: (error) => { this.message = error.error?.detail?.message || 'No se pudo consultar la venta.'; } });
  }
  searchReturnCustomers(): void { if (!this.isOnline || !this.returnCustomerQuery.trim()) { this.returnCustomers = []; return; } this.commerce.searchReturnCustomers(this.returnCustomerQuery.trim()).subscribe({ next: (customers) => { this.returnCustomers = customers; }, error: () => { this.message = 'No se pudieron buscar clientes.'; } }); }
  searchRegisteredCustomers(): void { if (!this.isOnline || !this.registeredCustomerQuery.trim()) { this.registeredCustomers = []; return; } this.commerce.searchReturnCustomers(this.registeredCustomerQuery.trim()).subscribe({ next: (customers) => { this.registeredCustomers = customers; }, error: () => { this.message = 'No se pudieron buscar clientes registrados.'; } }); }
  lookupCreditNote(): void { if (!this.creditNoteCode.trim()) { this.creditNoteBalance = null; return; } if (!this.isOnline) { this.message = 'La consulta de nota de crédito requiere conexión online.'; return; } if (!this.selectedRegisteredCustomerId || !this.branchId) { this.message = 'Seleccioná un cliente registrado y una sucursal antes de consultar la nota.'; return; } this.commerce.lookupCreditNote({ credit_note_code: this.creditNoteCode.trim(), customer_id: this.selectedRegisteredCustomerId, branch_id: Number(this.branchId) }).subscribe({ next: (balance) => { this.creditNoteBalance = balance; this.message = `Nota de crédito validada. Saldo disponible: Bs ${balance.available_balance}.`; }, error: (error) => { this.creditNoteBalance = null; this.message = error.error?.detail?.message || 'No se pudo validar la nota de crédito.'; } }); }
  processReturn(): void {
    if (!this.isOnline) { this.message = 'La devolución solo puede procesarse online.'; return; }
    if (this.busy) return;
    if (this.returnPendingRetry) { this.submitReturn(this.returnPendingRetry.saleId, this.returnPendingRetry.request); return; }
    if (!this.returnValid || !this.returnSale) return;
    const request: ReturnRequest = { items: Object.entries(this.returnItems).filter(([, item]) => item.quantity > 0).map(([id, item]) => ({ sale_item_id: Number(id), quantity: item.quantity, condition: item.condition })), beneficiary_customer_id: this.returnBeneficiaryCustomerId || undefined, reason: this.returnReason.trim(), idempotency_key: `return-${Date.now()}-${Math.random().toString(36).slice(2)}` };
    this.submitReturn(this.returnSale.sale_id, request);
  }
  private submitReturn(saleId: number, request: ReturnRequest): void { this.busy = true; this.commerce.submitReturn(saleId, request).pipe(timeout({ each: 10000 }), finalize(() => { this.busy = false; this.changeDetector.detectChanges(); })).subscribe({ next: (result) => { this.returnSuccess = result; this.returnPendingRetry = null; this.message = `Devolución confirmada. Nota de crédito: ${result.credit_note_code}.`; this.returnSale = null; this.returnItems = {}; }, error: (error) => { if (this.isAmbiguousCreditError(error)) { this.returnPendingRetry = { saleId, request: { ...request, items: request.items.map((item) => ({ ...item })) } }; this.message = 'La respuesta fue incierta; reintentá exactamente la misma devolución.'; } else { this.returnPendingRetry = null; this.message = error.error?.detail?.message || 'No se pudo procesar la devolución.'; } } }); }


  // =========================================================================
  // CU-28: GENERACIÓN E IMPRESIÓN DE ETIQUETAS COLGANTES CON CÓDIGO DE BARRAS
  // =========================================================================
    onLabelCopiesInputChange(tag: PosLabelBatchItem): void {
    if (!tag.copies || tag.copies < 1) tag.copies = 1;
    if (tag.copies > 100) tag.copies = 100;
    this.changeDetector.detectChanges();
  }

  syncLabelCopiesToStock(): void {
    for (const item of this.labelBatch) {
      const inv = this.inventoryItems.find((i) => i.product_variant_id === item.variant_id);
      if (inv && inv.available_quantity > 0) {
        item.copies = inv.available_quantity;
      }
    }
    this.labelBatch = [...this.labelBatch];
    this.message = 'Se ajustó la cantidad de etiquetas al stock real disponible de cada prenda en la sucursal.';
    this.changeDetector.detectChanges();
  }

  openLabelsMode(): void {
    this.mode = 'LABELS';
    this.message = '';
    if (this.labelBatch.length === 0 && this.inventoryItems.length > 0) {
      this.loadDefaultLabelBatch();
    }
  }

  get filteredLabelInventory(): InventoryRow[] {
    const q = this.labelSearchTerm.trim().toLowerCase();
    if (!q) return this.inventoryItems;
    return this.inventoryItems.filter(
      (i) =>
        i.product_name.toLowerCase().includes(q) ||
        i.sku.toLowerCase().includes(q) ||
        i.size_name.toLowerCase().includes(q) ||
        i.color_name.toLowerCase().includes(q)
    );
  }

  get totalLabelCopies(): number {
    return this.labelBatch.reduce((acc, item) => acc + Math.max(1, item.copies), 0);
  }

  get expandedLabelSheet(): PosLabelBatchItem[] {
    const list: PosLabelBatchItem[] = [];
    for (const item of this.labelBatch) {
      const count = Math.min(100, Math.max(1, Number(item.copies || 1)));
      for (let i = 0; i < count; i++) {
        list.push(item);
      }
    }
    return list;
  }

  loadDefaultLabelBatch(): void {
    const sample = this.inventoryItems.slice(0, 6);
    this.labelBatch = sample.map((item, idx) => ({
      variant_id: item.product_variant_id,
      sku: item.sku,
      product_name: item.product_name,
      size_name: item.size_name,
      color_name: item.color_name,
      unit_price: this.getVariantPrice(item),
      copies: idx < 2 ? 2 : 1,
    }));
    this.changeDetector.detectChanges();
  }

  clearLabelBatch(): void {
    this.labelBatch = [];
    this.changeDetector.detectChanges();
  }

  addVariantToLabelBatch(item: InventoryRow): void {
    const existing = this.labelBatch.find((b) => b.variant_id === item.product_variant_id);
    if (existing) {
      existing.copies += 1;
      this.labelBatch = [...this.labelBatch];
    } else {
      this.labelBatch = [
        ...this.labelBatch,
        {
          variant_id: item.product_variant_id,
          sku: item.sku,
          product_name: item.product_name,
          size_name: item.size_name,
          color_name: item.color_name,
          unit_price: this.getVariantPrice(item),
          copies: 1,
        },
      ];
    }
    this.changeDetector.detectChanges();
  }

  updateLabelCopies(variantId: number, delta: number): void {
    const idx = this.labelBatch.findIndex((b) => b.variant_id === variantId);
    if (idx < 0) return;
    const next = this.labelBatch[idx].copies + delta;
    if (next <= 0) {
      this.labelBatch = this.labelBatch.filter((b) => b.variant_id !== variantId);
    } else {
      this.labelBatch[idx].copies = Math.min(30, next);
      this.labelBatch = [...this.labelBatch];
    }
    this.changeDetector.detectChanges();
  }

  scanFromLabelToPos(sku: string): void {
    this.mode = 'SALE';
    this.scanBarcode(sku);
  }

  // =========================================================================
  // CU-29: ARQUEO Y CIERRE DE CAJA POR TURNO (REPORTE Z)
  // =========================================================================
  openCashCloseMode(): void {
    this.mode = 'CASH_CLOSE';
    this.message = '';
    if (this.lastTotal > 0) {
      if (this.paymentMethod === 'CASH') {
        this.cashCloseCashSales = Math.max(this.cashCloseCashSales, Number(this.lastTotal.toFixed(2)));
      } else if (this.paymentMethod === 'QR') {
        this.cashCloseQrSales = Math.max(this.cashCloseQrSales, Number(this.lastTotal.toFixed(2)));
      } else {
        this.cashCloseCardSales = Math.max(this.cashCloseCardSales, Number(this.lastTotal.toFixed(2)));
      }
    }
    if (this.cashCloseHistory.length === 0) {
      this.autoFillExactCashCount();
    }
  }

  get expectedCashInDrawer(): number {
    return Number(
      (
        Number(this.cashCloseOpeningFloat || 0) +
        Number(this.cashCloseCashSales || 0) +
        Number(this.cashCloseExchangeIn || 0) -
        Number(this.cashCloseRefundsOut || 0)
      ).toFixed(2)
    );
  }

  get countedCashInDrawer(): number {
    return Number(
      this.cashDenominations
        .reduce((sum, d) => sum + d.value * Math.max(0, Number(d.count || 0)), 0)
        .toFixed(2)
    );
  }

  get cashCloseDiscrepancy(): number {
    return Number((this.countedCashInDrawer - this.expectedCashInDrawer).toFixed(2));
  }

  autoFillExactCashCount(): void {
    let remaining = Math.max(0, Math.round(this.expectedCashInDrawer));
    for (const denom of this.cashDenominations) {
      if (denom.value >= 10) {
        denom.count = Math.floor(remaining / denom.value);
        remaining = remaining % denom.value;
      } else {
        denom.count = remaining;
        remaining = 0;
      }
    }
    this.cashDenominations = [...this.cashDenominations];
    this.changeDetector.detectChanges();
  }

  submitCashCloseReport(): void {
    const user = this.auth.currentUser();
    const cashierName = user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email : 'Cajero de Sucursal';
    const diff = this.cashCloseDiscrepancy;
    const status: 'EXACT' | 'SURPLUS' | 'SHORTAGE' = diff === 0 ? 'EXACT' : diff > 0 ? 'SURPLUS' : 'SHORTAGE';
    const code = `Z-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${String(this.cashCloseHistory.length + 1).padStart(3, '0')}`;

    const report: PosCashCloseReport = {
      report_code: code,
      closed_at: new Date().toISOString(),
      branch_name: this.selectedBranchName,
      cashier_name: cashierName,
      shift_label: this.cashCloseShiftLabel,
      opening_float: Number(this.cashCloseOpeningFloat || 0),
      cash_sales_total: Number(this.cashCloseCashSales || 0),
      qr_sales_total: Number(this.cashCloseQrSales || 0),
      card_sales_total: Number(this.cashCloseCardSales || 0),
      exchange_cash_in: Number(this.cashCloseExchangeIn || 0),
      refunds_cash_out: Number(this.cashCloseRefundsOut || 0),
      expected_cash_in_drawer: this.expectedCashInDrawer,
      counted_cash_in_drawer: this.countedCashInDrawer,
      discrepancy: diff,
      status,
      transactions_count: 14,
      notes: this.cashCloseNotes.trim(),
      denominations: this.cashDenominations.map((d) => ({
        label: d.label,
        value: d.value,
        count: Number(d.count || 0),
        subtotal: Number((d.value * Number(d.count || 0)).toFixed(2)),
      })),
    };

    this.cashCloseHistory = [report, ...this.cashCloseHistory];
    this.activeZReport = report;
    this.showZReportModal = true;
    this.message = `Cierre de caja ${code} asentado correctamente. Estado: ${status === 'EXACT' ? 'Cuadre Exacto' : status === 'SURPLUS' ? 'Sobrante' : 'Faltante'}.`;
    this.changeDetector.detectChanges();
  }

  viewZReport(report: PosCashCloseReport): void {
    this.activeZReport = report;
    this.showZReportModal = true;
  }
}
