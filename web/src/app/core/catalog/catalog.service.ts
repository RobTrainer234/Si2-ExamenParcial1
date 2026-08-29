import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';
import { AvailabilityItem, CatalogDetail, CatalogFilters, CatalogPage } from '../models/api.models';

export interface CatalogQuery {
  page: number;
  page_size: number;
  q?: string;
  category_id?: number;
  size_id?: number;
  color_id?: number;
  branch_id?: number;
}

@Injectable({ providedIn: 'root' })
export class CatalogService {
  constructor(private readonly http: HttpClient) {}

  list(filters: CatalogQuery): Observable<CatalogPage> {
    let params = new HttpParams().set('page', filters.page).set('page_size', filters.page_size);
    Object.entries(filters).forEach(([key, value]) => {
      if (key !== 'page' && key !== 'page_size' && value !== undefined && value !== '') {
        params = params.set(key, value);
      }
    });
    return this.http.get<CatalogPage>(`${appConfig.apiBaseUrl}/catalog`, { params });
  }

  detail(id: number): Observable<CatalogDetail> {
    return this.http.get<CatalogDetail>(`${appConfig.apiBaseUrl}/catalog/${id}`);
  }

  filters(): Observable<CatalogFilters> {
    return this.http.get<CatalogFilters>(`${appConfig.apiBaseUrl}/catalog/filters`);
  }

  availability(productId: number, sizeId: number, colorId: number): Observable<AvailabilityItem[]> {
    const params = new HttpParams().set('size_id', sizeId).set('color_id', colorId);
    return this.http.get<AvailabilityItem[]>(`${appConfig.apiBaseUrl}/catalog/${productId}/availability`, { params });
  }
}
