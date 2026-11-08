export interface SyncMetadata {
  tenant_id: number | null;
  tenant_name: string;
  branch_id: number;
  branch_name: string;
  sync_timestamp: string;
  catalog_version: string;
}

export interface SyncCategoryItem {
  id: number;
  name: string;
  is_active: boolean;
}

export interface SyncProductItem {
  id: number;
  category_id: number;
  category_name: string;
  name: string;
  code: string;
  slug: string;
  description: string | null;
  audience?: 'WOMEN' | 'MEN' | 'UNISEX';
  size_system?: 'ALPHA' | 'NUMERIC' | 'ONE_SIZE';
  price: number;
  image_url: string | null;
  is_active: boolean;
}

export interface SyncVariantItem {
  id: number;
  product_id: number;
  sku: string;
  size_id: number | null;
  size_name: string | null;
  size_type?: 'ALPHA' | 'NUMERIC' | 'ONE_SIZE' | null;
  sort_order?: number | null;
  color_id: number | null;
  color_name: string | null;
  price: number;
  is_active: boolean;
}

export interface SyncInventoryItem {
  product_variant_id: number;
  stock_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface OfflineProductDetail {
  product: SyncProductItem | null;
  variants: SyncVariantItem[];
  inventory: Record<number, SyncInventoryItem>;
  metadata: SyncMetadata | null;
}

export interface SyncCatalogResponse {
  metadata: SyncMetadata;
  categories: SyncCategoryItem[];
  products: SyncProductItem[];
  variants: SyncVariantItem[];
  inventory: SyncInventoryItem[];
}

export interface OfflineCustomerRecord {
  id: string;
  full_name: string;
  nit_ci: string;
  phone?: string | null;
  email?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OfflineSaleItemPayload {
  product_variant_id: number;
  quantity: number;
  unit_price: number;
}

export interface OfflineSalePayload {
  customer_id?: number | null;
  customer_name?: string | null;
  customer_nit?: string | null;
  customer_phone?: string | null;
  items: OfflineSaleItemPayload[];
  discount?: number;
  total: number;
  payment_method?: 'CASH';
  created_at?: string;
}

export interface OfflineReservationItemPayload {
  product_variant_id: number;
  quantity: number;
}

export interface OfflineReservationPayload {
  customer_id?: number | null;
  customer_name?: string | null;
  customer_nit?: string | null;
  customer_phone?: string | null;
  items: OfflineReservationItemPayload[];
  scheduled_for?: string | null;
  notes?: string | null;
  created_at?: string;
}

export type OperationType = 'SALE' | 'RESERVATION';
export type SyncOperationStatus = 'PENDING_SYNC' | 'SYNCING' | 'CONFIRMED' | 'CONFLICT' | 'REJECTED';

export interface SyncConflictDetail {
  code: string;
  message: string;
  variant_id?: number | null;
  sku?: string | null;
  requested_quantity?: number | null;
  available_quantity?: number | null;
}

export interface OfflineOperationRecord {
  client_operation_id: string;
  branch_id: number;
  operation_type: OperationType;
  status: SyncOperationStatus;
  sale_payload?: OfflineSalePayload | null;
  reservation_payload?: OfflineReservationPayload | null;
  sale_id?: number | null;
  order_number?: string | null;
  reservation_id?: number | null;
  conflict_detail?: SyncConflictDetail | null;
  created_at: string;
  synced_at?: string | null;
}

export interface SyncTransactionItemRequest {
  client_operation_id: string;
  branch_id: number;
  operation_type: OperationType;
  sale_payload?: OfflineSalePayload | null;
  reservation_payload?: OfflineReservationPayload | null;
}

export interface SyncTransactionBatchRequest {
  operations: SyncTransactionItemRequest[];
}

export interface SyncTransactionItemResult {
  client_operation_id: string;
  operation_type: string;
  status: 'CONFIRMED' | 'CONFLICT' | 'REJECTED';
  sale_id?: number | null;
  order_number?: string | null;
  reservation_id?: number | null;
  conflict_detail?: SyncConflictDetail | null;
  processed_at: string;
}

export interface SyncTransactionBatchResponse {
  processed_count: number;
  confirmed_count: number;
  conflict_count: number;
  results: SyncTransactionItemResult[];
}

