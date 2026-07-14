from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel


class APIErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    retryable: bool = False


@dataclass(slots=True)
class ApplicationError(Exception):
    code: str
    message: str
    status_code: int = 400
    retryable: bool = False


DEFAULT_ERROR_MESSAGES = {
    400: ("BAD_REQUEST", "The request could not be completed."),
    401: ("UNAUTHENTICATED", "Authentication is required."),
    403: ("FORBIDDEN", "You do not have permission to perform this action."),
    404: ("NOT_FOUND", "The requested resource was not found."),
    409: ("CONFLICT", "The request conflicts with the current resource state."),
    422: ("VALIDATION_ERROR", "The request contains invalid data."),
}


def safe_error_details(status_code: int, detail: object) -> tuple[str, str, bool]:
    default_code, default_message = DEFAULT_ERROR_MESSAGES.get(
        status_code, ("REQUEST_FAILED", "The request could not be completed.")
    )
    if not isinstance(detail, dict):
        return default_code, default_message, False

    code = detail.get("code")
    message = detail.get("message")
    retryable = detail.get("retryable", False)
    return (
        code if isinstance(code, str) else default_code,
        message if isinstance(message, str) else default_message,
        retryable if isinstance(retryable, bool) else False,
    )
