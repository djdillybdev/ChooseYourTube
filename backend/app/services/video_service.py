import asyncio
import re
from dataclasses import dataclass
import feedparser  # type: ignore[import-untyped]
import httpx

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Literal, cast

from datetime import datetime, timedelta, timezone

from app.schemas.base import PaginatedResponse
from ..core.config import settings
from ..schemas.video import VideoCreate, VideoUpdate, VideoOut
from ..db.crud import crud_channel, crud_video
from ..db.session import sessionmanager
from ..db.models.video import Video
from ..db.models.user_state import UserVideoState
from ..db.tenancy import user_uuid
from ..clients.youtube import YouTubeAPI
from ..core.errors import ApplicationError
from .sync_service import SyncProgress

INITIAL_VIDEO_FETCH_LIMIT = 1000
VIDEO_BATCH_SIZE = 500

YT_RSS_BASE_URL = "https://www.youtube.com/feeds/videos.xml?channel_id="
RSS_MAX_BYTES = 2 * 1024 * 1024
RSS_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# Configurable with safe fallbacks
SHORTS_MAX_SECONDS = getattr(
    settings, "SHORTS_MAX_SECONDS", 180
)  # Shorts can be up to 3 minutes now
SHORTS_DEFAULT_TO_SHORT = getattr(settings, "SHORTS_DEFAULT_TO_SHORT", True)

_SHORTS_TAG_PATTERN = re.compile(r"(?<!\w)#?shorts?\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class RSSVideoEntry:
    """Video metadata available directly from a YouTube channel feed."""

    id: str
    title: str
    description: str | None
    thumbnail_url: str
    published_at: datetime
    is_short: bool


def parse_iso8601_duration(duration_string: str) -> int:
    """
    Parses an ISO 8601 duration string (e.g., PT4M13S) into seconds.
    """
    if not duration_string or duration_string == "P0D":
        return 0

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_string)
    if not match:
        return 0

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return int(timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds())


def _get_best_thumbnail_url(thumbnails: dict) -> str | None:
    """Helper to extract the best available thumbnail URL."""
    for quality in ["high", "medium", "default"]:
        if quality in thumbnails:
            return thumbnails[quality]["url"]
    return None


# async def _is_short(video_id: str) -> bool:
#     url = 'https://www.youtube.com/shorts/' + video_id
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     return response.status_code == 200


def _has_shorts_text_cues(snippet: dict) -> bool:
    """Detect #short / #shorts in title, description, or tags."""
    title = snippet.get("title") or ""
    desc = snippet.get("description") or ""
    tags = snippet.get("tags") or []
    if _SHORTS_TAG_PATTERN.search(title) or _SHORTS_TAG_PATTERN.search(desc):
        return True
    for t in tags:
        if _SHORTS_TAG_PATTERN.search(str(t) if t is not None else ""):
            return True
    return False


def _classify_is_short(duration_seconds: int, snippet: dict) -> bool:
    """
    API-only heuristic:
    - If duration > SHORTS_MAX_SECONDS ⇒ not a Short.
    - If #short(s) present ⇒ Short.
    - Otherwise (≤ SHORTS_MAX_SECONDS, no cues) ⇒ default via SHORTS_DEFAULT_TO_SHORT.
    """
    duration_seconds = duration_seconds or 0
    if duration_seconds > SHORTS_MAX_SECONDS:
        return False
    if _has_shorts_text_cues(snippet):
        return True
    return SHORTS_DEFAULT_TO_SHORT  # ambiguous case


def _extract_playlist_video_ids(items: list[dict[str, Any]]) -> list[str]:
    video_ids: list[str] = []
    for video_item in items:
        snippet = video_item.get("snippet", {})
        content_details = video_item.get("contentDetails", {})
        video_id = content_details.get("videoId") or snippet.get("resourceId", {}).get(
            "videoId"
        )
        if isinstance(video_id, str) and video_id:
            video_ids.append(video_id)
    return list(dict.fromkeys(video_ids))


async def fetch_initial_channel_videos(
    channel_id: str,
    db_session: AsyncSession,
    youtube_client: YouTubeAPI,
    owner_id: str,
) -> SyncProgress:
    channel = await crud_channel.get_channels(
        db_session, owner_id=owner_id, id=channel_id, first=True
    )
    if channel is None:
        raise ApplicationError("NOT_FOUND", "Channel not found.", 404)

    uploaded_videos: list[dict[str, Any]] = []
    next_page_token: str | None = None
    while len(uploaded_videos) < INITIAL_VIDEO_FETCH_LIMIT:
        response = await youtube_client.playlist_items_list_async(
            part="snippet,contentDetails",
            playlistId=channel.uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        items = response.get("items", [])
        if not isinstance(items, list) or not items:
            break
        uploaded_videos.extend(items)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    video_ids = _extract_playlist_video_ids(uploaded_videos)
    return await create_and_update_videos(
        video_ids, channel_id, db_session, youtube_client, owner_id=owner_id
    )


async def _fetch_rss_bytes(channel) -> bytes | None:
    headers: dict[str, str] = {}
    if channel.rss_etag:
        headers["If-None-Match"] = channel.rss_etag
    if channel.rss_last_modified:
        headers["If-Modified-Since"] = channel.rss_last_modified

    try:
        async with httpx.AsyncClient(
            timeout=RSS_TIMEOUT, follow_redirects=True
        ) as client:
            async with client.stream(
                "GET", YT_RSS_BASE_URL + channel.id, headers=headers
            ) as response:
                if response.status_code == 304:
                    return None
                response.raise_for_status()
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > RSS_MAX_BYTES:
                        raise ApplicationError(
                            "RSS_RESPONSE_TOO_LARGE",
                            "The channel feed was larger than the supported limit.",
                            502,
                        )
                channel.rss_etag = response.headers.get("etag")
                channel.rss_last_modified = response.headers.get("last-modified")
                return bytes(content)
    except ApplicationError:
        raise
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ApplicationError(
            "RSS_FETCH_FAILED",
            "The channel feed is temporarily unavailable.",
            503,
            retryable=True,
        ) from exc
    except httpx.HTTPStatusError as exc:
        retryable = exc.response.status_code >= 500 or exc.response.status_code == 429
        raise ApplicationError(
            "RSS_FETCH_FAILED" if retryable else "RSS_REQUEST_REJECTED",
            "The channel feed could not be loaded.",
            503 if retryable else 502,
            retryable=retryable,
        ) from exc


async def _rss_video_ids(channel) -> tuple[list[str], int]:
    content = await _fetch_rss_bytes(channel)
    if content is None:
        return [], 0
    parsed = await asyncio.to_thread(feedparser.parse, content)
    entries = parsed.get("entries") if hasattr(parsed, "get") else None
    if not isinstance(entries, list):
        entries = getattr(parsed, "entries", None)
    if not isinstance(entries, list):
        raise ApplicationError(
            "RSS_MALFORMED", "The channel feed returned malformed data.", 502
        )
    ids: list[str] = []
    malformed = 0
    for entry in entries:
        video_id = entry.get("yt_videoid") if hasattr(entry, "get") else None
        link = entry.get("link") if hasattr(entry, "get") else None
        if not isinstance(video_id, str):
            video_id = getattr(entry, "yt_videoid", None)
        if not isinstance(link, str):
            link = getattr(entry, "link", None)
        if not isinstance(video_id, str) or not isinstance(link, str):
            malformed += 1
            continue
        if "/shorts/" not in link:
            ids.append(video_id)
    if entries and not ids and malformed == len(entries):
        raise ApplicationError(
            "RSS_MALFORMED", "The channel feed returned malformed entries.", 502
        )
    return list(dict.fromkeys(ids)), malformed


def _feed_value(entry: Any, key: str) -> Any:
    if hasattr(entry, "get"):
        value = entry.get(key)
        if value is not None:
            return value
    return getattr(entry, key, None)


def _parse_rss_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _rss_timestamps_equal(left: datetime | None, right: datetime) -> bool:
    if left is None:
        return False
    if left.tzinfo is None:
        left = left.replace(tzinfo=timezone.utc)
    return left.astimezone(timezone.utc) == right.astimezone(timezone.utc)


def _parse_rss_video_entries(content: bytes) -> tuple[list[RSSVideoEntry], int]:
    parsed = feedparser.parse(content)
    entries = parsed.get("entries") if hasattr(parsed, "get") else None
    if not isinstance(entries, list):
        entries = getattr(parsed, "entries", None)
    if not isinstance(entries, list):
        raise ApplicationError(
            "RSS_MALFORMED", "The channel feed returned malformed data.", 502
        )

    videos: dict[str, RSSVideoEntry] = {}
    malformed = 0
    for entry in entries:
        video_id = _feed_value(entry, "yt_videoid")
        title = _feed_value(entry, "title") or _feed_value(entry, "media_title")
        published_at = _parse_rss_timestamp(
            _feed_value(entry, "published") or _feed_value(entry, "updated")
        )
        if (
            not isinstance(video_id, str)
            or not video_id
            or len(video_id) > 16
            or not isinstance(title, str)
            or not title
            or published_at is None
        ):
            malformed += 1
            continue

        description = _feed_value(entry, "media_description") or _feed_value(
            entry, "summary"
        )
        if not isinstance(description, str):
            description = None
        link = _feed_value(entry, "link")
        thumbnails = _feed_value(entry, "media_thumbnail")
        thumbnail_url = None
        if isinstance(thumbnails, list) and thumbnails:
            first_thumbnail = thumbnails[0]
            if hasattr(first_thumbnail, "get"):
                candidate = first_thumbnail.get("url")
                if isinstance(candidate, str) and candidate.startswith(
                    ("https://", "http://")
                ):
                    thumbnail_url = candidate
        if thumbnail_url is None:
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        shorts_text = f"{title}\n{description or ''}"
        videos[video_id] = RSSVideoEntry(
            id=video_id,
            title=title[:255],
            description=description,
            thumbnail_url=thumbnail_url,
            published_at=published_at,
            is_short=(isinstance(link, str) and "/shorts/" in link)
            or bool(_SHORTS_TAG_PATTERN.search(shorts_text)),
        )

    if entries and not videos and malformed == len(entries):
        raise ApplicationError(
            "RSS_MALFORMED", "The channel feed returned malformed entries.", 502
        )
    return list(videos.values()), malformed


async def refresh_latest_channel_videos_from_rss(
    channel_id: str,
    db_session: AsyncSession,
    owner_id: str,
) -> SyncProgress:
    """Refresh a channel using RSS metadata without calling the Data API."""

    channel = await crud_channel.get_channels(
        db_session, owner_id=owner_id, id=channel_id, first=True
    )
    if channel is None:
        raise ApplicationError("NOT_FOUND", "Channel not found.", 404)

    content = await _fetch_rss_bytes(channel)
    if content is None:
        return SyncProgress()
    entries, malformed = await asyncio.to_thread(_parse_rss_video_entries, content)

    entry_ids = [entry.id for entry in entries]
    existing = await crud_video.get_videos(db_session, owner_id=owner_id, id=entry_ids)
    existing_by_id = {video.id: video for video in existing}
    progress = SyncProgress(discovered=len(entries), skipped=malformed)

    for entry in entries:
        video = existing_by_id.get(entry.id)
        if video is None:
            db_session.add(
                Video(
                    id=entry.id,
                    channel_id=channel_id,
                    title=entry.title,
                    description=entry.description,
                    thumbnail_url=entry.thumbnail_url,
                    published_at=entry.published_at,
                    duration_seconds=None,
                    is_short=entry.is_short,
                    yt_tags=[],
                )
            )
            progress.created += 1
            continue

        metadata_unchanged = (
            video.title == entry.title
            and video.description == entry.description
            and video.thumbnail_url == entry.thumbnail_url
            and _rss_timestamps_equal(video.published_at, entry.published_at)
        )
        if metadata_unchanged:
            progress.skipped += 1
            continue
        video.title = entry.title
        video.description = entry.description
        video.thumbnail_url = entry.thumbnail_url
        video.published_at = entry.published_at
        progress.updated += 1

    await db_session.commit()
    return progress


async def refresh_latest_channel_videos(
    channel_id: str,
    db_session: AsyncSession,
    youtube_client: YouTubeAPI,
    owner_id: str,
) -> SyncProgress:
    """
    Fetch and add the latest videos for a channel
    """

    channel = await crud_channel.get_channels(
        db_session, owner_id=owner_id, id=channel_id, first=True
    )
    if channel is None:
        raise ApplicationError("NOT_FOUND", "Channel not found.", 404)
    parsed_video_ids, malformed = await _rss_video_ids(channel)
    await db_session.commit()
    if not parsed_video_ids:
        return SyncProgress(skipped=malformed)

    latest_videos = await crud_video.get_videos(
        db_session, owner_id=owner_id, channel_id=channel_id
    )
    existing_ids = {video.id for video in latest_videos}
    seen_video_ids = existing_ids.intersection(parsed_video_ids)
    if len(seen_video_ids) == len(parsed_video_ids):
        return SyncProgress(
            discovered=len(parsed_video_ids), skipped=len(parsed_video_ids) + malformed
        )
    if not seen_video_ids:
        response = await youtube_client.playlist_items_list_async(
            part="snippet,contentDetails",
            playlistId=channel.uploads_playlist_id,
            maxResults=50,
        )
        raw_items = response.get("items", [])
        video_ids_to_update = _extract_playlist_video_ids(
            raw_items if isinstance(raw_items, list) else []
        )
    else:
        video_ids_to_update = [
            video_id for video_id in parsed_video_ids if video_id not in existing_ids
        ]

    progress = await create_and_update_videos(
        video_ids_to_update, channel_id, db_session, youtube_client, owner_id=owner_id
    )
    progress.skipped += malformed
    return progress


async def create_and_update_videos(
    video_ids: list[str],
    channel_id: str,
    db_session: AsyncSession,
    youtube_client: YouTubeAPI,
    owner_id: str,
) -> SyncProgress:
    video_ids = [video_id for video_id in dict.fromkeys(video_ids) if video_id]
    if not video_ids:
        return SyncProgress()
    existing = await crud_video.get_videos(db_session, owner_id=owner_id, id=video_ids)
    existing_ids = {video.id for video in existing}
    full_video_items = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        response = await youtube_client.videos_list_async(
            part="snippet,contentDetails", id=",".join(chunk)
        )
        items = response.get("items", [])
        full_video_items.extend(items)

    videos_to_create = []

    for video_item in full_video_items:
        snippet = video_item.get("snippet", {})
        content_details = video_item.get("contentDetails", {})
        video_id = video_item.get("id")
        if not video_id:
            continue
        duration_seconds = parse_iso8601_duration(content_details.get("duration"))

        is_short = _classify_is_short(duration_seconds, snippet)

        new_video = VideoCreate(
            id=video_id,
            channel_id=channel_id,
            title=snippet.get("title"),
            description=snippet.get("description"),
            thumbnail_url=_get_best_thumbnail_url(snippet.get("thumbnails", {})),
            published_at=datetime.fromisoformat(
                snippet.get("publishedAt").replace("Z", "+00:00")
            ),
            duration_seconds=duration_seconds,
            is_short=is_short,
            yt_tags=snippet.get("tags", []),
        )

        videos_to_create.append(new_video)

    if videos_to_create:
        await crud_video.create_videos_bulk(db_session, videos_to_create)
    returned_ids = {video.id for video in videos_to_create}
    return SyncProgress(
        discovered=len(video_ids),
        created=len(returned_ids - existing_ids),
        skipped=len(existing_ids),
        failed=len(set(video_ids) - returned_ids),
    )


# Compatibility entrypoints for older queued jobs during a rolling deployment.
async def fetch_and_store_all_channel_videos_task(
    ctx: dict, channel_id: str, owner_id: str
) -> None:
    youtube_client = YouTubeAPI(api_key=settings.YOUTUBE_API_KEY, account_usage=True)
    async with sessionmanager.session() as db_session:
        try:
            await fetch_initial_channel_videos(
                channel_id, db_session, youtube_client, owner_id=owner_id
            )
        except ApplicationError as exc:
            if exc.code == "NOT_FOUND":
                return
            raise
    await ctx["redis"].enqueue_job(
        "sync_channel_playlists_task", owner_id=owner_id, channel_id=channel_id
    )


async def refresh_latest_channel_videos_task(
    ctx: dict, channel_id: str, owner_id: str
) -> None:
    youtube_client = YouTubeAPI(api_key=settings.YOUTUBE_API_KEY, account_usage=True)
    async with sessionmanager.session() as db_session:
        await refresh_latest_channel_videos(
            channel_id, db_session, youtube_client, owner_id=owner_id
        )


async def get_video_by_id(
    video_id: str, db_session: AsyncSession, owner_id: str
) -> Video:
    video = await crud_video.get_videos(
        db_session, owner_id=owner_id, id=video_id, first=True
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


async def get_all_videos(
    db_session: AsyncSession,
    owner_id: str,
    limit: int = 50,
    offset: int = 0,
    is_favorited: bool | None = None,
    is_watched: bool | None = None,
    is_short: bool | None = None,
    channel_id: str | list[str] | None = None,
    video_ids: list[str] | None = None,
    tag_id: str | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    min_duration_seconds: int | None = None,
    max_duration_seconds: int | None = None,
    q: str | None = None,
    order_by: str = "published_at",
    order_direction: Literal["asc", "desc"] = "desc",
) -> PaginatedResponse[VideoOut]:
    """
    Get all videos with optional filtering and search.

    All filters (including tag_id, date ranges, and search) are applied at the
    SQL level for accurate pagination counts.

    When a search query is active and order_by is the default "published_at",
    automatically switches to "relevance" sorting for better results.
    """
    # Auto-relevance: when searching with default sort, prefer relevance
    if q and order_by == "published_at":
        order_by = "relevance"

    total = await crud_video.count_videos(
        db_session,
        owner_id=owner_id,
        channel_id=channel_id,
        id=video_ids,
        is_favorited=is_favorited,
        is_watched=is_watched,
        is_short=is_short,
        tag_id=tag_id,
        published_after=published_after,
        published_before=published_before,
        min_duration_seconds=min_duration_seconds,
        max_duration_seconds=max_duration_seconds,
        q=q,
    )

    videos = await crud_video.get_videos(
        db_session,
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        channel_id=channel_id,
        id=video_ids,
        is_favorited=is_favorited,
        is_watched=is_watched,
        is_short=is_short,
        tag_id=tag_id,
        published_after=published_after,
        published_before=published_before,
        min_duration_seconds=min_duration_seconds,
        max_duration_seconds=max_duration_seconds,
        q=q,
    )

    return PaginatedResponse[VideoOut](
        total=total,
        items=cast(list[VideoOut], videos),
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def get_videos_for_channel(
    channel_id: str,
    db_session: AsyncSession,
    owner_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Video]:
    return await crud_video.get_videos(
        db_session, owner_id=owner_id, channel_id=channel_id, limit=limit, offset=offset
    )


async def update_video(
    video_id: str,
    payload: VideoUpdate,
    db_session: AsyncSession,
    owner_id: str,
) -> Video:
    """
    Updates a video by its ID. Allows updating favorited status, watched status, short status, and tags.
    """
    video = await crud_video.get_videos(
        db_session, owner_id=owner_id, id=video_id, first=True
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    uid = user_uuid(owner_id)
    state = video.user_state
    if payload.is_favorited is not None or payload.is_watched is not None:
        if state is None:
            state = UserVideoState(user_id=uid, video_id=video.id)
            db_session.add(state)
        if payload.is_favorited is not None:
            state.is_favorited = payload.is_favorited
            video.is_favorited = payload.is_favorited
        if payload.is_watched is not None:
            state.is_watched = payload.is_watched
            video.is_watched = payload.is_watched
        await db_session.flush()
        if not state.is_favorited and not state.is_watched:
            await db_session.delete(state)
            video.user_state = None
    if payload.is_short is not None:
        video.is_short = payload.is_short

    # Handle tag synchronization
    if payload.tag_ids is not None:
        from .tag_service import sync_entity_tags

        await sync_entity_tags(video, payload.tag_ids, db_session, owner_id=owner_id)

    return await crud_video.update_video(db_session, video)


async def delete_video_by_id(
    video_id: str, db_session: AsyncSession, owner_id: str
) -> None:
    """Delete an owned video after verifying it exists."""
    from app.core.demo_policy import DemoOperation, require_demo_safe

    require_demo_safe(DemoOperation.VIDEO_DELETE)
    # First, get the video to ensure it exists (this also handles the 404 case)
    video_to_delete = await get_video_by_id(video_id, db_session, owner_id=owner_id)

    # Now, pass the object to the CRUD layer for deletion
    await crud_video.delete_video(db_session, video_to_delete)
