import { test, expect } from '@playwright/test';

test('remote sign-in, authenticated exports, reload and sign-out', async ({ page }) => {
  test.skip(!process.env.EOG_TEST_REMOTE_API, 'Run against Vite configured with an external VITE_API_BASE');
  const token = 'a'.repeat(64);
  const report = {
    experiment_id: 'fixture', status: 'complete', timestamp: '2026-10-27T00:00:00Z',
    config: { subjects: ['S1'], models: ['logistic_regression'], windows: [100], evaluation: 'loso', smoke: false, selection_policy: 'fixture' },
    dataset: { fingerprint: 'fixture', files: {} }, config_hash: 'fixture', class_names: [], results: [],
  };
  await page.route('https://eog-api.example/api/**', async route => {
    const request = route.request();
    if (request.headers().authorization !== `Bearer ${token}`) {
      return route.fulfill({ status: 403, json: { detail: 'Authenticated access required' } });
    }
    const url = new URL(request.url());
    if (url.pathname.endsWith('/export')) return route.fulfill({ body: JSON.stringify(report), contentType: 'application/json' });
    if (url.pathname.endsWith('/models')) return route.fulfill({ json: { models: [], active_model_id: null } });
    if (url.pathname.endsWith('/ready')) return route.fulfill({ json: { dataset: false, model: false, worker: true, storage: true, version: 'test' } });
    if (url.pathname.endsWith('/experiments')) return route.fulfill({ json: { experiments: [report] } });
    return route.fulfill({ json: report });
  });
  await page.goto('/reports');
  await expect(page.getByRole('heading', { name: 'Sign in to EOG Intent' })).toBeVisible();
  await page.getByLabel('Access token').fill('b'.repeat(64));
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Authenticated access required');
  await page.getByLabel('Access token').fill(token);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Reports & provenance' })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export JSON' }).click();
  expect((await download).suggestedFilename()).toBe('fixture.json');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Reports & provenance' })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByLabel('Access token')).toBeEmpty();
  expect(await page.evaluate(() => sessionStorage.getItem('eog-access-token'))).toBeNull();
});
