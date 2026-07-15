import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ImportsAPI } from '../../../../src/lib/api/imports';
import { SyncRunsAPI } from '../../../../src/lib/api/syncRuns';
import { TagsAPI } from '../../../../src/lib/api/tags';

function client() {
	return {
		get: vi.fn(),
		post: vi.fn(),
		postForm: vi.fn(),
		patch: vi.fn(),
		delete: vi.fn(),
		invalidateCache: vi.fn()
	};
}

describe('critical Phase 2-5 API wrappers', () => {
	let mockClient: ReturnType<typeof client>;

	beforeEach(() => {
		mockClient = client();
	});

	it('forwards every subscription import operation with uncached reads', async () => {
		const api = new ImportsAPI(mockClient as any);
		const file = new File(['Channel Id\nUC1'], 'subscriptions.csv', { type: 'text/csv' });

		api.uploadCSV(file);
		expect(mockClient.postForm).toHaveBeenCalledWith(
			'/imports/subscriptions/csv',
			expect.any(FormData)
		);
		api.startOAuth();
		expect(mockClient.get).toHaveBeenLastCalledWith('/imports/youtube/oauth/start', undefined, {
			cacheTTL: 0
		});
		api.get('import-1', { state: 'new', search: 'music' });
		expect(mockClient.get).toHaveBeenLastCalledWith(
			'/imports/import-1',
			{ state: 'new', search: 'music' },
			{ cacheTTL: 0 }
		);
		api.updateSelection('import-1', { candidate_ids: ['candidate-1'], selected: true });
		expect(mockClient.patch).toHaveBeenCalledWith('/imports/import-1/candidates', {
			candidate_ids: ['candidate-1'],
			selected: true
		});
		api.commit('import-1', { selected_candidate_ids: ['candidate-1'] });
		expect(mockClient.post).toHaveBeenCalledWith('/imports/import-1/commit', {
			selected_candidate_ids: ['candidate-1']
		});
	});

	it('uses bounded uncached reads for sync status and exposes retry/quota', () => {
		const api = new SyncRunsAPI(mockClient as any);
		api.list({ status: 'failed' });
		expect(mockClient.get).toHaveBeenCalledWith('/sync-runs', { status: 'failed' });
		api.get('run-1');
		expect(mockClient.get).toHaveBeenCalledWith('/sync-runs/run-1', undefined, {
			cacheTTL: 0,
			retries: 1
		});
		api.retry('run-1');
		expect(mockClient.post).toHaveBeenCalledWith('/sync-runs/run-1/retry');
		api.quota();
		expect(mockClient.get).toHaveBeenCalledWith('/sync-runs/quota', undefined, { cacheTTL: 0 });
	});

	it('invalidates tag and associated-resource caches after mutations', async () => {
		const api = new TagsAPI(mockClient as any);
		mockClient.post.mockResolvedValue({ id: 'tag-1', name: 'music' });
		mockClient.patch.mockResolvedValue({ id: 'tag-1', name: 'audio' });

		await api.list({ limit: 20 });
		await api.get('tag-1');
		await api.create({ name: 'music' });
		await api.update('tag-1', { name: 'audio' });
		await api.delete('tag-1');
		await api.getVideos('tag-1', { limit: 10 });
		await api.getChannels('tag-1', { offset: 10 });

		expect(mockClient.delete).toHaveBeenCalledWith('/tags/tag-1');
		expect(mockClient.invalidateCache).toHaveBeenCalledWith('tags/');
		expect(mockClient.invalidateCache).toHaveBeenCalledWith('channels/');
		expect(mockClient.invalidateCache).toHaveBeenCalledWith('videos/');
		expect(mockClient.get).toHaveBeenCalledWith('/tags/tag-1/videos', { limit: 10 });
		expect(mockClient.get).toHaveBeenCalledWith('/tags/tag-1/channels', { offset: 10 });
	});
});
