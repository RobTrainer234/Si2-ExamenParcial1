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
    permissions: ['sales.read', 'sales.create'],
    branches: [{ id: 10, name: 'Aurora Central' }],
  },
};

const catalogProduct = {
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

const branchInventory = {
  id: 5001,
  branch_id: 10,
  branch_name: 'Aurora Central',
  product_id: 101,
  product_name: 'Vestido Aurora',
  product_variant_id: 1002,
  sku: 'VES-AURORA-001-M-ROJO',
  size_name: 'M',
  color_name: 'Rojo',
  stock_quantity: 8,
  reserved_quantity: 0,
  available_quantity: 8,
};

const saleLookup = {
  sale_id: 13001,
  order_number: 'ORD-CU13-001',
  sale_date: '2030-01-13',
  branch_id: 10,
  status: 'PAID',
  items: [{
    id: 1,
    variant_id: 1001,
    name: 'Vestido Aurora',
    sku: 'VES-AURORA-001-S-ROJO',
    purchased_quantity: 1,
    remaining_exchangeable_quantity: 1,
    net_paid_line_total: 350,
  }],
};

const quote = {
  returned_value: 350,
  replacement_unit_price: 350,
  delivered_value: 350,
  difference: 0,
  cash_settlement_eligible: true,
  available_stock: 8,
  reserved_stock: 0,
  expires_at: '2099-12-31T23:59:59Z',
  quote_fingerprint: 'cu13-quote-fingerprint',
};

function pageOf<T>(items: T[]) {
  return { items, total: items.length, page: 1, page_size: 100, total_pages: items.length ? 1 : 0 };
}

test.describe('CU-13 · Gestionar Cambio de Prendas · Interfaz Actual Web', () => {
  test('captures the online exchange after mocked server confirmation', async ({ browser }) => {
    const configuredBaseUrl = new URL(process.env.E2E_BASE_URL || 'http://127.0.0.1:4200');
    const loopbackHostnames = new Set(['127.0.0.1', 'localhost', '::1', '[::1]']);
    if (configuredBaseUrl.protocol !== 'http:' || !loopbackHostnames.has(configuredBaseUrl.hostname)) {
      throw new Error(`E2E_BASE_URL must use http:// and a loopback hostname, received ${configuredBaseUrl.origin}`);
    }

    const appOrigin = configuredBaseUrl.origin;
    const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    const apiRequests: string[] = [];
    const externalRequestsAborted: string[] = [];
    const allowedFontOrigins = new Set(['https://fonts.googleapis.com', 'https://fonts.gstatic.com']);
    const allowedFontRequests: string[] = [];
    let lookupPayload: unknown;
    let quotePayload: unknown;
    let finalizePayload: any;
    let finalizeSeen = false;

    await page.route('**/api/v1/**', async (route) => {
      const request = route.request();
      const requestOrigin = request.headers().origin;
      if (requestOrigin !== appOrigin) {
        await route.abort();
        throw new Error(`Rejected API request with origin ${requestOrigin || '<missing>'}; expected ${appOrigin}`);
      }
      const url = new URL(request.url());
      const path = url.pathname;
      apiRequests.push(`${request.method()} ${path}`);

      if (request.method() === 'GET' && path === '/api/v1/catalog/navigation') {
        await route.fulfill({ json: { audiences: [], categories: [], seasons: [], branches: [{ id: 10, name: 'Aurora Central' }] } });
        return;
      }
      if (request.method() === 'GET' && path === '/api/v1/catalog/filters') {
        await route.fulfill({ json: { categories: [{ id: 1, name: 'Vestidos' }], sizes: [], colors: [], branches: [{ id: 10, name: 'Aurora Central' }], audiences: [] } });
        return;
      }
      if (request.method() === 'GET' && path === '/api/v1/catalog') {
        await route.fulfill({ json: pageOf([catalogProduct]) });
        return;
      }
      if (request.method() === 'GET' && path === '/api/v1/inventory') {
        await route.fulfill({ json: pageOf([branchInventory]) });
        return;
      }
      if (request.method() === 'GET' && path === '/api/v1/sales/lookup/ORD-CU13-001') {
        await route.fulfill({ json: saleLookup });
        return;
      }
      if (request.method() === 'POST' && path === '/api/v1/sales/13001/exchange/quote') {
        quotePayload = request.postDataJSON();
        expect(quotePayload).toEqual({ returned_variant_id: 1001, returned_quantity: 1, new_variant_id: 1002, new_quantity: 1 });
        await route.fulfill({ json: quote });
        return;
      }
      if (request.method() === 'POST' && path === '/api/v1/sales/13001/exchange') {
        finalizeSeen = true;
        finalizePayload = request.postDataJSON();
        expect(finalizePayload.returned_variant_id).toBe(1001);
        expect(finalizePayload.returned_quantity).toBe(1);
        expect(finalizePayload.new_variant_id).toBe(1002);
        expect(finalizePayload.new_quantity).toBe(1);
        expect(finalizePayload.quote_fingerprint).toBe(quote.quote_fingerprint);
        expect(finalizePayload.quote_expires_at).toBe(quote.expires_at);
        expect(typeof finalizePayload.idempotency_key).toBe('string');
        expect(finalizePayload.idempotency_key).not.toBe('');
        await route.fulfill({ json: { order_number: 'ORD-CU13-001', status: 'EXCHANGED', quarantine_id: 9001, quarantine_status: 'PENDING', returned_value: 350, delivered_value: 350, difference: 0 } });
        return;
      }
      throw new Error(`Unexpected CU-13 API request: ${request.method()} ${request.url()}`);
    });

    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.origin === appOrigin) {
        await route.fallback();
        return;
      }
      if (allowedFontOrigins.has(url.origin)) {
        allowedFontRequests.push(request.url());
        await route.fallback();
        return;
      }
      externalRequestsAborted.push(request.url());
      await route.abort();
    });

    await page.addInitScript((session) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
    }, cashierSession);

    try {
      await page.goto('/pos');
      await expect(page.getByRole('heading', { name: 'Punto de venta (POS)' })).toBeVisible();
      await page.getByRole('button', { name: /Cambio/ }).click();

      await page.getByLabel('Número de orden o recibo').fill('ORD-CU13-001');
      await page.getByRole('button', { name: 'Buscar venta', exact: true }).click();
      await expect(page.getByText('Venta encontrada: ORD-CU13-001')).toBeVisible();

      await page.getByLabel('Artículo devuelto').selectOption({ label: 'Vestido Aurora · VES-AURORA-001-S-ROJO · Neto pagado Bs 350 · Restan 1 de 1' });
      await page.getByLabel('Variante de reemplazo').selectOption({ label: 'Vestido Aurora · M / Rojo · Disponible 8' });
      await page.getByRole('button', { name: 'Solicitar cotización', exact: true }).click();
      await expect(page.getByText('Cotización autenticada del servidor')).toBeVisible();
      await expect(page.getByText(/Diferencia:/)).toContainText('0.00');
      await expect(page.getByText(/Vigente hasta 2099-12-31T23:59:59Z/)).toBeVisible();

      await expect(page.getByRole('button', { name: 'Confirmar cambio online', exact: true })).toBeEnabled();
      await page.getByRole('button', { name: 'Confirmar cambio online', exact: true }).click();
      await expect(page.getByText('Estado del cambio: EXCHANGED')).toBeVisible();
      await expect(page.getByText(/Cuarentena recepción: PENDING/)).toBeVisible();
      expect(finalizeSeen).toBe(true);
      expect(apiRequests.some((request) => request.includes('/sync/transactions'))).toBe(false);
      expect(externalRequestsAborted.every((requestUrl) => new URL(requestUrl).origin !== appOrigin)).toBe(true);
      expect(allowedFontRequests.every((requestUrl) => allowedFontOrigins.has(new URL(requestUrl).origin))).toBe(true);
      const queuedExchangeRecords = await page.evaluate(async () => {
        const database = await new Promise<IDBDatabase | null>((resolve) => {
          const request = indexedDB.open('fashionstore_offline_catalog');
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => resolve(null);
        });
        if (!database || !Array.from(database.objectStoreNames).includes('pending_operations')) return [];
        return await new Promise<unknown[]>((resolve, reject) => {
          const request = database.transaction('pending_operations').objectStore('pending_operations').getAll();
          request.onsuccess = () => resolve((request.result as Array<{ operation_type?: string }>).filter((item) => item.operation_type === 'EXCHANGE'));
          request.onerror = () => reject(request.error);
        });
      });
      expect(queuedExchangeRecords).toEqual([]);

      await expect.poll(() => page.locator('.toast').count()).toBe(0);
      await page.evaluate(async () => {
        await document.fonts.ready;
      });
      await page.screenshot({
        path: '../docs/ui-screens/etapa-2/CU-13_Gestionar_Cambio_Prendas_Interfaz_Actual_Web.png',
        fullPage: true,
      });
    } finally {
      await context.close();
    }
  });
});
