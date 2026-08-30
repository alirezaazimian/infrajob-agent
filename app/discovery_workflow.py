from app.ats_detector import (
    detect_ats_source,
)

from app.discovery_registry import (
    add_discovered_source,
    get_all_discovered_sources,
    get_discovered_source,
    load_discovery_registry,
    save_discovery_registry,
    update_discovery_status,
    utc_now_iso,
)

from app.source_verifier import (
    verify_source,
)


VERIFIED_RESULTS = {
    "verified",
    "verified_empty",
}


PERMANENT_REJECTION_RESULTS = {
    "invalid_identifier",
    "unsupported_ats",
}


TEMPORARY_FAILURE_RESULTS = {
    "access_blocked",
    "rate_limited",
    "timeout",
    "connection_error",
    "upstream_error",
    "http_error",
    "invalid_response",
}


def store_verification_result(
    source_id,
    verification_result,
):
    config = (
        load_discovery_registry()
    )

    for source in config[
        "sources"
    ]:
        if source[
            "id"
        ] != source_id:
            continue

        metadata = source.setdefault(
            "metadata",
            {},
        )

        metadata[
            "last_verification"
        ] = {
            "checked_at": (
                utc_now_iso()
            ),
            "verified": (
                verification_result.get(
                    "verified",
                    False,
                )
            ),
            "reachable": (
                verification_result.get(
                    "reachable",
                    False,
                )
            ),
            "status": (
                verification_result.get(
                    "status"
                )
            ),
            "job_count": (
                verification_result.get(
                    "job_count",
                    0,
                )
            ),
            "reason": (
                verification_result.get(
                    "reason"
                )
            ),
        }

        save_discovery_registry(
            config
        )

        return source

    raise KeyError(
        f"Discovery source not found: "
        f"{source_id}"
    )


def register_source_from_url(
    company,
    market,
    source_url,
    discovered_via="manual_url",
    metadata=None,
):
    detection = detect_ats_source(
        source_url
    )

    ats = detection[
        "ats"
    ]

    identifier = (
        detection.get(
            "identifier"
        )
        or "unknown"
    )

    source_metadata = dict(
        metadata
        or {}
    )

    source_metadata[
        "ats_detection"
    ] = {
        "confidence": (
            detection.get(
                "confidence"
            )
        ),
        "detected_url": (
            detection.get(
                "url"
            )
        ),
    }

    source = add_discovered_source(
        company=company,
        ats=ats,
        identifier=identifier,
        market=market,
        discovered_via=(
            discovered_via
        ),
        source_url=source_url,
        metadata=source_metadata,
    )

    return source


def verify_discovered_source(
    source_id,
):
    source = get_discovered_source(
        source_id
    )

    if source is None:
        raise KeyError(
            f"Discovery source not found: "
            f"{source_id}"
        )

    current_status = source[
        "status"
    ]

    if current_status in {
        "verified",
        "promoted",
        "rejected",
    }:
        return {
            "source": source,
            "verification": None,
            "action": "skipped",
        }

    update_discovery_status(
        source_id,
        "verifying",
    )

    metadata = source.get(
        "metadata",
        {},
    )

    options = metadata.get(
        "options",
        {},
    )

    verification = verify_source(
        source[
            "ats"
        ],
        source[
            "identifier"
        ],
        options=options,
    )

    store_verification_result(
        source_id,
        verification,
    )

    result_status = verification[
        "status"
    ]

    if result_status in VERIFIED_RESULTS:
        updated_source = (
            update_discovery_status(
                source_id,
                "verified",
            )
        )

        return {
            "source": updated_source,
            "verification": verification,
            "action": "verified",
        }

    if (
        result_status
        in PERMANENT_REJECTION_RESULTS
    ):
        updated_source = (
            update_discovery_status(
                source_id,
                "rejected",
                rejection_reason=(
                    verification.get(
                        "reason"
                    )
                    or result_status
                ),
            )
        )

        return {
            "source": updated_source,
            "verification": verification,
            "action": "rejected",
        }

    if (
        result_status
        in TEMPORARY_FAILURE_RESULTS
    ):
        updated_source = (
            get_discovered_source(
                source_id
            )
        )

        return {
            "source": updated_source,
            "verification": verification,
            "action": "pending",
        }

    updated_source = (
        get_discovered_source(
            source_id
        )
    )

    return {
        "source": updated_source,
        "verification": verification,
        "action": "pending",
    }


def process_pending_sources():
    results = []

    sources = (
        get_all_discovered_sources()
    )

    for source in sources:
        if source[
            "status"
        ] not in {
            "discovered",
            "verifying",
        }:
            continue

        result = (
            verify_discovered_source(
                source[
                    "id"
                ]
            )
        )

        results.append(
            result
        )

    return results


def summarize_workflow_results(
    results,
):
    summary = {
        "verified": 0,
        "rejected": 0,
        "pending": 0,
        "skipped": 0,
    }

    for result in results:
        action = result.get(
            "action",
            "pending",
        )

        if action not in summary:
            summary[
                action
            ] = 0

        summary[
            action
        ] += 1

    return summary