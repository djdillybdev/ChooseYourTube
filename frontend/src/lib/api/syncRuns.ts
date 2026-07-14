import type {
	PaginatedResponse,
	SyncRunFilters,
	SyncRunOut,
	YouTubeQuotaStatusOut
} from '$lib/types/api';
import type { APIClient } from './client';

export class SyncRunsAPI {
	constructor(private client: APIClient) {}

	list(filters?: SyncRunFilters): Promise<PaginatedResponse<SyncRunOut>> {
		return this.client.get('/sync-runs', filters);
	}

	get(id: string): Promise<SyncRunOut> {
		return this.client.get(`/sync-runs/${id}`, undefined, { cacheTTL: 0, retries: 1 });
	}

	retry(id: string): Promise<SyncRunOut> {
		return this.client.post(`/sync-runs/${id}/retry`);
	}

	quota(): Promise<YouTubeQuotaStatusOut> {
		return this.client.get('/sync-runs/quota', undefined, { cacheTTL: 0 });
	}
}
