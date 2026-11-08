import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.E2E_PWA_BASE_URL || 'http://127.0.0.1:4300';

export default defineConfig({
  testDir: './e2e',
  testMatch: 'offline-pwa.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'html',
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run build && node e2e/serve-production.mjs',
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
