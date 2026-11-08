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

const conflictOperation = {
  client_operation_id: 'op-cu12-conflict-001',
  branch_id: 10,
  operation_type: 'SALE',
  status: 'CONFLICT',
  sale_payload: {
    customer_id: null,
    customer_name: 'Sofía Moreno',
    customer_nit: '7845123',
    customer_phone: '70000001',
    items: [{ product_variant_id: 1001, quantity: 2, unit_price: 150 }],
    total: 300,
    created_at: '2026-04-10T15:30:00.000Z',
  },
  sale_id: null,
  order_number: null,
  conflict_detail: {
    code: 'INSUFFICIENT_STOCK',
    message: 'Stock insuficiente para uno o más productos.',
    variant_id: 1001,
  },
  created_at: '2026-04-10T15:30:00.000Z',
  synced_at: '2026-04-10T15:31:00.000Z',
};

async function seedConflictOperation(page: import('@playwright/test').Page): Promise<void> {
  await page.evaluate(async (operation) => {
    const database = await new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open('fashionstore_offline_catalog');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction('pending_operations', 'readwrite');
      transaction.objectStore('pending_operations').put(operation);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }, conflictOperation);
}

test.describe('CU-12 · Gestionar Conflictos de Sincronización', () => {
  test('captures the current conflict state in the offline operations tray', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    const syncRequests: string[] = [];

    await page.route('**/api/v1/**', async (route) => {
      const request = route.request();
      const url = new URL(request.url());

      if (request.method() === 'GET' && url.pathname === '/api/v1/catalog/navigation') {
        await route.fulfill({
          json: { audiences: [], categories: [], seasons: [], branches: [] },
        });
        return;
      }

      if (url.pathname === '/api/v1/sync/transactions') {
        syncRequests.push(`${request.method()} ${url.pathname}`);
      }
      throw new Error(`CU-12 received an unexpected API request: ${request.method()} ${url.pathname}`);
    });

    await page.addInitScript((session) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
    }, cashierSession);

    try {
      // Visit once so the application creates its IndexedDB schema in this isolated context.
      await page.goto('/offline-transactions');
      await expect(page.getByRole('heading', { name: 'Bandeja de Operaciones Pendientes' })).toBeVisible();

      await seedConflictOperation(page);
      await page.reload();

      await expect(page.getByRole('heading', { name: 'Bandeja de Operaciones Pendientes' })).toBeVisible();
      const operationRow = page.getByRole('row').filter({ hasText: conflictOperation.client_operation_id });
      await expect(operationRow).toBeVisible();
      await expect(operationRow.getByText('VENTA', { exact: true })).toBeVisible();
      await expect(operationRow.getByText(conflictOperation.client_operation_id)).toBeVisible();
      await expect(operationRow.getByText('#10')).toBeVisible();
      await expect(operationRow.getByText('Sofía Moreno')).toBeVisible();
      await expect(operationRow.getByText('Conflicto')).toBeVisible();
      await expect(operationRow.getByText('INSUFFICIENT_STOCK: Stock insuficiente para uno o más productos.')).toBeVisible();
      expect(syncRequests).toEqual([]);

      await page.screenshot({
        path: '../docs/ui-screens/etapa-2/CU-12_Gestionar_Conflictos_Sincronizacion_Estado_Actual.png',
        fullPage: true,
      });
    } finally {
      await context.close();
    }
  });
});
