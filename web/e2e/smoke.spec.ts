import { expect, test } from '@playwright/test';

const adminEmail = process.env.E2E_ADMIN_EMAIL;
const adminPassword = process.env.E2E_ADMIN_PASSWORD;

test.describe('FashionStore smoke flows', () => {
  test('public catalog is available', async ({ page }) => {
    await page.goto('/catalog');
    await expect(page).toHaveTitle(/FashionStore/i);
    await expect(page.getByRole('heading', { name: /encuentra lo que/i })).toBeVisible();
    await expect(page.locator('.catalog-loading')).toBeHidden();
    await expect(page.locator('.result-count, .empty')).toBeVisible();
    await expect.poll(() => page.locator('.product-card').count()).toBeGreaterThan(0);
    await expect.poll(() => page.locator('.product-image img').evaluateAll((images) => images.every((image) => image.complete && image.naturalWidth > 0))).toBe(true);
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
});
