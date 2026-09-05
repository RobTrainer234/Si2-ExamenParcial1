import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AudienceCode, CatalogFilterOption, CatalogItem } from '../../core/models/api.models';
import { CatalogService } from '../../core/catalog/catalog.service';

@Component({
  standalone: true,
  imports: [CurrencyPipe, ReactiveFormsModule, RouterLink],
  template: `
    <section class="catalog-hero">
      <div class="hero-copy-block"><p class="eyebrow">FashionStore / Colección actual</p><h1>Encuentra lo que<br><em>te representa.</em></h1><p class="hero-copy">Prendas seleccionadas para acompañar tu estilo todos los días, disponibles en nuestras sucursales.</p></div>
      <div class="hero-index"><span>01</span><span>Catálogo<br>abierto</span></div>
    </section>
    <section class="lookbook-banner"><div><p class="eyebrow">Curaduría FashionStore</p><h2>Texturas, cortes y piezas<br><em>para vivir tu temporada.</em></h2></div><span class="material-symbols-outlined">arrow_outward</span></section>
   <section class="catalog-tools">
      <form [formGroup]="filters" (ngSubmit)="search()" class="search-form">
         <label class="search-box"><span class="material-symbols-outlined">search</span><input formControlName="q" placeholder="Buscar prendas, códigos..." aria-label="Buscar prendas"></label>
        <label>Categoría<select formControlName="category_id"><option value="">Todas</option>@for (option of categories; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
        <label>Sucursal<select formControlName="branch_id"><option value="">Todas</option>@for (option of branches; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
        <button class="button button-dark" type="submit">Buscar</button>
      </form>
       @if (!loading && !error) { <p class="result-count">{{ total }} prendas encontradas</p> }
    </section>
     <section class="catalog-filters" aria-label="Filtros del catálogo">
       <div class="catalog-filter-section category-section"><span class="filter-section-label">Categorías</span><div class="catalog-ribbon"><button class="ribbon-chip" [class.active]="!filters.controls.category_id.value" (click)="clearCategory()">Todo</button>@for (category of categories; track category.id) { <button class="ribbon-chip" [class.selected]="isFilterSelected('category_id', category.id)" (click)="setCategory(category.id)">{{ category.name }}</button> }</div></div>
       <div class="catalog-filter-row">
         <div class="quick-filter-group"><span class="filter-section-label">Tallas</span><div class="filter-options">@for (option of sizes; track option.id) { <button [class.selected]="isFilterSelected('size_id', option.id)" (click)="setQuickFilter('size_id', option.id)">{{ option.name }}</button> }</div></div>
         <div class="quick-filter-group color-filter"><span class="filter-section-label">Colores</span><div class="filter-options">@for (option of colors; track option.id) { <button [class.selected]="isFilterSelected('color_id', option.id)" [style.--swatch]="option.hex_code || '#b7aea3'" [attr.aria-label]="option.name" [title]="option.name" (click)="setQuickFilter('color_id', option.id)"></button> }</div></div>
       </div>
     </section>
     @if (activeAudience) { <div class="catalog-context"><span class="audience-pill">{{ audienceLabel(activeAudience) }}</span>@if (activeSort === 'newest') { <span class="context-divider">/</span><span>Novedades</span> }</div> }
     <p class="branch-context"><span class="material-symbols-outlined">storefront</span><span class="filter-section-label">Sucursal</span><strong>{{ selectedBranchName }}</strong></p>
     @if (error) { <p class="error page-message">No se pudo cargar el catálogo. Intenta nuevamente.</p> }
     @if (loading) { <section class="catalog-loading" aria-label="Cargando colección"><p class="loading-label">Cargando colección...</p><div class="loading-grid">@for (placeholder of loadingPlaceholders; track placeholder) { <div class="loading-card"><div class="loading-image"></div><div class="loading-line short"></div><div class="loading-line"></div></div> }</div></section> }
     @if (!loading && !error && products.length === 0) { <p class="empty page-message">No encontramos prendas con esos filtros.</p> }
     @if (!loading && !error && products.length > 0) { <section class="catalog-heading"><span class="eyebrow">Piezas seleccionadas</span><span>{{ total }} prendas · orden editorial</span></section> }
     @if (!loading && !error) { <section class="product-grid">
      @for (product of products; track product.id) {
        <a class="product-card" [routerLink]="['/catalog', product.id]">
           <div class="product-image"><img [src]="product.image_url || placeholder" [alt]="product.name" (error)="usePlaceholder($event)"><span class="editorial-mark">{{ product.image_url ? 'Nueva pieza' : 'Sin imagen' }}</span><button class="favorite-button" [class.is-favorite]="favorites.has(product.id)" [attr.aria-label]="favorites.has(product.id) ? 'Quitar de favoritos' : 'Guardar producto'" type="button" (click)="toggleFavorite($event, product.id)"><span class="material-symbols-outlined">favorite</span></button></div>
          <div class="product-meta"><span class="category-label">{{ product.category_name }}</span><h2>{{ product.name }}</h2><strong>{{ product.price | currency:'BOB':'symbol':'1.2-2' }}</strong></div>
        </a>
      }
     </section> }
    @if (totalPages > 1) {
      <nav class="pagination" aria-label="Paginación">
        <button class="button button-light" [disabled]="page === 1" (click)="goTo(page - 1)">Anterior</button>
        <span>Página {{ page }} de {{ totalPages }}</span>
        <button class="button button-light" [disabled]="page === totalPages" (click)="goTo(page + 1)">Siguiente</button>
      </nav>
    }
  `,
})
export class CatalogComponent {
  private readonly catalog = inject(CatalogService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  readonly filters = inject(FormBuilder).nonNullable.group({ q: [''], category_id: [''], size_id: [''], color_id: [''], branch_id: [''], audience: [''], season_id: [''], collection_id: [''], sort: ['editorial'] });
  products: CatalogItem[] = [];
  page = 1;
  total = 0;
  totalPages = 0;
  categories: CatalogFilterOption[] = [];
  sizes: CatalogFilterOption[] = [];
  colors: CatalogFilterOption[] = [];
  branches: CatalogFilterOption[] = [];
  loading = false;
  error = false;
  readonly favorites = new Set<number>();
  readonly loadingPlaceholders = [1, 2, 3, 4];
  get selectedBranchName(): string { const id = Number(this.filters.controls.branch_id.value); return this.branches.find((branch) => branch.id === id)?.name || 'Todas las sucursales'; }
  readonly placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="600" height="700" viewBox="0 0 600 700"%3E%3Crect width="600" height="700" fill="%23eee9e1"/%3E%3Ctext x="300" y="350" text-anchor="middle" fill="%2390887e" font-size="24"%3EFashionStore%3C/text%3E%3C/svg%3E';
  private readonly route = inject(ActivatedRoute);

  constructor() {
    this.catalog.filters().subscribe({ next: (filters) => { this.categories = filters.categories; this.sizes = filters.sizes; this.colors = filters.colors; this.branches = filters.branches; }, error: () => undefined });
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

  get activeAudience(): AudienceCode | null { const value = this.filters.controls.audience.value; return value === 'WOMEN' || value === 'MEN' || value === 'UNISEX' ? value : null; }
  get activeSort(): string { return this.filters.controls.sort.value; }
  audienceLabel(value: AudienceCode): string { return ({ WOMEN: 'Mujer', MEN: 'Hombre', UNISEX: 'Unisex' } as Record<AudienceCode, string>)[value]; }

  private toNumber(value: string): number | undefined { const parsed = Number(value); return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined; }
}
