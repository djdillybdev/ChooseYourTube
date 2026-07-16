import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchFromEventMock, refreshAuthSessionMock } = vi.hoisted(() => ({
	backendFetchFromEventMock: vi.fn(),
	refreshAuthSessionMock: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetchFromEventMock,
	refreshAuthSession: refreshAuthSessionMock
}));

import { GET } from '../../../../../src/routes/api/bootstrap/+server';

describe('application bootstrap route', () => {
	beforeEach(() => {
		backendFetchFromEventMock.mockReset();
		refreshAuthSessionMock.mockReset();
	});

	it('refreshes once before retrying the consolidated bootstrap', async () => {
		backendFetchFromEventMock
			.mockResolvedValueOnce(new Response(null, { status: 401 }))
			.mockResolvedValueOnce(Response.json({ channels: [], folders: [], tags: [] }));
		refreshAuthSessionMock.mockResolvedValue(true);

		const response = await GET({} as never);

		expect(refreshAuthSessionMock).toHaveBeenCalledOnce();
		expect(backendFetchFromEventMock).toHaveBeenCalledTimes(2);
		expect(backendFetchFromEventMock).toHaveBeenLastCalledWith({}, '/app/bootstrap');
		expect(response.status).toBe(200);
	});

	it('returns the original 401 when refresh fails', async () => {
		backendFetchFromEventMock.mockResolvedValue(new Response(null, { status: 401 }));
		refreshAuthSessionMock.mockResolvedValue(false);

		const response = await GET({} as never);

		expect(backendFetchFromEventMock).toHaveBeenCalledOnce();
		expect(response.status).toBe(401);
	});
});
