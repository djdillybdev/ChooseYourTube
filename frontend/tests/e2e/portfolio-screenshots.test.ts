import { expect, test } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const screenshotDir = fileURLToPath(new URL('../../../docs/screenshots/', import.meta.url));
const mediaDir = fileURLToPath(new URL('../../../.portfolio-artifacts/', import.meta.url));
const liveBaseUrl = process.env.PORTFOLIO_BASE_URL?.replace(/\/$/, '');

function target(path: string): string {
	return liveBaseUrl ? `${liveBaseUrl}${path}` : path;
}

async function authenticate(
	page: import('@playwright/test').Page,
	context: import('@playwright/test').BrowserContext
) {
	await page.goto(target('/login'));
	if (liveBaseUrl) {
		await page.getByRole('button', { name: 'Try the demo' }).click();
		await expect(page.getByRole('heading', { name: 'Inbox' })).toBeVisible({ timeout: 30_000 });
		return;
	}

	await context.addCookies([
		{
			name: 'cyt_access_token',
			value: 'portfolio-screenshot-access',
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);
	await page.goto(target('/inbox'));
}

async function settle(page: import('@playwright/test').Page) {
	await page.waitForLoadState('networkidle');
	await page.locator('img').evaluateAll(async (images) => {
		await Promise.all(
			images.map((image) => {
				if ((image as HTMLImageElement).complete) return Promise.resolve();
				return new Promise<void>((resolve) => {
					image.addEventListener('load', () => resolve(), { once: true });
					image.addEventListener('error', () => resolve(), { once: true });
				});
			})
		);
	});
}

async function showCaption(page: import('@playwright/test').Page, message: string) {
	await page.evaluate((text) => {
		let caption = document.querySelector<HTMLElement>('#portfolio-video-caption');
		if (!caption) {
			caption = document.createElement('div');
			caption.id = 'portfolio-video-caption';
			Object.assign(caption.style, {
				position: 'fixed',
				left: '10%',
				right: '10%',
				bottom: '32px',
				zIndex: '2147483647',
				padding: '18px 24px',
				borderRadius: '14px',
				background: 'rgba(15, 23, 42, .92)',
				color: '#fff',
				font: '600 26px/1.35 system-ui, sans-serif',
				textAlign: 'center',
				boxShadow: '0 12px 30px rgba(15, 23, 42, .3)'
			});
			document.body.append(caption);
		}
		caption.textContent = text;
	}, message);
}

test('capture portfolio views', async ({ page, context }) => {
	test.skip(!process.env.CAPTURE_PORTFOLIO, 'Set CAPTURE_PORTFOLIO=1 to update images.');
	mkdirSync(screenshotDir, { recursive: true });

	await page.setViewportSize({ width: 1440, height: 900 });
	await page.goto(target('/login'));
	await settle(page);
	await page.screenshot({ path: `${screenshotDir}/login-desktop.png`, fullPage: true });

	await authenticate(page, context);
	await settle(page);
	await page.screenshot({ path: `${screenshotDir}/inbox-desktop.png`, fullPage: true });

	await page.getByText('Filters', { exact: true }).click();
	await page.screenshot({ path: `${screenshotDir}/filters-desktop.png`, fullPage: true });

	await page.goto(target('/settings'));
	await settle(page);
	await page.screenshot({ path: `${screenshotDir}/organization-desktop.png`, fullPage: true });

	await page.goto(target('/watch-later'));
	await settle(page);
	await page.screenshot({ path: `${screenshotDir}/watch-later-desktop.png`, fullPage: true });

	await page.goto(target('/settings/imports'));
	await settle(page);
	await page.screenshot({ path: `${screenshotDir}/imports-desktop.png`, fullPage: true });

	await page.goto(target('/settings/sync'));
	await settle(page);
	await page.screenshot({ path: `${screenshotDir}/sync-desktop.png`, fullPage: true });

	await page.setViewportSize({ width: 375, height: 812 });
	await page.goto(target('/inbox'));
	await page.getByRole('button', { name: 'Open navigation' }).click();
	await page.waitForTimeout(350);
	await page.screenshot({ path: `${screenshotDir}/mobile-navigation.png`, fullPage: true });
});

test('record portfolio walkthrough', async ({ browser }) => {
	test.skip(
		!process.env.CAPTURE_PORTFOLIO_VIDEO || !liveBaseUrl,
		'Set CAPTURE_PORTFOLIO_VIDEO=1 and PORTFOLIO_BASE_URL to record the live demo.'
	);
	test.setTimeout(240_000);
	mkdirSync(mediaDir, { recursive: true });

	const context = await browser.newContext({
		viewport: { width: 1920, height: 1080 },
		recordVideo: { dir: mediaDir, size: { width: 1920, height: 1080 } }
	});
	const page = await context.newPage();

	await page.goto(target('/login'));
	await showCaption(
		page,
		'ChooseYourTube is a self-hostable YouTube inbox for intentional viewing—without recommendations, comments or trending feeds.'
	);
	await page.waitForTimeout(4_000);
	await page.getByRole('button', { name: 'Try the demo' }).click();
	await expect(page.getByRole('heading', { name: 'Inbox' })).toBeVisible({ timeout: 30_000 });
	await settle(page);
	await showCaption(
		page,
		'Users follow only the channels they choose. PostgreSQL keeps a durable personal library, so browsing does not depend on a live YouTube request.'
	);
	await page.waitForTimeout(10_000);

	await page.getByText('Filters', { exact: true }).click();
	await showCaption(
		page,
		'PostgreSQL full-text search combines with URL-backed channel, tag, watched, date and duration filters.'
	);
	await page.waitForTimeout(12_000);
	await page.getByRole('button', { name: 'Reset filters' }).click();
	await page.getByText('Filters', { exact: true }).click();
	await page.waitForTimeout(2_000);

	const watchedButton = page.getByRole('button', { name: /Mark as (?:un)?watched/ }).first();
	const watchedLabel = await watchedButton.getAttribute('aria-label');
	const restoreWatchedLabel =
		watchedLabel === 'Mark as watched' ? 'Mark as unwatched' : 'Mark as watched';
	await watchedButton.click();
	await showCaption(
		page,
		'Safe interactions remain owner-scoped. Watch Later is an application-owned system playlist with ordered membership.'
	);
	await page.waitForTimeout(4_000);

	const saveButton = page.getByRole('button', { name: 'Save to Watch Later' }).first();
	let addedVideoTitle: string | null = null;
	if (await saveButton.count()) {
		addedVideoTitle = await saveButton
			.locator('xpath=ancestor::article')
			.locator('h3')
			.textContent();
		await saveButton.click();
		await page.waitForTimeout(4_000);
	}

	await page
		.getByRole('button', { name: /^Play / })
		.first()
		.click();
	await expect(page).toHaveURL(/\/player/);
	await showCaption(
		page,
		'The player preserves queue order and exposes playback failures instead of silently skipping content.'
	);
	await page.waitForTimeout(12_000);

	const categoryLink = page.locator('a[href^="/categories/"]').first();
	if (await categoryLink.count()) {
		await categoryLink.click();
		await settle(page);
		await page.waitForTimeout(10_000);
	}

	await page.goto(target('/watch-later'));
	await settle(page);
	await showCaption(page, 'Watch Later and custom playlists keep playback explicit and ordered.');
	await page.waitForTimeout(8_000);

	await page.goto(target('/playlists'));
	await settle(page);
	await showCaption(
		page,
		'Playlists are durable, user-owned collections rather than recommendation feeds.'
	);
	await page.waitForTimeout(8_000);

	await page.goto(target('/settings/imports'));
	await settle(page);
	await showCaption(
		page,
		'Full mode previews OAuth or Takeout imports, deduplicates candidates and discards Google tokens after discovery.'
	);
	await page.waitForTimeout(12_000);

	await page.goto(target('/settings/sync'));
	await settle(page);
	await showCaption(
		page,
		'Every refresh records durable progress, safe errors and bounded retry state—even after queue results disappear.'
	);
	await page.waitForTimeout(12_000);

	await page.goto(target('/settings'));
	await settle(page);
	await showCaption(
		page,
		'Docker runs FastAPI, PostgreSQL, Redis and arq workers. This Vercel demo shares the code and migrations but stays RSS-only to protect quota.'
	);
	await page.waitForTimeout(8_000);

	await page.goto(target('/inbox'));
	await settle(page);
	await page.getByRole('button', { name: 'All', exact: true }).click();
	if (restoreWatchedLabel) {
		await page.getByRole('button', { name: restoreWatchedLabel }).first().click();
	}
	if (addedVideoTitle) {
		const article = page.getByRole('article', { name: addedVideoTitle });
		await article.getByRole('button', { name: 'Remove from Watch Later' }).click();
	}
	await showCaption(
		page,
		'Try the live demo or follow the complete self-hosting guide at github.com/djdillybdev/ChooseYourTube.'
	);
	await page.waitForTimeout(4_000);

	const video = page.video();
	await context.close();
	if (!video) throw new Error('Playwright did not create a portfolio video.');
	await video.saveAs(`${mediaDir}/chooseyourtube-demo-v1.0.0.webm`);
});
