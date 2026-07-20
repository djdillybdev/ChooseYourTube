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
        "CHOOSEYOURTUBE_VERSION": "1.0.0",
        "CADDY_VERSION": "2.11.4",
    }
    command = [
        "docker",
        "compose",
        "--env-file",
        ".env.example",
        "-f",
        "compose.yaml",
        "-f",
        "compose.release.yaml",
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
    assert services["backend"]["image"].endswith(":1.0.0")
    assert services["frontend"]["image"].endswith(":1.0.0")
    assert services["caddy"]["image"] == "caddy:2.11.4-alpine"
    assert services["caddy"]["volumes"], "Caddy certificate storage must be persistent"
    print("Oracle Compose security contract passed")


if __name__ == "__main__":
    main()
