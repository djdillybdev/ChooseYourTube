import asyncio
from typing import Dict, Any, Iterator, Optional
from contextlib import contextmanager

import googleapiclient.discovery  # type: ignore[import-untyped]
import googleapiclient.errors  # type: ignore[import-untyped]

from ..core.config import settings
from ..core.errors import ApplicationError


class YouTubeAPI:
    """
    A helper class to interact with the YouTube Data API using the
    googleapiclient.discovery library.

    Uses an API key for public read-only data. Web OAuth imports use the
    dedicated, short-lived client in ``youtube_oauth.py``.
    """

    def __init__(
        self,
        api_service_name: str = "youtube",
        api_version: str = "v3",
        api_key: Optional[str] = None,
        account_usage: bool = False,
    ):
        """
        Initialize a YouTube client using an API key.

        :param api_service_name: The name of the Google API service, defaults to "youtube".
        :param api_version: The version of the API, defaults to "v3".
        :param api_key: A public API key for read-only access to public resources.
        """
        self.account_usage = account_usage
        if api_key is not None:
            # Build using an API key (sufficient for public data).
            self.youtube = googleapiclient.discovery.build(
                api_service_name, api_version, developerKey=api_key
            )
        else:
            raise ValueError(
                "Must provide an api_key."
            )

    def channels_list(self, **kwargs):
        return self.youtube.channels().list(**kwargs).execute()

    def playlist_items_list(self, **kwargs):
        return self.youtube.playlistItems().list(**kwargs).execute()

    def playlists_list(self, **kwargs):
        return self.youtube.playlists().list(**kwargs).execute()

    def videos_list(self, **kwargs):
        return self.youtube.videos().list(**kwargs).execute()

    async def _execute_async(self, operation: str, execute):
        usage_date = None
        if self.account_usage:
            from app.services.youtube_usage_service import reserve_quota

            usage_date = await reserve_quota(operation)
        try:
            response = await asyncio.to_thread(execute)
        except googleapiclient.errors.HttpError as exc:
            if usage_date is not None:
                from app.services.youtube_usage_service import finalize_quota

                await finalize_quota(usage_date, operation, "failed")
            status = getattr(exc.resp, "status", None)
            error_text = str(exc).lower()
            if status == 403 and any(
                marker in error_text
                for marker in ("quotaexceeded", "dailylimitexceeded", "quota exceeded")
            ):
                raise ApplicationError(
                    "YOUTUBE_QUOTA_EXHAUSTED",
                    "YouTube refresh is temporarily unavailable because the daily quota was reached.",
                    429,
                    retryable=False,
                ) from exc
            if status == 429:
                raise ApplicationError(
                    "YOUTUBE_RATE_LIMITED",
                    "YouTube is temporarily rate limiting refreshes.",
                    503,
                    retryable=True,
                ) from exc
            if status in {500, 502, 503, 504}:
                raise ApplicationError(
                    "YOUTUBE_UPSTREAM_ERROR",
                    "YouTube is temporarily unavailable.",
                    503,
                    retryable=True,
                ) from exc
            if status in {401, 403}:
                raise ApplicationError(
                    "YOUTUBE_AUTH_INVALID",
                    "YouTube credentials are invalid or not authorized.",
                    502,
                    retryable=False,
                ) from exc
            raise ApplicationError(
                "YOUTUBE_REQUEST_FAILED",
                "YouTube could not complete the request.",
                502,
                retryable=False,
            ) from exc
        except (TimeoutError, ConnectionError) as exc:
            if usage_date is not None:
                from app.services.youtube_usage_service import finalize_quota

                await finalize_quota(usage_date, operation, "failed")
            raise ApplicationError(
                "UPSTREAM_TIMEOUT",
                "YouTube did not respond in time.",
                503,
                retryable=True,
            ) from exc
        if usage_date is not None:
            from app.services.youtube_usage_service import finalize_quota

            await finalize_quota(usage_date, operation, "succeeded")
        return response

    async def channels_list_async(self, **kwargs):
        return await self._execute_async(
            "channels.list", self.youtube.channels().list(**kwargs).execute
        )

    async def playlist_items_list_async(self, **kwargs):
        return await self._execute_async(
            "playlistItems.list", self.youtube.playlistItems().list(**kwargs).execute
        )

    async def playlists_list_async(self, **kwargs):
        return await self._execute_async(
            "playlists.list", self.youtube.playlists().list(**kwargs).execute
        )

    async def videos_list_async(self, **kwargs):
        return await self._execute_async(
            "videos.list", self.youtube.videos().list(**kwargs).execute
        )

    def get_channel_info(
        self,
        channel_id: str | None = None,
        handle: str | None = None,
        username: str | None = None,
        parts: str = "snippet,contentDetails,statistics",
    ) -> Dict[str, Any]:
        """
        Retrieves channel details for a given channel ID or username.

        :param channel_id: The channel ID (e.g., UC_xxx...).
        :param handle: The channel handle
        :param username: The channel username (legacy).
        :param parts: The parts to request, default snippet,contentDetails,statistics.
        :return: The API response dict for the channel.
        """
        if not channel_id and not handle:
            raise ValueError(
                "You must provide either channel_id or handle or username."
            )

        request = self.youtube.channels().list(
            part=parts, id=channel_id, forHandle=handle, forUsername=username
        )
        response = request.execute()
        return response


class YouTubeAPIManager:
    def __init__(self, api_key: Optional[str] = None):
        """
        For this example, we assume an API key only (for read-only public data).
        """
        self._api_key = api_key
        self._client: Optional[YouTubeAPI] = None

    def init_client(self):
        """
        Create a single YouTubeAPI instance, stored on the manager.
        """
        if not self._api_key:
            raise ValueError("No YOUTUBE_API_KEY provided.")
        self._client = YouTubeAPI(api_key=self._api_key, account_usage=True)

    @contextmanager
    def get_client(self) -> Iterator[YouTubeAPI]:
        """
        Yield the YouTubeAPI client. This is a plain context manager, not async,
        because the google client library is generally not async.
        """
        if self._client is None:
            self.init_client()

        assert self._client is not None
        yield self._client


youtube_api_manager = YouTubeAPIManager(api_key=settings.YOUTUBE_API_KEY)


def get_youtube_api() -> YouTubeAPI:
    """
    A simple dependency that returns the global YouTubeAPI instance.
    """
    # Ensure the manager has been initialized
    if youtube_api_manager._client is None:
        youtube_api_manager.init_client()
    assert youtube_api_manager._client is not None
    return youtube_api_manager._client
