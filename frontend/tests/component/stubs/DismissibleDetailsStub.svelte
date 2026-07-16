<script lang="ts">
	import { dismissibleDetails } from '../../../src/lib/actions/dismissibleDetails';
</script>

<button type="button">Outside control</button>

<details use:dismissibleDetails>
	<summary>Open menu</summary>
	<label>
		Menu field
		<input />
	</label>
</details>
