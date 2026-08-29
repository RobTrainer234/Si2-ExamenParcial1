export interface Page<T> { items: T[]; page: number; page_size: number; total: number; total_pages: number; }
export interface AdminUser { id: number; first_name: string; last_name: string; email: string; phone: string; role: string; is_active: boolean; }
export interface City { id: number; name: string; is_active: boolean; }
export interface Branch { id: number; city_id: number; city_name: string; name: string; address: string; phone: string; latitude: number | null; longitude: number | null; is_active: boolean; }
export interface Category { id: number; name: string; description: string | null; is_active: boolean; }
export interface Size { id: number; name: string; is_active: boolean; }
export interface Color { id: number; name: string; hex_code: string | null; is_active: boolean; }
export interface Supplier { id: number; trade_name: string; legal_name: string | null; tax_id: string | null; email: string | null; phone: string | null; address: string | null; is_active: boolean; }
export interface ProductSummary { id: number; category_id: number; category_name: string; code: string; name: string; slug: string; price: number; is_active: boolean; }
export interface ProductVariant { id: number; size_id: number; size_name: string; color_id: number; color_name: string; sku: string; is_active: boolean; }
export interface ProductDetail extends ProductSummary { description: string | null; variants: ProductVariant[]; supplier_ids: number[]; images: { id: number; image_url: string; is_primary: boolean; sort_order: number }[]; }
