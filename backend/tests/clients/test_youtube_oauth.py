from unittest.mock import MagicMock, patch

import pytest

from app.clients import youtube_oauth


def test_authorization_uses_web_flow_and_readonly_scope():
    flow = MagicMock()
    flow.authorization_url.return_value = ("https://accounts.google.test/auth", "ignored")
    with patch(
        "app.clients.youtube_oauth.google_auth_oauthlib.flow.Flow.from_client_config",
        return_value=flow,
    ) as factory:
        url = youtube_oauth.authorization_url("state-value")
    assert url == "https://accounts.google.test/auth"
    assert factory.call_args.kwargs["state"] == "state-value"
    assert factory.call_args.kwargs["scopes"] == [youtube_oauth.YOUTUBE_READONLY_SCOPE]
    flow.authorization_url.assert_called_once()


@pytest.mark.asyncio
async def test_collection_fetches_every_subscription_page():
    flow = MagicMock()
    first = {
        "items": [
            {"snippet": {"title": "One", "resourceId": {"channelId": "UC1"}}}
        ],
        "nextPageToken": "next",
    }
    second = {
        "items": [
            {"snippet": {"title": "Two", "resourceId": {"channelId": "UC2"}}}
        ]
    }
    request = MagicMock()
    request.execute.side_effect = [first, second]
    youtube = MagicMock()
    youtube.subscriptions.return_value.list.return_value = request
    with (
        patch("app.clients.youtube_oauth.build_flow", return_value=flow),
        patch(
            "app.clients.youtube_oauth.googleapiclient.discovery.build",
            return_value=youtube,
        ),
    ):
        subscriptions = await youtube_oauth.collect_subscriptions("code", "state")
    assert [item["channel_id"] for item in subscriptions] == ["UC1", "UC2"]
    assert youtube.subscriptions.return_value.list.call_count == 2
    flow.fetch_token.assert_called_once_with(code="code")
