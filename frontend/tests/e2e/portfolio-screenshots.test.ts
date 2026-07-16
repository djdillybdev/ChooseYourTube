import { expect, test } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

test.skip(
	!process.env.CAPTURE_PORTFOLIO,
	'Run with CAPTURE_PORTFOLIO=1 to update portfolio images.'
);

const screenshotDir = fileURLToPath(new URL('../../../docs/screenshots/', import.meta.url));

test('capture portfolio views', async ({ page, context }) => {
	mkdirSync(screenshotDir, { recursive: true });

	await page.setViewportSize({ width: 1440, height: 900 });
	await page.goto('/login');
	await page.screenshot({ path: `${screenshotDir}/login-desktop.png`, fullPage: true });

	await context.addCookies([
		{
			name: 'cyt_access_token',
			value: 'portfolio-screenshot-access',
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);
	await page.goto('/inbox');
	await expect(page.getByRole('heading', { name: 'Inbox' })).toBeVisible();
	await page.screenshot({ path: `${screenshotDir}/inbox-desktop.png`, fullPage: true });

	await page.getByText('Filters', { exact: true }).click();
	await page.screenshot({ path: `${screenshotDir}/filters-desktop.png`, fullPage: true });

	await page.goto('/channels/UC_portfolio');
	await page.screenshot({ path: `${screenshotDir}/channel-desktop.png`, fullPage: true });

	await page.goto('/inbox');
	await page.getByRole('button', { name: 'Add Channel', exact: true }).click();
	await page.getByLabel('Channel Handle or URL').fill('@added');
	await page.getByRole('dialog').getByRole('button', { name: 'Add Channel', exact: true }).click();
	await expect(page.getByRole('heading', { name: 'Channel followed' })).toBeVisible();
	await page.screenshot({ path: `${screenshotDir}/follow-channel-feedback.png`, fullPage: true });
	await page.getByRole('button', { name: 'Done' }).click();

	await page.getByRole('button', { name: 'Save to Watch Later', exact: true }).click();
	await page.goto('/watch-later');
	await page.screenshot({ path: `${screenshotDir}/watch-later-desktop.png`, fullPage: true });

	await page.setViewportSize({ width: 375, height: 812 });
	await page.goto('/inbox');
	await page.getByRole('button', { name: 'Open navigation' }).click();
	await page.waitForTimeout(350);
	await page.screenshot({ path: `${screenshotDir}/mobile-navigation.png`, fullPage: true });
});
