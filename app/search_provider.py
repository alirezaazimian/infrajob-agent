import json

from pathlib import Path


CONFIG_PATH = Path(
    "config/discovery_runtime.json"
)


VALID_SEARCH_STATUSES = {
    "success",
    "no_results",
    "rate_limited",
    "error",
}


def load_search_provider_config():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    provider_config = config.get(
        "search_provider"
    )

    if not isinstance(
        provider_config,
        dict,
    ):
        raise ValueError(
            "discovery_runtime.json "
            "must contain "
            "'search_provider'."
        )

    validate_search_provider_config(
        provider_config
    )

    return provider_config


def validate_search_provider_config(
    config,
):
    required_fields = {
        "name",
        "backend",
        "region",
        "safesearch",
        "max_results_per_query",
        "timeout_seconds",
    }

    missing = (
        required_fields
        - config.keys()
    )

    if missing:
        raise ValueError(
            "Search provider config "
            f"is missing: "
            f"{sorted(missing)}"
        )

    if config["name"] != "ddgs":
        raise ValueError(
            "Unsupported search "
            f"provider: "
            f"{config['name']}"
        )

    max_results = config[
        "max_results_per_query"
    ]

    if (
        not isinstance(
            max_results,
            int,
        )
        or max_results <= 0
    ):
        raise ValueError(
            "'max_results_per_query' "
            "must be a positive integer."
        )

    timeout = config[
        "timeout_seconds"
    ]

    if (
        not isinstance(
            timeout,
            int,
        )
        or timeout <= 0
    ):
        raise ValueError(
            "'timeout_seconds' "
            "must be a positive integer."
        )

    return True


def build_search_result(
    query,
    status,
    results=None,
    error=None,
    provider="ddgs",
):
    normalized_results = (
        results
        or []
    )

    return {
        "provider": provider,
        "query": query,
        "status": status,
        "result_count": len(
            normalized_results
        ),
        "results": (
            normalized_results
        ),
        "error": error,
    }


def classify_search_exception(
    error,
):
    message = str(
        error
    ).strip()

    normalized = (
        message.lower()
    )

    rate_limit_signals = {
        "rate limit",
        "ratelimit",
        "too many requests",
        "429",
    }

    for signal in (
        rate_limit_signals
    ):
        if signal in normalized:
            return (
                "rate_limited",
                message,
            )

    return (
        "error",
        message,
    )


def normalize_search_result(
    raw_result,
):
    if not isinstance(
        raw_result,
        dict,
    ):
        return None

    url = (
        raw_result.get(
            "href"
        )
        or raw_result.get(
            "url"
        )
        or ""
    ).strip()

    if not url:
        return None

    title = (
        raw_result.get(
            "title"
        )
        or ""
    ).strip()

    snippet = (
        raw_result.get(
            "body"
        )
        or raw_result.get(
            "snippet"
        )
        or raw_result.get(
            "description"
        )
        or ""
    ).strip()

    return {
        "title": title,
        "url": url,
        "snippet": snippet,
    }


def deduplicate_results(
    results,
):
    seen_urls = set()

    unique_results = []

    for result in results:
        url = result[
            "url"
        ]

        if url in seen_urls:
            continue

        seen_urls.add(
            url
        )

        unique_results.append(
            result
        )

    return unique_results


def search_ddgs(
    query,
    max_results=None,
):
    try:
        from ddgs import DDGS

    except ImportError as error:
        return build_search_result(
            query=query,
            status="error",
            error=(
                "ddgs is not installed. "
                "Run: pip install -U ddgs"
            ),
        )

    provider_config = (
        load_search_provider_config()
    )

    if max_results is None:
        max_results = provider_config[
            "max_results_per_query"
        ]

    if max_results <= 0:
        raise ValueError(
            "max_results must be "
            "greater than zero."
        )

    try:
        client = DDGS(
            timeout=provider_config[
                "timeout_seconds"
            ]
        )

        raw_results = client.text(
            query=query,
            region=provider_config[
                "region"
            ],
            safesearch=provider_config[
                "safesearch"
            ],
            max_results=max_results,
            backend=provider_config[
                "backend"
            ],
        )

    except Exception as error:
        (
            status,
            message,
        ) = classify_search_exception(
            error
        )

        return build_search_result(
            query=query,
            status=status,
            error=message,
        )

    normalized_results = []

    for raw_result in (
        raw_results
        or []
    ):
        result = (
            normalize_search_result(
                raw_result
            )
        )

        if result is None:
            continue

        normalized_results.append(
            result
        )

    normalized_results = (
        deduplicate_results(
            normalized_results
        )
    )

    if not normalized_results:
        return build_search_result(
            query=query,
            status="no_results",
            results=[],
        )

    return build_search_result(
        query=query,
        status="success",
        results=normalized_results,
    )


def search_web(
    query,
    max_results=None,
):
    query = (
        query
        or ""
    ).strip()

    if not query:
        raise ValueError(
            "Search query cannot "
            "be empty."
        )

    provider_config = (
        load_search_provider_config()
    )

    provider_name = (
        provider_config[
            "name"
        ]
    )

    if provider_name == "ddgs":
        return search_ddgs(
            query=query,
            max_results=max_results,
        )

    raise ValueError(
        "Unsupported search "
        f"provider: "
        f"{provider_name}"
    )


def search_query_record(
    query_record,
    max_results=None,
):
    if not isinstance(
        query_record,
        dict,
    ):
        raise ValueError(
            "query_record must "
            "be a dictionary."
        )

    query = query_record.get(
        "query"
    )

    if not query:
        raise ValueError(
            "query_record is missing "
            "'query'."
        )

    search_result = search_web(
        query=query,
        max_results=max_results,
    )

    return {
        "query_id": (
            query_record.get(
                "id"
            )
        ),
        "market_code": (
            query_record.get(
                "market_code"
            )
        ),
        "ats": (
            query_record.get(
                "ats"
            )
        ),
        "role": (
            query_record.get(
                "role"
            )
        ),
        **search_result,
    }