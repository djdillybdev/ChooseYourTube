import { describe, expect, it } from 'vitest';
import { load } from '../../../../src/routes/settings/+page';

describe('settings page load', () => {
	it('redirects to inbox', () => {
		try {
			load();
			throw new Error('expected redirect');
		} catch (error) {
			expect(error).toMatchObject({
				status: 307,
				location: '/inbox'
			});
		}
	});
});
