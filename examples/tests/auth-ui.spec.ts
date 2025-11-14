
// Example Playwright test (template)
import { test, expect } from '@playwright/test';

test('Auth UI example', async ({ page }) => {
  await page.goto(process.env.APP_URL || 'http://localhost:3000');
  await expect(page.locator('input[name="phone"]')).toBeVisible();
  const btn = page.locator('button#get-code');
  await expect(btn).toBeDisabled();
  await page.locator('input[name="phone"]').fill('7999888776');
  await expect(btn).toBeEnabled();
});
