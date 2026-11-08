export interface Page<T> { items: T[]; page: number; page_size: number; total: number; total_pages: number; }
export interface AdminUser { id: number; first_name: string; last_name: string; email: string; phone: string; role: string; is_active: boolean; branch_ids: number[]; supplier_id: number | null; }
export interface City { id: number; name: string; is_active: boolean; }
export interface Branch { id: number; city_id: number; city_name: string; name: string; address: string; phone: string; latitude: number | null; longitude: number | null; is_active: boolean; }
export interface Category { id: number; name: string; description: string | null; is_active: boolean; }
export type SizeType = 'ALPHA' | 'NUMERIC' | 'ONE_SIZE';
export type SizeSystem = SizeType;
export interface Size { id: number; name: string; size_type: SizeType; sort_order: number; is_active: boolean; }
export interface Color { id: number; name: string; hex_code: string | null; is_active: boolean; }
export interface Supplier { id: number; trade_name: string; legal_name: string | null; tax_id: string | null; email: string | null; phone: string | null; address: string | null; is_active: boolean; product_ids: number[]; }
export interface Season { id: number; name: string; starts_on: string | null; ends_on: string | null; is_active: boolean; }
export interface Collection { id: number; season_id: number; season_name: string; name: string; description: string | null; is_active: boolean; }
export type AudienceCode = 'WOMEN' | 'MEN' | 'UNISEX';
export interface ProductSummary { id: number; category_id: number; category_name: string; audience: AudienceCode; size_system: SizeSystem; code: string; name: string; slug: string; price: number; is_active: boolean; variant_count: number; }
export interface ProductVariant { id: number; size_id: number; size_name: string; size_type: SizeType; sort_order: number; color_id: number; color_name: string; sku: string; is_active: boolean; }
export interface ProductImage { id: number; image_url: string; is_primary: boolean; sort_order: number; }
export interface ProductDetail extends ProductSummary { description: string | null; season_id: number | null; collection_id: number | null; variants: ProductVariant[]; supplier_ids: number[]; images: ProductImage[]; }
export interface InventoryRow { id: number; branch_id: number; branch_name: string; product_variant_id: number; product_id: number; product_name: string; sku: string; size_id: number; size_name: string; size_type: SizeType; size_sort_order: number; color_id: number; color_name: string; stock_quantity: number; reserved_quantity: number; available_quantity: number; available: boolean; }
export type InventoryMovementType = 'IN' | 'OUT' | 'RETURN' | 'RESERVE' | 'RELEASE' | 'SALE';
export interface InventoryMovement { id: number; inventory_id: number; branch_id: number; branch_name: string; movement_type: InventoryMovementType; quantity: number; stock_before: number; stock_after: number; reason: string | null; reference_type: string | null; reference_id: number | null; created_by: number | null; created_at: string; }
export type ReservationStatus = 'PENDING' | 'PREPARING' | 'READY' | 'ATTENDED' | 'CANCELLED' | 'EXPIRED';
export interface ReservationItem { id: number; product_variant_id: number; product_id: number; product_name: string; sku: string; size_name: string; color_name: string; quantity: number; unit_price: number; }
export interface Reservation { id: number; customer_id: number; customer_name: string; branch_id: number; branch_name: string; branch_city_name?: string | null; branch_address?: string | null; branch_phone?: string | null; branch_latitude?: number | null; branch_longitude?: number | null; scheduled_for: string | null; status: ReservationStatus; notes: string | null; expires_at: string | null; created_at: string; items: ReservationItem[]; }
export interface ImageInput { image_url: string; is_primary: boolean; sort_order: number; }
export type SupplyStatus = 'AVAILABLE' | 'LIMITED' | 'OUT_OF_STOCK' | 'UPCOMING';
export interface SupplyOffer { id: number; supplier_id: number; supplier_name: string; product_id: number; product_name: string; product_variant_id: number; sku: string; size_name: string; color_name: string; season_id: number; season_name: string; collection_id: number | null; collection_name: string | null; status: SupplyStatus; available_quantity: number; expected_date: string | null; notes: string | null; is_active: boolean; }
export interface CartItem { id: number; product_variant_id: number; product_id: number; product_name: string; sku: string; size_name: string; color_name: string; quantity: number; unit_price: number; line_total: number; available_quantity: number; }
export interface Cart { id: number; customer_id: number; status: string; items: CartItem[]; subtotal: number; total: number; updated_at: string; }
export type FulfillmentType = 'PICKUP' | 'DELIVERY';
export interface ShippingDetails { recipient_name: string; recipient_ci: string; recipient_phone: string; department_or_city: string; zone: string; street: string; house_number: string; reference: string; }
export interface DigitalPurchaseOptions { fulfillment_type?: FulfillmentType; shipping_details?: ShippingDetails; }
export interface SalePayment { id: number; sale_id: number; method: string; provider: string | null; transaction_reference: string | null; status: string; amount: number; received_amount: number | null; change_amount: number | null; paid_at: string | null; }
export interface StripePaymentIntent { payment_id: number; sale_id: number; provider: 'STRIPE'; payment_intent_id: string; client_secret: string; amount: number; currency: string; status: 'PENDING' | 'APPROVED' | 'FAILED' | 'CANCELLED'; }
export interface QRPaymentResponse { payment_id: number; sale_id: number; order_number: string; amount: number; currency: string; qr_data: string; qr_image_url: string; business_name: string; nit: string; bank_name: string; transaction_reference: string; expires_at: string; status: string; }
export interface QRPaymentStatusResponse { transaction_reference: string; sale_id: number; order_number: string; amount: number; currency: string; status: string; is_confirmed: boolean; }
export interface SaleItem { id: number; product_variant_id: number; product_name: string; sku: string; quantity: number; unit_price: number; discount: number; line_total: number; }
export interface Sale { id: number; order_number: string; customer_id: number | null; branch_id: number | null; cashier_id: number | null; channel: string; status: string; subtotal: number; discount: number; total: number; created_at: string; items: SaleItem[]; payments: SalePayment[]; fulfillment_type?: FulfillmentType; shipping_details?: ShippingDetails | null; }
export interface ExchangeSaleItem { id: number; variant_id: number; name: string; sku: string; purchased_quantity: number; net_paid_line_total: number; remaining_exchangeable_quantity: number; category_name?: string | null; exchange_days?: number; is_exchangeable?: boolean; policy_note?: string | null; }
export interface ExchangeSaleLookup { sale_id: number; order_number: string; sale_date: string; branch_id: number; status: string; store_policy_days?: number; days_elapsed?: number; is_within_policy?: boolean; policy_summary?: string; items: ExchangeSaleItem[]; }
export interface ReturnLookupItem { id: number; variant_id: number; name: string; sku: string; purchased_quantity: number; net_paid_line_total: number | string; remaining_returnable_quantity: number; selected_quantity?: number; condition?: 'SELLABLE' | 'DAMAGED'; }
export interface ReturnLookupResponse { sale_id: number; order_number: string; sale_date: string; branch_id: number; status: string; customer_id: number | null; items: ReturnLookupItem[]; }
export interface ReturnRequest { items: { sale_item_id: number; quantity: number; condition: 'SELLABLE' | 'DAMAGED' }[]; beneficiary_customer_id?: number; reason: string; idempotency_key: string; }
export interface ReturnResponse extends Sale { return_id: number; credit_note_code: string; credit_note_amount: number | string; }
export interface ReturnCustomer { id: number; name: string; email?: string | null; }
export interface CreditNoteBalanceLookup { available_balance: number | string; customer_id: number; expires_at: string | null; }
export interface CreditNoteLookupRequest { credit_note_code: string; customer_id: number; branch_id: number; }
export interface CreditNoteSettlementRequest { credit_note_code: string; idempotency_key: string; method?: 'CASH' | 'CARD' | 'QR'; amount?: number; transaction_reference?: string; }
export interface CreditNoteSettlementResponse extends Sale { redemption_id: number; applied_amount: number | string; post_redemption_balance: number | string; cash_change: number | string; }
export interface ExchangeQuoteInput { returned_variant_id: number; returned_quantity: number; new_variant_id: number; new_quantity: number; }
export interface ExchangeQuote { returned_value: number; replacement_unit_price: number; delivered_value: number; difference: number; cash_settlement_eligible: boolean; available_stock: number; reserved_stock: number; expires_at: string; quote_fingerprint: string; [key: string]: unknown; }
export interface ExchangeFinalizeInput extends ExchangeQuoteInput { quote_fingerprint: string; quote_expires_at: string; idempotency_key: string; cash_tendered?: number; cashier_confirmed?: boolean; reason?: string; item_condition?: string; inspection_checklist?: string[]; condition_notes?: string; }
export interface ExchangeFinalizeResponse { sale_id?: number; order_number?: string; returned_variant_id?: number; returned_quantity?: number; new_variant_id?: number; new_quantity?: number; quarantine_id: number | null; status: string; quarantine_status?: string | null; item_condition?: string | null; inspection_summary?: string | null; returned_value?: number | string; delivered_value?: number | string; difference?: number | string; cash_tendered?: number | string | null; cash_change?: number | string | null; cash_refunded?: number | string | null; exchanged_at?: string; [key: string]: unknown; }
export type QuarantineStatus = 'PENDING' | 'RELEASED' | 'REJECTED';
export type QuarantineDecision = 'RELEASE' | 'REJECT';
export interface QuarantineItem { id: number; tenant_id: number; branch_id: number; inventory_id: number; product_variant_id: number; exchange_item_id: number; quantity: number; status: QuarantineStatus; inspected_by: number | null; inspection_reason: string | null; inspected_at: string | null; created_at: string; }
export interface QuarantineInspectionInput { decision: QuarantineDecision; reason: string; }
export interface Promotion { id: number; name: string; description: string | null; discount_type: 'PERCENT' | 'FIXED'; discount_value: number; starts_at: string; ends_at: string; is_active: boolean; product_ids: number[]; }
export interface PromotionInput { name: string; description?: string | null; discount_type: 'PERCENT' | 'FIXED'; discount_value: number; starts_at: string; ends_at: string; }
export interface DashboardFilters { branch_id?: number; start_date?: string; end_date?: string; }
export type ReportExportFormat = 'xlsx' | 'pdf' | 'pptx';
export type ChartType = 'bar' | 'line' | 'pie' | 'table' | 'kpi';
export type ReportAssistantIntentKind = 'dashboard' | 'top_products' | 'sales_by_branch' | 'inventory' | 'reservations' | 'revenue_by_category' | string;
export interface ReportAssistantRequest { prompt: string; date_from?: string; date_to?: string; branch_id?: number; }
export interface ReportAssistantFilters { date_from?: string | null; date_to?: string | null; branch_id?: number | null; }
export interface ReportAssistantIntent { kind: ReportAssistantIntentKind; filters?: ReportAssistantFilters; chart_type?: ChartType; reasoning?: string | null; }
export interface ReportAssistantResponse { intent: ReportAssistantIntent; filters: ReportAssistantFilters; data: unknown; narrative: string; provider: string; fallback_used: boolean; }
export interface RevenueByCategoryItem { category_id: number; category_name: string; sales_count: number; units_sold: number; total_revenue: number; }
export interface MLModelMetrics {
  model_name: string;
  model_type: string;
  mae?: number | null;
  rmse?: number | null;
  r2_score?: number | null;
  silhouette_score?: number | null;
  inertia?: number | null;
  samples_count: number;
  real_samples_count?: number | null;
  synthetic_samples_count?: number | null;
  trained_at: string;
}
export interface DemandForecastPoint { period: string; predicted_units: number; predicted_revenue: number; confidence_lower: number; confidence_upper: number; }
export interface DemandForecastResponse { target: string; branch_id?: number | null; branch_name?: string | null; forecast: DemandForecastPoint[]; metrics: MLModelMetrics; narrative: string; }
export interface CustomerSegmentItem { segment_id: number; name: string; description: string; customer_count: number; percentage: number; avg_recency_days: number; avg_frequency: number; avg_monetary: number; suggested_action: string; }
export interface CustomerAnomaly { recency_days: number; frequency: number; monetary: number; anomaly_score: number; data_source: 'real' | 'synthetic'; }
export interface CustomerSegmentationResponse { algorithm: string; clusters_count: number; silhouette_score: number; inertia: number; segments: CustomerSegmentItem[]; metrics: MLModelMetrics; narrative: string; anomalies: CustomerAnomaly[]; anomalies_count: number; }
export interface MLTrainingResponse { status: string; message: string; supervised_metrics: MLModelMetrics; unsupervised_metrics: MLModelMetrics; }
export interface RevenueSummary { sales_count: number; subtotal: number; discount: number; total: number; }
export interface SalesByBranchItem { branch_id: number | null; branch_name: string; sales_count: number; total: number; }
export interface TopProductItem { product_id: number; product_name: string; units_sold: number; revenue: number; }
export interface LowStockItem { inventory_id: number; branch_id: number; branch_name: string; product_id: number; product_name: string; sku: string; available_quantity: number; }
export interface ReservationStatusItem { status: string; count: number; }
export interface SalesByChannelItem { channel: string; sales_count: number; total: number; }
export interface DashboardReport { revenue: RevenueSummary; sales_by_branch: SalesByBranchItem[]; top_products: TopProductItem[]; low_stock: LowStockItem[]; reservations: ReservationStatusItem[]; sales_by_channel: SalesByChannelItem[]; }
export interface RecommendationItem { product_id: number; product_name: string; category_name: string; price: number; image_url: string | null; score: number; reason: string; }
export interface VirtualFittingSession { id: number; customer_id: number | null; product_id: number; product_name: string; image_url: string | null; status: string; device_info: string | null; started_at: string; ended_at: string | null; }
export interface SubscriptionPlan {
  id: number;
  code: string;
  name: string;
  price_monthly?: number;
  price_annual?: number;
  currency?: string;
  max_active_branches: number;
  generative_reports_enabled: boolean;
  is_active: boolean;
}
export interface SubscriptionRecord { id: number; tenant_id: number; plan: SubscriptionPlan; status: string; valid_from: string; valid_until: string | null; paused_at?: string | null; }
export interface SubscriptionCurrentStatus {
  tenant_id: number;
  tenant_name: string;
  tenant_status: string;
  subscription: SubscriptionRecord | null;
  plan: SubscriptionPlan | null;
  max_active_branches: number;
  generative_reports_enabled: boolean;
  active_branch_count: number;
  is_trial: boolean;
  is_expired: boolean;
  read_only_mode: boolean;
  is_paused: boolean;
  days_remaining: number | null;
  retention_days_remaining: number | null;
  email_verified: boolean;
  is_cancelled?: boolean;
  cancellation_reason?: string | null;
  cancellation_effective_at?: string | null;
  reactivation_requested: boolean;
  requested_plan_code: string | null;
}
export interface PlatformTenant {
  id: number;
  name: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'INACTIVE';
  created_at: string;
  active_subscription: SubscriptionRecord | null;
  is_trial?: boolean;
  is_expired?: boolean;
  is_cancelled?: boolean;
  cancellation_reason?: string | null;
  reactivation_requested?: boolean;
  requested_plan_code?: string | null;
}

