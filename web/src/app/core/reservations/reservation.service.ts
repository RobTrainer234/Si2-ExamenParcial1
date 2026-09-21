import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';
import { Page, Reservation } from '../models/admin.models';

@Injectable({ providedIn: 'root' })
export class ReservationService {
  private readonly http = inject(HttpClient);
  private readonly base = `${appConfig.apiBaseUrl}/reservations`;

  mine(status?: string): Observable<Page<Reservation>> {
    let params = new HttpParams().set('page', 1).set('page_size', 100);
    if (status) params = params.set('status', status);
    return this.http.get<Page<Reservation>>(`${this.base}/mine`, { params });
  }

  get(id: number): Observable<Reservation> { return this.http.get<Reservation>(`${this.base}/${id}`); }
  create(data: { branch_id: number; scheduled_for: string; items: { product_variant_id: number; quantity: number }[] }): Observable<Reservation> { return this.http.post<Reservation>(this.base, data); }
  cancel(id: number): Observable<Reservation> { return this.http.patch<Reservation>(`${this.base}/${id}/cancel`, {}); }
}
