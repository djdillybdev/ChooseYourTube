import type {
	CandidateSelectionUpdate,
	OAuthStartOut,
	SubscriptionCandidateState,
	SubscriptionImportCommit,
	SubscriptionImportDetailOut,
	SubscriptionImportOut,
	SyncRunOut
} from '$lib/types/api';
import type { APIClient } from './client';

export class ImportsAPI {
	constructor(private client: APIClient) {}

	uploadCSV(file: File): Promise<SubscriptionImportDetailOut> {
		const form = new FormData();
		form.set('file', file);
		return this.client.postForm('/imports/subscriptions/csv', form);
	}

	startOAuth(): Promise<OAuthStartOut> {
		return this.client.get('/imports/youtube/oauth/start', undefined, { cacheTTL: 0 });
	}

	get(
		id: string,
		params: {
			state?: SubscriptionCandidateState;
			search?: string;
			limit?: number;
			offset?: number;
		} = {}
	): Promise<SubscriptionImportDetailOut> {
		return this.client.get(`/imports/${id}`, params, { cacheTTL: 0 });
	}

	updateSelection(id: string, payload: CandidateSelectionUpdate): Promise<SubscriptionImportOut> {
		return this.client.patch(`/imports/${id}/candidates`, payload);
	}

	commit(id: string, payload: SubscriptionImportCommit): Promise<SyncRunOut> {
		return this.client.post(`/imports/${id}/commit`, payload);
	}
}
