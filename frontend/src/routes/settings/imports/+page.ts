import type { PageLoad } from './$types';

export const load: PageLoad = ({ url }) => ({
	oauthError: url.searchParams.get('oauth_error')
});
