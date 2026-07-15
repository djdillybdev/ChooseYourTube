import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from fastapi_users import exceptions as fu_exceptions
from sqlalchemy import select

from app.auth.models import RefreshSession
from app.db.models.channel import Channel
from app.db.models.playlist import Playlist
from app.db.models.video import Video
from app.db.session import get_db_session
from app.main import app
from app.clients.youtube import get_youtube_api
from app.queue import get_arq_redis
from app.routers.auth_session import (
    SessionLoginRequest,
    SessionRefreshRequest,
    _hash_token,
    session_login,
    session_logout,
    session_refresh,
)


@pytest.fixture
def auth_client(db_session, mock_youtube_api, mock_arq_redis):
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_youtube_api] = lambda: mock_youtube_api
    app.dependency_overrides[get_arq_redis] = lambda: mock_arq_redis

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _register(client: TestClient, email: str, password: str = "testpassword123"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code in (201, 400)
    return response


def _login_token(
    client: TestClient, email: str, password: str = "testpassword123"
) -> str:
    response = client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestMultiUserAuth:
    async def test_protected_routes_require_auth(self, auth_client):
        response = auth_client.get("/channels/")
        assert response.status_code == 401

    async def test_users_only_see_their_own_data(self, auth_client, db_session):
        user_1_email = "user1@example.com"
        user_2_email = "user2@example.com"

        user_1 = _register(auth_client, user_1_email).json()
        user_2 = _register(auth_client, user_2_email).json()

        token_1 = _login_token(auth_client, user_1_email)
        token_2 = _login_token(auth_client, user_2_email)

        owner_1 = str(uuid.UUID(user_1["id"]))
        owner_2 = str(uuid.UUID(user_2["id"]))

        channel_1 = Channel(
            owner_id=owner_1,
            id="UC_owner_1",
            handle="owner1",
            title="Owner 1 Channel",
            uploads_playlist_id="UU_owner_1",
        )
        channel_2 = Channel(
            owner_id=owner_2,
            id="UC_owner_2",
            handle="owner2",
            title="Owner 2 Channel",
            uploads_playlist_id="UU_owner_2",
        )
        db_session.add(channel_1)
        db_session.add(channel_2)
        await db_session.commit()

        db_session.add(
            Video(
                owner_id=owner_1,
                id="video_owner_1",
                channel_id=channel_1.id,
                title="Owner 1 Video",
                description="v1",
                published_at=datetime.now(timezone.utc),
                duration_seconds=100,
                is_short=False,
            )
        )
        db_session.add(
            Video(
                owner_id=owner_2,
                id="video_owner_2",
                channel_id=channel_2.id,
                title="Owner 2 Video",
                description="v2",
                published_at=datetime.now(timezone.utc),
                duration_seconds=120,
                is_short=False,
            )
        )
        db_session.add(Playlist(id="playlist_owner_1", owner_id=owner_1, name="P1"))
        db_session.add(Playlist(id="playlist_owner_2", owner_id=owner_2, name="P2"))
        await db_session.commit()

        resp_tag_1 = auth_client.post(
            "/tags/",
            json={"name": "tag-user-1"},
            headers=_auth_headers(token_1),
        )
        assert resp_tag_1.status_code == 201

        resp_tag_2 = auth_client.post(
            "/tags/",
            json={"name": "tag-user-2"},
            headers=_auth_headers(token_2),
        )
        assert resp_tag_2.status_code == 201

        resp_folder_1 = auth_client.post(
            "/folders/",
            json={"name": "folder-user-1"},
            headers=_auth_headers(token_1),
        )
        assert resp_folder_1.status_code == 201

        resp_folder_2 = auth_client.post(
            "/folders/",
            json={"name": "folder-user-2"},
            headers=_auth_headers(token_2),
        )
        assert resp_folder_2.status_code == 201

        ch_1 = auth_client.get("/channels/", headers=_auth_headers(token_1)).json()
        ch_2 = auth_client.get("/channels/", headers=_auth_headers(token_2)).json()
        assert [c["id"] for c in ch_1["items"]] == ["UC_owner_1"]
        assert [c["id"] for c in ch_2["items"]] == ["UC_owner_2"]

        v_1 = auth_client.get("/videos/", headers=_auth_headers(token_1)).json()
        v_2 = auth_client.get("/videos/", headers=_auth_headers(token_2)).json()
        assert [v["id"] for v in v_1["items"]] == ["video_owner_1"]
        assert [v["id"] for v in v_2["items"]] == ["video_owner_2"]

        p_1 = auth_client.get("/playlists/", headers=_auth_headers(token_1)).json()
        p_2 = auth_client.get("/playlists/", headers=_auth_headers(token_2)).json()
        assert [p["id"] for p in p_1["items"]] == ["playlist_owner_1"]
        assert [p["id"] for p in p_2["items"]] == ["playlist_owner_2"]

        t_1 = auth_client.get("/tags/", headers=_auth_headers(token_1)).json()
        t_2 = auth_client.get("/tags/", headers=_auth_headers(token_2)).json()
        assert [t["name"] for t in t_1["items"]] == ["tag-user-1"]
        assert [t["name"] for t in t_2["items"]] == ["tag-user-2"]

        f_1 = auth_client.get("/folders/tree", headers=_auth_headers(token_1)).json()
        f_2 = auth_client.get("/folders/tree", headers=_auth_headers(token_2)).json()
        assert [f["name"] for f in f_1] == ["folder-user-1"]
        assert [f["name"] for f in f_2] == ["folder-user-2"]


class TestRotatingSessions:
    def test_session_login_rejects_invalid_credentials_and_demo_mode(
        self, auth_client, monkeypatch
    ):
        _register(auth_client, "session@example.com")
        invalid = auth_client.post(
            "/auth/session/login",
            json={"email": "session@example.com", "password": "wrong"},
        )
        assert invalid.status_code == 401
        assert invalid.json()["code"] == "INVALID_CREDENTIALS"

        monkeypatch.setattr("app.routers.auth_session.settings.APP_MODE", "demo")
        disabled = auth_client.post(
            "/auth/session/login",
            json={"email": "session@example.com", "password": "testpassword123"},
        )
        assert disabled.status_code == 403
        assert disabled.json()["code"] == "FEATURE_DISABLED_IN_DEMO"

    def test_session_refresh_requires_a_valid_token(self, auth_client):
        missing = auth_client.post("/auth/session/refresh", json={"refresh_token": ""})
        invalid = auth_client.post(
            "/auth/session/refresh", json={"refresh_token": "does-not-exist"}
        )
        assert missing.status_code == 401
        assert missing.json()["code"] == "REFRESH_MISSING"
        assert invalid.status_code == 401
        assert invalid.json()["code"] == "REFRESH_INVALID"

    def test_refresh_rotates_token_and_reuse_revokes_chain(self, auth_client):
        _register(auth_client, "rotate@example.com")
        login = auth_client.post(
            "/auth/session/login",
            json={"email": "rotate@example.com", "password": "testpassword123"},
            headers={"user-agent": "pytest"},
        )
        assert login.status_code == 200
        original = login.json()["refresh_token"]

        refreshed = auth_client.post(
            "/auth/session/refresh", json={"refresh_token": original}
        )
        assert refreshed.status_code == 200
        replacement = refreshed.json()["refresh_token"]
        assert replacement != original

        reused = auth_client.post(
            "/auth/session/refresh", json={"refresh_token": original}
        )
        assert reused.status_code == 401
        assert reused.json()["code"] == "SESSION_REVOKED"

        chain = auth_client.post(
            "/auth/session/refresh", json={"refresh_token": replacement}
        )
        assert chain.status_code == 401
        assert chain.json()["code"] == "SESSION_REVOKED"

    @pytest.mark.asyncio
    async def test_expired_refresh_is_revoked(self, auth_client, db_session):
        _register(auth_client, "expired@example.com")
        login = auth_client.post(
            "/auth/session/login",
            json={"email": "expired@example.com", "password": "testpassword123"},
        )
        token = login.json()["refresh_token"]
        row = await db_session.scalar(
            select(RefreshSession).where(
                RefreshSession.token_hash == _hash_token(token)
            )
        )
        assert row is not None
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db_session.commit()

        response = auth_client.post(
            "/auth/session/refresh", json={"refresh_token": token}
        )
        assert response.status_code == 401
        assert response.json()["code"] == "REFRESH_EXPIRED"

    def test_logout_is_idempotent_for_missing_unknown_and_live_tokens(
        self, auth_client
    ):
        _register(auth_client, "logout-session@example.com")
        login = auth_client.post(
            "/auth/session/login",
            json={
                "email": "logout-session@example.com",
                "password": "testpassword123",
            },
        )
        token = login.json()["refresh_token"]

        for candidate in ("", "unknown", token, token):
            response = auth_client.post(
                "/auth/session/logout", json={"refresh_token": candidate}
            )
            assert response.status_code == 200
            assert response.json() == {"ok": True}


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/auth/session/refresh",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
    )


@pytest.mark.asyncio
async def test_session_handlers_cover_inactive_and_missing_user_branches(monkeypatch):
    monkeypatch.setattr("app.routers.auth_session.settings.APP_MODE", "full")
    manager = AsyncMock()
    manager.authenticate.return_value = MagicMock(is_active=False)
    with pytest.raises(HTTPException) as inactive:
        await session_login(
            SessionLoginRequest(email="inactive@example.com", password="password"),
            _request(),
            AsyncMock(),
            manager,
        )
    assert inactive.value.status_code == 401

    active = MagicMock(is_active=True)
    manager.authenticate.return_value = active
    with patch(
        "app.routers.auth_session.issue_session",
        new=AsyncMock(return_value={"access_token": "token"}),
    ):
        result = await session_login(
            SessionLoginRequest(email="active@example.com", password="password"),
            _request(),
            AsyncMock(),
            manager,
        )
    assert result["access_token"] == "token"

    valid = MagicMock(
        revoked_at=None,
        replaced_by_id=None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        user_id=uuid.uuid4(),
    )
    db = AsyncMock()
    db.scalar.return_value = valid
    manager.get.side_effect = fu_exceptions.UserNotExists()
    with pytest.raises(HTTPException) as missing_user:
        await session_refresh(SessionRefreshRequest(refresh_token="token"), _request(), db, manager)
    assert missing_user.value.status_code == 401


@pytest.mark.asyncio
async def test_session_handlers_cover_revocation_variants_and_logout():
    manager = AsyncMock()
    db = AsyncMock()
    for revoked_at, replaced_by_id in (
        (datetime.now(timezone.utc), None),
        (None, uuid.uuid4()),
    ):
        db.scalar.return_value = MagicMock(
            revoked_at=revoked_at,
            replaced_by_id=replaced_by_id,
            session_id=uuid.uuid4(),
        )
        with pytest.raises(HTTPException) as revoked:
            await session_refresh(
                SessionRefreshRequest(refresh_token="token"), _request(), db, manager
            )
        assert revoked.value.status_code == 401

    db.scalar.return_value = None
    assert await session_logout(SessionRefreshRequest(refresh_token="unknown"), db) == {
        "ok": True
    }
    live = MagicMock(session_id=uuid.uuid4())
    db.scalar.return_value = live
    assert await session_logout(SessionRefreshRequest(refresh_token="live"), db) == {
        "ok": True
    }
