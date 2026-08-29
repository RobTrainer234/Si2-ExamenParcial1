import { Component, inject } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { CatalogFilterOption, CatalogItem } from '../../core/models/api.models';
import { CatalogService } from '../../core/catalog/catalog.service';

@Component({
  standalone: true,
  imports: [CurrencyPipe, ReactiveFormsModule, RouterLink],
  template: `
    <section class="catalog-hero">
      <p class="eyebrow">Colección esencial</p>
      <h1>Encuentra lo que<br><em>te representa.</em></h1>
      <p class="hero-copy">Prendas seleccionadas para acompañar tu estilo todos los días.</p>
    </section>
    <section class="catalog-tools">
      <form [formGroup]="filters" (ngSubmit)="search()" class="search-form">
        <label class="search-box"><span>⌕</span><input formControlName="q" placeholder="Buscar prendas, códigos..." aria-label="Buscar prendas"></label>
        <label>Categoría<select formControlName="category_id"><option value="">Todas</option>@for (option of categories; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
        <label>Talla<select formControlName="size_id"><option value="">Todas</option>@for (option of sizes; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
        <label>Color<select formControlName="color_id"><option value="">Todos</option>@for (option of colors; track option.id) { <option [value]="option.id">{{ option.name }}</option> }</select></label>
        <button class="button button-dark" type="submit">Buscar</button>
      </form>
      <p class="result-count">{{ total }} prendas encontradas</p>
    </section>
    @if (error) { <p class="error page-message">No se pudo cargar el catálogo.</p> }
    @if (loading) { <p class="loading page-message">Cargando colección...</p> }
    @if (!loading && !error && products.length === 0) { <p class="empty page-message">No encontramos prendas con esos filtros.</p> }
    <section class="product-grid">
      @for (product of products; track product.id) {
        <a class="product-card" [routerLink]="['/catalog', product.id]">
          <div class="product-image"><img [src]="product.image_url || placeholder" [alt]="product.name"></div>
          <div class="product-meta"><span class="category-label">{{ product.category_name }}</span><h2>{{ product.name }}</h2><strong>{{ product.price | currency:'BOB':'symbol':'1.2-2' }}</strong></div>
        </a>
      }
    </section>
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
  readonly filters = inject(FormBuilder).nonNullable.group({ q: [''], category_id: [''], size_id: [''], color_id: [''] });
  products: CatalogItem[] = [];
  page = 1;
  total = 0;
  totalPages = 0;
  categories: CatalogFilterOption[] = [];
  sizes: CatalogFilterOption[] = [];
  colors: CatalogFilterOption[] = [];
  loading = false;
  error = false;
  readonly placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="600" height="700" viewBox="0 0 600 700"%3E%3Crect width="600" height="700" fill="%23eee9e1"/%3E%3Ctext x="300" y="350" text-anchor="middle" fill="%2390887e" font-size="24"%3EFashionStore%3C/text%3E%3C/svg%3E';

  constructor() {
    this.catalog.filters().subscribe({ next: (filters) => { this.categories = filters.categories; this.sizes = filters.sizes; this.colors = filters.colors; }, error: () => undefined });
    this.load();
  }

  search(): void { this.page = 1; this.load(); }

  goTo(page: number): void { this.page = page; this.load(); }

  private load(): void {
    this.loading = true;
    this.error = false;
    const raw = this.filters.getRawValue();
    this.catalog.list({ page: this.page, page_size: 12, q: raw.q, category_id: this.toNumber(raw.category_id), size_id: this.toNumber(raw.size_id), color_id: this.toNumber(raw.color_id) }).subscribe({ next: (response) => { this.products = response.items; this.total = response.total; this.totalPages = response.total_pages; this.loading = false; }, error: () => { this.error = true; this.loading = false; } });
  }

  private toNumber(value: string): number | undefined { const parsed = Number(value); return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined; }
}
