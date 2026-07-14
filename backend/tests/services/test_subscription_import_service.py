import uuid

import pytest

from app.core.errors import ApplicationError
from app.db.crud import crud_subscription_import
from app.db.models.channel import Channel
from app.schemas.subscription_import import (
    CandidateSelectionUpdate,
    SubscriptionImportCommit,
)
from app.services import subscription_import_service as service


CHANNEL_A = "UC" + "a" * 22
CHANNEL_B = "UC" + "b" * 22
CHANNEL_C = "UC" + "c" * 22


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
