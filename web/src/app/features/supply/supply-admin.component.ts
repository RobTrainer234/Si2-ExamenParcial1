import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AdminService } from '../../core/admin/admin.service';
import { Collection, ProductDetail, ProductSummary, Season, Supplier, SupplyOffer, SupplyStatus } from '../../core/models/admin.models';

@Component({
  selector: 'app-supply-admin',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section class="supply-page">
      <div class="admin-heading"><div><p class="eyebrow">Cadena de suministro</p><h1>Abastecimiento</h1><p class="admin-subtitle">Registra qué proveedor puede abastecer cada variante por temporada y colección.</p></div><span class="master-count">{{ offers.length }} ofertas</span></div>
      <form class="supply-form" (ngSubmit)="create()"><label>Proveedor<select [(ngModel)]="form.supplier_id" name="supplier_id" required (change)="loadOffers()"><option [ngValue]="0">Selecciona proveedor</option>@for (supplier of suppliers; track supplier.id) { <option [ngValue]="supplier.id">{{ supplier.trade_name }}</option> }</select></label><label>Producto<select [(ngModel)]="form.product_id" name="product_id" required (change)="loadVariants()"><option [ngValue]="0">Selecciona producto</option>@for (product of products; track product.id) { <option [ngValue]="product.id">{{ product.name }}</option> }</select></label><label>Variante<select [(ngModel)]="form.product_variant_id" name="product_variant_id" required><option [ngValue]="0">Selecciona talla y color</option>@for (variant of variants; track variant.id) { <option [ngValue]="variant.id">{{ variant.size_name }} · {{ variant.color_name }} · {{ variant.sku }}</option> }</select></label><label>Temporada<select [(ngModel)]="form.season_id" name="season_id" required><option [ngValue]="0">Selecciona temporada</option>@for (season of seasons; track season.id) { <option [ngValue]="season.id">{{ season.name }}</option> }</select></label><label>Colección<select [(ngModel)]="form.collection_id" name="collection_id"><option [ngValue]="null">Sin colección</option>@for (collection of collections; track collection.id) { <option [ngValue]="collection.id">{{ collection.name }}</option> }</select></label><label>Estado<select [(ngModel)]="form.status" name="status"><option value="AVAILABLE">Disponible</option><option value="LIMITED">Limitado</option><option value="OUT_OF_STOCK">Agotado</option><option value="UPCOMING">Próximo</option></select></label><label>Cantidad disponible<input [(ngModel)]="form.available_quantity" name="available_quantity" type="number" min="0" required></label><label>Fecha estimada<input [(ngModel)]="form.expected_date" name="expected_date" type="date"></label><label class="supply-notes">Notas<textarea [(ngModel)]="form.notes" name="notes" maxlength="1000"></textarea></label><button class="button button-dark" [disabled]="!canCreate">Registrar oferta</button></form>
      @if (error) { <p class="error admin-alert">{{ error }}</p> }
      <div class="supply-toolbar"><input [(ngModel)]="offerQuery" placeholder="Buscar producto o SKU" aria-label="Buscar oferta"><select [(ngModel)]="offerFilter" aria-label="Filtrar ofertas"><option value="all">Todos los estados</option><option value="AVAILABLE">Disponibles</option><option value="LIMITED">Limitadas</option><option value="OUT_OF_STOCK">Agotadas</option><option value="UPCOMING">Próximas</option></select></div><div class="supply-list">@for (offer of filteredOffers; track offer.id) { <article class="supply-card"><div><strong>{{ offer.product_name }}</strong><small>{{ offer.sku }} · {{ offer.size_name }} · {{ offer.color_name }}</small></div><span>{{ offer.season_name }}{{ offer.collection_name ? ' · ' + offer.collection_name : '' }}</span>@if (editingOfferId === offer.id) { <label class="supply-inline-field">Estado<select [(ngModel)]="offer.status"><option value="AVAILABLE">Disponible</option><option value="LIMITED">Limitado</option><option value="OUT_OF_STOCK">Agotado</option><option value="UPCOMING">Próximo</option></select></label><label class="supply-inline-field">Cantidad<input type="number" min="0" [(ngModel)]="offer.available_quantity"></label><label class="supply-inline-field">Fecha<input type="date" [(ngModel)]="offer.expected_date"></label><button class="small-button" type="button" (click)="saveOffer(offer)">Guardar</button><button class="small-button" type="button" (click)="editingOfferId = null">Cancelar</button> } @else { <span class="status-pill" [class.active]="offer.is_active">{{ statusLabel(offer.status) }} · {{ offer.available_quantity }}</span><button class="small-button" type="button" (click)="editingOfferId = offer.id">Editar</button><button class="small-button" type="button" (click)="toggleOffer(offer)">{{ offer.is_active ? 'Desactivar' : 'Activar' }}</button> }</article> } @empty { <p class="master-empty">Selecciona un proveedor o cambia los filtros.</p> }</div>
    </section>
  `,
})
export class SupplyAdminComponent {
  private readonly api = inject(AdminService);
  suppliers: Supplier[] = [];
  products: ProductSummary[] = [];
  variants: ProductDetail['variants'] = [];
  seasons: Season[] = [];
  collections: Collection[] = [];
  offers: SupplyOffer[] = [];
  offerQuery = ''; offerFilter: 'all' | SupplyStatus = 'all'; editingOfferId: number | null = null; error = '';
  form: { supplier_id: number; product_id: number; product_variant_id: number; season_id: number; collection_id: number | null; status: SupplyStatus; available_quantity: number; expected_date: string; notes: string } = { supplier_id: 0, product_id: 0, product_variant_id: 0, season_id: 0, collection_id: null, status: 'AVAILABLE', available_quantity: 0, expected_date: '', notes: '' };

  constructor() {
    this.api.suppliers().subscribe((page) => this.suppliers = page.items.filter((item) => item.is_active));
    this.api.products().subscribe((page) => this.products = page.items.filter((item) => item.is_active));
    this.api.seasons().subscribe((page) => this.seasons = page.items.filter((item) => item.is_active));
    this.api.collections().subscribe((page) => this.collections = page.items.filter((item) => item.is_active));
  }

  get canCreate(): boolean { return Boolean(this.form.supplier_id && this.form.product_variant_id && this.form.season_id); }
  get filteredOffers(): SupplyOffer[] { const query = this.offerQuery.trim().toLowerCase(); return this.offers.filter((offer) => (this.offerFilter === 'all' || offer.status === this.offerFilter) && (!query || `${offer.product_name} ${offer.sku} ${offer.size_name} ${offer.color_name}`.toLowerCase().includes(query))); }
  loadOffers(): void { if (this.form.supplier_id) this.api.supplyOffers(this.form.supplier_id).subscribe({ next: (offers) => this.offers = offers, error: () => this.error = 'No se pudieron cargar las ofertas.' }); }
  loadVariants(): void { this.variants = []; this.form.product_variant_id = 0; if (this.form.product_id) this.api.product(this.form.product_id).subscribe({ next: (product) => this.variants = product.variants, error: () => this.error = 'No se pudieron cargar las variantes.' }); }
  create(): void { if (!this.canCreate) return; const { product_id, ...data } = this.form; this.api.createSupplyOffer(this.form.supplier_id, { ...data, collection_id: data.collection_id || null, expected_date: data.expected_date || null, notes: data.notes || null }).subscribe({ next: (offer) => { this.offers = [offer, ...this.offers]; this.error = ''; }, error: (response) => this.error = response.error?.detail?.message || 'No se pudo registrar la oferta.' }); }
  saveOffer(offer: SupplyOffer): void { if (!this.form.supplier_id) return; this.api.updateSupplyOffer(this.form.supplier_id, offer.id, { status: offer.status, available_quantity: offer.available_quantity, expected_date: offer.expected_date || null, notes: offer.notes || null }).subscribe({ next: (updated) => { this.offers = this.offers.map((item) => item.id === updated.id ? updated : item); this.editingOfferId = null; this.error = ''; }, error: (response) => this.error = response.error?.detail?.message || 'No se pudo actualizar la oferta.' }); }
  toggleOffer(offer: SupplyOffer): void { if (!this.form.supplier_id) return; this.api.setSupplyOfferActive(this.form.supplier_id, offer.id, !offer.is_active).subscribe({ next: (updated) => this.offers = this.offers.map((item) => item.id === updated.id ? updated : item), error: (response) => this.error = response.error?.detail?.message || 'No se pudo cambiar el estado de la oferta.' }); }
  statusLabel(status: SupplyStatus): string { return ({ AVAILABLE: 'Disponible', LIMITED: 'Limitado', OUT_OF_STOCK: 'Agotado', UPCOMING: 'Próximo' } as Record<SupplyStatus, string>)[status]; }
}
