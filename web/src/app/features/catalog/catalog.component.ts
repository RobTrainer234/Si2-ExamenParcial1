import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AudienceCode, CatalogFilterOption, CatalogItem, CatalogNavigation } from '../../core/models/api.models';
import { CatalogService } from '../../core/catalog/catalog.service';

@Component({
  standalone: true,
  imports: [CurrencyPipe, ReactiveFormsModule, RouterLink],
  template: `
    <section class="collection-browser" aria-labelledby="collection-title">
      <div class="collection-header-meta">
        <p class="collection-breadcrumb">FashionStore / Catálogo / {{ collectionContextLabel }}</p>
        <div class="collection-context-row" aria-label="Contexto de colección">
          <span class="context-pill"><span class="material-symbols-outlined">event</span><strong>Temporada:</strong> {{ activeSeasonName }}</span>
          <span class="context-pill"><span class="material-symbols-outlined">style</span><strong>Colección:</strong> {{ activeCollectionName }}</span>
          <span class="context-pill"><span class="material-symbols-outlined">person</span><strong>Público:</strong> {{ activeAudienceName }}</span>
        </div>
      </div>
      <div class="collection-title-wrap">
        <h1 id="collection-title">{{ collectionTitle }}</h1>
        <p class="collection-summary">{{ collectionDescription }}</p>
        @if (!loading && !error) {
          <div class="result-count-badge">
            <span class="live-status-dot"></span>
            <p class="result-count"><strong>{{ total }}</strong> {{ total === 1 ? 'prenda disponible' : 'prendas disponibles' }} · {{ selectedBranchName }}</p>
          </div>
        }
      </div>
    </section>

    <div class="catalog-control-panel">
      <div class="catalog-toolbar-wrapper">
        <form [formGroup]="filters" (ngSubmit)="search()" class="search-form catalog-toolbar" aria-label="Filtros principales del catálogo">
          <div class="search-box-wrap">
            <label class="search-box"><span class="material-symbols-outlined" aria-hidden="true">search</span><input formControlName="q" placeholder="Buscar prendas, códigos..." aria-label="Buscar prendas"></label>
          </div>
          <div class="filter-selects-group">
            <label><span class="select-label">Categoría</span><select formControlName="category_id"><option value="">Todas</option>@for (option of categories; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
            <label><span class="select-label">Sucursal</span><select formControlName="branch_id"><option value="">Todas</option>@for (option of branches; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
            <label><span class="select-label">Ordenar por</span><select formControlName="sort"><option value="editorial">Orden del catálogo</option><option value="newest">Novedades primero</option></select></label>
            <button class="button button-dark apply-filters-btn" type="submit"><span class="material-symbols-outlined">tune</span>Aplicar filtros</button>
          </div>
        </form>
      </div>

      <section class="catalog-filters" aria-label="Filtros secundarios del catálogo">
        <div class="catalog-filter-section category-section">
          <div class="filter-header-title">
            <span class="material-symbols-outlined">category</span>
            <span class="filter-section-label">Categorías</span>
          </div>
          <div class="catalog-ribbon">
            <button type="button" class="ribbon-chip" [class.active]="!filters.controls.category_id.value" (click)="clearCategory()">Todo</button>
            @for (category of categories; track category.id) {
              <button type="button" class="ribbon-chip" [class.selected]="isFilterSelected('category_id', category.id)" [class.active]="isFilterSelected('category_id', category.id)" (click)="setCategory(category.id)">{{ category.name }}</button>
            }
          </div>
        </div>
        <div class="catalog-filter-row">
          <div class="quick-filter-group">
            <div class="filter-header-title">
              <span class="material-symbols-outlined">straighten</span>
              <span class="filter-section-label">Tallas</span>
            </div>
            <div class="filter-options size-options">
              @for (option of sizes; track option.id) {
                <button type="button" class="size-btn" [class.selected]="isFilterSelected('size_id', option.id)" (click)="setQuickFilter('size_id', option.id)">{{ option.name }}</button>
              }
            </div>
          </div>
          <div class="quick-filter-group color-filter">
            <div class="filter-header-title">
              <span class="material-symbols-outlined">palette</span>
              <span class="filter-section-label">Colores</span>
            </div>
            <div class="filter-options color-options">
              @for (option of colors; track option.id) {
                <button type="button" class="color-swatch-btn" [class.selected]="isFilterSelected('color_id', option.id)" [style.--swatch]="option.hex_code || '#b7aea3'" [attr.aria-label]="option.name" [title]="option.name" (click)="setQuickFilter('color_id', option.id)"></button>
              }
            </div>
          </div>
        </div>
        @if (activeFilterSummary.length > 0) {
          <div class="active-filter-chips" aria-label="Filtros activos">
            <span class="active-filters-label">Filtros activos:</span>
            @for (filter of activeFilterSummary; track filter) { <span>{{ filter }}</span> }
          </div>
        }
      </section>
    </div>

    @if (activeAudience || activeSort === 'newest') { <div class="catalog-context">@if (activeAudience) { <span class="audience-pill">{{ activeAudienceName }}</span> }@if (activeSort === 'newest') { <span class="context-divider">/</span><span>Novedades primero</span> }</div> }
    @if (error) { <p class="error page-message">No se pudo cargar el catálogo. Intenta nuevamente.</p> }
    @if (loading) { <section class="catalog-loading" aria-label="Cargando colección"><p class="loading-label">Cargando prendas...</p><div class="loading-grid">@for (placeholder of loadingPlaceholders; track placeholder) { <div class="loading-card"><div class="loading-image"></div><div class="loading-line short"></div><div class="loading-line"></div></div> }</div></section> }
    @if (!loading && !error && products.length === 0) { <p class="empty page-message">No encontramos prendas con esos filtros.</p> }
    @if (!loading && !error && products.length > 0) { <section class="catalog-heading"><span class="eyebrow">Prendas</span><span>{{ activeSortLabel }}</span></section> }
    @if (!loading && !error) { <section class="product-grid collection-product-grid">
      @for (product of products; track product.id) {
        <a class="product-card" [routerLink]="['/catalog', product.id]">
          <div class="product-image"><img [src]="product.image_url || placeholder" [alt]="product.name" (error)="usePlaceholder($event)"><button class="favorite-button" [class.is-favorite]="favorites.has(product.id)" [attr.aria-label]="favorites.has(product.id) ? 'Quitar de favoritos' : 'Guardar producto'" type="button" (click)="toggleFavorite($event, product.id)"><span class="material-symbols-outlined">favorite</span></button></div>
          <div class="product-meta"><span class="category-label">{{ product.category_name }}</span><h2>{{ product.name }}</h2><strong>{{ product.price | currency:'BOB':'symbol':'1.2-2' }}</strong></div>
        </a>
      }
    </section> }
    @if (totalPages > 1) {
      <nav class="pagination" aria-label="Paginación">
        <button class="button button-light" type="button" [disabled]="page === 1" (click)="goTo(page - 1)">Anterior</button>
        <span>Página {{ page }} de {{ totalPages }}</span>
        <button class="button button-light" type="button" [disabled]="page === totalPages" (click)="goTo(page + 1)">Siguiente</button>
      </nav>
    }
  `,
})
export class CatalogComponent {
  private readonly catalog = inject(CatalogService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly route = inject(ActivatedRoute);
  readonly filters = inject(FormBuilder).nonNullable.group({ q: [''], category_id: [''], size_id: [''], color_id: [''], branch_id: [''], audience: [''], season_id: [''], collection_id: [''], sort: ['editorial'] });
  products: CatalogItem[] = [];
  page = 1;
  total = 0;
  totalPages = 0;
  categories: CatalogFilterOption[] = [];
  sizes: CatalogFilterOption[] = [];
  colors: CatalogFilterOption[] = [];
  branches: CatalogFilterOption[] = [];
  navigation: CatalogNavigation | null = null;
  loading = false;
  error = false;
  readonly favorites = new Set<number>();
  readonly loadingPlaceholders = [1, 2, 3, 4];
  readonly placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="600" height="700" viewBox="0 0 600 700"%3E%3Crect width="600" height="700" fill="%23eee9e1"/%3E%3Ctext x="300" y="350" text-anchor="middle" fill="%2390887e" font-size="24"%3EFashionStore%3C/text%3E%3C/svg%3E';

  constructor() {
    this.catalog.filters().subscribe({ next: (filters) => { this.categories = filters.categories; this.sizes = filters.sizes; this.colors = filters.colors; this.branches = filters.branches; }, error: () => undefined });
    this.catalog.navigation().subscribe({ next: (navigation) => { this.navigation = navigation; this.changeDetector.markForCheck(); }, error: () => { this.navigation = null; this.changeDetector.markForCheck(); } });
    this.route.queryParamMap.subscribe((params) => { this.filters.patchValue({ audience: params.get('audience') || '', season_id: params.get('season_id') || '', collection_id: params.get('collection_id') || '', sort: params.get('sort') || 'editorial' }); this.load(); });
  }

  search(): void { this.page = 1; this.load(); }
  setCategory(categoryId: number): void { this.filters.patchValue({ category_id: String(categoryId) }); this.page = 1; this.load(); }
  clearCategory(): void { this.filters.patchValue({ category_id: '' }); this.page = 1; this.load(); }
  setQuickFilter(field: 'size_id' | 'color_id', value: number): void { const control = this.filters.controls[field]; control.setValue(control.value === String(value) ? '' : String(value)); this.page = 1; this.load(); }
  isFilterSelected(field: 'category_id' | 'size_id' | 'color_id', value: number): boolean { return this.filters.controls[field].value === `${value}`; }

  toggleFavorite(event: Event, productId: number): void {
    event.preventDefault();
    event.stopPropagation();
    this.favorites.has(productId) ? this.favorites.delete(productId) : this.favorites.add(productId);
  }

  usePlaceholder(event: Event): void {
    const image = event.target as HTMLImageElement;
    image.onerror = null;
    image.src = this.placeholder;
  }

  goTo(page: number): void { this.page = page; this.load(); }

  private load(): void {
    this.loading = true;
    this.error = false;
    const raw = this.filters.getRawValue();
    this.catalog.list({ page: this.page, page_size: 12, q: raw.q, category_id: this.toNumber(raw.category_id), size_id: this.toNumber(raw.size_id), color_id: this.toNumber(raw.color_id), branch_id: this.toNumber(raw.branch_id), audience: raw.audience || undefined, season_id: this.toNumber(raw.season_id), collection_id: this.toNumber(raw.collection_id), sort: raw.sort || 'editorial' }).pipe(
      finalize(() => { this.loading = false; this.changeDetector.markForCheck(); }),
    ).subscribe({
      next: (response) => { this.products = response.items; this.total = response.total; this.totalPages = response.total_pages; },
      error: () => { this.error = true; this.products = []; this.total = 0; this.totalPages = 0; },
    });
  }

  get selectedBranchName(): string { const id = Number(this.filters.controls.branch_id.value); return this.branches.find((branch) => branch.id === id)?.name || 'Todas las sucursales'; }
  get activeAudience(): AudienceCode | null { const value = this.filters.controls.audience.value; return value === 'WOMEN' || value === 'MEN' || value === 'UNISEX' ? value : null; }
  get activeSort(): string { return this.filters.controls.sort.value; }
  get activeSortLabel(): string { return this.activeSort === 'newest' ? 'Novedades primero' : 'Orden del catálogo'; }
  get collectionContextLabel(): string { return this.activeCollectionName === 'Todas las colecciones' ? 'Colección general' : this.activeCollectionName; }
  get collectionTitle(): string { return this.activeAudience ? `Prendas para ${this.activeAudienceName}` : 'Explorá la colección'; }
  get collectionDescription(): string {
    if (this.activeAudience) {
      return `Buscá prendas de ${this.activeAudienceName.toLowerCase()} con filtros claros por categoría, talla, color y sucursal.`;
    }
    return 'Navegá el catálogo completo con una sola grilla ordenada, filtros simples y disponibilidad por sucursal.';
  }
  get resultContext(): string { return [this.activeAudienceName, this.activeSeasonName, this.selectedBranchName].filter(Boolean).join(' · '); }
  get activeAudienceName(): string {
    if (!this.activeAudience) { return 'Todos los públicos'; }
    return this.navigation?.audiences.find((audience) => audience.code === this.activeAudience)?.name || this.audienceLabel(this.activeAudience);
  }
  get activeSeasonName(): string { return this.activeSeason?.name || (this.filters.controls.season_id.value ? 'Temporada seleccionada' : 'Temporada actual'); }
  get activeCollectionName(): string { return this.activeCollection?.name || (this.filters.controls.collection_id.value ? 'Colección seleccionada' : 'Todas las colecciones'); }
  get activeFilterSummary(): string[] {
    const filters: string[] = [];
    const category = this.findOptionName(this.categories, this.filters.controls.category_id.value);
    const size = this.findOptionName(this.sizes, this.filters.controls.size_id.value);
    const color = this.findOptionName(this.colors, this.filters.controls.color_id.value);
    if (category) { filters.push(`Categoría: ${category}`); }
    if (size) { filters.push(`Talla: ${size}`); }
    if (color) { filters.push(`Color: ${color}`); }
    if (this.filters.controls.q.value.trim()) { filters.push(`Búsqueda: ${this.filters.controls.q.value.trim()}`); }
    return filters;
  }
  audienceLabel(value: AudienceCode): string { return ({ WOMEN: 'Mujer', MEN: 'Hombre', UNISEX: 'Unisex' } as Record<AudienceCode, string>)[value]; }

  private get activeSeason() { const id = this.toNumber(this.filters.controls.season_id.value); return id ? this.navigation?.seasons.find((season) => season.id === id) || null : null; }
  private get activeCollection() {
    const id = this.toNumber(this.filters.controls.collection_id.value);
    if (!id) { return null; }
    const seasons = this.activeSeason ? [this.activeSeason] : this.navigation?.seasons || [];
    return seasons.flatMap((season) => season.collections).find((collection) => collection.id === id) || null;
  }
  private findOptionName(options: CatalogFilterOption[], rawId: string): string | null { const id = Number(rawId); return options.find((option) => option.id === id)?.name || null; }
  private toNumber(value: string): number | undefined { const parsed = Number(value); return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined; }
}
