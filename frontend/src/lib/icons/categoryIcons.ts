import type { LucideIcon } from '@lucide/svelte';
import Activity from '@lucide/svelte/icons/activity';
import Archive from '@lucide/svelte/icons/archive';
import Atom from '@lucide/svelte/icons/atom';
import Award from '@lucide/svelte/icons/award';
import Bike from '@lucide/svelte/icons/bike';
import BookOpen from '@lucide/svelte/icons/book-open';
import Bookmark from '@lucide/svelte/icons/bookmark';
import Briefcase from '@lucide/svelte/icons/briefcase';
import CalendarDays from '@lucide/svelte/icons/calendar-days';
import Camera from '@lucide/svelte/icons/camera';
import CircleHelp from '@lucide/svelte/icons/circle-help';
import Clapperboard from '@lucide/svelte/icons/clapperboard';
import Cloud from '@lucide/svelte/icons/cloud';
import Coffee from '@lucide/svelte/icons/coffee';
import CookingPot from '@lucide/svelte/icons/cooking-pot';
import Dumbbell from '@lucide/svelte/icons/dumbbell';
import Earth from '@lucide/svelte/icons/earth';
import Film from '@lucide/svelte/icons/film';
import Flame from '@lucide/svelte/icons/flame';
import FlaskConical from '@lucide/svelte/icons/flask-conical';
import Folder from '@lucide/svelte/icons/folder';
import Gamepad2 from '@lucide/svelte/icons/gamepad-2';
import Gift from '@lucide/svelte/icons/gift';
import Globe from '@lucide/svelte/icons/globe';
import GraduationCap from '@lucide/svelte/icons/graduation-cap';
import Headphones from '@lucide/svelte/icons/headphones';
import Heart from '@lucide/svelte/icons/heart';
import House from '@lucide/svelte/icons/house';
import Image from '@lucide/svelte/icons/image';
import Laptop from '@lucide/svelte/icons/laptop';
import Leaf from '@lucide/svelte/icons/leaf';
import Library from '@lucide/svelte/icons/library';
import Lightbulb from '@lucide/svelte/icons/lightbulb';
import List from '@lucide/svelte/icons/list';
import MapIcon from '@lucide/svelte/icons/map';
import Medal from '@lucide/svelte/icons/medal';
import MessageCircle from '@lucide/svelte/icons/message-circle';
import Mic from '@lucide/svelte/icons/mic';
import MonitorPlay from '@lucide/svelte/icons/monitor-play';
import Music from '@lucide/svelte/icons/music';
import Newspaper from '@lucide/svelte/icons/newspaper';
import Palette from '@lucide/svelte/icons/palette';
import PawPrint from '@lucide/svelte/icons/paw-print';
import Plane from '@lucide/svelte/icons/plane';
import Podcast from '@lucide/svelte/icons/podcast';
import Radio from '@lucide/svelte/icons/radio';
import Rocket from '@lucide/svelte/icons/rocket';
import School from '@lucide/svelte/icons/school';
import ShoppingBag from '@lucide/svelte/icons/shopping-bag';
import Sparkles from '@lucide/svelte/icons/sparkles';
import Star from '@lucide/svelte/icons/star';
import Target from '@lucide/svelte/icons/target';
import Telescope from '@lucide/svelte/icons/telescope';
import Theater from '@lucide/svelte/icons/theater';
import Trophy from '@lucide/svelte/icons/trophy';
import Tv from '@lucide/svelte/icons/tv';
import Utensils from '@lucide/svelte/icons/utensils';
import Video from '@lucide/svelte/icons/video';
import Wrench from '@lucide/svelte/icons/wrench';

export interface CategoryIconOption {
	key: string;
	label: string;
	component: LucideIcon;
}

export const CATEGORY_ICONS: CategoryIconOption[] = [
	{ key: 'activity', label: 'Activity', component: Activity },
	{ key: 'archive', label: 'Archive', component: Archive },
	{ key: 'atom', label: 'Atom', component: Atom },
	{ key: 'award', label: 'Award', component: Award },
	{ key: 'bike', label: 'Bike', component: Bike },
	{ key: 'book-open', label: 'Book Open', component: BookOpen },
	{ key: 'bookmark', label: 'Bookmark', component: Bookmark },
	{ key: 'briefcase', label: 'Briefcase', component: Briefcase },
	{ key: 'calendar-days', label: 'Calendar', component: CalendarDays },
	{ key: 'camera', label: 'Camera', component: Camera },
	{ key: 'circle-help', label: 'Help', component: CircleHelp },
	{ key: 'clapperboard', label: 'Clapperboard', component: Clapperboard },
	{ key: 'cloud', label: 'Cloud', component: Cloud },
	{ key: 'coffee', label: 'Coffee', component: Coffee },
	{ key: 'cooking-pot', label: 'Cooking', component: CookingPot },
	{ key: 'dumbbell', label: 'Fitness', component: Dumbbell },
	{ key: 'earth', label: 'Earth', component: Earth },
	{ key: 'film', label: 'Film', component: Film },
	{ key: 'flame', label: 'Trending', component: Flame },
	{ key: 'flask-conical', label: 'Science', component: FlaskConical },
	{ key: 'folder', label: 'Folder', component: Folder },
	{ key: 'gamepad-2', label: 'Gaming', component: Gamepad2 },
	{ key: 'gift', label: 'Gift', component: Gift },
	{ key: 'globe', label: 'Globe', component: Globe },
	{ key: 'graduation-cap', label: 'Education', component: GraduationCap },
	{ key: 'headphones', label: 'Headphones', component: Headphones },
	{ key: 'heart', label: 'Heart', component: Heart },
	{ key: 'house', label: 'Home', component: House },
	{ key: 'image', label: 'Photography', component: Image },
	{ key: 'laptop', label: 'Technology', component: Laptop },
	{ key: 'leaf', label: 'Nature', component: Leaf },
	{ key: 'library', label: 'Library', component: Library },
	{ key: 'lightbulb', label: 'Ideas', component: Lightbulb },
	{ key: 'map', label: 'Map', component: MapIcon },
	{ key: 'medal', label: 'Medal', component: Medal },
	{ key: 'message-circle', label: 'Chat', component: MessageCircle },
	{ key: 'mic', label: 'Microphone', component: Mic },
	{ key: 'monitor-play', label: 'Streaming', component: MonitorPlay },
	{ key: 'music', label: 'Music', component: Music },
	{ key: 'newspaper', label: 'News', component: Newspaper },
	{ key: 'palette', label: 'Art', component: Palette },
	{ key: 'paw-print', label: 'Animals', component: PawPrint },
	{ key: 'plane', label: 'Travel', component: Plane },
	{ key: 'podcast', label: 'Podcast', component: Podcast },
	{ key: 'radio', label: 'Radio', component: Radio },
	{ key: 'rocket', label: 'Rocket', component: Rocket },
	{ key: 'school', label: 'School', component: School },
	{ key: 'shopping-bag', label: 'Shopping', component: ShoppingBag },
	{ key: 'sparkles', label: 'Sparkles', component: Sparkles },
	{ key: 'star', label: 'Star', component: Star },
	{ key: 'target', label: 'Target', component: Target },
	{ key: 'telescope', label: 'Astronomy', component: Telescope },
	{ key: 'theater', label: 'Theater', component: Theater },
	{ key: 'trophy', label: 'Sports', component: Trophy },
	{ key: 'tv', label: 'Television', component: Tv },
	{ key: 'utensils', label: 'Food', component: Utensils },
	{ key: 'video', label: 'Video', component: Video },
	{ key: 'wrench', label: 'Tools', component: Wrench }
];

const iconByKey = new Map(CATEGORY_ICONS.map((icon) => [icon.key, icon.component]));

export function getCategoryIcon(iconKey: string | null | undefined): LucideIcon {
	return (iconKey && iconByKey.get(iconKey)) || List;
}

export function hasCategoryIcon(iconKey: string | null | undefined): boolean {
	return iconKey ? iconByKey.has(iconKey) : false;
}
