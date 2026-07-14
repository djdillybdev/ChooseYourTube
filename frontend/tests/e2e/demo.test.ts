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

	await page.goto('/settings/sync');
	await expect(page.getByRole('heading', { name: 'Sync Activity' })).toBeVisible();
	await expect(page.getByText('The channel feed is temporarily unavailable.')).toBeVisible();
	await page.getByRole('button', { name: 'Retry' }).click();
	await expect(page.getByRole('table').getByText('queued', { exact: true })).toBeVisible();
});

test('video can be saved to and removed from Watch Later', async ({ page, context }) => {
	await context.addCookies([
		{
			name: 'cyt_access_token',
			value: 'e2e-access',
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);

	await page.goto('/inbox');
	await page.getByRole('button', { name: 'Save to Watch Later', exact: true }).click();
	await expect(
		page.getByRole('button', { name: 'Remove from Watch Later', exact: true })
	).toBeVisible();
	await page.goto('/watch-later');
	await expect(page.getByText('Phase 3 portfolio video')).toBeVisible();
	await page.getByRole('button', { name: 'Remove' }).click();
	await expect(page.getByRole('heading', { name: 'Nothing saved yet' })).toBeVisible();
});

test('tags can be created, renamed, and deleted in organization settings', async ({
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

	await page.goto('/settings');
	await page.getByLabel('Tag name').fill(' Portfolio ');
	await page.getByRole('button', { name: 'Create tag' }).click();
	await expect(page.getByText('portfolio', { exact: true })).toBeVisible();
	await page.getByRole('button', { name: 'Rename' }).click();
	await page.locator('input.input-sm').fill('Engineering');
	await page.getByRole('button', { name: 'Save' }).click();
	await expect(page.getByText('engineering', { exact: true })).toBeVisible();
	page.on('dialog', (dialog) => dialog.accept());
	await page.getByRole('button', { name: 'Delete' }).click();
	await expect(page.getByText(/No tags yet/)).toBeVisible();
});

test('Takeout CSV can be reviewed and committed as a durable import', async ({ page, context }) => {
	await context.addCookies([
		{
			name: 'cyt_access_token',
			value: 'e2e-access',
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);

	await page.goto('/settings/imports');
	await page.getByLabel('Choose CSV').setInputFiles({
		name: 'subscriptions.csv',
		mimeType: 'text/csv',
		buffer: Buffer.from(
			'Channel Id,Channel Url,Channel Title\nUC_imported_portfolio1,,Imported Portfolio Channel'
		)
	});
	await expect(page.getByRole('heading', { name: 'Review subscriptions' })).toBeVisible();
	await page.getByRole('checkbox', { name: /Select Imported Portfolio Channel/ }).check();
	await page.getByRole('tab', { name: /Selected/ }).click();
	await expect(page.getByText('Imported Portfolio Channel')).toBeVisible();
	await page.getByRole('button', { name: 'Import 1 channels' }).click();
	await expect(page.getByText('succeeded', { exact: true })).toBeVisible({ timeout: 15_000 });
});
