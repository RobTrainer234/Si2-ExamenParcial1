import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { CommerceService } from '../../core/commerce/commerce.service';
import { RecommendationItem } from '../../core/models/admin.models';

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule, CurrencyPipe, RouterLink],
  template: `
    <section class="operations-page recommendations-page">
      <!-- Luxury Atelier Header -->
      <header class="atelier-header">
        <div class="atelier-header-content">
          <div class="atelier-tag-row">
            <span class="atelier-eyebrow">
              <span class="material-symbols-outlined">auto_awesome</span>
              Atelier Personal Stylist · Ciclo 3
            </span>
            <div class="engine-status-pill">
              <span class="pulse-dot"></span>
              <span>Motor Inteligente Local Activo</span>
            </div>
          </div>
          <h2 class="atelier-title">Recomendaciones Curadas para Ti</h2>
          <p class="atelier-subtitle">
            Nuestro motor heurístico analiza tus compras previas, afinidad por categorías, temporada vigente y disponibilidad en tienda para crear tu guardarropa ideal.
          </p>
        </div>
      </header>

      <!-- Feedback / Error Message -->
      @if (message && !isLoading) {
        <div class="recommendations-feedback-banner">
          <span class="material-symbols-outlined">info</span>
          <span>{{ message }}</span>
        </div>
      }

      <!-- Loading Shimmer State -->
      @if (isLoading) {
        <div class="loading-shimmer-container">
          <div class="hero-shimmer"></div>
          <div class="grid-shimmer">
            <div class="card-shimmer"></div>
            <div class="card-shimmer"></div>
            <div class="card-shimmer"></div>
          </div>
        </div>
      } @else if (recommendations.length > 0) {
        <!-- Featured Hero Recommendation (Top Pick) -->
        @if (featuredItem && selectedCategory === 'all') {
          <article class="featured-look-card">
            <div class="featured-image-wrapper">
              @if (featuredItem.image_url) {
                <img [src]="featuredItem.image_url" [alt]="featuredItem.product_name" class="featured-img" />
              } @else {
                <div class="image-placeholder">
                  <span class="material-symbols-outlined">apparel</span>
                </div>
              }
              <div class="featured-badges">
                <span class="badge-featured">
                  <span class="material-symbols-outlined">auto_awesome</span>
                  Selección #1 del Asesor
                </span>
                <span class="badge-match">{{ formatMatchScore(featuredItem.score) }} Coincidencia</span>
              </div>
            </div>

            <div class="featured-details">
              <div class="featured-category-row">
                <span class="category-pill">{{ featuredItem.category_name }}</span>
                <span class="season-pill">Colección Actual</span>
              </div>
              <h3 class="featured-title">{{ featuredItem.product_name }}</h3>
              <div class="featured-price">
                {{ featuredItem.price | currency:'BOB':'symbol':'1.2-2' }}
              </div>

              <!-- Stylist Note Quote Box -->
              <div class="stylist-insight-box">
                <div class="stylist-avatar">
                  <span class="material-symbols-outlined">psychology</span>
                </div>
                <div class="stylist-quote">
                  <strong>Diagnóstico del Personal Stylist:</strong>
                  <p>{{ featuredItem.reason }}</p>
                </div>
              </div>

              <div class="featured-actions">
                <a class="button button-dark hero-action-btn" [routerLink]="['/catalog', featuredItem.product_id]">
                  <span>Ver prenda y tallas</span>
                  <span class="material-symbols-outlined">arrow_forward</span>
                </a>
              </div>
            </div>
          </article>
        }

        <!-- Filter Chips Bar -->
        <div class="filter-chips-bar">
          <span class="filter-label">Filtrar por categoría:</span>
          <div class="chips-list">
            <button
              type="button"
              class="filter-chip"
              [class.active]="selectedCategory === 'all'"
              (click)="setCategory('all')"
            >
              <span>Todas las sugerencias ({{ recommendations.length }})</span>
            </button>
            @for (cat of categories; track cat) {
              <button
                type="button"
                class="filter-chip"
                [class.active]="selectedCategory === cat"
                (click)="setCategory(cat)"
              >
                <span>{{ cat }} ({{ getCategoryCount(cat) }})</span>
              </button>
            }
          </div>
        </div>

        <!-- Curated Grid of Recommended Products -->
        <div class="recommendations-grid">
          @for (item of filteredRecommendations; track item.product_id) {
            <article class="recommendation-card">
              <div class="card-image-wrap">
                @if (item.image_url) {
                  <img [src]="item.image_url" [alt]="item.product_name" class="product-img" />
                } @else {
                  <div class="image-placeholder">
                    <span class="material-symbols-outlined">auto_awesome</span>
                  </div>
                }
                <!-- Card Badges -->
                <div class="card-floating-badges">
                  <span class="match-score-pill">
                    <span class="material-symbols-outlined">verified</span>
                    {{ formatMatchScore(item.score) }}
                  </span>
                  <span class="card-category-badge">{{ item.category_name }}</span>
                </div>
              </div>

              <div class="card-body">
                <h4 class="card-product-title">{{ item.product_name }}</h4>

                <!-- Stylist Reason Box -->
                <div class="card-stylist-reason">
                  <span class="material-symbols-outlined">style</span>
                  <p>{{ item.reason }}</p>
                </div>

                <div class="card-footer-row">
                  <div class="card-price">
                    {{ item.price | currency:'BOB':'symbol':'1.2-2' }}
                  </div>
                  <a class="button button-dark card-action-btn" [routerLink]="['/catalog', item.product_id]">
                    <span>Ver prenda</span>
                    <span class="material-symbols-outlined">chevron_right</span>
                  </a>
                </div>
              </div>
            </article>
          }
        </div>
      } @else {
        <!-- Empty State -->
        <div class="empty-recommendations-state">
          <div class="empty-icon-bubble">
            <span class="material-symbols-outlined">apparel</span>
          </div>
          <h3>Tu selección inteligente se está preparando</h3>
          <p>
            Aún no encontramos prendas coincidentes con existencias inmediatas en tienda. Explora nuestro catálogo completo para descubrir las últimas novedades.
          </p>
          <a class="button button-dark" routerLink="/catalog">Explorar Catálogo Completo</a>
        </div>
      }
    </section>
  `,
  styles: [`
    .recommendations-page {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1.5rem 1rem 4rem;
    }

    /* Atelier Header */
    .atelier-header {
      background: linear-gradient(135deg, #181614 0%, #24201c 100%);
      border: 1px solid rgba(212, 175, 55, 0.25);
      border-radius: 20px;
      padding: 2.25rem 2.5rem;
      margin-bottom: 2rem;
      color: #f7f3ec;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.12);
      position: relative;
      overflow: hidden;
    }

    .atelier-header::after {
      content: '';
      position: absolute;
      top: -50%;
      right: -10%;
      width: 320px;
      height: 320px;
      background: radial-gradient(circle, rgba(212, 175, 55, 0.12) 0%, transparent 70%);
      pointer-events: none;
    }

    .atelier-tag-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 0.85rem;
    }

    .atelier-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #d4af37;
    }

    .atelier-eyebrow .material-symbols-outlined {
      font-size: 16px;
    }

    .engine-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.3rem 0.85rem;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(212, 175, 55, 0.3);
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 600;
      color: #e5be7a;
      letter-spacing: 0.03em;
    }

    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulse-ring 2s infinite;
    }

    @keyframes pulse-ring {
      0% { transform: scale(0.9); opacity: 0.8; }
      50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 12px #10b981; }
      100% { transform: scale(0.9); opacity: 0.8; }
    }

    .atelier-title {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 2rem;
      font-weight: 600;
      margin: 0 0 0.6rem;
      color: #ffffff;
      letter-spacing: -0.01em;
      line-height: 1.2;
    }

    .atelier-subtitle {
      font-size: 0.92rem;
      color: #b8b0a2;
      max-width: 760px;
      margin: 0;
      line-height: 1.55;
    }

    /* Feedback Banner */
    .recommendations-feedback-banner {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 1rem 1.25rem;
      background: #fdf8ed;
      border: 1px solid #ebd9b0;
      border-radius: 12px;
      color: #8f6d2d;
      font-size: 0.88rem;
      margin-bottom: 2rem;
    }

    /* Hero Featured Look Card */
    .featured-look-card {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 2rem;
      background: #ffffff;
      border: 1px solid rgba(212, 175, 55, 0.35);
      border-radius: 20px;
      padding: 1.75rem;
      margin-bottom: 2.5rem;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.06);
      align-items: center;
      transition: transform 0.25s ease, box-shadow 0.25s ease;
    }

    .featured-look-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 18px 40px rgba(184, 146, 74, 0.12);
    }

    .featured-image-wrapper {
      position: relative;
      border-radius: 16px;
      overflow: hidden;
      aspect-ratio: 3 / 4;
      background: #f3efe8;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .featured-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.5s ease;
    }

    .featured-look-card:hover .featured-img {
      transform: scale(1.04);
    }

    .featured-badges {
      position: absolute;
      top: 12px;
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      gap: 6px;
      flex-wrap: wrap;
    }

    .badge-featured {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 5px 10px;
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(8px);
      color: #d4af37;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }

    .badge-featured .material-symbols-outlined {
      font-size: 14px;
    }

    .badge-match {
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      background: rgba(16, 185, 129, 0.9);
      backdrop-filter: blur(8px);
      color: #ffffff;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }

    .featured-details {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    .featured-category-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .category-pill {
      display: inline-block;
      padding: 3px 9px;
      background: #f4eee2;
      color: #8f6d2d;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .season-pill {
      display: inline-block;
      padding: 3px 9px;
      background: #eef2ff;
      color: #4338ca;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 600;
    }

    .featured-title {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.75rem;
      font-weight: 600;
      margin: 0;
      color: #1a1815;
      line-height: 1.25;
    }

    .featured-price {
      font-size: 1.35rem;
      font-weight: 700;
      color: #8f6d2d;
      font-family: inherit;
    }

    /* Stylist Insight Box */
    .stylist-insight-box {
      display: flex;
      gap: 1rem;
      padding: 1.25rem 1.4rem;
      background: #fbf9f4;
      border: 1px solid rgba(212, 175, 55, 0.25);
      border-left: 4px solid #d4af37;
      border-radius: 12px;
      align-items: flex-start;
    }

    .stylist-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #b8924a 0%, #d4af37 100%);
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      box-shadow: 0 4px 10px rgba(184, 146, 74, 0.3);
    }

    .stylist-avatar .material-symbols-outlined {
      font-size: 20px;
    }

    .stylist-quote strong {
      display: block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #8f6d2d;
      margin-bottom: 0.25rem;
    }

    .stylist-quote p {
      margin: 0;
      font-size: 0.88rem;
      line-height: 1.5;
      color: #2e2b26;
      font-style: italic;
    }

    .featured-actions {
      display: flex;
      gap: 1rem;
      margin-top: 0.5rem;
    }

    .hero-action-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.85rem 1.75rem;
      border-radius: 999px;
      font-weight: 600;
      font-size: 0.88rem;
    }

    /* Filter Chips Bar */
    .filter-chips-bar {
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .filter-label {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #787166;
    }

    .chips-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .filter-chip {
      padding: 0.45rem 1rem;
      background: #f4efe8;
      border: 1px solid #e5dfd5;
      border-radius: 999px;
      font-size: 0.78rem;
      color: #4a453d;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .filter-chip:hover {
      background: #eae3d7;
      color: #1a1815;
    }

    .filter-chip.active {
      background: #1a1815;
      color: #d4af37;
      border-color: #1a1815;
      font-weight: 600;
    }

    /* Curated Grid */
    .recommendations-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
      gap: 1.75rem;
    }

    .recommendation-card {
      background: #ffffff;
      border: 1px solid #e8e3da;
      border-radius: 16px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
      transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }

    .recommendation-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
      border-color: rgba(212, 175, 55, 0.4);
    }

    .card-image-wrap {
      position: relative;
      width: 100%;
      aspect-ratio: 3 / 4;
      background: #f3efe8;
      overflow: hidden;
    }

    .product-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.4s ease;
    }

    .recommendation-card:hover .product-img {
      transform: scale(1.05);
    }

    .image-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #b8b0a2;
    }

    .image-placeholder .material-symbols-outlined {
      font-size: 48px;
    }

    .card-floating-badges {
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      display: flex;
      justify-content: space-between;
      gap: 6px;
      pointer-events: none;
    }

    .match-score-pill {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 3px 8px;
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(6px);
      color: #d4af37;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.03em;
    }

    .match-score-pill .material-symbols-outlined {
      font-size: 12px;
      color: #10b981;
    }

    .card-category-badge {
      padding: 3px 8px;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(6px);
      color: #4a453d;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 600;
    }

    .card-body {
      padding: 1.2rem;
      display: flex;
      flex-direction: column;
      flex: 1;
      gap: 0.75rem;
    }

    .card-product-title {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.05rem;
      font-weight: 600;
      color: #1a1815;
      margin: 0;
      line-height: 1.3;
    }

    /* Card Stylist Reason */
    .card-stylist-reason {
      display: flex;
      align-items: flex-start;
      gap: 0.45rem;
      padding: 0.65rem 0.75rem;
      background: #faf7f2;
      border-left: 3px solid #d4af37;
      border-radius: 6px;
    }

    .card-stylist-reason .material-symbols-outlined {
      font-size: 15px;
      color: #8f6d2d;
      flex-shrink: 0;
      margin-top: 1px;
    }

    .card-stylist-reason p {
      margin: 0;
      font-size: 0.74rem;
      line-height: 1.4;
      color: #4a453d;
    }

    .card-footer-row {
      margin-top: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      padding-top: 0.5rem;
      border-top: 1px solid #f2ede4;
    }

    .card-price {
      font-size: 1.05rem;
      font-weight: 700;
      color: #8f6d2d;
    }

    .card-action-btn {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 0.5rem 0.9rem;
      font-size: 0.75rem;
      border-radius: 999px;
    }

    .card-action-btn .material-symbols-outlined {
      font-size: 15px;
    }

    /* Empty State */
    .empty-recommendations-state {
      padding: 4rem 2rem;
      text-align: center;
      background: #ffffff;
      border: 1px dashed #d6cebf;
      border-radius: 20px;
      max-width: 600px;
      margin: 2rem auto;
    }

    .empty-icon-bubble {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: #f4eee2;
      color: #8f6d2d;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1.25rem;
    }

    .empty-icon-bubble .material-symbols-outlined {
      font-size: 36px;
    }

    .empty-recommendations-state h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.4rem;
      margin: 0 0 0.5rem;
      color: #1a1815;
    }

    .empty-recommendations-state p {
      font-size: 0.88rem;
      color: #787166;
      margin: 0 auto 1.5rem;
      line-height: 1.5;
    }

    /* Shimmer Skeleton */
    .loading-shimmer-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .hero-shimmer {
      height: 280px;
      background: linear-gradient(90deg, #f0eae1 25%, #e8e0d4 50%, #f0eae1 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      border-radius: 20px;
    }

    .grid-shimmer {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
    }

    .card-shimmer {
      height: 380px;
      background: linear-gradient(90deg, #f0eae1 25%, #e8e0d4 50%, #f0eae1 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      border-radius: 16px;
    }

    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Responsive */
    @media (max-width: 900px) {
      .featured-look-card {
        grid-template-columns: 1fr;
        gap: 1.25rem;
      }

      .featured-image-wrapper {
        max-height: 360px;
      }

      .atelier-header {
        padding: 1.5rem;
      }

      .atelier-title {
        font-size: 1.5rem;
      }
    }
  `]
})
export class RecommendationsComponent implements OnInit {
  private readonly commerce = inject(CommerceService);

  recommendations: RecommendationItem[] = [];
  selectedCategory = 'all';
  isLoading = true;
  message = '';

  ngOnInit(): void {
    this.loadRecommendations();
  }

  loadRecommendations(): void {
    this.isLoading = true;
    this.commerce.recommendations().subscribe({
      next: (response) => {
        this.recommendations = response.items;
        this.isLoading = false;
        this.message = response.items.length ? '' : 'No hay recomendaciones disponibles con stock actual.';
      },
      error: () => {
        this.isLoading = false;
        this.message = 'No se pudieron cargar las recomendaciones en este momento.';
      }
    });
  }

  get featuredItem(): RecommendationItem | null {
    return this.recommendations.length > 0 ? this.recommendations[0] : null;
  }

  get categories(): string[] {
    const cats = new Set(this.recommendations.map(r => r.category_name));
    return Array.from(cats);
  }

  get filteredRecommendations(): RecommendationItem[] {
    if (this.selectedCategory === 'all') {
      return this.recommendations;
    }
    return this.recommendations.filter(r => r.category_name === this.selectedCategory);
  }

  setCategory(cat: string): void {
    this.selectedCategory = cat;
  }

  getCategoryCount(cat: string): number {
    return this.recommendations.filter(r => r.category_name === cat).length;
  }

  formatMatchScore(score: number): string {
    const pct = Math.min(99, Math.round(Number(score) * 100));
    return `${pct}% Match IA`;
  }
}
