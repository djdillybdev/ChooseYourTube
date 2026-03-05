import { describe, expect, it } from 'vitest';
import { fit16x9 } from '../../../../src/lib/utils/playerFrameFit';

describe('fit16x9', () => {
	it('fits by width when container is short enough', () => {
		const result = fit16x9(1200, 900, 1400);
		expect(result).toEqual({ width: 1200, height: 675 });
	});

	it('fits by height when container is height-constrained', () => {
		const result = fit16x9(1200, 500, 1400);
		expect(result).toEqual({ width: 888, height: 500 });
	});

	it('applies max width cap before fitting', () => {
		const result = fit16x9(2200, 1000, 1400);
		expect(result).toEqual({ width: 1400, height: 787 });
	});

	it('returns zeros for non-positive input', () => {
		expect(fit16x9(0, 500, 1000)).toEqual({ width: 0, height: 0 });
		expect(fit16x9(1000, 0, 1000)).toEqual({ width: 0, height: 0 });
		expect(fit16x9(1000, 500, 0)).toEqual({ width: 0, height: 0 });
	});
});
