"""Helpers for resilient third-party API handling.

The project intentionally keeps these helpers dependency-light so they can inspect
exceptions from Cohere/httpx without depending on one exact SDK exception class.
"""

from __future__ import annotations

from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any


RETRYABLE_STATUS_CODES = {
    408,
    409,
    425,
    429,
    500,
    502,
    503,
    504,
}


QUOTA_MARKERS = (
    "trial key",
    "api calls / month",
    "api calls/month",
    "monthly quota",
    "monthly limit",
    "quota exceeded",
    "quota has been reached",
    "billing quota",
    "insufficient quota",
)


TRANSIENT_MARKERS = (
    "timed out",
    "timeout",
    "temporarily unavailable",
    "connection reset",
    "connection aborted",
    "connection refused",
    "network error",
    "server error",
    "service unavailable",
)


def status_code_from_exception(error: BaseException) -> int | None:
    """Return an HTTP-like status code when one is available."""

    status_code = getattr(error, "status_code", None)

    if isinstance(status_code, int):
        return status_code

    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)

    if isinstance(response_status, int):
        return response_status

    return None


def headers_from_exception(error: BaseException) -> dict[str, Any]:
    """Best-effort extraction of response headers from SDK exceptions."""

    headers = getattr(error, "headers", None)

    if headers:
        try:
            return dict(headers)
        except Exception:
            pass

    response = getattr(error, "response", None)
    response_headers = getattr(response, "headers", None)

    if response_headers:
        try:
            return dict(response_headers)
        except Exception:
            pass

    return {}


def normalized_error_text(error: BaseException) -> str:
    """Normalize an exception to text for provider-agnostic classification."""

    parts = [str(error)]

    body = getattr(error, "body", None)
    if body:
        parts.append(str(body))

    message = getattr(error, "message", None)
    if message:
        parts.append(str(message))

    return " ".join(parts).lower()


def is_quota_exhausted(error: BaseException) -> bool:
    """Return True for non-transient provider quota/billing exhaustion."""

    if status_code_from_exception(error) != 429:
        return False

    text = normalized_error_text(error)
    return any(marker in text for marker in QUOTA_MARKERS)


def is_rate_limited(error: BaseException) -> bool:
    return status_code_from_exception(error) == 429


def is_auth_error(error: BaseException) -> bool:
    return status_code_from_exception(error) in {401, 403}


def is_retryable_provider_error(error: BaseException) -> bool:
    """Return True only when another short retry can reasonably succeed."""

    if is_quota_exhausted(error):
        return False

    status_code = status_code_from_exception(error)

    if status_code is not None:
        return status_code in RETRYABLE_STATUS_CODES

    text = normalized_error_text(error)
    return any(marker in text for marker in TRANSIENT_MARKERS)


def retry_after_seconds(
    error: BaseException,
    default: float,
    maximum: float = 20.0,
) -> float:
    """Read Retry-After when supplied, otherwise return a bounded default."""

    headers = {
        str(key).lower(): value
        for key, value in headers_from_exception(error).items()
    }

    raw_value = headers.get("retry-after")

    if raw_value is None:
        return max(0.0, min(float(default), maximum))

    try:
        return max(0.0, min(float(raw_value), maximum))
    except (TypeError, ValueError):
        pass

    try:
        retry_at = parsedate_to_datetime(str(raw_value))

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)

        seconds = (
            retry_at
            - datetime.now(timezone.utc)
        ).total_seconds()

        return max(0.0, min(seconds, maximum))
    except Exception:
        return max(0.0, min(float(default), maximum))


def public_failure_reason(error: BaseException) -> str:
    """Return a safe, coarse reason suitable for UI behavior."""

    if is_quota_exhausted(error):
        return "quota"

    if is_rate_limited(error):
        return "rate_limit"

    if is_auth_error(error):
        return "configuration"

    return "unavailable"
