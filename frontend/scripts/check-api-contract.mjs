import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const frontend = resolve(import.meta.dirname, '..');
const backend = resolve(frontend, '..', 'backend');
const temporary = mkdtempSync(join(tmpdir(), 'chooseyourtube-contract-'));
const schema = join(temporary, 'openapi.json');
const types = join(temporary, 'generated.ts');

try {
	execFileSync('uv', ['run', 'python', 'scripts/export_openapi.py', schema], {
		cwd: backend,
		env: { ...process.env, UV_CACHE_DIR: join(tmpdir(), 'chooseyourtube-uv-cache') },
		stdio: 'inherit'
	});
	execFileSync('pnpm', ['exec', 'openapi-typescript', schema, '-o', types], {
		cwd: frontend,
		stdio: 'inherit'
	});
	execFileSync(
		'pnpm',
		['exec', 'prettier', '--config', join(frontend, '.prettierrc'), '--write', schema, types],
		{
			cwd: frontend,
			stdio: 'ignore'
		}
	);

	const comparisons = [
		[schema, join(frontend, 'openapi.json')],
		[types, join(frontend, 'src', 'lib', 'types', 'generated.ts')]
	];
	for (const [actual, expected] of comparisons) {
		if (!readFileSync(actual).equals(readFileSync(expected))) {
			throw new Error(`API contract drift detected in ${expected}`);
		}
	}
} finally {
	rmSync(temporary, { recursive: true, force: true });
}
