import { test, expect } from '@playwright/test';

test.describe('Login', () => {
  test('affiche le formulaire de connexion', async ({ page }) => {
    await page.goto('/auth');
    await expect(page.locator('h2')).toContainText('Connexion');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toContainText('Se connecter');
  });

  test('affiche une erreur avec des identifiants invalides', async ({ page }) => {
    await page.goto('/auth');
    await page.fill('input[type="email"]', 'wrong@test.sn');
    await page.fill('input[type="password"]', 'wrongpass');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1000);
    const errorEl = page.locator('.login-form__alert');
    await expect(errorEl).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test('redirige vers la connexion si non authentifié', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/auth/);
  });
});
