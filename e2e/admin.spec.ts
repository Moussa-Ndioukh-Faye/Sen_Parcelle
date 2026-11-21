import { test, expect } from '@playwright/test';
import { ADMIN_STATE } from './helpers';

test.use({ storageState: ADMIN_STATE });

test.describe('Blockchain Admin', () => {
  test('affiche le titre de la page blockchain', async ({ page }) => {
    await page.goto('/blockchain');
    await expect(page.locator('main h1')).toContainText('Blockchain');
  });

  test('affiche le vérificateur de certificat', async ({ page }) => {
    await page.goto('/blockchain');
    await expect(page.locator('main input')).toBeVisible();
    await expect(page.locator('main button', { hasText: 'Vérifier' })).toBeVisible();
  });
});

test.describe('Parcelles', () => {
  test('affiche la page des parcelles', async ({ page }) => {
    await page.goto('/parcelles');
    await expect(page.locator('main h2')).toContainText('Parcelles');
  });

  test('affiche la grille des parcelles', async ({ page }) => {
    await page.goto('/parcelles');
    await expect(page.locator('main .parcels-grid')).toBeAttached();
  });
});
