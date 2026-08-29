import { Component, inject } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AvailabilityItem, CatalogDetail, CatalogVariant } from '../../core/models/api.models';
import { CatalogService } from '../../core/catalog/catalog.service';

@Component({
  standalone: true,
  imports: [CurrencyPipe, RouterLink],
  template: `
    @if (loading) { <p class="loading page-message">Cargando producto...</p> }
    @if (error) { <p class="error page-message">No se pudo encontrar el producto.</p> }
    @if (product) {
      <a class="back-link" routerLink="/catalog">← Volver al catálogo</a>
      <section class="detail-layout">
        <div class="detail-gallery"><img [src]="selectedImage || placeholder" [alt]="product.name"></div>
        <div class="detail-content"><span class="category-label">{{ product.category_name }}</span><h1>{{ product.name }}</h1><p class="detail-price">{{ product.price | currency:'BOB':'symbol':'1.2-2' }}</p><p class="detail-description">{{ product.description || 'Una prenda pensada para tu día a día.' }}</p>
          <div class="selection"><h3>Talla</h3><div class="choice-row">@for (variant of product.variants; track variant.id) { <button [class.selected]="selectedVariant?.id === variant.id" (click)="select(variant)">{{ variant.size_name }}</button> }</div></div>
          <div class="selection"><h3>Color</h3><p>{{ selectedVariant?.color_name || 'Selecciona una talla para ver el color' }}</p></div>
          <button class="button button-dark availability-button" [disabled]="!selectedVariant || loadingAvailability" (click)="checkAvailability()">{{ loadingAvailability ? 'Consultando...' : 'Ver disponibilidad en sucursales' }}</button>
          @if (availability.length > 0) { <div class="availability-list"><h3>Disponibilidad</h3>@for (branch of availability; track branch.branch_id) { <div class="branch-row"><div><strong>{{ branch.branch_name }}</strong><small>{{ branch.city_name }} · {{ branch.address }}</small></div><span [class.in-stock]="branch.available">{{ branch.available ? branch.stock + ' disponibles' : 'Agotado' }}</span></div> }</div> }
          @if (checked && availability.length === 0) { <p class="muted">No hay existencias registradas para esta combinación.</p> }
        </div>
      </section>
    }
  `,
})
export class ProductDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly catalog = inject(CatalogService);
  product: CatalogDetail | null = null;
  selectedVariant: CatalogVariant | null = null;
  availability: AvailabilityItem[] = [];
  selectedImage = '';
  loading = true;
  loadingAvailability = false;
  checked = false;
  error = false;
  readonly placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="600" height="700" viewBox="0 0 600 700"%3E%3Crect width="600" height="700" fill="%23eee9e1"/%3E%3Ctext x="300" y="350" text-anchor="middle" fill="%2390887e" font-size="24"%3EFashionStore%3C/text%3E%3C/svg%3E';

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.catalog.detail(id).subscribe({ next: (product) => { this.product = product; this.selectedImage = product.images.find((image) => image.is_primary)?.image_url || product.images[0]?.image_url || ''; this.loading = false; }, error: () => { this.error = true; this.loading = false; } });
  }

  select(variant: CatalogVariant): void { this.selectedVariant = variant; this.checked = false; this.availability = []; }

  checkAvailability(): void {
    if (!this.product || !this.selectedVariant) return;
    this.loadingAvailability = true;
    this.catalog.availability(this.product.id, this.selectedVariant.size_id, this.selectedVariant.color_id).subscribe({ next: (items) => { this.availability = items; this.checked = true; this.loadingAvailability = false; }, error: () => { this.availability = []; this.checked = true; this.loadingAvailability = false; } });
  }
}
