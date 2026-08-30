import re

from urllib.parse import (
    urlparse,
)

from app.ats_detector import (
    detect_ats_source,
)

from app.discovery_registry import (
    get_all_discovered_sources,
)

from app.source_registry import (
    get_all_company_sources,
)


SUPPORTED_ATS = {
    "lever",
    "greenhouse",
    "personio",
    "ashby",
}


def normalize_identifier(
    value,
):
    return (
        value
        or ""
    ).strip().lower()


def source_key(
    ats,
    identifier,
):
    return (
        (
            ats
            or ""
        )
        .strip()
        .lower(),
        normalize_identifier(
            identifier
        ),
    )


def get_existing_source_keys():
    keys = set()

    for source in (
        get_all_company_sources()
    ):
        keys.add(
            source_key(
                source.get(
                    "ats"
                ),
                source.get(
                    "identifier"
                ),
            )
        )

    return keys


def get_discovered_source_keys():
    keys = set()

    for source in (
        get_all_discovered_sources()
    ):
        keys.add(
            source_key(
                source.get(
                    "ats"
                ),
                source.get(
                    "identifier"
                ),
            )
        )

    return keys


def humanize_identifier(
    identifier,
):
    value = (
        identifier
        or ""
    ).strip()

    value = re.sub(
        r"[-_]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip().title()


def clean_company_guess(
    value,
):
    text = (
        value
        or ""
    ).strip()

    if not text:
        return ""

    patterns = [
        r"\s*\|\s*jobs.*$",
        r"\s*\|\s*careers.*$",
        r"\s*-\s*jobs.*$",
        r"\s*-\s*careers.*$",
        r"\s+jobs$",
        r"\s+careers$",
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip(
        " |-"
    )


def guess_company_name(
    search_result,
    identifier,
):
    title = (
        search_result.get(
            "title"
        )
        or ""
    ).strip()

    title_patterns = [
        r"^jobs at\s+(.+)$",
        r"^careers at\s+(.+)$",
        r"^(.+?)\s+jobs$",
        r"^(.+?)\s+careers$",
    ]

    for pattern in title_patterns:
        match = re.match(
            pattern,
            title,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        company = (
            clean_company_guess(
                match.group(
                    1
                )
            )
        )

        if company:
            return company

    return humanize_identifier(
        identifier
    )


def build_canonical_url(
    ats,
    identifier,
    original_url=None,
):
    identifier = (
        identifier
        or ""
    ).strip()

    if ats == "lever":
        return (
            "https://jobs.lever.co/"
            f"{identifier}"
        )

    if ats == "greenhouse":
        return (
            "https://boards.greenhouse.io/"
            f"{identifier}"
        )

    if ats == "ashby":
        return (
            "https://jobs.ashbyhq.com/"
            f"{identifier}"
        )

    if ats == "personio":
        # Personio can use multiple country/domain
        # variants, so preserve the discovered host
        # whenever possible.

        if original_url:
            parsed = urlparse(
                original_url
            )

            hostname = (
                parsed.hostname
                or ""
            )

            if hostname:
                return (
                    f"https://{hostname}/"
                )

        return (
            f"https://{identifier}"
            ".jobs.personio.de/"
        )

    return original_url


def extract_candidate(
    query_record,
    search_result,
    production_keys=None,
    discovery_keys=None,
):
    if production_keys is None:
        production_keys = (
            get_existing_source_keys()
        )

    if discovery_keys is None:
        discovery_keys = (
            get_discovered_source_keys()
        )

    result_url = (
        search_result.get(
            "url"
        )
        or ""
    ).strip()

    if not result_url:
        return None

    detection = detect_ats_source(
        result_url
    )

    ats = detection.get(
        "ats"
    )

    identifier = detection.get(
        "identifier"
    )

    if (
        ats not in SUPPORTED_ATS
        or not identifier
    ):
        return None

    key = source_key(
        ats,
        identifier,
    )

    expected_ats = (
        query_record.get(
            "ats"
        )
        or ""
    ).strip().lower()

    expected_ats_match = (
        not expected_ats
        or expected_ats == ats
    )

    if not expected_ats_match:
        return None

    if key in production_keys:
        duplicate_status = (
            "production"
        )

    elif key in discovery_keys:
        duplicate_status = (
            "discovery"
        )

    else:
        duplicate_status = (
            "new"
        )

    company_guess = (
        guess_company_name(
            search_result,
            identifier,
        )
    )

    canonical_url = (
        build_canonical_url(
            ats,
            identifier,
            original_url=result_url,
        )
    )

    return {
        "key": (
            f"{ats}:"
            f"{normalize_identifier(identifier)}"
        ),
        "ats": ats,
        "identifier": identifier,
        "company_guess": (
            company_guess
        ),
        "market_code": (
            query_record.get(
                "market_code"
            )
        ),
        "country": (
            query_record.get(
                "country"
            )
        ),
        "role": (
            query_record.get(
                "role"
            )
        ),
        "query_id": (
            query_record.get(
                "id"
            )
        ),
        "query": (
            query_record.get(
                "query"
            )
        ),
        "source_url": (
            canonical_url
        ),
        "result_url": (
            result_url
        ),
        "result_title": (
            search_result.get(
                "title"
            )
            or ""
        ),
        "result_snippet": (
            search_result.get(
                "snippet"
            )
            or ""
        ),
        "detection_confidence": (
            detection.get(
                "confidence"
            )
        ),
        "duplicate_status": (
            duplicate_status
        ),
    }


def merge_candidate(
    existing,
    incoming,
):
    query_ids = set(
        existing.get(
            "query_ids",
            [],
        )
    )

    query_id = incoming.get(
        "query_id"
    )

    if query_id:
        query_ids.add(
            query_id
        )

    roles = set(
        existing.get(
            "matched_roles",
            [],
        )
    )

    role = incoming.get(
        "role"
    )

    if role:
        roles.add(
            role
        )

    result_urls = set(
        existing.get(
            "result_urls",
            [],
        )
    )

    result_url = incoming.get(
        "result_url"
    )

    if result_url:
        result_urls.add(
            result_url
        )

    existing[
        "query_ids"
    ] = sorted(
        query_ids
    )

    existing[
        "matched_roles"
    ] = sorted(
        roles
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

    return existing


def extract_candidates(
    query_record,
    search_results,
    include_duplicates=False,
):
    production_keys = (
        get_existing_source_keys()
    )

    discovery_keys = (
        get_discovered_source_keys()
    )

    candidates_by_key = {}

    for search_result in (
        search_results
        or []
    ):
        candidate = (
            extract_candidate(
                query_record,
                search_result,
                production_keys=(
                    production_keys
                ),
                discovery_keys=(
                    discovery_keys
                ),
            )
        )

        if candidate is None:
            continue

        if (
            not include_duplicates
            and candidate[
                "duplicate_status"
            ] != "new"
        ):
            continue

        key = candidate[
            "key"
        ]

        if key not in (
            candidates_by_key
        ):
            candidate[
                "query_ids"
            ] = [
                candidate[
                    "query_id"
                ]
            ]

            candidate[
                "matched_roles"
            ] = [
                candidate[
                    "role"
                ]
            ]

            candidate[
                "result_urls"
            ] = [
                candidate[
                    "result_url"
                ]
            ]

            candidate[
                "evidence_count"
            ] = 1

            candidates_by_key[
                key
            ] = candidate

            continue

        merge_candidate(
            candidates_by_key[
                key
            ],
            candidate,
        )

    return list(
        candidates_by_key.values()
    )


def extract_candidates_from_search(
    search_output,
    query_record,
    include_duplicates=False,
):
    if not isinstance(
        search_output,
        dict,
    ):
        raise ValueError(
            "search_output must "
            "be a dictionary."
        )

    results = search_output.get(
        "results",
        []
    )

    return extract_candidates(
        query_record,
        results,
        include_duplicates=(
            include_duplicates
        ),
    )