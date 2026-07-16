import { APIError } from '$lib/types/api';

interface CacheEntry<T = unknown> {
	data: T;
	expires: number;
}

interface FetchOptions extends RequestInit {
	retries?: number;
	cacheKey?: string;
	cacheTTL?: number;
}

let browserRefreshPromise: Promise<boolean> | null = null;

async function refreshBrowserSession(fetcher: typeof fetch): Promise<boolean> {
	if (!browserRefreshPromise) {
		browserRefreshPromise = fetcher('/api/auth/refresh', {
			method: 'POST',
			credentials: 'include'
		})
			.then((response) => response.ok)
			.catch(() => false)
			.finally(() => {
				browserRefreshPromise = null;
			});
	}
	return browserRefreshPromise;
}

/**
 * Delay utility for exponential backoff
 */
function delay(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Base API client with retry logic and caching
 */
export class APIClient {
	private baseURL: string;
	private fetcher: typeof fetch;
	private cache = new Map<string, CacheEntry>();
	private defaultRetries = 3;
	private defaultCacheTTL = 5 * 60 * 1000; // 5 minutes

	constructor(baseURL?: string, fetcher: typeof fetch = fetch) {
		this.baseURL = baseURL || '/api/backend';
		this.fetcher = fetcher;
	}

	/**
	 * Main fetch method with retry logic and caching
	 */
	async fetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
		const {
			retries = this.defaultRetries,
			cacheKey,
			cacheTTL = this.defaultCacheTTL,
			...fetchOptions
		} = options;

		const url = `${this.baseURL}${endpoint}`;
		const method = fetchOptions.method || 'GET';
		const finalCacheKey = cacheKey || `${method}:${url}`;

		const shouldCache = method === 'GET' && cacheTTL > 0 && typeof window !== 'undefined';

		// Check cache for GET requests
		if (shouldCache) {
			const cached = this.cache.get(finalCacheKey);
			if (cached && Date.now() < cached.expires) {
				return cached.data as T;
			}
		}

		// Attempt fetch with retry logic
		let lastError: Error | null = null;
		let refreshed = false;

		for (let attempt = 0; attempt < retries; attempt++) {
			try {
				const response = await this.fetcher(url, {
					...fetchOptions,
					credentials: 'include',
					headers:
						fetchOptions.body instanceof FormData
							? fetchOptions.headers
							: { 'Content-Type': 'application/json', ...fetchOptions.headers }
				});

				// Handle non-2xx responses
				if (!response.ok) {
					const errorBody = await response.json().catch(() => ({}));
					if (response.status === 401 && typeof window !== 'undefined' && !refreshed) {
						refreshed = true;
						if (await refreshBrowserSession(this.fetcher)) {
							attempt -= 1;
							continue;
						}
					}
					if (response.status === 401 && typeof window !== 'undefined') {
						const next = `${window.location.pathname}${window.location.search}`;
						window.location.assign(
							`/login?reason=session_expired&next=${encodeURIComponent(next)}`
						);
					}
					throw new APIError(response.status, errorBody);
				}

				// Handle 204 No Content
				const data = response.status === 204 ? null : await response.json();

				// Cache successful GET requests
				if (shouldCache && data !== null) {
					this.cache.set(finalCacheKey, {
						data,
						expires: Date.now() + cacheTTL
					});
				}

				return data as T;
			} catch (error) {
				lastError = error instanceof Error ? error : new Error('Unknown error');

				// Don't retry on 4xx errors (client errors)
				if (error instanceof APIError && error.status >= 400 && error.status < 500) {
					throw error;
				}

				// Exponential backoff for retries
				if (attempt < retries - 1) {
					const backoffTime = Math.pow(2, attempt) * 1000;
					await delay(backoffTime);
				}
			}
		}

		// All retries failed
		throw lastError || new Error('Request failed after retries');
	}

	/**
	 * Convenience method for GET requests
	 */
	async get<T>(
		endpoint: string,
		params?: Record<string, unknown>,
		options: Omit<FetchOptions, 'method'> = {}
	): Promise<T> {
		const query = params ? '?' + new URLSearchParams(this.buildQueryParams(params)).toString() : '';
		return this.fetch<T>(`${endpoint}${query}`, { ...options, method: 'GET' });
	}

	/**
	 * Convenience method for POST requests
	 */
	async post<T>(endpoint: string, body?: unknown): Promise<T> {
		return this.fetch<T>(endpoint, {
			method: 'POST',
			body: body ? JSON.stringify(body) : undefined
		});
	}

	async postForm<T>(endpoint: string, body: FormData): Promise<T> {
		return this.fetch<T>(endpoint, {
			method: 'POST',
			body
		});
	}

	/**
	 * Convenience method for PATCH requests
	 */
	async patch<T>(endpoint: string, body: unknown): Promise<T> {
		return this.fetch<T>(endpoint, {
			method: 'PATCH',
			body: JSON.stringify(body)
		});
	}

	/**
	 * Convenience method for PUT requests
	 */
	async put<T>(endpoint: string, body: unknown): Promise<T> {
		return this.fetch<T>(endpoint, {
			method: 'PUT',
			body: JSON.stringify(body)
		});
	}

	/**
	 * Convenience method for DELETE requests
	 */
	async delete(endpoint: string): Promise<void> {
		return this.fetch<void>(endpoint, {
			method: 'DELETE',
			cacheTTL: 0 // Don't cache delete requests
		});
	}

	/**
	 * Invalidate cache entries matching a pattern
	 */
	invalidateCache(pattern?: string): void {
		if (pattern) {
			for (const key of this.cache.keys()) {
				if (key.includes(pattern)) {
					this.cache.delete(key);
				}
			}
		} else {
			this.cache.clear();
		}
	}

	/**
	 * Build query parameters, filtering out undefined values
	 */
	private buildQueryParams(params: Record<string, unknown>): Record<string, string> {
		const result: Record<string, string> = {};

		for (const [key, value] of Object.entries(params)) {
			if (value !== undefined && value !== null) {
				result[key] = String(value);
			}
		}

		return result;
	}
}

// Create and export a singleton instance
export const apiClient = new APIClient();
