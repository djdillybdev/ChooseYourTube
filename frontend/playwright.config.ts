import { defineConfig } from '@playwright/test';

const portfolioBaseUrl = process.env.PORTFOLIO_BASE_URL?.replace(/\/$/, '');

export default defineConfig({
	webServer: portfolioBaseUrl
		? undefined
		: [
				{ command: 'node tests/e2e/fake-backend.mjs', port: 8123 },
				{
					command:
						'API_BASE_URL=http://127.0.0.1:8123 pnpm run build && API_BASE_URL=http://127.0.0.1:8123 pnpm run preview',
					port: 4173
				}
			],
	use: { baseURL: portfolioBaseUrl ?? 'http://localhost:4173' },
	testDir: 'tests/e2e'
});
