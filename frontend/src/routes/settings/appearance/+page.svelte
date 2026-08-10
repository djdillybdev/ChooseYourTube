<script lang="ts">
	import { applyTheme, themeOptions, type ThemePreference } from '$lib/theme';
	import { setTheme, uiState } from '$lib/stores/uiState.svelte';

	function chooseTheme(theme: ThemePreference) {
		setTheme(theme);
		applyTheme(theme);
	}
</script>

<svelte:head><title>Appearance - Settings - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-6xl p-6 pt-5">
	<section class="rounded-box border border-base-300 bg-base-100 p-5">
		<div class="mb-5">
			<h2 class="text-xl font-semibold">Appearance</h2>
			<p class="text-sm text-base-content/70">
				Choose the colors used throughout ChooseYourTube. This preference is saved in this browser.
			</p>
		</div>

		<fieldset>
			<legend class="sr-only">Color theme</legend>
			<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
				{#each themeOptions as option (option.value)}
					<label
						class="card cursor-pointer border-2 p-4 transition-colors hover:border-primary"
						class:border-primary={uiState.current.theme === option.value}
						class:border-base-300={uiState.current.theme !== option.value}
					>
						<div class="flex items-start gap-3">
							<input
								class="radio mt-0.5 radio-primary"
								type="radio"
								name="theme"
								value={option.value}
								checked={uiState.current.theme === option.value}
								onchange={() => chooseTheme(option.value)}
							/>
							<span>
								<span class="block font-medium">{option.label}</span>
								<span class="mt-1 block text-sm text-base-content/70">{option.description}</span>
							</span>
						</div>
						<span class="mt-4 flex gap-1" aria-hidden="true">
							{#each option.preview as color (color)}
								<span class="h-5 flex-1 rounded-sm" style={`background: ${color}`}></span>
							{/each}
						</span>
					</label>
				{/each}
			</div>
		</fieldset>
	</section>
</div>
