import requests

from app.collectors.greenhouse import (
    fetch_greenhouse_jobs,
)

from app.collectors.personio import (
    fetch_personio_jobs,
)

from app.collectors.lever import (
    fetch_lever_jobs,
)

from app.collectors.ashby import (
    fetch_ashby_jobs,
)


SUPPORTED_ATS = {
    "greenhouse",
    "personio",
    "lever",
    "ashby",
}


def build_result(
    ats,
    identifier,
    verified=False,
    reachable=False,
    job_count=0,
    status="unknown",
    reason=None,
):
    return {
        "ats": ats,
        "identifier": identifier,
        "verified": verified,
        "reachable": reachable,
        "job_count": job_count,
        "status": status,
        "reason": reason,
    }


def classify_http_error(
    error,
):
    response = error.response

    if response is None:
        return (
            "http_error",
            "HTTP request failed",
        )

    status_code = (
        response.status_code
    )

    if status_code == 404:
        return (
            "invalid_identifier",
            "ATS source was not found",
        )

    if status_code in {
        401,
        403,
    }:
        return (
            "access_blocked",
            (
                f"ATS returned "
                f"HTTP {status_code}"
            ),
        )

    if status_code == 429:
        return (
            "rate_limited",
            "ATS rate limit reached",
        )

    if status_code >= 500:
        return (
            "upstream_error",
            (
                f"ATS returned "
                f"HTTP {status_code}"
            ),
        )

    return (
        "http_error",
        (
            f"ATS returned "
            f"HTTP {status_code}"
        ),
    )


def fetch_source_jobs(
    ats,
    identifier,
    options=None,
):
    options = (
        options
        or {}
    )

    if ats == "greenhouse":
        return fetch_greenhouse_jobs(
            identifier
        )

    if ats == "personio":
        language = options.get(
            "language",
            "en",
        )

        return fetch_personio_jobs(
            identifier,
            language=language,
        )

    if ats == "lever":
        region = options.get(
            "region",
            "global",
        )

        return fetch_lever_jobs(
            identifier,
            region=region,
        )

    if ats == "ashby":
        return fetch_ashby_jobs(
            identifier
        )

    raise ValueError(
        f"Unsupported ATS: {ats}"
    )


def verify_source(
    ats,
    identifier,
    options=None,
):
    normalized_ats = (
        ats
        .strip()
        .lower()
    )

    normalized_identifier = (
        identifier
        .strip()
    )

    if normalized_ats not in SUPPORTED_ATS:
        return build_result(
            normalized_ats,
            normalized_identifier,
            status="unsupported_ats",
            reason=(
                f"Unsupported ATS: "
                f"{normalized_ats}"
            ),
        )

    if not normalized_identifier:
        return build_result(
            normalized_ats,
            normalized_identifier,
            status="invalid_identifier",
            reason=(
                "Source identifier "
                "is empty"
            ),
        )

    try:
        jobs = fetch_source_jobs(
            normalized_ats,
            normalized_identifier,
            options=options,
        )

    except requests.exceptions.HTTPError as error:
        (
            status,
            reason,
        ) = classify_http_error(
            error
        )

        return build_result(
            normalized_ats,
            normalized_identifier,
            verified=False,
            reachable=(
                error.response
                is not None
            ),
            status=status,
            reason=reason,
        )

    except requests.exceptions.Timeout:
        return build_result(
            normalized_ats,
            normalized_identifier,
            verified=False,
            reachable=False,
            status="timeout",
            reason=(
                "ATS request timed out"
            ),
        )

    except requests.exceptions.ConnectionError:
        return build_result(
            normalized_ats,
            normalized_identifier,
            verified=False,
            reachable=False,
            status="connection_error",
            reason=(
                "Could not connect "
                "to ATS"
            ),
        )

    except ValueError as error:
        return build_result(
            normalized_ats,
            normalized_identifier,
            verified=False,
            reachable=True,
            status="invalid_response",
            reason=str(
                error
            ),
        )

    if not isinstance(
        jobs,
        list,
    ):
        return build_result(
            normalized_ats,
            normalized_identifier,
            verified=False,
            reachable=True,
            status="invalid_response",
            reason=(
                "ATS response did not "
                "contain a job list"
            ),
        )

    # --------------------------------------------------
    # A reachable ATS board with zero open jobs is still
    # a valid source.
    #
    # Empty board != invalid source.
    # --------------------------------------------------

    if not jobs:
        return build_result(
            normalized_ats,
            normalized_identifier,
            verified=True,
            reachable=True,
            job_count=0,
            status="verified_empty",
            reason=(
                "Source is valid but "
                "currently has no jobs"
            ),
        )

    return build_result(
        normalized_ats,
        normalized_identifier,
        verified=True,
        reachable=True,
        job_count=len(
            jobs
        ),
        status="verified",
        reason=None,
    )