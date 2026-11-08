import { expect, test } from '@playwright/test';

const cashierSession = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  user: {
    id: 42,
    tenant_id: 1,
    tenant: { id: 1, name: 'Boutique Aurora', status: 'ACTIVE' },
    first_name: 'Lucía',
    last_name: 'Cajera',
    email: 'cajera.mock@example.test',
    phone: '70000000',
    role: 'CASHIER',
    is_active: true,
    permissions: ['sales.create'],
    branches: [{ id: 10, name: 'Aurora Central' }],
  },
};

const product = {
  id: 101,
  category_id: 1,
  category_name: 'Vestidos',
  audience: 'WOMEN',
  name: 'Vestido Aurora',
  code: 'VES-AURORA-001',
  slug: 'vestido-aurora',
  price: 350,
  image_url: null,
  is_active: true,
};

const inventoryItem = {
  id: 5001,
  branch_id: 10,
  branch_name: 'Aurora Central',
  product_id: 101,
  product_name: 'Vestido Aurora',
  product_variant_id: 1001,
  sku: 'VES-AURORA-001-S-ROJO',
  size_name: 'S',
  color_name: 'Rojo',
  stock_quantity: 12,
  reserved_quantity: 0,
  available_quantity: 12,
};

async function mockPosApi(page: import('@playwright/test').Page, syncCalls: string[]): Promise<void> {
  await page.route('**/api/v1/**', async (route) => {
    await route.fulfill({ json: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } });
  });

  await page.route('**/api/v1/sync/transactions', async (route) => {
    syncCalls.push(route.request().method());
    await route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'Sync must not run during this capture' }) });
  });

  await page.route('**/api/v1/catalog/filters**', async (route) => {
    await route.fulfill({
      json: {
        categories: [{ id: 1, name: 'Vestidos' }],
        sizes: [{ id: 1, name: 'S' }],
        colors: [{ id: 1, name: 'Rojo', hex_code: '#b91c1c' }],
        branches: [{ id: 10, name: 'Aurora Central' }],
        audiences: [],
      },
    });
  });

  await page.route('**/api/v1/catalog**', async (route) => {
    await route.fulfill({ json: { items: [product], total: 1, page: 1, page_size: 100, total_pages: 1 } });
  });

  await page.route('**/api/v1/inventory**', async (route) => {
    await route.fulfill({ json: { items: [inventoryItem], total: 1, page: 1, page_size: 100, total_pages: 1 } });
  });
}

test.describe('CU-08 · Registrar Venta de Contado Offline', () => {
  test('captures the rendered POS with a sale queued as PENDING_SYNC', async ({ page }) => {
    const syncCalls: string[] = [];
    await mockPosApi(page, syncCalls);
    await page.addInitScript((session) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
    }, cashierSession);
    await page.setViewportSize({ width: 1440, height: 1200 });

    await page.goto('/pos');
    await expect(page.getByRole('heading', { name: 'Punto de venta (POS)' })).toBeVisible();
    await expect(page.locator('select').nth(0)).toHaveValue('10');
    await expect(page.locator('select').nth(1)).toHaveValue('1001');

    await page.context().setOffline(true);
    await page.getByRole('button', { name: 'Cobrar venta' }).click();

    await expect(page.getByText(/\(Modo Offline\) Venta registrada localmente en espera de sincronización/)).toBeVisible();
    await expect(page.getByText(/Modo Offline: Hay 1 operación\(es\) pendiente\(s\) de sincronización/)).toBeVisible();

    const queued = await page.evaluate(async () => {
      const database = await new Promise<IDBDatabase>((resolve, reject) => {
        const request = indexedDB.open('fashionstore_offline_catalog');
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      return await new Promise<{ status: string; operationType: string }>((resolve, reject) => {
        const request = database.transaction('pending_operations').objectStore('pending_operations').getAll();
        request.onsuccess = () => {
          const [operation] = request.result as Array<{ status: string; operation_type: string }>;
          resolve({ status: operation?.status, operationType: operation?.operation_type });
        };
        request.onerror = () => reject(request.error);
      });
    });
    expect(queued).toEqual({ status: 'PENDING_SYNC', operationType: 'SALE' });
    expect(syncCalls).toEqual([]);

    await page.screenshot({
      path: '../docs/ui-screens/etapa-2/CU-08_Registrar_Venta_Contado_Offline.png',
      fullPage: true,
    });
  });
});
