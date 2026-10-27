import { test, expect } from '@playwright/test';

test('dashboard percentages follow the selected saved result', async ({ page }) => {
  const result = (window_ms: number, accuracy: number, macro_f1: number) => ({
    model_name: 'logistic_regression', window_ms, n_samples: Math.ceil(window_ms * .256),
    metrics: { accuracy, balanced_accuracy: accuracy, macro_f1 }, folds: [], n_predictions: 100,
    coverage: 1, source_test_trials: 100,
  });
  const report = { experiment_id: 'fixture', status: 'complete', timestamp: '2026-10-27T00:00:00Z',
    config: { subjects: ['S1'], smoke: false, models: ['logistic_regression'], windows: [100, 400], evaluation: 'loso' },
    dataset: { fingerprint: 'fixture', files: {} }, class_names: [],
    results: [result(100, .778393, .779398), result(400, .88515, .884124)] };
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/experiments') return route.fulfill({ json: { experiments: [report] } });
    if (path === '/api/v1/experiments/fixture') return route.fulfill({ json: report });
    return route.fulfill({ status: 503, json: { detail: 'Unavailable in this fixture' } });
  });
  await page.goto('/');
  const f1 = page.locator('.metric-strip a').filter({ hasText: 'macro F1' });
  await expect(f1).toContainText('77.94%');
  await page.getByLabel('Dashboard result').selectOption('logistic_regression:400');
  await expect(f1).toContainText('88.41%');
  await expect(f1).toContainText('400 ms');
  await page.reload();
  await expect(f1).toContainText('88.41%');
});

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
