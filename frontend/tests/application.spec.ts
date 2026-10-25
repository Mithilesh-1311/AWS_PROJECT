import { test, expect } from '@playwright/test';
const routes = ['/', '/dataset', '/signal', '/early-window', '/predictions', '/replay', '/experiments', '/quality', '/methodology', '/reports'];

test('all routes render actual API data without runtime errors', async ({ page }) => {
  test.setTimeout(180000);
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  for (const route of routes) {
    await page.goto(route);
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('.loading-state, .skeleton')).toHaveCount(0, { timeout: 45000 });
    await expect(page.locator('main')).not.toBeEmpty();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  expect(errors).toEqual([]);
  await page.goto('/');
  await expect(page.locator('.metric-strip')).toContainText('4,032');
  await expect(page.locator('.loading-state, .skeleton')).toHaveCount(0);
  await page.screenshot({ path: 'test-results/overview-desktop.png', fullPage: true });
});

test('real prediction matches API provenance and survives trial selection', async ({ page, request }) => {
  const response = await request.post('http://127.0.0.1:8000/api/v1/predictions', { data: { subject_id: 'S1', trial_id: 0 } });
  const prediction = await response.json(); expect(prediction.state).toBe('predicted');
  await page.goto('/predictions?subject=S1&trial=0');
  await page.getByRole('button', { name: 'Predict direction' }).click();
  await expect(page.locator('.prediction-heading')).toHaveText(prediction.predicted_direction);
  await expect(page.locator('.prediction-result')).toContainText(prediction.model_id);
  await expect(page.locator('.prediction-result')).toContainText('26 / 101.56 / 97.66');
  await page.screenshot({ path: 'test-results/prediction-desktop.png', fullPage: true });
  await page.getByLabel('Trial index').fill('1');
  await expect(page.locator('.prediction-heading')).toHaveCount(0);
  await expect(page).toHaveURL(/trial=1/);
  await page.getByRole('button', { name: 'Predict direction' }).click();
  await expect(page.locator('.prediction-heading')).toBeVisible();
});

test('all dataset trials are selectable', async ({ page }) => {
  await page.goto('/dataset');
  await expect(page.locator('#trial option')).toHaveCount(288);
  await page.locator('#trial').selectOption('287');
  await expect(page).toHaveURL(/trial=287/);
  await expect(page.locator('.chart-container svg').first()).toBeVisible();
});

test('real recorded replay predicts, pauses, resets and disconnects', async ({ page }) => {
  await page.goto('/replay?subject=S1&trial=0');
  await page.getByLabel('Playback speed').selectOption('8');
  await page.getByRole('button', { name: 'Connect / restart' }).click();
  await expect(page.locator('.prediction-heading')).toBeVisible();
  await expect(page.locator('.evidence-strip')).toContainText('predicted');
  await page.getByRole('button', { name: 'Reset trial' }).click();
  await page.getByRole('button', { name: 'Disconnect', exact: true }).click();
  await expect(page.locator('.evidence-strip')).toContainText('disconnected');
  await page.getByLabel('Playback speed').selectOption('0.25');
  await page.getByRole('button', { name: 'Connect / restart' }).click();
  await page.getByRole('button', { name: 'Pause', exact: true }).click();
  await expect(page.locator('.evidence-strip')).toContainText('paused');
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await page.getByRole('button', { name: 'Disconnect', exact: true }).click();
});

test('real worker job completes and its report exports', async ({ page, request }) => {
  test.setTimeout(120000);
  await page.goto('/');
  const submission = page.waitForResponse(response => response.url().endsWith('/api/v1/jobs') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Run S1–S3 smoke job' }).click();
  const created = await (await submission).json();
  await expect.poll(async () => {
    const response = await request.get(`http://127.0.0.1:8000/api/v1/jobs/${created.id}`);
    return (await response.json()).state;
  }, { timeout: 100000, intervals: [2000] }).toBe('succeeded');
  const response = await request.get(`http://127.0.0.1:8000/api/v1/jobs/${created.id}`);
  const id = (await response.json()).result.experiment_id;
  await page.goto(`/reports?experiment=${id}`);
  await expect(page.locator('main')).toContainText('SMOKE');
  const exportResponse = await request.get(`http://127.0.0.1:8000/api/v1/experiments/${id}/export?format=csv`);
  expect(exportResponse.ok()).toBeTruthy(); expect(await exportResponse.text()).toContain('logistic_regression');
});

test('mobile routes, drawer focus and reduced motion', async ({ page }) => {
  test.setTimeout(180000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const route of routes) {
    await page.goto(route);
    await expect(page.locator('.loading-state, .skeleton')).toHaveCount(0, { timeout: 45000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  await page.goto('/');
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused();
  await expect(page.locator('.metric-strip')).toContainText('4,032');
  await expect(page.locator('.loading-state, .skeleton')).toHaveCount(0);
  await page.screenshot({ path: 'test-results/overview-mobile.png', fullPage: true });
});

test('request failures and missing model are actionable', async ({ page }) => {
  await page.route('**/api/v1/models', route => route.fulfill({ json: { models: [], active_model_id: null } }));
  await page.goto('/predictions');
  await expect(page.locator('main')).toContainText('No compatible model');
  await expect(page.getByRole('button', { name: 'Predict direction' })).toBeDisabled();
  await page.unrouteAll();
  await page.route('**/api/**', route => route.abort());
  await page.goto('/');
  await expect(page.locator('[role=alert]').first()).toBeVisible();
  await page.unrouteAll();
  await page.reload();
  await expect(page.locator('.metric-strip')).toContainText('4,032');
});
