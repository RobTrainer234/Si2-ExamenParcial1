import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { adminGuard, permissionGuard } from './core/auth/role.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'catalog' },
  { path: 'catalog', loadComponent: () => import('./features/catalog/catalog.component').then((module) => module.CatalogComponent) },
  { path: 'catalog/:id', loadComponent: () => import('./features/catalog/product-detail.component').then((module) => module.ProductDetailComponent) },
  { path: 'cart', canActivate: [authGuard], loadComponent: () => import('./features/commerce/cart.component').then((module) => module.CartComponent) },
  { path: 'purchase-history', canActivate: [authGuard], loadComponent: () => import('./features/commerce/purchase-history.component').then((module) => module.PurchaseHistoryComponent) },
  { path: 'recommendations', canActivate: [authGuard], loadComponent: () => import('./features/commerce/recommendations.component').then((module) => module.RecommendationsComponent) },
  { path: 'fitting-bag', canActivate: [authGuard], loadComponent: () => import('./features/reservations/fitting-bag.component').then((module) => module.FittingBagComponent) },
  { path: 'my-reservations', canActivate: [authGuard], loadComponent: () => import('./features/reservations/my-reservations.component').then((module) => module.MyReservationsComponent) },
  { path: 'my-reservations/:id', canActivate: [authGuard], loadComponent: () => import('./features/reservations/my-reservations.component').then((module) => module.MyReservationsComponent) },
  { path: 'pos', canActivate: [permissionGuard('sales.create')], loadComponent: () => import('./features/commerce/pos.component').then((module) => module.PosComponent) },
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then((module) => module.LoginComponent) },
  { path: 'register', loadComponent: () => import('./features/auth/register.component').then((module) => module.RegisterComponent) },
  { path: 'banca-movil', loadComponent: () => import('./features/commerce/mobile-banking.component').then((module) => module.MobileBankingComponent) },
  { path: 'account', redirectTo: 'catalog' },
  { path: 'admin', canActivate: [adminGuard], loadComponent: () => import('./features/admin/admin.component').then((module) => module.AdminComponent) },
  { path: 'cycle-3-admin', canActivate: [adminGuard], loadComponent: () => import('./features/admin/cycle3-admin.component').then((module) => module.Cycle3AdminComponent) },
  { path: 'operations', canActivate: [permissionGuard('inventory.read')], loadComponent: () => import('./features/operations/operations.component').then((module) => module.OperationsComponent) },
  { path: 'reservations', canActivate: [permissionGuard('reservations.manage')], loadComponent: () => import('./features/reservations/reservations.component').then((module) => module.ReservationsComponent) },
  { path: 'supplier', canActivate: [permissionGuard('suppliers.portal')], loadComponent: () => import('./features/supplier/supplier.component').then((module) => module.SupplierComponent) },
  { path: 'supply', canActivate: [permissionGuard('suppliers.manage')], loadComponent: () => import('./features/supply/supply-admin.component').then((module) => module.SupplyAdminComponent) },
  { path: 'audit', canActivate: [adminGuard], loadComponent: () => import('./features/audit/audit.component').then((module) => module.AuditComponent) },
  { path: '**', redirectTo: 'catalog' },
];
