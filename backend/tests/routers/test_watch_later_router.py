import pytest

from app.services.playlist_service import ensure_watch_later

TEST_OWNER_ID = "10000000-0000-0000-0000-000000000099"


@pytest.mark.asyncio
async def test_watch_later_static_route_initializes_playlist(test_client, db_session):
    response = test_client.get("/playlists/watch-later")

    assert response.status_code == 200
    assert response.json()["system_key"] == "watch_later"
    assert response.json()["video_ids"] == []


@pytest.mark.asyncio
async def test_watch_later_general_mutations_are_protected(test_client, db_session):
    playlist = await ensure_watch_later(db_session, owner_id=TEST_OWNER_ID)

    rename = test_client.patch(
        f"/playlists/{playlist.id}", json={"name": "Not allowed"}
    )
    delete = test_client.delete(f"/playlists/{playlist.id}")

    assert rename.status_code == 403
    assert delete.status_code == 403
