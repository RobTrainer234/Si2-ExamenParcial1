import { Component, inject } from '@angular/core';
import { DatePipe, JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpParams } from '@angular/common/http';

import { appConfig } from '../../core/config/app-config';

interface AuditEntry { id: number; user_name: string | null; action: string; entity_type: string; entity_id: number | null; description: string | null; old_values: Record<string, unknown> | null; new_values: Record<string, unknown> | null; created_at: string; }
interface AuditPage { items: AuditEntry[]; total: number; page: number; page_size: number; total_pages: number; }

@Component({
  selector: 'app-audit',
  standalone: true,
  imports: [FormsModule, DatePipe, JsonPipe],
  template: `
    <section class="audit-page"><div class="admin-heading"><div><p class="eyebrow">Control y trazabilidad</p><h1>Bitácora</h1><p class="admin-subtitle">Consulta quién modificó la información operativa y qué valores cambió.</p></div><span class="master-count">{{ page?.total || 0 }} eventos</span></div><div class="audit-toolbar"><select [(ngModel)]="entityType" (change)="load()"><option value="">Todas las entidades</option><option value="product">Productos</option><option value="supplier">Proveedores</option><option value="supply_offer">Abastecimiento</option><option value="inventory">Inventario</option></select><select [(ngModel)]="action" (change)="load()"><option value="">Todas las acciones</option><option value="CREATE">Creaciones</option><option value="UPDATE">Actualizaciones</option></select></div><div class="audit-list">@for (entry of page?.items || []; track entry.id) { <article class="audit-card"><div class="audit-card-top"><span class="status-pill active">{{ entry.action }}</span><strong>{{ entry.entity_type }} #{{ entry.entity_id || 'global' }}</strong><time>{{ entry.created_at | date:'medium' }}</time></div><p>{{ entry.description || 'Cambio registrado' }}</p><small>Realizado por {{ entry.user_name || 'sistema' }}</small><details><summary>Valores</summary><pre>{{ { anterior: entry.old_values, nuevos: entry.new_values } | json }}</pre></details></article> } @empty { <p class="master-empty">No hay eventos con estos filtros.</p> }</div></section>
  `,
})
export class AuditComponent {
  private readonly http = inject(HttpClient);
  page: AuditPage | null = null; entityType = ''; action = '';
  constructor() { this.load(); }
  load(): void { let params = new HttpParams().set('page', 1).set('page_size', 100); if (this.entityType) params = params.set('entity_type', this.entityType); if (this.action) params = params.set('action', this.action); this.http.get<AuditPage>(`${appConfig.apiBaseUrl}/audit`, { params }).subscribe({ next: (page) => this.page = page }); }
}
