#!/usr/bin/env python3
"""Exercise the deployed recruiter demo through its public HTTP surface."""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


def request_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(
        url, data=body, headers=headers, method=method
    )
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
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    ready = request_json(opener, f"{backend}/health/ready")
    assert ready["status"] == "ready"
    request_json(opener, f"{frontend}/api/meta")
    request_json(opener, f"{frontend}/api/auth/demo", method="POST")

    videos = request_json(opener, f"{frontend}/api/backend/videos?limit=20&offset=0")
    items = videos.get("items", [])
    assert items, "Seeded inbox returned no videos"
    search = request_json(
        opener,
        f"{frontend}/api/backend/videos?{urllib.parse.urlencode({'q': 'demo', 'limit': 10})}",
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
