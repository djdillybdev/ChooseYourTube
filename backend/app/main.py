import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import auth_backend, fastapi_users
from app.auth.schemas import UserCreate, UserRead, UserUpdate
from app.core.config import Settings, settings
from app.core.errors import APIErrorBody, ApplicationError, safe_error_details
from app.core.observability import RequestContextMiddleware, configure_logging
from app.db.schema_guard import assert_required_playlist_schema
from app.db.session import sessionmanager
from app.routers import (
    auth_session,
    channels,
    folders,
    health,
    playlists,
    subscription_imports,
    sync_runs,
    tags,
    videos,
)

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
) -> JSONResponse:
    body = APIErrorBody(
        code=code,
        message=message,
        request_id=_request_id(request),
        retryable=retryable,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def check_database_schema_on_startup() -> None:
    if not settings.enable_startup_schema_check:
        return
    async with sessionmanager.session() as db_session:
        await assert_required_playlist_schema(db_session)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    await check_database_schema_on_startup()
    yield


def create_app(app_settings: Settings = settings) -> FastAPI:
    configure_logging(app_settings.debug_logs)
    application = FastAPI(
        title="ChooseYourTube API",
        summary="Backend API for the ChooseYourTube distraction-free YouTube reader.",
        version="0.1.0",
        license_info={"name": "GPL-3.0-only", "identifier": "GPL-3.0-only"},
        responses={
            code: {"model": APIErrorBody, "description": "Safe API error"}
            for code in (400, 401, 403, 404, 409, 422, 500)
        },
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)

    application.include_router(channels.router)
    application.include_router(videos.router)
    application.include_router(folders.router)
    application.include_router(tags.router)
    application.include_router(playlists.router)
    application.include_router(health.router)
    application.include_router(sync_runs.router)
    application.include_router(subscription_imports.router)
    application.include_router(
        fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
    )
    if app_settings.REGISTRATION_ENABLED:
        application.include_router(
            fastapi_users.get_register_router(UserRead, UserCreate),
            prefix="/auth",
            tags=["auth"],
        )
    application.include_router(
        fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
    )
    application.include_router(
        fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"]
    )
    application.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["users"],
    )
    application.include_router(auth_session.router)

    @application.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request, exc: ApplicationError
    ) -> JSONResponse:
        return _error_response(
            request, exc.status_code, exc.code, exc.message, exc.retryable
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code, message, retryable = safe_error_details(exc.status_code, exc.detail)
        return _error_response(request, exc.status_code, code, message, retryable)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info("request_validation_failed")
        return _error_response(
            request,
            422,
            "VALIDATION_ERROR",
            "The request contains invalid data.",
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_request_error")
        return _error_response(
            request,
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            retryable=False,
        )

    @application.get("/", tags=["Metadata"])
    async def root() -> dict[str, object]:
        return {
            "name": "ChooseYourTube API",
            "version": "0.1.0",
            "mode": app_settings.APP_MODE,
            "links": {
                "docs": "/docs",
                "openapi": "/openapi.json",
                "liveness": "/health/live",
                "readiness": "/health/ready",
            },
            "features": app_settings.public_features,
        }

    return application


app = create_app()
