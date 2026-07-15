import { defineConfig } from '@playwright/test';

export default defineConfig({
	testDir: 'tests/e2e-full',
	fullyParallel: false,
	workers: 1,
	retries: process.env.CI ? 2 : 0,
	reporter: process.env.CI ? [['html', { open: 'never' }], ['github']] : 'list',
	use: {
		baseURL: 'http://127.0.0.1:5173',
		trace: 'retain-on-failure',
		screenshot: 'only-on-failure'
	}
});
