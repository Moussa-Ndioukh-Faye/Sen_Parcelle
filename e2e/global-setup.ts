import { chromium, FullConfig } from '@playwright/test';
import { ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_STATE } from './helpers';

/** Connexion admin unique, réutilisée par les tests (limite de 5 connexions/minute). */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const { baseURL, launchOptions } = config.projects[0].use;
  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ baseURL });
  await page.goto('/auth');
  await page.fill('input[type="email"]', ADMIN_EMAIL);
  await page.fill('input[type="password"]', ADMIN_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/dashboard/);
  await page.context().storageState({ path: ADMIN_STATE });
  await browser.close();
}
