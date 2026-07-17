<script lang="ts">
	interface DurationRange {
		minMinutes: number | undefined;
		maxMinutes: number | undefined;
	}

	interface Props {
		minMinutes?: number;
		maxMinutes?: number;
		onchange: (range: DurationRange) => void;
	}

	let { minMinutes, maxMinutes, onchange }: Props = $props();
	let localMin = $state(0);
	let localMax = $state(60);

	$effect(() => {
		localMin = minMinutes ?? 0;
		localMax = maxMinutes ?? 60;
	});

	const summary = $derived.by(() => {
		if (localMin === 0 && localMax === 60) return 'Any duration';
		if (localMin === 60) return '1hr+';
		if (localMin === 0) return `Up to ${localMax} min`;
		if (localMax === 60) return `${localMin} min+`;
		return `${localMin}–${localMax} min`;
	});

	function readValue(event: Event): number {
		return Number((event.currentTarget as HTMLInputElement).value);
	}

	function updateMinimum(event: Event) {
		localMin = readValue(event);
		if (localMin > localMax) localMax = localMin;
	}

	function updateMaximum(event: Event) {
		localMax = readValue(event);
		if (localMax < localMin) localMin = localMax;
	}

	function commit() {
		onchange({
			minMinutes: localMin === 0 ? undefined : localMin,
			maxMinutes: localMax === 60 ? undefined : localMax
		});
	}
</script>

<fieldset class="space-y-2" aria-describedby="duration-summary">
	<legend class="sr-only">Duration</legend>
	<div class="flex items-center justify-between gap-2">
		<span class="text-xs font-medium text-base-content" aria-hidden="true">Duration</span>
		<output id="duration-summary" class="text-xs text-base-content/70" aria-live="polite">
			{summary}
		</output>
	</div>

	<label class="block text-xs text-base-content" for="minimum-duration-filter">
		<span class="flex justify-between"><span>Minimum</span><span>{localMin} min</span></span>
		<input
			id="minimum-duration-filter"
			type="range"
			min="0"
			max="60"
			step="1"
			value={localMin}
			aria-label="Minimum duration"
			class="range w-full range-primary range-xs"
			oninput={updateMinimum}
			onchange={commit}
		/>
	</label>

	<label class="block text-xs text-base-content" for="maximum-duration-filter">
		<span class="flex justify-between">
			<span>Maximum</span><span>{localMax === 60 ? '1hr+' : `${localMax} min`}</span>
		</span>
		<input
			id="maximum-duration-filter"
			type="range"
			min="0"
			max="60"
			step="1"
			value={localMax}
			aria-label="Maximum duration"
			class="range w-full range-primary range-xs"
			oninput={updateMaximum}
			onchange={commit}
		/>
	</label>
</fieldset>
