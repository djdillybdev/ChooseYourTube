"""Wait for a Compose stack and verify registration, login, and authentication."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("SMOKE_API_URL", "http://127.0.0.1:8000").rstrip("/")
EMAIL = os.getenv("SMOKE_EMAIL", "compose-smoke@example.com")
PASSWORD = os.getenv("SMOKE_PASSWORD", "Compose-Smoke-Password-2026!")


def request(path: str, *, method: str = "GET", body: object | None = None, token: str | None = None):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request_object = urllib.request.Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request_object, timeout=5) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        payload = error.read()
        return error.code, json.loads(payload) if payload else None


def wait_until_ready() -> None:
    deadline = time.monotonic() + 120
    last_status: object = "not started"
    while time.monotonic() < deadline:
        try:
            status, payload = request("/health/ready")
            last_status = (status, payload)
            if status == 200:
                return
        except (OSError, ValueError) as error:
            last_status = error
        time.sleep(2)
    raise RuntimeError(f"API did not become ready: {last_status}")


def main() -> int:
    wait_until_ready()
    register_status, _ = request(
        "/auth/register", method="POST", body={"email": EMAIL, "password": PASSWORD}
    )
    if register_status not in {201, 400}:
        raise RuntimeError(f"Registration failed with status {register_status}")

    login_status, session = request(
        "/auth/session/login", method="POST", body={"email": EMAIL, "password": PASSWORD}
    )
    if login_status != 200 or not isinstance(session, dict) or not session.get("access_token"):
        raise RuntimeError(f"Login failed with status {login_status}: {session}")

    me_status, user = request("/users/me", token=session["access_token"])
    if me_status != 200 or not isinstance(user, dict) or user.get("email") != EMAIL:
        raise RuntimeError(f"Authenticated request failed with status {me_status}: {user}")
    print("Compose smoke test passed: ready, registered, logged in, authenticated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise
