import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';
import { Cart, Sale, SalePayment } from '../models/admin.models';

@Injectable({ providedIn: 'root' })
export class CommerceService {
  private readonly base = appConfig.apiBaseUrl;
  constructor(private readonly http: HttpClient) {}
  cart(): Observable<Cart> { return this.http.get<Cart>(`${this.base}/cart`); }
  addToCart(product_variant_id: number, quantity = 1): Observable<Cart> { return this.http.post<Cart>(`${this.base}/cart/items`, { product_variant_id, quantity }); }
  updateCartItem(id: number, quantity: number): Observable<Cart> { return this.http.patch<Cart>(`${this.base}/cart/items/${id}`, { quantity }); }
  removeCartItem(id: number): Observable<Cart> { return this.http.delete<Cart>(`${this.base}/cart/items/${id}`); }
  digitalPurchase(branch_id: number): Observable<Sale> { return this.http.post<Sale>(`${this.base}/purchases/digital`, { branch_id }); }
  electronicPayment(sale_id: number, idempotency_key: string): Observable<SalePayment> { return this.http.post<SalePayment>(`${this.base}/payments/electronic`, { sale_id, idempotency_key, method: 'CARD' }); }
  approveSandbox(transaction_reference: string, amount: number): Observable<SalePayment> { return this.http.post<SalePayment>(`${this.base}/payments/electronic/notification`, { transaction_reference, amount, status: 'APPROVED' }); }
  physicalSale(data: { branch_id: number; items: { product_variant_id: number; quantity: number }[] }): Observable<Sale> { return this.http.post<Sale>(`${this.base}/sales/physical`, data); }
  cashPayment(saleId: number, amount: number, method = 'CASH'): Observable<Sale> { return this.http.post<Sale>(`${this.base}/sales/${saleId}/cash-payment`, { method, amount }); }
}
