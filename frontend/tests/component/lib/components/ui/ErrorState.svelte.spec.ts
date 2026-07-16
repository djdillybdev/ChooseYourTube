import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ErrorState from '../../../../../src/lib/components/ui/ErrorState.svelte';

describe('ErrorState', () => {
	it('renders a safe request ID and invokes an available retry', async () => {
		const retry = vi.fn();
		render(ErrorState, {
			heading: 'Videos could not be loaded',
			message: 'Check your connection and try again.',
			requestId: 'request-123',
			onRetry: retry
		});

		expect(screen.getByRole('alert')).toHaveTextContent('Request ID: request-123');
		await fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));
		expect(retry).toHaveBeenCalledOnce();
	});

	it('does not expose retry when none is safe', () => {
		render(ErrorState, { message: 'Retry after the quota resets.' });
		expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
	});
});
