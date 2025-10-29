import { FormEvent, useEffect, useMemo, useState } from 'react'
import './App.css'
import { addChannel, getApiBaseUrl, getChannels, getVideosForChannel } from './api'
import type { Channel, Video } from './types'

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function formatDuration(seconds: number | null) {
  if (seconds === null || Number.isNaN(seconds)) {
    return null
  }

  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  const parts = []
  if (mins > 0) {
    parts.push(`${mins}m`)
  }
  parts.push(`${secs}s`)

  return parts.join(' ')
}

function App() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [channelsLoading, setChannelsLoading] = useState(false)
  const [channelsError, setChannelsError] = useState<string | null>(null)

  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null)

  const [videos, setVideos] = useState<Video[]>([])
  const [videosLoading, setVideosLoading] = useState(false)
  const [videosError, setVideosError] = useState<string | null>(null)

  const [activeVideo, setActiveVideo] = useState<Video | null>(null)

  const [handleInput, setHandleInput] = useState('')
  const [addChannelLoading, setAddChannelLoading] = useState(false)
  const [addChannelError, setAddChannelError] = useState<string | null>(null)
  const [addChannelSuccess, setAddChannelSuccess] = useState<string | null>(null)

  useEffect(() => {
    const loadChannels = async () => {
      setChannelsLoading(true)
      setChannelsError(null)
      try {
        const data = await getChannels()
        setChannels(data)

        if (data.length > 0) {
          setSelectedChannelId((prev) => prev ?? data[0].id)
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unable to load channels'
        setChannelsError(message)
      } finally {
        setChannelsLoading(false)
      }
    }

    loadChannels()
  }, [])

  useEffect(() => {
    const channelId = selectedChannelId
    if (!channelId) {
      setVideos([])
      return
    }

    const loadVideos = async () => {
      setVideosLoading(true)
      setVideosError(null)
      try {
        const data = await getVideosForChannel(channelId)
        setVideos(data)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unable to load videos'
        setVideosError(message)
      } finally {
        setVideosLoading(false)
      }
    }

    loadVideos()
  }, [selectedChannelId])

  const selectedChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannelId) ?? null,
    [channels, selectedChannelId],
  )

  const onChannelSelect = (channelId: string) => {
    setSelectedChannelId(channelId)
  }

  const onAddChannel = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmed = handleInput.trim()
    if (!trimmed) {
      setAddChannelError('Enter a channel handle or ID to add it.')
      setAddChannelSuccess(null)
      return
    }

    setAddChannelLoading(true)
    setAddChannelError(null)
    setAddChannelSuccess(null)

    try {
      const newChannel = await addChannel(trimmed)
      setChannels((prev) => {
        const next = [...prev]
        const existingIndex = next.findIndex((channel) => channel.id === newChannel.id)
        if (existingIndex >= 0) {
          next[existingIndex] = newChannel
        } else {
          next.unshift(newChannel)
        }
        return next
      })
      setHandleInput('')
      setAddChannelSuccess(`${newChannel.title} has been added.`)
      setSelectedChannelId(newChannel.id)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to add channel'
      setAddChannelError(message)
    } finally {
      setAddChannelLoading(false)
    }
  }

  useEffect(() => {
    if (!activeVideo) {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setActiveVideo(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [activeVideo])

  const onVideoSelect = (video: Video) => {
    setActiveVideo(video)
  }

  const onModalClose = () => {
    setActiveVideo(null)
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="sidebar__header">
          <h1>ChooseYourTube</h1>
          <p className="sidebar__subtitle">Build your own distraction-free subscriptions.</p>
        </header>

        <section className="sidebar__section">
          <h2 className="sidebar__section-title">Add a channel</h2>
          <form className="add-channel-form" onSubmit={onAddChannel}>
            <label htmlFor="channel-handle" className="sr-only">
              Channel handle or ID
            </label>
            <div className="add-channel-form__controls">
              <input
                id="channel-handle"
                type="text"
                placeholder="@handle or channel ID"
                value={handleInput}
                onChange={(event) => setHandleInput(event.target.value)}
                disabled={addChannelLoading}
              />
              <button type="submit" disabled={addChannelLoading}>
                {addChannelLoading ? 'Adding…' : 'Add'}
              </button>
            </div>
          </form>
          <p className="sidebar__help">
            We’ll use the YouTube Data API to find the channel and queue a background job to
            fetch its videos.
          </p>
          {addChannelError ? <p className="feedback feedback--error">{addChannelError}</p> : null}
          {addChannelSuccess ? <p className="feedback feedback--success">{addChannelSuccess}</p> : null}
        </section>

        <section className="sidebar__section">
          <div className="channels-header">
            <h2 className="sidebar__section-title">Your channels</h2>
            <span className="api-indicator">API: {getApiBaseUrl()}</span>
          </div>
          {channelsLoading ? <p className="muted">Loading channels…</p> : null}
          {channelsError ? <p className="feedback feedback--error">{channelsError}</p> : null}

          <div className="channel-list" role="list">
            {channels.length === 0 && !channelsLoading ? (
              <p className="muted">No channels yet. Add one to get started.</p>
            ) : null}
            {channels.map((channel) => (
              <button
                role="listitem"
                key={channel.id}
                className={`channel-list__item${channel.id === selectedChannelId ? ' channel-list__item--active' : ''}`}
                onClick={() => onChannelSelect(channel.id)}
              >
                <span className="channel-list__title">{channel.title}</span>
                <span className="channel-list__meta">
                  {channel.total_videos} video{channel.total_videos === 1 ? '' : 's'}
                </span>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <main className="content">
        {selectedChannel ? (
          <>
            <header className="channel-details">
              {selectedChannel.thumbnail_url ? (
                <img
                  className="channel-details__thumbnail"
                  src={selectedChannel.thumbnail_url}
                  alt={`${selectedChannel.title} thumbnail`}
                />
              ) : null}
              <div>
                <h2>{selectedChannel.title}</h2>
                {selectedChannel.handle ? (
                  <p className="muted">{selectedChannel.handle}</p>
                ) : null}
                <p className="muted">
                  Added {formatDate(selectedChannel.created_at)} · Last updated{' '}
                  {formatDate(selectedChannel.last_updated)}
                </p>
                {selectedChannel.description ? (
                  <p className="channel-details__description">{selectedChannel.description}</p>
                ) : null}
              </div>
            </header>

            <section className="videos-section">
              <div className="videos-section__header">
                <h3>Latest videos</h3>
                <p className="muted">
                  Showing {videos.length} of {selectedChannel.total_videos} stored videos
                </p>
              </div>

              {videosLoading ? <p className="muted">Loading videos…</p> : null}
              {videosError ? <p className="feedback feedback--error">{videosError}</p> : null}

              <div className="video-grid">
                {!videosLoading && videos.length === 0 ? (
                  <p className="muted">No videos synced yet for this channel.</p>
                ) : null}

                {videos.map((video) => (
                  <button
                    key={video.id}
                    type="button"
                    className="video-card"
                    onClick={() => onVideoSelect(video)}
                  >
                    {video.thumbnail_url ? (
                      <img
                        src={video.thumbnail_url}
                        alt="Video thumbnail"
                        className="video-card__thumbnail"
                        loading="lazy"
                      />
                    ) : null}
                    <div className="video-card__body">
                      <h4 className="video-card__title">{video.title}</h4>
                      <p className="video-card__meta">
                        Published {formatDate(video.published_at)}
                        {video.duration_seconds !== null ? ` · ${formatDuration(video.duration_seconds)}` : ''}
                        {video.is_short ? ' · Short' : ''}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          </>
        ) : (
          <div className="empty-state">
            <h2>Welcome to ChooseYourTube</h2>
            <p>Add your first channel to start building your personal feed.</p>
          </div>
        )}
      </main>

      {activeVideo ? (
        <div className="modal-overlay" role="presentation" onClick={onModalClose}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="video-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button type="button" className="modal__close" onClick={onModalClose} aria-label="Close video">
              ×
            </button>
            <div className="modal__video">
              <iframe
                src={`https://www.youtube.com/embed/${activeVideo.id}`}
                title={activeVideo.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              />
            </div>
            <div className="modal__body">
              <h3 id="video-modal-title">{activeVideo.title}</h3>
              <p className="modal__meta">
                Published {formatDate(activeVideo.published_at)}
                {activeVideo.duration_seconds !== null ? ` · ${formatDuration(activeVideo.duration_seconds)}` : ''}
                {activeVideo.is_short ? ' · Short' : ''}
              </p>
              {activeVideo.description ? (
                <p className="modal__description">{activeVideo.description}</p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default App
