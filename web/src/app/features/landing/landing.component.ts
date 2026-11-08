import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AdminService } from '../../core/admin/admin.service';
import { AuthService } from '../../core/auth/auth.service';
import { SubscriptionPlan } from '../../core/models/admin.models';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="landing-page">
      <!-- HERO PRINCIPAL -->
      <section class="landing-hero" aria-labelledby="landing-title">
        <div class="landing-hero-copy">
          <div class="eyebrow-pill">
            <span class="pill-dot" aria-hidden="true"></span>
            <span>FashionStore Cloud · Plataforma SaaS para Indumentaria</span>
          </div>
          <h1 id="landing-title">
            FashionStore: una operación más clara para una tienda que sigue <em>creciendo.</em>
          </h1>
          <p class="landing-lead">
            Reuní tu catálogo digital, probador virtual, inventario multi-sucursal, punto de venta y continuidad en
            <strong>Modo offline</strong> dentro de un espacio aislado y seguro para tu marca de moda.
          </p>

          <div class="landing-actions" aria-label="Acciones principales">
            @if (auth.isAuthenticated()) {
              <a class="landing-button landing-button-primary" [routerLink]="auth.defaultHomeRoute()">
                <span class="material-symbols-outlined" aria-hidden="true">space_dashboard</span>
                <span>Ir a mi panel</span>
              </a>
            } @else {
              <a class="landing-button landing-button-primary" routerLink="/register-company">
                <span class="material-symbols-outlined" aria-hidden="true">rocket_launch</span>
                <span>Comenzar prueba para empresas (14 días)</span>
              </a>
            }
            <a class="landing-button landing-button-secondary" routerLink="/catalog">
              <span class="material-symbols-outlined" aria-hidden="true">diamond</span>
              <span>Explorar catálogo</span>
            </a>
            @if (!auth.isAuthenticated()) {
              <a class="landing-button landing-button-ghost" routerLink="/login">Ingresar</a>
            }
          </div>

          <div class="hero-policy-strip" aria-label="Condiciones de la prueba gratuita">
            <div class="policy-chip">
              <span class="material-symbols-outlined" aria-hidden="true">verified</span>
              <span><strong>14 días de prueba</strong> sin tarjeta ni cobro automático</span>
            </div>
            <div class="policy-chip">
              <span class="material-symbols-outlined" aria-hidden="true">bolt</span>
              <span><strong>Acceso inmediato</strong> sin esperar aprobación humana</span>
            </div>
            <div class="policy-chip">
              <span class="material-symbols-outlined" aria-hidden="true">storefront</span>
              <span>Hasta <strong>2 sucursales activas</strong> en prueba</span>
            </div>
          </div>
        </div>

        <!-- COMPOSICIÓN EDITORIAL / ARQUITECTURA EN VIVO -->
        <div class="landing-hero-showcase" aria-hidden="true">
          <div class="showcase-backdrop-card"></div>

          <div class="showcase-main-card">
            <div class="showcase-header">
              <span class="showcase-tag">Arquitectura Multitenant · Etapa SaaS</span>
              <span class="showcase-monogram">F</span>
            </div>
            <div class="showcase-title-block">
              <small>Atelier & Boutique Operations</small>
              <strong>Catálogo, stock multi-sucursal y continuidad offline en tiempo real.</strong>
            </div>
            <div class="showcase-metrics-grid">
              <div class="showcase-metric">
                <span class="metric-kicker">Aislamiento</span>
                <strong>Por empresa</strong>
                <small>Datos, usuarios y sucursales propios</small>
              </div>
              <div class="showcase-metric">
                <span class="metric-kicker">Resiliencia</span>
                <strong>PWA + SQLite</strong>
                <small>Catálogo y operaciones sin red</small>
              </div>
            </div>
            <div class="showcase-status-bar">
              <span class="status-indicator"></span>
              <span>Sincronización activa por tenant y sucursal</span>
            </div>
          </div>

          <div class="showcase-floating-badge">
            <span class="material-symbols-outlined">shield_lock</span>
            <div>
              <strong>Resguardo de 90 días</strong>
              <small>Consulta y exportación garantizadas al vencer</small>
            </div>
          </div>
        </div>
      </section>

      <!-- PILARES Y BENEFICIOS VERIFICADOS -->
      <section id="beneficios" class="landing-section" aria-labelledby="capabilities-title">
        <div class="landing-section-heading">
          <div>
            <p class="landing-eyebrow">Capacidades verificadas de la plataforma</p>
            <h2 id="capabilities-title">Las herramientas que tu equipo necesita, en un mismo lugar.</h2>
          </div>
          <p class="section-subtitle">
            Cada módulo respeta el aislamiento de tu empresa y dirige a cada rol —administrador, encargado, cajero,
            proveedor o cliente— a las funciones que le corresponden.
          </p>
        </div>

        <div class="capability-grid">
          <article class="capability-card">
            <div class="capability-top">
              <span class="capability-number">01</span>
              <span class="material-symbols-outlined capability-icon" aria-hidden="true">diamond</span>
            </div>
            <h3>Catálogo conectado y Probador</h3>
            <p>
              Publicá y explorá tus prendas con filtros por audiencia, temporada, colección, talla, color y disponibilidad
              real por sucursal, integrado con reservas y probador virtual.
            </p>
            <a routerLink="/catalog" class="capability-link">Ver catálogo público <span aria-hidden="true">↗</span></a>
          </article>

          <article class="capability-card capability-card-featured">
            <div class="capability-top">
              <span class="capability-number">02</span>
              <span class="material-symbols-outlined capability-icon" aria-hidden="true">dashboard_customize</span>
            </div>
            <h3>Operaciones multi-sucursal</h3>
            <p>
              Administrá ciudades, sucursales, kárdex de inventario, terminal POS de caja, atención de reservas y
              abastecimiento con proveedores bajo permisos estrictos por rol.
            </p>
            <span class="capability-status">Control transaccional de cuotas por plan</span>
          </article>

          <article class="capability-card">
            <div class="capability-top">
              <span class="capability-number">03</span>
              <span class="material-symbols-outlined capability-icon" aria-hidden="true">wifi_off</span>
            </div>
            <h3>Continuidad offline · Modo offline</h3>
            <p>
              Descargá el catálogo autorizado en navegador (IndexedDB / PWA) o móvil (SQLite) para consultar existencias
              con avisos claros de vigencia cuando la conexión no acompaña.
            </p>
            <span class="capability-status">Aislamiento automático al cambiar de sesión</span>
          </article>

          <article class="capability-card">
            <div class="capability-top">
              <span class="capability-number">04</span>
              <span class="material-symbols-outlined capability-icon" aria-hidden="true">Auto_Awesome</span>
            </div>
            <h3>Analítica ejecutiva y Sofía IA</h3>
            <p>
              Consultá KPIs operativos, exportación formal en Excel/PDF y, en el plan Profesional, reportes generativos en
              lenguaje natural y predicción de demanda con Machine Learning.
            </p>
            <span class="capability-status">Habilitado según el plan contratado</span>
          </article>
        </div>
      </section>

      <!-- PLANES REALES Y PRUEBA GRATUITA -->
      <section id="planes" class="landing-section plans-section" aria-labelledby="plans-title">
        <div class="landing-section-heading">
          <div>
            <p class="landing-eyebrow">Oferta transparente · Sin condiciones ocultas</p>
            <h2 id="plans-title">Planes diseñados para acompañar cada etapa de tu tienda.</h2>
          </div>
          <p class="section-subtitle">
            Comenzá con una prueba gratuita self-service de 14 días sin tarjeta y escalá las capacidades de tu empresa
            cuando tu operación lo requiera.
          </p>
        </div>

        <!-- SELECTOR DE FACTURACIÓN MENSUAL / ANUAL -->
        <div class="billing-switcher-wrap">
          <div class="billing-switcher" role="radiogroup" aria-label="Periodicidad de facturación">
            <button
              type="button"
              class="billing-switch-btn"
              [class.active]="billingPeriod === 'monthly'"
              (click)="billingPeriod = 'monthly'"
              role="radio"
              [attr.aria-checked]="billingPeriod === 'monthly'"
            >
              Facturación Mensual
            </button>
            <button
              type="button"
              class="billing-switch-btn"
              [class.active]="billingPeriod === 'annual'"
              (click)="billingPeriod = 'annual'"
              role="radio"
              [attr.aria-checked]="billingPeriod === 'annual'"
            >
              Facturación Anual
              <span class="annual-discount-pill">Ahorra 2 meses</span>
            </button>
          </div>
          <span class="billing-hint">
            {{ billingPeriod === 'annual' ? 'Planes anuales con 2 meses bonificados por pago anticipado' : 'Sin contratos forzosos · Pagos mensuales en bolivianos' }}
          </span>
        </div>

        <div class="plans-grid">
          <!-- TARJETA PRUEBA SELF-SERVICE 14 DÍAS -->
          <article class="plan-card plan-card-trial">
            <div class="plan-badge-row">
              <span class="plan-tag plan-tag-trial">Acceso inmediato Self-Service</span>
              <span class="plan-duration">14 días</span>
            </div>
            <h3>Prueba para Empresas</h3>
            <div class="plan-price-block">
              <span class="price-currency">Bs</span>
              <span class="price-amount">0</span>
              <span class="price-period">/ 14 días</span>
            </div>
            <p class="plan-price-subtext">Prueba 100% gratuita · Sin tarjeta de crédito</p>
            <p class="plan-description">
              Ideal para conocer FashionStore con tu propio catálogo y equipo, sin esperar aprobación manual ni ingresar
              medios de pago.
            </p>
            <ul class="plan-features" aria-label="Características de la prueba gratuita">
              <li>
                <span class="material-symbols-outlined" aria-hidden="true">check_circle</span>
                <span>Hasta <strong>2 sucursales activas</strong> durante los 14 días</span>
              </li>
              <li>
                <span class="material-symbols-outlined" aria-hidden="true">check_circle</span>
                <span>Funciones operativas completas (catálogo, stock, POS, reservas y modo offline)</span>
              </li>
              <li>
                <span class="material-symbols-outlined" aria-hidden="true">mail</span>
                <span>Verificación de correo posterior al primer ingreso</span>
              </li>
              <li>
                <span class="material-symbols-outlined" aria-hidden="true">block</span>
                <span class="feature-muted">Reportes generativos de IA deshabilitados en prueba</span>
              </li>
              <li>
                <span class="material-symbols-outlined" aria-hidden="true">inventory</span>
                <span>Al vencer: modo consulta y <strong>exportación de datos por 90 días</strong></span>
              </li>
            </ul>
            <div class="plan-footer">
              <a class="landing-button landing-button-primary full-width" routerLink="/register-company" [queryParams]="{ plan: 'TRIAL' }">
                Comenzar prueba gratis (14 días)
              </a>
              <small class="plan-footnote">Acceso inmediato sin tarjeta ni cobro automático.</small>
            </div>
          </article>

          <!-- PLANES OFICIALES DESDE BACKEND (BÁSICO Y PROFESIONAL) -->
          @for (plan of plans; track plan.code) {
            <article class="plan-card" [class.plan-card-pro]="plan.code === 'PROFESSIONAL'">
              <div class="plan-badge-row">
                <span class="plan-tag">{{ plan.code === 'PROFESSIONAL' ? 'Mayor capacidad + IA' : 'Operación esencial' }}</span>
                <span class="plan-code-pill">{{ plan.code }}</span>
              </div>
              <h3>Plan {{ plan.name }}</h3>
              <div class="plan-price-block">
                @if (billingPeriod === 'annual') {
                  <span class="price-original-striked">Bs {{ planAnnualOriginal(plan) }}</span>
                }
                <div class="price-main-line">
                  <span class="price-currency">Bs</span>
                  <span class="price-amount">{{ planPrice(plan) }}</span>
                  <span class="price-period">/ {{ billingPeriod === 'monthly' ? 'mes' : 'año' }}</span>
                </div>
              </div>
              @if (billingPeriod === 'annual') {
                <div class="plan-savings-pill">
                  <span class="material-symbols-outlined" aria-hidden="true">savings</span>
                  <span>Ahorras Bs {{ planSavingsAnnual(plan) }} al año · 2 meses gratis</span>
                </div>
              }
              <p class="plan-price-subtext">
                {{ billingPeriod === 'annual' ? 'Equivale a ' + planMonthlyEquivalent(plan) + ' facturado anualmente' : 'Cobro mensual estándar en bolivianos' }}
              </p>
              <p class="plan-description">
                @if (plan.code === 'PROFESSIONAL') {
                  Diseñado para cadenas de boutiques en expansión que requieren múltiples puntos de venta y analítica generativa.
                } @else {
                  Estructura sólida para boutiques que buscan centralizar su catálogo, inventario y ventas en hasta dos sucursales.
                }
              </p>
              <ul class="plan-features" [attr.aria-label]="'Características del plan ' + plan.name">
                <li>
                  <span class="material-symbols-outlined" aria-hidden="true">storefront</span>
                  <span>Hasta <strong>{{ plan.max_active_branches }} sucursales activas</strong> simultáneas</span>
                </li>
                <li>
                  <span class="material-symbols-outlined" aria-hidden="true">check_circle</span>
                  <span>Catálogo conectado, variantes, colecciones y probador virtual</span>
                </li>
                <li>
                  <span class="material-symbols-outlined" aria-hidden="true">check_circle</span>
                  <span>Terminal POS, reservas, proveedores y catálogo en Modo offline</span>
                </li>
                <li>
                  <span class="material-symbols-outlined" aria-hidden="true">
                    {{ plan.generative_reports_enabled ? 'auto_awesome' : 'remove_circle_outline' }}
                  </span>
                  <span [class.feature-muted]="!plan.generative_reports_enabled">
                    @if (plan.generative_reports_enabled) {
                      <strong>Reportes generativos con IA</strong> (voz/texto) y analítica ML incluidos
                    } @else {
                      Reportes generativos de IA no incluidos en este plan
                    }
                  </span>
                </li>
              </ul>
              <div class="plan-footer">
                <a
                  class="landing-button full-width"
                  [class.landing-button-primary]="plan.code === 'PROFESSIONAL'"
                  [class.landing-button-secondary]="plan.code !== 'PROFESSIONAL'"
                  routerLink="/register-company"
                  [queryParams]="{ plan: plan.code, billing: billingPeriod }"
                >
                  {{ plan.code === 'PROFESSIONAL' ? 'Elegir Plan Profesional' : 'Elegir Plan Básico' }}
                </a>
                <small class="plan-footnote">El acceso se habilita después de confirmar el pago.</small>
              </div>
            </article>
          }
        </div>

        <!-- BANNER DE CADENAS DE GRAN ESCALA -->
        <div class="enterprise-banner">
          <div class="enterprise-copy">
            <div class="enterprise-tag">
              <span class="material-symbols-outlined" aria-hidden="true">apartment</span>
              <span>¿Tu marca cuenta con más de 10 sucursales o franquicias?</span>
            </div>
            <h4>FashionStore Enterprise · Despliegue e integraciones a medida</h4>
            <p>
              Ofrecemos infraestructura aislada dedicada, migración asistida de catálogos e inventario, SLA de disponibilidad garantizado y soporte directo para cadenas en expansión.
            </p>
          </div>
          <div class="enterprise-action">
            <a routerLink="/register-company" [queryParams]="{ plan: 'ENTERPRISE' }" class="landing-button landing-button-secondary">
              <span class="material-symbols-outlined" aria-hidden="true">contact_support</span>
              <span>Consultar plan Enterprise</span>
            </a>
          </div>
        </div>

        <!-- TABLA COMPARATIVA DETALLADA DE CARACTERÍSTICAS -->
        <div class="comparison-section">
          <div class="comparison-header">
            <div>
              <p class="landing-eyebrow">Detalle de cobertura</p>
              <h3>Matriz comparativa de capacidades por plan</h3>
            </div>
            <button
              type="button"
              class="comparison-toggle-btn"
              (click)="showComparison = !showComparison"
              [attr.aria-expanded]="showComparison"
            >
              <span class="material-symbols-outlined">{{ showComparison ? 'expand_less' : 'table_rows' }}</span>
              <span>{{ showComparison ? 'Ocultar comparativa' : 'Ver comparativa completa' }}</span>
            </button>
          </div>

          @if (showComparison) {
            <div class="comparison-table-wrap" tabindex="0" role="region" aria-label="Tabla comparativa de capacidades por plan">
              <table class="comparison-table">
                <thead>
                  <tr>
                    <th scope="col" class="feature-col">Capacidad / Módulo</th>
                    <th scope="col" class="tier-col">Prueba 14 días</th>
                    <th scope="col" class="tier-col">Plan Básico</th>
                    <th scope="col" class="tier-col tier-col-pro">Plan Profesional</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="category-row">
                    <td colspan="4">Capacidad y Sedes</td>
                  </tr>
                  <tr>
                    <th scope="row">Sucursales activas simultáneas</th>
                    <td>Hasta 2</td>
                    <td>Hasta 2</td>
                    <td class="cell-pro"><strong>Hasta 10</strong></td>
                  </tr>
                  <tr>
                    <th scope="row">Usuarios operativos por empresa</th>
                    <td>Ilimitados</td>
                    <td>Ilimitados</td>
                    <td class="cell-pro">Ilimitados</td>
                  </tr>
                  <tr>
                    <th scope="row">Espacio empresarial aislado (Multitenant)</th>
                    <td><span class="check-yes">✔ Incluido</span></td>
                    <td><span class="check-yes">✔ Incluido</span></td>
                    <td class="cell-pro"><span class="check-yes">✔ Incluido</span></td>
                  </tr>

                  <tr class="category-row">
                    <td colspan="4">Operación Comercial y Tienda</td>
                  </tr>
                  <tr>
                    <th scope="row">Catálogo digital y colecciones de temporada</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Probador virtual interactivo y reservas presenciales</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Terminal POS de caja rápida y ventas</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Kárdex transaccional y control de stock</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Continuidad en Modo offline (PWA + SQLite móvil)</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Portal de abastecimiento y relación con proveedores</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>

                  <tr class="category-row">
                    <td colspan="4">Analítica e Inteligencia Artificial</td>
                  </tr>
                  <tr>
                    <th scope="row">Dashboard ejecutivo de ventas y stock</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Exportación formal en Excel y PDF</th>
                    <td><span class="check-yes">✔</span></td>
                    <td><span class="check-yes">✔</span></td>
                    <td class="cell-pro"><span class="check-yes">✔</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Predicción de demanda con Machine Learning</th>
                    <td><span class="check-no">✕ Deshabilitado</span></td>
                    <td><span class="check-no">✕ No incluido</span></td>
                    <td class="cell-pro"><span class="check-yes">✔ Incluido</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Sofía IA · Reportes generativos en voz y texto</th>
                    <td><span class="check-no">✕ Deshabilitado</span></td>
                    <td><span class="check-no">✕ No incluido</span></td>
                    <td class="cell-pro"><span class="check-yes">✔ Incluido</span></td>
                  </tr>

                  <tr class="category-row">
                    <td colspan="4">Certidumbre, Datos y Soporte</td>
                  </tr>
                  <tr>
                    <th scope="row">Modo solo lectura al vencer</th>
                    <td>90 días garantizados</td>
                    <td>90 días garantizados</td>
                    <td class="cell-pro">90 días garantizados</td>
                  </tr>
                  <tr>
                    <th scope="row">Exportación integral de datos en JSON</th>
                    <td><span class="check-yes">✔ Permitida</span></td>
                    <td><span class="check-yes">✔ Permitida</span></td>
                    <td class="cell-pro"><span class="check-yes">✔ Permitida</span></td>
                  </tr>
                  <tr>
                    <th scope="row">Soporte y acompañamiento</th>
                    <td>Comunidad y guías</td>
                    <td>Soporte estándar</td>
                    <td class="cell-pro"><strong>Prioritario y personalizado</strong></td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td></td>
                    <td>
                      <a routerLink="/register-company" [queryParams]="{ plan: 'TRIAL' }" class="table-action-btn">
                        Probar gratis
                      </a>
                    </td>
                    <td>
                      <a routerLink="/register-company" [queryParams]="{ plan: 'BASIC', billing: billingPeriod }" class="table-action-btn">
                        Elegir Básico
                      </a>
                    </td>
                    <td class="cell-pro">
                      <a routerLink="/register-company" [queryParams]="{ plan: 'PROFESSIONAL', billing: billingPeriod }" class="table-action-btn table-action-pro">
                        Elegir Profesional
                      </a>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          }
        </div>

        <!-- PREGUNTAS FRECUENTES DE PRECIOS Y FACTURACIÓN -->
        <div class="pricing-faq">
          <div class="pricing-faq-header">
            <p class="landing-eyebrow">Dudas resueltas</p>
            <h3>Preguntas frecuentes sobre planes y facturación</h3>
          </div>
          <div class="faq-list">
            @for (faq of faqs; track faq.q; let i = $index) {
              <div class="faq-item" [class.open]="openFaqIndex === i">
                <button
                  type="button"
                  class="faq-question-btn"
                  (click)="toggleFaq(i)"
                  [attr.aria-expanded]="openFaqIndex === i"
                >
                  <span>{{ faq.q }}</span>
                  <span class="material-symbols-outlined">{{ openFaqIndex === i ? 'expand_less' : 'expand_more' }}</span>
                </button>
                @if (openFaqIndex === i) {
                  <div class="faq-answer">
                    <p>{{ faq.a }}</p>
                  </div>
                }
              </div>
            }
          </div>
        </div>
      </section>

      <!-- CÓMO FUNCIONA EL RECORRIDO SELF-SERVICE Y POLÍTICA DE DATOS -->
      <section id="recorrido" class="landing-section workflow-section" aria-labelledby="workflow-title">
        <div class="landing-section-heading">
          <div>
            <p class="landing-eyebrow">Recorrido claro de principio a fin</p>
            <h2 id="workflow-title">Qué recibe tu empresa al registrarse y qué ocurre después.</h2>
          </div>
        </div>

        <div class="workflow-steps">
          <div class="workflow-step">
            <span class="step-index">Paso 01</span>
            <h3>Alta self-service inmediata</h3>
            <p>
              Registrás el nombre de tu empresa y tu cuenta de administrador en <code>/register-company</code>. Ingresás de
              inmediato a tu panel sin demoras ni aprobaciones manuales.
            </p>
          </div>
          <div class="workflow-step">
            <span class="step-index">Paso 02</span>
            <h3>14 días de operación real</h3>
            <p>
              Configurás hasta 2 sucursales activas, cargás tus productos, invitás a tu equipo operativo y verificás tu
              correo mediante el enlace de seguridad de tu cuenta.
            </p>
          </div>
          <div class="workflow-step">
            <span class="step-index">Paso 03</span>
            <h3>Vencimiento seguro y modo lectura</h3>
            <p>
              Si la prueba vence, nunca hay cargos sorpresa: se bloquean nuevas modificaciones pero conservás acceso de
              consulta y descarga/exportación de tus datos durante <strong>90 días</strong>.
            </p>
          </div>
          <div class="workflow-step">
            <span class="step-index">Paso 04</span>
            <h3>Reactivación cuando lo decidas</h3>
            <p>
              Podés solicitar la activación al plan Básico o Profesional directamente desde tu panel empresarial para que un
              administrador de plataforma active tu suscripción.
            </p>
          </div>
        </div>
      </section>

      <!-- CTA FINAL SEPARANDO EMPRESA SAAS DE COMPRADOR B2C -->
      <section class="trial-section" aria-labelledby="trial-title">
        <div class="trial-copy-block">
          <p class="landing-eyebrow">Comenzá hoy mismo</p>
          <h2 id="trial-title">Probá FashionStore para tu empresa de indumentaria.</h2>
          <p class="trial-copy">
            El alta self-service crea tu espacio empresarial aislado con 14 días de prueba y acceso inmediato al Centro de
            Control. Si solo buscás comprar prendas como cliente de la boutique, podés explorar el catálogo público.
          </p>
        </div>
        <div class="trial-action">
          <a class="landing-button landing-button-primary full-width" routerLink="/register-company">
            Prueba para empresas · Crear cuenta SaaS
          </a>
          <div class="trial-secondary-links">
            <a routerLink="/login">Ya tengo cuenta de equipo</a>
            <span aria-hidden="true">·</span>
            <a routerLink="/catalog">Ir al catálogo de clientes</a>
          </div>
        </div>
      </section>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .landing-page { color: var(--ink); overflow-x: hidden; padding-bottom: 40px; }

    /* HERO */
    .landing-hero {
      align-items: center;
      background:
        radial-gradient(circle at 88% 16%, rgba(141, 77, 56, 0.10), transparent 42%),
        radial-gradient(circle at 12% 85%, rgba(100, 111, 88, 0.10), transparent 38%),
        linear-gradient(125deg, #f8f4ed 0%, var(--paper) 56%, #efe7dc 100%);
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: clamp(36px, 5vw, 76px);
      grid-template-columns: minmax(0, 1.12fr) minmax(320px, 0.88fr);
      margin: 0 auto;
      max-width: 1440px;
      padding: clamp(48px, 7vw, 96px) clamp(22px, 6vw, 88px);
      position: relative;
    }
    .landing-hero-copy { max-width: 680px; position: relative; z-index: 1; }
    .eyebrow-pill {
      align-items: center;
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--accent);
      display: inline-flex;
      font-size: 0.68rem;
      font-weight: 700;
      gap: 8px;
      letter-spacing: 0.14em;
      margin-bottom: 20px;
      padding: 7px 14px;
      text-transform: uppercase;
    }
    .pill-dot {
      background: var(--accent);
      border-radius: 50%;
      height: 7px;
      width: 7px;
    }
    .landing-eyebrow {
      color: var(--accent);
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.18em;
      margin: 0 0 14px;
      text-transform: uppercase;
    }
    h1, h2, h3, p { margin-top: 0; }
    h1 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(2.5rem, 5vw, 4.7rem);
      font-weight: 500;
      letter-spacing: -0.04em;
      line-height: 1.02;
      margin-bottom: 22px;
    }
    h1 em {
      color: var(--accent);
      font-style: italic;
      font-weight: 400;
    }
    .landing-lead {
      color: var(--muted);
      font-size: clamp(1rem, 1.35vw, 1.14rem);
      line-height: 1.7;
      margin-bottom: 28px;
      max-width: 590px;
    }
    .landing-actions {
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
    }
    .landing-button {
      align-items: center;
      border-radius: 10px;
      display: inline-flex;
      font-size: 0.73rem;
      font-weight: 700;
      gap: 8px;
      justify-content: center;
      letter-spacing: 0.1em;
      min-height: 48px;
      padding: 13px 22px;
      text-transform: uppercase;
      transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .landing-button:hover { transform: translateY(-2px); }
    .landing-button:focus-visible {
      outline: 3px solid var(--accent);
      outline-offset: 2px;
    }
    .landing-button-primary {
      background: var(--ink);
      box-shadow: 0 12px 28px -10px rgba(27, 28, 26, 0.35);
      color: #fff;
    }
    .landing-button-primary:hover { background: var(--accent); }
    .landing-button-secondary {
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid var(--line);
      color: var(--ink);
    }
    .landing-button-secondary:hover {
      background: #fff;
      border-color: var(--accent);
    }
    .landing-button-ghost {
      color: var(--ink);
      padding: 13px 16px;
      text-decoration: underline;
      text-underline-offset: 4px;
    }
    .full-width { width: 100%; }

    .hero-policy-strip {
      border-top: 1px solid rgba(229, 224, 216, 0.9);
      display: flex;
      flex-wrap: wrap;
      gap: 14px 22px;
      padding-top: 20px;
    }
    .policy-chip {
      align-items: center;
      color: var(--muted);
      display: inline-flex;
      font-size: 0.78rem;
      gap: 7px;
    }
    .policy-chip .material-symbols-outlined {
      color: var(--accent);
      font-size: 18px;
    }
    .policy-chip strong { color: var(--ink); }

    /* SHOWCASE CARD */
    .landing-hero-showcase {
      min-height: 420px;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .showcase-backdrop-card {
      background: linear-gradient(140deg, #d7c5b2, #b89f87);
      border-radius: 20px;
      height: 360px;
      position: absolute;
      right: 6%;
      top: 6%;
      transform: rotate(-4deg);
      width: 86%;
    }
    .showcase-main-card {
      background: linear-gradient(155deg, #23201e 0%, #171816 100%);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 20px;
      box-shadow: 0 28px 60px rgba(27, 28, 26, 0.22);
      color: #f7efe5;
      display: flex;
      flex-direction: column;
      gap: 22px;
      padding: 30px;
      position: relative;
      width: 90%;
      z-index: 2;
    }
    .showcase-header {
      align-items: center;
      display: flex;
      justify-content: space-between;
    }
    .showcase-tag {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 999px;
      font-size: 0.64rem;
      letter-spacing: 0.14em;
      padding: 5px 12px;
      text-transform: uppercase;
    }
    .showcase-monogram {
      align-items: center;
      background: #f7efe5;
      border-radius: 50%;
      color: #1b1c1a;
      display: inline-flex;
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.2rem;
      font-weight: 700;
      height: 38px;
      justify-content: center;
      width: 38px;
    }
    .showcase-title-block small {
      color: #c9b39d;
      display: block;
      font-size: 0.72rem;
      letter-spacing: 0.12em;
      margin-bottom: 6px;
      text-transform: uppercase;
    }
    .showcase-title-block strong {
      display: block;
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.5rem;
      font-weight: 500;
      line-height: 1.22;
    }
    .showcase-metrics-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, 1fr);
    }
    .showcase-metric {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.09);
      border-radius: 12px;
      padding: 14px;
    }
    .metric-kicker {
      color: #c9b39d;
      display: block;
      font-size: 0.62rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .showcase-metric strong {
      display: block;
      font-size: 1.02rem;
      margin: 4px 0 2px;
    }
    .showcase-metric small {
      color: rgba(247, 239, 229, 0.72);
      font-size: 0.72rem;
    }
    .showcase-status-bar {
      align-items: center;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      color: #d8d2ca;
      display: flex;
      font-size: 0.74rem;
      gap: 8px;
      padding-top: 14px;
    }
    .status-indicator {
      background: #4ade80;
      border-radius: 50%;
      box-shadow: 0 0 0 4px rgba(74, 222, 128, 0.18);
      height: 8px;
      width: 8px;
    }
    .showcase-floating-badge {
      align-items: center;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 14px;
      bottom: -8px;
      box-shadow: 0 18px 38px rgba(27, 28, 26, 0.12);
      color: var(--ink);
      display: flex;
      gap: 12px;
      left: 0;
      padding: 12px 16px;
      position: absolute;
      z-index: 3;
    }
    .showcase-floating-badge .material-symbols-outlined {
      background: var(--panel);
      border-radius: 10px;
      color: var(--accent);
      font-size: 22px;
      padding: 8px;
    }
    .showcase-floating-badge strong {
      display: block;
      font-size: 0.8rem;
    }
    .showcase-floating-badge small {
      color: var(--muted);
      font-size: 0.7rem;
    }

    /* SECTIONS */
    .landing-section {
      margin: 0 auto;
      max-width: 1280px;
      padding: clamp(56px, 8vw, 100px) 24px 0;
    }
    .landing-section-heading {
      align-items: end;
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      justify-content: space-between;
      margin-bottom: 38px;
    }
    h2 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(1.9rem, 3.6vw, 3.2rem);
      font-weight: 500;
      letter-spacing: -0.03em;
      line-height: 1.08;
      margin-bottom: 0;
      max-width: 660px;
    }
    .section-subtitle {
      color: var(--muted);
      font-size: 0.94rem;
      line-height: 1.65;
      margin: 0;
      max-width: 440px;
    }

    /* CAPABILITIES */
    .capability-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(4, 1fr);
    }
    .capability-card {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 290px;
      padding: 26px;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .capability-card:hover {
      box-shadow: 0 18px 40px -16px rgba(27, 28, 26, 0.12);
      transform: translateY(-4px);
    }
    .capability-card-featured {
      background: var(--ink);
      border-color: var(--ink);
      color: #fff;
    }
    .capability-top {
      align-items: center;
      display: flex;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .capability-number {
      color: var(--accent);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.14em;
    }
    .capability-card-featured .capability-number { color: #d9b69f; }
    .capability-icon {
      color: var(--accent);
      font-size: 28px;
    }
    .capability-card-featured .capability-icon { color: #f7efe5; }
    .capability-card h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.45rem;
      font-weight: 500;
      margin-bottom: 10px;
    }
    .capability-card p {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.62;
      margin-bottom: 20px;
    }
    .capability-card-featured p { color: #d8d2ca; }
    .capability-link {
      color: var(--accent);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .capability-status {
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.7rem;
      letter-spacing: 0.04em;
      padding-top: 12px;
    }
    .capability-card-featured .capability-status {
      border-top-color: rgba(255, 255, 255, 0.14);
      color: #d9b69f;
    }

    /* BILLING SWITCHER */
    .billing-switcher-wrap {
      align-items: center;
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin: 0 auto 36px;
    }
    .billing-switcher {
      background: #f1ede5;
      border: 1px solid var(--line);
      border-radius: 999px;
      display: inline-flex;
      padding: 4px;
    }
    .billing-switch-btn {
      align-items: center;
      background: transparent;
      border: none;
      border-radius: 999px;
      color: var(--muted);
      cursor: pointer;
      display: inline-flex;
      font-family: inherit;
      font-size: 0.84rem;
      font-weight: 600;
      gap: 8px;
      padding: 9px 18px;
      transition: background 0.2s ease, color 0.2s ease;
    }
    .billing-switch-btn.active {
      background: var(--ink);
      color: #fff;
    }
    .annual-discount-pill {
      background: var(--accent);
      border-radius: 999px;
      color: #fff;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      padding: 3px 8px;
      text-transform: uppercase;
    }
    .billing-hint {
      color: var(--muted);
      font-size: 0.78rem;
    }
    .plan-price-block {
      align-items: baseline;
      display: flex;
      gap: 4px;
      margin: 14px 0 2px;
    }
    .price-currency {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.25rem;
      font-weight: 600;
    }
    .price-amount {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 2.75rem;
      font-weight: 700;
      line-height: 1;
    }
    .price-period {
      color: var(--muted);
      font-size: 0.85rem;
      font-weight: 500;
    }
    .plan-card-pro .price-period { color: #d8d2ca; }
    .plan-price-subtext {
      color: var(--muted);
      font-size: 0.76rem;
      margin: 0 0 16px;
    }
    .plan-card-pro .plan-price-subtext { color: #d9b69f; }

    /* PLANS */
    .plans-grid {
      display: grid;
      gap: 20px;
      grid-template-columns: repeat(3, 1fr);
    }
    .plan-card {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 30px;
    }
    .plan-card-trial {
      background: linear-gradient(180deg, #faf6f0 0%, #ffffff 100%);
      border: 2px solid var(--accent);
      box-shadow: 0 20px 45px -18px rgba(141, 77, 56, 0.18);
    }
    .plan-card-pro {
      background: #1b1c1a;
      border-color: #1b1c1a;
      color: #fff;
    }
    .plan-badge-row {
      align-items: center;
      display: flex;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .plan-tag {
      background: var(--panel);
      border-radius: 999px;
      color: var(--ink);
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      padding: 5px 11px;
      text-transform: uppercase;
    }
    .plan-tag-trial {
      background: var(--accent);
      color: #fff;
    }
    .plan-card-pro .plan-tag {
      background: rgba(255, 255, 255, 0.12);
      color: #f7efe5;
    }
    .plan-duration, .plan-code-pill {
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .plan-card-pro .plan-code-pill { color: #d9b69f; }
    .plan-card h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.75rem;
      font-weight: 500;
      margin-bottom: 10px;
    }
    .plan-description {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.6;
      margin-bottom: 22px;
    }
    .plan-card-pro .plan-description { color: #d8d2ca; }
    .plan-features {
      border-top: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      gap: 12px;
      list-style: none;
      margin: 0 0 26px;
      padding: 20px 0 0;
    }
    .plan-card-pro .plan-features { border-top-color: rgba(255, 255, 255, 0.14); }
    .plan-features li {
      align-items: flex-start;
      display: flex;
      font-size: 0.85rem;
      gap: 10px;
      line-height: 1.5;
    }
    .plan-features .material-symbols-outlined {
      color: var(--accent);
      font-size: 19px;
      margin-top: 1px;
    }
    .plan-card-pro .plan-features .material-symbols-outlined { color: #d9b69f; }
    .feature-muted { opacity: 0.72; }
    .plan-footer {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: auto;
    }
    .plan-footnote {
      color: var(--muted);
      font-size: 0.72rem;
      text-align: center;
    }
    .plan-card-pro .plan-footnote { color: #b8b2a8; }
    .plan-card-pro .landing-button-primary {
      background: #f7efe5;
      color: #1b1c1a;
    }
    .plan-card-pro .landing-button-primary:hover {
      background: #d9b69f;
    }

    /* PRICE STRIP & SAVINGS */
    .price-original-striked {
      color: var(--muted);
      font-size: 0.95rem;
      margin-bottom: 2px;
      text-decoration: line-through;
    }
    .plan-card-pro .price-original-striked {
      color: #b8b2a8;
    }
    .price-main-line {
      align-items: baseline;
      display: flex;
      gap: 4px;
    }
    .plan-savings-pill {
      align-items: center;
      background: #edf7f1;
      border: 1px solid #bbf7d0;
      border-radius: 999px;
      color: #15803d;
      display: inline-flex;
      font-size: 0.72rem;
      font-weight: 700;
      gap: 5px;
      margin: 4px 0 10px;
      padding: 4px 10px;
      width: fit-content;
    }
    .plan-savings-pill .material-symbols-outlined {
      font-size: 15px;
    }
    .plan-card-pro .plan-savings-pill {
      background: rgba(217, 182, 159, 0.18);
      border-color: rgba(217, 182, 159, 0.35);
      color: #d9b69f;
    }

    /* ENTERPRISE BANNER */
    .enterprise-banner {
      align-items: center;
      background: linear-gradient(135deg, #242220 0%, #171816 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 18px;
      color: #f7efe5;
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      justify-content: space-between;
      margin-top: 32px;
      padding: 28px 32px;
    }
    .enterprise-copy {
      max-width: 720px;
    }
    .enterprise-tag {
      align-items: center;
      color: #d9b69f;
      display: inline-flex;
      font-size: 0.7rem;
      font-weight: 700;
      gap: 6px;
      letter-spacing: 0.12em;
      margin-bottom: 8px;
      text-transform: uppercase;
    }
    .enterprise-tag .material-symbols-outlined {
      font-size: 16px;
    }
    .enterprise-copy h4 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.35rem;
      font-weight: 500;
      margin: 0 0 8px;
    }
    .enterprise-copy p {
      color: #d8d2ca;
      font-size: 0.88rem;
      line-height: 1.55;
      margin: 0;
    }
    .enterprise-action .landing-button {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
    }
    .enterprise-action .landing-button:hover {
      background: #d9b69f;
      color: #1b1c1a;
    }

    /* COMPARISON MATRIX TABLE */
    .comparison-section {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 20px;
      margin-top: 40px;
      padding: 32px;
    }
    .comparison-header {
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .comparison-header h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.55rem;
      font-weight: 500;
      margin: 0;
    }
    .comparison-toggle-btn {
      align-items: center;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--ink);
      cursor: pointer;
      display: inline-flex;
      font-size: 0.82rem;
      font-weight: 600;
      gap: 6px;
      padding: 8px 16px;
      transition: background 0.2s ease;
    }
    .comparison-toggle-btn:hover {
      background: #eae3d8;
    }
    .comparison-table-wrap {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }
    .comparison-table {
      border-collapse: collapse;
      font-size: 0.88rem;
      min-width: 680px;
      text-align: left;
      width: 100%;
    }
    .comparison-table th,
    .comparison-table td {
      border-bottom: 1px solid var(--line);
      padding: 14px 18px;
      vertical-align: middle;
    }
    .comparison-table thead th {
      background: #faf7f2;
      border-bottom: 2px solid var(--line);
      font-size: 0.88rem;
      font-weight: 700;
      padding: 16px 18px;
    }
    .feature-col {
      width: 40%;
    }
    .tier-col {
      text-align: center;
      width: 20%;
    }
    .tier-col-pro {
      background: #fdfaf6 !important;
      color: var(--ink);
    }
    .category-row td {
      background: #f7f4ee;
      color: var(--accent);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      padding: 10px 18px;
      text-transform: uppercase;
    }
    .comparison-table tbody th {
      color: var(--ink);
      font-weight: 500;
    }
    .comparison-table tbody td {
      color: var(--muted);
      text-align: center;
    }
    .comparison-table tbody td.cell-pro {
      background: #fdfaf6;
      color: var(--ink);
    }
    .check-yes {
      color: #166534;
      font-weight: 600;
    }
    .check-no {
      color: #991b1b;
      opacity: 0.7;
    }
    .comparison-table tfoot td {
      border-bottom: none;
      padding-top: 20px;
      text-align: center;
    }
    .table-action-btn {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      display: inline-block;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 8px 14px;
      text-decoration: none;
      transition: background 0.2s ease, border-color 0.2s ease;
    }
    .table-action-btn:hover {
      background: var(--ink);
      border-color: var(--ink);
      color: #fff;
    }
    .table-action-pro {
      background: var(--ink);
      border-color: var(--ink);
      color: #fff;
    }
    .table-action-pro:hover {
      background: var(--accent);
      border-color: var(--accent);
    }

    /* FAQ ACCORDION */
    .pricing-faq {
      margin-top: 48px;
    }
    .pricing-faq-header {
      margin-bottom: 22px;
      text-align: center;
    }
    .pricing-faq-header h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.7rem;
      font-weight: 500;
      margin: 0;
    }
    .faq-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin: 0 auto;
      max-width: 900px;
    }
    .faq-item {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .faq-item.open {
      border-color: var(--accent);
      box-shadow: 0 4px 16px -6px rgba(141, 77, 56, 0.12);
    }
    .faq-question-btn {
      align-items: center;
      background: none;
      border: none;
      color: var(--ink);
      cursor: pointer;
      display: flex;
      font-family: inherit;
      font-size: 0.94rem;
      font-weight: 600;
      justify-content: space-between;
      padding: 18px 22px;
      text-align: left;
      width: 100%;
    }
    .faq-question-btn:hover {
      background: #faf7f2;
    }
    .faq-answer {
      border-top: 1px solid var(--line);
      padding: 16px 22px 20px;
    }
    .faq-answer p {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.6;
      margin: 0;
    }

    /* WORKFLOW */
    .workflow-steps {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(4, 1fr);
    }
    .workflow-step {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 24px;
    }
    .step-index {
      color: var(--accent);
      display: block;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      margin-bottom: 10px;
      text-transform: uppercase;
    }
    .workflow-step h3 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.3rem;
      font-weight: 500;
      margin-bottom: 8px;
    }
    .workflow-step p {
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.6;
      margin: 0;
    }

    /* CTA BANNER */
    .trial-section {
      align-items: center;
      background: linear-gradient(135deg, #f3ede3 0%, #e9e0d3 100%);
      border: 1px solid var(--line);
      border-radius: 20px;
      display: flex;
      gap: 32px;
      justify-content: space-between;
      margin: 64px auto 20px;
      max-width: 1232px;
      padding: clamp(32px, 5vw, 56px);
    }
    .trial-copy-block { max-width: 640px; }
    .trial-section h2 { margin-bottom: 12px; }
    .trial-copy {
      color: var(--muted);
      line-height: 1.65;
      margin-bottom: 0;
    }
    .trial-action {
      min-width: 300px;
      text-align: center;
    }
    .trial-secondary-links {
      align-items: center;
      color: var(--muted);
      display: flex;
      font-size: 0.76rem;
      gap: 10px;
      justify-content: center;
      margin-top: 14px;
    }
    .trial-secondary-links a {
      color: var(--ink);
      font-weight: 600;
      text-decoration: underline;
      text-underline-offset: 3px;
    }

    @media (max-width: 1024px) {
      .capability-grid, .workflow-steps { grid-template-columns: repeat(2, 1fr); }
      .plans-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 760px) {
      .landing-hero {
        grid-template-columns: 1fr;
        padding-bottom: 48px;
      }
      .landing-hero-showcase { min-height: 360px; }
      .showcase-main-card { width: 100%; }
      .capability-grid, .workflow-steps { grid-template-columns: 1fr; }
      .trial-section {
        align-items: flex-start;
        flex-direction: column;
        margin: 44px 16px 12px;
      }
      .trial-action { width: 100%; min-width: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .landing-button, .capability-card { transition: none; }
      .landing-button:hover, .capability-card:hover { transform: none; }
    }
  `],
})
export class LandingComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly admin = inject(AdminService);

  billingPeriod: 'monthly' | 'annual' = 'monthly';
  showComparison = true;
  openFaqIndex: number | null = 0;

  faqs = [
    {
      q: '¿Tengo que ingresar tarjeta de crédito para la prueba de 14 días?',
      a: 'No. El alta self-service es 100% gratuita y no solicita datos de tarjeta de crédito ni medios de pago. Tu espacio empresarial se inicializa de forma inmediata.',
    },
    {
      q: '¿Qué ocurre cuando finalizan los 14 días de prueba?',
      a: 'Tu cuenta pasa automáticamente al modo de solo lectura. No hay cobros forzosos ni cargos automáticos. Durante 90 días mantendrás acceso completo para consultar existencias, exportar tus datos en formato JSON o solicitar la activación de un plan desde tu panel de control.',
    },
    {
      q: '¿Cómo se gestiona el cobro y la facturación en Bolivia?',
      a: 'Los planes Básico y Profesional están expresados en moneda nacional (Bolivianos - Bs). La activación o renovación se tramita directamente desde la cuenta de la empresa y se habilita de forma asistida por un administrador de plataforma mediante los canales autorizados (transferencia bancaria, QR o pasarelas locales).',
    },
    {
      q: '¿Cómo funciona el ahorro de 2 meses en facturación anual?',
      a: 'Al elegir el ciclo anual, pagas únicamente el equivalente a 10 meses y recibes 12 meses completos de servicio. En el Plan Básico ahorras Bs 398 al año y en el Plan Profesional ahorras Bs 998 al año.',
    },
    {
      q: '¿Puedo cambiar de plan Básico a Profesional más adelante?',
      a: 'Sí. Podés solicitar la actualización a Plan Profesional en cualquier momento desde tu panel administrativo para ampliar tu cupo a 10 sucursales y activar el módulo de analítica predictiva y Sofía IA.',
    },
    {
      q: '¿La tienda puede seguir vendiendo si se corta la conexión a internet?',
      a: 'Sí. Gracias a la tecnología de Modo offline (IndexedDB / PWA en navegadores y SQLite en dispositivos móviles), el catálogo y las operaciones locales continúan funcionando y se sincronizan automáticamente al restablecerse la red.',
    },
  ];

  plans: SubscriptionPlan[] = [
    {
      id: 1,
      code: 'BASIC',
      name: 'Básico',
      price_monthly: 199,
      price_annual: 1990,
      currency: 'BOB',
      max_active_branches: 2,
      generative_reports_enabled: false,
      is_active: true,
    },
    {
      id: 2,
      code: 'PROFESSIONAL',
      name: 'Profesional',
      price_monthly: 499,
      price_annual: 4990,
      currency: 'BOB',
      max_active_branches: 10,
      generative_reports_enabled: true,
      is_active: true,
    },
  ];

  planPrice(plan: SubscriptionPlan): number {
    if (this.billingPeriod === 'annual') {
      if (plan.price_annual && plan.price_annual > 0) return plan.price_annual;
      return plan.code === 'PROFESSIONAL' ? 4990 : 1990;
    }
    if (plan.price_monthly && plan.price_monthly > 0) return plan.price_monthly;
    return plan.code === 'PROFESSIONAL' ? 499 : 199;
  }

  planMonthlyEquivalent(plan: SubscriptionPlan): string {
    const annual = this.planPrice(plan);
    const equiv = Math.round(annual / 12);
    return `Bs ${equiv} / mes`;
  }

  planAnnualOriginal(plan: SubscriptionPlan): number {
    const monthly = (plan.price_monthly && plan.price_monthly > 0)
      ? plan.price_monthly
      : (plan.code === 'PROFESSIONAL' ? 499 : 199);
    return monthly * 12;
  }

  planSavingsAnnual(plan: SubscriptionPlan): number {
    const original = this.planAnnualOriginal(plan);
    const discounted = (plan.price_annual && plan.price_annual > 0)
      ? plan.price_annual
      : (plan.code === 'PROFESSIONAL' ? 4990 : 1990);
    return Math.max(0, original - discounted);
  }

  toggleFaq(index: number): void {
    this.openFaqIndex = this.openFaqIndex === index ? null : index;
  }

  ngOnInit(): void {
    this.admin.publicPlans().subscribe({
      next: (res) => {
        if (res.items && res.items.length > 0) {
          this.plans = res.items;
        }
      },
      error: () => undefined,
    });
  }
}
