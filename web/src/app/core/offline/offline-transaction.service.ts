import { Injectable, inject } from '@angular/core';
import { OfflineCatalogService } from './offline-catalog.service';
import {
  OfflineCustomerRecord,
  OfflineOperationRecord,
  OfflineReservationPayload,
  OfflineSalePayload,
  SyncOperationStatus,
  SyncTransactionItemResult,
} from './offline.models';

@Injectable({ providedIn: 'root' })
export class OfflineTransactionService {
  private catalogService = inject(OfflineCatalogService);
  private memoryOperations = new Map<string, OfflineOperationRecord>();

  private get hasIndexedDb(): boolean {
    return typeof window !== 'undefined' && typeof window.indexedDB !== 'undefined';
  }

  private generateId(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return `op-web-${crypto.randomUUID()}`;
    }
    return `op-web-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  async saveCustomer(input: {
    id?: string;
    full_name: string;
    nit_ci: string;
    phone?: string | null;
    email?: string | null;
  }): Promise<OfflineCustomerRecord> {
    return this.catalogService.saveOfflineCustomer(input);
  }

  async listCustomers(query?: string): Promise<OfflineCustomerRecord[]> {
    return this.catalogService.listOfflineCustomers(query);
  }

  async deleteCustomer(id: string): Promise<void> {
    return this.catalogService.deleteOfflineCustomer(id);
  }

  async recordOfflineSale(branchId: number, payload: OfflineSalePayload): Promise<OfflineOperationRecord> {
    const opId = this.generateId();
    const now = new Date().toISOString();
    const record: OfflineOperationRecord = {
      client_operation_id: opId,
      branch_id: branchId,
      operation_type: 'SALE',
      status: 'PENDING_SYNC',
      sale_payload: {
        ...payload,
        created_at: payload.created_at || now,
        payment_method: 'CASH',
      },
      created_at: now,
    };

    if (payload.customer_name && payload.customer_name.trim()) {
      await this.catalogService.saveOfflineCustomer({
        full_name: payload.customer_name,
        nit_ci: payload.customer_nit || '0',
        phone: payload.customer_phone || null,
      });
    }

    // Deduct provisional stock from local offline inventory
    for (const item of payload.items) {
      await this.catalogService.decrementLocalInventory(item.product_variant_id, item.quantity);
    }

    await this.saveOperation(record);
    return record;
  }

  async recordOfflineReservation(branchId: number, payload: OfflineReservationPayload): Promise<OfflineOperationRecord> {
    const opId = this.generateId();
    const now = new Date().toISOString();
    const record: OfflineOperationRecord = {
      client_operation_id: opId,
      branch_id: branchId,
      operation_type: 'RESERVATION',
      status: 'PENDING_SYNC',
      reservation_payload: {
        ...payload,
        created_at: payload.created_at || now,
      },
      created_at: now,
    };

    if (payload.customer_name && payload.customer_name.trim()) {
      await this.catalogService.saveOfflineCustomer({
        full_name: payload.customer_name,
        nit_ci: payload.customer_nit || '0',
        phone: payload.customer_phone || null,
      });
    }

    // Reserve provisional stock in local offline inventory
    for (const item of payload.items) {
      await this.catalogService.reserveLocalInventory(item.product_variant_id, item.quantity);
    }

    await this.saveOperation(record);
    return record;
  }

  async saveOperation(record: OfflineOperationRecord): Promise<void> {
    this.memoryOperations.set(record.client_operation_id, { ...record });
    if (!this.hasIndexedDb) return;

    const db = await this.catalogService.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('pending_operations', 'readwrite');
      const store = tx.objectStore('pending_operations');
      const req = store.put(record);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async listOperations(statusFilter?: SyncOperationStatus): Promise<OfflineOperationRecord[]> {
    if (!this.hasIndexedDb) {
      const all = Array.from(this.memoryOperations.values());
      all.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      return statusFilter ? all.filter((o) => o.status === statusFilter) : all;
    }

    const db = await this.catalogService.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('pending_operations', 'readonly');
      const store = tx.objectStore('pending_operations');
      const req = store.getAll();
      req.onsuccess = () => {
        const all: OfflineOperationRecord[] = req.result || [];
        all.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        resolve(statusFilter ? all.filter((o) => o.status === statusFilter) : all);
      };
      req.onerror = () => reject(req.error);
    });
  }

  async updateOperationResult(result: SyncTransactionItemResult): Promise<void> {
    const op = await this.getOperation(result.client_operation_id);
    if (!op) return;

    op.status = result.status;
    op.sale_id = result.sale_id;
    op.order_number = result.order_number;
    op.reservation_id = result.reservation_id;
    op.conflict_detail = result.conflict_detail;
    op.synced_at = result.processed_at;

    await this.saveOperation(op);
  }

  async getOperation(clientOperationId: string): Promise<OfflineOperationRecord | null> {
    if (!this.hasIndexedDb) {
      return this.memoryOperations.get(clientOperationId) || null;
    }
    const db = await this.catalogService.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('pending_operations', 'readonly');
      const store = tx.objectStore('pending_operations');
      const req = store.get(clientOperationId);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  async deleteOperation(clientOperationId: string): Promise<void> {
    this.memoryOperations.delete(clientOperationId);
    if (!this.hasIndexedDb) return;
    const db = await this.catalogService.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('pending_operations', 'readwrite');
      const store = tx.objectStore('pending_operations');
      const req = store.delete(clientOperationId);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async clearAllOperations(): Promise<void> {
    this.memoryOperations.clear();
    if (!this.hasIndexedDb) return;
    const db = await this.catalogService.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('pending_operations', 'readwrite');
      tx.objectStore('pending_operations').clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }
}
