import adapter from '@sveltejs/adapter-node';
import vercelAdapter from '@sveltejs/adapter-vercel';

const deployToVercel = process.env.VERCEL === '1' || process.env.DEPLOY_TARGET === 'vercel';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: deployToVercel
			? vercelAdapter({ runtime: 'nodejs22.x', regions: ['iad1'] })
			: adapter()
	}
};

export default config;
