"""Validate security-sensitive invariants in the Oracle Compose overlay."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    environment = os.environ | {
        "APP_DOMAIN": "tube.example.com",
        "ACME_EMAIL": "admin@example.com",
        "REGISTRATION_EMAIL_ALLOWLIST": "invited@example.com",
        "AUTH_SECRET": "ci-auth-secret-with-at-least-thirty-two-characters",
        "POSTGRES_PASSWORD": "ci-postgres-password-with-24-chars",
    }
    command = [
        "docker",
        "compose",
        "--env-file",
        ".env.example",
        "-f",
        "compose.yaml",
        "-f",
        "deploy/oracle/compose.yaml",
        "config",
        "--format",
        "json",
    ]
    rendered = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    services = json.loads(rendered.stdout)["services"]

    for private_service in ("backend", "frontend", "postgres", "redis"):
        assert not services[private_service].get("ports"), (
            f"{private_service} must not publish production host ports"
        )

    caddy_ports = {
        (port["target"], int(port["published"])) for port in services["caddy"]["ports"]
    }
    assert caddy_ports == {(80, 80), (443, 443)}
    assert services["backend"].get("build"), "backend must build from the checkout"
    assert services["frontend"].get("build"), "frontend must build from the checkout"
    assert services["caddy"]["image"] == "caddy:2.11.4-alpine"
    assert services["caddy"]["volumes"], "Caddy certificate storage must be persistent"
    backend_environment = services["backend"]["environment"]
    assert backend_environment["REGISTRATION_EMAIL_ALLOWLIST"] == "invited@example.com"
    assert backend_environment["REGISTRATION_ALLOWLIST_REQUIRED"] == "true"
    assert backend_environment["APP_ENV"] == "production"
    assert backend_environment["API_ORIGIN"] == "https://tube.example.com"
    assert backend_environment["API_CORS_ORIGINS"] == "https://tube.example.com"
    assert services["frontend"]["environment"]["ORIGIN"] == "https://tube.example.com"
    for service_name in ("postgres", "redis", "backend", "worker", "frontend", "caddy"):
        assert services[service_name]["restart"] == "unless-stopped"
    print("Oracle Compose security contract passed")


if __name__ == "__main__":
    main()
