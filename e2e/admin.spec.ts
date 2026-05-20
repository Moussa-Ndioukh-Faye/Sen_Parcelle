import { test, expect } from '@playwright/test';

test.describe('Blockchain Admin', () => {
  test('affiche le titre de la page blockchain', async ({ page }) => {
    await page.goto('/blockchain');
    await expect(page.locator('h1')).toContainText('Blockchain');
  });

  test('affiche le vérificateur de certificat', async ({ page }) => {
    await page.goto('/blockchain');
    await expect(page.locator('input')).toBeVisible();
    await expect(page.locator('button')).toContainText('Vérifier');
  });
});

test.describe('Parcelles', () => {
  test('affiche la liste des parcelles', async ({ page }) => {
    await page.goto('/parcelles');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('affiche les boutons de filtre', async ({ page }) => {
    await page.goto('/parcelles');
    const buttons = page.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });
});
