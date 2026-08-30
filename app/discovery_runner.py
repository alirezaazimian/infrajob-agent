import argparse

from app.candidate_extractor import (
    extract_candidates_from_search,
)

from app.discovery_queue import (
    load_runtime_config,
    mark_query_result,
    select_queries_for_run,
)

from app.discovery_workflow import (
    register_source_from_url,
    verify_discovered_source,
)

from app.search_provider import (
    search_query_record,
)


SEARCH_STATUS_MAP = {
    "success": "success",
    "no_results": "no_results",
    "rate_limited": "rate_limited",
    "error": "error",
}


def merge_candidate(
    existing,
    incoming,
    query_score,
):
    query_ids = set(
        existing.get(
            "query_ids",
            [],
        )
    )

    query_ids.update(
        incoming.get(
            "query_ids",
            [],
        )
    )

    matched_roles = set(
        existing.get(
            "matched_roles",
            [],
        )
    )

    matched_roles.update(
        incoming.get(
            "matched_roles",
            [],
        )
    )

    result_urls = set(
        existing.get(
            "result_urls",
            [],
        )
    )

    result_urls.update(
        incoming.get(
            "result_urls",
            [],
        )
    )

    existing[
        "query_ids"
    ] = sorted(
        query_ids
    )

    existing[
        "matched_roles"
    ] = sorted(
        matched_roles
    )

    existing[
        "result_urls"
    ] = sorted(
        result_urls
    )

    existing[
        "evidence_count"
    ] = len(
        result_urls
    )

    existing[
        "best_query_score"
    ] = max(
        existing.get(
            "best_query_score",
            0,
        ),
        query_score,
    )

    return existing


def collect_candidates(
    query_batch,
):
    candidates_by_key = {}

    statistics = {
        "search_success": 0,
        "search_no_results": 0,
        "search_rate_limited": 0,
        "search_errors": 0,
        "raw_results": 0,
    }

    for index, query in enumerate(
        query_batch,
        start=1,
    ):
        print()

        print(
            f"[{index}/{len(query_batch)}]"
        )

        print(
            query["query"]
        )

        search_output = (
            search_query_record(
                query
            )
        )

        search_status = (
            search_output[
                "status"
            ]
        )

        result_count = (
            search_output.get(
                "result_count",
                0,
            )
        )

        statistics[
            "raw_results"
        ] += result_count

        queue_status = (
            SEARCH_STATUS_MAP.get(
                search_status,
                "error",
            )
        )

        mark_query_result(
            query["id"],
            status=queue_status,
            result_count=result_count,
            error=search_output.get(
                "error"
            ),
        )

        if search_status == "success":
            statistics[
                "search_success"
            ] += 1

        elif search_status == (
            "no_results"
        ):
            statistics[
                "search_no_results"
            ] += 1

        elif search_status == (
            "rate_limited"
        ):
            statistics[
                "search_rate_limited"
            ] += 1

        else:
            statistics[
                "search_errors"
            ] += 1

        print(
            "Search:",
            search_status,
            "| Results:",
            result_count,
        )

        if search_status != "success":
            continue

        candidates = (
            extract_candidates_from_search(
                search_output,
                query,
                include_duplicates=False,
            )
        )

        print(
            "New ATS candidates:",
            len(candidates),
        )

        for candidate in candidates:
            key = candidate[
                "key"
            ]

            query_score = query.get(
                "score",
                0,
            )

            if key not in (
                candidates_by_key
            ):
                candidate[
                    "best_query_score"
                ] = query_score

                candidates_by_key[
                    key
                ] = candidate

                continue

            merge_candidate(
                candidates_by_key[
                    key
                ],
                candidate,
                query_score,
            )

    candidates = list(
        candidates_by_key.values()
    )

    candidates.sort(
        key=lambda item: (
            item.get(
                "best_query_score",
                0,
            ),
            item.get(
                "evidence_count",
                0,
            ),
            item.get(
                "key",
                "",
            ),
        ),
        reverse=True,
    )

    return (
        candidates,
        statistics,
    )


def register_candidates(
    candidates,
    limit,
):
    registered = []

    for candidate in candidates[
        :limit
    ]:
        metadata = {
            "discovery": {
                "query_ids": (
                    candidate.get(
                        "query_ids",
                        [],
                    )
                ),
                "matched_roles": (
                    candidate.get(
                        "matched_roles",
                        [],
                    )
                ),
                "result_urls": (
                    candidate.get(
                        "result_urls",
                        [],
                    )
                ),
                "evidence_count": (
                    candidate.get(
                        "evidence_count",
                        0,
                    )
                ),
                "best_query_score": (
                    candidate.get(
                        "best_query_score",
                        0,
                    )
                ),
                "result_title": (
                    candidate.get(
                        "result_title",
                        "",
                    )
                ),
                "result_snippet": (
                    candidate.get(
                        "result_snippet",
                        "",
                    )
                ),
            }
        }

        source = register_source_from_url(
            company=candidate[
                "company_guess"
            ],
            market=candidate[
                "market_code"
            ],
            source_url=candidate[
                "source_url"
            ],
            discovered_via=(
                "web_search"
            ),
            metadata=metadata,
        )

        registered.append(
            source
        )

    return registered


def verify_registered_sources(
    sources,
    limit,
):
    results = []

    for source in sources[
        :limit
    ]:
        print()

        print(
            "Verifying:",
            source["company"],
            "|",
            source["ats"],
            "/",
            source["identifier"],
        )

        result = (
            verify_discovered_source(
                source["id"]
            )
        )

        results.append(
            result
        )

        verification = (
            result.get(
                "verification"
            )
        )

        print(
            "Action:",
            result["action"],
        )

        if verification:
            print(
                "Verifier:",
                verification[
                    "status"
                ],
                "| Jobs:",
                verification[
                    "job_count"
                ],
            )

    return results


def summarize_verification(
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


def run_discovery_cycle(
    query_limit=None,
    verify=True,
):
    config = (
        load_runtime_config()
    )

    candidate_limit = config.get(
        "max_candidates_per_run",
        20,
    )

    verification_limit = config.get(
        "max_verifications_per_run",
        10,
    )

    query_batch = (
        select_queries_for_run(
            limit=query_limit
        )
    )

    print(
        "=" * 60
    )

    print(
        "InfraJob Source Discovery"
    )

    print(
        "=" * 60
    )

    print(
        "Queries selected:",
        len(query_batch),
    )

    if not query_batch:
        return {
            "queries_selected": 0,
            "candidates_found": 0,
            "registered": 0,
            "verification": {
                "verified": 0,
                "rejected": 0,
                "pending": 0,
                "skipped": 0,
            },
        }

    (
        candidates,
        search_statistics,
    ) = collect_candidates(
        query_batch
    )

    print()
    print(
        "=" * 60
    )

    print(
        "Candidate Extraction"
    )

    print(
        "=" * 60
    )

    print(
        "Unique new candidates:",
        len(candidates),
    )

    if len(
        candidates
    ) > candidate_limit:
        print(
            "Candidate budget:",
            candidate_limit,
        )

        print(
            "Deferred candidates:",
            (
                len(candidates)
                - candidate_limit
            ),
        )

    registered = (
        register_candidates(
            candidates,
            candidate_limit,
        )
    )

    print(
        "Registered candidates:",
        len(registered),
    )

    verification_results = []

    if verify:
        verification_results = (
            verify_registered_sources(
                registered,
                verification_limit,
            )
        )

    verification_summary = (
        summarize_verification(
            verification_results
        )
    )

    deferred_verification = max(
        len(registered)
        - (
            verification_limit
            if verify
            else 0
        ),
        0,
    )

    print()
    print(
        "=" * 60
    )

    print(
        "Discovery Summary"
    )

    print(
        "=" * 60
    )

    print(
        "Queries:",
        len(query_batch),
    )

    print(
        "Raw search results:",
        search_statistics[
            "raw_results"
        ],
    )

    print(
        "Unique candidates:",
        len(candidates),
    )

    print(
        "Registered:",
        len(registered),
    )

    print(
        "Verified:",
        verification_summary[
            "verified"
        ],
    )

    print(
        "Rejected:",
        verification_summary[
            "rejected"
        ],
    )

    print(
        "Pending:",
        verification_summary[
            "pending"
        ],
    )

    print(
        "Deferred verification:",
        deferred_verification,
    )

    return {
        "queries_selected": (
            len(query_batch)
        ),
        "candidates_found": (
            len(candidates)
        ),
        "registered": (
            len(registered)
        ),
        "deferred_verification": (
            deferred_verification
        ),
        "search": search_statistics,
        "verification": (
            verification_summary
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run InfraJob source "
            "discovery cycle."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Override maximum number "
            "of search queries."
        ),
    )

    parser.add_argument(
        "--no-verify",
        action="store_true",
        help=(
            "Discover and register "
            "sources without "
            "verification."
        ),
    )

    args = parser.parse_args()

    run_discovery_cycle(
        query_limit=args.limit,
        verify=(
            not args.no_verify
        ),
    )


if __name__ == "__main__":
    main()