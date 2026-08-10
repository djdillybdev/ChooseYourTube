"""Create deterministic browser-test data in an isolated E2E database."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi_users.password import PasswordHelper
from sqlalchemy import select

from app.auth.models import User
from app.db.models.channel import Channel
from app.db.models.association_tables import playlist_videos, video_tags
from app.db.models.folder import Folder
from app.db.models.playlist import Playlist
from app.db.models.tag import Tag
from app.db.models.video import Video
from app.db.session import sessionmanager
from app.services.playlist_service import ensure_watch_later
from app.services.tag_service import sync_entity_tags


PASSWORD = "Phase6-password-2026!"
USERS = (
    (uuid.UUID("10000000-0000-0000-0000-000000000001"), "phase6-one@example.com"),
    (uuid.UUID("10000000-0000-0000-0000-000000000002"), "phase6-two@example.com"),
)


async def seed_user(user_id: uuid.UUID, email: str) -> None:
    owner_id = str(user_id)
    async with sessionmanager.session() as db:
        user = await db.scalar(select(User).where(User.id == user_id))
        if user is None:
            user = User(
                id=user_id,
                email=email,
                hashed_password=PasswordHelper().hash(PASSWORD),
                is_active=True,
                is_superuser=False,
                is_verified=True,
            )
            db.add(user)

        channel_id = "UC" + ("1" if user_id == USERS[0][0] else "2") * 22
        channel = await db.scalar(
            select(Channel).where(Channel.id == channel_id)
        )
        if channel is None:
            folder = Folder(
                id=str(uuid.uuid5(user_id, "folder")),
                owner_id=owner_id,
                name="Engineering",
            )
            tag = Tag(
                id=str(uuid.uuid5(user_id, "tag")), owner_id=owner_id, name="portfolio"
            )
            db.add_all([folder, tag])
            await db.flush()
            channel = Channel(
                owner_id=owner_id,
                id=channel_id,
                title=f"Phase 6 Channel {email[7]}",
                handle=f"phase6-{email[7]}",
                description="Deterministic full-stack browser fixture",
                uploads_playlist_id="UU" + channel_id[2:],
                folder_id=folder.id,
            )
            db.add(channel)
            now = datetime.now(timezone.utc)
            videos = [
                Video(
                    owner_id=owner_id,
                    id=f"p6{email[7]}video{index}",
                    channel_id=channel_id,
                    title=f"Phase 6 portfolio video {index}",
                    description="Browser automation fixture",
                    published_at=now - timedelta(days=index),
                    duration_seconds=45 if index == 1 else 240 + index,
                    is_short=index == 1,
                    is_watched=index == 2,
                    is_favorited=index == 3,
                    tags=[tag] if index == 1 else [],
                )
                for index in range(1, 5)
            ]
            db.add_all(videos)
            playlist = Playlist(
                id=str(uuid.uuid5(user_id, "playlist")),
                owner_id=owner_id,
                name="Phase 6 Playlist",
            )
            db.add(playlist)
            await db.flush()
            await sync_entity_tags(channel, [tag.id], db, owner_id)
            await db.execute(
                playlist_videos.insert(),
                [
                    {
                        "user_id": user_id,
                        "playlist_id": playlist.id,
                        "video_id": video.id,
                        "position": position,
                    }
                    for position, video in enumerate(videos[:2])
                ],
            )
            for video in videos[:1]:
                await db.execute(
                    video_tags.insert().values(
                        user_id=user_id, video_id=video.id, tag_id=tag.id
                    )
                )
        await db.commit()

    async with sessionmanager.session() as db:
        watch_later = await ensure_watch_later(db, owner_id=owner_id)
        first_video = await db.scalar(
            select(Video).where(Video.channel_id == channel_id).order_by(Video.id)
        )
        if first_video is not None and first_video not in watch_later.videos:
            watch_later.videos.append(first_video)
            await db.commit()


async def main() -> None:
    for user_id, email in USERS:
        await seed_user(user_id, email)
    await sessionmanager.close()
    print("Seeded deterministic Phase 6 E2E users and content")


if __name__ == "__main__":
    asyncio.run(main())
