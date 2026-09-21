import { expect, test } from '@playwright/test';

const adminEmail = process.env.E2E_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD;

test.describe('FashionStore smoke flows', () => {
  test('public catalog is available', async ({ page }) => {
    await page.goto('/catalog');
    await expect(page).toHaveTitle(/FashionStore/i);
    await expect(page.getByRole('heading', { name: /explorá la colección/i })).toBeVisible();
    await expect(page.locator('.catalog-loading')).toBeHidden();
    await expect(page.locator('.result-count, .empty')).toBeVisible();
    await expect.poll(() => page.locator('.product-card').count()).toBeGreaterThan(0);
    await expect.poll(() => page.locator('.product-image img').evaluateAll((images) => images.every((image) => image.complete && image.naturalWidth > 0))).toBe(true);
  });

  test('client can search, filter and open product detail', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill('client.demo@fashionstore.com');
    await page.getByLabel('Contraseña').fill('Client123!');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page).toHaveURL(/\/catalog$/);

    await page.getByLabel('Buscar prendas').fill('Bolso');
    await page.getByRole('button', { name: 'Aplicar filtros' }).click();
    await expect(page.locator('.product-card')).toHaveCount(1);
    await expect(page.getByRole('heading', { name: 'Bolso Cuero Sur' })).toBeVisible();

    await page.getByRole('button', { name: 'Todo' }).click();
    await page.getByLabel('Categoría').selectOption({ label: 'Accesorios' });
    await page.getByRole('button', { name: 'Aplicar filtros' }).click();
    await expect(page.locator('.product-card')).toHaveCount(1);

    await page.locator('.product-card').click();
    await expect(page).toHaveURL(/\/catalog\/\d+$/);
    await expect(page.getByRole('heading', { name: 'Bolso Cuero Sur' })).toBeVisible();
  });

  test('client can check availability by branch', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill('client.demo@fashionstore.com');
    await page.getByLabel('Contraseña').fill('Client123!');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page).toHaveURL(/\/catalog$/);

    await page.locator('.product-card').first().click();
    await expect(page).toHaveURL(/\/catalog\/\d+$/);
    await expect(page.getByRole('button', { name: 'Ver disponibilidad en tiendas' })).toBeEnabled();
    await page.getByRole('button', { name: 'Ver disponibilidad en tiendas' }).click();
    await expect(page.getByRole('heading', { name: 'Disponibilidad en tiendas' })).toBeVisible();
    await expect(page.locator('.branch-row')).toHaveCount(2);
    await expect(page.locator('.branch-row').first()).toContainText(/disponibles|Agotado/);
    await expect(page.locator('.branch-row').first().getByRole('button', { name: 'Agregar a bolsa' })).toBeVisible();

    await page.locator('.branch-row').first().getByRole('button', { name: 'Agregar a bolsa' }).click();
    await expect(page).toHaveURL(/\/catalog\/\d+$/);
    await expect(page.getByRole('status')).toContainText('se agregó a la bolsa');
    await page.getByRole('link', { name: 'Ver bolsa', exact: true }).click();
    await expect(page).toHaveURL(/\/fitting-bag$/);
    await expect(page.getByRole('heading', { name: 'Bolsa de probador' })).toBeVisible();
    await page.getByLabel('Sucursal disponible').selectOption({ index: 1 });
    const reservationResponse = page.waitForResponse((response) => response.url().includes('/api/v1/reservations') && response.request().method() === 'POST');
    await page.getByRole('button', { name: 'Confirmar reserva de probador' }).click();
    await expect((await reservationResponse).status()).toBe(201);
  });

  test('administrator can open audit log', async ({ page }) => {
    test.skip(!adminEmail || !adminPassword, 'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD');

    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill(adminEmail!);
    await page.getByLabel('Contraseña').fill(adminPassword!);
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page).toHaveURL(/\/catalog$/);

    await page.goto('/audit');
    await expect(page.getByRole('heading', { name: 'Bitácora' })).toBeVisible();
    await expect(page.locator('.master-count')).toContainText('eventos');
  });

  test('authorized operator can open inventory and movement history', async ({ page }) => {
    test.skip(!adminEmail || !adminPassword, 'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD');

    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill(adminEmail!);
    await page.getByLabel('Contraseña').fill(adminPassword!);
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page).toHaveURL(/\/catalog$/);
    await page.goto('/operations');
    await expect(page.getByRole('heading', { name: 'Inventario asignado' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Historial de movimientos' })).toBeVisible();
  });
});
