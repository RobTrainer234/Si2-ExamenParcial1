import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { adminGuard } from './core/auth/role.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'catalog' },
  { path: 'catalog', loadComponent: () => import('./features/catalog/catalog.component').then((module) => module.CatalogComponent) },
  { path: 'catalog/:id', loadComponent: () => import('./features/catalog/product-detail.component').then((module) => module.ProductDetailComponent) },
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then((module) => module.LoginComponent) },
  { path: 'register', loadComponent: () => import('./features/auth/register.component').then((module) => module.RegisterComponent) },
  { path: 'account', canActivate: [authGuard], redirectTo: 'catalog' },
  { path: 'admin', canActivate: [adminGuard], loadComponent: () => import('./features/admin/admin.component').then((module) => module.AdminComponent) },
  { path: '**', redirectTo: 'catalog' },
];
