import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { vi } from 'vitest';

import { PosComponent } from './pos.component';
import { CommerceService } from '../../core/commerce/commerce.service';
import { AuthService } from '../../core/auth/auth.service';
import { CatalogService } from '../../core/catalog/catalog.service';
import { AdminService } from '../../core/admin/admin.service';
import { OfflineTransactionService } from '../../core/offline/offline-transaction.service';
import { SyncTransactionService } from '../../core/offline/sync-transaction.service';
import { SyncCatalogService } from '../../core/offline/sync-catalog.service';

describe('PosComponent exchange mode', () => {
  let fixture: ComponentFixture<PosComponent>;
  let component: PosComponent;
  let commerce: { lookupSaleForExchange: ReturnType<typeof vi.fn>; exchangeQuote: ReturnType<typeof vi.fn>; finalizeExchange: ReturnType<typeof vi.fn>; lookupReturn: ReturnType<typeof vi.fn>; searchReturnCustomers: ReturnType<typeof vi.fn>; submitReturn: ReturnType<typeof vi.fn>; lookupCreditNote: ReturnType<typeof vi.fn>; settleCreditNote: ReturnType<typeof vi.fn>; physicalSale: ReturnType<typeof vi.fn>; cashPayment: ReturnType<typeof vi.fn>; pushScannerRelay: ReturnType<typeof vi.fn>; popScannerRelay: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    commerce = { lookupSaleForExchange: vi.fn(() => of(null)), exchangeQuote: vi.fn(() => of(null)), finalizeExchange: vi.fn(() => of(null)), lookupReturn: vi.fn(() => of(null)), searchReturnCustomers: vi.fn(() => of([])), submitReturn: vi.fn(() => of(null)), lookupCreditNote: vi.fn(() => of(null)), settleCreditNote: vi.fn(() => of(null)), physicalSale: vi.fn(() => of(null)), cashPayment: vi.fn(() => of(null)), pushScannerRelay: vi.fn(() => of({ queued: true })), popScannerRelay: vi.fn(() => of({ items: [] })) };
    await TestBed.configureTestingModule({
      imports: [PosComponent],
      providers: [
        { provide: CommerceService, useValue: commerce },
        { provide: AuthService, useValue: { currentUser: () => null } },
        { provide: CatalogService, useValue: { filters: () => of({ branches: [] }), list: () => of({ items: [] }) } },
        { provide: AdminService, useValue: { inventoryAll: () => of({ items: [] }) } },
        { provide: OfflineTransactionService, useValue: { listCustomers: () => Promise.resolve([]) } },
        { provide: SyncTransactionService, useValue: { pendingCount: () => 0, isSyncing: () => false } },
        { provide: SyncCatalogService, useValue: { lastSync: () => null, autoSync: vi.fn() } },
      ],
    }).overrideComponent(PosComponent, { set: { template: '' } }).compileComponents();
    fixture = TestBed.createComponent(PosComponent);
    component = fixture.componentInstance;
  });

  it('keeps exchange separate from ordinary return mode', () => {
    expect(component.mode).toBe('SALE');
    component.mode = 'RETURN';
    expect(component.returnValid).toBe(false);
    component.mode = 'EXCHANGE';
    expect(component.mode).toBe('EXCHANGE');
  });

  it('clears loaded sale state when the lookup target changes', () => {
    component.exchangeOrderNumber = 'ORD-42';
    component.exchangeSale = { sale_id: 42, order_number: 'ORD-42', sale_date: '2030-01-01', branch_id: 3, status: 'PAID', items: [] };
    component.exchangeInventoryItems = [{ product_variant_id: 9, available_quantity: 2 } as any];
    component.exchangeReturnedVariantId = 7;
    component.exchangeNewVariantId = 9;
    component.exchangeQuote = {} as any;
    component.exchangeSuccess = { quarantine_id: 1, status: 'EXCHANGED', quarantine_status: 'PENDING' };

    component.onExchangeOrderNumberChange('ORD-43');

    expect(component.exchangeOrderNumber).toBe('ORD-43');
    expect(component.exchangeSale).toBeNull();
    expect(component.exchangeInventoryItems).toEqual([]);
    expect(component.exchangeReturnedVariantId).toBe(0);
    expect(component.exchangeNewVariantId).toBe(0);
    expect(component.exchangeQuote).toBeNull();
    expect(component.exchangeSuccess).toBeNull();
  });

  it('snapshots an ambiguous finalize and replays the exact request without mutation', () => {
    const finalize$ = new Subject<never>();
    commerce.finalizeExchange.mockReturnValue(finalize$);
    component.exchangeSale = { sale_id: 42, order_number: 'ORD-42', sale_date: '2030-01-01', branch_id: 3, status: 'PAID', items: [{ id: 1, variant_id: 7, name: 'Camisa', sku: 'SKU-7', purchased_quantity: 1, net_paid_line_total: 100, remaining_exchangeable_quantity: 1 }] };
    component.exchangeReturnedVariantId = 7;
    component.exchangeNewVariantId = 9;
    component.exchangeReturnedQuantity = 1;
    component.exchangeNewQuantity = 1;
    component.exchangeInventoryItems = [{ product_variant_id: 9, available_quantity: 2 } as any];
    component.exchangeQuote = { returned_value: 100, replacement_unit_price: 100, delivered_value: 100, difference: 0, cash_settlement_eligible: true, available_stock: 2, reserved_stock: 0, expires_at: new Date(Date.now() + 60000).toISOString(), quote_fingerprint: 'fp' };
    (component as any).exchangeQuotedReturnedVariantId = 7;
    (component as any).exchangeQuotedNewVariantId = 9;
    (component as any).exchangeQuotedReturnedQuantity = 1;
    (component as any).exchangeQuotedNewQuantity = 1;

    component.finalizeExchange();
    const firstRequest = commerce.finalizeExchange.mock.calls[0];
    finalize$.error({ status: 503 });
    component.onExchangeOrderNumberChange('OTHER');
    component.onExchangeSelectionChange('newVariant', 55);
    component.finalizeExchange();

    expect(component.exchangePendingRetry).not.toBeNull();
    expect(commerce.finalizeExchange.mock.calls[1]).toEqual(firstRequest);
    expect(component.exchangeOrderNumber).toBe('ORD-42');
    expect(component.exchangeNewVariantId).toBe(9);
  });

  it('does not submit the original or ambiguous retry while offline', () => {
    const originalOnline = navigator.onLine;
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    component.finalizeExchange();
    component.exchangePendingRetry = { saleId: 42, input: { returned_variant_id: 7, returned_quantity: 1, new_variant_id: 9, new_quantity: 1, quote_fingerprint: 'fp', quote_expires_at: '2030-01-01T00:10:00Z', idempotency_key: 'idem-1' } };
    component.finalizeExchange();

    expect(commerce.finalizeExchange).not.toHaveBeenCalled();
    expect(component.message).toContain('online');
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: originalOnline });
  });

  it('rejects zero-stock replacement variants and reports expired quotes', () => {
    component.exchangeSale = { sale_id: 42, order_number: 'ORD-42', sale_date: '2030-01-01', branch_id: 3, status: 'PAID', items: [{ id: 1, variant_id: 7, name: 'Camisa', sku: 'SKU-7', purchased_quantity: 1, net_paid_line_total: 100, remaining_exchangeable_quantity: 1 }] };
    component.exchangeReturnedVariantId = 7;
    component.exchangeNewVariantId = 9;
    component.exchangeInventoryItems = [{ product_variant_id: 9, available_quantity: 0 } as any];
    expect(component.exchangeSelectionValid).toBe(false);
    component.exchangeQuote = { returned_value: 100, replacement_unit_price: 100, delivered_value: 100, difference: 0, cash_settlement_eligible: true, available_stock: 1, reserved_stock: 0, expires_at: new Date(Date.now() - 1000).toISOString(), quote_fingerprint: 'fp' };
    expect(component.exchangeConfirmValid).toBe(false);
    component.finalizeExchange();
    expect(component.message).toContain('vencida');
  });

  it('requires a fresh quote and the appropriate settlement before confirmation', () => {
    component.exchangeSale = { sale_id: 42, order_number: 'ORD-42', sale_date: '2030-01-01', branch_id: 3, status: 'PAID', items: [{ id: 1, variant_id: 7, name: 'Camisa', sku: 'SKU-7', purchased_quantity: 1, net_paid_line_total: 100, remaining_exchangeable_quantity: 1 }] };
    component.exchangeReturnedVariantId = 7;
    component.exchangeNewVariantId = 9;
    component.exchangeReturnedQuantity = 1;
    component.exchangeNewQuantity = 1;
    component.exchangeQuote = { returned_value: 100, replacement_unit_price: 120, delivered_value: 120, difference: 20, cash_settlement_eligible: true, available_stock: 2, reserved_stock: 0, expires_at: new Date(Date.now() + 60000).toISOString(), quote_fingerprint: 'fp' };
    (component as any).exchangeQuotedReturnedVariantId = 7;
    (component as any).exchangeQuotedReturnedQuantity = 1;
    (component as any).exchangeQuotedNewVariantId = 9;
    (component as any).exchangeQuotedNewQuantity = 1;
    expect(component.exchangeConfirmValid).toBe(false);
    component.exchangeCashTendered = 20;
    expect(component.exchangeConfirmValid).toBe(true);
    component.exchangeNewQuantity = 2;
    expect(component.exchangeConfirmValid).toBe(false);
  });

  it('CU13-8: blocks lookup, quote, and finalization while offline without queueing', () => {
    const onlineSpy = vi.spyOn(window.navigator, 'onLine', 'get').mockReturnValue(false);
    try {
      component.exchangeOrderNumber = 'ORD-42';
      component.lookupExchangeSale();
      expect(commerce.lookupSaleForExchange).not.toHaveBeenCalled();
      expect(component.message).toContain('online');

      component.exchangeSale = { sale_id: 42, order_number: 'ORD-42', sale_date: '2030-01-01', branch_id: 3, status: 'PAID', items: [{ id: 1, variant_id: 7, name: 'Camisa', sku: 'SKU-7', purchased_quantity: 1, net_paid_line_total: 100, remaining_exchangeable_quantity: 1 }] };
      component.exchangeInventoryItems = [{ product_variant_id: 9, available_quantity: 2 } as any];
      component.exchangeReturnedVariantId = 7;
      component.exchangeNewVariantId = 9;
      component.requestExchangeQuote();
      expect(commerce.exchangeQuote).not.toHaveBeenCalled();

      component.exchangeQuote = { returned_value: 100, replacement_unit_price: 100, delivered_value: 100, difference: 0, cash_settlement_eligible: true, available_stock: 2, reserved_stock: 0, expires_at: new Date(Date.now() + 60000).toISOString(), quote_fingerprint: 'fp' };
      expect(component.exchangeConfirmValid).toBe(false);
      component.finalizeExchange();
      expect(commerce.finalizeExchange).not.toHaveBeenCalled();
    } finally {
      onlineSpy.mockRestore();
    }
  });

  it('CU13-8: blocks nonzero difference when original sale is not cash-settlement eligible and handles refund receipt', () => {
    component.exchangeSale = { sale_id: 42, order_number: 'ORD-42', sale_date: '2030-01-01', branch_id: 3, status: 'PAID', items: [{ id: 1, variant_id: 7, name: 'Camisa', sku: 'SKU-7', purchased_quantity: 2, net_paid_line_total: 200, remaining_exchangeable_quantity: 2 }] };
    component.exchangeInventoryItems = [{ product_variant_id: 9, available_quantity: 3 } as any];
    component.exchangeReturnedVariantId = 7;
    component.exchangeReturnedQuantity = 1;
    component.exchangeNewVariantId = 9;
    component.exchangeNewQuantity = 1;

    // Ineligible nonzero difference
    component.exchangeQuote = { returned_value: 100, replacement_unit_price: 80, delivered_value: 80, difference: -20, cash_settlement_eligible: false, available_stock: 3, reserved_stock: 0, expires_at: new Date(Date.now() + 60000).toISOString(), quote_fingerprint: 'fp-ineligible' };
    component.exchangeCashierConfirmed = true;
    expect(component.exchangeConfirmValid).toBe(false);

    // Eligible negative difference (cash refund)
    component.exchangeQuote = { returned_value: 100, replacement_unit_price: 80, delivered_value: 80, difference: -20, cash_settlement_eligible: true, available_stock: 3, reserved_stock: 0, expires_at: new Date(Date.now() + 60000).toISOString(), quote_fingerprint: 'fp-refund' };
    component.exchangeCashierConfirmed = false;
    expect(component.exchangeConfirmValid).toBe(false);
    component.exchangeCashierConfirmed = true;
    expect(component.exchangeConfirmValid).toBe(true);

    commerce.finalizeExchange.mockReturnValue(of({
      sale_id: 42,
      order_number: 'ORD-42',
      returned_variant_id: 7,
      returned_quantity: 1,
      new_variant_id: 9,
      new_quantity: 1,
      status: 'EXCHANGED',
      quarantine_id: 15,
      quarantine_status: 'PENDING',
      returned_value: '100.00',
      delivered_value: '80.00',
      difference: '-20.00',
      cash_refunded: '20.00',
      exchanged_at: '2030-01-01T12:00:00Z',
    }));

    component.exchangeReason = 'Cambio a modelo menor precio';
    component.finalizeExchange();

    expect(commerce.finalizeExchange).toHaveBeenCalledWith(42, expect.objectContaining({
      cashier_confirmed: true,
      reason: 'Cambio a modelo menor precio',
    }));
    // Quote must be cleared after confirmation to prevent accidental second submission
    expect(component.exchangeQuote).toBeNull();
    expect(component.exchangeSuccess?.quarantine_id).toBe(15);
    expect(component.exchangeSuccess?.quarantine_status).toBe('PENDING');
    expect(component.exchangeSale?.items[0].remaining_exchangeable_quantity).toBe(1);

    component.resetExchangeFlow();
    expect(component.exchangeSuccess).toBeNull();
    expect(component.exchangeSale).toBeNull();
  });

  it('looks up returns online and preselects the original customer', () => {
    component.returnOrderNumber = 'FS-42';
    commerce.lookupReturn.mockReturnValue(of({ sale_id: 42, order_number: 'FS-42', branch_id: 2, status: 'CONFIRMED', customer_id: 17, items: [{ id: 4, variant_id: 9, name: 'Camisa', sku: 'SKU', purchased_quantity: 2, remaining_returnable_quantity: 2, net_paid_line_total: '20.00' }] }));
    component.lookupReturn();
    expect(commerce.lookupReturn).toHaveBeenCalledWith('FS-42');
    expect(component.returnSale?.customer_id).toBe(17);
    expect(component.returnBeneficiaryCustomerId).toBe(17);
  });

  it('blocks return lookup and submit offline and never queues it', () => {
    const onlineSpy = vi.spyOn(window.navigator, 'onLine', 'get').mockReturnValue(false);
    try {
      component.returnOrderNumber = 'FS-42';
      component.lookupReturn();
      expect(commerce.lookupReturn).not.toHaveBeenCalled();
      expect(component.message).toContain('online');
      component.returnSale = { sale_id: 42, order_number: 'FS-42', sale_date: '2030-01-01', branch_id: 2, status: 'CONFIRMED', customer_id: 17, items: [{ id: 4, variant_id: 9, name: 'Camisa', sku: 'SKU', purchased_quantity: 1, remaining_returnable_quantity: 1, net_paid_line_total: '20.00' }] };
      component.returnReason = 'Talla';
      component.returnItems[4] = { quantity: 1, condition: 'SELLABLE' };
      component.processReturn();
      expect(commerce.submitReturn).not.toHaveBeenCalled();
    } finally { onlineSpy.mockRestore(); }
  });

  it('calculates credit-note due and sends no tender when the note covers the sale', () => {
    component.branchId = 2;
    component.variantId = 9;
    component.quantity = 1;
    component.amount = 20;
    component.creditNoteCode = 'NC-1';
    component.selectedRegisteredCustomerId = 17;
    component.creditNoteBalance = { available_balance: '20.00', customer_id: 17, expires_at: null };
    expect(component.creditNoteAppliedAmount).toBe(20);
    expect(component.creditNoteRemainingDue).toBe(0);
    commerce.physicalSale.mockReturnValue(of({ id: 5, total: 20 }));
    commerce.settleCreditNote.mockReturnValue(of({ applied_amount: '20.00', post_redemption_balance: '0.00', cash_change: '0.00', status: 'CONFIRMED' }));
    component.create();
    expect(commerce.physicalSale).toHaveBeenCalledWith({ branch_id: 2, customer_id: 17, items: [{ product_variant_id: 9, quantity: 1 }] });
    expect(commerce.settleCreditNote).toHaveBeenCalledWith(5, expect.objectContaining({ credit_note_code: 'NC-1' }));
    expect(commerce.settleCreditNote.mock.calls[0][1]).not.toHaveProperty('method');
  });

  it('freezes exact settlement request after an ambiguous response', () => {
    component.creditNoteCode = 'NC-1';
    component.selectedRegisteredCustomerId = 17;
    component.creditNoteBalance = { available_balance: '5.00', customer_id: 17, expires_at: null };
    component.branchId = 2; component.variantId = 9; component.quantity = 1; component.amount = 20; component.paymentMethod = 'CASH';
    commerce.physicalSale.mockReturnValue(of({ id: 5, total: 20 }));
    commerce.settleCreditNote.mockReturnValue(throwError(() => ({ status: 503 })));
    component.create();
    expect(component.creditSettlementPendingRetry).not.toBeNull();
    const first = commerce.settleCreditNote.mock.calls[0];
    component.create();
    expect(commerce.settleCreditNote.mock.calls[1]).toEqual(first);
  });

  it('keeps credit due tied to the sale total, not tender received', () => {
    component.selectedVariant = { product_id: 100, product_variant_id: 9 } as any;
    component.catalogProducts = [{ id: 100, price: 100 } as any];
    component.quantity = 1;
    component.creditNoteBalance = { available_balance: '50.00', customer_id: 17, expires_at: null };
    component.amount = 60;
    expect(component.creditNoteAppliedAmount).toBe(50);
    expect(component.creditNoteRemainingDue).toBe(50);
    component.amount = 50;
    expect(component.creditNoteRemainingDue).toBe(50);
  });

  it('reuses a pending physical sale after a definitive settlement failure and creates a fresh key', () => {
    component.branchId = 2; component.variantId = 9; component.quantity = 1; component.amount = 50;
    component.creditNoteCode = 'NC-1'; component.selectedRegisteredCustomerId = 17;
    component.creditNoteBalance = { available_balance: '50.00', customer_id: 17, expires_at: null };
    commerce.physicalSale.mockReturnValue(of({ id: 5, order_number: 'ORD-5', total: 100, customer_id: 17 }));
    commerce.settleCreditNote.mockReturnValueOnce(throwError(() => ({ status: 400, error: { detail: { message: 'Tender required' } } }))).mockReturnValueOnce(of({ id: 5, order_number: 'ORD-5', total: 100, customer_id: 17, applied_amount: '50.00', post_redemption_balance: '0.00', cash_change: '0.00', redemption_id: 1 }));
    component.create();
    const firstRequest = commerce.settleCreditNote.mock.calls[0][1];
    component.amount = 50;
    component.create();
    const secondRequest = commerce.settleCreditNote.mock.calls[1][1];
    expect(commerce.physicalSale).toHaveBeenCalledTimes(1);
    expect(commerce.settleCreditNote.mock.calls[1][0]).toBe(5);
    expect(secondRequest.idempotency_key).not.toBe(firstRequest.idempotency_key);
  });

  it('unlocks correction after an ambiguous settlement retry fails while retaining the pending sale', () => {
    component.branchId = 2; component.variantId = 9; component.quantity = 1; component.amount = 100;
    component.creditNoteCode = 'NC-1'; component.selectedRegisteredCustomerId = 17;
    component.creditNoteBalance = { available_balance: '50.00', customer_id: 17, expires_at: null };
    commerce.physicalSale.mockReturnValue(of({ id: 5, order_number: 'ORD-5', total: 100, customer_id: 17 }));
    commerce.settleCreditNote.mockReturnValueOnce(throwError(() => ({ status: 503 }))).mockReturnValueOnce(throwError(() => ({ status: 400, error: { detail: { message: 'Insufficient tender' } } })));
    component.create();
    const frozen = component.creditSettlementPendingRetry;
    component.amount = 50;
    component.create();
    expect(commerce.settleCreditNote.mock.calls[1][1]).toEqual(frozen?.request);
    expect(component.creditSettlementPendingRetry).toBeNull();
    expect((component as any).pendingCreditSale.id).toBe(5);
    expect(commerce.physicalSale).toHaveBeenCalledTimes(1);
  });

  it('clears a definitive return retry while preserving sale and selection', () => {
    component.returnSale = { sale_id: 42, order_number: 'FS-42', sale_date: '2030-01-01', branch_id: 2, status: 'CONFIRMED', customer_id: 17, items: [{ id: 4, variant_id: 9, name: 'Camisa', sku: 'SKU', purchased_quantity: 1, remaining_returnable_quantity: 1, net_paid_line_total: '20.00' }] };
    component.returnItems[4] = { quantity: 1, condition: 'SELLABLE' };
    component.returnReason = 'Talla';
    component.returnPendingRetry = { saleId: 42, request: { items: [{ sale_item_id: 4, quantity: 1, condition: 'SELLABLE' }], reason: 'Talla', idempotency_key: 'frozen' } };
    commerce.submitReturn.mockReturnValue(throwError(() => ({ status: 400, error: { detail: { message: 'Invalid return' } } })));
    component.processReturn();
    expect(component.returnPendingRetry).toBeNull();
    expect(component.returnSale?.sale_id).toBe(42);
    expect(component.returnItems[4].quantity).toBe(1);
  });

  it('CU-22: supports offline customer mode and attaches customer minimal data to POS sale', () => {
    component.setFinalConsumer();
    expect(component.customerName).toContain('Consumidor Final');
    expect(component.customerNit).toBe('0');
    expect(component.isFinalConsumerActive).toBe(true);

    component.useCustomerForSale({
      id: 'cust-nit-445566',
      full_name: 'Mariana Paredes',
      nit_ci: '445566',
      phone: '71234567',
      email: null,
      created_at: '2026-10-23T00:00:00Z',
      updated_at: '2026-10-23T00:00:00Z',
    });
    expect(component.mode).toBe('SALE');
    expect(component.customerName).toBe('Mariana Paredes');
    expect(component.customerNit).toBe('445566');
    expect(component.customerPhone).toBe('71234567');
    expect(component.isFinalConsumerActive).toBe(false);
  });

  it('CU-22: validates customer inputs, saves locally, and autocompletes from offline padrón', async () => {
    const offlineTxMock = (component as any).offlineTx;
    offlineTxMock.saveCustomer = vi.fn((c) => Promise.resolve({ id: 'c-1', ...c }));

    // Initials helper
    expect(component.getCustomerInitials('Ana María Gómez')).toBe('AM');
    expect(component.getCustomerInitials('Carlos')).toBe('CA');
    expect(component.getCustomerInitials('')).toBe('CL');

    // Attempt saving with empty name/NIT
    component.customerName = '';
    component.customerNit = '';
    component.saveCurrentCustomerLocally();
    expect(component.message).toContain('Ingresa al menos Nombre');

    // Fill valid data and save
    component.customerName = 'Roberto Sucre';
    component.customerNit = '3492810';
    component.customerPhone = '77889900';
    component.saveCurrentCustomerLocally();
    expect(offlineTxMock.saveCustomer).toHaveBeenCalledWith({
      full_name: 'Roberto Sucre',
      nit_ci: '3492810',
      phone: '77889900',
    });

    // Selecting from offlineCustomers dropdown
    component.offlineCustomers = [
      { id: 'cust-1', full_name: 'Claudia Torrez', nit_ci: '987654', phone: '76543210', created_at: '', updated_at: '' },
    ];
    component.onSelectOfflineCustomer('cust-1');
    expect(component.customerName).toBe('Claudia Torrez');
    expect(component.customerNit).toBe('987654');
    expect(component.customerPhone).toBe('76543210');

    // Filtering offline customers
    component.offlineCustomers = [
      { id: '1', full_name: 'Lucía Vargas', nit_ci: '111222', phone: '7001', created_at: '', updated_at: '' },
      { id: '2', full_name: 'Mario Moreno', nit_ci: '333444', phone: '7002', created_at: '', updated_at: '' },
    ];
    component.customerSearchQuery = 'mario';
    component.filterOfflineCustomers();
    expect(component.filteredOfflineCustomers.length).toBe(1);
    expect(component.filteredOfflineCustomers[0].full_name).toBe('Mario Moreno');

    component.customerSearchQuery = '111222';
    component.filterOfflineCustomers();
    expect(component.filteredOfflineCustomers.length).toBe(1);
    expect(component.filteredOfflineCustomers[0].full_name).toBe('Lucía Vargas');
  });

  it('CU-27: scans multiple barcodes into a multi-line cart and generates an invoice receipt on payment', () => {
    component.branchId = 1;
    component.catalogProducts = [
      { id: 10, price: 150 } as any,
      { id: 20, price: 80 } as any,
    ];
    component.inventoryItems = [
      { product_variant_id: 101, product_id: 10, product_name: 'Abrigo Alba', sku: 'AUR-ABR-M-NEG', size_name: 'M', color_name: 'Negro', available_quantity: 5 } as any,
      { product_variant_id: 202, product_id: 20, product_name: 'Blusa Seda', sku: 'AUR-BLU-S-BLA', size_name: 'S', color_name: 'Blanco', available_quantity: 3 } as any,
    ];

    // Scan first garment twice and second garment once
    component.scanBarcode('AUR-ABR-M-NEG');
    component.scanBarcode('AUR-ABR-M-NEG');
    component.scanBarcode('AUR-BLU-S-BLA');

    expect(component.cartItems.length).toBe(2);
    expect(component.totalCartUnits).toBe(3);
    expect(component.cartTotal).toBe(380); // 2 * 150 + 1 * 80
    expect(component.amount).toBe(380);

    // Customer pays with Bs 400
    component.amount = 400;
    component.customerName = 'Lucía Méndez';
    component.customerNit = '7894561';
    expect(component.liveChange).toBe(20);

    commerce.physicalSale.mockReturnValue(of({ id: 88, order_number: 'ORD-0088', total: 380 }));
    commerce.cashPayment.mockReturnValue(of({ id: 88, order_number: 'ORD-0088', total: 380, status: 'PAID' }));

    component.create();

    expect(commerce.physicalSale).toHaveBeenCalledWith({
      branch_id: 1,
      items: [
        { product_variant_id: 101, quantity: 2 },
        { product_variant_id: 202, quantity: 1 },
      ],
    });
    expect(component.lastInvoice).not.toBeNull();
    expect(component.lastInvoice?.invoice_number).toBe('ORD-0088');
    expect(component.lastInvoice?.items.length).toBe(2);
    expect(component.lastInvoice?.total).toBe(380);
    expect(component.lastInvoice?.amount_received).toBe(400);
    expect(component.lastInvoice?.change_returned).toBe(20);
    expect(component.showInvoiceModal).toBe(true);
    expect(component.cartItems.length).toBe(0);
  });
});
