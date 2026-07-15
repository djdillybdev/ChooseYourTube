from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.db.models.channel import Channel
from app.db.models.video import Video
from app.core.errors import ApplicationError
from app.services.video_service import (
    RSS_MAX_BYTES,
    _fetch_rss_bytes,
    _parse_rss_video_entries,
    _rss_video_ids,
    refresh_latest_channel_videos_from_rss,
)


@pytest.fixture
async def channel(db_session):
    row = Channel(
        id="UC_rss",
        handle="rss",
        title="RSS",
        uploads_playlist_id="UU_rss",
        rss_etag='"old"',
        rss_last_modified="Mon, 13 Jul 2026 10:00:00 GMT",
    )
    db_session.add(row)
    await db_session.commit()
    return row


@pytest.mark.asyncio
async def test_rss_uses_conditionals_and_stores_response_metadata(channel):
    seen_headers = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(
            200,
            content=b"<feed></feed>",
            headers={"etag": '"new"', "last-modified": "Tue, 14 Jul 2026 10:00:00 GMT"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with patch("app.services.video_service.httpx.AsyncClient", return_value=client):
        content = await _fetch_rss_bytes(channel)

    assert content == b"<feed></feed>"
    assert seen_headers["if-none-match"] == '"old"'
    assert channel.rss_etag == '"new"'


@pytest.mark.asyncio
async def test_rss_304_is_successful_no_change(channel):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(304)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with patch("app.services.video_service.httpx.AsyncClient", return_value=client):
        assert await _fetch_rss_bytes(channel) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (404, "RSS_REQUEST_REJECTED", False),
        (429, "RSS_FETCH_FAILED", True),
        (503, "RSS_FETCH_FAILED", True),
    ],
)
async def test_rss_classifies_http_failures(channel, status, code, retryable):
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, request=request)
        )
    )
    with (
        patch("app.services.video_service.httpx.AsyncClient", return_value=client),
        pytest.raises(ApplicationError) as error,
    ):
        await _fetch_rss_bytes(channel)
    assert error.value.code == code
    assert error.value.retryable is retryable


@pytest.mark.asyncio
async def test_rss_timeout_is_retryable(channel):
    async def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow feed", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(timeout))
    with (
        patch("app.services.video_service.httpx.AsyncClient", return_value=client),
        pytest.raises(ApplicationError) as error,
    ):
        await _fetch_rss_bytes(channel)
    assert error.value.code == "RSS_FETCH_FAILED"
    assert error.value.retryable is True


@pytest.mark.asyncio
async def test_rss_rejects_oversized_response(channel):
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, request=request, content=b"x" * (RSS_MAX_BYTES + 1)
            )
        )
    )
    with (
        patch("app.services.video_service.httpx.AsyncClient", return_value=client),
        pytest.raises(ApplicationError) as error,
    ):
        await _fetch_rss_bytes(channel)
    assert error.value.code == "RSS_RESPONSE_TOO_LARGE"


@pytest.mark.asyncio
async def test_rss_rejects_missing_entries_and_malformed_only_entries(channel):
    with (
        patch(
            "app.services.video_service._fetch_rss_bytes",
            new=AsyncMock(return_value=b"feed"),
        ),
        patch("app.services.video_service.feedparser.parse", return_value={}),
        pytest.raises(ApplicationError) as missing,
    ):
        await _rss_video_ids(channel)
    assert missing.value.code == "RSS_MALFORMED"

    with (
        patch(
            "app.services.video_service._fetch_rss_bytes",
            new=AsyncMock(return_value=b"feed"),
        ),
        patch(
            "app.services.video_service.feedparser.parse",
            return_value={"entries": [{"title": "missing id"}]},
        ),
        pytest.raises(ApplicationError) as malformed,
    ):
        await _rss_video_ids(channel)
    assert malformed.value.code == "RSS_MALFORMED"


@pytest.mark.asyncio
async def test_rss_deduplicates_videos_skips_shorts_and_counts_bad_entries(channel):
    parsed = {
        "entries": [
            {"yt_videoid": "video-1", "link": "https://youtube.com/watch?v=video-1"},
            {"yt_videoid": "video-1", "link": "https://youtube.com/watch?v=video-1"},
            {"yt_videoid": "short-1", "link": "https://youtube.com/shorts/short-1"},
            {"link": "https://youtube.com/watch?v=missing"},
        ]
    }
    with (
        patch(
            "app.services.video_service._fetch_rss_bytes",
            new=AsyncMock(return_value=b"feed"),
        ),
        patch("app.services.video_service.feedparser.parse", return_value=parsed),
    ):
        video_ids, malformed = await _rss_video_ids(channel)
    assert video_ids == ["video-1"]
    assert malformed == 1


def test_rss_entry_parser_uses_feed_metadata_and_safe_fallbacks():
    parsed = {
        "entries": [
            {
                "yt_videoid": "video-1",
                "title": "A regular upload",
                "summary": "Feed description",
                "media_thumbnail": [{"url": "https://img.example/video-1.jpg"}],
                "published": "2026-07-14T12:30:00+00:00",
                "link": "https://youtube.com/watch?v=video-1",
            },
            {
                "yt_videoid": "short-1",
                "title": "A compact explanation #Shorts",
                "published": "2026-07-15T09:00:00Z",
                "link": "https://youtube.com/watch?v=short-1",
            },
            {"yt_videoid": "missing-metadata"},
        ]
    }
    with patch("app.services.video_service.feedparser.parse", return_value=parsed):
        videos, malformed = _parse_rss_video_entries(b"feed")

    assert malformed == 1
    assert videos[0].description == "Feed description"
    assert videos[0].thumbnail_url == "https://img.example/video-1.jpg"
    assert videos[0].published_at == datetime(2026, 7, 14, 12, 30, tzinfo=timezone.utc)
    assert videos[0].is_short is False
    assert videos[1].thumbnail_url.endswith("/short-1/hqdefault.jpg")
    assert videos[1].is_short is True


def test_rss_entry_parser_reads_youtube_atom_shape():
    content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:yt="http://www.youtube.com/xml/schemas/2015"
          xmlns:media="http://search.yahoo.com/mrss/">
      <entry>
        <yt:videoId>atom-video</yt:videoId>
        <title>Atom upload</title>
        <link rel="alternate" href="https://www.youtube.com/watch?v=atom-video"/>
        <published>2026-07-15T10:00:00+00:00</published>
        <media:group>
          <media:description>Atom description</media:description>
          <media:thumbnail url="https://i.ytimg.com/vi/atom-video/hqdefault.jpg"/>
        </media:group>
      </entry>
    </feed>
    """

    videos, malformed = _parse_rss_video_entries(content)

    assert malformed == 0
    assert len(videos) == 1
    assert videos[0].id == "atom-video"
    assert videos[0].description == "Atom description"
    assert videos[0].thumbnail_url.endswith("/atom-video/hqdefault.jpg")


@pytest.mark.asyncio
async def test_rss_only_refresh_upserts_metadata_and_preserves_user_state(
    db_session, channel
):
    existing = Video(
        owner_id="test-user",
        id="video-1",
        channel_id=channel.id,
        title="Old title",
        description="Old description",
        thumbnail_url="https://img.example/old.jpg",
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        duration_seconds=90,
        is_short=True,
        is_favorited=True,
        is_watched=True,
        yt_tags=["kept"],
    )
    db_session.add(existing)
    await db_session.commit()
    parsed = {
        "entries": [
            {
                "yt_videoid": "video-1",
                "title": "Updated from RSS",
                "summary": "Updated description",
                "media_thumbnail": [{"url": "https://img.example/new.jpg"}],
                "published": "2026-07-14T12:30:00Z",
                "link": "https://youtube.com/watch?v=video-1",
            },
            {
                "yt_videoid": "video-2",
                "title": "Created from RSS",
                "published": "2026-07-15T12:30:00Z",
                "link": "https://youtube.com/watch?v=video-2",
            },
            {"title": "Malformed"},
        ]
    }

    with (
        patch(
            "app.services.video_service._fetch_rss_bytes",
            new=AsyncMock(return_value=b"feed"),
        ),
        patch("app.services.video_service.feedparser.parse", return_value=parsed),
    ):
        first = await refresh_latest_channel_videos_from_rss(channel.id, db_session)
        second = await refresh_latest_channel_videos_from_rss(channel.id, db_session)

    await db_session.refresh(existing)
    created = await db_session.get(Video, ("test-user", "video-2"))
    assert first.discovered == 2
    assert first.created == 1
    assert first.updated == 1
    assert first.skipped == 1
    assert second.created == 0
    assert second.updated == 0
    assert second.skipped == 3
    assert existing.title == "Updated from RSS"
    assert existing.is_favorited is True
    assert existing.is_watched is True
    assert existing.is_short is True
    assert existing.yt_tags == ["kept"]
    assert created is not None
    assert created.duration_seconds is None


@pytest.mark.asyncio
async def test_rss_only_refresh_treats_not_modified_as_success(channel, db_session):
    with patch(
        "app.services.video_service._fetch_rss_bytes",
        new=AsyncMock(return_value=None),
    ):
        progress = await refresh_latest_channel_videos_from_rss(channel.id, db_session)
    assert progress.discovered == 0
    assert progress.failed == 0
