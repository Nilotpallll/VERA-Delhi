import { defineConfig, devices } from '@playwright/test';

/**
 * VERA E2E Test Configuration
 *
 * Targets:
 * - Desktop Chrome (primary)
 * - Desktop Firefox
 * - Mobile Chrome (Galaxy S9+ viewport)
 *
 * Flows covered:
 * - Public consumer flow (paste evidence → scan → verdict)
 * - Investigation dashboard (analyst role)
 * - Evidence upload
 * - Error/PARTIAL states
 */

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // Serial to avoid race on shared backend state
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'Desktop Firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'Mobile Chrome (Galaxy S9+)',
      use: { ...devices['Galaxy S9+'] },
    },
  ],
  /* Dev server — disable in CI where a real server is running */
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        cwd: './apps/web',
      },
});
