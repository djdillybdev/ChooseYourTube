import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function expectNoBlockingAxeViolations(
	page: import('@playwright/test').Page,
	includeColorContrast = false
) {
	let scan = new AxeBuilder({ page }).withTags([
		'wcag2a',
		'wcag2aa',
		'wcag21a',
		'wcag21aa',
		'wcag22aa'
	]);
	if (!includeColorContrast) scan = scan.disableRules(['color-contrast']);
	const results = await scan.analyze();
	const blocking = results.violations.filter(
		(violation) => violation.impact === 'serious' || violation.impact === 'critical'
	);
	expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
}

async function authenticate(context: import('@playwright/test').BrowserContext) {
	await context.addCookies([
		{
			name: 'cyt_access_token',
			value: 'e2e-access',
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);
}

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

test('a channel can be added and browsed', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');

	await page.getByRole('button', { name: 'Add Channel', exact: true }).click();
	await page.getByLabel('Channel Handle or URL').fill('@added');
	await page.getByRole('dialog').getByRole('button', { name: 'Add Channel', exact: true }).click();

	const channelLink = page.getByRole('link', { name: 'Added Channel', exact: true });
	await expect(channelLink).toBeVisible();
	await channelLink.click();
	await expect(page).toHaveURL(/\/channels\/UC_added_channel/);
	await expect(page.getByRole('heading', { name: 'Added Channel', exact: true })).toBeVisible();
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
	await page.getByRole('button', { name: 'Delete' }).click();
	const confirmation = page.getByRole('dialog', { name: 'Delete tag?' });
	await expect(confirmation).toBeVisible();
	await confirmation.getByRole('button', { name: 'Delete tag' }).click();
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

test('application shell remains usable at phone, tablet, and desktop widths', async ({
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

	for (const width of [375, 768, 1280]) {
		await page.setViewportSize({ width, height: 720 });
		await page.goto('/inbox');
		const overflows = await page.evaluate(
			() => document.documentElement.scrollWidth > document.documentElement.clientWidth
		);
		expect(overflows).toBe(false);
	}

	await page.setViewportSize({ width: 375, height: 720 });
	await page.getByRole('button', { name: 'Open navigation' }).click();
	await expect(page.getByLabel('Primary navigation')).toBeVisible();
	await page.keyboard.press('Escape');
	await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused();
});

test('principal pages have no serious or critical axe violations', async ({ page, context }) => {
	await page.goto('/login');
	await expectNoBlockingAxeViolations(page, true);

	await authenticate(context);
	for (const path of [
		'/inbox',
		'/channels/UC_portfolio',
		'/watch-later',
		'/player',
		'/settings/imports',
		'/settings'
	]) {
		await page.goto(path);
		await expectNoBlockingAxeViolations(page);
	}
});
