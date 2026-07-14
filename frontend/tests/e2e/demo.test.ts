import { expect, test } from '@playwright/test';

test('unauthenticated users are redirected to login', async ({ page }) => {
	await page.goto('/');
	await expect(page).toHaveURL(/\/login/);
	await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible();
});

test('manual refresh becomes visible and failed activity can be retried', async ({
	page,
	context
}) => {
	await context.addCookies([
		{
			name: 'cyt_access_token',
			value: 'e2e-access',
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);

	await page.goto('/channels/UC_portfolio');
	await page.getByRole('button', { name: /refresh/i }).click();
	await expect(page.getByText('succeeded', { exact: true })).toBeVisible({ timeout: 15_000 });

	await page.goto('/settings');
	await expect(page.getByRole('heading', { name: 'Sync Activity' })).toBeVisible();
	await expect(page.getByText('The channel feed is temporarily unavailable.')).toBeVisible();
	await page.getByRole('button', { name: 'Retry' }).click();
	await expect(page.getByRole('table').getByText('queued', { exact: true })).toBeVisible();
});
