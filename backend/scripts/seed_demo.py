"""Idempotently seed or restore the configured demo account."""

from __future__ import annotations

import asyncio

from app.core.config import settings
from app.db.session import sessionmanager
from app.services.demo_service import seed_demo


async def main() -> None:
    if settings.APP_MODE != "demo" or settings.DEMO_USER_EMAIL is None:
        raise SystemExit("APP_MODE=demo and DEMO_USER_EMAIL are required")
    async with sessionmanager.session() as db:
        owner_id = await seed_demo(db, email=str(settings.DEMO_USER_EMAIL))
    await sessionmanager.close()
    print(f"Seeded demo catalog for owner {owner_id}")


if __name__ == "__main__":
    asyncio.run(main())
