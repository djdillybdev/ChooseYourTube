<script lang="ts">
	interface Props {
		channelId: string;
		active: 'videos' | 'playlists';
	}

	let { channelId, active }: Props = $props();
</script>

<div class="tabs tabs-box mb-4 w-fit">
	<a
		href={`/channels/${channelId}`}
		class="tab"
		class:tab-active={active === 'videos'}
		aria-current={active === 'videos' ? 'page' : undefined}
	>
		Videos
	</a>
	<a
		href={`/channels/${channelId}/playlists`}
		class="tab"
		class:tab-active={active === 'playlists'}
		aria-current={active === 'playlists' ? 'page' : undefined}
	>
		Playlists
	</a>
</div>
