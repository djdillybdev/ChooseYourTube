import arq
from fastapi import HTTPException, status
from .core.config import settings


# This function will be used as a dependency to get the arq client
async def get_arq_redis():
    """
    Creates and returns an arq Redis client.
    This will be used via dependency injection in your routes.
    """
    if not settings.BACKGROUND_JOBS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED_IN_DEMO",
                "message": "External refresh is disabled in the demo; data is maintained daily.",
                "retryable": False,
            },
        )
    return await arq.create_pool(settings.get_redis_settings())
