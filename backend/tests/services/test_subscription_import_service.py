import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import ApplicationError
from app.db.crud import crud_subscription_import as _crud_subscription_import
from app.db.models.channel import Channel as ChannelModel
from app.db.models.folder import Folder as FolderModel
from app.db.models.tag import Tag as TagModel
from app.schemas.subscription_import import (
    CandidateSelectionUpdate,
    SubscriptionImportCommit,
)
from app.services import subscription_import_service as _service


CHANNEL_A = "UC" + "a" * 22
CHANNEL_B = "UC" + "b" * 22
CHANNEL_C = "UC" + "c" * 22
TEST_OWNER_ID = "10000000-0000-0000-0000-000000000099"
OTHER_OWNER_ID = "20000000-0000-0000-0000-000000000099"


class _OwnerProxy:
    def __init__(self, target, owned_methods):
        self._target = target
        self._owned_methods = owned_methods

    def __getattr__(self, name):
        value = getattr(self._target, name)
        if name not in self._owned_methods:
            return value

        async def call(*args, **kwargs):
            if "owner_id" in kwargs:
                kwargs["owner_id"] = (
                    OTHER_OWNER_ID
                    if kwargs["owner_id"] == "another-owner"
                    else TEST_OWNER_ID
                )
            if name == "get_owned_import" and len(args) >= 3:
                args = (
                    *args[:2],
                    OTHER_OWNER_ID if args[2] == "another-owner" else TEST_OWNER_ID,
                    *args[3:],
                )
            return await value(*args, **kwargs)

        return call


service = _OwnerProxy(
    _service,
    {
        "collect_csv",
        "consume_oauth_state",
        "create_oauth_import",
        "defer_execution",
        "enqueue_run",
        "execute_import",
        "fail_execution",
        "get_detail",
        "get_owned_import",
        "prepare_commit",
        "store_oauth_candidates",
        "update_selection",
    },
)
crud_subscription_import = _OwnerProxy(
    _crud_subscription_import, {"list_candidates"}
)


def Channel(**kwargs):
    if "owner_id" in kwargs:
        kwargs["owner_id"] = TEST_OWNER_ID
    return ChannelModel(**kwargs)


def Folder(**kwargs):
    if "owner_id" in kwargs:
        kwargs["owner_id"] = TEST_OWNER_ID
    return FolderModel(**kwargs)


def Tag(**kwargs):
    if "owner_id" in kwargs:
        kwargs["owner_id"] = TEST_OWNER_ID
    return TagModel(**kwargs)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        (CHANNEL_A, CHANNEL_A),
        (f" https://www.youtube.com/channel/{CHANNEL_A} ", CHANNEL_A),
        (f"http://m.youtube.com/channel/{CHANNEL_B}", CHANNEL_B),
        ("ftp://youtube.com/channel/" + CHANNEL_A, None),
        ("https://example.com/channel/" + CHANNEL_A, None),
        ("https://youtube.com/@unsupported", None),
        ("https://youtube.com/channel/not-an-id", None),
    ],
)
def test_channel_id_normalization(value, expected):
    assert service.normalize_channel_id(value) == expected


@pytest.mark.parametrize(
    ("value", "expected", "unsafe"),
    [
        (None, None, False),
        ("   ", None, False),
        ("=formula", None, True),
        ("+formula", None, True),
        ("safe title", "safe", False),
    ],
)
def test_safe_csv_display_values(value, expected, unsafe):
    assert service._safe_display(value, maximum=4) == (expected, unsafe)


def takeout_csv(*rows: tuple[str, str, str]) -> bytes:
    lines = ["Channel Id,Channel Url,Channel Title"]
    lines.extend(",".join(row) for row in rows)
    return ("\ufeff" + "\n".join(lines)).encode()


@pytest.mark.asyncio
async def test_csv_preview_preserves_valid_rows_and_classifies_existing(db_session):
    db_session.add(
        Channel(
            owner_id="owner",
            id=CHANNEL_B,
            title="Existing",
            handle="existing",
            uploads_playlist_id="UUexisting",
        )
    )
    await db_session.commit()
    record = await service.collect_csv(
        db_session,
        owner_id="owner",
        payload=takeout_csv(
            (CHANNEL_A, "", "New channel"),
            ("", f"https://youtube.com/channel/{CHANNEL_B}", "Existing channel"),
            (CHANNEL_A, "", "Duplicate"),
            ("", "https://youtube.com/@unsupported", "=unsafe"),
        ),
    )

    assert record.status == "ready"
    assert (record.candidate_count, record.new_count, record.existing_count) == (4, 1, 1)
    assert record.invalid_count == 2
    invalid, _ = await crud_subscription_import.list_candidates(
        db_session,
        import_id=record.id,
        owner_id="owner",
        state="invalid",
    )
    assert any("duplicated" in (candidate.message or "") for candidate in invalid)
    assert all(candidate.channel_title != "=unsafe" for candidate in invalid)


@pytest.mark.asyncio
async def test_csv_limits_and_headers_are_safe_errors(db_session):
    with pytest.raises(ApplicationError, match="2 MB") as too_large:
        await service.collect_csv(
            db_session, owner_id="owner", payload=b"x" * (service.MAX_CSV_BYTES + 1)
        )
    assert too_large.value.code == "IMPORT_FILE_TOO_LARGE"

    with pytest.raises(ApplicationError) as missing_headers:
        await service.collect_csv(
            db_session, owner_id="owner", payload=b"Title,Something\nA,B"
        )
    assert missing_headers.value.code == "IMPORT_CSV_HEADERS"

    too_many_rows = "Channel Id\n" + "\n".join([CHANNEL_A] * (service.MAX_CSV_ROWS + 1))
    with pytest.raises(ApplicationError) as row_limit:
        await service.collect_csv(
            db_session, owner_id="owner", payload=too_many_rows.encode()
        )
    assert row_limit.value.code == "IMPORT_ROW_LIMIT"

    with pytest.raises(ApplicationError) as encoding:
        await service.collect_csv(db_session, owner_id="owner", payload=b"\xff\xfe")
    assert encoding.value.code == "IMPORT_CSV_ENCODING"

    with pytest.raises(ApplicationError) as no_header:
        await service.collect_csv(db_session, owner_id="owner", payload=b"")
    assert no_header.value.code == "IMPORT_CSV_HEADERS"


@pytest.mark.asyncio
async def test_oauth_state_is_hashed_expiring_and_one_use(db_session):
    record, raw_state = await service.create_oauth_import(db_session, owner_id="owner")
    assert record.oauth_state_hash != raw_state
    assert len(record.oauth_state_hash or "") == 64

    consumed = await service.consume_oauth_state(db_session, raw_state)
    assert consumed.id == record.id
    with pytest.raises(ApplicationError) as replay:
        await service.consume_oauth_state(db_session, raw_state)
    assert replay.value.code == "OAUTH_STATE_INVALID"


@pytest.mark.asyncio
async def test_oauth_state_rejects_missing_and_expired_values(db_session):
    with pytest.raises(ApplicationError) as missing:
        await service.consume_oauth_state(db_session, "missing")
    assert missing.value.code == "OAUTH_STATE_INVALID"

    record, raw_state = await service.create_oauth_import(db_session, owner_id="owner")
    record.oauth_state_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()
    with pytest.raises(ApplicationError) as expired:
        await service.consume_oauth_state(db_session, raw_state)
    assert expired.value.code == "OAUTH_STATE_INVALID"


@pytest.mark.asyncio
async def test_oauth_candidates_deduplicate_classify_and_sanitize(db_session):
    db_session.add(
        Channel(
            owner_id="owner",
            id=CHANNEL_B,
            title="Existing",
            handle="existing-oauth",
            uploads_playlist_id="UUexisting-oauth",
        )
    )
    record, _ = await service.create_oauth_import(db_session, owner_id="owner")
    stored = await service.store_oauth_candidates(
        db_session,
        import_record=record,
        subscriptions=[
            {"channel_id": CHANNEL_A, "title": "New"},
            {"channel_id": CHANNEL_A, "title": "Duplicate"},
            {"channel_id": CHANNEL_B, "title": "Existing"},
            {"channel_id": None, "title": "=unsafe"},
        ],
    )
    assert (stored.candidate_count, stored.new_count, stored.existing_count) == (3, 1, 1)
    assert stored.invalid_count == 1
    assert stored.error_code is None

    detail = await service.get_detail(
        db_session,
        import_id=record.id,
        owner_id="owner",
        state=None,
        search=None,
        limit=2,
        offset=0,
    )
    assert detail.candidates.total == 3
    assert detail.candidates.has_more is True


@pytest.mark.asyncio
async def test_selection_commit_and_retry_are_persisted(db_session):
    record = await service.collect_csv(
        db_session,
        owner_id="owner",
        payload=takeout_csv((CHANNEL_A, "", "A"), (CHANNEL_B, "", "B")),
    )
    candidates, _ = await crud_subscription_import.list_candidates(
        db_session, import_id=record.id, owner_id="owner", state="new"
    )
    await service.update_selection(
        db_session,
        import_id=record.id,
        owner_id="owner",
        payload=CandidateSelectionUpdate(candidate_ids=[candidates[0].id], selected=True),
    )
    committed = await service.prepare_commit(
        db_session,
        import_id=record.id,
        owner_id="owner",
        payload=SubscriptionImportCommit(),
    )
    assert committed.status == "queued"
    assert committed.selected_count == 1

    with pytest.raises(ApplicationError) as hidden:
        await service.get_owned_import(db_session, record.id, "another-owner")
    assert hidden.value.status_code == 404


@pytest.mark.asyncio
async def test_execute_import_batches_metadata_and_enqueues_initial_sync(
    db_session, mock_youtube_api, mock_arq_redis
):
    record = await service.collect_csv(
        db_session,
        owner_id="owner",
        payload=takeout_csv((CHANNEL_C, "", "Imported")),
    )
    candidates, _ = await crud_subscription_import.list_candidates(
        db_session, import_id=record.id, owner_id="owner", state="new"
    )
    await service.prepare_commit(
        db_session,
        import_id=record.id,
        owner_id="owner",
        payload=SubscriptionImportCommit(selected_candidate_ids=[candidates[0].id]),
    )
    mock_youtube_api.channels_list_async.return_value = {
        "items": [
            {
                "id": CHANNEL_C,
                "snippet": {
                    "title": "Imported",
                    "customUrl": "@imported",
                    "thumbnails": {},
                },
                "contentDetails": {"relatedPlaylists": {"uploads": "UUimported"}},
            }
        ]
    }

    progress = await service.execute_import(
        db_session,
        mock_arq_redis,
        mock_youtube_api,
        import_id=record.id,
        owner_id="owner",
    )

    assert progress.created == 1
    imported = await service.get_owned_import(db_session, record.id, "owner")
    assert imported.status == "succeeded"
    assert imported.imported_count == 1
    mock_youtube_api.channels_list_async.assert_awaited_once()
    assert mock_arq_redis.enqueue_job.await_count == 1


@pytest.mark.asyncio
async def test_candidate_ids_from_another_import_are_rejected(db_session):
    first = await service.collect_csv(
        db_session, owner_id="owner", payload=takeout_csv((CHANNEL_A, "", "A"))
    )
    second = await service.collect_csv(
        db_session, owner_id="owner", payload=takeout_csv((CHANNEL_B, "", "B"))
    )
    candidates, _ = await crud_subscription_import.list_candidates(
        db_session, import_id=second.id, owner_id="owner", state="new"
    )
    with pytest.raises(ApplicationError) as invalid:
        await service.update_selection(
            db_session,
            import_id=first.id,
            owner_id="owner",
            payload=CandidateSelectionUpdate(
                candidate_ids=[uuid.UUID(str(candidates[0].id))], selected=True
            ),
        )
    assert invalid.value.code == "IMPORT_CANDIDATE_INVALID"


@pytest.mark.asyncio
async def test_selection_rejects_noneditable_and_nonnew_candidates(db_session):
    record = await service.collect_csv(
        db_session, owner_id="owner", payload=takeout_csv((CHANNEL_A, "", "A"))
    )
    candidates, _ = await crud_subscription_import.list_candidates(
        db_session, import_id=record.id, owner_id="owner"
    )
    candidate = candidates[0]
    candidate.state = "existing"
    await db_session.commit()
    with pytest.raises(ApplicationError) as state_error:
        await service.update_selection(
            db_session,
            import_id=record.id,
            owner_id="owner",
            payload=CandidateSelectionUpdate(candidate_ids=[candidate.id], selected=True),
        )
    assert state_error.value.code == "IMPORT_CANDIDATE_INVALID"

    record.status = "queued"
    await db_session.commit()
    with pytest.raises(ApplicationError) as locked:
        await service.update_selection(
            db_session,
            import_id=record.id,
            owner_id="owner",
            payload=CandidateSelectionUpdate(candidate_ids=[candidate.id], selected=False),
        )
    assert locked.value.code == "IMPORT_NOT_EDITABLE"


@pytest.mark.asyncio
async def test_prepare_commit_validates_destinations_and_empty_selection(db_session):
    record = await service.collect_csv(
        db_session, owner_id="owner", payload=takeout_csv((CHANNEL_A, "", "A"))
    )
    with pytest.raises(ApplicationError) as folder_error:
        await service.prepare_commit(
            db_session,
            import_id=record.id,
            owner_id="owner",
            payload=SubscriptionImportCommit(folder_id="missing"),
        )
    assert folder_error.value.code == "IMPORT_FOLDER_INVALID"

    folder = Folder(id="folder", owner_id="owner", name="Folder")
    tag = Tag(id="tag", owner_id="owner", name="tag")
    db_session.add_all([folder, tag])
    await db_session.commit()
    with pytest.raises(ApplicationError) as tag_error:
        await service.prepare_commit(
            db_session,
            import_id=record.id,
            owner_id="owner",
            payload=SubscriptionImportCommit(folder_id=folder.id, tag_ids=[tag.id, "missing"]),
        )
    assert tag_error.value.code == "IMPORT_TAG_INVALID"

    with pytest.raises(ApplicationError) as empty:
        await service.prepare_commit(
            db_session,
            import_id=record.id,
            owner_id="owner",
            payload=SubscriptionImportCommit(folder_id=folder.id, tag_ids=[tag.id, tag.id]),
        )
    assert empty.value.code == "IMPORT_SELECTION_EMPTY"


@pytest.mark.asyncio
async def test_import_failure_state_helpers_are_owner_scoped(db_session):
    missing_id = uuid.uuid4()
    await service.fail_execution(
        db_session, import_id=missing_id, owner_id="owner", code="FAILED", message="failed"
    )
    await service.defer_execution(
        db_session, import_id=missing_id, owner_id="owner", code="RETRY", message="retry"
    )

    record = await service.collect_csv(
        db_session, owner_id="owner", payload=takeout_csv((CHANNEL_A, "", "A"))
    )
    await service.defer_execution(
        db_session, import_id=record.id, owner_id="owner", code="RETRY", message="retry"
    )
    await db_session.refresh(record)
    assert (record.status, record.error_code) == ("queued", "RETRY")
    await service.fail_execution(
        db_session, import_id=record.id, owner_id="owner", code="FAILED", message="failed"
    )
    await db_session.refresh(record)
    assert (record.status, record.error_code) == ("failed", "FAILED")


@pytest.mark.asyncio
async def test_execute_import_reports_partial_metadata_failure(
    db_session, mock_youtube_api, mock_arq_redis
):
    record = await service.collect_csv(
        db_session,
        owner_id="owner",
        payload=takeout_csv((CHANNEL_A, "", "A"), (CHANNEL_B, "", "B")),
    )
    candidates, _ = await crud_subscription_import.list_candidates(
        db_session, import_id=record.id, owner_id="owner", state="new"
    )
    await service.prepare_commit(
        db_session,
        import_id=record.id,
        owner_id="owner",
        payload=SubscriptionImportCommit(
            selected_candidate_ids=[candidate.id for candidate in candidates]
        ),
    )
    mock_youtube_api.channels_list_async.return_value = {
        "items": [
            {
                "id": CHANNEL_A,
                "snippet": {"title": "A", "customUrl": "@a", "thumbnails": {}},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU-a"}},
            }
        ]
    }
    with patch(
        "app.services.sync_service.enqueue_run",
        new=AsyncMock(side_effect=ApplicationError("QUEUE_UNAVAILABLE", "queue", 503)),
    ):
        progress = await service.execute_import(
            db_session,
            mock_arq_redis,
            mock_youtube_api,
            import_id=record.id,
            owner_id="owner",
        )
    assert (progress.created, progress.failed) == (1, 1)
    await db_session.refresh(record)
    assert record.status == "partial"
