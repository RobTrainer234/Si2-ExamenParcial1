import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { adminGuard, permissionGuard } from './core/auth/role.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'catalog' },
  { path: 'catalog', loadComponent: () => import('./features/catalog/catalog.component').then((module) => module.CatalogComponent) },
  { path: 'catalog/:id', loadComponent: () => import('./features/catalog/product-detail.component').then((module) => module.ProductDetailComponent) },
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then((module) => module.LoginComponent) },
  { path: 'register', loadComponent: () => import('./features/auth/register.component').then((module) => module.RegisterComponent) },
  { path: 'account', canActivate: [authGuard], redirectTo: 'catalog' },
  { path: 'admin', canActivate: [adminGuard], loadComponent: () => import('./features/admin/admin.component').then((module) => module.AdminComponent) },
  { path: 'operations', canActivate: [permissionGuard('inventory.read')], loadComponent: () => import('./features/operations/operations.component').then((module) => module.OperationsComponent) },
  { path: 'supplier', canActivate: [permissionGuard('suppliers.portal')], loadComponent: () => import('./features/supplier/supplier.component').then((module) => module.SupplierComponent) },
  { path: 'supply', canActivate: [permissionGuard('suppliers.manage')], loadComponent: () => import('./features/supply/supply-admin.component').then((module) => module.SupplyAdminComponent) },
  { path: 'audit', canActivate: [adminGuard], loadComponent: () => import('./features/audit/audit.component').then((module) => module.AuditComponent) },
  { path: '**', redirectTo: 'catalog' },
];
