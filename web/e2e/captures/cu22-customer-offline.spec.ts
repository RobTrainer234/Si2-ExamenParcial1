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

test.describe('CU-22 · Gestionar Datos Mínimos de Clientes Offline', () => {
  test('captures customer registration and listing in local IndexedDB padron', async ({ page }) => {
    const syncCalls: string[] = [];
    await mockPosApi(page, syncCalls);

    await page.addInitScript((session) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
    }, cashierSession);
    await page.setViewportSize({ width: 1440, height: 1100 });

    await page.goto('/pos');
    await expect(page.getByRole('heading', { name: 'Punto de venta (POS)' })).toBeVisible();

    // Switch to Clientes Offline tab
    const customersTab = page.getByRole('button', { name: /Clientes Offline/ });
    await expect(customersTab).toBeVisible();
    await customersTab.click();

    await expect(page.getByText('Padrón Local de Clientes (IndexedDB)')).toBeVisible();
    await expect(page.getByText('CU-22 · GESTIÓN DE DATOS MÍNIMOS DE CLIENTES OFFLINE')).toBeVisible();

    // Register first client: Valeria Méndez Arteaga
    await page.getByPlaceholder('Ej. Carlos Alberto Rojas').fill('Valeria Méndez Arteaga');
    await page.getByPlaceholder('Ej. 5928371015').fill('8492015');
    await page.getByPlaceholder('Ej. 72194850').fill('71234567');
    await page.getByPlaceholder('Ej. cliente@correo.com').fill('valeria.mendez@fashionstore.test');

    await page.getByRole('button', { name: 'Guardar cliente en IndexedDB' }).click();
    await expect(page.getByText(/registrado en el padrón local offline \(IndexedDB\)/)).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Valeria Méndez Arteaga' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '8492015' })).toBeVisible();

    // Register second client: Roberto Carlos Morales
    await page.getByPlaceholder('Ej. Carlos Alberto Rojas').fill('Roberto Carlos Morales');
    await page.getByPlaceholder('Ej. 5928371015').fill('6321940');
    await page.getByPlaceholder('Ej. 72194850').fill('77654321');
    await page.getByPlaceholder('Ej. cliente@correo.com').fill('roberto.morales@fashionstore.test');

    await page.getByRole('button', { name: 'Guardar cliente en IndexedDB' }).click();
    await expect(page.getByRole('cell', { name: 'Roberto Carlos Morales' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '6321940' })).toBeVisible();

    // Now fill the form with a third client ready to submit for great UI presentation
    await page.getByPlaceholder('Ej. Carlos Alberto Rojas').fill('Mariana Soto Céspedes');
    await page.getByPlaceholder('Ej. 5928371015').fill('10293847');
    await page.getByPlaceholder('Ej. 72194850').fill('68912345');
    await page.getByPlaceholder('Ej. cliente@correo.com').fill('mariana.soto@fashionstore.test');

    // Verify IndexedDB contents
    const storedCustomers = await page.evaluate(async () => {
      const database = await new Promise<IDBDatabase>((resolve, reject) => {
        const request = indexedDB.open('fashionstore_offline_catalog');
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      return await new Promise<any[]>((resolve, reject) => {
        const request = database.transaction('offline_customers').objectStore('offline_customers').getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    });

    expect(storedCustomers.length).toBe(2);
    expect(storedCustomers.some((c: any) => c.full_name === 'Valeria Méndez Arteaga')).toBe(true);
    expect(storedCustomers.some((c: any) => c.full_name === 'Roberto Carlos Morales')).toBe(true);
    expect(syncCalls).toEqual([]);

    await page.evaluate(async () => {
      await document.fonts.ready;
    });

    await page.screenshot({
      path: '../docs/ui-screens/etapa-2/CU-22_Gestionar_Datos_Minimos_Clientes_Offline.png',
      fullPage: true,
    });
  });
});
