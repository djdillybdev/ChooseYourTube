export interface Channel {
  id: string
  title: string
  handle: string | null
  description: string | null
  thumbnail_url: string | null
  is_favorited: boolean
  folder_id: number | null
  created_at: string
  last_updated: string
  total_videos: number
}

export interface Video {
  id: string
  channel_id: string
  title: string
  description: string | null
  thumbnail_url: string | null
  published_at: string
  duration_seconds: number | null
  yt_tags: string[]
  is_short: boolean
  is_favorited: boolean
  is_watched: boolean
  created_at: string
}
