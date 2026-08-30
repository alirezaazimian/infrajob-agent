from app.discovery_registry import (
    get_all_discovered_sources,
    get_discovered_source,
    get_discovered_source_by_identity,
    load_discovery_registry,
    save_discovery_registry,
    utc_now_iso,
)

from app.source_qualifier import (
    qualify_source,
)


def build_qualification_snapshot(
    result,
):
    return {
        "checked_at": (
            utc_now_iso()
        ),
        "status": (
            result[
                "qualification_status"
            ]
        ),
        "qualified": (
            result[
                "qualified"
            ]
        ),
        "reason": (
            result[
                "reason"
            ]
        ),
        "requested_market": (
            result[
                "requested_market"
            ]
        ),
        "verified_markets": (
            result.get(
                "verified_markets",
                [],
            )
        ),
        "total_jobs": (
            result.get(
                "total_jobs",
                0,
            )
        ),
        "target_role_jobs": (
            result.get(
                "target_role_jobs",
                0,
            )
        ),
        "requested_market_role_jobs": (
            result.get(
                "requested_market_role_jobs",
                0,
            )
        ),
        "enabled_market_role_jobs": (
            result.get(
                "enabled_market_role_jobs",
                0,
            )
        ),
        "unknown_country_role_jobs": (
            result.get(
                "unknown_country_role_jobs",
                0,
            )
        ),
        "country_counts": (
            result.get(
                "country_counts",
                {},
            )
        ),
        "target_role_country_counts": (
            result.get(
                "target_role_country_counts",
                {},
            )
        ),
        "role_counts": (
            result.get(
                "role_counts",
                {},
            )
        ),
        "target_role_samples": (
            result.get(
                "target_role_samples",
                [],
            )
        ),
    }


def persist_qualification_result(
    source_id,
    result,
):
    config = (
        load_discovery_registry()
    )

    snapshot = (
        build_qualification_snapshot(
            result
        )
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
            "qualification"
        ] = snapshot

        save_discovery_registry(
            config
        )

        return snapshot

    raise KeyError(
        f"Discovery source not found: "
        f"{source_id}"
    )


def qualify_and_persist_source(
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

    result = qualify_source(
        source_id
    )

    snapshot = (
        persist_qualification_result(
            source_id,
            result,
        )
    )

    return {
        "source": source,
        "result": result,
        "qualification": snapshot,
        "action": "qualified",
    }


def qualify_source_by_identity(
    ats,
    identifier,
):
    source = (
        get_discovered_source_by_identity(
            ats,
            identifier,
        )
    )

    if source is None:
        raise KeyError(
            "Discovery source not found: "
            f"{ats}/{identifier}"
        )

    return qualify_and_persist_source(
        source[
            "id"
        ]
    )


def qualify_verified_sources(
    force=False,
):
    results = []

    sources = (
        get_all_discovered_sources()
    )

    for source in sources:
        if source.get(
            "status"
        ) != "verified":
            continue

        metadata = source.get(
            "metadata",
            {},
        )

        existing = metadata.get(
            "qualification"
        )

        if (
            existing
            and not force
        ):
            results.append(
                {
                    "source": source,
                    "result": None,
                    "qualification": (
                        existing
                    ),
                    "action": "skipped",
                }
            )

            continue

        result = (
            qualify_and_persist_source(
                source[
                    "id"
                ]
            )
        )

        results.append(
            result
        )

    return results


def summarize_qualification_results(
    results,
):
    summary = {
        "qualified": 0,
        "review": 0,
        "rejected": 0,
        "skipped": 0,
    }

    for item in results:
        if item.get(
            "action"
        ) == "skipped":
            summary[
                "skipped"
            ] += 1

            continue

        qualification = item[
            "qualification"
        ]

        status = qualification[
            "status"
        ]

        if qualification[
            "qualified"
        ]:
            summary[
                "qualified"
            ] += 1

        elif status.startswith(
            "review_"
        ):
            summary[
                "review"
            ] += 1

        elif status.startswith(
            "reject_"
        ):
            summary[
                "rejected"
            ] += 1

    return summary