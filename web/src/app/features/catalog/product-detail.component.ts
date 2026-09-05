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
      <a class="back-link" routerLink="/catalog"><span class="material-symbols-outlined">arrow_back</span> Volver al catálogo</a>
      <section class="detail-layout">
        <div class="detail-gallery-wrap">
          <div class="detail-gallery-stage">
            @if (product.images.length > 1) {
              <div class="gallery-thumbs gallery-thumbs-vertical" aria-label="Fotos del producto">
                @for (image of product.images; track image.image_url) {
                  <button type="button" [class.active]="selectedImage === image.image_url" (click)="selectedImage = image.image_url" [attr.aria-label]="'Ver foto ' + ($index + 1)"><img [src]="image.image_url" [alt]="product.name + ' ' + ($index + 1)"></button>
                }
              </div>
            }
            <div class="detail-gallery"><img [src]="selectedImage || placeholder" [alt]="product.name"><span class="gallery-counter">{{ selectedImageIndex + 1 }} / {{ product.images.length || 1 }}</span></div>
          </div>
          <div class="product-reference"><span>Ref. {{ product.code }}</span><button type="button" (click)="copyReference()"><span class="material-symbols-outlined">content_copy</span> Copiar</button></div>
          <details class="product-accordion"><summary>Descripción y cuidados <span class="material-symbols-outlined">add</span></summary><p>{{ product.description || 'Una prenda pensada para tu día a día.' }}</p></details>
        </div>
        <div class="detail-content">
          <div class="detail-kicker"><span class="category-label">{{ product.category_name }}</span><span class="detail-audience">{{ audienceLabel }}</span></div>
          <h1>{{ product.name }}</h1>
          <p class="detail-price">{{ product.price | currency:'BOB':'symbol':'1.2-2' }}</p>
          <p class="detail-description">{{ product.description || 'Una prenda pensada para tu día a día.' }}</p>
          <div class="selection">
            <div class="selection-heading"><h3>Color</h3><strong>{{ selectedVariant?.color_name || 'Selecciona un color' }}</strong></div>
            <div class="color-choices">@for (variant of colorOptions; track variant.color_id) { <button type="button" [class.selected]="selectedVariant?.color_id === variant.color_id" [class.unavailable]="!colorAvailable(variant.color_id)" [style.--swatch]="colorSwatch(variant.color_name)" [attr.aria-label]="variant.color_name" [disabled]="!colorAvailable(variant.color_id)" (click)="selectColor(variant.color_id)"></button> }</div>
          </div>
          <div class="selection">
            <div class="selection-heading"><h3>Talla</h3><span>{{ selectedVariant?.available ? (selectedVariant?.stock_total || 0) + ' disponibles' : 'Agotada' }}</span></div>
            <div class="choice-row">@for (variant of sizeOptions; track variant.size_id) { <button type="button" [class.selected]="selectedVariant?.size_id === variant.size_id" [class.unavailable]="!variant.available" [disabled]="!variant.available" (click)="selectSize(variant.size_id)">{{ variant.size_name }}</button> }</div>
          </div>
          <button class="button button-dark availability-button" [disabled]="!selectedVariant || loadingAvailability" (click)="checkAvailability()">{{ loadingAvailability ? 'Consultando...' : 'Ver disponibilidad en tiendas' }}</button>
          @if (availability.length > 0) { <div class="availability-list"><h3>Disponibilidad en tiendas</h3>@for (branch of availability; track branch.branch_id) { <div class="branch-row"><div><strong>{{ branch.branch_name }}</strong><small>{{ branch.city_name }} · {{ branch.address }}</small></div><span [class.in-stock]="branch.available">{{ branch.available ? branch.stock + ' disponibles' : 'Agotado' }}</span></div> }</div> }
          @if (checked && availability.length === 0) { <p class="muted">No hay existencias registradas para esta combinación.</p> }
          <details class="product-accordion detail-accordion"><summary>Envíos y devoluciones <span class="material-symbols-outlined">add</span></summary><p>Consulta la disponibilidad en tu sucursal más cercana antes de visitar la tienda.</p></details>
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
  selectedColorId = 0;
  loading = true;
  loadingAvailability = false;
  checked = false;
  error = false;
  readonly placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="600" height="700" viewBox="0 0 600 700"%3E%3Crect width="600" height="700" fill="%23eee9e1"/%3E%3Ctext x="300" y="350" text-anchor="middle" fill="%2390887e" font-size="24"%3EFashionStore%3C/text%3E%3C/svg%3E';

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.catalog.detail(id).subscribe({ next: (product) => { this.product = product; this.selectedImage = product.images.find((image) => image.is_primary)?.image_url || product.images[0]?.image_url || ''; this.selectedVariant = product.variants.find((variant) => variant.available) || product.variants[0] || null; this.selectedColorId = this.selectedVariant?.color_id || 0; this.loading = false; }, error: () => { this.error = true; this.loading = false; } });
  }

  get selectedImageIndex(): number { return this.product?.images.findIndex((image) => image.image_url === this.selectedImage) ?? 0; }
  get colorOptions(): CatalogVariant[] { return this.uniqueBy(this.product?.variants || [], 'color_id'); }
  get sizeOptions(): CatalogVariant[] { return this.uniqueBy((this.product?.variants || []).filter((variant) => !this.selectedColorId || variant.color_id === this.selectedColorId), 'size_id'); }
  get audienceLabel(): string { return this.product?.audience === 'WOMEN' ? 'Mujer' : this.product?.audience === 'MEN' ? 'Hombre' : 'Unisex'; }
  colorAvailable(colorId: number): boolean { return (this.product?.variants || []).some((item) => item.color_id === colorId && item.available); }
  select(variant: CatalogVariant): void { this.selectedVariant = variant; this.selectedColorId = variant.color_id; this.checked = false; this.availability = []; }
  selectColor(colorId: number): void { const variant = (this.product?.variants || []).find((item) => item.color_id === colorId && item.size_id === this.selectedVariant?.size_id && item.available) || (this.product?.variants || []).find((item) => item.color_id === colorId && item.available); if (variant) this.select(variant); }
  selectSize(sizeId: number): void { const variant = (this.product?.variants || []).find((item) => item.size_id === sizeId && item.color_id === this.selectedColorId); if (variant?.available) this.select(variant); }
  colorSwatch(name: string): string { const value = name.toLowerCase(); return value.includes('negro') || value.includes('black') ? '#1a1918' : value.includes('verde') || value.includes('green') ? '#646f58' : value.includes('terracota') || value.includes('rojo') ? '#9e5a44' : '#c19a6b'; }
  copyReference(): void { if (this.product) navigator.clipboard?.writeText(this.product.code); }
  private uniqueBy(items: CatalogVariant[], key: 'color_id' | 'size_id'): CatalogVariant[] { return items.filter((item, index, values) => values.findIndex((candidate) => candidate[key] === item[key]) === index); }

  checkAvailability(): void {
    if (!this.product || !this.selectedVariant) return;
    this.loadingAvailability = true;
    this.catalog.availability(this.product.id, this.selectedVariant.size_id, this.selectedVariant.color_id).subscribe({ next: (items) => { this.availability = items; this.checked = true; this.loadingAvailability = false; }, error: () => { this.availability = []; this.checked = true; this.loadingAvailability = false; } });
  }
}
