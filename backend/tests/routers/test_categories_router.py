from datetime import datetime, timezone

import pytest

from app.db.models.category import Category
from app.db.models.channel import Channel

TEST_USER_ID = "10000000-0000-0000-0000-000000000099"
OTHER_USER_ID = "10000000-0000-0000-0000-000000000098"


def make_channel(channel_id: str, owner_id: str = TEST_USER_ID) -> Channel:
    now = datetime.now(timezone.utc)
    return Channel(
        owner_id=owner_id,
        id=channel_id,
        title=f"Channel {channel_id}",
        handle=f"@{channel_id}",
        uploads_playlist_id=f"uploads-{channel_id}",
        created_at=now,
        last_updated=now,
    )


@pytest.mark.asyncio
async def test_category_crud_and_case_insensitive_uniqueness(test_client, db_session):
    created = test_client.post(
        "/categories/", json={"name": "  Games  ", "icon_key": "gamepad-2"}
    )
    assert created.status_code == 201
    category = created.json()
    assert category["name"] == "Games"
    assert category["icon_key"] == "gamepad-2"
    assert category["channel_ids"] == []

    duplicate = test_client.post("/categories/", json={"name": "games"})
    assert duplicate.status_code == 409

    renamed = test_client.patch(
        f"/categories/{category['id']}", json={"name": "Favorites"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Favorites"
    assert renamed.json()["icon_key"] == "gamepad-2"

    reiconed = test_client.patch(
        f"/categories/{category['id']}",
        json={"name": "Favorites", "icon_key": "star"},
    )
    assert reiconed.status_code == 200
    assert reiconed.json()["icon_key"] == "star"

    cleared = test_client.patch(
        f"/categories/{category['id']}",
        json={"name": "Favorites", "icon_key": None},
    )
    assert cleared.status_code == 200
    assert cleared.json()["icon_key"] is None

    listed = test_client.get("/categories/")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [category["id"]]

    deleted = test_client.delete(f"/categories/{category['id']}")
    assert deleted.status_code == 204
    assert test_client.get(f"/categories/{category['id']}").status_code == 404


@pytest.mark.asyncio
async def test_category_icon_key_is_optional_and_validated(test_client, db_session):
    created = test_client.post("/categories/", json={"name": "No Icon"})
    assert created.status_code == 201
    assert created.json()["icon_key"] is None

    malformed = test_client.post(
        "/categories/", json={"name": "Malformed", "icon_key": "Not an icon!"}
    )
    assert malformed.status_code == 422


@pytest.mark.asyncio
async def test_replace_memberships_from_both_axes(test_client, db_session):
    db_session.add_all([make_channel("channel-1"), make_channel("channel-2")])
    await db_session.commit()
    category_ids = []
    for name in ("Games", "News"):
        response = test_client.post("/categories/", json={"name": name})
        category_ids.append(response.json()["id"])

    category_response = test_client.put(
        f"/categories/{category_ids[0]}/channels",
        json={"channel_ids": ["channel-1", "channel-1", "channel-2"]},
    )
    assert category_response.status_code == 200
    assert category_response.json()["channel_ids"] == ["channel-1", "channel-2"]

    channel_response = test_client.put(
        "/categories/channels/channel-1",
        json={"category_ids": [category_ids[0], category_ids[1], category_ids[1]]},
    )
    assert channel_response.status_code == 200
    assert channel_response.json()["category_ids"] == sorted(category_ids)

    cleared = test_client.put(
        f"/categories/{category_ids[0]}/channels", json={"channel_ids": []}
    )
    assert cleared.status_code == 200
    assert cleared.json()["channel_ids"] == []
    assert test_client.get(f"/categories/{category_ids[1]}").json()["channel_ids"] == [
        "channel-1"
    ]


@pytest.mark.asyncio
async def test_membership_validation_is_atomic(test_client, db_session):
    channel = make_channel("channel-1")
    category = Category(
        id="category-1",
        owner_id=TEST_USER_ID,
        name="Games",
        normalized_name="games",
    )
    db_session.add_all([channel, category])
    await db_session.commit()

    response = test_client.put(
        "/categories/category-1/channels",
        json={"channel_ids": ["channel-1", "missing"]},
    )
    assert response.status_code == 400
    assert test_client.get("/categories/category-1").json()["channel_ids"] == []

    response = test_client.put(
        "/categories/channels/channel-1",
        json={"category_ids": ["category-1", "missing"]},
    )
    assert response.status_code == 400
    assert test_client.get("/categories/category-1").json()["channel_ids"] == []


@pytest.mark.asyncio
async def test_category_access_is_owner_scoped(test_client, db_session):
    db_session.add(
        Category(
            id="other-category",
            owner_id=OTHER_USER_ID,
            name="Private",
            normalized_name="private",
        )
    )
    await db_session.commit()

    assert test_client.get("/categories/other-category").status_code == 404
    assert test_client.patch(
        "/categories/other-category", json={"name": "Leaked"}
    ).status_code == 404
    assert test_client.delete("/categories/other-category").status_code == 404
