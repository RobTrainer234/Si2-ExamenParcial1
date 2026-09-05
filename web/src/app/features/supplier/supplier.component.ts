import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { appConfig } from '../../core/config/app-config';
import { SupplierPortal, SupplierSupplyOffer } from '../../core/models/api.models';

@Component({
  selector: 'app-supplier',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section class="admin-page supplier-portal-page">
      @if (portal) {
        <div class="admin-heading"><div><p class="eyebrow">Portal de proveedor</p><h1>{{ portal.trade_name }}</h1><p class="admin-subtitle">Consulta los productos asociados a tu cuenta.</p></div><span class="master-count">{{ portal.products.length }} productos</span></div>
        <div class="supplier-portal-grid">@for (product of portal.products; track product.id) { <article class="supplier-portal-card"><span class="material-symbols-outlined">checkroom</span><div><strong>{{ product.name }}</strong><small>{{ product.code }}</small></div><span class="status-pill" [class.active]="product.is_active">{{ product.is_active ? 'Activo' : 'Inactivo' }}</span></article> } @empty { <p class="master-empty">Aún no tienes productos asociados.</p> }</div>
        <div class="supplier-offers-heading"><div><p class="eyebrow">Disponibilidad</p><h2>Ofertas de abastecimiento</h2></div><span class="master-count">{{ offers.length }} ofertas</span></div>
        <div class="supplier-offer-list">@for (offer of offers; track offer.id) { <article class="supplier-offer-card"><div><strong>{{ offer.product_name }}</strong><small>{{ offer.sku }} · {{ offer.size_name }} · {{ offer.color_name }}</small><small>{{ offer.season_name }}{{ offer.collection_name ? ' · ' + offer.collection_name : '' }}</small></div><label>Estado<select [(ngModel)]="offer.status"><option value="AVAILABLE">Disponible</option><option value="LIMITED">Limitado</option><option value="OUT_OF_STOCK">Agotado</option><option value="UPCOMING">Próximo</option></select></label><label>Cantidad<input type="number" min="0" [(ngModel)]="offer.available_quantity"></label><label>Fecha<input type="date" [(ngModel)]="offer.expected_date"></label><label>Notas<input [(ngModel)]="offer.notes" maxlength="1000"></label><button class="small-button" type="button" (click)="save(offer)">Guardar</button></article> } @empty { <p class="master-empty">No hay ofertas de abastecimiento registradas.</p> }</div>
      } @else { <p class="master-empty">Cargando información del proveedor...</p> }
    </section>
  `,
})
export class SupplierComponent {
  private readonly http = inject(HttpClient);
  portal: SupplierPortal | null = null;
  offers: SupplierSupplyOffer[] = [];

  constructor() { this.http.get<SupplierPortal>(`${appConfig.apiBaseUrl}/suppliers/me`).subscribe({ next: (portal) => { this.portal = portal; this.http.get<SupplierSupplyOffer[]>(`${appConfig.apiBaseUrl}/suppliers/me/offers`).subscribe({ next: (offers) => this.offers = offers }); } }); }
  save(offer: SupplierSupplyOffer): void { this.http.patch<SupplierSupplyOffer>(`${appConfig.apiBaseUrl}/suppliers/me/offers/${offer.id}`, { status: offer.status, available_quantity: offer.available_quantity, expected_date: offer.expected_date || null, notes: offer.notes || null }).subscribe({ next: (updated) => Object.assign(offer, updated) }); }
}
