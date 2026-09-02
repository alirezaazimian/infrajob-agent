from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import requests
from urllib.parse import urlparse


VALIDATION_VERSION = "m21.3.2"

STATUS_LIVE = "live"
STATUS_CLOSED = "closed"
STATUS_REVIEW = "review"
STATUS_SKIPPED = "skipped"


DEFAULT_TIMEOUT_SECONDS = 12

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36 "
        "InfraJob-Agent/1.0"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


CLOSED_PHRASES = (
    "this job is no longer available",
    "this position is no longer available",
    "this vacancy is no longer available",
    "job is no longer available",
    "position is no longer available",
    "job no longer available",
    "position no longer available",
    "job has expired",
    "job posting has expired",
    "posting has expired",
    "vacancy has expired",
    "position has been filled",
    "vacancy has been filled",
    "job has been filled",
    "no longer accepting applications",
    "not accepting applications",
    "applications are closed",
    "application period has ended",
    "application period is closed",
    "this vacancy is closed",
    "job not found",
    "position not found",
    "vacancy not found",
)


def _clean_url(value: Any) -> str:
    if not value:
        return ""

    return str(value).strip()


def _is_http_url(url: str) -> bool:
    return (
        url.startswith("https://")
        or url.startswith("http://")
    )


def _find_closed_phrase(
    body: str,
) -> str | None:
    lowered = body.lower()

    for phrase in CLOSED_PHRASES:
        if phrase in lowered:
            return phrase

    return None


GENERIC_LANDING_PATHS = {
    "",
    "/",
    "/jobs",
    "/jobs/",
    "/careers",
    "/careers/",
    "/career",
    "/career/",
    "/open-positions",
    "/open-positions/",
    "/vacancies",
    "/vacancies/",
}


def _looks_like_specific_job_url(
    url: str,
) -> bool:
    path = (
        urlparse(url).path
        or ""
    ).rstrip("/")

    if not path:
        return False

    segments = [
        segment
        for segment in path.split("/")
        if segment
    ]

    if len(segments) >= 2:
        return True

    return bool(
        re.search(
            r"\d{4,}",
            path,
        )
    )


def _redirect_collapsed_to_landing_page(
    original_url: str,
    final_url: str,
) -> bool:
    if not original_url or not final_url:
        return False

    if not _looks_like_specific_job_url(
        original_url
    ):
        return False

    final_path = (
        urlparse(final_url).path
        or ""
    )

    return (
        final_path.lower()
        in GENERIC_LANDING_PATHS
    )


def classify_http_result(
    *,
    status_code: int,
    body: str = "",
    final_url: str = "",
) -> dict:
    """
    Classify an already-fetched vacancy response.

    This function is intentionally separate from network I/O so it can
    be regression-tested without hitting a live job board.
    """

    if status_code in {404, 410}:
        return {
            "status": STATUS_CLOSED,
            "reason": (
                f"vacancy endpoint returned HTTP {status_code}"
            ),
            "review_flags": [],
            "closed_evidence": (
                f"http_status:{status_code}"
            ),
        }

    if status_code in {401, 403, 429}:
        return {
            "status": STATUS_REVIEW,
            "reason": (
                f"vacancy endpoint returned HTTP {status_code}; "
                "availability cannot be determined reliably"
            ),
            "review_flags": [
                (
                    "access was restricted or rate-limited; "
                    "do not treat the vacancy as closed"
                )
            ],
            "closed_evidence": None,
        }

    if 500 <= status_code <= 599:
        return {
            "status": STATUS_REVIEW,
            "reason": (
                f"vacancy endpoint returned server error HTTP {status_code}"
            ),
            "review_flags": [
                "temporary server failure may be masking a live vacancy"
            ],
            "closed_evidence": None,
        }

    if 200 <= status_code <= 299:
        closed_phrase = _find_closed_phrase(
            body
        )

        if closed_phrase:
            return {
                "status": STATUS_CLOSED,
                "reason": (
                    "vacancy page contains explicit closure evidence"
                ),
                "review_flags": [],
                "closed_evidence": (
                    f"page_phrase:{closed_phrase}"
                ),
            }

        return {
            "status": STATUS_LIVE,
            "reason": (
                "vacancy endpoint is reachable and no explicit "
                "closure evidence was detected"
            ),
            "review_flags": [],
            "closed_evidence": None,
        }

    return {
        "status": STATUS_REVIEW,
        "reason": (
            f"vacancy endpoint returned unexpected HTTP {status_code}"
        ),
        "review_flags": [
            "unexpected HTTP response requires manual verification"
        ],
        "closed_evidence": None,
    }


def validate_live_vacancy(
    job: dict,
    *,
    session: requests.Session | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """
    Verify whether the vacancy URL still appears to be live.

    Important:
    - HTTP 403/429/timeouts are REVIEW, never CLOSED.
    - HTTP 404/410 or explicit closure wording are CLOSED.
    - A reachable 2xx page without closure evidence is LIVE.
    """

    url = _clean_url(
        job.get("url")
    )

    base_result = {
        "version": VALIDATION_VERSION,
        "url": url,
        "status": STATUS_REVIEW,
        "http_status": None,
        "final_url": None,
        "redirected": False,
        "reason": "",
        "review_flags": [],
        "closed_evidence": None,
    }

    if not url:
        base_result.update(
            {
                "status": STATUS_REVIEW,
                "reason": (
                    "vacancy has no URL to validate"
                ),
                "review_flags": [
                    "missing vacancy URL"
                ],
            }
        )
        return base_result

    if not _is_http_url(url):
        base_result.update(
            {
                "status": STATUS_REVIEW,
                "reason": (
                    "vacancy URL is not an HTTP/HTTPS URL"
                ),
                "review_flags": [
                    "invalid vacancy URL format"
                ],
            }
        )
        return base_result

    client = session or requests.Session()

    try:
        response = client.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds,
            allow_redirects=True,
        )

    except requests.exceptions.Timeout:
        base_result.update(
            {
                "status": STATUS_REVIEW,
                "reason": (
                    "vacancy validation request timed out"
                ),
                "review_flags": [
                    "timeout prevents reliable live/closed classification"
                ],
            }
        )
        return base_result

    except requests.exceptions.ConnectionError:
        base_result.update(
            {
                "status": STATUS_REVIEW,
                "reason": (
                    "vacancy validation connection failed"
                ),
                "review_flags": [
                    "connection failure prevents reliable classification"
                ],
            }
        )
        return base_result

    except requests.exceptions.RequestException as error:
        base_result.update(
            {
                "status": STATUS_REVIEW,
                "reason": (
                    "vacancy validation request failed"
                ),
                "review_flags": [
                    f"request_error:{type(error).__name__}"
                ],
            }
        )
        return base_result

    final_url = str(
        response.url
        or url
    )

    # Avoid scanning arbitrarily huge pages. Closure indicators, when
    # present, normally appear well before this boundary.
    body = (
        response.text[:500_000]
        if response.text
        else ""
    )

    classified = classify_http_result(
        status_code=response.status_code,
        body=body,
        final_url=final_url,
    )

    redirected = (
        final_url.rstrip("/")
        != url.rstrip("/")
    )

    if (
        classified["status"] == STATUS_LIVE
        and redirected
        and _redirect_collapsed_to_landing_page(
            url,
            final_url,
        )
    ):
        classified = {
            "status": STATUS_REVIEW,
            "reason": (
                "vacancy URL redirected to a generic jobs/careers "
                "landing page; the specific posting may no longer be live"
            ),
            "review_flags": [
                (
                    "specific vacancy URL collapsed to a generic "
                    "landing page after redirect"
                )
            ],
            "closed_evidence": None,
        }

    base_result.update(
        {
            "http_status": response.status_code,
            "final_url": final_url,
            "redirected": redirected,
            **classified,
        }
    )

    return base_result


def skipped_live_validation(
    reason: str,
) -> dict:
    return {
        "version": VALIDATION_VERSION,
        "url": "",
        "status": STATUS_SKIPPED,
        "http_status": None,
        "final_url": None,
        "redirected": False,
        "reason": reason,
        "review_flags": [],
        "closed_evidence": None,
    }
