from unittest.mock import patch

import httpx
import pytest

from app.db.models.channel import Channel
from app.services.video_service import _fetch_rss_bytes


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
