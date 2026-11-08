import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { OfflineTransactionService } from './offline-transaction.service';
import {
  SyncTransactionBatchRequest,
  SyncTransactionBatchResponse,
} from './offline.models';

@Injectable({ providedIn: 'root' })
export class SyncTransactionService {
  private http = inject(HttpClient);
  private offlineTx = inject(OfflineTransactionService);

  readonly isSyncing = signal<boolean>(false);
  readonly pendingCount = signal<number>(0);
  readonly lastSync = signal<Date | null>(null);
  readonly syncError = signal<string | null>(null);
  readonly lastBatchResponse = signal<SyncTransactionBatchResponse | null>(null);

  constructor() {
    this.refreshPendingCount();
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.syncPendingTransactions();
      });
    }
  }

  async refreshPendingCount(): Promise<number> {
    const pending = await this.offlineTx.listOperations('PENDING_SYNC');
    this.pendingCount.set(pending.length);
    return pending.length;
  }

  async syncPendingTransactions(): Promise<SyncTransactionBatchResponse | null> {
    if (this.isSyncing()) return null;

    const pending = await this.offlineTx.listOperations('PENDING_SYNC');
    if (pending.length === 0) {
      this.pendingCount.set(0);
      return null;
    }

    this.isSyncing.set(true);
    this.syncError.set(null);

    const batchRequest: SyncTransactionBatchRequest = {
      operations: pending.map((op) => ({
        client_operation_id: op.client_operation_id,
        branch_id: op.branch_id,
        operation_type: op.operation_type,
        sale_payload: op.sale_payload,
        reservation_payload: op.reservation_payload,
      })),
    };

    try {
      const response = await firstValueFrom(
        this.http.post<SyncTransactionBatchResponse>('/api/v1/sync/transactions', batchRequest)
      );

      for (const res of response.results) {
        await this.offlineTx.updateOperationResult(res);
      }

      this.lastBatchResponse.set(response);
      this.lastSync.set(new Date());
      await this.refreshPendingCount();
      return response;
    } catch (err: any) {
      const errorMsg = err?.error?.detail?.message || err?.message || 'Error de red al sincronizar operaciones.';
      this.syncError.set(errorMsg);
      return null;
    } finally {
      this.isSyncing.set(false);
      await this.refreshPendingCount();
    }
  }
}
