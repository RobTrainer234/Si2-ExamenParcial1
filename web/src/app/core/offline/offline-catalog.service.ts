import { Injectable } from '@angular/core';
import {
  OfflineCustomerRecord,
  SyncCatalogResponse,
  SyncCategoryItem,
  SyncInventoryItem,
  SyncMetadata,
  SyncProductItem,
  SyncVariantItem,
} from './offline.models';

const DB_NAME = 'fashionstore_offline_catalog';
const DB_VERSION = 3;

@Injectable({ providedIn: 'root' })
export class OfflineCatalogService {
  private dbPromise: Promise<IDBDatabase> | null = null;
  private readonly memoryStore = {
    metadata: new Map<number, SyncMetadata>(),
    categories: new Map<number, SyncCategoryItem>(),
    products: new Map<number, SyncProductItem>(),
    variants: new Map<number, SyncVariantItem>(),
    inventory: new Map<number, SyncInventoryItem>(),
    customers: new Map<string, OfflineCustomerRecord>(),
  };

  private get hasIndexedDb(): boolean {
    return typeof window !== 'undefined' && typeof window.indexedDB !== 'undefined';
  }

  initDb(): Promise<IDBDatabase> {
    if (!this.hasIndexedDb) {
      return Promise.reject(new Error('IndexedDB not supported in this environment'));
    }
    if (this.dbPromise) {
      return this.dbPromise;
    }

    this.dbPromise = new Promise((resolve, reject) => {
      const request = window.indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains('metadata')) {
          db.createObjectStore('metadata', { keyPath: 'branch_id' });
        }
        if (!db.objectStoreNames.contains('categories')) {
          db.createObjectStore('categories', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('products')) {
          const productStore = db.createObjectStore('products', { keyPath: 'id' });
          productStore.createIndex('category_id', 'category_id', { unique: false });
        }
        if (!db.objectStoreNames.contains('variants')) {
          const variantStore = db.createObjectStore('variants', { keyPath: 'id' });
          variantStore.createIndex('product_id', 'product_id', { unique: false });
          variantStore.createIndex('sku', 'sku', { unique: false });
        }
        if (!db.objectStoreNames.contains('inventory')) {
          db.createObjectStore('inventory', { keyPath: 'product_variant_id' });
        }
        if (!db.objectStoreNames.contains('pending_operations')) {
          const opStore = db.createObjectStore('pending_operations', { keyPath: 'client_operation_id' });
          opStore.createIndex('status', 'status', { unique: false });
          opStore.createIndex('created_at', 'created_at', { unique: false });
        }
        if (!db.objectStoreNames.contains('offline_customers')) {
          const customerStore = db.createObjectStore('offline_customers', { keyPath: 'id' });
          customerStore.createIndex('nit_ci', 'nit_ci', { unique: false });
          customerStore.createIndex('full_name', 'full_name', { unique: false });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    return this.dbPromise;
  }

  async saveSyncPayload(payload: SyncCatalogResponse): Promise<void> {
    if (!this.hasIndexedDb) {
      // Memory fallback for tests / unsupported environments
      this.clearMemoryStore();
      this.memoryStore.metadata.set(payload.metadata.branch_id, payload.metadata);
      payload.categories.forEach((c) => this.memoryStore.categories.set(c.id, c));
      payload.products.forEach((p) => this.memoryStore.products.set(p.id, p));
      payload.variants.forEach((v) => this.memoryStore.variants.set(v.id, v));
      payload.inventory.forEach((i) => this.memoryStore.inventory.set(i.product_variant_id, i));
      return;
    }

    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(['metadata', 'categories', 'products', 'variants', 'inventory'], 'readwrite');
      tx.onerror = () => reject(tx.error);
      tx.oncomplete = () => resolve();

      const metaStore = tx.objectStore('metadata');
      const catStore = tx.objectStore('categories');
      const prodStore = tx.objectStore('products');
      const varStore = tx.objectStore('variants');
      const invStore = tx.objectStore('inventory');

      // Clear existing records before refreshing
      metaStore.clear();
      catStore.clear();
      prodStore.clear();
      varStore.clear();
      invStore.clear();

      metaStore.put(payload.metadata);
      payload.categories.forEach((c) => catStore.put(c));
      payload.products.forEach((p) => prodStore.put(p));
      payload.variants.forEach((v) => varStore.put(v));
      payload.inventory.forEach((i) => invStore.put(i));
    });
  }

  async getLatestMetadata(): Promise<SyncMetadata | null> {
    if (!this.hasIndexedDb) {
      const values = Array.from(this.memoryStore.metadata.values());
      return values.length > 0 ? values[0] : null;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('metadata', 'readonly');
      const store = tx.objectStore('metadata');
      const req = store.getAll();
      req.onsuccess = () => {
        const items = req.result as SyncMetadata[];
        resolve(items.length > 0 ? items[0] : null);
      };
      req.onerror = () => reject(req.error);
    });
  }

  async getCategories(): Promise<SyncCategoryItem[]> {
    if (!this.hasIndexedDb) {
      return Array.from(this.memoryStore.categories.values()).filter((c) => c.is_active);
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('categories', 'readonly');
      const store = tx.objectStore('categories');
      const req = store.getAll();
      req.onsuccess = () => resolve((req.result as SyncCategoryItem[]).filter((c) => c.is_active));
      req.onerror = () => reject(req.error);
    });
  }

  async getProducts(categoryId?: number, query?: string): Promise<SyncProductItem[]> {
    if (!this.hasIndexedDb) {
      let items = Array.from(this.memoryStore.products.values()).filter((p) => p.is_active);
      if (categoryId) {
        items = items.filter((p) => p.category_id === categoryId);
      }
      if (query && query.trim()) {
        const q = query.trim().toLowerCase();
        items = items.filter((p) => p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q));
      }
      return items;
    }

    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('products', 'readonly');
      const store = tx.objectStore('products');
      const req = store.getAll();
      req.onsuccess = () => {
        let items = (req.result as SyncProductItem[]).filter((p) => p.is_active);
        if (categoryId) {
          items = items.filter((p) => p.category_id === categoryId);
        }
        if (query && query.trim()) {
          const q = query.trim().toLowerCase();
          items = items.filter((p) => p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q));
        }
        resolve(items);
      };
      req.onerror = () => reject(req.error);
    });
  }

  async getProductDetail(id: number): Promise<import('./offline.models').OfflineProductDetail> {
    const [product, metadata] = await Promise.all([this.getProductById(id), this.getLatestMetadata()]);
    const variants = product ? await this.getVariantsByProductId(id) : [];
    const inventoryEntries = await Promise.all(variants.map(async (variant) => [variant.id, await this.getInventory(variant.id)] as const));
    return {
      product,
      variants,
      inventory: Object.fromEntries(inventoryEntries.filter((entry): entry is [number, SyncInventoryItem] => entry[1] !== null)),
      metadata,
    };
  }

  async getProductById(id: number): Promise<SyncProductItem | null> {
    if (!this.hasIndexedDb) {
      return this.memoryStore.products.get(id) ?? null;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('products', 'readonly');
      const store = tx.objectStore('products');
      const req = store.get(id);
      req.onsuccess = () => resolve(req.result ?? null);
      req.onerror = () => reject(req.error);
    });
  }

  async getVariantsByProductId(productId: number): Promise<SyncVariantItem[]> {
    if (!this.hasIndexedDb) {
      return Array.from(this.memoryStore.variants.values()).filter((v) => v.product_id === productId && v.is_active);
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('variants', 'readonly');
      const store = tx.objectStore('variants');
      const index = store.index('product_id');
      const req = index.getAll(productId);
      req.onsuccess = () => resolve((req.result as SyncVariantItem[]).filter((v) => v.is_active));
      req.onerror = () => reject(req.error);
    });
  }

  async getInventory(variantId: number): Promise<SyncInventoryItem | null> {
    if (!this.hasIndexedDb) {
      return this.memoryStore.inventory.get(variantId) ?? null;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('inventory', 'readonly');
      const store = tx.objectStore('inventory');
      const req = store.get(variantId);
      req.onsuccess = () => resolve(req.result ?? null);
      req.onerror = () => reject(req.error);
    });
  }

  async decrementLocalInventory(variantId: number, qty: number): Promise<void> {
    const inv = await this.getInventory(variantId);
    if (!inv) return;
    inv.stock_quantity = Math.max(0, inv.stock_quantity - qty);
    inv.available_quantity = Math.max(0, inv.stock_quantity - inv.reserved_quantity);

    if (!this.hasIndexedDb) {
      this.memoryStore.inventory.set(variantId, inv);
      return;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('inventory', 'readwrite');
      tx.objectStore('inventory').put(inv);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async reserveLocalInventory(variantId: number, qty: number): Promise<void> {
    const inv = await this.getInventory(variantId);
    if (!inv) return;
    inv.reserved_quantity += qty;
    inv.available_quantity = Math.max(0, inv.stock_quantity - inv.reserved_quantity);

    if (!this.hasIndexedDb) {
      this.memoryStore.inventory.set(variantId, inv);
      return;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('inventory', 'readwrite');
      tx.objectStore('inventory').put(inv);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async saveOfflineCustomer(
    input: {
      id?: string;
      full_name: string;
      nit_ci: string;
      phone?: string | null;
      email?: string | null;
    }
  ): Promise<OfflineCustomerRecord> {
    const now = new Date().toISOString();
    const cleanNit = input.nit_ci.trim();
    const id = input.id?.trim() || (cleanNit ? `cust-nit-${cleanNit}` : `cust-web-${Date.now()}`);
    const record: OfflineCustomerRecord = {
      id,
      full_name: input.full_name.trim(),
      nit_ci: cleanNit,
      phone: input.phone?.trim() || null,
      email: input.email?.trim() || null,
      created_at: now,
      updated_at: now,
    };

    if (!this.hasIndexedDb) {
      this.memoryStore.customers.set(record.id, record);
      return record;
    }

    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('offline_customers', 'readwrite');
      tx.objectStore('offline_customers').put(record);
      tx.oncomplete = () => resolve(record);
      tx.onerror = () => reject(tx.error);
    });
  }

  async listOfflineCustomers(query?: string): Promise<OfflineCustomerRecord[]> {
    let items: OfflineCustomerRecord[];
    if (!this.hasIndexedDb) {
      items = Array.from(this.memoryStore.customers.values());
    } else {
      const db = await this.initDb();
      items = await new Promise<OfflineCustomerRecord[]>((resolve, reject) => {
        const tx = db.transaction('offline_customers', 'readonly');
        const req = tx.objectStore('offline_customers').getAll();
        req.onsuccess = () => resolve((req.result as OfflineCustomerRecord[]) || []);
        req.onerror = () => reject(req.error);
      });
    }

    if (query && query.trim()) {
      const q = query.trim().toLowerCase();
      items = items.filter(
        (c) =>
          c.full_name.toLowerCase().includes(q) ||
          c.nit_ci.toLowerCase().includes(q) ||
          (c.phone ?? '').toLowerCase().includes(q)
      );
    }

    return items.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  }

  async deleteOfflineCustomer(id: string): Promise<void> {
    if (!this.hasIndexedDb) {
      this.memoryStore.customers.delete(id);
      return;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('offline_customers', 'readwrite');
      tx.objectStore('offline_customers').delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async clearCache(): Promise<void> {
    this.clearMemoryStore();
    if (!this.hasIndexedDb) {
      return;
    }
    const db = await this.initDb();
    return new Promise((resolve, reject) => {
      const storeNames = ['metadata', 'categories', 'products', 'variants', 'inventory'];
      if (db.objectStoreNames.contains('offline_customers')) {
        storeNames.push('offline_customers');
      }
      const tx = db.transaction(storeNames, 'readwrite');
      tx.onerror = () => reject(tx.error);
      tx.oncomplete = () => resolve();

      tx.objectStore('metadata').clear();
      tx.objectStore('categories').clear();
      tx.objectStore('products').clear();
      tx.objectStore('variants').clear();
      tx.objectStore('inventory').clear();
      if (db.objectStoreNames.contains('offline_customers')) {
        tx.objectStore('offline_customers').clear();
      }
    });
  }

  private clearMemoryStore(): void {
    this.memoryStore.metadata.clear();
    this.memoryStore.categories.clear();
    this.memoryStore.products.clear();
    this.memoryStore.variants.clear();
    this.memoryStore.inventory.clear();
    this.memoryStore.customers.clear();
  }
}
