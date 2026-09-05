export interface UserSession {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  is_active: boolean;
  permissions?: string[];
  supplier_id?: number | null;
}

export interface SupplierPortalProduct { id: number; code: string; name: string; is_active: boolean; }
export interface SupplierPortal { supplier_id: number; trade_name: string; products: SupplierPortalProduct[]; }
export interface SupplierSupplyOffer { id: number; supplier_id: number; supplier_name: string; product_id: number; product_name: string; product_variant_id: number; sku: string; size_name: string; color_name: string; season_id: number; season_name: string; collection_id: number | null; collection_name: string | null; status: 'AVAILABLE' | 'LIMITED' | 'OUT_OF_STOCK' | 'UPCOMING'; available_quantity: number; expected_date: string | null; notes: string | null; is_active: boolean; }

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserSession;
}

export interface CatalogItem {
  id: number;
  category_id: number;
  category_name: string;
  audience: AudienceCode;
  code: string;
  name: string;
  slug: string;
  price: number;
  image_url: string | null;
}

export interface CatalogPage {
  items: CatalogItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export type AudienceCode = 'WOMEN' | 'MEN' | 'UNISEX';
export interface AudienceOption { code: AudienceCode; name: string; product_count: number; }
export interface CatalogFilterOption { id: number; name: string; hex_code?: string | null; size_type?: 'ALPHA' | 'NUMERIC' | 'ONE_SIZE'; sort_order?: number; }

export interface CatalogFilters {
  categories: CatalogFilterOption[];
  sizes: CatalogFilterOption[];
  colors: CatalogFilterOption[];
  branches: CatalogFilterOption[];
  audiences: AudienceOption[];
}

export interface NavigationCollection { id: number; name: string; product_count: number; }
export interface NavigationSeason { id: number; name: string; collections: NavigationCollection[]; }
export interface CatalogNavigation { audiences: AudienceOption[]; categories: CatalogFilterOption[]; seasons: NavigationSeason[]; branches: CatalogFilterOption[]; }

export interface CatalogVariant {
  id: number;
  size_id: number;
  size_name: string;
  size_type: 'ALPHA' | 'NUMERIC' | 'ONE_SIZE';
  sort_order: number;
  color_id: number;
  color_name: string;
  sku: string;
  stock_total: number;
  available: boolean;
}

export interface CatalogDetail extends CatalogItem {
  size_system: 'ALPHA' | 'NUMERIC' | 'ONE_SIZE';
  description: string | null;
  images: { image_url: string; is_primary: boolean; sort_order: number }[];
  variants: CatalogVariant[];
}

export interface AvailabilityItem {
  branch_id: number;
  branch_name: string;
  city_name: string;
  address: string;
  available: boolean;
  stock: number;
}
