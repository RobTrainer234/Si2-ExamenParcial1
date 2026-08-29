import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';
import { AdminUser, Branch, Category, City, Color, Page, ProductDetail, ProductSummary, Size, Supplier } from '../models/admin.models';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly base = appConfig.apiBaseUrl;
  constructor(private readonly http: HttpClient) {}

  private page<T>(path: string, q?: string): Observable<Page<T>> {
    let params = new HttpParams().set('page', 1).set('page_size', 100);
    if (q) params = params.set('q', q);
    return this.http.get<Page<T>>(`${this.base}/${path}`, { params });
  }

  users(q = ''): Observable<Page<AdminUser>> { return this.page<AdminUser>('users', q); }
  setUserActive(id: number, active: boolean): Observable<AdminUser> { return this.http.patch<AdminUser>(`${this.base}/users/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  createUser(data: unknown): Observable<AdminUser> { return this.http.post<AdminUser>(`${this.base}/users`, data); }

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
  createSize(name: string): Observable<Size> { return this.http.post<Size>(`${this.base}/sizes`, { name }); }
  createColor(data: unknown): Observable<Color> { return this.http.post<Color>(`${this.base}/colors`, data); }
  setMasterActive(path: 'categories' | 'sizes' | 'colors', id: number, active: boolean): Observable<unknown> { return this.http.patch(`${this.base}/${path}/${id}/${active ? 'activate' : 'deactivate'}`, {}); }

  suppliers(q = ''): Observable<Page<Supplier>> { return this.page<Supplier>('suppliers', q); }
  createSupplier(data: unknown): Observable<Supplier> { return this.http.post<Supplier>(`${this.base}/suppliers`, data); }
  setSupplierActive(id: number, active: boolean): Observable<Supplier> { return this.http.patch<Supplier>(`${this.base}/suppliers/${id}/${active ? 'activate' : 'deactivate'}`, {}); }

  products(q = ''): Observable<Page<ProductSummary>> { return this.page<ProductSummary>('products', q); }
  product(id: number): Observable<ProductDetail> { return this.http.get<ProductDetail>(`${this.base}/products/${id}`); }
  createProduct(data: unknown): Observable<ProductDetail> { return this.http.post<ProductDetail>(`${this.base}/products`, data); }
  setProductActive(id: number, active: boolean): Observable<ProductDetail> { return this.http.patch<ProductDetail>(`${this.base}/products/${id}/${active ? 'activate' : 'deactivate'}`, {}); }
  addVariant(productId: number, data: unknown): Observable<ProductDetail> { return this.http.post<ProductDetail>(`${this.base}/products/${productId}/variants`, data); }
}
