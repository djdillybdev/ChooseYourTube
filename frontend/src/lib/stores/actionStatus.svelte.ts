export type ActionStatus = {
	id: number;
	message: string;
};

let nextId = 0;
let clearTimer: ReturnType<typeof setTimeout> | undefined;

class ActionStatusState {
	current = $state<ActionStatus | null>(null);

	announce(message: string, duration = 4000): void {
		if (clearTimer) clearTimeout(clearTimer);
		this.current = { id: ++nextId, message };
		clearTimer = setTimeout(() => this.clear(), duration);
	}

	clear(): void {
		if (clearTimer) clearTimeout(clearTimer);
		clearTimer = undefined;
		this.current = null;
	}
}

export const actionStatus = new ActionStatusState();
