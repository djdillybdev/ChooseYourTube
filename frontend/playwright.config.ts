import { defineConfig } from '@playwright/test';

export default defineConfig({
	webServer: [
		{ command: 'node tests/e2e/fake-backend.mjs', port: 8123 },
		{
			command:
				'API_BASE_URL=http://127.0.0.1:8123 pnpm run build && API_BASE_URL=http://127.0.0.1:8123 pnpm run preview',
			port: 4173
		}
	],
	use: { baseURL: 'http://localhost:4173' },
	testDir: 'tests/e2e'
});
