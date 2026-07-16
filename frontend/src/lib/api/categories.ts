import type { APIClient } from './client';
import type {
	CategoryChannelsUpdate,
	CategoryCreate,
	CategoryOut,
	CategoryUpdate,
	ChannelCategoriesOut,
	ChannelCategoriesUpdate
} from '$lib/types/api';

export class CategoriesAPI {
	constructor(private client: APIClient) {}

	list(): Promise<CategoryOut[]> {
		return this.client.get<CategoryOut[]>('/categories/');
	}

	get(id: string): Promise<CategoryOut> {
		return this.client.get<CategoryOut>(`/categories/${id}`);
	}

	async create(data: CategoryCreate): Promise<CategoryOut> {
		const category = await this.client.post<CategoryOut>('/categories/', data);
		this.client.invalidateCache('categories/');
		return category;
	}

	async update(id: string, data: CategoryUpdate): Promise<CategoryOut> {
		const category = await this.client.patch<CategoryOut>(`/categories/${id}`, data);
		this.client.invalidateCache('categories/');
		this.client.invalidateCache(`/categories/${id}`);
		return category;
	}

	async delete(id: string): Promise<void> {
		await this.client.delete(`/categories/${id}`);
		this.client.invalidateCache('categories/');
	}

	async setChannels(id: string, data: CategoryChannelsUpdate): Promise<CategoryOut> {
		const category = await this.client.put<CategoryOut>(`/categories/${id}/channels`, data);
		this.client.invalidateCache('categories/');
		this.client.invalidateCache(`/categories/${id}`);
		return category;
	}

	async setForChannel(
		channelId: string,
		data: ChannelCategoriesUpdate
	): Promise<ChannelCategoriesOut> {
		const membership = await this.client.put<ChannelCategoriesOut>(
			`/categories/channels/${channelId}`,
			data
		);
		this.client.invalidateCache('categories/');
		return membership;
	}
}
