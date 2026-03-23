import { expect, test } from '@playwright/test';

test('tools page restores local-only jd and resume inputs', async ({ page }) => {
  await page.goto('/tools.html');
  await page.fill('#jd-url', 'https://example.com/jd');
  await page.fill('#jd-text', 'Python, Kubernetes, 5년 이상 경력');
  await page.fill('#resume-text', '백엔드 엔지니어 경험과 프로젝트 요약');
  await page.reload();

  await expect(page.locator('#jd-url')).toHaveValue('https://example.com/jd');
  await expect(page.locator('#jd-text')).toHaveValue('Python, Kubernetes, 5년 이상 경력');
  await expect(page.locator('#resume-text')).toHaveValue('백엔드 엔지니어 경험과 프로젝트 요약');
});

test('tools page explains local-only storage and war room handoff', async ({ page }) => {
  await page.goto('/tools.html');
  await expect(page.getByText('브라우저 로컬 저장소')).toBeVisible();
  await expect(page.getByRole('link', { name: '데모 War Room' })).toBeVisible();
});
