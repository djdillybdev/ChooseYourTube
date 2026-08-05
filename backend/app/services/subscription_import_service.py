from __future__ import annotations

import csv
import hashlib
import io
import re
import secrets
import uuid
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from arq.connections import ArqRedis
from fastapi import HTTPException

from app.core.errors import ApplicationError
from app.db.crud import crud_channel, crud_subscription_import
from app.db.models.folder import Folder
from app.db.models.subscription_import import (
    SubscriptionImport,
    SubscriptionImportCandidate,
)
from app.db.models.tag import Tag
from app.db.tenancy import user_uuid
from app.schemas.base import PaginatedResponse
from app.schemas.subscription_import import (
    CandidateSelectionUpdate,
    SubscriptionCandidateState,
    SubscriptionImportCandidateOut,
    SubscriptionImportCommit,
    SubscriptionImportDetailOut,
    SubscriptionImportOut,
    SubscriptionImportSource,
)
from app.schemas.sync_run import SyncRunKind
from app.clients.youtube import YouTubeAPI
from app.services.sync_service import SyncProgress

MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_CSV_ROWS = 5_000
YOUTUBE_CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
UNSAFE_SPREADSHEET_PREFIXES = ("=", "+", "-", "@")
logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def normalize_channel_id(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if YOUTUBE_CHANNEL_ID.fullmatch(candidate):
        return candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        return None
    host = parsed.netloc.lower().split(":", 1)[0]
    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        return None
    segments = [part for part in parsed.path.split("/") if part]
    if len(segments) == 2 and segments[0].lower() == "channel":
        return segments[1] if YOUTUBE_CHANNEL_ID.fullmatch(segments[1]) else None
    return None


def _safe_display(value: str | None, *, maximum: int) -> tuple[str | None, bool]:
    if not value:
        return None, False
    normalized = value.strip()
    if not normalized:
        return None, False
    if normalized.startswith(UNSAFE_SPREADSHEET_PREFIXES):
        return None, True
    return normalized[:maximum], False


async def _classify_candidates(
    db: AsyncSession,
    import_record: SubscriptionImport,
    candidates: list[SubscriptionImportCandidate],
) -> None:
    channel_ids = [candidate.channel_id for candidate in candidates if candidate.channel_id]
    existing = await crud_channel.get_channels(
        db, owner_id=import_record.owner_id, id=channel_ids
    )
    existing_ids = {channel.id for channel in existing}
    for candidate in candidates:
        if candidate.channel_id is None:
            candidate.state = "invalid"
        elif candidate.channel_id in existing_ids:
            candidate.state = "existing"
        else:
            candidate.state = "new"


async def collect_csv(
    db: AsyncSession, *, owner_id: str, payload: bytes
) -> SubscriptionImport:
    if len(payload) > MAX_CSV_BYTES:
        raise ApplicationError(
            "IMPORT_FILE_TOO_LARGE", "Takeout CSV files must be 2 MB or smaller.", 413
        )
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ApplicationError(
            "IMPORT_CSV_ENCODING", "The Takeout CSV must use UTF-8 encoding.", 422
        ) from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ApplicationError("IMPORT_CSV_HEADERS", "The CSV has no header row.", 422)
    headers = {_normalize_header(header): header for header in reader.fieldnames if header}
    id_header = headers.get("channelid")
    url_header = headers.get("channelurl")
    title_header = headers.get("channeltitle")
    if id_header is None and url_header is None:
        raise ApplicationError(
            "IMPORT_CSV_HEADERS",
            "The CSV must contain a Channel Id or Channel Url column.",
            422,
        )

    rows = list(reader)
    if len(rows) > MAX_CSV_ROWS:
        raise ApplicationError(
            "IMPORT_ROW_LIMIT", "Takeout CSV files may contain at most 5,000 rows.", 422
        )

    record = SubscriptionImport(
        user_id=user_uuid(owner_id),
        source=SubscriptionImportSource.YOUTUBE_TAKEOUT_CSV.value,
        status="collecting",
    )
    db.add(record)
    await db.flush()

    seen: set[str] = set()
    candidates: list[SubscriptionImportCandidate] = []
    for source_index, row in enumerate(rows, start=2):
        raw_id = row.get(id_header, "") if id_header else ""
        raw_url = row.get(url_header, "") if url_header else ""
        channel_id = normalize_channel_id(raw_id) or normalize_channel_id(raw_url)
        safe_title, unsafe_title = _safe_display(
            row.get(title_header) if title_header else None, maximum=255
        )
        safe_url, unsafe_url = _safe_display(raw_url, maximum=512)
        message = None
        if channel_id is None:
            message = "No supported YouTube channel ID was found in this row."
        elif channel_id in seen:
            message = "This channel is duplicated earlier in the file."
            channel_id = None
        else:
            seen.add(channel_id)
        if unsafe_title or unsafe_url:
            message = (
                f"{message} " if message else ""
            ) + "An unsafe spreadsheet-style display value was omitted."
        candidate = SubscriptionImportCandidate(
            import_id=record.id,
            channel_id=channel_id,
            channel_title=safe_title,
            channel_url=safe_url,
            state="invalid" if channel_id is None else "new",
            source_index=source_index,
            message=message,
        )
        db.add(candidate)
        candidates.append(candidate)

    await _classify_candidates(db, record, candidates)
    record.status = "ready"
    record.ready_at = _now()
    await db.flush()
    await crud_subscription_import.refresh_counts(db, record)
    await db.commit()
    await db.refresh(record)
    return record


async def create_oauth_import(
    db: AsyncSession, *, owner_id: str
) -> tuple[SubscriptionImport, str]:
    raw_state = secrets.token_urlsafe(32)
    record = SubscriptionImport(
        user_id=user_uuid(owner_id),
        source=SubscriptionImportSource.YOUTUBE_OAUTH.value,
        status="collecting",
        oauth_state_hash=hashlib.sha256(raw_state.encode()).hexdigest(),
        oauth_state_expires_at=_now() + timedelta(minutes=10),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record, raw_state


async def consume_oauth_state(
    db: AsyncSession, raw_state: str
) -> SubscriptionImport:
    state_hash = hashlib.sha256(raw_state.encode()).hexdigest()
    record = await crud_subscription_import.get_import_by_state_hash(
        db, state_hash, for_update=True
    )
    now = _now()
    expires_at = record.oauth_state_expires_at if record is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if (
        record is None
        or record.oauth_state_consumed_at is not None
        or expires_at is None
        or expires_at <= now
    ):
        await db.rollback()
        raise ApplicationError(
            "OAUTH_STATE_INVALID",
            "The Google authorization request expired or was already used.",
            400,
        )
    record.oauth_state_consumed_at = now
    await db.commit()
    return record


async def store_oauth_candidates(
    db: AsyncSession,
    *,
    import_record: SubscriptionImport,
    subscriptions: list[dict[str, str | None]],
) -> SubscriptionImport:
    seen: set[str] = set()
    candidates: list[SubscriptionImportCandidate] = []
    for source_index, subscription in enumerate(subscriptions, start=1):
        channel_id = normalize_channel_id(subscription.get("channel_id"))
        if channel_id and channel_id in seen:
            continue
        if channel_id:
            seen.add(channel_id)
        safe_title, _ = _safe_display(subscription.get("title"), maximum=255)
        candidate = SubscriptionImportCandidate(
            import_id=import_record.id,
            channel_id=channel_id,
            channel_title=safe_title,
            channel_url=(
                f"https://www.youtube.com/channel/{channel_id}" if channel_id else None
            ),
            state="invalid" if channel_id is None else "new",
            source_index=source_index,
            message=None if channel_id else "Google returned a subscription without a channel ID.",
        )
        db.add(candidate)
        candidates.append(candidate)
    await _classify_candidates(db, import_record, candidates)
    import_record.status = "ready"
    import_record.ready_at = _now()
    import_record.error_code = None
    import_record.error_message = None
    await db.flush()
    await crud_subscription_import.refresh_counts(db, import_record)
    await db.commit()
    await db.refresh(import_record)
    return import_record


async def fail_collection(
    db: AsyncSession, import_record: SubscriptionImport, code: str, message: str
) -> None:
    import_record.status = "failed"
    import_record.error_code = code
    import_record.error_message = message
    import_record.finished_at = _now()
    await db.commit()


async def get_owned_import(
    db: AsyncSession, import_id: uuid.UUID, owner_id: str
) -> SubscriptionImport:
    record = await crud_subscription_import.get_import(db, import_id, owner_id=owner_id)
    if record is None:
        raise ApplicationError("NOT_FOUND", "Subscription import not found.", 404)
    return record


async def get_detail(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    state: SubscriptionCandidateState | None,
    search: str | None,
    limit: int,
    offset: int,
) -> SubscriptionImportDetailOut:
    record = await get_owned_import(db, import_id, owner_id)
    candidates, total = await crud_subscription_import.list_candidates(
        db,
        import_id=import_id,
        owner_id=owner_id,
        state=state.value if state else None,
        search=search,
        limit=limit,
        offset=offset,
    )
    candidate_page = PaginatedResponse[SubscriptionImportCandidateOut](
            total=total,
            items=[SubscriptionImportCandidateOut.model_validate(item) for item in candidates],
            limit=limit,
            offset=offset,
            has_more=offset + len(candidates) < total,
        )
    return SubscriptionImportDetailOut.model_validate(
        {
            "import": SubscriptionImportOut.model_validate(record),
            "candidates": candidate_page,
        }
    )


async def update_selection(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    payload: CandidateSelectionUpdate,
) -> SubscriptionImport:
    record = await get_owned_import(db, import_id, owner_id)
    if record.status != "ready":
        raise ApplicationError(
            "IMPORT_NOT_EDITABLE", "This import can no longer be edited.", 409
        )
    candidates = await crud_subscription_import.get_candidates_by_ids(
        db,
        import_id=import_id,
        owner_id=owner_id,
        candidate_ids=payload.candidate_ids,
    )
    if len(candidates) != len(set(payload.candidate_ids)):
        raise ApplicationError(
            "IMPORT_CANDIDATE_INVALID", "One or more candidates are invalid.", 422
        )
    allowed = {"new", "selected"}
    if any(candidate.state not in allowed for candidate in candidates):
        raise ApplicationError(
            "IMPORT_CANDIDATE_INVALID", "Only new channels can be selected.", 422
        )
    for candidate in candidates:
        candidate.state = "selected" if payload.selected else "new"
    await db.flush()
    await crud_subscription_import.refresh_counts(db, record)
    await db.commit()
    await db.refresh(record)
    return record


async def prepare_commit(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    payload: SubscriptionImportCommit,
) -> SubscriptionImport:
    record = await get_owned_import(db, import_id, owner_id)
    if record.status not in {"ready", "partial", "failed"}:
        if record.status in {"queued", "running"}:
            return record
        raise ApplicationError("IMPORT_NOT_READY", "This import is not ready.", 409)

    if payload.folder_id is not None:
        folder = await db.scalar(
            select(Folder).where(
                Folder.id == payload.folder_id, Folder.user_id == user_uuid(owner_id)
            )
        )
        if folder is None:
            raise ApplicationError(
                "IMPORT_FOLDER_INVALID", "The destination folder is invalid.", 422
            )
    unique_tag_ids = list(dict.fromkeys(payload.tag_ids))
    if unique_tag_ids:
        tag_count = int(
            await db.scalar(
                select(func.count(Tag.id)).where(
                    Tag.user_id == user_uuid(owner_id), Tag.id.in_(unique_tag_ids)
                )
            )
            or 0
        )
        if tag_count != len(unique_tag_ids):
            raise ApplicationError(
                "IMPORT_TAG_INVALID", "One or more destination tags are invalid.", 422
            )

    if payload.selected_candidate_ids is not None:
        selected = await crud_subscription_import.get_candidates_by_ids(
            db,
            import_id=import_id,
            owner_id=owner_id,
            candidate_ids=payload.selected_candidate_ids,
        )
        if len(selected) != len(set(payload.selected_candidate_ids)) or any(
            candidate.state not in {"new", "selected", "failed"}
            for candidate in selected
        ):
            raise ApplicationError(
                "IMPORT_CANDIDATE_INVALID", "One or more candidates cannot be imported.", 422
            )
        await crud_subscription_import.replace_selection(
            db,
            import_id=import_id,
            owner_id=owner_id,
            selected_ids=payload.selected_candidate_ids,
        )
    elif record.status in {"partial", "failed"}:
        failed, _ = await crud_subscription_import.list_candidates(
            db,
            import_id=import_id,
            owner_id=owner_id,
            state="failed",
            limit=MAX_CSV_ROWS,
        )
        await crud_subscription_import.replace_selection(
            db,
            import_id=import_id,
            owner_id=owner_id,
            selected_ids=[candidate.id for candidate in failed],
        )

    await db.flush()
    await crud_subscription_import.refresh_counts(db, record)
    if record.selected_count == 0:
        raise ApplicationError(
            "IMPORT_SELECTION_EMPTY", "Select at least one new channel to import.", 422
        )
    record.destination_folder_id = payload.folder_id
    record.destination_tags = list(
        (await db.scalars(select(Tag).where(
            Tag.user_id == user_uuid(owner_id), Tag.id.in_(unique_tag_ids)
        ))).all()
    )
    record.status = "queued"
    record.queued_at = _now()
    record.started_at = None
    record.finished_at = None
    record.error_code = None
    record.error_message = None
    await db.commit()
    await db.refresh(record)
    return record


async def execute_import(
    db: AsyncSession,
    redis: ArqRedis,
    youtube_client: YouTubeAPI,
    *,
    import_id: uuid.UUID,
    owner_id: str,
) -> SyncProgress:
    """Create selected channels in bounded metadata batches."""
    from app.services import channel_service, sync_service

    record = await get_owned_import(db, import_id, owner_id)
    record.status = "running"
    record.started_at = record.started_at or _now()
    await db.commit()
    candidates = await crud_subscription_import.candidates_for_processing(
        db, import_id=import_id, owner_id=owner_id
    )
    progress = SyncProgress(discovered=len(candidates))
    metadata: dict[str, dict] = {}
    channel_ids = [candidate.channel_id for candidate in candidates if candidate.channel_id]
    for start in range(0, len(channel_ids), 50):
        response = await youtube_client.channels_list_async(
            part="snippet,contentDetails,statistics",
            id=",".join(channel_ids[start : start + 50]),
            maxResults=50,
        )
        metadata.update({item["id"]: item for item in response.get("items", [])})

    for candidate in candidates:
        if candidate.channel_id is None or candidate.channel_id not in metadata:
            candidate.state = "failed"
            candidate.message = "YouTube no longer exposes this channel."
            progress.failed += 1
            await db.commit()
            continue
        existing = await crud_channel.get_channels(
            db, owner_id=owner_id, id=candidate.channel_id, first=True
        )
        if existing is not None:
            candidate.state = "existing"
            candidate.message = "This channel is already followed."
            progress.skipped += 1
            await db.commit()
            continue
        try:
            channel = await channel_service.create_channel_from_metadata(
                metadata[candidate.channel_id],
                db,
                owner_id=owner_id,
                folder_id=record.destination_folder_id,
                tag_ids=record.destination_tag_ids,
            )
        except IntegrityError:
            await db.rollback()
            refreshed_candidate = await db.get(SubscriptionImportCandidate, candidate.id)
            assert refreshed_candidate is not None
            existing = await crud_channel.get_channels(
                db, owner_id=owner_id, id=refreshed_candidate.channel_id, first=True
            )
            if existing is not None:
                refreshed_candidate.state = "existing"
                refreshed_candidate.message = "This channel is already followed."
                progress.skipped += 1
            else:
                refreshed_candidate.state = "failed"
                refreshed_candidate.message = "The channel could not be added."
                progress.failed += 1
            await db.commit()
            continue
        except HTTPException as exc:
            if exc.status_code == 409:
                refreshed_candidate = await db.get(
                    SubscriptionImportCandidate, candidate.id
                )
                assert refreshed_candidate is not None
                refreshed_candidate.state = "existing"
                refreshed_candidate.message = "This channel is already followed."
                progress.skipped += 1
                await db.commit()
                continue
            candidate.state = "failed"
            candidate.message = "The channel could not be added."
            progress.failed += 1
            await db.commit()
            continue
        except ApplicationError as exc:
            candidate.state = "failed"
            candidate.message = exc.message
            progress.failed += 1
            await db.commit()
            continue

        candidate.state = "imported"
        candidate.message = None
        progress.created += 1
        await db.commit()
        try:
            await sync_service.enqueue_run(
                db,
                redis,
                owner_id=owner_id,
                kind=SyncRunKind.INITIAL_CHANNEL_SYNC,
                channel_id=channel.id,
            )
        except ApplicationError:
            logger.exception(
                "import_initial_sync_enqueue_failed",
                extra={
                    "owner_id": owner_id,
                    "channel_id": channel.id,
                    "subscription_import_id": str(import_id),
                },
            )

    record = await get_owned_import(db, import_id, owner_id)
    await crud_subscription_import.refresh_counts(db, record)
    record.status = (
        "partial"
        if progress.failed and (progress.created or progress.skipped)
        else "failed"
        if progress.failed
        else "succeeded"
    )
    record.finished_at = _now()
    record.error_code = "IMPORT_CANDIDATES_FAILED" if progress.failed else None
    record.error_message = (
        "Some selected channels could not be imported." if progress.failed else None
    )
    await db.commit()
    return progress


async def fail_execution(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    code: str,
    message: str,
) -> None:
    record = await crud_subscription_import.get_import(db, import_id, owner_id=owner_id)
    if record is None:
        return
    record.status = "failed"
    record.error_code = code
    record.error_message = message
    record.finished_at = _now()
    await db.commit()


async def defer_execution(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    code: str,
    message: str,
) -> None:
    record = await crud_subscription_import.get_import(db, import_id, owner_id=owner_id)
    if record is None:
        return
    record.status = "queued"
    record.error_code = code
    record.error_message = message
    await db.commit()
