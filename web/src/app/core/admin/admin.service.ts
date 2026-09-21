import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';
import { AdminUser, Branch, Category, City, Collection, Color, DashboardFilters, DashboardReport, ImageInput, InventoryMovement, InventoryRow, Page, ProductDetail, ProductSummary, Promotion, ReportAssistantRequest, ReportAssistantResponse, ReportExportFormat, Reservation, Season, Size, Supplier, SupplyOffer } from '../models/admin.models';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly base = appConfig.apiBaseUrl;
  constructor(private readonly http: HttpClient) {}

  private page<T>(path: string, q?: string): Observable<Page<T>> {
    let params = new HttpParams().set('page', 1).set('page_size', 100);
    if (q) params = params.set('q', q);
    return this.http.get<Page<T>>(`${this.base}/${path}`, { params });
  }

  private reportParams(filters: DashboardFilters = {}): HttpParams {
    let params = new HttpParams();
    if (filters.branch_id) params = params.set('branch_id', filters.branch_id);
    if (filters.start_date) params = params.set('date_from', filters.start_date);
    if (filters.end_date) params = params.set('date_to', filters.end_date);
    return params;
  }

  users(q = ''): Observable<Page<AdminUser>> { return this.page<AdminUser>('users', q); }
  setUserActive(id: number, active: boolean): Observable<AdminUser> { return this.http.patch<AdminUser>(`${this.base}/users/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  createUser(data: unknown): Observable<AdminUser> { return this.http.post<AdminUser>(`${this.base}/users`, data); }
  updateUser(id: number, data: unknown): Observable<AdminUser> { return this.http.patch<AdminUser>(`${this.base}/users/${id}`, data); }

  cities(q = ''): Observable<Page<City>> { return this.page<City>('cities', q); }
  createCity(name: string): Observable<City> { return this.http.post<City>(`${this.base}/cities`, { name }); }
  setCityActive(id: number, active: boolean): Observable<City> { return this.http.patch<City>(`${this.base}/cities/${id}/${active ? 'activate' : 'deactivate'}`, {}); }

  branches(cityId?: number): Observable<Page<Branch>> {
    let params = new HttpParams().set('page', 1).set('page_size', 100);
    if (cityId) params = params.set('city_id', cityId);
    return this.http.get<Page<Branch>>(`${this.base}/branches`, { params });
  }
  createBranch(data: unknown): Observable<Branch> { return this.http.post<Branch>(`${this.base}/branches`, data); }
  setBranchActive(id: number, active: boolean): Observable<Branch> { return this.http.patch<Branch>(`${this.base}/branches/${id}/${active ? 'activate' : 'deactivate'}`, {}); }

  categories(q = ''): Observable<Page<Category>> { return this.page<Category>('categories', q); }
  sizes(q = ''): Observable<Page<Size>> { return this.page<Size>('sizes', q); }
  colors(q = ''): Observable<Page<Color>> { return this.page<Color>('colors', q); }
  createCategory(data: unknown): Observable<Category> { return this.http.post<Category>(`${this.base}/categories`, data); }
  createSize(data: unknown): Observable<Size> { return this.http.post<Size>(`${this.base}/sizes`, data); }
  createColor(data: unknown): Observable<Color> { return this.http.post<Color>(`${this.base}/colors`, data); }
  updateCategory(id: number, data: unknown): Observable<Category> { return this.http.patch<Category>(`${this.base}/categories/${id}`, data); }
  updateSize(id: number, data: unknown): Observable<Size> { return this.http.patch<Size>(`${this.base}/sizes/${id}`, data); }
  updateColor(id: number, data: unknown): Observable<Color> { return this.http.patch<Color>(`${this.base}/colors/${id}`, data); }
  setMasterActive(path: 'categories' | 'sizes' | 'colors', id: number, active: boolean): Observable<unknown> { return this.http.patch(`${this.base}/${path}/${id}/${active ? 'activate' : 'deactivate'}`, {}); }

  suppliers(q = ''): Observable<Page<Supplier>> { return this.page<Supplier>('suppliers', q); }
  createSupplier(data: unknown): Observable<Supplier> { return this.http.post<Supplier>(`${this.base}/suppliers`, data); }
  setSupplierActive(id: number, active: boolean): Observable<Supplier> { return this.http.patch<Supplier>(`${this.base}/suppliers/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  supplyOffers(supplierId: number): Observable<SupplyOffer[]> { return this.http.get<SupplyOffer[]>(`${this.base}/suppliers/${supplierId}/offers`); }
  createSupplyOffer(supplierId: number, data: unknown): Observable<SupplyOffer> { return this.http.post<SupplyOffer>(`${this.base}/suppliers/${supplierId}/offers`, data); }
  updateSupplyOffer(supplierId: number, offerId: number, data: unknown): Observable<SupplyOffer> { return this.http.patch<SupplyOffer>(`${this.base}/suppliers/${supplierId}/offers/${offerId}`, data); }
  setSupplyOfferActive(supplierId: number, offerId: number, active: boolean): Observable<SupplyOffer> { return this.http.patch<SupplyOffer>(`${this.base}/suppliers/${supplierId}/offers/${offerId}/${active ? 'activate' : 'deactivate'}`, {}); }

  seasons(q = ''): Observable<Page<Season>> { return this.page<Season>('seasons', q); }
  createSeason(data: unknown): Observable<Season> { return this.http.post<Season>(`${this.base}/seasons`, data); }
  updateSeason(id: number, data: unknown): Observable<Season> { return this.http.patch<Season>(`${this.base}/seasons/${id}`, data); }
  setSeasonActive(id: number, active: boolean): Observable<Season> { return this.http.patch<Season>(`${this.base}/seasons/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  collections(seasonId?: number): Observable<Page<Collection>> {
    let params = new HttpParams().set('page', 1).set('page_size', 100);
    if (seasonId) params = params.set('season_id', seasonId);
    return this.http.get<Page<Collection>>(`${this.base}/collections`, { params });
  }
  createCollection(data: unknown): Observable<Collection> { return this.http.post<Collection>(`${this.base}/collections`, data); }
  updateCollection(id: number, data: unknown): Observable<Collection> { return this.http.patch<Collection>(`${this.base}/collections/${id}`, data); }
  setCollectionActive(id: number, active: boolean): Observable<Collection> { return this.http.patch<Collection>(`${this.base}/collections/${id}/${active ? 'activate' : 'deactivate'}`, {}); }

  products(q = ''): Observable<Page<ProductSummary>> { return this.page<ProductSummary>('products', q); }
  product(id: number): Observable<ProductDetail> { return this.http.get<ProductDetail>(`${this.base}/products/${id}`); }
  createProduct(data: unknown): Observable<ProductDetail> { return this.http.post<ProductDetail>(`${this.base}/products`, data); }
  updateProduct(id: number, data: unknown): Observable<ProductDetail> { return this.http.patch<ProductDetail>(`${this.base}/products/${id}`, data); }
  setProductActive(id: number, active: boolean): Observable<ProductDetail> { return this.http.patch<ProductDetail>(`${this.base}/products/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  inventory(productId: number): Observable<Page<InventoryRow>> { const params = new HttpParams().set('page', 1).set('page_size', 100).set('product_id', productId); return this.http.get<Page<InventoryRow>>(`${this.base}/inventory`, { params }); }
  inventoryAll(branchId?: number, page = 1, pageSize = 100): Observable<Page<InventoryRow>> { let params = new HttpParams().set('page', page).set('page_size', pageSize); if (branchId) params = params.set('branch_id', branchId); return this.http.get<Page<InventoryRow>>(`${this.base}/inventory`, { params }); }
  createInventory(data: unknown): Observable<InventoryRow> { return this.http.post<InventoryRow>(`${this.base}/inventory`, data); }
  updateInventory(id: number, stock_quantity: number): Observable<InventoryRow> { return this.http.patch<InventoryRow>(`${this.base}/inventory/${id}`, { stock_quantity }); }
  inventoryMovements(inventoryId?: number, movementType?: string, page = 1, pageSize = 100): Observable<Page<InventoryMovement>> { let params = new HttpParams().set('page', page).set('page_size', pageSize); if (inventoryId) params = params.set('inventory_id', inventoryId); if (movementType) params = params.set('movement_type', movementType); return this.http.get<Page<InventoryMovement>>(`${this.base}/inventory/movements`, { params }); }
  createInventoryMovement(data: unknown): Observable<InventoryMovement> { return this.http.post<InventoryMovement>(`${this.base}/inventory/movements`, data); }
  reservations(branchId: number, status?: string): Observable<Page<Reservation>> { let params = new HttpParams().set('page', 1).set('page_size', 100).set('branch_id', branchId); if (status) params = params.set('status', status); return this.http.get<Page<Reservation>>(`${this.base}/reservations/branch`, { params }); }
  reservationBranches(): Observable<Page<Branch>> { return this.http.get<Page<Branch>>(`${this.base}/reservations/branches`); }
  updateReservationStatus(id: number, reservationStatus: string): Observable<Reservation> { return this.http.patch<Reservation>(`${this.base}/reservations/${id}/status`, { status: reservationStatus }); }
  addVariant(productId: number, data: unknown): Observable<ProductDetail> { return this.http.post<ProductDetail>(`${this.base}/products/${productId}/variants`, data); }
  addVariantsBulk(productId: number, variants: unknown[]): Observable<ProductDetail> { return this.http.post<ProductDetail>(`${this.base}/products/${productId}/variants/bulk`, { variants }); }
  promotions(q = ''): Observable<Page<Promotion>> { return this.page<Promotion>('promotions', q); }
  createPromotion(data: unknown): Observable<Promotion> { return this.http.post<Promotion>(`${this.base}/promotions`, data); }
  updatePromotion(id: number, data: unknown): Observable<Promotion> { return this.http.patch<Promotion>(`${this.base}/promotions/${id}`, data); }
  setPromotionProducts(id: number, product_ids: number[]): Observable<Promotion> { return this.http.post<Promotion>(`${this.base}/promotions/${id}/products`, { product_ids }); }
  setPromotionActive(id: number, active: boolean): Observable<Promotion> { return this.http.patch<Promotion>(`${this.base}/promotions/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  dashboard(filters: DashboardFilters = {}): Observable<DashboardReport> {
    let params = new HttpParams();
    if (filters.branch_id) params = params.set('branch_id', filters.branch_id);
    if (filters.start_date) params = params.set('date_from', filters.start_date);
    if (filters.end_date) params = params.set('date_to', filters.end_date);
    return this.http.get<DashboardReport>(`${this.base}/reports/dashboard`, { params });
  }
  exportReport(format: ReportExportFormat, filters: DashboardFilters = {}): Observable<Blob> {
    return this.http.get(`${this.base}/reports/export/${format}`, { params: this.reportParams(filters), responseType: 'blob' });
  }
  reportAssistant(request: ReportAssistantRequest): Observable<ReportAssistantResponse> { return this.http.post<ReportAssistantResponse>(`${this.base}/reports/assistant`, request); }
  addImage(productId: number, data: ImageInput): Observable<ProductDetail> { return this.http.post<ProductDetail>(`${this.base}/products/${productId}/images`, data); }
  uploadImage(productId: number, file: File, isPrimary: boolean, sortOrder: number): Observable<ProductDetail> { const data = new FormData(); data.append('file', file); data.append('is_primary', String(isPrimary)); data.append('sort_order', String(sortOrder)); return this.http.post<ProductDetail>(`${this.base}/products/${productId}/images/upload`, data); }
  updateImage(productId: number, imageId: number, data: { is_primary?: boolean; sort_order?: number }): Observable<ProductDetail> { return this.http.patch<ProductDetail>(`${this.base}/products/${productId}/images/${imageId}`, data); }
  deleteImage(productId: number, imageId: number): Observable<ProductDetail> { return this.http.delete<ProductDetail>(`${this.base}/products/${productId}/images/${imageId}`); }
}
