import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { adminGuard, permissionGuard, platformAdminGuard } from './core/auth/role.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', loadComponent: () => import('./features/landing/landing.component').then((module) => module.LandingComponent) },
  { path: 'catalog', loadComponent: () => import('./features/catalog/catalog.component').then((module) => module.CatalogComponent) },
  { path: 'catalog/:id', loadComponent: () => import('./features/catalog/product-detail.component').then((module) => module.ProductDetailComponent) },
  { path: 'cart', canActivate: [authGuard], loadComponent: () => import('./features/commerce/cart.component').then((module) => module.CartComponent) },
  { path: 'purchase-history', canActivate: [authGuard], loadComponent: () => import('./features/commerce/purchase-history.component').then((module) => module.PurchaseHistoryComponent) },
  { path: 'recommendations', canActivate: [authGuard], loadComponent: () => import('./features/commerce/recommendations.component').then((module) => module.RecommendationsComponent) },
  { path: 'fitting-bag', canActivate: [authGuard], loadComponent: () => import('./features/reservations/fitting-bag.component').then((module) => module.FittingBagComponent) },
  { path: 'my-reservations', canActivate: [authGuard], loadComponent: () => import('./features/reservations/my-reservations.component').then((module) => module.MyReservationsComponent) },
  { path: 'my-reservations/:id', canActivate: [authGuard], loadComponent: () => import('./features/reservations/my-reservations.component').then((module) => module.MyReservationsComponent) },
  { path: 'pos', canActivate: [permissionGuard('sales.create')], loadComponent: () => import('./features/commerce/pos.component').then((module) => module.PosComponent) },
  { path: 'offline-transactions', canActivate: [authGuard], loadComponent: () => import('./features/commerce/offline-transactions-tray.component').then((m) => m.OfflineTransactionsTrayComponent) },
  { path: 'offline-tray', redirectTo: 'offline-transactions' },
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then((module) => module.LoginComponent) },
  { path: 'register', loadComponent: () => import('./features/auth/register.component').then((module) => module.RegisterComponent) },
  { path: 'register-company', loadComponent: () => import('./features/auth/company-register.component').then((module) => module.CompanyRegisterComponent) },
  { path: 'subscription/success', loadComponent: () => import('./features/auth/paid-checkout-return.component').then((module) => module.PaidCheckoutReturnComponent), data: { checkoutState: 'success' } },
  { path: 'subscription/cancel', loadComponent: () => import('./features/auth/paid-checkout-return.component').then((module) => module.PaidCheckoutReturnComponent), data: { checkoutState: 'cancel' } },
  { path: 'banca-movil', loadComponent: () => import('./features/commerce/mobile-banking.component').then((module) => module.MobileBankingComponent) },
  { path: 'account', redirectTo: 'catalog' },
  { path: 'platform', canActivate: [platformAdminGuard], loadComponent: () => import('./features/admin/platform-admin.component').then((module) => module.PlatformAdminComponent) },
  { path: 'admin', canActivate: [adminGuard], loadComponent: () => import('./features/admin/admin.component').then((module) => module.AdminComponent) },
  { path: 'cycle-3-admin', canActivate: [adminGuard], loadComponent: () => import('./features/admin/cycle3-admin.component').then((module) => module.Cycle3AdminComponent) },
  { path: 'operations', canActivate: [permissionGuard('inventory.read')], loadComponent: () => import('./features/operations/operations.component').then((module) => module.OperationsComponent) },
  { path: 'reservations', canActivate: [permissionGuard('reservations.manage')], loadComponent: () => import('./features/reservations/reservations.component').then((module) => module.ReservationsComponent) },
  { path: 'supplier', canActivate: [permissionGuard('suppliers.portal')], loadComponent: () => import('./features/supplier/supplier.component').then((module) => module.SupplierComponent) },
  { path: 'supply', canActivate: [permissionGuard('suppliers.manage')], loadComponent: () => import('./features/supply/supply-admin.component').then((module) => module.SupplyAdminComponent) },
  { path: 'audit', canActivate: [adminGuard], loadComponent: () => import('./features/audit/audit.component').then((module) => module.AuditComponent) },
  { path: '**', redirectTo: 'catalog' },
];

