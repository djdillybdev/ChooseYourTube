import { FormEvent, useEffect, useMemo, useState } from "react";

import { createChannel, fetchChannels, fetchVideosForChannel } from "./api";
import "./App.css";
import { Channel, Video } from "./types";

function formatPublishedDate(date: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(date));
  } catch (error) {
    return date;
  }
}

export default function App() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelsLoading, setChannelsLoading] = useState(true);
  const [channelsError, setChannelsError] = useState<string | null>(null);

  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);

  const [videos, setVideos] = useState<Video[]>([]);
  const [videosLoading, setVideosLoading] = useState(false);
  const [videosError, setVideosError] = useState<string | null>(null);

  const [handleInput, setHandleInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<
    { type: "success" | "error"; message: string }
    | null
  >(null);

  useEffect(() => {
    const abortController = new AbortController();
    setChannelsLoading(true);
    setChannelsError(null);

    fetchChannels(abortController.signal)
      .then((data) => {
        setChannels(data);
        if (data.length > 0) {
          setSelectedChannelId((current) => current ?? data[0].id);
        }
      })
      .catch((error) => {
        if (error instanceof Error && error.name !== "AbortError") {
          setChannelsError(error.message);
        }
      })
      .finally(() => {
        setChannelsLoading(false);
      });

    return () => abortController.abort();
  }, []);

  useEffect(() => {
    if (!selectedChannelId) {
      setVideos([]);
      return;
    }

    const abortController = new AbortController();
    setVideosLoading(true);
    setVideosError(null);

    fetchVideosForChannel(selectedChannelId, abortController.signal)
      .then((data) => setVideos(data))
      .catch((error) => {
        if (error instanceof Error && error.name !== "AbortError") {
          setVideosError(error.message);
        }
      })
      .finally(() => setVideosLoading(false));

    return () => abortController.abort();
  }, [selectedChannelId]);

  const selectedChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannelId) ?? null,
    [channels, selectedChannelId]
  );

  useEffect(() => {
    if (selectedChannelId) {
      const channelStillExists = channels.some(
        (channel) => channel.id === selectedChannelId
      );
      if (!channelStillExists) {
        setSelectedChannelId(channels[0]?.id ?? null);
      }
    }
  }, [channels, selectedChannelId]);

  const handleChannelSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedHandle = handleInput.trim();
    if (!trimmedHandle) {
      setSubmitStatus({ type: "error", message: "Please enter a channel handle." });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const newChannel = await createChannel(trimmedHandle);
      setChannels((previous) => {
        const withoutDuplicate = previous.filter(
          (channel) => channel.id !== newChannel.id
        );
        return [newChannel, ...withoutDuplicate];
      });
      setHandleInput("");
      setSubmitStatus({
        type: "success",
        message: `Channel “${newChannel.title}” added successfully.`,
      });
      setSelectedChannelId(newChannel.id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to add channel.";
      setSubmitStatus({ type: "error", message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>ChooseYourTube</h1>
        <div className="channel-list" role="navigation" aria-label="Channels">
          {channelsLoading && <p>Loading channels…</p>}
          {channelsError && <p role="alert">{channelsError}</p>}
          {!channelsLoading && !channelsError && channels.length === 0 && (
            <p>No channels added yet.</p>
          )}
          {!channelsLoading &&
            !channelsError &&
            channels.map((channel) => {
              const isActive = channel.id === selectedChannelId;
              return (
                <button
                  key={channel.id}
                  type="button"
                  className={`channel-item${isActive ? " active" : ""}`}
                  onClick={() => setSelectedChannelId(channel.id)}
                >
                  <div className="channel-item-title">{channel.title}</div>
                  <div className="channel-item-meta">
                    {channel.handle ? `@${channel.handle}` : "Untitled handle"} · {" "}
                    {channel.total_videos} videos
                  </div>
                </button>
              );
            })}
        </div>
      </aside>

      <main className="main-content">
        <section className="add-channel-card" aria-labelledby="add-channel-heading">
          <h2 id="add-channel-heading">Add a YouTube channel</h2>
          <p>
            Paste the channel handle (for example, <strong>@GoogleDevelopers</strong>) to
            add it to your library. Videos are fetched in the background shortly after the
            channel is added.
          </p>

          <form onSubmit={handleChannelSubmit}>
            <label htmlFor="channel-handle" className="sr-only">
              Channel handle
            </label>
            <input
              id="channel-handle"
              type="text"
              placeholder="Enter a channel handle"
              value={handleInput}
              onChange={(event) => setHandleInput(event.target.value)}
              disabled={isSubmitting}
              autoComplete="off"
            />
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding…" : "Add channel"}
            </button>
          </form>
          {submitStatus && (
            <p
              className={`status-message ${submitStatus.type === "error" ? "error" : "success"}`}
              role={submitStatus.type === "error" ? "alert" : "status"}
            >
              {submitStatus.message}
            </p>
          )}
        </section>

        <section aria-labelledby="all-channels-heading">
          <h2 id="all-channels-heading">All channels</h2>
          {channelsLoading && <p>Loading channels…</p>}
          {channelsError && <p role="alert">{channelsError}</p>}
          {!channelsLoading && !channelsError && channels.length === 0 && (
            <p>Once you add channels they will appear here.</p>
          )}
          {!channelsLoading && !channelsError && channels.length > 0 && (
            <div className="channels-grid">
              {channels.map((channel) => (
                <article key={channel.id} className="channel-card">
                  {channel.thumbnail_url ? (
                    <img src={channel.thumbnail_url} alt="Channel thumbnail" />
                  ) : null}
                  <h3>{channel.title}</h3>
                  <p>{channel.description ?? "No description available."}</p>
                  <p>
                    <strong>{channel.total_videos}</strong> videos · Added {" "}
                    {formatPublishedDate(channel.created_at)}
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>

        {selectedChannel && (
          <section className="videos-section" aria-labelledby="videos-heading">
            <div className="videos-header">
              <div>
                <h2 id="videos-heading">Videos from {selectedChannel.title}</h2>
                <p>
                  Showing {videos.length} video{videos.length === 1 ? "" : "s"}. Latest
                  refresh may take a moment after adding a channel.
                </p>
              </div>
            </div>

            {videosLoading && <p>Loading videos…</p>}
            {videosError && <p role="alert">{videosError}</p>}
            {!videosLoading && !videosError && videos.length === 0 && (
              <p>No videos found for this channel yet.</p>
            )}
            {!videosLoading && !videosError && videos.length > 0 && (
              <div className="videos-list">
                {videos.map((video) => (
                  <article key={video.id} className="video-card">
                    {video.thumbnail_url ? (
                      <img src={video.thumbnail_url} alt="Video thumbnail" />
                    ) : (
                      <div
                        style={{
                          height: "0",
                          paddingBottom: "56.25%",
                          background: "linear-gradient(135deg, #93c5fd, #3b82f6)",
                        }}
                      />
                    )}
                    <div className="video-card-content">
                      <h3>{video.title}</h3>
                      <time dateTime={video.published_at}>
                        Published {formatPublishedDate(video.published_at)}
                      </time>
                      {video.description && <p>{video.description}</p>}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
