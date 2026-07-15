import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const API = 'http://127.0.0.1:8000';
const PASSWORD = 'Phase6-password-2026!';

async function session(request: import('@playwright/test').APIRequestContext, email: string) {
	const response = await request.post(`${API}/auth/session/login`, {
		data: { email, password: PASSWORD }
	});
	expect(response.ok()).toBe(true);
	return response.json() as Promise<{ access_token: string; refresh_token: string }>;
}

async function expectAccessible(page: import('@playwright/test').Page) {
	const result = await new AxeBuilder({ page })
		.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
		.analyze();
	const blocking = result.violations.filter(
		(violation) => violation.impact === 'serious' || violation.impact === 'critical'
	);
	expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
}

test('full-mode login, inbox, persistent state, and logout', async ({ page }) => {
	await page.goto('/login');
	await page.getByLabel('Email').fill('phase6-one@example.com');
	await page.getByLabel('Password').fill(PASSWORD);
	await page.getByRole('button', { name: 'Log in' }).click();
	await expect(page).toHaveURL(/\/inbox/);
	await expect(page.getByText('Phase 6 portfolio video 1')).toBeVisible();
	await expectAccessible(page);

	const firstVideo = page.getByRole('group', { name: 'Phase 6 portfolio video 1' });
	await firstVideo.getByRole('button', { name: 'Remove from Watch Later' }).click();
	await expect(firstVideo.getByRole('button', { name: 'Save to Watch Later' })).toBeVisible();
	await page.reload();
	await expect(
		page
			.getByRole('group', { name: 'Phase 6 portfolio video 1' })
			.getByRole('button', { name: 'Save to Watch Later' })
	).toBeVisible();

	await page.getByRole('button', { name: 'Logout' }).click();
	await expect(page).toHaveURL(/\/login/);
});

test('owner-scoped API resources cannot be read by another user', async ({ request }) => {
	const first = await session(request, 'phase6-one@example.com');
	const second = await session(request, 'phase6-two@example.com');
	const created = await request.post(`${API}/tags/`, {
		headers: { Authorization: `Bearer ${first.access_token}` },
		data: { name: 'private-phase6' }
	});
	expect(created.status()).toBe(201);
	const tag = await created.json();

	const hidden = await request.get(`${API}/tags/${tag.id}`, {
		headers: { Authorization: `Bearer ${second.access_token}` }
	});
	expect(hidden.status()).toBe(404);
});

test('refresh sessions rotate and force reauthentication after reuse', async ({ request }) => {
	const login = await session(request, 'phase6-two@example.com');
	const rotated = await request.post(`${API}/auth/session/refresh`, {
		data: { refresh_token: login.refresh_token }
	});
	expect(rotated.ok()).toBe(true);
	const replacement = await rotated.json();
	expect(replacement.refresh_token).not.toBe(login.refresh_token);

	const reused = await request.post(`${API}/auth/session/refresh`, {
		data: { refresh_token: login.refresh_token }
	});
	expect(reused.status()).toBe(401);
	const revoked = await request.post(`${API}/auth/session/refresh`, {
		data: { refresh_token: replacement.refresh_token }
	});
	expect(revoked.status()).toBe(401);
});
