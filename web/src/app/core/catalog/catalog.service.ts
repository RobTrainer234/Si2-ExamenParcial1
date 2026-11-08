import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, from, map, switchMap, throwError } from 'rxjs';

import { appConfig } from '../config/app-config';
import { AvailabilityItem, CatalogDetail, CatalogFilters, CatalogNavigation, CatalogPage, CatalogVariant } from '../models/api.models';
import { OfflineCatalogService } from '../offline/offline-catalog.service';
import { OfflineProductDetail, SyncVariantItem } from '../offline/offline.models';

export interface CatalogQuery {
  page: number;
  page_size: number;
  q?: string;
  category_id?: number;
  size_id?: number;
  color_id?: number;
  branch_id?: number;
  audience?: string;
  season_id?: number;
  collection_id?: number;
  sort?: string;
}

@Injectable({ providedIn: 'root' })
export class CatalogService {
  private readonly offline = inject(OfflineCatalogService);
  readonly lastDetailWasOffline = signal(false);
  readonly lastAvailabilityWasOffline = signal(false);
  readonly lastOfflineBranchName = signal('la sucursal sincronizada');

  constructor(private readonly http: HttpClient) {}

  list(filters: CatalogQuery): Observable<CatalogPage> {
    let params = new HttpParams().set('page', filters.page).set('page_size', filters.page_size);
    Object.entries(filters).forEach(([key, value]) => {
      if (key !== 'page' && key !== 'page_size' && value !== undefined && value !== '') params = params.set(key, value);
    });
    return this.http.get<CatalogPage>(`${appConfig.apiBaseUrl}/catalog`, { params });
  }

  detail(id: number): Observable<CatalogDetail> {
    this.lastDetailWasOffline.set(false);
    return this.http.get<CatalogDetail>(`${appConfig.apiBaseUrl}/catalog/${id}`).pipe(
      catchError((error) => from(this.offline.getProductDetail(id)).pipe(
        switchMap((local) => {
          if (!local.product) return throwError(() => error);
          this.lastDetailWasOffline.set(true);
          this.lastOfflineBranchName.set(local.metadata?.branch_name || 'la sucursal sincronizada');
          return [this.mapOfflineDetail(local)];
        }),
      )),
    );
  }

  filters(): Observable<CatalogFilters> { return this.http.get<CatalogFilters>(`${appConfig.apiBaseUrl}/catalog/filters`); }
  navigation(): Observable<CatalogNavigation> { return this.http.get<CatalogNavigation>(`${appConfig.apiBaseUrl}/catalog/navigation`); }

  availability(productId: number, sizeId: number, colorId: number): Observable<AvailabilityItem[]> {
    const params = new HttpParams().set('size_id', sizeId).set('color_id', colorId);
    this.lastAvailabilityWasOffline.set(false);
    return this.http.get<AvailabilityItem[]>(`${appConfig.apiBaseUrl}/catalog/${productId}/availability`, { params }).pipe(
      catchError(() => from(this.offline.getProductDetail(productId)).pipe(
        map((local) => this.mapOfflineAvailability(local, sizeId, colorId)),
      )),
    );
  }

  private mapOfflineDetail(local: OfflineProductDetail): CatalogDetail {
    const product = local.product!;
    const variants = local.variants.map((variant, index) => this.mapOfflineVariant(variant, local.inventory[variant.id], index));
    return {
      id: product.id,
      category_id: product.category_id,
      category_name: product.category_name,
      audience: product.audience!,
      code: product.code,
      name: product.name,
      slug: product.slug,
      price: product.price,
      image_url: product.image_url,
      description: product.description,
      size_system: product.size_system!,
      images: product.image_url ? [{ image_url: product.image_url, is_primary: true, sort_order: 0 }] : [],
      variants,
    };
  }

  private mapOfflineVariant(variant: SyncVariantItem, inventory: OfflineProductDetail['inventory'][number], sortOrder: number): CatalogVariant {
    const stock = inventory?.available_quantity ?? 0;
    return {
      id: variant.id,
      size_id: variant.size_id ?? 0,
      size_name: variant.size_name ?? 'Sin talla',
      size_type: variant.size_type!,
      sort_order: variant.sort_order!,
      color_id: variant.color_id ?? 0,
      color_name: variant.color_name ?? 'Sin color',
      sku: variant.sku,
      stock_total: stock,
      available: stock > 0,
    };
  }

  private mapOfflineAvailability(local: OfflineProductDetail, sizeId: number, colorId: number): AvailabilityItem[] {
    if (!local.product || !local.metadata) return [];
    const matches = local.variants.filter((variant) => variant.size_id === sizeId && variant.color_id === colorId);
    if (matches.length === 0 || matches.some((variant) => !local.inventory[variant.id])) return [];
    const stock = matches.reduce((total, variant) => total + local.inventory[variant.id].available_quantity, 0);
    this.lastAvailabilityWasOffline.set(true);
    this.lastOfflineBranchName.set(local.metadata.branch_name || 'la sucursal sincronizada');
    return [{ branch_id: local.metadata.branch_id, branch_name: local.metadata.branch_name, city_name: '', address: '', available: stock > 0, stock }];
  }
}
