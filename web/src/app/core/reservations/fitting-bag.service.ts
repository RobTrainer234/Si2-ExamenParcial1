import { Injectable, computed, signal } from '@angular/core';

import { AvailabilityItem, CatalogDetail, CatalogVariant } from '../models/api.models';

export interface FittingBagBranch {
  branch_id: number;
  branch_name: string;
  city_name: string;
  address: string;
  stock: number;
}

export interface FittingBagItem {
  product_id: number;
  product_name: string;
  product_code: string;
  image_url: string | null;
  unit_price: number;
  product_variant_id: number;
  size_name: string;
  color_name: string;
  sku: string;
  quantity: number;
  available_branches: FittingBagBranch[];
}

@Injectable({ providedIn: 'root' })
export class FittingBagService {
  private readonly storageKey = 'fashionstore.fittingBag.v1';
  private readonly itemsState = signal<FittingBagItem[]>(this.load());
  readonly items = this.itemsState.asReadonly();
  readonly count = computed(() => this.itemsState().reduce((total, item) => total + item.quantity, 0));
  readonly itemCount = computed(() => this.itemsState().length);
  readonly sharedBranches = computed(() => this.intersectBranches(this.itemsState()));

  add(product: CatalogDetail, variant: CatalogVariant, availability: AvailabilityItem[], quantity = 1): void {
    const availableBranches = availability.filter((branch) => branch.available && branch.stock > 0).map((branch) => ({
      branch_id: branch.branch_id,
      branch_name: branch.branch_name,
      city_name: branch.city_name,
      address: branch.address,
      stock: branch.stock,
    }));
    if (!availableBranches.length) return;

    this.update((items) => {
      const current = items.find((item) => item.product_variant_id === variant.id);
      if (current) {
        return items.map((item) => item.product_variant_id === variant.id ? { ...item, quantity: Math.min(item.quantity + quantity, this.maxSharedStock(item, availableBranches)), available_branches: availableBranches } : item);
      }
      return [...items, {
        product_id: product.id,
        product_name: product.name,
        product_code: product.code,
        image_url: product.images.find((image) => image.is_primary)?.image_url || product.images[0]?.image_url || product.image_url,
        unit_price: product.price,
        product_variant_id: variant.id,
        size_name: variant.size_name,
        color_name: variant.color_name,
        sku: variant.sku,
        quantity: Math.max(1, quantity),
        available_branches: availableBranches,
      }];
    });
  }

  setQuantity(productVariantId: number, quantity: number): void {
    this.update((items) => items.map((item) => item.product_variant_id === productVariantId ? { ...item, quantity: Math.max(1, Math.min(quantity, this.itemMaxQuantity(item))) } : item));
  }

  remove(productVariantId: number): void {
    this.update((items) => items.filter((item) => item.product_variant_id !== productVariantId));
  }

  clear(): void {
    this.itemsState.set([]);
    this.persist([]);
  }

  private update(project: (items: FittingBagItem[]) => FittingBagItem[]): void {
    const next = project(this.itemsState());
    this.itemsState.set(next);
    this.persist(next);
  }

  private intersectBranches(items: FittingBagItem[]): FittingBagBranch[] {
    if (!items.length) return [];
    const [first, ...rest] = items;
    return first.available_branches
      .filter((branch) => rest.every((item) => item.available_branches.some((candidate) => candidate.branch_id === branch.branch_id && candidate.stock >= item.quantity)) && branch.stock >= first.quantity)
      .map((branch) => ({ ...branch, stock: Math.min(...items.map((item) => item.available_branches.find((candidate) => candidate.branch_id === branch.branch_id)?.stock || 0)) }));
  }

  private itemMaxQuantity(item: FittingBagItem): number {
    const stocks = item.available_branches.map((branch) => branch.stock).filter((stock) => stock > 0);
    return stocks.length ? Math.max(...stocks) : 1;
  }

  private maxSharedStock(item: FittingBagItem, branches: FittingBagBranch[]): number {
    const stocks = branches.map((branch) => branch.stock).filter((stock) => stock > 0);
    const max = stocks.length ? Math.max(...stocks) : item.quantity;
    return Math.max(1, max);
  }

  private load(): FittingBagItem[] {
    try {
      const raw = globalThis.localStorage?.getItem(this.storageKey);
      if (!raw) return [];
      const parsed = JSON.parse(raw) as FittingBagItem[];
      return Array.isArray(parsed) ? parsed.filter((item) => item.product_variant_id && item.quantity > 0 && Array.isArray(item.available_branches)) : [];
    } catch {
      return [];
    }
  }

  private persist(items: FittingBagItem[]): void {
    try {
      globalThis.localStorage?.setItem(this.storageKey, JSON.stringify(items));
    } catch {
      // Storage is best-effort; the in-memory draft remains usable.
    }
  }
}
