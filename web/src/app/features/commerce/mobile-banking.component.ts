import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';

import { CommerceService } from '../../core/commerce/commerce.service';

@Component({
  selector: 'app-mobile-banking',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="mobile-banking-viewport">
      <!-- App Header -->
      <header class="bank-app-header">
        <div class="bank-app-brand">
          <div class="bank-logo-badge">
            <span class="material-symbols-outlined">account_balance</span>
          </div>
          <div>
            <h1 class="bank-title">BNB Móvil</h1>
            <span class="bank-subtitle">Banca Digital Interoperable · Simple QR</span>
          </div>
        </div>
        <div class="bank-security-badge">
          <span class="material-symbols-outlined">lock</span>
          <span>SSL ASOBAN</span>
        </div>
      </header>

      <!-- Main Container -->
      <main class="bank-app-content">
        @if (success) {
          <!-- Pantalla de Comprobante Exitoso -->
          <div class="transfer-voucher-card">
            <div class="voucher-status-icon">
              <span class="material-symbols-outlined">check_circle</span>
            </div>
            <h2>¡Transferencia Exitosa!</h2>
            <p class="voucher-subtitle">El débito ha sido procesado y acreditado inmediatamente al comercio.</p>

            <div class="voucher-amount-highlight">
              <small>Monto debitado</small>
              <strong>{{ amount | currency:'BOB':'symbol':'1.2-2' }}</strong>
            </div>

            <div class="voucher-details-grid">
              <div class="voucher-row">
                <span>Beneficiario</span>
                <strong>FashionStore Atelier S.R.L.</strong>
              </div>
              <div class="voucher-row">
                <span>NIT Comercio</span>
                <code>102938475</code>
              </div>
              <div class="voucher-row">
                <span>Banco Destino</span>
                <span>Banco Nacional de Bolivia</span>
              </div>
              <div class="voucher-row">
                <span>N° de Pedido</span>
                <strong>{{ orderNumber }}</strong>
              </div>
              <div class="voucher-row">
                <span>Referencia Simple QR</span>
                <code>{{ ref }}</code>
              </div>
              <div class="voucher-row">
                <span>Fecha y Hora</span>
                <span>{{ receiptDate | date:'dd/MM/yyyy HH:mm:ss' }}</span>
              </div>
            </div>

            <div class="voucher-notice">
              <span class="material-symbols-outlined">info</span>
              <p>Tu compra en <strong>FashionStore</strong> se ha confirmado automáticamente. Ya puedes volver a la pantalla de la tienda.</p>
            </div>

            <a routerLink="/cart" class="bank-return-btn">
              <span class="material-symbols-outlined">arrow_back</span>
              <span>Volver a la tienda</span>
            </a>
          </div>
        } @else {
          <!-- Pantalla de Confirmación de Transferencia -->
          <div class="transfer-confirmation-card">
            <div class="transfer-card-header">
              <span class="material-symbols-outlined">qr_code_scanner</span>
              <div>
                <h3>Transferencia Simple QR</h3>
                <small>Pago a Comercio Certificado</small>
              </div>
            </div>

            <!-- Cuenta de Origen -->
            <div class="bank-account-box">
              <div class="account-header">
                <span class="account-label">Cuenta de Origen</span>
                <span class="account-balance">Saldo Disp: Bs 6,450.00</span>
              </div>
              <div class="account-info">
                <strong>Caja de Ahorro BNB Clásica</strong>
                <code>100-294819-01 · Moneda Nacional</code>
              </div>
            </div>

            <!-- Destinatario -->
            <div class="transfer-summary-box">
              <div class="summary-row">
                <span>Comercio Beneficiario</span>
                <strong>FashionStore Atelier S.R.L.</strong>
              </div>
              <div class="summary-row">
                <span>NIT</span>
                <code>102938475</code>
              </div>
              <div class="summary-row">
                <span>Banco Receptor</span>
                <span>Banco Nacional de Bolivia (BNB)</span>
              </div>
              <div class="summary-row">
                <span>Glosa / Concepto</span>
                <span>Pago Pedido {{ orderNumber }}</span>
              </div>
              <div class="summary-row">
                <span>Ref. Transacción</span>
                <code>{{ ref }}</code>
              </div>
            </div>

            <!-- Total a Transferir -->
            <div class="transfer-amount-display">
              <span>Total a Transferir</span>
              <strong>{{ amount | currency:'BOB':'symbol':'1.2-2' }}</strong>
            </div>

            @if (error) {
              <div class="bank-error-box">
                <span class="material-symbols-outlined">error</span>
                <span>{{ error }}</span>
              </div>
            }

            <!-- Botón de Confirmación -->
            <button
              type="button"
              class="bank-confirm-btn"
              [disabled]="processing || !ref || amount <= 0"
              (click)="confirmTransfer()"
            >
              @if (processing) {
                <span class="material-symbols-outlined spinning">sync</span>
                <span>Procesando transferencia interbancaria...</span>
              } @else {
                <span class="material-symbols-outlined">verified</span>
                <span>Confirmar Transferencia ({{ amount | currency:'BOB':'symbol':'1.2-2' }})</span>
              }
            </button>

            <div class="bank-security-footer">
              <span class="material-symbols-outlined">shield</span>
              <small>Transacción cifrada y respaldada por la red interbancaria ASOBAN y Banco Central de Bolivia.</small>
            </div>
          </div>
        }
      </main>
    </div>
  `,
  styles: [`
    .mobile-banking-viewport {
      min-height: 100vh;
      background: #0f172a;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      flex-direction: column;
    }

    .bank-app-header {
      background: #002b49;
      border-bottom: 2px solid #b8924a;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .bank-app-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .bank-logo-badge {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: #004b7a;
      color: #b8924a;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .bank-logo-badge .material-symbols-outlined {
      font-size: 24px;
    }

    .bank-title {
      font-size: 1.15rem;
      font-weight: 800;
      color: #ffffff;
      margin: 0;
      letter-spacing: 0.04em;
    }

    .bank-subtitle {
      font-size: 0.68rem;
      color: #94a3b8;
      display: block;
    }

    .bank-security-badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: rgba(184, 146, 74, 0.15);
      border: 1px solid rgba(184, 146, 74, 0.35);
      color: #deb86d;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.06em;
    }

    .bank-security-badge .material-symbols-outlined {
      font-size: 14px;
    }

    .bank-app-content {
      flex: 1;
      max-width: 480px;
      width: 100%;
      margin: 0 auto;
      padding: 24px 16px;
    }

    .transfer-confirmation-card, .transfer-voucher-card {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 24px 20px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    .transfer-card-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid #334155;
    }

    .transfer-card-header .material-symbols-outlined {
      font-size: 28px;
      color: #deb86d;
    }

    .transfer-card-header h3 {
      margin: 0;
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
    }

    .transfer-card-header small {
      color: #94a3b8;
      font-size: 0.72rem;
    }

    .bank-account-box {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 18px;
    }

    .account-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .account-label {
      font-size: 0.68rem;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .account-balance {
      font-size: 0.72rem;
      color: #10b981;
      font-weight: 700;
    }

    .account-info strong {
      display: block;
      font-size: 0.88rem;
      color: #ffffff;
      margin-bottom: 2px;
    }

    .account-info code {
      font-size: 0.75rem;
      color: #94a3b8;
    }

    .transfer-summary-box {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 18px;
    }

    .summary-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 7px 0;
      font-size: 0.8rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .summary-row:last-child {
      border-bottom: none;
    }

    .summary-row span:first-child {
      color: #94a3b8;
    }

    .summary-row strong {
      color: #ffffff;
    }

    .summary-row code {
      background: #1e293b;
      padding: 2px 6px;
      border-radius: 4px;
      color: #deb86d;
      font-size: 0.75rem;
    }

    .transfer-amount-display {
      background: #002b49;
      border: 1px solid #004b7a;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .transfer-amount-display span {
      font-size: 0.78rem;
      color: #94a3b8;
      text-transform: uppercase;
      font-weight: 600;
    }

    .transfer-amount-display strong {
      font-size: 1.4rem;
      color: #deb86d;
      font-weight: 800;
    }

    .bank-error-box {
      display: flex;
      align-items: center;
      gap: 10px;
      background: #450a0a;
      border: 1px solid #991b1b;
      color: #fca5a5;
      padding: 12px 16px;
      border-radius: 10px;
      font-size: 0.8rem;
      margin-bottom: 18px;
    }

    .bank-confirm-btn {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 16px 20px;
      border-radius: 12px;
      background: #005a9c;
      color: #ffffff;
      border: none;
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0, 90, 156, 0.4);
      transition: all 0.25s ease;
    }

    .bank-confirm-btn:hover:not(:disabled) {
      background: #006ebf;
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(0, 90, 156, 0.6);
    }

    .bank-confirm-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .bank-security-footer {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      margin-top: 16px;
      color: #64748b;
    }

    .bank-security-footer .material-symbols-outlined {
      font-size: 16px;
      color: #10b981;
      margin-top: 2px;
    }

    .bank-security-footer small {
      font-size: 0.68rem;
      line-height: 1.4;
    }

    /* VOUCHER / COMPROBANTE */
    .transfer-voucher-card {
      text-align: center;
    }

    .voucher-status-icon {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: rgba(16, 185, 129, 0.15);
      color: #10b981;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;
    }

    .voucher-status-icon .material-symbols-outlined {
      font-size: 40px;
    }

    .transfer-voucher-card h2 {
      font-size: 1.35rem;
      font-weight: 800;
      color: #ffffff;
      margin: 0 0 6px 0;
    }

    .voucher-subtitle {
      font-size: 0.8rem;
      color: #94a3b8;
      margin: 0 0 20px 0;
      line-height: 1.4;
    }

    .voucher-amount-highlight {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 20px;
    }

    .voucher-amount-highlight small {
      display: block;
      font-size: 0.72rem;
      color: #94a3b8;
      text-transform: uppercase;
      margin-bottom: 4px;
    }

    .voucher-amount-highlight strong {
      font-size: 1.6rem;
      color: #10b981;
      font-weight: 800;
    }

    .voucher-details-grid {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 20px;
      text-align: left;
    }

    .voucher-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 7px 0;
      font-size: 0.78rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .voucher-row:last-child {
      border-bottom: none;
    }

    .voucher-row span:first-child {
      color: #94a3b8;
    }

    .voucher-row strong {
      color: #ffffff;
    }

    .voucher-row code {
      background: #1e293b;
      padding: 2px 6px;
      border-radius: 4px;
      color: #deb86d;
      font-size: 0.75rem;
    }

    .voucher-notice {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      background: rgba(184, 146, 74, 0.1);
      border: 1px solid rgba(184, 146, 74, 0.3);
      padding: 12px 14px;
      border-radius: 10px;
      text-align: left;
      margin-bottom: 24px;
    }

    .voucher-notice .material-symbols-outlined {
      color: #deb86d;
      font-size: 20px;
      margin-top: 2px;
    }

    .voucher-notice p {
      margin: 0;
      font-size: 0.75rem;
      line-height: 1.4;
      color: #f1f5f9;
    }

    .bank-return-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 14px 24px;
      border-radius: 12px;
      background: #334155;
      color: #ffffff;
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 700;
      transition: background 0.2s ease;
      width: 100%;
    }

    .bank-return-btn:hover {
      background: #475569;
    }

    .spinning {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      100% { transform: rotate(360deg); }
    }
  `],
})
export class MobileBankingComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly commerceService = inject(CommerceService);

  ref = '';
  amount = 0;
  orderNumber = '';
  processing = false;
  success = false;
  error: string | null = null;
  receiptDate: Date = new Date();

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.ref = params['ref'] || '';
      this.amount = parseFloat(params['amount'] || '0');
      this.orderNumber = params['order'] || '';
    });
  }

  confirmTransfer(): void {
    if (!this.ref || this.amount <= 0) {
      this.error = 'Datos de transferencia incompletos.';
      return;
    }

    this.processing = true;
    this.error = null;

    this.commerceService.confirmQrTransfer(this.ref, this.amount).subscribe({
      next: () => {
        this.processing = false;
        this.success = true;
        this.receiptDate = new Date();
      },
      error: (err) => {
        this.processing = false;
        this.error = err?.error?.detail || 'No se pudo procesar la transferencia bancaria.';
      },
    });
  }
}
