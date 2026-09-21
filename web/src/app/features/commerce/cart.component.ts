import { CurrencyPipe, DatePipe } from '@angular/common';
import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subscription, catchError, finalize, firstValueFrom, interval, of, switchMap, timeout } from 'rxjs';

import { CommerceService } from '../../core/commerce/commerce.service';
import { Cart, DigitalPurchaseOptions, FulfillmentType, QRPaymentResponse, ShippingDetails } from '../../core/models/admin.models';
import { CatalogFilterOption } from '../../core/models/api.models';
import { CatalogService } from '../../core/catalog/catalog.service';
import { appConfig } from '../../core/config/app-config';

declare const window: any;

export interface ConfirmedOrderItem {
  product_name: string;
  size_name?: string;
  color_name?: string;
  sku?: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface ConfirmedOrderDetails {
  orderNumber: string;
  saleId?: number;
  total: number;
  subtotal: number;
  discount: number;
  paymentMethod: 'STRIPE' | 'QR' | 'DEMO';
  branchName: string;
  createdAt: string | Date;
  items: ConfirmedOrderItem[];
  paymentMethodLabel: string;
  paymentTitle: string;
  paymentDescription: string;
  fulfillmentType: FulfillmentType;
  shippingDetails?: ShippingDetails | null;
}

@Component({
  standalone: true,
  imports: [CurrencyPipe, DatePipe, FormsModule, RouterLink],
  template: `
    <section class="operations-page commerce-page">
      @if (!isOrderConfirmed) {
        <div class="admin-heading">
          <div>
            <p class="eyebrow">Tu selección</p>
            <h2>Carrito de compras</h2>
            <p class="admin-subtitle">Revisa tus prendas, selecciona la sucursal de retiro y elige tu pasarela de pago preferida.</p>
          </div>
        </div>

        @if (message) {
          <p class="checkout-feedback checkout-feedback-error">{{ message }}</p>
        }

        @if (loading) {
          <p class="loading page-message">Cargando carrito...</p>
        }

        @if (!loading && cart && !cart.items.length) {
          <div class="cart-result-card">
            <div class="cart-result-icon">
              <span class="material-symbols-outlined">shopping_bag</span>
            </div>
            <span class="panel-index">TU SELECCIÓN</span>
            <h3>Tu carrito está vacío.</h3>
            <p>Explora la colección y encuentra una pieza para añadirla a tu selección.</p>
            <a class="button button-dark" routerLink="/catalog">
              Ver colección
              <span class="material-symbols-outlined">arrow_forward</span>
            </a>
          </div>
        }

        @if (!loading && cart?.items?.length) {
        <div class="cart-checkout-stack">
          <!-- Tabla de Artículos en Carrito -->
          <div class="operations-table-card">
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Precio</th>
                    <th>Cantidad</th>
                    <th>Total</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  @for (item of cart!.items; track item.id) {
                    <tr>
                      <td>
                        <strong>{{ item.product_name }}</strong>
                        <small>{{ item.size_name }} · {{ item.color_name }} · {{ item.sku }}</small>
                      </td>
                      <td>{{ item.unit_price | currency:'BOB':'symbol':'1.2-2' }}</td>
                      <td>
                        <input
                          class="stock-input"
                          type="number"
                          min="1"
                          [value]="item.quantity"
                          (change)="update(item.id, $any($event.target).value)"
                        />
                      </td>
                      <td>{{ item.line_total | currency:'BOB':'symbol':'1.2-2' }}</td>
                      <td>
                        <button class="small-button" type="button" (click)="remove(item.id)">Eliminar</button>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>

            <!-- Resumen y Selección de Sucursal -->
            <div class="checkout-summary">
              <div class="checkout-summary-heading">
                <div>
                  <span class="panel-index">01 · REVISIÓN</span>
                  <h3>Finalizar compra</h3>
                </div>
                <span class="material-symbols-outlined">shopping_bag</span>
              </div>
              <div class="checkout-total">
                <span>Total a pagar</span>
                <strong>{{ cart!.total | currency:'BOB':'symbol':'1.2-2' }}</strong>
              </div>
              <div class="payment-tabs-bar" role="radiogroup" aria-label="Tipo de entrega">
                <button type="button" class="payment-tab-btn" [class.active]="fulfillmentType === 'PICKUP'" (click)="setFulfillmentType('PICKUP')">
                  <span class="material-symbols-outlined">storefront</span>
                  <div><strong>Retiro en tienda</strong><small>Sin costo adicional</small></div>
                </button>
                <button type="button" class="payment-tab-btn" [class.active]="fulfillmentType === 'DELIVERY'" (click)="setFulfillmentType('DELIVERY')">
                  <span class="material-symbols-outlined">local_shipping</span>
                  <div><strong>Delivery</strong><small>Sin costo adicional · la sucursal reserva inventario</small></div>
                </button>
              </div>
              <label class="checkout-branch">
                <span>{{ fulfillmentType === 'DELIVERY' ? 'Sucursal de origen para inventario' : 'Sucursal de retiro' }}</span>
                <small>{{ fulfillmentType === 'DELIVERY' ? 'Elegí la tienda que preparará tu pedido para delivery.' : 'Selecciona la tienda donde retirarás tu pedido.' }}</small>
                <select [(ngModel)]="branchId" (change)="onBranchChange()">
                  <option [ngValue]="null">Selecciona una sucursal</option>
                  @for (branch of branches; track branch.id) {
                    <option [ngValue]="branch.id">{{ branch.name }}</option>
                  }
                </select>
              </label>

              @if (fulfillmentType === 'DELIVERY') {
                <div class="checkout-summary delivery-form">
                  <span class="panel-index">DATOS DE DELIVERY</span>
                  <label>Nombre del destinatario<input type="text" [(ngModel)]="shippingDetails.recipient_name" /></label>
                  <label>CI<input type="text" [(ngModel)]="shippingDetails.recipient_ci" /></label>
                  <label>Teléfono<input type="tel" [(ngModel)]="shippingDetails.recipient_phone" /></label>
                  <label>Departamento/Ciudad<input type="text" [(ngModel)]="shippingDetails.department_or_city" /></label>
                  <label>Zona<input type="text" [(ngModel)]="shippingDetails.zone" /></label>
                  <label>Calle<input type="text" [(ngModel)]="shippingDetails.street" /></label>
                  <label>Número de casa<input type="text" [(ngModel)]="shippingDetails.house_number" /></label>
                  <label>Referencia<input type="text" [(ngModel)]="shippingDetails.reference" /></label>
                  <small class="checkout-required"><span class="material-symbols-outlined">info</span>El delivery no tiene costo adicional; el total se mantiene igual.</small>
                </div>
              }

              @if (!branchId) {
                <small class="checkout-required">
                  <span class="material-symbols-outlined">info</span>
                  Selecciona una sucursal para activar las opciones de pago.
                </small>
              }
            </div>
          </div>

          <!-- Selector de Método de Pago: Tarjeta vs Código QR -->
          <div class="payment-method-selector-card">
            <div class="payment-selector-header">
              <span class="panel-index">02 · MÉTODO DE PAGO</span>
              <h3>¿Cómo deseas pagar tu pedido?</h3>
              <p>Selecciona tu pasarela preferida para concretar la compra.</p>
            </div>

            <div class="payment-tabs-bar" role="tablist">
              <button
                type="button"
                class="payment-tab-btn"
                [class.active]="activePaymentMethod === 'QR'"
                (click)="setPaymentMethod('QR')"
              >
                <span class="material-symbols-outlined">qr_code_2</span>
                <div>
                  <strong>Pago con Código QR</strong>
                  <small>Simple QR · Banco Móvil (BNB, BCP, etc.)</small>
                </div>
              </button>

              <button
                type="button"
                class="payment-tab-btn"
                [class.active]="activePaymentMethod === 'STRIPE'"
                (click)="setPaymentMethod('STRIPE')"
              >
                <span class="material-symbols-outlined">credit_card</span>
                <div>
                  <strong>Tarjeta de Crédito / Débito</strong>
                  <small>Pasarela Internacional Stripe</small>
                </div>
              </button>
            </div>
          </div>

          <!-- VISTA 1: PASARELA PAGO CON CÓDIGO QR (SIMPLE QR BOLIVIA) -->
          @if (activePaymentMethod === 'QR') {
            <div class="qr-payment-panel">
              <div class="qr-panel-top-banner">
                <div class="qr-brand-heading">
                  <div class="qr-badge-icon">
                    <span class="material-symbols-outlined">qr_code_scanner</span>
                  </div>
                  <div>
                    <span class="panel-index">PASARELA SIMPLE QR · INTERBANCARIO</span>
                    <h4>Pago Móvil Inmediato con Código QR</h4>
                  </div>
                </div>
                <div class="qr-status-indicator">
                  <span class="live-pulse-dot"></span>
                  <span>QR ACTIVO · VENCE EN {{ countdownTimer }}</span>
                </div>
              </div>

              @if (!branchId) {
                <div class="qr-notice-card">
                  <span class="material-symbols-outlined">info</span>
                  <p>Por favor, selecciona primero una <strong>Sucursal de retiro</strong> en la sección superior para generar el código QR con tu pedido.</p>
                </div>
              } @else if (loadingQr) {
                <div class="qr-loading-box">
                  <span class="material-symbols-outlined spinning">sync</span>
                  <p>Generando código QR dinámico oficial para tu pedido...</p>
                </div>
              } @else if (qrData) {
                <div class="qr-showcase-grid">
                  <!-- Columna Izquierda: Tarjeta QR Escaneable -->
                  <div class="qr-display-box">
                    <div class="simple-qr-header">
                      <span class="simple-qr-tag">SIMPLE QR</span>
                      <small>PAGO INTEROPERABLE</small>
                    </div>

                    <div class="qr-image-container">
                      <img [src]="qrData.qr_image_url" alt="Código QR de Pago FashionStore" class="qr-scannable-image" />
                      <div class="qr-medallion-overlay">F</div>
                    </div>

                    <div class="qr-total-display">
                      <span>Total a pagar</span>
                      <strong>{{ qrData.amount | currency:'BOB':'symbol':'1.2-2' }}</strong>
                    </div>

                    <small class="qr-scan-prompt">Abre tu app bancaria (BNB, BCP, GanaMóvil, Banco Unión) y escanea este código.</small>
                  </div>

                  <!-- Columna Derecha: Datos Bancarios & Simulador Interactivo -->
                  <div class="qr-details-and-simulator">
                    <!-- Datos Oficiales de la Transferencia -->
                    <div class="qr-bank-details-card">
                      <h5>Datos de la Transferencia Bancaria</h5>
                      <div class="qr-data-row">
                        <span>Beneficiario:</span>
                        <strong>{{ qrData.business_name }}</strong>
                      </div>
                      <div class="qr-data-row">
                        <span>NIT del Comercio:</span>
                        <code>{{ qrData.nit }}</code>
                      </div>
                      <div class="qr-data-row">
                        <span>Banco Receptor:</span>
                        <strong>{{ qrData.bank_name }}</strong>
                      </div>
                      <div class="qr-data-row">
                        <span>Glosa / Referencia:</span>
                        <code>Pago Pedido {{ qrData.order_number }}</code>
                      </div>
                      <div class="qr-data-row">
                        <span>Sucursal Asignada:</span>
                        <span>{{ getBranchName(branchId) }}</span>
                      </div>
                    </div>

                    <!-- PANEL DE VERIFICACIÓN EN VIVO (ESTÁNDAR DE PASARELA OFICIAL) -->
                    <div class="qr-bank-simulator-panel qr-live-status-card">
                      <div class="simulator-header">
                        <div class="simulator-icon">
                          <span class="material-symbols-outlined">sync_saved_locally</span>
                        </div>
                        <div>
                          <h6>Esperando confirmación bancaria</h6>
                          <small>Red Interbancaria ASOBAN · Verificación en tiempo real</small>
                        </div>
                        <span class="live-status-pill">
                          <span class="live-pulse-dot"></span>
                          EN VIVO
                        </span>
                      </div>

                      <p class="simulator-desc">
                        Escanea el código QR desde la cámara de tu celular o tu app bancaria (BNB, BCP, GanaMóvil). Cuando completes la transferencia, la confirmación se detectará automáticamente.
                      </p>

                      @if (cardError) {
                        <div class="stripe-error-banner">
                          <span class="material-symbols-outlined">error</span>
                          <span>{{ cardError }}</span>
                        </div>
                      }

                      <button
                        type="button"
                        class="button button-dark qr-simulate-btn"
                        [disabled]="paying"
                        (click)="confirmBankTransfer()"
                      >
                        <span class="material-symbols-outlined" [class.spinning]="paying">
                          {{ paying ? 'sync' : 'check_circle' }}
                        </span>
                        <span>{{ paying ? 'Verificando acreditación...' : 'Ya realicé la transferencia' }}</span>
                      </button>

                      <div class="qr-device-assist">
                        <a [href]="mobileBankingUrl" target="_blank" class="qr-mobile-shortcut-btn">
                          <span class="material-symbols-outlined">smartphone</span>
                          <span>Abrir Banca Móvil en este equipo</span>
                        </a>
                      </div>

                      <div class="simulator-footer">
                        <span class="material-symbols-outlined">verified_user</span>
                        <small>Pago protegido por el sistema de pagos interoperables de Bolivia.</small>
                      </div>
                    </div>
                  </div>
                </div>
              }
            </div>
          }

          <!-- VISTA 2: PASARELA TARJETA STRIPE ELEMENTS -->
          @if (activePaymentMethod === 'STRIPE') {
            @if (isStripeEnabled) {
              <div class="stripe-payment-panel stripe-elements-card">
                <div class="stripe-panel-heading">
                  <div class="stripe-icon">
                    <span class="material-symbols-outlined">credit_card</span>
                  </div>
                  <div>
                    <span class="panel-index">PASARELA DE PAGO INTERNACIONAL</span>
                    <strong>Pago Seguro con Tarjeta (Stripe Elements)</strong>
                  </div>
                  <span class="stripe-secure-badge">
                    <span class="material-symbols-outlined">verified_user</span>
                    SSL 256-bit
                  </span>
                </div>

                <p class="stripe-panel-desc">
                  Ingresa los datos de tu tarjeta de crédito o débito. La transacción se procesa directamente a través de los servidores cifrados de Stripe.
                </p>

                <!-- Tarjetas aceptadas -->
                <div class="stripe-accepted-badges">
                  <span class="card-brand-pill">VISA</span>
                  <span class="card-brand-pill">MASTERCARD</span>
                  <span class="card-brand-pill">AMERICAN EXPRESS</span>
                  <span class="card-brand-pill">DÉBITO / CRÉDITO</span>
                </div>

                <!-- Montura del Stripe Card Element -->
                <div class="stripe-mount-wrapper" [class.mount-error]="!!cardError">
                  @if (!isStripeReady) {
                    <div class="stripe-loading-text">
                      <span class="material-symbols-outlined spinning">sync</span>
                      <span>Cargando formulario seguro de tarjeta...</span>
                    </div>
                  }
                  <div id="stripe-card-element" [style.display]="isStripeReady ? 'block' : 'none'"></div>
                </div>

                @if (cardError) {
                  <div class="stripe-error-banner">
                    <span class="material-symbols-outlined">error</span>
                    <span>{{ cardError }}</span>
                  </div>
                }

                <button
                  class="button button-dark stripe-pay-button"
                  type="button"
                  [disabled]="!branchId || paying || !isStripeReady"
                  (click)="payWithStripe()"
                >
                  <span class="material-symbols-outlined" [class.spinning]="paying">lock</span>
                  {{ paying ? 'Procesando pago en Stripe...' : ('Pagar ' + (cart!.total | currency:'BOB':'symbol':'1.2-2') + ' con Stripe') }}
                  <span class="material-symbols-outlined">arrow_forward</span>
                </button>

                <div class="stripe-security-footer">
                  <span class="material-symbols-outlined">lock</span>
                  <small>Tus datos financieros no son almacenados en nuestros servidores. Protegido por Stripe PCI-DSS Level 1.</small>
                </div>
              </div>
            } @else {
              <!-- Modo Demo / Sandbox -->
              <div class="payment-pending stripe-payment-panel">
                <div class="stripe-panel-heading">
                  <div class="stripe-icon"><span class="material-symbols-outlined">credit_card</span></div>
                  <div>
                    <span class="panel-index">02 · PAGO ELECTRÓNICO</span>
                    <strong>Pagar en Modo Demostración</strong>
                  </div>
                  <span class="stripe-demo-badge">DEMO</span>
                </div>
                <p>Completa tu compra de forma segura en el entorno de demostración académica.</p>
                <button
                  class="button button-dark stripe-pay-button"
                  type="button"
                  [disabled]="!branchId || paying"
                  (click)="demoCheckout()"
                >
                  <span class="material-symbols-outlined">lock</span>
                  {{ paying ? 'Procesando pago...' : 'Pagar en Sandbox (Demo)' }}
                  <span class="material-symbols-outlined">arrow_forward</span>
                </button>
              </div>
            }
          }
        </div>
      }
    } @else {
      <!-- PANTALLA NOVEDOSA, ELEGANTE Y AMIGABLE DE COMPRA CONFIRMADA -->
      <div class="order-confirmation-experience">
        <!-- Hero Celebration Card -->
        <div class="confirmation-hero-card">
          <div class="hero-confetti-accent">
            <div class="hero-status-ring">
              <div class="hero-check-circle">
                <span class="material-symbols-outlined">verified</span>
              </div>
            </div>
          </div>

          <div class="hero-headline-block">
            <span class="hero-kicker-badge">
              <span class="material-symbols-outlined">diamond</span>
              <span>FashionStore Atelier · Compra Exitosa</span>
            </span>
            <h1 class="hero-main-title">¡Gracias por tu compra!</h1>
            <p class="hero-desc-text">
              Tu transacción ha sido procesada de manera segura. Hemos registrado tu pedido y nuestro equipo de atelier ya se encuentra preparándolo para tu retiro.
            </p>
          </div>

          <!-- Order Reference Box con botón Copiar -->
          <div class="order-id-highlight-box">
            <div class="order-id-label-wrap">
              <span class="order-meta-label">CÓDIGO DE ORDEN OFICIAL</span>
              <strong class="order-code-text">{{ confirmedOrderDetails.orderNumber }}</strong>
            </div>
            <button
              type="button"
              class="copy-code-btn"
              (click)="copyOrderCode(confirmedOrderDetails.orderNumber)"
              title="Copiar código al portapapeles"
            >
              <span class="material-symbols-outlined">{{ copiedCode ? 'check' : 'content_copy' }}</span>
              <span>{{ copiedCode ? '¡Copiado!' : 'Copiar' }}</span>
            </button>
          </div>
        </div>

        <!-- Timeline de Progreso del Pedido (Novedoso y Amigable) -->
        <div class="order-timeline-card">
          <div class="timeline-step step-completed">
            <div class="step-icon-bubble">
              <span class="material-symbols-outlined">check</span>
            </div>
            <div class="step-content">
              <strong>Pago Verificado</strong>
              <small>{{ confirmedOrderDetails.paymentMethodLabel }}</small>
            </div>
          </div>
          <div class="timeline-connector completed"></div>

          <div class="timeline-step step-active">
            <div class="step-icon-bubble pulsing">
              <span class="material-symbols-outlined">checkroom</span>
            </div>
            <div class="step-content">
              <strong>En Preparación</strong>
              <small>Empaque de boutique</small>
            </div>
          </div>
          <div class="timeline-connector"></div>

          <div class="timeline-step step-upcoming">
            <div class="step-icon-bubble">
              <span class="material-symbols-outlined">storefront</span>
            </div>
            <div class="step-content">
              <strong>{{ confirmedOrderDetails.fulfillmentType === 'DELIVERY' ? 'Delivery Solicitado' : 'Listo para Retiro' }}</strong>
              <small>{{ confirmedOrderDetails.fulfillmentType === 'DELIVERY' ? deliverySummary(confirmedOrderDetails.shippingDetails) : confirmedOrderDetails.branchName }}</small>
            </div>
          </div>
        </div>

        <!-- Cuadrícula de Dos Columnas: Logística de Retiro y Recibo Digital -->
        <div class="confirmation-two-col-grid">
          <!-- Columna Izquierda: Logística, Respaldo y Concierge -->
          <div class="confirmation-info-column">
            <!-- Sucursal de Retiro -->
            <div class="luxury-info-panel branch-pickup-panel">
              <div class="panel-icon-wrap">
                <span class="material-symbols-outlined">storefront</span>
              </div>
              <div class="panel-body">
                <span class="panel-mini-tag">{{ confirmedOrderDetails.fulfillmentType === 'DELIVERY' ? 'DIRECCIÓN DE DELIVERY' : 'PUNTO DE RETIRO SELECCIONADO' }}</span>
                <h3>{{ confirmedOrderDetails.fulfillmentType === 'DELIVERY' ? deliveryRecipient(confirmedOrderDetails.shippingDetails) : confirmedOrderDetails.branchName }}</h3>
                <p class="panel-subtext">
                  {{ confirmedOrderDetails.fulfillmentType === 'DELIVERY' ? deliverySummary(confirmedOrderDetails.shippingDetails) : 'Presenta el código ' + confirmedOrderDetails.orderNumber + ' en caja para retirar tus prendas sin esperas.' }}
                </p>
                <div class="branch-meta-chips">
                  <span class="meta-chip">
                    <span class="material-symbols-outlined">schedule</span>
                    <span>Lun - Sáb: 09:00 a 20:00</span>
                  </span>
                  <span class="meta-chip verified-chip">
                    <span class="material-symbols-outlined">verified</span>
                    <span>Reserva en mostrador activa</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- Respaldo de Pago -->
            <div class="luxury-info-panel payment-info-panel">
              <div class="panel-icon-wrap">
                <span class="material-symbols-outlined">verified_user</span>
              </div>
              <div class="panel-body">
                <span class="panel-mini-tag">MÉTODO DE PAGO</span>
                <div class="payment-method-row">
                  <strong>{{ confirmedOrderDetails.paymentTitle }}</strong>
                  <span class="payment-badge-pill">Aprobado</span>
                </div>
                <p class="panel-subtext">
                  {{ confirmedOrderDetails.paymentDescription }}
                </p>
                <small class="secure-footer-text">
                  <span class="material-symbols-outlined">lock</span>
                  <span>Transacción respaldada con cifrado SSL 256-bit y registro de auditoría</span>
                </small>
              </div>
            </div>

            <!-- Concierge Sofía IA -->
            <div class="luxury-info-panel concierge-panel">
              <div class="concierge-avatar">
                <span class="material-symbols-outlined">smart_toy</span>
              </div>
              <div class="panel-body">
                <h4>¿Deseas consultar sobre tu pedido?</h4>
                <p>Sofía, nuestra asistente virtual de boutique, puede orientarte sobre el estado de tu retiro o resolver cualquier inquietud.</p>
                <button type="button" class="concierge-action-btn" (click)="triggerSofiaChat()">
                  <span class="material-symbols-outlined">chat</span>
                  <span>Conversar con Sofía IA</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Columna Derecha: Recibo Digital Haute-Couture -->
          <div class="confirmation-receipt-column">
            <div class="luxury-digital-ticket">
              <div class="ticket-header">
                <div class="ticket-brand">
                  <strong>FASHIONSTORE</strong>
                  <small>COMPROBANTE OFICIAL DE PAGO · {{ confirmedOrderDetails.createdAt | date:'dd/MM/yyyy HH:mm' }}</small>
                </div>
                <span class="ticket-stamp">PAGADO</span>
              </div>

              <!-- Lista de Prendas Compradas -->
              <div class="ticket-items-list">
                @for (item of confirmedOrderDetails.items; track item.product_name + $index) {
                  <div class="ticket-item-row">
                    <div class="ticket-item-avatar">
                      <span class="material-symbols-outlined">apparel</span>
                    </div>
                    <div class="ticket-item-details">
                      <strong>{{ item.product_name }}</strong>
                      <div class="ticket-item-specs">
                        @if (item.size_name) { <span>Talla: {{ item.size_name }}</span> }
                        @if (item.color_name) { <span>· Color: {{ item.color_name }}</span> }
                        @if (item.sku) { <span>· SKU: {{ item.sku }}</span> }
                      </div>
                      <small class="ticket-unit-calc">{{ item.quantity }} × {{ item.unit_price | currency:'BOB':'symbol':'1.2-2' }}</small>
                    </div>
                    <strong class="ticket-line-total">{{ item.line_total | currency:'BOB':'symbol':'1.2-2' }}</strong>
                  </div>
                }
                @empty {
                  <div class="ticket-item-row">
                    <div class="ticket-item-avatar">
                      <span class="material-symbols-outlined">checkroom</span>
                    </div>
                    <div class="ticket-item-details">
                      <strong>Prendas de Colección Atelier</strong>
                      <small>Orden procesada satisfactoriamente</small>
                    </div>
                    <strong class="ticket-line-total">{{ confirmedOrderDetails.total | currency:'BOB':'symbol':'1.2-2' }}</strong>
                  </div>
                }
              </div>

              <!-- Desglose de Precios -->
              <div class="ticket-totals-section">
                <div class="ticket-calc-row">
                  <span>Subtotal</span>
                  <span>{{ confirmedOrderDetails.subtotal | currency:'BOB':'symbol':'1.2-2' }}</span>
                </div>
                @if (confirmedOrderDetails.discount > 0) {
                  <div class="ticket-calc-row discount-row">
                    <span>Descuento comercial aplicado</span>
                    <span>-{{ confirmedOrderDetails.discount | currency:'BOB':'symbol':'1.2-2' }}</span>
                  </div>
                }
                <div class="ticket-calc-row grand-total-row">
                  <div>
                    <strong>Total Pagado</strong>
                    <small>Moneda oficial bolivianos (BOB)</small>
                  </div>
                  <strong class="grand-total-amount">{{ confirmedOrderDetails.total | currency:'BOB':'symbol':'1.2-2' }}</strong>
                </div>
              </div>

              <div class="ticket-perforated-line"></div>

              <!-- Botones y Acciones del Recibo -->
              <div class="ticket-actions-bar">
                <a routerLink="/purchase-history" class="button button-dark ticket-primary-btn">
                  <span class="material-symbols-outlined">receipt_long</span>
                  <span>Ver en mi Historial de Compras</span>
                  <span class="material-symbols-outlined">arrow_forward</span>
                </a>

                <div class="ticket-secondary-actions">
                  <button type="button" class="ticket-util-btn" (click)="printReceipt()">
                    <span class="material-symbols-outlined">print</span>
                    <span>Imprimir Comprobante</span>
                  </button>
                  <a routerLink="/catalog" class="ticket-util-btn">
                    <span class="material-symbols-outlined">store</span>
                    <span>Seguir Explorando Boutique</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    }
  </section>
  `,
})
export class CartComponent implements OnInit, OnDestroy {
  private readonly commerce = inject(CommerceService);
  private readonly catalog = inject(CatalogService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  cart: Cart | null = null;
  branches: CatalogFilterOption[] = [];
  branchId: number | null = null;
  fulfillmentType: FulfillmentType = 'PICKUP';
  shippingDetails: ShippingDetails = this.emptyShippingDetails();
  loading = true;
  paying = false;
  message = '';
  cardError = '';
  isStripeReady = false;

  confirmedOrder: ConfirmedOrderDetails | null = null;
  copiedCode = false;

  get isOrderConfirmed(): boolean {
    return Boolean(this.confirmedOrder || (this.message && this.message.includes('confirmad')));
  }

  get confirmedOrderDetails(): ConfirmedOrderDetails {
    if (this.confirmedOrder) {
      return this.confirmedOrder;
    }

    const orderMatch = this.message.match(/Pedido\s+(FS-[\w-]+)/i) || this.message.match(/Demostración\s+(FS-[\w-]+)/i);
    const orderNumber = orderMatch ? orderMatch[1] : 'FS-' + Date.now().toString(36).toUpperCase();

    const branchMatch = this.message.match(/Retiro en\s+([^.]+)/i);
    const branchName = branchMatch ? branchMatch[1].trim() : this.getBranchName(this.branchId);

    const isStripe = this.message.toLowerCase().includes('stripe');
    const isQr = this.message.toLowerCase().includes('transferencia') || this.message.toLowerCase().includes('qr');

    return {
      orderNumber,
      total: this.cart?.total || 0,
      subtotal: this.cart?.subtotal || this.cart?.total || 0,
      discount: Math.max(0, (this.cart?.subtotal || 0) - (this.cart?.total || 0)),
      paymentMethod: isStripe ? 'STRIPE' : isQr ? 'QR' : 'DEMO',
      branchName,
      createdAt: new Date(),
      items: (this.cart?.items || []).map((i) => ({
        product_name: i.product_name,
        size_name: i.size_name,
        color_name: i.color_name,
        sku: i.sku,
        quantity: i.quantity,
        unit_price: Number(i.unit_price),
        line_total: Number(i.line_total),
      })),
      paymentMethodLabel: isStripe ? 'Stripe Internacional' : isQr ? 'Simple QR Bolivia' : 'Modo Demostración',
      paymentTitle: isStripe ? 'Tarjeta de Crédito / Débito (Stripe)' : isQr ? 'Simple QR · Transferencia Móvil' : 'Pago Seguro Sandbox',
      paymentDescription: isStripe
        ? 'Procesado exitosamente mediante tarjeta bancaria con cifrado SSL y certificación PCI-DSS Nivel 1.'
        : isQr
        ? 'Transferencia bancaria validada automáticamente a través de la pasarela Simple QR.'
        : 'Transacción simulada en entorno de pruebas académicas.',
      fulfillmentType: this.fulfillmentType,
      shippingDetails: this.fulfillmentType === 'DELIVERY' ? this.shippingDetails : null,
    };
  }

  private emptyShippingDetails(): ShippingDetails {
    return { recipient_name: '', recipient_ci: '', recipient_phone: '', department_or_city: '', zone: '', street: '', house_number: '', reference: '' };
  }

  setFulfillmentType(type: FulfillmentType): void {
    this.fulfillmentType = type;
    this.cardError = '';
    this.message = '';
    this.qrData = null;
    this.stopQrPolling();
    if (type === 'PICKUP') {
      this.shippingDetails = this.emptyShippingDetails();
    }
    if (this.activePaymentMethod === 'QR' && this.branchId && this.cart?.items?.length && this.validateCheckout(false)) {
      this.prepareQrPayment();
    }
  }

  buildDigitalPurchaseOptions(): DigitalPurchaseOptions | undefined {
    if (this.fulfillmentType !== 'DELIVERY') return undefined;
    return { fulfillment_type: 'DELIVERY', shipping_details: { ...this.shippingDetails } };
  }

  validateCheckout(showMessage = true): boolean {
    if (!this.branchId || !this.cart) {
      if (showMessage) this.message = 'Selecciona una sucursal para activar las opciones de pago.';
      return false;
    }
    if (this.fulfillmentType !== 'DELIVERY') return true;
    const labels: Record<keyof ShippingDetails, string> = {
      recipient_name: 'nombre del destinatario',
      recipient_ci: 'CI',
      recipient_phone: 'teléfono',
      department_or_city: 'departamento o ciudad',
      zone: 'zona',
      street: 'calle',
      house_number: 'número de casa',
      reference: 'referencia',
    };
    const missing = (Object.keys(labels) as (keyof ShippingDetails)[]).filter((key) => !String(this.shippingDetails[key] || '').trim());
    if (missing.length) {
      if (showMessage) this.message = `Completá los datos de delivery: ${missing.map((key) => labels[key]).join(', ')}.`;
      return false;
    }
    return true;
  }

  deliveryRecipient(details?: ShippingDetails | null): string {
    return details?.recipient_name || 'Destinatario de delivery';
  }

  deliverySummary(details?: ShippingDetails | null): string {
    if (!details) return 'Delivery a coordinar.';
    return `${details.street} ${details.house_number}, ${details.zone}, ${details.department_or_city}. Tel: ${details.recipient_phone}. Ref: ${details.reference}.`;
  }

  private deliveryMessageSuffix(branchName: string): string {
    return this.fulfillmentType === 'DELIVERY' ? ` Delivery desde ${branchName}.` : ` Retiro en ${branchName}.`;
  }

  copyOrderCode(code: string): void {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(code).then(() => {
        this.copiedCode = true;
        this.changeDetector.detectChanges();
        setTimeout(() => {
          this.copiedCode = false;
          this.changeDetector.detectChanges();
        }, 2500);
      });
    }
  }

  printReceipt(): void {
    if (typeof window !== 'undefined') {
      window.print();
    }
  }

  triggerSofiaChat(): void {
    const trigger = document.querySelector('.ai-trigger-button') as HTMLButtonElement | null;
    if (trigger) {
      trigger.click();
    }
  }

  activePaymentMethod: 'STRIPE' | 'QR' = 'QR';

  // QR State
  qrData: QRPaymentResponse | null = null;
  loadingQr = false;
  countdownSeconds = 900; // 15 minutos
  countdownTimer = '15:00';
  private timerInterval: any = null;
  private qrPollSubscription?: Subscription;

  get mobileBankingUrl(): string {
    if (!this.qrData) return '#';
    const origin = typeof window !== 'undefined' ? window.location.origin : 'http://192.168.0.7:4200';
    return `${origin}/banca-movil?ref=${this.qrData.transaction_reference}&amount=${this.qrData.amount}&order=${this.qrData.order_number}`;
  }

  // Stripe State
  private stripe: any = null;
  private cardElement: any = null;
  private elements: any = null;

  readonly isStripeEnabled = appConfig.paymentProvider === 'STRIPE' && !!appConfig.stripePublishableKey;

  ngOnInit(): void {
    this.load();
    this.startCountdown();
    this.catalog.filters().pipe(timeout({ each: 10000 })).subscribe({
      next: (filters) => {
        this.branches = filters.branches;
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.message = 'No se pudieron cargar las sucursales disponibles.';
        this.changeDetector.detectChanges();
      },
    });
  }

  ngOnDestroy(): void {
    if (this.cardElement) {
      try {
        this.cardElement.destroy();
      } catch {}
      this.cardElement = null;
    }
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    this.stopQrPolling();
  }

  private startCountdown(): void {
    if (this.timerInterval) clearInterval(this.timerInterval);
    this.countdownSeconds = 900;
    this.timerInterval = setInterval(() => {
      if (this.countdownSeconds > 0) {
        this.countdownSeconds--;
        const mins = Math.floor(this.countdownSeconds / 60).toString().padStart(2, '0');
        const secs = (this.countdownSeconds % 60).toString().padStart(2, '0');
        this.countdownTimer = `${mins}:${secs}`;
        this.changeDetector.detectChanges();
      } else {
        clearInterval(this.timerInterval);
      }
    }, 1000);
  }

  setPaymentMethod(method: 'STRIPE' | 'QR'): void {
    if (this.activePaymentMethod !== method) {
      this.stopQrPolling();
    }
    this.activePaymentMethod = method;
    this.cardError = '';
    this.changeDetector.detectChanges();

    if (method === 'QR' && this.branchId && !this.qrData) {
      this.prepareQrPayment();
    } else if (method === 'STRIPE' && this.isStripeEnabled) {
      this.isStripeReady = false;
      setTimeout(() => this.initStripeElements(), 60);
    }
  }

  load(clearMessage = true): void {
    this.loading = true;
    if (clearMessage) this.message = '';
    this.commerce.cart().pipe(
      timeout({ each: 10000 }),
      finalize(() => {
        this.loading = false;
        this.changeDetector.detectChanges();
        if (this.activePaymentMethod === 'STRIPE' && this.isStripeEnabled && this.cart?.items?.length) {
          this.isStripeReady = false;
          setTimeout(() => this.initStripeElements(), 60);
        } else if (this.activePaymentMethod === 'QR' && this.branchId && this.cart?.items?.length) {
          this.prepareQrPayment();
        }
      }),
    ).subscribe({
      next: (cart) => {
        this.cart = cart;
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.message = 'No se pudo cargar el carrito. Comprueba tu sesión e inténtalo nuevamente.';
        this.changeDetector.detectChanges();
      },
    });
  }

  onBranchChange(): void {
    this.stopQrPolling();
    this.cardError = '';
    this.qrData = null;
    this.changeDetector.detectChanges();

    if (this.activePaymentMethod === 'QR' && this.branchId) {
      this.prepareQrPayment();
    }
  }

  getBranchName(id: number | null): string {
    return this.branches.find((b) => b.id === id)?.name || 'Sucursal principal';
  }

  update(id: number, quantity: string): void {
    this.commerce.updateCartItem(id, Math.max(1, Number(quantity) || 1)).subscribe({
      next: (cart) => {
        this.cart = cart;
        this.qrData = null;
        this.changeDetector.detectChanges();
        if (this.activePaymentMethod === 'QR' && this.branchId) {
          this.prepareQrPayment();
        }
      },
      error: () => {
        this.message = 'No se pudo actualizar la cantidad.';
        this.changeDetector.detectChanges();
      },
    });
  }

  remove(id: number): void {
    this.stopQrPolling();
    this.commerce.removeCartItem(id).subscribe({
      next: (cart) => {
        this.cart = cart;
        this.qrData = null;
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.message = 'No se pudo eliminar el artículo.';
        this.changeDetector.detectChanges();
      },
    });
  }

  // --- QR PAYMENT LOGIC ---
  async prepareQrPayment(): Promise<void> {
    if (this.loadingQr || !this.validateCheckout()) return;
    this.loadingQr = true;
    this.cardError = '';
    this.changeDetector.detectChanges();

    try {
      // 1. Crear venta digital si aún no se generó
      const sale = await firstValueFrom(this.commerce.digitalPurchase(this.branchId!, this.buildDigitalPurchaseOptions()));

      // 2. Solicitar QR oficial al backend con la URL base del cliente
      const clientBase = typeof window !== 'undefined' ? window.location.origin : 'http://192.168.0.7:4200';
      const qrRes = await firstValueFrom(this.commerce.generateQrPayment(sale.id, clientBase));
      this.qrData = qrRes;
      this.startCountdown();
      this.startQrPolling(qrRes.transaction_reference);
      this.loadingQr = false;
      this.changeDetector.detectChanges();
    } catch (err: any) {
      this.cardError = err?.error?.detail?.message || err?.message || 'No se pudo generar el código QR de pago.';
      this.loadingQr = false;
      this.changeDetector.detectChanges();
    }
  }

  startQrPolling(ref: string): void {
    this.stopQrPolling();
    this.qrPollSubscription = interval(2500).pipe(
      switchMap(() => this.commerce.getQrPaymentStatus(ref)),
      catchError(() => of(null)),
    ).subscribe((status) => {
      if (status && status.is_confirmed) {
        this.stopQrPolling();
        const branchName = this.getBranchName(this.branchId);

        const items: ConfirmedOrderItem[] = (this.cart?.items || []).map((i) => ({
          product_name: i.product_name,
          size_name: i.size_name,
          color_name: i.color_name,
          sku: i.sku,
          quantity: i.quantity,
          unit_price: Number(i.unit_price),
          line_total: Number(i.line_total),
        }));

        this.confirmedOrder = {
          orderNumber: status.order_number,
          saleId: status.sale_id,
          total: Number(status.amount || this.cart?.total || 0),
          subtotal: Number(this.cart?.subtotal || status.amount || 0),
          discount: Math.max(0, (this.cart?.subtotal || 0) - Number(status.amount || this.cart?.total || 0)),
          paymentMethod: 'QR',
          branchName: branchName,
          createdAt: new Date(),
          items,
          paymentMethodLabel: 'Simple QR Bolivia',
          paymentTitle: 'Transferencia Interbancaria QR Simple',
          paymentDescription: 'Transferencia bancaria validada automáticamente a través de la pasarela Simple QR.',
          fulfillmentType: this.fulfillmentType,
          shippingDetails: this.fulfillmentType === 'DELIVERY' ? { ...this.shippingDetails } : null,
        };

        this.message = `¡Transferencia bancaria recibida y confirmada! Pedido ${status.order_number} confirmado.${this.deliveryMessageSuffix(branchName)}`;
        this.qrData = null;
        this.load(false);
        this.changeDetector.detectChanges();
      }
    });
  }

  stopQrPolling(): void {
    if (this.qrPollSubscription) {
      this.qrPollSubscription.unsubscribe();
      this.qrPollSubscription = undefined;
    }
  }

  async confirmBankTransfer(): Promise<void> {
    if (!this.qrData || this.paying) return;
    this.paying = true;
    this.cardError = '';
    this.message = '';
    this.changeDetector.detectChanges();

    try {
      // 1. Verificar si ya fue confirmado externamente (ej. desde el celular)
      const status = await firstValueFrom(this.commerce.getQrPaymentStatus(this.qrData.transaction_reference));
      if (status && status.is_confirmed) {
        this.stopQrPolling();
        const branchName = this.getBranchName(this.branchId);
        const items: ConfirmedOrderItem[] = (this.cart?.items || []).map((i) => ({
          product_name: i.product_name,
          size_name: i.size_name,
          color_name: i.color_name,
          sku: i.sku,
          quantity: i.quantity,
          unit_price: Number(i.unit_price),
          line_total: Number(i.line_total),
        }));

        this.confirmedOrder = {
          orderNumber: status.order_number,
          saleId: status.sale_id,
          total: Number(status.amount || this.cart?.total || 0),
          subtotal: Number(this.cart?.subtotal || status.amount || 0),
          discount: Math.max(0, (this.cart?.subtotal || 0) - Number(status.amount || this.cart?.total || 0)),
          paymentMethod: 'QR',
          branchName: branchName,
          createdAt: new Date(),
          items,
          paymentMethodLabel: 'Simple QR Bolivia',
          paymentTitle: 'Transferencia Interbancaria QR Simple',
          paymentDescription: 'Transferencia bancaria validada automáticamente a través de la pasarela Simple QR.',
          fulfillmentType: this.fulfillmentType,
          shippingDetails: this.fulfillmentType === 'DELIVERY' ? { ...this.shippingDetails } : null,
        };

        this.message = `¡Transferencia bancaria recibida y confirmada! Pedido ${status.order_number} confirmado.${this.deliveryMessageSuffix(branchName)}`;
        this.paying = false;
        this.qrData = null;
        this.load(false);
        this.changeDetector.detectChanges();
        return;
      }

      // 2. Si no, procesar la confirmación bancaria
      const confirmedSale = await firstValueFrom(
        this.commerce.confirmQrTransfer(this.qrData.transaction_reference, this.qrData.amount),
      );
      this.stopQrPolling();
      const branchName = this.getBranchName(this.branchId);
      const items: ConfirmedOrderItem[] = (this.cart?.items || []).map((i) => ({
        product_name: i.product_name,
        size_name: i.size_name,
        color_name: i.color_name,
        sku: i.sku,
        quantity: i.quantity,
        unit_price: Number(i.unit_price),
        line_total: Number(i.line_total),
      }));

      this.confirmedOrder = {
        orderNumber: confirmedSale.order_number,
        saleId: confirmedSale.id,
        total: Number(confirmedSale.total || this.cart?.total || 0),
        subtotal: Number(confirmedSale.subtotal || this.cart?.subtotal || this.cart?.total || 0),
        discount: Number(confirmedSale.discount || Math.max(0, (this.cart?.subtotal || 0) - (this.cart?.total || 0))),
        paymentMethod: 'QR',
        branchName: branchName,
        createdAt: confirmedSale.created_at || new Date(),
        items: items.length > 0 ? items : (confirmedSale.items || []).map((i: any) => ({
          product_name: i.product_name,
          size_name: i.size_name || '',
          color_name: i.color_name || '',
          sku: i.sku || '',
          quantity: i.quantity,
          unit_price: Number(i.unit_price),
          line_total: Number(i.line_total),
        })),
        paymentMethodLabel: 'Simple QR Bolivia',
        paymentTitle: 'Transferencia Interbancaria QR Simple',
        paymentDescription: 'Transferencia verificada en tiempo real mediante QR interbancario de la banca móvil.',
        fulfillmentType: this.fulfillmentType,
        shippingDetails: this.fulfillmentType === 'DELIVERY' ? { ...this.shippingDetails } : null,
      };

      this.message = `¡Transferencia bancaria recibida con éxito! Pedido ${confirmedSale.order_number} confirmado.${this.deliveryMessageSuffix(branchName)}`;
      this.paying = false;
      this.qrData = null;
      this.load(false);
      this.changeDetector.detectChanges();
    } catch (err: any) {
      this.cardError = err?.error?.detail?.message || err?.message || 'Error al validar la transferencia bancaria.';
      this.paying = false;
      this.changeDetector.detectChanges();
    }
  }

  // --- STRIPE PAYMENT LOGIC ---
  private async loadStripeSdk(): Promise<any> {
    if (typeof window !== 'undefined' && window.Stripe) {
      return window.Stripe;
    }
    return new Promise((resolve, reject) => {
      const existingScript = document.getElementById('stripe-js-cdn');
      if (existingScript) {
        existingScript.addEventListener('load', () => resolve(window.Stripe));
        return;
      }
      const script = document.createElement('script');
      script.id = 'stripe-js-cdn';
      script.src = 'https://js.stripe.com/v3/';
      script.async = true;
      script.onload = () => resolve(window.Stripe);
      script.onerror = () => reject(new Error('No se pudo cargar el SDK de Stripe.'));
      document.head.appendChild(script);
    });
  }

  private async initStripeElements(): Promise<void> {
    try {
      const StripeFactory = await this.loadStripeSdk();
      if (!this.stripe) {
        this.stripe = StripeFactory(appConfig.stripePublishableKey);
      }
      if (!this.elements) {
        this.elements = this.stripe.elements();
      }

      if (this.cardElement) {
        try {
          this.cardElement.unmount();
          this.cardElement.destroy();
        } catch {}
        this.cardElement = null;
      }

      const style = {
        base: {
          color: '#1b1c1a',
          fontFamily: "'Plus Jakarta Sans', Arial, sans-serif",
          fontSize: '15px',
          fontSmoothing: 'antialiased',
          '::placeholder': {
            color: '#8d8780',
          },
        },
        invalid: {
          color: '#c00000',
          iconColor: '#c00000',
        },
      };

      this.cardElement = this.elements.create('card', { style, hidePostalCode: true });

      const tryMount = (retries = 8) => {
        const mountEl = document.getElementById('stripe-card-element');
        if (mountEl) {
          mountEl.innerHTML = '';
          this.cardElement.mount('#stripe-card-element');
          this.cardElement.on('change', (event: any) => {
            this.cardError = event.error ? event.error.message : '';
            this.changeDetector.detectChanges();
          });
          this.cardElement.on('ready', () => {
            this.isStripeReady = true;
            this.changeDetector.detectChanges();
          });
          setTimeout(() => {
            this.isStripeReady = true;
            this.changeDetector.detectChanges();
          }, 350);
        } else if (retries > 0) {
          setTimeout(() => tryMount(retries - 1), 60);
        }
      };

      tryMount();
    } catch (err: any) {
      this.cardError = 'No se pudo inicializar la pasarela de Stripe. Verifica tu conexión.';
      this.changeDetector.detectChanges();
    }
  }

  async payWithStripe(): Promise<void> {
    if (!this.validateCheckout() || this.paying || !this.stripe || !this.cardElement) return;
    this.paying = true;
    this.cardError = '';
    this.message = '';

    try {
      // 1. Crear venta digital en backend
      const sale = await firstValueFrom(this.commerce.digitalPurchase(this.branchId!, this.buildDigitalPurchaseOptions()));

      // 2. Crear PaymentIntent en backend
      const idempotencyKey = `stripe-web-${sale.id}-${Date.now()}`;
      const intent = await firstValueFrom(this.commerce.stripePaymentIntent(sale.id, idempotencyKey));

      // 3. Confirmar tarjeta con Stripe.js
      const result = await this.stripe.confirmCardPayment(intent.client_secret, {
        payment_method: {
          card: this.cardElement,
        },
      });

      if (result.error) {
        this.cardError = result.error.message || 'Error al procesar la tarjeta.';
        this.paying = false;
        this.changeDetector.detectChanges();
        return;
      }

      // 4. Confirmar en backend (descontar inventario y vaciar carrito)
      const piId = result.paymentIntent?.id || intent.payment_intent_id;
      const confirmedSale = await firstValueFrom(this.commerce.confirmStripePayment(piId));

      const branchName = this.getBranchName(this.branchId);

      const items: ConfirmedOrderItem[] = (this.cart?.items || []).map((i) => ({
        product_name: i.product_name,
        size_name: i.size_name,
        color_name: i.color_name,
        sku: i.sku,
        quantity: i.quantity,
        unit_price: Number(i.unit_price),
        line_total: Number(i.line_total),
      }));

      this.confirmedOrder = {
        orderNumber: confirmedSale.order_number,
        saleId: confirmedSale.id,
        total: Number(confirmedSale.total || this.cart?.total || 0),
        subtotal: Number(confirmedSale.subtotal || this.cart?.subtotal || this.cart?.total || 0),
        discount: Number(confirmedSale.discount || Math.max(0, (this.cart?.subtotal || 0) - (this.cart?.total || 0))),
        paymentMethod: 'STRIPE',
        branchName: branchName,
        createdAt: confirmedSale.created_at || new Date(),
        items: items.length > 0 ? items : (confirmedSale.items || []).map((i: any) => ({
          product_name: i.product_name,
          size_name: i.size_name || '',
          color_name: i.color_name || '',
          sku: i.sku || '',
          quantity: i.quantity,
          unit_price: Number(i.unit_price),
          line_total: Number(i.line_total),
        })),
        paymentMethodLabel: 'Stripe Internacional',
        paymentTitle: 'Tarjeta de Crédito / Débito (Stripe)',
        paymentDescription: 'Procesado exitosamente mediante tarjeta bancaria con autorización instantánea y certificación PCI-DSS Nivel 1.',
        fulfillmentType: this.fulfillmentType,
        shippingDetails: this.fulfillmentType === 'DELIVERY' ? { ...this.shippingDetails } : null,
      };

      this.message = `¡Pago exitoso con Stripe! Pedido ${confirmedSale.order_number} confirmado.${this.deliveryMessageSuffix(branchName)}`;
      this.paying = false;
      this.load(false);
      this.changeDetector.detectChanges();
    } catch (error: any) {
      this.cardError = error?.error?.detail?.message || error?.message || 'El pago no pudo completarse.';
      this.paying = false;
      this.changeDetector.detectChanges();
    }
  }

  demoCheckout(): void {
    if (!this.validateCheckout() || this.paying) return;
    this.paying = true;
    this.message = '';
    this.commerce.digitalPurchase(this.branchId!, this.buildDigitalPurchaseOptions()).pipe(
      finalize(() => {
        this.paying = false;
        this.changeDetector.detectChanges();
      }),
    ).subscribe({
      next: (sale) => {
        this.commerce.electronicPayment(sale.id, `web-demo-${sale.id}-${Date.now()}`).subscribe({
          next: (payment) => {
            this.commerce.approveSandbox(payment.transaction_reference!, Number(sale.total)).subscribe({
              next: () => {
                const branchName = this.getBranchName(this.branchId);
                const items: ConfirmedOrderItem[] = (this.cart?.items || []).map((i) => ({
                  product_name: i.product_name,
                  size_name: i.size_name,
                  color_name: i.color_name,
                  sku: i.sku,
                  quantity: i.quantity,
                  unit_price: Number(i.unit_price),
                  line_total: Number(i.line_total),
                }));

                this.confirmedOrder = {
                  orderNumber: sale.order_number,
                  saleId: sale.id,
                  total: Number(sale.total),
                  subtotal: Number(sale.subtotal),
                  discount: Number(sale.discount),
                  paymentMethod: 'DEMO',
                  branchName: branchName,
                  createdAt: sale.created_at || new Date(),
                  items,
                  paymentMethodLabel: 'Modo Demostración',
                  paymentTitle: 'Sandbox Académico',
                  paymentDescription: 'Compra confirmada en el entorno de pruebas de FashionStore.',
                  fulfillmentType: this.fulfillmentType,
                  shippingDetails: this.fulfillmentType === 'DELIVERY' ? { ...this.shippingDetails } : null,
                };

                this.message = `Demostración ${sale.order_number} confirmada.`;
                this.load(false);
                this.changeDetector.detectChanges();
              },
              error: () => {
                this.message = 'Error al aprobar demostración.';
                this.changeDetector.detectChanges();
              },
            });
          },
          error: () => {
            this.message = 'Error en pago electrónico demo.';
            this.changeDetector.detectChanges();
          },
        });
      },
      error: (error: { error?: { detail?: { message?: string } } }) => {
        this.message = error.error?.detail?.message || 'El pedido no pudo completarse.';
        this.changeDetector.detectChanges();
      },
    });
  }
}
