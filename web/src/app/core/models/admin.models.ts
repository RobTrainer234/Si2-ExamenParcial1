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
export interface Promotion { id: number; name: string; description: string | null; discount_type: 'PERCENT' | 'FIXED'; discount_value: number; starts_at: string; ends_at: string; is_active: boolean; product_ids: number[]; }
export interface PromotionInput { name: string; description?: string | null; discount_type: 'PERCENT' | 'FIXED'; discount_value: number; starts_at: string; ends_at: string; }
export interface DashboardFilters { branch_id?: number; start_date?: string; end_date?: string; }
export type ReportExportFormat = 'xlsx' | 'pdf' | 'pptx';
export type ReportAssistantIntentKind = 'dashboard' | 'top_products' | 'sales_by_branch' | 'inventory' | 'reservations' | string;
export interface ReportAssistantRequest { prompt: string; date_from?: string; date_to?: string; branch_id?: number; }
export interface ReportAssistantFilters { date_from?: string | null; date_to?: string | null; branch_id?: number | null; }
export interface ReportAssistantIntent { kind: ReportAssistantIntentKind; filters?: ReportAssistantFilters; reasoning?: string | null; }
export interface ReportAssistantResponse { intent: ReportAssistantIntent; filters: ReportAssistantFilters; data: unknown; narrative: string; provider: string; fallback_used: boolean; }
export interface RevenueSummary { sales_count: number; subtotal: number; discount: number; total: number; }
export interface SalesByBranchItem { branch_id: number | null; branch_name: string; sales_count: number; total: number; }
export interface TopProductItem { product_id: number; product_name: string; units_sold: number; revenue: number; }
export interface LowStockItem { inventory_id: number; branch_id: number; branch_name: string; product_id: number; product_name: string; sku: string; available_quantity: number; }
export interface ReservationStatusItem { status: string; count: number; }
export interface SalesByChannelItem { channel: string; sales_count: number; total: number; }
export interface DashboardReport { revenue: RevenueSummary; sales_by_branch: SalesByBranchItem[]; top_products: TopProductItem[]; low_stock: LowStockItem[]; reservations: ReservationStatusItem[]; sales_by_channel: SalesByChannelItem[]; }
export interface RecommendationItem { product_id: number; product_name: string; category_name: string; price: number; image_url: string | null; score: number; reason: string; }
export interface VirtualFittingSession { id: number; customer_id: number | null; product_id: number; product_name: string; image_url: string | null; status: string; device_info: string | null; started_at: string; ended_at: string | null; }
