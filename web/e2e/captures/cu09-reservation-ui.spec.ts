import { expect, test } from '@playwright/test';

const clientSession = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  user: {
    id: 7,
    tenant_id: 1,
    tenant: { id: 1, name: 'Boutique Aurora', status: 'ACTIVE' },
    first_name: 'María',
    last_name: 'Cliente',
    email: 'cliente.mock@example.test',
    phone: '70000001',
    role: 'CLIENT',
    is_active: true,
    permissions: [],
    branches: [],
  },
};

const fittingBag = [
  {
    product_id: 101,
    product_name: 'Vestido Aurora',
    product_code: 'VES-AURORA-001',
    image_url: null,
    unit_price: 350,
    product_variant_id: 1001,
    size_name: 'S',
    color_name: 'Rojo',
    sku: 'VES-AURORA-001-S-ROJO',
    quantity: 1,
    available_branches: [
      {
        branch_id: 10,
        branch_name: 'Aurora Central',
        city_name: 'Santa Cruz',
        address: 'Av. Principal 123',
        stock: 4,
      },
    ],
  },
];

function tomorrow(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}

test.describe('CU-09 · Reserva de Prendas · Interfaz Actual Online', () => {
  test('captures the populated online reservation form without submitting', async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    const apiRequests: string[] = [];

    await page.route('**/api/v1/**', async (route) => {
      apiRequests.push(`${route.request().method()} ${route.request().url()}`);
      throw new Error(`CU-09 must not call an API other than the mocked shell navigation: ${apiRequests.at(-1)}`);
    });
    await page.route('**/api/v1/catalog/navigation', async (route) => {
      await route.fulfill({
        json: { audiences: [], categories: [], seasons: [], branches: [] },
      });
    });

    await page.addInitScript(({ session, bag }) => {
      localStorage.setItem('fashionstore_session', JSON.stringify(session));
      localStorage.setItem('fashionstore.fittingBag.v1', JSON.stringify(bag));
    }, { session: clientSession, bag: fittingBag });

    try {
      await page.goto('/fitting-bag');

      await expect(page.getByRole('heading', { name: 'Bolsa de probador' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Vestido Aurora' })).toBeVisible();

      const branch = page.getByRole('combobox', { name: 'Sucursal disponible' });
      await branch.selectOption({ label: 'Aurora Central · Santa Cruz' });
      await expect(branch.locator('option:checked')).toHaveText('Aurora Central · Santa Cruz');
      await expect(page.getByText('Av. Principal 123')).toBeVisible();

      const visitDate = page.getByLabel('Fecha de visita');
      await expect(visitDate).toHaveValue(tomorrow());
      await expect(page.getByRole('button', { name: 'Confirmar reserva de probador' })).toBeEnabled();
      expect(apiRequests).toEqual([]);

      await page.screenshot({
        path: '../docs/ui-screens/etapa-2/CU-09_Reserva_Prendas_Interfaz_Actual_Online.png',
        fullPage: true,
      });
    } finally {
      await context.close();
    }
  });
});
