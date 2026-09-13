import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth/auth.service';
import { CatalogService } from './core/catalog/catalog.service';
import { AudienceCode, CatalogNavigation } from './core/models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterLink, RouterOutlet],
  template: `
     <header class="site-header"><button class="menu-toggle" type="button" (click)="openMenu()" aria-label="Abrir menú de catálogo"><span class="material-symbols-outlined">menu</span></button><a class="brand" routerLink="/catalog"><span>F</span><strong>FashionStore</strong><small>Catálogo</small></a><nav><a routerLink="/catalog" routerLinkActive="active">Colección</a>@if (auth.isAuthenticated()) { <a routerLink="/cart" routerLinkActive="active">Carrito</a> } @if (auth.currentUser()?.role === 'ADMIN') { <a routerLink="/admin" routerLinkActive="active">Administración</a><a routerLink="/audit" routerLinkActive="active">Bitácora</a> } @if (auth.hasPermission('suppliers.manage')) { <a routerLink="/supply" routerLinkActive="active">Abastecimiento</a> } @if (auth.hasPermission('inventory.read') && auth.currentUser()?.role !== 'ADMIN') { <a routerLink="/operations" routerLinkActive="active">Operación</a> } @if (auth.hasPermission('sales.create')) { <a routerLink="/pos" routerLinkActive="active">Caja</a> } @if (auth.hasPermission('reservations.manage')) { <a routerLink="/reservations" routerLinkActive="active">Reservas</a> } @if (auth.hasPermission('suppliers.portal')) { <a routerLink="/supplier" routerLinkActive="active">Proveedor</a> } @if (auth.isAuthenticated()) { <span class="welcome">Hola, {{ auth.currentUser()?.first_name }}</span><button class="text-button" (click)="logout()">Salir</button> } @else { <a routerLink="/login">Ingresar</a><a class="nav-cta" routerLink="/register">Crear cuenta</a> }</nav></header>
    @if (menuOpen) { <div class="catalog-menu-layer"><button class="menu-backdrop" type="button" aria-label="Cerrar menú" (click)="closeMenu()"></button><aside class="catalog-menu" aria-label="Menú del catálogo"><div class="catalog-menu-top"><button class="menu-close" type="button" (click)="closeMenu()" aria-label="Cerrar menú"><span class="material-symbols-outlined">close</span></button><div class="audience-tabs">@for (audience of navigation?.audiences || []; track audience.code) { <a [class.active]="menuAudience === audience.code" [routerLink]="['/catalog']" [queryParams]="{ audience: audience.code }" (click)="menuAudience = audience.code; closeMenu()">{{ audience.name }}<small>{{ audience.product_count }}</small></a> }</div></div><div class="catalog-menu-scroll">@if (navigation) { <section class="menu-section menu-featured"><span class="menu-section-label">Explorar</span><a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience, sort: 'newest' }" (click)="closeMenu()"><strong>Novedades</strong><span class="menu-new">Nuevo</span></a><a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience }" (click)="closeMenu()"><strong>Todo el catálogo</strong></a></section><div class="menu-columns"><section class="menu-section"><span class="menu-section-label">Colecciones</span>@for (season of navigation.seasons; track season.id) { <div class="menu-season"><strong>{{ season.name }}</strong>@for (collection of season.collections; track collection.id) { <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience, collection_id: collection.id }" (click)="closeMenu()">{{ collection.name }}<small>{{ collection.product_count }}</small></a> }</div> }</section><section class="menu-section"><span class="menu-section-label">Categorías</span>@for (category of navigation.categories; track category.id) { <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience, category_id: category.id }" (click)="closeMenu()">{{ category.name }}</a> }</section></div><section class="menu-section menu-discover"><span class="menu-section-label">Descubrir</span><a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience }" fragment="stores" (click)="closeMenu()">Disponible en sucursales <span class="material-symbols-outlined">arrow_outward</span></a></section> } @else { <p class="menu-loading">Cargando navegación...</p> }</div></aside></div> }
    <main class="page-shell"><router-outlet></router-outlet></main>
    <nav class="mobile-nav" aria-label="Navegación móvil"><a routerLink="/catalog" routerLinkActive="active"><span class="material-symbols-outlined">auto_awesome</span><small>Catálogo</small></a><a routerLink="/catalog" fragment="stores"><span class="material-symbols-outlined">storefront</span><small>Tiendas</small></a>@if (auth.currentUser()?.role === 'ADMIN') { <a routerLink="/admin" routerLinkActive="active"><span class="material-symbols-outlined">tune</span><small>Admin</small></a> }<a routerLink="/catalog"><span class="material-symbols-outlined">inventory_2</span><small>Gestión</small></a></nav>
     <footer><span>FASHIONSTORE / CICLO 2</span><span>Elegir bien. Vestir mejor.</span></footer>
  `,
})
export class AppComponent {
  readonly auth = inject(AuthService);
  private readonly catalog = inject(CatalogService);
  private readonly router = inject(Router);
  navigation: CatalogNavigation | null = null;
  menuOpen = false;
  menuAudience: AudienceCode | null = null;

  constructor() { this.catalog.navigation().subscribe({ next: (navigation) => { this.navigation = navigation; this.menuAudience = navigation.audiences.find((item) => item.product_count > 0)?.code || 'WOMEN'; }, error: () => undefined }); }

  openMenu(): void { this.menuOpen = true; }
  closeMenu(): void { this.menuOpen = false; }

  logout(): void { this.auth.logout(); this.router.navigateByUrl('/catalog'); }
}
