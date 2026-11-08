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
  client_operation_id: 'op-cu11-reservation-9001',
  branch_id: 10,
  operation_type: 'RESERVATION',
  status: 'PENDING_SYNC',
  reservation_payload: {
    customer_id: null,
    customer_name: 'Sofía Moreno',
    customer_nit: '7845123',
    customer_phone: '70000001',
    items: [{ product_variant_id: 1001, quantity: 1 }],
    scheduled_for: '2026-04-15',
    notes: 'Reserva sintética para la captura CU-11',
    created_at: '2026-04-10T15:30:00.000Z',
  },
  reservation_id: null,
  created_at: '2026-04-10T15:30:00.000Z',
  synced_at: null,
};

async function seedPendingReservation(page: import('@playwright/test').Page): Promise<void> {
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

async function readReservation(page: import('@playwright/test').Page): Promise<{
  status: string;
  syncedAt: string | null;
  reservationId: number | null;
}> {
  return page.evaluate(async (operationId) => {
    const database = await new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open('fashionstore_offline_catalog');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    return new Promise((resolve, reject) => {
      const request = database.transaction('pending_operations').objectStore('pending_operations').get(operationId);
      request.onsuccess = () => {
        const operation = request.result as { status: string; synced_at: string | null; reservation_id: number | null };
        resolve({ status: operation.status, syncedAt: operation.synced_at, reservationId: operation.reservation_id });
      };
      request.onerror = () => reject(request.error);
    });
  }, pendingReservation.client_operation_id);
}

test.describe('CU-11 · Sincronizar Operaciones con el Servidor', () => {
  test('captures one mocked reservation synchronization as confirmed', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    const syncRequests: Array<{ method: string; body: { operations: Array<{ client_operation_id: string; operation_type: string; branch_id: number }> } }> = [];

    await page.route('**/api/v1/**', async (route) => {
      const request = route.request();
      const url = new URL(request.url());

      if (request.method() === 'GET' && url.pathname === '/api/v1/catalog/navigation') {
        await route.fulfill({
          json: { audiences: [], categories: [], seasons: [], branches: [] },
        });
        return;
      }

      if (request.method() === 'POST' && url.pathname === '/api/v1/sync/transactions') {
        const body = request.postDataJSON() as { operations: Array<{ client_operation_id: string }> };
        syncRequests.push({ method: request.method(), body });
        await route.fulfill({
          json: {
            processed_count: 1,
            confirmed_count: 1,
            conflict_count: 0,
            results: [{
              client_operation_id: pendingReservation.client_operation_id,
              operation_type: 'RESERVATION',
              status: 'CONFIRMED',
              reservation_id: 9001,
              conflict_detail: null,
              processed_at: '2026-04-10T15:31:00.000Z',
            }],
          },
        });
        return;
      }

      throw new Error(`CU-11 received an unexpected API request: ${request.method()} ${url.pathname}`);
    });

    await page.addInitScript((session) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
    }, cashierSession);

    try {
      // Visit once so the application creates its IndexedDB schema in this isolated context.
      await page.goto('/offline-transactions');
      await expect(page.getByRole('heading', { name: 'Bandeja de Operaciones Pendientes' })).toBeVisible();

      await seedPendingReservation(page);
      await page.reload();
      await expect(page.getByRole('heading', { name: 'Bandeja de Operaciones Pendientes' })).toBeVisible();

      const operationRow = page.getByRole('row').filter({ hasText: pendingReservation.client_operation_id });
      await expect(operationRow).toBeVisible();
      await expect(operationRow.getByText('Pendiente')).toBeVisible();

      await page.getByRole('button', { name: /Sincronizar ahora/ }).click();

      await expect(operationRow.getByText('Confirmada')).toBeVisible();
      await expect(operationRow.getByText('Reserva #9001')).toBeVisible();
      await expect(page.getByText('Sincronización completada: 1 confirmadas, 0 en conflicto/rechazadas.')).toBeVisible();

      expect(syncRequests).toHaveLength(1);
      expect(syncRequests[0].method).toBe('POST');
      expect(syncRequests[0].body.operations).toHaveLength(1);
      expect(syncRequests[0].body.operations[0]).toMatchObject({
        client_operation_id: pendingReservation.client_operation_id,
        operation_type: 'RESERVATION',
        branch_id: 10,
      });

      const syncedReservation = await readReservation(page);
      expect(syncedReservation.status).toBe('CONFIRMED');
      expect(syncedReservation.reservationId).toBe(9001);
      expect(syncedReservation.syncedAt).toEqual(expect.any(String));

      await page.screenshot({
        path: '../docs/ui-screens/etapa-2/CU-11_Sincronizar_Operaciones_Offline.png',
        fullPage: true,
      });
    } finally {
      await context.close();
    }
  });
});
