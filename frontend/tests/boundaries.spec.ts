import { test, expect } from '@playwright/test';

test('empty registry and unavailable dataset retain actionable navigation', async ({ page }) => {
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/models') return route.fulfill({ json: { models: [], active_model_id: null } });
    if (path === '/api/ready') return route.fulfill({ json: { dataset: false, model: false, worker: false, storage: true, version: 'test', active_model_id: null } });
    return route.fulfill({ status: 503, json: { detail: 'Dataset unavailable; configure EOG_DATASET_ROOT' } });
  });
  await page.goto('/predictions');
  await expect(page.getByRole('button', { name: 'Predict direction' })).toBeDisabled();
  await expect(page.locator('main')).toContainText('No compatible model');
  await expect(page.getByRole('alert').first()).toContainText('Dataset unavailable');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('dialog').getByRole('link', { name: 'Methodology', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Methodology', exact: true })).toBeVisible();
  await expect(page.getByRole('dialog')).not.toBeVisible();
});

for (const classes of [4, 36]) {
  test(`historical ${classes}-class reports use their own class names on mobile`, async ({ page }) => {
    const names = Array.from({ length: classes }, (_, i) => `Class_${i}`);
    await page.route('**/api/v1/experiments', route => route.fulfill({ json: { experiments: [] } }));
    await page.route('**/api/experiments/latest/results', route => route.fulfill({ json: {
      experiment_id: 'fixture', model_name: 'logistic_regression', n_classes: classes, class_names: names,
      alignment: 'onset', split_method: 'fixture_holdout', timestamp: '2026-10-26T00:00:00Z',
      subjects_train: ['S1'], subjects_test: ['S2'], notes: 'Explicit browser test fixture',
      window_results: [{ window_ms: 100, effective_ms: 101.5625, n_samples: 26, n_train: 100, n_test: 100,
        accuracy: .5, macro_f1: .5, per_class_precision: names.map(() => .5), per_class_recall: names.map(() => .5),
        per_class_f1: names.map(() => .5), confusion_matrix: names.map((_, i) => names.map((_, j) => Number(i === j))) }],
    } }));
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/experiments');
    await page.getByRole('button', { name: 'Show legacy retrospective reports' }).click();
    await expect(page.getByRole('cell', { name: `Class_${classes - 1}`, exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  });
}
