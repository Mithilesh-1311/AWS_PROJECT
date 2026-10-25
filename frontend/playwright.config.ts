import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', timeout: 60000, workers: 1, retries: 0,
  use: { baseURL: process.env.EOG_TEST_URL || 'http://127.0.0.1:5173', viewport: { width: 1440, height: 900 }, trace: 'retain-on-failure' },
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
});
