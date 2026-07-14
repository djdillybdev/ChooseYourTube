import type { SyncRunOut, SyncRunStatus } from '$lib/types/api';

const TERMINAL: ReadonlySet<SyncRunStatus> = new Set(['succeeded', 'partial', 'failed']);
const DELAYS = [1000, 2000, 4000, 8000, 10000];

export function isTerminalSync(status: SyncRunStatus): boolean {
	return TERMINAL.has(status);
}

export async function pollSyncRun(
	id: string,
	getRun: (id: string) => Promise<SyncRunOut>,
	onUpdate: (run: SyncRunOut) => void,
	isCancelled: () => boolean = () => false,
	wait: (milliseconds: number) => Promise<void> = (milliseconds) =>
		new Promise((resolve) => setTimeout(resolve, milliseconds))
): Promise<SyncRunOut | null> {
	let attempt = 0;
	while (!isCancelled()) {
		const run = await getRun(id);
		if (isCancelled()) return null;
		onUpdate(run);
		if (isTerminalSync(run.status)) return run;
		await wait(DELAYS[Math.min(attempt, DELAYS.length - 1)]);
		attempt += 1;
	}
	return null;
}
