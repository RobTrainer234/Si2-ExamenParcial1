import { Component, HostListener, OnDestroy, inject, signal } from '@angular/core';
import { NavigationStart, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SwUpdate } from '@angular/service-worker';
import { Subscription, filter } from 'rxjs';

import { AdminService } from './core/admin/admin.service';
import { AuthService } from './core/auth/auth.service';
import { CatalogService } from './core/catalog/catalog.service';
import { CommerceService } from './core/commerce/commerce.service';
import { AudienceCode, CatalogNavigation, NavigationSeason } from './core/models/api.models';
import { NotificationService } from './core/notifications/notification.service';
import { AiChatWidgetComponent } from './features/chat/ai-chat-widget.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, RouterOutlet, AiChatWidgetComponent],
  template: `
    <header class="site-header">
      <div class="header-container">
        <!-- Izquierda: Brand Boutique + Botón Explorar Colecciones -->
        <div class="header-left">
          <a class="brand" routerLink="/" (click)="closeAllMenus()">
            <span class="brand-monogram">F</span>
            <div class="brand-text">
              <strong class="brand-name">FashionStore</strong>
              <small class="brand-tagline">{{ isLandingContext ? 'Plataforma SaaS · Indumentaria' : (auth.currentUser()?.tenant?.name || 'Atelier & Boutique') }}</small>
            </div>
          </a>
          @if (!isLandingContext && auth.currentUser()?.role !== 'PLATFORM_ADMIN') {
            <button class="catalog-trigger-btn" type="button" (click)="toggleMenu()" aria-label="Abrir catálogo completo">
              <span class="material-symbols-outlined">{{ menuOpen ? 'close' : 'apps' }}</span>
              <span>Colecciones</span>
            </button>
          }
        </div>

        <!-- Centro: Enlaces directos de navegación contextual -->
        @if (isLandingContext) {
          <nav class="header-nav-center" aria-label="Navegación de plataforma SaaS">
            <a href="#beneficios">
              <span class="material-symbols-outlined">verified</span>
              <span>Beneficios</span>
            </a>
            <a href="#planes">
              <span class="material-symbols-outlined">workspace_premium</span>
              <span>Planes y Prueba</span>
            </a>
            <a routerLink="/catalog">
              <span class="material-symbols-outlined">diamond</span>
              <span>Catálogo Demo</span>
            </a>
          </nav>
        } @else {
          <nav class="header-nav-center" aria-label="Navegación principal">
            <a routerLink="/catalog" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: false }">
              <span class="material-symbols-outlined">diamond</span>
              <span>Catálogo</span>
            </a>
            @if (auth.currentUser()?.role !== 'PLATFORM_ADMIN') {
              <a routerLink="/fitting-bag" routerLinkActive="active">
                <span class="material-symbols-outlined">checkroom</span>
                <span>Probador Virtual</span>
              </a>
            }
            @if (auth.isAuthenticated() && auth.currentUser()?.role === 'CLIENT') {
              <a routerLink="/my-reservations" routerLinkActive="active">
                <span class="material-symbols-outlined">calendar_month</span>
                <span>Mis Reservas</span>
              </a>
            }
            @if (auth.currentUser()?.role === 'PLATFORM_ADMIN') {
              <a routerLink="/platform" routerLinkActive="active">
                <span class="material-symbols-outlined">domain</span>
                <span>Consola SaaS</span>
              </a>
            }
          </nav>
        }

        <!-- Derecha: Gestión operativa + Carrito + Usuario -->
        <div class="header-right">
          @if (auth.currentUser()?.role === 'PLATFORM_ADMIN') {
            <a routerLink="/platform" class="management-trigger-btn" routerLinkActive="active">
              <span class="material-symbols-outlined">admin_panel_settings</span>
              <span>Gobernanza SaaS</span>
            </a>
          }
          @if (isStaffOrAdmin) {
            <div class="management-dropdown-wrapper">
              <button 
                type="button" 
                class="management-trigger-btn" 
                [class.active]="managementDropdownOpen" 
                (click)="toggleManagementDropdown($event)"
                aria-haspopup="true"
                [attr.aria-expanded]="managementDropdownOpen"
              >
                <span class="material-symbols-outlined">dashboard_customize</span>
                <span>Gestión Operativa</span>
                @if (pendingReservationsCount > 0) {
                  <span class="nav-badge" title="Reservas pendientes de atención">{{ pendingReservationsCount }}</span>
                }
                <span class="material-symbols-outlined dropdown-arrow">{{ managementDropdownOpen ? 'expand_less' : 'expand_more' }}</span>
              </button>

              @if (managementDropdownOpen) {
                <div class="management-dropdown-menu" (click)="$event.stopPropagation()">
                  <div class="dropdown-column">
                    <div class="dropdown-section-title">
                      <span class="material-symbols-outlined">insights</span>
                      <span>Estratégico</span>
                    </div>
                    @if (auth.currentUser()?.role === 'ADMIN') {
                      <a routerLink="/cycle-3-admin" routerLinkActive="active" (click)="closeAllMenus()">
                        <span class="material-symbols-outlined">analytics</span>
                        <div>
                          <strong>Dashboard & Reportes IA</strong>
                          <small>KPIs, ventas, descuentos y Sofía IA</small>
                        </div>
                      </a>
                      <a routerLink="/admin" routerLinkActive="active" (click)="closeAllMenus()">
                        <span class="material-symbols-outlined">tune</span>
                        <div>
                          <strong>Centro de Control</strong>
                          <small>Sucursales, productos y precios</small>
                        </div>
                      </a>
                      <a routerLink="/audit" routerLinkActive="active" (click)="closeAllMenus()">
                        <span class="material-symbols-outlined">policy</span>
                        <div>
                          <strong>Bitácora de Auditoría</strong>
                          <small>Registro inmutable y seguridad</small>
                        </div>
                      </a>
                    }
                  </div>

                  <div class="dropdown-column">
                    <div class="dropdown-section-title">
                      <span class="material-symbols-outlined">store</span>
                      <span>Sucursal & Tienda</span>
                    </div>
                    @if (auth.hasPermission('sales.create')) {
                      <a routerLink="/pos" routerLinkActive="active" (click)="closeAllMenus()">
                        <span class="material-symbols-outlined">point_of_sale</span>
                        <div>
                          <strong>Caja y Devoluciones</strong>
                          <small>Terminal POS, cobro y kárdex</small>
                        </div>
                      </a>
                    }
                    @if (auth.hasPermission('reservations.manage')) {
                      <a routerLink="/reservations" routerLinkActive="active" (click)="closeAllMenus()">
                        <span class="material-symbols-outlined">event_available</span>
                        <div>
                          <strong>Atención de Reservas</strong>
                          <small>Cola en vivo de probadores</small>
                        </div>
                        @if (pendingReservationsCount > 0) {
                          <span class="nav-badge">{{ pendingReservationsCount }}</span>
                        }
                      </a>
                    }
                    @if (auth.hasPermission('inventory.read')) {
                      <a routerLink="/operations" routerLinkActive="active" (click)="closeAllMenus()">
                        <span class="material-symbols-outlined">inventory_2</span>
                        <div>
                          <strong>Inventario & Kárdex</strong>
                          <small>Stock multi-sucursal y ajustes</small>
                        </div>
                      </a>
                    }
                  </div>

                  @if (auth.hasPermission('suppliers.manage') || auth.hasPermission('suppliers.portal')) {
                    <div class="dropdown-column">
                      <div class="dropdown-section-title">
                        <span class="material-symbols-outlined">local_shipping</span>
                        <span>Proveedores</span>
                      </div>
                      @if (auth.hasPermission('suppliers.manage')) {
                        <a routerLink="/supply" routerLinkActive="active" (click)="closeAllMenus()">
                          <span class="material-symbols-outlined">add_shopping_cart</span>
                          <div>
                            <strong>Abastecimiento</strong>
                            <small>Recepción y compras mayoristas</small>
                          </div>
                        </a>
                      }
                      @if (auth.hasPermission('suppliers.portal')) {
                        <a routerLink="/supplier" routerLinkActive="active" (click)="closeAllMenus()">
                          <span class="material-symbols-outlined">badge</span>
                          <div>
                            <strong>Portal del Proveedor</strong>
                            <small>Entregas y catálogos vinculados</small>
                          </div>
                        </a>
                      }
                    </div>
                  }
                </div>
              }
            </div>
          }

          <!-- Carrito de compras (solo contexto tienda/cliente) -->
          @if (!isLandingContext && auth.currentUser()?.role !== 'PLATFORM_ADMIN') {
            <a routerLink="/cart" class="header-cart-btn" aria-label="Ver carrito" (click)="closeAllMenus()">
              <span class="material-symbols-outlined">shopping_bag</span>
              @if (cartItemsCount > 0) {
                <span class="cart-badge">{{ cartItemsCount }}</span>
              }
            </a>
          }

          <!-- Semáforo de Conectividad Online/Offline -->
          <a routerLink="/offline-transactions" class="header-status-indicator" [class.status-offline]="!isOnline()" [title]="isOnline() ? 'Sistema conectado al servidor (Online)' : 'Sistema sin conexión a internet (Offline). Haz clic para ver operaciones pendientes.'">
            <span class="status-indicator-dot"></span>
            <span class="status-indicator-label">{{ isOnline() ? 'Online' : 'Offline' }}</span>
          </a>

          <!-- Perfil de usuario o Login -->
          @if (auth.isAuthenticated()) {
            <div class="user-pill-wrapper">
              <button 
                type="button" 
                class="user-pill-btn" 
                (click)="toggleUserDropdown($event)"
                aria-haspopup="true"
                [attr.aria-expanded]="userDropdownOpen"
              >
                <div class="user-avatar">{{ userInitials }}</div>
                <div class="user-info">
                  <span class="user-name">{{ auth.currentUser()?.first_name }}</span>
                  <span class="user-role-badge">{{ roleBadgeText }}</span>
                </div>
                <span class="material-symbols-outlined user-chevron">{{ userDropdownOpen ? 'expand_less' : 'expand_more' }}</span>
              </button>

              @if (userDropdownOpen) {
                <div class="user-dropdown-card" (click)="$event.stopPropagation()">
                  <div class="user-dropdown-header">
                    <strong>{{ auth.currentUser()?.first_name }} {{ auth.currentUser()?.last_name }}</strong>
                    <small>{{ auth.currentUser()?.email }}</small>
                    @if (auth.currentUser()?.tenant?.name) {
                      <small>{{ auth.currentUser()?.tenant?.name }}</small>
                    }
                    <span class="role-tag">{{ roleBadgeText }}</span>
                  </div>
                  <div class="user-dropdown-actions">
                    <a [routerLink]="auth.defaultHomeRoute()" (click)="closeAllMenus()" class="dropdown-action-link">
                      <span class="material-symbols-outlined">space_dashboard</span>
                      <span>Ir a mi espacio principal</span>
                    </a>
                    @if (auth.currentUser()?.role === 'CLIENT') {
                      <a routerLink="/my-reservations" (click)="closeAllMenus()" class="dropdown-action-link">
                        <span class="material-symbols-outlined">history</span>
                        <span>Historial de reservas</span>
                      </a>
                    }
                    <button type="button" class="logout-btn" (click)="logout()">
                      <span class="material-symbols-outlined">logout</span>
                      <span>Cerrar sesión</span>
                    </button>
                  </div>
                </div>
              }
            </div>
          } @else {
            <div class="auth-buttons">
              <a routerLink="/login" class="login-link" (click)="closeAllMenus()">Ingresar</a>
              @if (isLandingContext) {
                <a routerLink="/register-company" class="register-cta" (click)="closeAllMenus()">Probar 14 días</a>
              } @else {
                <a routerLink="/register" class="login-link" (click)="closeAllMenus()">Cuenta cliente</a>
                <a routerLink="/register-company" class="register-cta" (click)="closeAllMenus()">Prueba empresas</a>
              }
            </div>
          }
        </div>
      </div>
    </header>

    <!-- Mega-Menú Modal Flotante de Colecciones y Catálogo -->
    @if (menuOpen) {
      <div class="mega-menu-backdrop" (click)="closeMenu()">
        <div class="mega-menu-modal" (click)="$event.stopPropagation()" role="dialog" aria-modal="true" aria-labelledby="catalog-menu-title">
          <div class="mega-menu-header">
            <div class="mega-menu-title-wrap">
              <span class="mega-kicker">Catálogo Exclusivo</span>
              <h2 id="catalog-menu-title">Explorar FashionStore</h2>
            </div>
            <button class="mega-close-btn" type="button" (click)="closeMenu()" aria-label="Cerrar menú de catálogo">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          @if (navigation) {
            <div class="mega-audience-tabs" role="tablist">
              @for (audience of navigation.audiences; track audience.code) {
                <button
                  type="button"
                  class="mega-tab-btn"
                  [class.active]="menuAudience === audience.code"
                  (click)="menuAudience = audience.code"
                >
                  <span>{{ audience.name }}</span>
                  <span class="mega-tab-count">{{ audience.product_count }}</span>
                </button>
              }
            </div>

            <div class="mega-menu-content">
              <!-- Accesos directos / destacados -->
              <section class="mega-quick-section" aria-label="Explorar accesos directos">
                <div class="section-title">
                  <span class="material-symbols-outlined">explore</span>
                  <h3>Explorar</h3>
                </div>
                <div class="mega-quick-links">
                  <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience }" (click)="closeMenu()" class="quick-link-card">
                    <span class="material-symbols-outlined">grid_view</span>
                    <div>
                      <strong>Todo el catálogo</strong>
                      <small>Ver todas las prendas de {{ currentAudienceName }}</small>
                    </div>
                  </a>
                  <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience, sort: 'newest' }" (click)="closeMenu()" class="quick-link-card">
                    <span class="material-symbols-outlined">auto_awesome</span>
                    <div>
                      <strong>Novedades</strong>
                      <small>Últimos lanzamientos de temporada</small>
                    </div>
                  </a>
                  <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience }" fragment="stores" (click)="closeMenu()" class="quick-link-card">
                    <span class="material-symbols-outlined">storefront</span>
                    <div>
                      <strong>Disponible en sucursales</strong>
                      <small>Consulta stock en sucursales físicas</small>
                    </div>
                  </a>
                </div>
              </section>

              <div class="mega-grid-panels">
                <!-- Temporadas y Colecciones -->
                <div class="mega-panel-section">
                  <div class="section-title">
                    <span class="material-symbols-outlined">style</span>
                    <h3>Colecciones</h3>
                    <small class="section-badge">{{ collectionTotal() }} prendas</small>
                  </div>
                  <div class="mega-seasons-list">
                    @for (season of navigation.seasons; track season.id) {
                      <div class="mega-season-card">
                        <div class="mega-season-name">
                          <strong>{{ season.name }}</strong>
                          <small>{{ seasonTotal(season) }} prendas</small>
                        </div>
                        <div class="mega-collection-links">
                          @for (collection of season.collections; track collection.id) {
                            <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience, collection_id: collection.id }" (click)="closeMenu()">
                              <span>{{ collection.name }}</span>
                              <span class="item-count">{{ collection.product_count }}</span>
                            </a>
                          }
                        </div>
                      </div>
                    }
                  </div>
                </div>

                <!-- Categorías -->
                <div class="mega-panel-section">
                  <div class="section-title">
                    <span class="material-symbols-outlined">category</span>
                    <h3>Categorías</h3>
                    <small class="section-badge">{{ navigation.categories.length }} opciones</small>
                  </div>
                  <div class="mega-categories-grid">
                    @for (category of navigation.categories; track category.id) {
                      <a [routerLink]="['/catalog']" [queryParams]="{ audience: menuAudience, category_id: category.id }" (click)="closeMenu()" class="mega-category-pill">
                        <span class="material-symbols-outlined pill-icon">checkroom</span>
                        <span>{{ category.name }}</span>
                      </a>
                    }
                  </div>
                </div>
              </div>
            </div>
          } @else {
            <div class="mega-loading">
              <span class="material-symbols-outlined spinning">sync</span>
              <p>Cargando catálogo...</p>
            </div>
          }
        </div>
      </div>
    }

    <main class="page-shell"><router-outlet></router-outlet></main>
    <app-ai-chat-widget />

    <section class="toast-host" aria-live="polite" aria-label="Notificaciones">
      @for (notification of notifications.messages(); track notification.id) {
        <button class="toast" [class.toast-success]="notification.kind === 'success'" [class.toast-error]="notification.kind === 'error'" type="button" (click)="notifications.dismiss(notification.id)">
          <span class="material-symbols-outlined">{{ notification.kind === 'success' ? 'check_circle' : 'error' }}</span>
          <span>{{ notification.message }}</span>
        </button>
      }
    </section>

    <!-- Barra de navegación inferior para móviles -->
    <nav class="mobile-nav" aria-label="Navegación móvil">
      <a routerLink="/catalog" routerLinkActive="active" (click)="closeAllMenus()">
        <span class="material-symbols-outlined">diamond</span>
        <small>Catálogo</small>
      </a>
      <a routerLink="/fitting-bag" routerLinkActive="active" (click)="closeAllMenus()">
        <span class="material-symbols-outlined">checkroom</span>
        <small>Probador</small>
      </a>
      <a routerLink="/cart" routerLinkActive="active" (click)="closeAllMenus()" class="mobile-cart-link">
        <span class="material-symbols-outlined">shopping_bag</span>
        @if (cartItemsCount > 0) {
          <span class="mobile-badge">{{ cartItemsCount }}</span>
        }
        <small>Carrito</small>
      </a>
      @if (isStaffOrAdmin) {
        <a routerLink="/cycle-3-admin" routerLinkActive="active" (click)="closeAllMenus()">
          <span class="material-symbols-outlined">analytics</span>
          <small>Gestión</small>
        </a>
      }
      @if (auth.isAuthenticated()) {
        <button type="button" class="mobile-user-link" (click)="toggleUserDropdown($event)">
          <span class="material-symbols-outlined">account_circle</span>
          <small>{{ auth.currentUser()?.first_name }}</small>
        </button>
      } @else {
        <a routerLink="/login" routerLinkActive="active" (click)="closeAllMenus()">
          <span class="material-symbols-outlined">login</span>
          <small>Acceder</small>
        </a>
      }
    </nav>

    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <strong>FASHIONSTORE · ATELIER & BOUTIQUE</strong>
          <span>Plataforma Inteligente de Comercio Electrónico con Vestidores Virtuales</span>
        </div>
        <div class="footer-links">
          <span>Sistemas de Información II — UAGRM</span>
          <span>Elegir bien. Vestir mejor.</span>
        </div>
      </div>
    </footer>
  `,
})
export class AppComponent implements OnDestroy {
  readonly auth = inject(AuthService);
  private readonly catalog = inject(CatalogService);
  private readonly admin = inject(AdminService);
  private readonly commerce = inject(CommerceService);
  readonly notifications = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly routerEvents: Subscription;
  private reservationTimer: ReturnType<typeof setInterval> | null = null;
  private previousPendingCount = 0;

  navigation: CatalogNavigation | null = null;
  private readonly swUpdate = inject(SwUpdate, { optional: true });

  menuOpen = false;
  managementDropdownOpen = false;
  userDropdownOpen = false;
  menuAudience: AudienceCode | null = null;
  pendingReservationsCount = 0;
  cartItemsCount = 0;
  readonly isOnline = signal<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.isOnline.set(true));
      window.addEventListener('offline', () => this.isOnline.set(false));
    }

    if (this.swUpdate?.isEnabled) {
      this.swUpdate.versionUpdates.subscribe((evt) => {
        if (evt.type === 'VERSION_READY') {
          this.swUpdate?.activateUpdate().then(() => document.location.reload());
        }
      });
      this.swUpdate.checkForUpdate().catch(() => undefined);
    }

    this.catalog.navigation().subscribe({
      next: (navigation) => {
        this.navigation = navigation;
        this.menuAudience = navigation.audiences.find((item) => item.product_count > 0)?.code || 'WOMEN';
      },
      error: () => undefined,
    });

    this.loadCartCount();

    this.routerEvents = this.router.events.pipe(filter((event) => event instanceof NavigationStart)).subscribe(() => {
      this.closeAllMenus();
      this.checkPendingReservations();
      this.loadCartCount();
    });

    this.checkPendingReservations();
    this.reservationTimer = setInterval(() => {
      this.checkPendingReservations();
      this.loadCartCount();
    }, 45000);
  }

  loadCartCount(): void {
    if (!this.auth.isAuthenticated() || !this.auth.hasPermission('cart.manage')) {
      this.cartItemsCount = 0;
      return;
    }
    this.commerce.cart().subscribe({
      next: (cart) => {
        this.cartItemsCount = cart.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
      },
      error: () => {
        this.cartItemsCount = 0;
      },
    });
  }

  private checkPendingReservations(): void {
    if (!this.auth.isAuthenticated() || !this.auth.hasPermission('reservations.manage')) {
      this.pendingReservationsCount = 0;
      this.previousPendingCount = 0;
      return;
    }

    this.admin.reservationBranches().subscribe({
      next: (branchesPage) => {
        if (!branchesPage.items || branchesPage.items.length === 0) return;
        const branch = branchesPage.items[0];
        this.admin.reservations(branch.id, 'PENDING').subscribe({
          next: (page) => {
            const count = page.total ?? page.items?.length ?? 0;
            if (count > this.previousPendingCount && this.previousPendingCount > 0) {
              this.notifications.success(`¡Hay ${count} reserva(s) pendientes de atención en ${branch.name}!`);
            }
            this.previousPendingCount = count;
            this.pendingReservationsCount = count;
          },
          error: () => undefined,
        });
      },
      error: () => undefined,
    });
  }

  get currentAudienceName(): string {
    return this.navigation?.audiences.find((a) => a.code === this.menuAudience)?.name || 'Colección';
  }

  get userInitials(): string {
    const user = this.auth.currentUser();
    if (!user) return 'FS';
    const first = user.first_name ? user.first_name.charAt(0) : '';
    const last = user.last_name ? user.last_name.charAt(0) : '';
    return (first + last).toUpperCase() || 'U';
  }

  get isLandingContext(): boolean {
    const path = (this.router.url || '/').split('?')[0].split('#')[0];
    return path === '/' || path === '' || path === '/register-company';
  }

  get roleBadgeText(): string {
    const role = this.auth.currentUser()?.role;
    switch (role) {
      case 'PLATFORM_ADMIN': return 'Superadmin SaaS';
      case 'ADMIN': return 'Administrador';
      case 'BRANCH_MANAGER':
      case 'OPERATOR': return 'Encargado';
      case 'CASHIER':
      case 'SELLER': return 'Cajero';
      case 'CLIENT': return 'Cliente';
      case 'SUPPLIER': return 'Proveedor';
      default: return role || 'Usuario';
    }
  }

  get isStaffOrAdmin(): boolean {
    const role = this.auth.currentUser()?.role;
    return role === 'ADMIN' ||
      this.auth.hasPermission('sales.create') ||
      this.auth.hasPermission('inventory.read') ||
      this.auth.hasPermission('reservations.manage') ||
      this.auth.hasPermission('suppliers.manage') ||
      this.auth.hasPermission('suppliers.portal');
  }

  toggleMenu(): void {
    this.menuOpen = !this.menuOpen;
    if (this.menuOpen) {
      this.managementDropdownOpen = false;
      this.userDropdownOpen = false;
    }
  }

  openMenu(): void {
    this.menuOpen = true;
    this.managementDropdownOpen = false;
    this.userDropdownOpen = false;
  }

  closeMenu(): void {
    this.menuOpen = false;
  }

  toggleManagementDropdown(event?: MouseEvent): void {
    if (event) event.stopPropagation();
    this.managementDropdownOpen = !this.managementDropdownOpen;
    this.userDropdownOpen = false;
  }

  toggleUserDropdown(event?: MouseEvent): void {
    if (event) event.stopPropagation();
    this.userDropdownOpen = !this.userDropdownOpen;
    this.managementDropdownOpen = false;
  }

  closeAllMenus(): void {
    this.menuOpen = false;
    this.managementDropdownOpen = false;
    this.userDropdownOpen = false;
  }

  @HostListener('document:click')
  onDocumentClick(): void {
    this.managementDropdownOpen = false;
    this.userDropdownOpen = false;
  }

  @HostListener('document:keydown', ['$event'])
  closeMenuWithEscape(event: KeyboardEvent): void {
    if (event.key === 'Escape' || event.key === 'Esc') {
      this.closeAllMenus();
    }
  }

  ngOnDestroy(): void {
    if (this.reservationTimer) {
      clearInterval(this.reservationTimer);
    }
    this.routerEvents.unsubscribe();
  }

  collectionTotal(): number {
    return this.navigation?.seasons.reduce((total, season) => total + this.seasonTotal(season), 0) || 0;
  }

  seasonTotal(season: NavigationSeason): number {
    return season.collections.reduce((total, collection) => total + collection.product_count, 0);
  }

  logout(): void {
    this.auth.logout();
    this.pendingReservationsCount = 0;
    this.cartItemsCount = 0;
    this.closeAllMenus();
    this.router.navigateByUrl('/catalog');
  }
}
