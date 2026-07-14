export interface RuntimeMetadata {
	name: string;
	version: string;
	mode: 'full' | 'demo';
	features: {
		registration: boolean;
		background_jobs: boolean;
		youtube_oauth: boolean;
		demo_login: boolean;
		subscription_imports: boolean;
	};
}
