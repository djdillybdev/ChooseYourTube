from __future__ import annotations

import asyncio

import google_auth_oauthlib.flow  # type: ignore[import-untyped]
import googleapiclient.discovery  # type: ignore[import-untyped]
import googleapiclient.errors  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.errors import ApplicationError

YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"


def _client_config() -> dict[str, object]:
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }


def build_flow(*, state: str | None = None):
    return google_auth_oauthlib.flow.Flow.from_client_config(
        _client_config(),
        scopes=[YOUTUBE_READONLY_SCOPE],
        state=state,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


def authorization_url(state: str) -> str:
    flow = build_flow(state=state)
    url, _ = flow.authorization_url(
        access_type="online",
        include_granted_scopes="true",
        prompt="consent",
    )
    return str(url)


async def collect_subscriptions(code: str, state: str) -> list[dict[str, str | None]]:
    flow = build_flow(state=state)
    try:
        await asyncio.to_thread(flow.fetch_token, code=code)
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=flow.credentials, cache_discovery=False
        )
        subscriptions: list[dict[str, str | None]] = []
        page_token: str | None = None
        while True:
            request = youtube.subscriptions().list(
                part="snippet", mine=True, maxResults=50, pageToken=page_token
            )
            response = await asyncio.to_thread(request.execute)
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                subscriptions.append(
                    {
                        "channel_id": snippet.get("resourceId", {}).get("channelId"),
                        "title": snippet.get("title"),
                    }
                )
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return subscriptions
    except googleapiclient.errors.HttpError as exc:
        raise ApplicationError(
            "OAUTH_SUBSCRIPTIONS_FAILED",
            "Google could not provide the YouTube subscriptions.",
            502,
            retryable=True,
        ) from exc
    except ApplicationError:
        raise
    except Exception as exc:
        raise ApplicationError(
            "OAUTH_EXCHANGE_FAILED",
            "Google authorization could not be completed.",
            400,
        ) from exc
