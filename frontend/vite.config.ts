import { defineConfig } from 'vitest/config';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	test: {
		expect: {
			requireAssertions: true
		},
		coverage: {
			provider: 'v8',
			reporter: ['text', 'html', 'lcov'],
			include: [
				'src/hooks.server.ts',
				'src/lib/api/auth.ts',
				'src/lib/api/client.ts',
				'src/lib/api/imports.ts',
				'src/lib/api/syncRuns.ts',
				'src/lib/api/tags.ts',
				'src/lib/server/auth.ts',
				'src/lib/stores/watchLater.svelte.ts',
				'src/lib/utils/channelLookup.ts',
				'src/lib/utils/formatDate.ts',
				'src/lib/utils/formatDuration.ts',
				'src/lib/utils/syncPolling.ts',
				'src/lib/utils/videoFilterQuery.ts',
				'src/lib/components/layout/Sidebar.svelte',
				'src/lib/components/ui/ConfirmDialog.svelte',
				'src/lib/components/video/WatchLaterButton.svelte',
				'src/routes/api/auth/account/+server.ts',
				'src/routes/api/auth/demo/+server.ts',
				'src/routes/api/auth/login/+server.ts',
				'src/routes/api/auth/logout/+server.ts',
				'src/routes/api/auth/me/+server.ts',
				'src/routes/api/auth/refresh/+server.ts',
				'src/routes/api/auth/register/+server.ts',
				'src/routes/api/backend/[...path]/+server.ts',
				'src/routes/inbox/+page.ts',
				'src/routes/channels/[id]/+page.ts'
			],
			exclude: ['src/**/*.d.ts', 'src/**/*.spec.ts', 'src/**/*.test.ts'],
			thresholds: {
				lines: 70,
				branches: 70,
				functions: 70,
				statements: 70
			}
		},
		projects: [
			{
				extends: true,
				test: {
					name: 'server',
					environment: 'node',
					setupFiles: ['tests/setup/msw.setup.ts'],
					include: ['tests/unit/**/*.{test,spec}.ts']
				}
			},
			{
				extends: true,
				resolve: {
					conditions: ['browser']
				},
				test: {
					name: 'component',
					environment: 'jsdom',
					setupFiles: ['tests/setup/vitest.setup.ts', 'tests/setup/msw.setup.ts'],
					include: ['tests/component/**/*.svelte.{test,spec}.ts']
				}
			}
		]
	}
});
