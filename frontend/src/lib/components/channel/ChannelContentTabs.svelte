<script lang="ts">
	import { resolve } from '$app/paths';
	interface Props {
		channelId: string;
		active: 'videos' | 'playlists';
	}

	let { channelId, active }: Props = $props();
</script>

<div class="tabs-box mb-4 tabs w-fit">
	<a
		href={resolve('/channels/[id]', { id: channelId })}
		class="tab"
		class:tab-active={active === 'videos'}
		aria-current={active === 'videos' ? 'page' : undefined}
	>
		Videos
	</a>
	<a
		href={resolve('/channels/[id]/playlists', { id: channelId })}
		class="tab"
		class:tab-active={active === 'playlists'}
		aria-current={active === 'playlists' ? 'page' : undefined}
	>
		Playlists
	</a>
</div>
