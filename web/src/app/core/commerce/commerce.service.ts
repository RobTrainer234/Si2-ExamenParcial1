import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';
import { Cart, DigitalPurchaseOptions, Page, QRPaymentResponse, QRPaymentStatusResponse, RecommendationItem, Sale, SalePayment, StripePaymentIntent, VirtualFittingSession } from '../models/admin.models';

@Injectable({ providedIn: 'root' })
export class CommerceService {
  private readonly base = appConfig.apiBaseUrl;
  constructor(private readonly http: HttpClient) {}
  cart(): Observable<Cart> { return this.http.get<Cart>(`${this.base}/cart`); }
  addToCart(product_variant_id: number, quantity = 1): Observable<Cart> { return this.http.post<Cart>(`${this.base}/cart/items`, { product_variant_id, quantity }); }
  updateCartItem(id: number, quantity: number): Observable<Cart> { return this.http.patch<Cart>(`${this.base}/cart/items/${id}`, { quantity }); }
  removeCartItem(id: number): Observable<Cart> { return this.http.delete<Cart>(`${this.base}/cart/items/${id}`); }
  digitalPurchase(branch_id: number, options?: DigitalPurchaseOptions): Observable<Sale> { return this.http.post<Sale>(`${this.base}/purchases/digital`, { branch_id, ...(options || {}) }); }
  purchaseHistory(): Observable<Page<Sale>> { return this.http.get<Page<Sale>>(`${this.base}/purchases/mine`); }
  purchaseDetail(id: number): Observable<Sale> { return this.http.get<Sale>(`${this.base}/purchases/mine/${id}`); }
  electronicPayment(sale_id: number, idempotency_key: string): Observable<SalePayment> { return this.http.post<SalePayment>(`${this.base}/payments/electronic`, { sale_id, idempotency_key, method: 'CARD' }); }
  stripePaymentIntent(sale_id: number, idempotency_key: string): Observable<StripePaymentIntent> { return this.http.post<StripePaymentIntent>(`${this.base}/payments/stripe/intent`, { sale_id, idempotency_key, method: 'CARD' }); }
  confirmStripePayment(payment_intent_id: string): Observable<Sale> { return this.http.post<Sale>(`${this.base}/payments/stripe/confirm`, { payment_intent_id }); }
  generateQrPayment(sale_id: number, client_base_url?: string): Observable<QRPaymentResponse> { return this.http.post<QRPaymentResponse>(`${this.base}/payments/qr/generate`, { sale_id, client_base_url }); }
  getQrPaymentStatus(transaction_reference: string): Observable<QRPaymentStatusResponse> { return this.http.get<QRPaymentStatusResponse>(`${this.base}/payments/qr/status/${encodeURIComponent(transaction_reference)}`); }
  confirmQrTransfer(transaction_reference: string, amount: number): Observable<Sale> { return this.http.post<Sale>(`${this.base}/payments/qr/confirm-transfer`, { transaction_reference, amount }); }
  simulateQrPayment(transaction_reference: string, amount: number): Observable<Sale> { return this.http.post<Sale>(`${this.base}/payments/qr/simulate`, { transaction_reference, amount }); }
  approveSandbox(transaction_reference: string, amount: number): Observable<SalePayment> { return this.http.post<SalePayment>(`${this.base}/payments/electronic/notification`, { transaction_reference, amount, status: 'APPROVED' }, { headers: { 'X-Sandbox-Signature': appConfig.sandboxPaymentWebhookSecret } }); }
  physicalSale(data: { branch_id: number; items: { product_variant_id: number; quantity: number }[] }): Observable<Sale> { return this.http.post<Sale>(`${this.base}/sales/physical`, data); }
  cashPayment(saleId: number, amount: number, method = 'CASH', transaction_reference?: string): Observable<Sale> { return this.http.post<Sale>(`${this.base}/sales/${saleId}/cash-payment`, { method, amount, transaction_reference }); }
  recommendations(): Observable<{ items: RecommendationItem[] }> { return this.http.get<{ items: RecommendationItem[] }>(`${this.base}/recommendations/mine`); }
  startVirtualFitting(product_id: number, device_info = 'web-preview'): Observable<VirtualFittingSession> { return this.http.post<VirtualFittingSession>(`${this.base}/virtual-fitting/sessions`, { product_id, device_info }); }
  finishVirtualFitting(id: number): Observable<VirtualFittingSession> { return this.http.patch<VirtualFittingSession>(`${this.base}/virtual-fitting/sessions/${id}/finish`, {}); }
  virtualFittingSessions(): Observable<{ items: VirtualFittingSession[] }> { return this.http.get<{ items: VirtualFittingSession[] }>(`${this.base}/virtual-fitting/sessions/mine`); }
  returnSale(saleId: number, reason: string): Observable<Sale> { return this.http.post<Sale>(`${this.base}/sales/${saleId}/return`, { reason }); }
}
