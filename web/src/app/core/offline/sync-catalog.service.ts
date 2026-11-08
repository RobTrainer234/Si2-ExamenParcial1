import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, from, map, switchMap, tap, throwError } from 'rxjs';

import { appConfig } from '../config/app-config';
import { OfflineCatalogService } from './offline-catalog.service';
import { SyncCatalogResponse, SyncMetadata } from './offline.models';

@Injectable({ providedIn: 'root' })
export class SyncCatalogService {
  private readonly http = inject(HttpClient);
  private readonly offlineCatalog = inject(OfflineCatalogService);

  readonly isSyncing = signal<boolean>(false);
  readonly syncError = signal<string | null>(null);
  readonly lastSync = signal<SyncMetadata | null>(null);
  readonly isOnline = signal<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  constructor() {
    this.initNetworkListeners();
    this.loadLastSyncMetadata();
  }

  private initNetworkListeners(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.isOnline.set(true);
        this.autoSync();
      });
      window.addEventListener('offline', () => this.isOnline.set(false));
    }
  }

  private async loadLastSyncMetadata(): Promise<void> {
    try {
      const meta = await this.offlineCatalog.getLatestMetadata();
      this.lastSync.set(meta);
    } catch {
      // Ignored if offline DB not initialized yet
    }
  }

  autoSync(branchId?: number): void {
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      return;
    }
    if (this.isSyncing()) {
      return;
    }
    this.syncCatalog(branchId).subscribe({
      next: () => {},
      error: () => {},
    });
  }

  syncCatalog(branchId?: number): Observable<SyncCatalogResponse> {
    this.isSyncing.set(true);
    this.syncError.set(null);

    let params = new HttpParams();
    if (branchId) {
      params = params.set('branch_id', branchId);
    }

    return this.http.get<SyncCatalogResponse>(`${appConfig.apiBaseUrl}/sync/catalog`, { params }).pipe(
      switchMap((response) =>
        from(this.offlineCatalog.saveSyncPayload(response)).pipe(
          map(() => response),
        ),
      ),
      tap((response) => {
        this.lastSync.set(response.metadata);
        this.isSyncing.set(false);
      }),
      catchError((error) => {
        this.isSyncing.set(false);
        const errorMsg =
          error?.error?.detail?.message ||
          error?.message ||
          'Error al sincronizar catálogo con el servidor.';
        this.syncError.set(errorMsg);
        return throwError(() => error);
      }),
    );
  }

  async clearOfflineData(): Promise<void> {
    await this.offlineCatalog.clearCache();
    this.lastSync.set(null);
  }
}
