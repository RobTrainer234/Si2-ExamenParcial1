import { expect, test } from '@playwright/test';

const catalogPayload = {
  metadata: {
    tenant_id: 1,
    tenant_name: 'Boutique Aurora',
    branch_id: 10,
    branch_name: 'Aurora Central',
    sync_timestamp: '2026-10-23T20:00:00Z',
    catalog_version: 'cat-v1-100',
  },
  categories: [{ id: 1, name: 'Vestidos', is_active: true }],
  products: [{
    id: 101,
    category_id: 1,
    category_name: 'Vestidos',
    name: 'Vestido Persistente',
    code: 'VES-PERSISTENTE',
    slug: 'vestido-persistente',
    description: 'Producto guardado en IndexedDB',
    price: 350,
    image_url: null,
    is_active: true,
  }],
  variants: [{
    id: 1001,
    product_id: 101,
    sku: 'VES-PERSISTENTE-S-RED',
    size_id: 1,
    size_name: 'S',
    color_id: 1,
    color_name: 'Rojo',
    price: 350,
    is_active: true,
  }],
  inventory: [{
    product_variant_id: 1001,
    stock_quantity: 15,
    reserved_quantity: 3,
    available_quantity: 12,
  }],
};

const catalogPage = {
  items: catalogPayload.products,
  total: 1,
  page: 1,
  page_size: 12,
  total_pages: 1,
};

const filters = {
  categories: [{ id: 1, name: 'Vestidos' }],
  sizes: [{ id: 1, name: 'S' }],
  colors: [{ id: 1, name: 'Rojo', hex_code: '#b91c1c' }],
  branches: [{ id: 10, name: 'Aurora Central' }],
};

async function mockCatalogApi(page: import('@playwright/test').Page): Promise<void> {
  await page.route('**/api/v1/catalog/navigation**', async (route) => {
    await route.fulfill({ json: { seasons: [], collections: [], audiences: [] } });
  });
  await page.route('**/api/v1/catalog**', async (route) => {
    await route.fulfill({ json: route.request().url().includes('/filters') ? filters : catalogPage });
  });
  await page.route('**/api/v1/sync/catalog**', async (route) => {
    await route.fulfill({ json: catalogPayload });
  });
}

test.describe('production PWA offline durability', () => {
  test('registers the service worker and serves a durable offline catalog from IndexedDB', async ({ page, context }) => {
    await mockCatalogApi(page);
    await page.goto('/catalog');

    const registration = await page.evaluate(async () => {
      const current = await navigator.serviceWorker.ready;
      return { scope: current.scope };
    });
    expect(registration.scope).toMatch(/\/$/);

    const manifest = await page.request.get('/manifest.webmanifest');
    expect(manifest.ok()).toBe(true);
    expect((await manifest.json()).name).toContain('FashionStore');

    await page.getByRole('button', { name: /descargar catálogo offline/i }).click();
    await expect(page.getByText(/sincronizado: aurora central/i)).toBeVisible();

    const databaseEvidence = await page.evaluate(async () => {
      const database = await new Promise<IDBDatabase>((resolve, reject) => {
        const request = indexedDB.open('fashionstore_offline_catalog');
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      return {
        stores: Array.from(database.objectStoreNames),
        products: await new Promise<number>((resolve, reject) => {
          const request = database.transaction('products').objectStore('products').count();
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        }),
      };
    });
    expect(databaseEvidence.stores).toEqual(expect.arrayContaining(['metadata', 'products', 'variants', 'inventory']));
    expect(databaseEvidence.products).toBe(1);

    await page.reload();
    await expect.poll(() => page.evaluate(() => Boolean(navigator.serviceWorker.controller))).toBe(true);
    await context.setOffline(true);
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Vestido Persistente' })).toBeVisible();
    await expect(page.getByRole('status')).toContainText('Modo offline');
  });
});
