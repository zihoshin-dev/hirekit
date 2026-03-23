import { expect, test } from '@playwright/test';

test('demo shows verdict-first war room summary', async ({ page }) => {
  await page.goto('/demo.html');
  await page.fill('#companySearch', '카카오');
  await page.locator('.company-card', { hasText: '카카오' }).first().click({ force: true });

  await expect(page.locator('#dpHeroVerdict')).toBeVisible();
  await expect(page.locator('#dpHeroActions')).toContainText('지원');
  await expect(page.locator('#dpEvidenceSummary')).toBeVisible();
  await expect(page.locator('#dpScanSummary')).toContainText('소스');
});

test('demo warns when trust coverage is incomplete', async ({ page }) => {
  await page.goto('/demo.html');
  await page.fill('#companySearch', '딥마인드코리아');
  await page.locator('.company-card', { hasText: '딥마인드코리아' }).first().click({ force: true });

  await expect(page.locator('#dpWarRoomWarning')).toBeVisible();
  await expect(page.locator('#dpWarRoomWarning')).toContainText('검증 신호');
});
