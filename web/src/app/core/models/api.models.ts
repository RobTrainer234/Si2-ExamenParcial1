export interface UserSession {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  is_active: boolean;
}

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

export interface CatalogFilterOption { id: number; name: string; }

export interface CatalogFilters {
  categories: CatalogFilterOption[];
  sizes: CatalogFilterOption[];
  colors: CatalogFilterOption[];
  branches: CatalogFilterOption[];
}

export interface CatalogVariant {
  id: number;
  size_id: number;
  size_name: string;
  color_id: number;
  color_name: string;
  sku: string;
}

export interface CatalogDetail extends CatalogItem {
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
