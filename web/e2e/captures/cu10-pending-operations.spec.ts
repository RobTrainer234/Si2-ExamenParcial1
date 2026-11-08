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

const pendingReservation = {
  client_operation_id: 'op-cu10-reservation-001',
  branch_id: 10,
  operation_type: 'RESERVATION',
  status: 'PENDING_SYNC',
  reservation_payload: {
    customer_id: null,
    customer_name: 'María González',
    customer_nit: '7845123',
    customer_phone: '70000001',
    items: [{ product_variant_id: 1001, quantity: 1 }],
    scheduled_for: '2026-04-15',
    notes: 'Reserva capturada durante una jornada sin conexión',
    created_at: '2026-04-10T15:30:00.000Z',
  },
  reservation_id: null,
  created_at: '2026-04-10T15:30:00.000Z',
  synced_at: null,
};

async function seedPendingOperation(page: import('@playwright/test').Page): Promise<void> {
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
  }, pendingReservation);
}

test.describe('CU-10 · Consultar Operaciones Locales Pendientes', () => {
  test('captures one pending reservation in the offline operations tray', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    const syncCalls: string[] = [];

    await page.route('**/api/v1/**', async (route) => {
      throw new Error(`CU-10 must not call an API other than the mocked shell navigation: ${route.request().method()} ${route.request().url()}`);
    });
    await page.route('**/api/v1/sync/transactions', async (route) => {
      syncCalls.push(`${route.request().method()} ${route.request().url()}`);
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'CU-10 must not synchronize the captured operation' }),
      });
    });
    await page.route('**/api/v1/catalog/navigation', async (route) => {
      await route.fulfill({
        json: { audiences: [], categories: [], seasons: [], branches: [] },
      });
    });

    await page.addInitScript((session) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
    }, cashierSession);

    try {
      // The first visit lets the application create its IndexedDB schema.
      await page.goto('/offline-transactions');
      await expect(page.getByRole('heading', { name: 'Bandeja de Operaciones Pendientes' })).toBeVisible();

      // Seed only the isolated browser context's IDB, then reload the actual tray route.
      // The dev server itself is needed for a document reload, so keep API access mocked
      // and switch the isolated context offline immediately after the tray renders.
      await seedPendingOperation(page);
      await page.reload();
      await context.setOffline(true);

      await expect(page).toHaveURL(/\/offline-transactions$/);
      await expect(page.getByRole('heading', { name: 'Bandeja de Operaciones Pendientes' })).toBeVisible();
      const operationRow = page.getByRole('row').filter({ hasText: pendingReservation.client_operation_id });
      await expect(operationRow).toBeVisible();
      await expect(operationRow.getByText('RESERVA', { exact: true })).toBeVisible();
      await expect(operationRow.getByText(pendingReservation.client_operation_id)).toBeVisible();
      await expect(operationRow.getByText('#10')).toBeVisible();
      await expect(operationRow.getByText('María González')).toBeVisible();
      await expect(operationRow.getByText('1 prendas')).toBeVisible();
      await expect(operationRow.getByText('Pendiente')).toBeVisible();
      expect(syncCalls).toEqual([]);

      await page.screenshot({
        path: '../docs/ui-screens/etapa-2/CU-10_Consultar_Operaciones_Locales_Pendientes.png',
        fullPage: true,
      });
    } finally {
      await context.close();
    }
  });
});
