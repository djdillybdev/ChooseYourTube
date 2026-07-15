from __future__ import annotations

import asyncio
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from typing import Any

from fastapi_users.password import PasswordHelper
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshSession, User
from app.core.errors import ApplicationError
from app.db.models.association_tables import channel_tags, playlist_videos, video_tags
from app.db.models.channel import Channel
from app.db.models.folder import Folder
from app.db.models.playlist import Playlist
from app.db.models.subscription_import import (
    SubscriptionImport,
    SubscriptionImportCandidate,
)
from app.db.models.sync_run import SyncRun
from app.db.models.tag import Tag
from app.db.models.video import Video
from app.schemas.sync_run import SyncRunStatus
from app.services.sync_service import SyncProgress
from app.services.video_service import refresh_latest_channel_videos_from_rss

logger = logging.getLogger(__name__)
DEMO_MAINTENANCE_NAMESPACE = uuid.UUID("74000000-0000-0000-0000-000000000001")
HISTORICAL_RUN_IDS = (
    uuid.UUID("75000000-0000-0000-0000-000000000001"),
    uuid.UUID("75000000-0000-0000-0000-000000000002"),
)
IMPORT_ID = uuid.UUID("76000000-0000-0000-0000-000000000001")
MAINTENANCE_TIMEOUT_SECONDS = 180


def load_demo_seed() -> dict[str, Any]:
    resource = files("app.demo").joinpath("seed_v1.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def maintenance_run_id(now: datetime | None = None) -> uuid.UUID:
    day = (now or datetime.now(timezone.utc)).date().isoformat()
    return uuid.uuid5(DEMO_MAINTENANCE_NAMESPACE, f"demo-maintenance:{day}")


async def _ensure_demo_user(
    db: AsyncSession, catalog: dict[str, Any], email: str
) -> User:
    user_id = uuid.UUID(catalog["user_id"])
    user = await db.scalar(select(User).where(User.__table__.c.id == user_id))
    email_owner = await db.scalar(select(User).where(User.__table__.c.email == email))
    if email_owner is not None and email_owner.id != user_id:
        raise ApplicationError(
            "DEMO_EMAIL_CONFLICT",
            "The configured demo email already belongs to another account.",
            409,
        )
    if user is None:
        user = User(
            id=user_id,
            email=email,
            hashed_password=PasswordHelper().hash(secrets.token_urlsafe(48)),
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        db.add(user)
    else:
        user.email = email
        user.is_active = True
        user.is_superuser = False
        user.is_verified = True
    await db.flush()
    return user


async def _upsert_content(
    db: AsyncSession,
    catalog: dict[str, Any],
    owner_id: str,
    *,
    replace_existing: bool,
) -> None:
    snapshot_at = datetime.fromisoformat(catalog["snapshot_at"])
    for channel_index, definition in enumerate(catalog["channels"]):
        channel = await db.scalar(
            select(Channel).where(
                Channel.owner_id == owner_id, Channel.id == definition["id"]
            )
        )
        channel_created = channel is None
        if channel is None:
            channel = Channel(owner_id=owner_id, id=definition["id"])
            db.add(channel)
        if channel_created or replace_existing:
            channel.title = definition["title"]
            channel.handle = definition["handle"]
            channel.description = definition["description"]
            channel.uploads_playlist_id = "UU" + definition["id"][2:]
            channel.thumbnail_url = (
                f"https://i.ytimg.com/vi/{definition['videos'][0][0]}/hqdefault.jpg"
            )
            channel.last_updated = snapshot_at
        for video_index, (video_id, title, duration) in enumerate(definition["videos"]):
            video = await db.scalar(
                select(Video).where(Video.owner_id == owner_id, Video.id == video_id)
            )
            video_created = video is None
            if video is None:
                video = Video(owner_id=owner_id, id=video_id, channel_id=channel.id)
                db.add(video)
            if video_created or replace_existing:
                video.channel_id = channel.id
                video.title = title
                video.description = f"Curated demo snapshot from {channel.title}."
                video.thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                video.duration_seconds = duration
                video.is_short = duration <= 60
                video.published_at = snapshot_at - timedelta(
                    days=channel_index * 12 + video_index * 3
                )
                video.yt_tags = [definition["handle"], "demo"]
    await db.flush()


async def _reset_mutable_state(
    db: AsyncSession, catalog: dict[str, Any], owner_id: str
) -> None:
    await db.execute(
        delete(playlist_videos).where(playlist_videos.c.owner_id == owner_id)
    )
    await db.execute(delete(channel_tags).where(channel_tags.c.owner_id == owner_id))
    await db.execute(delete(video_tags).where(video_tags.c.owner_id == owner_id))
    await db.execute(delete(Playlist).where(Playlist.owner_id == owner_id))
    await db.execute(
        update(Channel)
        .where(Channel.owner_id == owner_id)
        .values(folder_id=None, is_favorited=False)
    )
    await db.execute(
        update(Folder).where(Folder.owner_id == owner_id).values(parent_id=None)
    )
    await db.execute(delete(Folder).where(Folder.owner_id == owner_id))
    await db.execute(delete(Tag).where(Tag.owner_id == owner_id))
    await db.execute(
        update(Video)
        .where(Video.owner_id == owner_id)
        .values(is_watched=False, is_favorited=False)
    )

    for definition in catalog["folders"]:
        db.add(
            Folder(
                id=definition["id"],
                owner_id=owner_id,
                name=definition["name"],
                position=definition["position"],
                parent_id=definition.get("parent_id"),
            )
        )
    for definition in catalog["tags"]:
        db.add(Tag(id=definition["id"], owner_id=owner_id, name=definition["name"]))
    await db.flush()

    for definition in catalog["channels"]:
        await db.execute(
            update(Channel)
            .where(Channel.owner_id == owner_id, Channel.id == definition["id"])
            .values(folder_id=definition["folder_id"])
        )
        for tag_id in definition["tag_ids"]:
            await db.execute(
                insert(channel_tags).values(
                    owner_id=owner_id, channel_id=definition["id"], tag_id=tag_id
                )
            )

    for video_id, tag_ids in catalog["video_tag_ids"].items():
        for tag_id in tag_ids:
            await db.execute(
                insert(video_tags).values(
                    owner_id=owner_id, video_id=video_id, tag_id=tag_id
                )
            )
    await db.execute(
        update(Video)
        .where(Video.owner_id == owner_id, Video.id.in_(catalog["watched_ids"]))
        .values(is_watched=True)
    )
    await db.execute(
        update(Video)
        .where(Video.owner_id == owner_id, Video.id.in_(catalog["favorite_ids"]))
        .values(is_favorited=True)
    )

    playlists = [
        {
            "id": "73000000-0000-0000-0000-000000000000",
            "name": "Watch Later",
            "description": "Videos saved to watch later",
            "current_position": 0,
            "video_ids": catalog["watch_later_ids"],
            "system_key": "watch_later",
            "is_system": True,
        },
        *catalog["playlists"],
    ]
    for definition in playlists:
        db.add(
            Playlist(
                id=definition["id"],
                owner_id=owner_id,
                name=definition["name"],
                description=definition["description"],
                current_position=definition["current_position"],
                is_system=definition.get("is_system", False),
                system_key=definition.get("system_key"),
                source_type="manual",
            )
        )
        await db.flush()
        for position, video_id in enumerate(definition["video_ids"]):
            await db.execute(
                insert(playlist_videos).values(
                    owner_id=owner_id,
                    playlist_id=definition["id"],
                    video_id=video_id,
                    position=position,
                )
            )


async def _ensure_portfolio_history(
    db: AsyncSession, catalog: dict[str, Any], owner_id: str
) -> None:
    now = datetime.fromisoformat(catalog["snapshot_at"])
    failed = await db.get(SyncRun, HISTORICAL_RUN_IDS[0])
    if failed is None:
        db.add(
            SyncRun(
                id=HISTORICAL_RUN_IDS[0],
                owner_id=owner_id,
                kind="channel_refresh",
                status="failed",
                channel_id="UC9-y-6csu5WGm29I7JiwpnA",
                attempt_count=1,
                error_code="UPSTREAM_TIMEOUT",
                error_message="A channel feed temporarily timed out; a later refresh recovered.",
                queued_at=now - timedelta(days=3),
                started_at=now - timedelta(days=3),
                finished_at=now - timedelta(days=3),
            )
        )
    recovered = await db.get(SyncRun, HISTORICAL_RUN_IDS[1])
    if recovered is None:
        db.add(
            SyncRun(
                id=HISTORICAL_RUN_IDS[1],
                owner_id=owner_id,
                kind="channel_refresh",
                status="succeeded",
                channel_id="UC9-y-6csu5WGm29I7JiwpnA",
                attempt_count=1,
                items_discovered=6,
                items_updated=6,
                queued_at=now - timedelta(days=2),
                started_at=now - timedelta(days=2),
                finished_at=now - timedelta(days=2),
            )
        )
    imported = await db.get(SubscriptionImport, IMPORT_ID)
    if imported is None:
        imported = SubscriptionImport(
            id=IMPORT_ID,
            owner_id=owner_id,
            source="youtube_takeout_csv",
            status="succeeded",
            candidate_count=4,
            new_count=4,
            selected_count=4,
            imported_count=4,
            created_at=now - timedelta(days=7),
            ready_at=now - timedelta(days=7),
            queued_at=now - timedelta(days=7),
            started_at=now - timedelta(days=7),
            finished_at=now - timedelta(days=7),
        )
        db.add(imported)
        await db.flush()
        for index, title in enumerate(
            ("Computerphile", "Kurzgesagt", "The Futur", "Great Art Explained")
        ):
            db.add(
                SubscriptionImportCandidate(
                    import_id=IMPORT_ID,
                    owner_id=owner_id,
                    channel_title=title,
                    state="imported",
                    source_index=index,
                )
            )


async def seed_demo(db: AsyncSession, *, email: str) -> str:
    catalog = load_demo_seed()
    user = await _ensure_demo_user(db, catalog, email)
    owner_id = str(user.id)
    await _upsert_content(db, catalog, owner_id, replace_existing=True)
    await _reset_mutable_state(db, catalog, owner_id)
    await _ensure_portfolio_history(db, catalog, owner_id)
    await db.commit()
    return owner_id


async def reset_demo_state(db: AsyncSession, *, owner_id: str) -> None:
    catalog = load_demo_seed()
    await _upsert_content(db, catalog, owner_id, replace_existing=False)
    await _reset_mutable_state(db, catalog, owner_id)
    await _ensure_portfolio_history(db, catalog, owner_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    await db.execute(
        delete(SyncRun).where(
            SyncRun.owner_id == owner_id,
            SyncRun.finished_at < cutoff,
            SyncRun.id.not_in(HISTORICAL_RUN_IDS),
        )
    )
    await db.commit()


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    result = await db.execute(
        delete(RefreshSession).where(
            RefreshSession.expires_at <= datetime.now(timezone.utc)
        )
    )
    await db.commit()
    return int(result.rowcount or 0)


async def refresh_curated_channels_from_rss(owner_id: str) -> SyncProgress:
    progress = SyncProgress()
    catalog = load_demo_seed()
    from app.db.session import sessionmanager

    async with asyncio.timeout(MAINTENANCE_TIMEOUT_SECONDS):
        for definition in catalog["channels"]:
            try:
                async with sessionmanager.session() as db:
                    channel_progress = await refresh_latest_channel_videos_from_rss(
                        definition["id"], db, owner_id=owner_id
                    )
                    progress.add(channel_progress)
            except Exception:
                progress.failed += 1
                logger.exception(
                    "demo_channel_refresh_failed",
                    extra={"owner_id": owner_id, "channel_id": definition["id"]},
                )
    return progress


def apply_progress(run: SyncRun, progress: SyncProgress) -> None:
    run.items_discovered += progress.discovered
    run.items_created += progress.created
    run.items_updated += progress.updated
    run.items_skipped += progress.skipped
    run.items_failed += progress.failed


def finish_run(
    run: SyncRun,
    status: SyncRunStatus,
    *,
    code: str | None = None,
    message: str | None = None,
) -> None:
    run.status = status.value
    run.error_code = code
    run.error_message = message
    run.finished_at = datetime.now(timezone.utc)
    run.updated_at = run.finished_at
