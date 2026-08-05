from app.services.subscription_import_service import MAX_CSV_BYTES
from app.services import subscription_import_service


CHANNEL_ID = "UC" + "r" * 22
TEST_OWNER_ID = "10000000-0000-0000-0000-000000000099"


def test_csv_upload_returns_preview_and_owner_scoped_detail(test_client):
    response = test_client.post(
        "/imports/subscriptions/csv",
        files={
            "file": (
                "subscriptions.csv",
                f"Channel Id,Channel Url,Channel Title\n{CHANNEL_ID},,Router channel",
                "text/csv",
            )
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["import"]["new_count"] == 1
    detail = test_client.get(f"/imports/{body['import']['id']}?state=new")
    assert detail.status_code == 200
    assert detail.json()["candidates"]["items"][0]["channel_id"] == CHANNEL_ID


def test_csv_upload_enforces_streaming_size_limit(test_client):
    response = test_client.post(
        "/imports/subscriptions/csv",
        files={"file": ("large.csv", b"x" * (MAX_CSV_BYTES + 1), "text/csv")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "IMPORT_FILE_TOO_LARGE"


def test_demo_mode_rejects_subscription_imports(test_client, monkeypatch):
    monkeypatch.setattr("app.routers.subscription_imports.settings.APP_MODE", "demo")
    response = test_client.post(
        "/imports/subscriptions/csv",
        files={"file": ("subscriptions.csv", b"Channel Id\n", "text/csv")},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FEATURE_DISABLED_IN_DEMO"


async def test_oauth_denial_consumes_state_and_redirects_to_failed_import(
    test_client, db_session
):
    record, state = await subscription_import_service.create_oauth_import(
        db_session, owner_id=TEST_OWNER_ID
    )
    response = test_client.get(
        f"/imports/youtube/oauth/callback?state={state}&error=access_denied",
        follow_redirects=False,
    )
    await db_session.refresh(record)
    assert response.status_code == 303
    assert response.headers["location"].endswith(f"/settings/imports/{record.id}")
    assert record.status == "failed"
    assert record.error_code == "OAUTH_CONSENT_DENIED"
