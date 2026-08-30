import json
import re

from pathlib import Path

from app.config_loader import (
    get_enabled_markets,
    load_target_roles,
)


CONFIG_PATH = Path(
    "config/discovery_search.json"
)


def load_discovery_search_config():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    validate_discovery_search_config(
        config
    )

    return config


def validate_discovery_search_config(
    config,
):
    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "Discovery search config "
            "must be a JSON object."
        )

    ats_targets = config.get(
        "ats_targets"
    )

    role_queries = config.get(
        "role_queries"
    )

    tier_query_limits = config.get(
        "tier_query_limits"
    )

    if not isinstance(
        ats_targets,
        list,
    ):
        raise ValueError(
            "Discovery search config "
            "must contain an "
            "'ats_targets' list."
        )

    if not isinstance(
        role_queries,
        list,
    ):
        raise ValueError(
            "Discovery search config "
            "must contain a "
            "'role_queries' list."
        )

    if not isinstance(
        tier_query_limits,
        dict,
    ):
        raise ValueError(
            "Discovery search config "
            "must contain "
            "'tier_query_limits'."
        )

    seen_ats = set()

    for target in ats_targets:
        ats = target.get(
            "ats"
        )

        prefix = target.get(
            "search_prefix"
        )

        if not ats:
            raise ValueError(
                "ATS target is missing "
                "'ats'."
            )

        if ats in seen_ats:
            raise ValueError(
                f"Duplicate ATS target: "
                f"{ats}"
            )

        seen_ats.add(
            ats
        )

        if not prefix:
            raise ValueError(
                f"ATS target '{ats}' "
                "is missing "
                "'search_prefix'."
            )

    validate_role_queries(
        role_queries
    )

    return True


def validate_role_queries(
    role_queries,
):
    target_roles_config = (
        load_target_roles()
    )

    valid_role_names = {
        role[
            "name"
        ]
        for role in target_roles_config[
            "roles"
        ]
    }

    seen_roles = set()

    for role_query in role_queries:
        role_name = role_query.get(
            "role"
        )

        phrase = role_query.get(
            "phrase"
        )

        if not role_name:
            raise ValueError(
                "Discovery role query "
                "is missing 'role'."
            )

        if role_name in seen_roles:
            raise ValueError(
                f"Duplicate discovery "
                f"role: {role_name}"
            )

        seen_roles.add(
            role_name
        )

        if role_name not in (
            valid_role_names
        ):
            raise ValueError(
                f"Discovery role "
                f"'{role_name}' "
                "does not exist in "
                "target_roles.json."
            )

        if not phrase:
            raise ValueError(
                f"Discovery role "
                f"'{role_name}' "
                "is missing a search "
                "phrase."
            )


def slugify(
    value,
):
    text = (
        value
        .strip()
        .lower()
    )

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )

    return text.strip(
        "-"
    )


def build_search_query(
    search_prefix,
    role_phrase,
    location,
):
    return (
        f'{search_prefix} '
        f'"{role_phrase}" '
        f'"{location}"'
    )


def calculate_query_score(
    market,
    role_query,
    ats_target,
):
    market_weight = market.get(
        "search_weight",
        0,
    )

    role_priority = (
        role_query.get(
            "priority",
            0,
        )
    )

    ats_priority = (
        ats_target.get(
            "priority",
            0,
        )
    )

    # --------------------------------------------------
    # Global ordering:
    #
    # market strategy dominates,
    # then role importance,
    # then ATS preference.
    # --------------------------------------------------

    return (
        market_weight * 10000
        + role_priority * 100
        + ats_priority
    )


def create_query_record(
    market,
    role_query,
    ats_target,
):
    market_code = market[
        "code"
    ]

    country = market[
        "country"
    ]

    ats = ats_target[
        "ats"
    ]

    role_name = role_query[
        "role"
    ]

    role_phrase = role_query[
        "phrase"
    ]

    query_id = (
        f"{market_code}:"
        f"{ats}:"
        f"{slugify(role_name)}"
    )

    query = build_search_query(
        ats_target[
            "search_prefix"
        ],
        role_phrase,
        country,
    )

    return {
        "id": query_id,
        "market_code": (
            market_code
        ),
        "country": country,
        "tier": market.get(
            "tier",
            "unknown",
        ),
        "strategy": market.get(
            "strategy",
            "unknown",
        ),
        "search_weight": (
            market.get(
                "search_weight",
                0,
            )
        ),
        "ats": ats,
        "role": role_name,
        "role_phrase": (
            role_phrase
        ),
        "query": query,
        "score": (
            calculate_query_score(
                market,
                role_query,
                ats_target,
            )
        ),
    }


def generate_market_queries(
    market,
    config,
):
    tier = market.get(
        "tier",
        "unknown",
    )

    query_limit = (
        config[
            "tier_query_limits"
        ].get(
            tier,
            0,
        )
    )

    if query_limit <= 0:
        return []

    role_queries = sorted(
        config[
            "role_queries"
        ],
        key=lambda item: (
            item.get(
                "priority",
                0,
            )
        ),
        reverse=True,
    )

    ats_targets = sorted(
        config[
            "ats_targets"
        ],
        key=lambda item: (
            item.get(
                "priority",
                0,
            )
        ),
        reverse=True,
    )

    candidates = []

    # --------------------------------------------------
    # Role-first generation gives every selected role
    # coverage across all ATS platforms before moving
    # to lower-priority roles.
    # --------------------------------------------------

    for role_query in role_queries:
        for ats_target in (
            ats_targets
        ):
            candidates.append(
                create_query_record(
                    market,
                    role_query,
                    ats_target,
                )
            )

    candidates.sort(
        key=lambda item: (
            item["score"],
            item["role"],
            item["ats"],
        ),
        reverse=True,
    )

    return candidates[
        :query_limit
    ]


def generate_discovery_queries():
    config = (
        load_discovery_search_config()
    )

    markets = (
        get_enabled_markets()
    )

    queries = []

    for market in markets:
        market_queries = (
            generate_market_queries(
                market,
                config,
            )
        )

        queries.extend(
            market_queries
        )

    queries.sort(
        key=lambda item: (
            item["score"],
            item["market_code"],
            item["role"],
            item["ats"],
        ),
        reverse=True,
    )

    return queries


def get_queries_for_market(
    market_code,
):
    normalized_code = (
        market_code
        .strip()
        .upper()
    )

    return [
        query
        for query in (
            generate_discovery_queries()
        )
        if query[
            "market_code"
        ] == normalized_code
    ]


def get_query_counts_by_market():
    counts = {}

    for query in (
        generate_discovery_queries()
    ):
        market_code = query[
            "market_code"
        ]

        counts[
            market_code
        ] = (
            counts.get(
                market_code,
                0,
            )
            + 1
        )

    return counts