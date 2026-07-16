#!/usr/bin/env python3
"""Exercise the deployed demo through its public HTTP surface."""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


EXPECTED_DEMO_CHANNEL_IDS = {
    "UCsXVk37bltHxD1rDPwtNM8Q",
    "UCq8ZAAsI89IoJ-fn1gYpO3g",
    "UCzR-rom72PHN9Zg7RML9EbA",
    "UCsBjURrPoezykLs9EqgamOA",
    "UC4eYXhJI4-7wSWc8UNRwD4A",
    "UC7_gcs09iThXybpVgjHZ_7g",
    "UCKy1dAqELo0zrOtPkf0eTMw",
}


def request_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with opener.open(request) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"{method} {url} returned {response.status}")
        return json.loads(response.read() or b"{}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", required=True, help="Public SvelteKit origin")
    parser.add_argument("--backend", required=True, help="Public FastAPI origin")
    args = parser.parse_args()
    frontend = args.frontend.rstrip("/")
    backend = args.backend.rstrip("/")
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar())
    )

    ready = request_json(opener, f"{backend}/health/ready")
    assert ready["status"] == "ready"
    request_json(opener, f"{frontend}/api/meta")
    request_json(opener, f"{frontend}/api/auth/demo", method="POST")

    channels = request_json(
        opener, f"{frontend}/api/backend/channels?limit=100&offset=0"
    )
    channel_ids = {item["id"] for item in channels.get("items", [])}
    assert channel_ids == EXPECTED_DEMO_CHANNEL_IDS, (
        "Deployed demo channels do not match the v2 catalog"
    )

    videos = request_json(opener, f"{frontend}/api/backend/videos?limit=20&offset=0")
    items = videos.get("items", [])
    assert items, "Seeded inbox returned no videos"
    search_terms = re.findall(r"[A-Za-z0-9]{4,}", items[0]["title"])
    assert search_terms, "Newest seeded video title had no searchable term"
    search_term = max(search_terms, key=len)
    search = request_json(
        opener,
        f"{frontend}/api/backend/videos?{urllib.parse.urlencode({'q': search_term, 'limit': 10})}",
    )
    assert search.get("items"), "Seeded search returned no videos"

    watch_later = request_json(opener, f"{frontend}/api/backend/playlists/watch-later")
    existing = set(watch_later.get("video_ids", []))
    candidate = next((item["id"] for item in items if item["id"] not in existing), None)
    assert candidate, "No video was available for the Watch Later smoke test"
    request_json(
        opener,
        f"{frontend}/api/backend/playlists/watch-later/videos/{candidate}",
        method="PUT",
    )
    request_json(
        opener,
        f"{frontend}/api/backend/playlists/watch-later/videos/{candidate}",
        method="DELETE",
    )
    print("Production demo smoke test passed.")


if __name__ == "__main__":
    main()
