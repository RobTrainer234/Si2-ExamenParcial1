import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterLink, RouterOutlet],
  template: `
    <header class="site-header"><a class="brand" routerLink="/catalog"><span>F</span> FashionStore</a><nav><a routerLink="/catalog" routerLinkActive="active">Colección</a>@if (auth.currentUser()?.role === 'ADMIN') { <a routerLink="/admin" routerLinkActive="active">Administración</a> } @if (auth.isAuthenticated()) { <span class="welcome">Hola, {{ auth.currentUser()?.first_name }}</span><button class="text-button" (click)="logout()">Salir</button> } @else { <a routerLink="/login">Ingresar</a><a class="nav-cta" routerLink="/register">Crear cuenta</a> }</nav></header>
    <main class="page-shell"><router-outlet></router-outlet></main>
    <footer><span>FASHIONSTORE / CICLO 1</span><span>Elegir bien. Vestir mejor.</span></footer>
  `,
})
export class AppComponent {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  logout(): void { this.auth.logout(); this.router.navigateByUrl('/catalog'); }
}
