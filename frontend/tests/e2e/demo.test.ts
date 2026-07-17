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

async function expectCursor(
	locator: import('@playwright/test').Locator,
	expected: 'auto' | 'pointer' | 'text' | 'grab' | 'grabbing' | 'not-allowed'
) {
	await expect
		.poll(() => locator.evaluate((element) => getComputedStyle(element).cursor))
		.toBe(expected);
}

test('unauthenticated users are redirected to login', async ({ page }) => {
	await page.goto('/');
	await expect(page).toHaveURL(/\/login/);
	await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible();
});

test('password login completes when JavaScript is disabled', async ({ browser }) => {
	const context = await browser.newContext({ javaScriptEnabled: false });
	const page = await context.newPage();
	await page.goto('/login?next=%2Finbox%3Fpage%3D2');
	await page.getByLabel('Email').fill('portfolio@example.com');
	await page.getByLabel('Password').fill('password');
	await page.getByRole('button', { name: 'Log in' }).click();

	await expect(page).toHaveURL(/\/inbox\?page=2/);
	await expect(page.getByRole('heading', { name: 'Inbox' })).toBeVisible();
	await context.close();
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
	await expect(page.getByText('Sync succeeded', { exact: true })).toBeVisible({ timeout: 15_000 });

	await page.goto('/settings/sync');
	await expect(page.getByRole('heading', { name: 'Sync Activity' })).toBeVisible();
	await expect(page.getByText('The channel feed is temporarily unavailable.')).toBeVisible();
	await page.getByRole('button', { name: 'Retry' }).click();
	await expect(page.getByRole('table').getByText('Sync queued', { exact: true })).toBeVisible();
});

test('logout protects browser Back history', async ({ page, context }) => {
	await page.goto('/login');
	await authenticate(context);
	await page.goto('/inbox');
	await page.getByRole('button', { name: 'Log out' }).click();
	await expect(page).toHaveURL(/\/login/);

	await page.goBack();
	await expect(page).toHaveURL(/\/login/);
	await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible();
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

test('video display preference persists across shared feeds', async ({ page, context }) => {
	await authenticate(context);
	await page.setViewportSize({ width: 1440, height: 900 });
	await page.goto('/inbox');

	await page.getByRole('button', { name: 'Grid view' }).click();
	await expect(page.getByRole('button', { name: 'Grid view' })).toHaveAttribute(
		'aria-pressed',
		'true'
	);
	await expect(page.getByTestId('video-items')).toHaveAttribute('data-display-mode', 'grid');
	await expect
		.poll(() =>
			page
				.getByTestId('video-items')
				.evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(' ').length)
		)
		.toBe(4);

	await page.reload();
	await expect(page.getByRole('button', { name: 'Grid view' })).toHaveAttribute(
		'aria-pressed',
		'true'
	);

	await page.goto('/channels/UC_portfolio');
	await expect(page.getByTestId('video-items')).toHaveAttribute('data-display-mode', 'grid');

	await page.getByRole('button', { name: 'Compact view' }).click();
	const videoCard = page.getByRole('article', { name: 'Phase 3 portfolio video' });
	await expect(videoCard).toHaveAttribute('data-display-mode', 'compact');
	await expect(videoCard.locator('img')).toHaveCount(0);
});

test('interactive elements use consistent semantic cursors', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');

	const videoCard = page.getByRole('article', { name: 'Phase 3 portfolio video' });
	await expectCursor(videoCard, 'auto');
	await expectCursor(
		videoCard.getByRole('button', { name: 'Play Phase 3 portfolio video' }).first(),
		'pointer'
	);
	await expectCursor(page.getByPlaceholder('Search unwatched videos...'), 'text');
	await expectCursor(page.getByRole('link', { name: 'Inbox' }), 'pointer');

	await page.getByText('Filters', { exact: true }).click();
	await expectCursor(page.getByText('Filters', { exact: true }), 'pointer');
	await expectCursor(page.getByLabel('Shorts'), 'pointer');

	await page.getByRole('button', { name: 'Save to Watch Later', exact: true }).click();
	await page.goto('/watch-later');
	const draggableVideo = page.locator('[draggable]:not([draggable="false"])');
	await expectCursor(draggableVideo, 'grab');
	await draggableVideo.hover();
	await page.mouse.down();
	await expectCursor(draggableVideo, 'grabbing');
	await page.mouse.up();

	await page.goto('/channels/UC_portfolio');
	await page.getByRole('button', { name: 'Edit channel' }).click();
	await expectCursor(page.getByRole('checkbox', { name: 'Favorite' }), 'pointer');
	await page.getByRole('button', { name: 'Cancel' }).click();

	await page.goto('/settings/imports');
	const disabledGoogleButton = page.getByRole('button', { name: 'Continue with Google' });
	await expect(disabledGoogleButton).toBeDisabled();
	await expectCursor(disabledGoogleButton, 'not-allowed');
	await expect(disabledGoogleButton).toHaveCSS('pointer-events', 'auto');
});

test('filters videos by duration and persists the range in the URL', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox?page=3');
	await expect(page.getByRole('article', { name: 'Phase 3 portfolio video' })).toBeVisible();

	await page.getByText('Filters', { exact: true }).click();
	const minimum = page.getByRole('slider', { name: 'Minimum duration' });
	await minimum.evaluate((element) => {
		const input = element as HTMLInputElement;
		input.value = '4';
		input.dispatchEvent(new Event('input', { bubbles: true }));
		input.dispatchEvent(new Event('change', { bubbles: true }));
	});

	await expect(page).toHaveURL(/page=1.*min_duration_minutes=4/);
	await expect(page.getByRole('article', { name: 'Phase 3 portfolio video' })).toHaveCount(0);

	await page.getByRole('button', { name: 'Reset filters' }).click();
	await expect(page).not.toHaveURL(/min_duration_minutes/);
	await expect(page.getByRole('article', { name: 'Phase 3 portfolio video' })).toBeVisible();
});

test('a channel can be favorited while videos cannot', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/channels/UC_portfolio');

	await page.getByRole('button', { name: 'Add Portfolio Channel to favorites' }).click();
	await page.getByRole('link', { name: 'Favorites' }).click();
	await expect(page.getByRole('heading', { name: 'Favorites' })).toBeVisible();
	await expect(page.getByRole('heading', { name: 'Portfolio Channel' })).toBeVisible();

	const videoCard = page.getByRole('article', { name: 'Phase 3 portfolio video' });
	await expect(videoCard.getByRole('button', { name: /favorites/i })).toHaveCount(0);

	await page.getByRole('button', { name: 'Remove Portfolio Channel from favorites' }).click();
	await expect(page.getByRole('heading', { name: 'No favorite channels' })).toBeVisible();
});

test('a channel can be added and browsed', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');

	await page.getByRole('button', { name: 'Add Channel', exact: true }).click();
	const channelInput = page.getByLabel('Channel Handle or URL');
	await expect(channelInput).toBeFocused();
	await channelInput.fill('@added');
	await page.getByRole('dialog').getByRole('button', { name: 'Add Channel', exact: true }).click();
	await expect(page.getByRole('heading', { name: 'Channel followed' })).toBeVisible();
	await expect(
		page.getByText(/video synchronization is queued|videos are synchronizing/)
	).toBeVisible();
	await page.getByRole('button', { name: 'Done' }).click();
	await page.getByRole('button', { name: 'Expand Uncategorized' }).click();

	const channelLink = page.getByRole('link', { name: 'Added Channel', exact: true });
	await expect(channelLink).toBeVisible();
	await channelLink.click();
	await expect(page).toHaveURL(/\/channels\/UC_added_channel/);
	await expect(page.getByRole('heading', { name: 'Added Channel', exact: true })).toBeVisible();
});

test('dialogs restore focus to their trigger after cancellation', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');

	const trigger = page.getByRole('button', { name: 'Add Channel', exact: true });
	await trigger.click();
	await expect(page.getByLabel('Channel Handle or URL')).toBeFocused();
	await page.getByRole('dialog').getByRole('button', { name: 'Cancel' }).click();
	await expect(trigger).toBeFocused();
});

test('filters and video actions close when clicking outside', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');
	const pageHeading = page.getByRole('heading', { name: 'Inbox' });

	await page.getByText('Filters', { exact: true }).click();
	await expect(page.getByLabel('Length')).toBeVisible();
	await pageHeading.click();
	await expect(page.getByLabel('Length')).toBeHidden();

	const videoCard = page.getByRole('article', { name: 'Phase 3 portfolio video' });
	await videoCard.getByText('More', { exact: true }).click();
	await expect(videoCard.getByRole('button', { name: 'Save to playlist' })).toBeVisible();
	await pageHeading.click();
	await expect(videoCard.getByRole('button', { name: 'Save to playlist' })).toBeHidden();
});

test('route progress is visible only during client navigation', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');
	const progress = page.getByRole('progressbar', { name: 'Loading page' });
	await expect(progress).toHaveCount(0);

	let releaseNavigation!: () => void;
	const navigationGate = new Promise<void>((resolve) => (releaseNavigation = resolve));
	await page.route('**/api/backend/playlists/**', async (route) => {
		await navigationGate;
		await route.continue();
	});

	const playlistRequest = page.waitForRequest(
		(request) => new URL(request.url()).pathname === '/api/backend/playlists/'
	);
	const navigation = page.getByRole('link', { name: 'Playlists' }).click();
	await playlistRequest;
	await expect(progress).toBeVisible();
	releaseNavigation();
	await navigation;

	await expect(page.getByRole('heading', { name: 'Playlists' })).toBeVisible();
	await expect(progress).toHaveCount(0);
});

test('categories can be created, populated, renamed, and deleted', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');

	await page.getByRole('button', { name: 'New Category' }).click();
	await page.getByLabel('Category Name').fill('Games');
	await page.getByRole('radio', { name: 'Gaming' }).click();
	await page.getByRole('dialog').getByRole('button', { name: 'Create Category' }).click();
	const gamesLink = page.getByRole('link', { name: 'Games' });
	await expect(gamesLink.locator('svg.lucide-gamepad-2')).toBeVisible();
	await gamesLink.click();
	await expect(page.getByRole('heading', { name: 'Games' })).toBeVisible();

	await page.getByRole('button', { name: 'Edit category' }).click();
	const dialog = page.getByRole('dialog');
	await dialog.getByLabel('Category Name').fill('Gaming');
	await dialog.getByRole('radio', { name: 'Star' }).click();
	await dialog.getByLabel('Portfolio Channel').check();
	await dialog.getByRole('button', { name: 'Save' }).click();
	await expect(page.getByRole('heading', { name: 'Gaming' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'Gaming' }).locator('svg.lucide-star')).toBeVisible();
	await expect(
		page
			.locator('main')
			.getByRole('link', { name: /Portfolio Channel/ })
			.first()
	).toBeVisible();

	await page.getByRole('button', { name: 'Edit category' }).click();
	await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click();
	const confirmation = page.getByRole('dialog', { name: 'Delete category?' });
	await confirmation.getByRole('button', { name: 'Delete category' }).click();
	await expect(page).toHaveURL(/\/inbox$/);
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

	for (const width of [320, 375, 768, 1280, 1440]) {
		await page.setViewportSize({ width, height: 720 });
		await page.goto('/inbox');
		const overflows = await page.evaluate(
			() => document.documentElement.scrollWidth > document.documentElement.clientWidth
		);
		expect(overflows).toBe(false);
	}

	await page.setViewportSize({ width: 320, height: 720 });
	await page.goto('/inbox');
	await expect(
		page.getByRole('button', { name: 'Play Phase 3 portfolio video' }).first()
	).toBeVisible();
	await page.getByText('Filters', { exact: true }).click();
	const filterBounds = await page.locator('.dropdown-content').first().boundingBox();
	expect(filterBounds).not.toBeNull();
	expect(filterBounds?.x ?? -1).toBeGreaterThanOrEqual(0);
	expect((filterBounds?.x ?? 0) + (filterBounds?.width ?? 0)).toBeLessThanOrEqual(320);

	await page.setViewportSize({ width: 375, height: 720 });
	await page.getByRole('button', { name: 'Open navigation' }).click();
	await expect(page.getByLabel('Primary navigation')).toBeVisible();
	await page.keyboard.press('Escape');
	await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused();
});

test('sidebar keeps long channel names compact without horizontal scrolling', async ({
	page,
	context
}) => {
	await authenticate(context);
	const longChannelName =
		'Portfolio Channel With A Deliberately Long Name That Must Stay On One Line';

	for (const width of [375, 1280]) {
		await page.setViewportSize({ width, height: 720 });
		await page.goto('/inbox');
		if (width < 768) await page.getByRole('button', { name: 'Open navigation' }).click();

		const sidebar = page.getByLabel('Primary navigation');
		await expect(sidebar).toBeVisible();
		const toggle = sidebar.getByRole('button', { name: /(?:Expand|Collapse) Uncategorized/ });
		if ((await toggle.getAttribute('aria-label'))?.startsWith('Expand')) await toggle.click();

		const channelTitle = sidebar.getByTitle('Portfolio Channel');
		await channelTitle.evaluate((element, name) => {
			element.textContent = name;
			element.setAttribute('title', name);
		}, longChannelName);
		const categoryTitle = sidebar.getByTitle('Uncategorized');
		const navigation = page.getByRole('navigation', { name: 'Primary' });

		await expect
			.poll(() => navigation.evaluate((element) => element.scrollWidth <= element.clientWidth))
			.toBe(true);
		const titleStyles = await channelTitle.evaluate((element) => {
			const styles = getComputedStyle(element);
			return {
				overflow: styles.overflow,
				textOverflow: styles.textOverflow,
				whiteSpace: styles.whiteSpace,
				isTruncated: element.scrollWidth > element.clientWidth
			};
		});
		expect(titleStyles).toEqual({
			overflow: 'hidden',
			textOverflow: 'ellipsis',
			whiteSpace: 'nowrap',
			isTruncated: true
		});

		const categoryBounds = await categoryTitle.boundingBox();
		const channelBounds = await channelTitle.boundingBox();
		expect(categoryBounds).not.toBeNull();
		expect(channelBounds).not.toBeNull();
		expect(categoryBounds?.x, `channel title x: ${channelBounds?.x}`).toBe(channelBounds?.x);

		const sidebarBounds = await sidebar.boundingBox();
		const inboxBounds = await sidebar.getByRole('link', { name: 'Inbox' }).boundingBox();
		expect((inboxBounds?.x ?? 0) + (inboxBounds?.width ?? 0)).toBeLessThanOrEqual(
			(sidebarBounds?.x ?? 0) + (sidebarBounds?.width ?? 0)
		);
	}
});

test('inbox watched filters preserve an explicit all state in the URL', async ({
	page,
	context
}) => {
	await authenticate(context);
	await page.goto('/inbox');

	await page.getByRole('button', { name: 'All', exact: true }).click();
	await expect(page).toHaveURL(/is_watched=all/);
	await expect(page.getByRole('button', { name: 'All', exact: true })).toHaveClass(/btn-active/);

	await page.getByRole('button', { name: 'Watched', exact: true }).click();
	await expect(page).toHaveURL(/is_watched=true/);

	await page.goBack();
	await expect(page).toHaveURL(/is_watched=all/);
});

test('principal pages have no serious or critical axe violations', async ({ page, context }) => {
	await page.goto('/login');
	await expectNoBlockingAxeViolations(page, true);

	await authenticate(context);
	for (const path of [
		'/inbox',
		'/favorites',
		'/channels/UC_portfolio',
		'/watch-later',
		'/player',
		'/settings/imports',
		'/settings'
	]) {
		await page.goto(path);
		await expectNoBlockingAxeViolations(page, true);
	}
});

test('open video filters have accessible names and contrast', async ({ page, context }) => {
	await authenticate(context);
	await page.goto('/inbox');
	await page.getByText('Filters', { exact: true }).click();

	await expect(page.getByLabel('Length')).toBeVisible();
	await expect(page.getByLabel('Channel')).toBeVisible();
	await expect(page.getByLabel('Tag')).toBeVisible();
	await expect(page.getByLabel('Published after')).toBeVisible();
	await expect(page.getByLabel('Published before')).toBeVisible();
	await expect(page.getByLabel('Sort by')).toBeVisible();
	await expect(page.getByLabel('Direction')).toBeVisible();
	await expectNoBlockingAxeViolations(page, true);
});
