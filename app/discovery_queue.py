import json

from collections import (
    defaultdict,
)

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path

from app.discovery_query_generator import (
    generate_discovery_queries,
)


CONFIG_PATH = Path(
    "config/discovery_runtime.json"
)

STATE_PATH = Path(
    "runtime/discovery_query_state.json"
)


VALID_RESULT_STATUSES = {
    "success",
    "no_results",
    "error",
    "rate_limited",
}


def utc_now():
    return datetime.now(
        timezone.utc
    )


def utc_now_iso():
    return (
        utc_now()
        .replace(
            microsecond=0
        )
        .isoformat()
    )


def load_runtime_config():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    validate_runtime_config(
        config
    )

    return config


def validate_runtime_config(
    config,
):
    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "Discovery runtime config "
            "must be a JSON object."
        )

    required_fields = {
        "max_queries_per_run",
        "cooldown_hours",
        "error_retry_hours",
        "rate_limit_retry_hours",
    }

    missing = (
        required_fields
        - config.keys()
    )

    if missing:
        raise ValueError(
            "Discovery runtime config "
            f"is missing: "
            f"{sorted(missing)}"
        )

    for field in required_fields:
        value = config[
            field
        ]

        if (
            not isinstance(
                value,
                int,
            )
            or value < 0
        ):
            raise ValueError(
                f"'{field}' must be "
                "a non-negative integer."
            )

    if (
        config[
            "max_queries_per_run"
        ]
        <= 0
    ):
        raise ValueError(
            "'max_queries_per_run' "
            "must be greater than 0."
        )

    return True


def empty_state():
    return {
        "schema_version": 1,
        "queries": {},
    }


def load_query_state():
    if not STATE_PATH.exists():
        return empty_state()

    with STATE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        state = json.load(
            file
        )

    if not isinstance(
        state,
        dict,
    ):
        raise ValueError(
            "Discovery query state "
            "must be a JSON object."
        )

    if not isinstance(
        state.get(
            "queries"
        ),
        dict,
    ):
        raise ValueError(
            "Discovery query state "
            "must contain a "
            "'queries' object."
        )

    return state


def save_query_state(
    state,
):
    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        STATE_PATH.with_suffix(
            ".tmp"
        )
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write(
            "\n"
        )

    temporary_path.replace(
        STATE_PATH
    )


def clear_query_state():
    state = empty_state()

    save_query_state(
        state
    )

    return state


def parse_timestamp(
    value,
):
    timestamp = (
        datetime.fromisoformat(
            value
        )
    )

    if timestamp.tzinfo is None:
        timestamp = (
            timestamp.replace(
                tzinfo=timezone.utc
            )
        )

    return timestamp


def get_cooldown_hours(
    query_state,
    config,
):
    status = query_state.get(
        "last_status"
    )

    if status == "error":
        return config[
            "error_retry_hours"
        ]

    if status == "rate_limited":
        return config[
            "rate_limit_retry_hours"
        ]

    return config[
        "cooldown_hours"
    ]


def is_query_due(
    query_id,
    state=None,
    config=None,
    now=None,
):
    if state is None:
        state = load_query_state()

    if config is None:
        config = (
            load_runtime_config()
        )

    if now is None:
        now = utc_now()

    query_state = (
        state[
            "queries"
        ].get(
            query_id
        )
    )

    if query_state is None:
        return True

    last_run_at = (
        query_state.get(
            "last_run_at"
        )
    )

    if not last_run_at:
        return True

    last_run = parse_timestamp(
        last_run_at
    )

    cooldown_hours = (
        get_cooldown_hours(
            query_state,
            config,
        )
    )

    next_run = (
        last_run
        + timedelta(
            hours=cooldown_hours
        )
    )

    return now >= next_run


def get_due_queries(
    now=None,
):
    config = (
        load_runtime_config()
    )

    state = (
        load_query_state()
    )

    if now is None:
        now = utc_now()

    queries = (
        generate_discovery_queries()
    )

    return [
        query
        for query in queries
        if is_query_due(
            query["id"],
            state=state,
            config=config,
            now=now,
        )
    ]


def group_queries_by_market(
    queries,
):
    groups = defaultdict(
        list
    )

    for query in queries:
        groups[
            query[
                "market_code"
            ]
        ].append(
            query
        )

    for market_code in groups:
        groups[
            market_code
        ].sort(
            key=lambda item: (
                item[
                    "score"
                ],
                item[
                    "id"
                ],
            ),
            reverse=True,
        )

    return groups


def select_queries_for_run(
    limit=None,
    now=None,
):
    config = (
        load_runtime_config()
    )

    if limit is None:
        limit = config[
            "max_queries_per_run"
        ]

    if limit <= 0:
        return []

    due_queries = (
        get_due_queries(
            now=now
        )
    )

    groups = (
        group_queries_by_market(
            due_queries
        )
    )

    if not groups:
        return []

    market_weights = {}

    for market_code, items in (
        groups.items()
    ):
        if not items:
            continue

        market_weights[
            market_code
        ] = max(
            items[0].get(
                "search_weight",
                0,
            ),
            1,
        )

    selected_counts = {
        market_code: 0
        for market_code in groups
    }

    selected = []

    while (
        len(selected) < limit
    ):
        available_markets = [
            market_code
            for market_code, items
            in groups.items()
            if items
        ]

        if not available_markets:
            break

        # --------------------------------------------------
        # Weighted fair scheduling:
        #
        # Markets with higher search_weight receive more
        # slots, but every enabled market gets a chance
        # before one market monopolizes the queue.
        # --------------------------------------------------

        market_code = min(
            available_markets,
            key=lambda code: (
                selected_counts[
                    code
                ]
                / market_weights[
                    code
                ],
                -market_weights[
                    code
                ],
                code,
            ),
        )

        query = (
            groups[
                market_code
            ].pop(
                0
            )
        )

        selected.append(
            query
        )

        selected_counts[
            market_code
        ] += 1

    return selected


def mark_query_result(
    query_id,
    status,
    result_count=0,
    error=None,
    now=None,
):
    if status not in (
        VALID_RESULT_STATUSES
    ):
        raise ValueError(
            f"Invalid query result "
            f"status: {status}"
        )

    known_queries = {
        query[
            "id"
        ]
        for query in (
            generate_discovery_queries()
        )
    }

    if query_id not in known_queries:
        raise KeyError(
            f"Unknown discovery "
            f"query: {query_id}"
        )

    if now is None:
        timestamp = utc_now_iso()
    else:
        timestamp = (
            now
            .replace(
                microsecond=0
            )
            .isoformat()
        )

    state = (
        load_query_state()
    )

    previous = (
        state[
            "queries"
        ].get(
            query_id,
            {},
        )
    )

    run_count = (
        previous.get(
            "run_count",
            0,
        )
        + 1
    )

    success_count = (
        previous.get(
            "success_count",
            0,
        )
    )

    consecutive_failures = (
        previous.get(
            "consecutive_failures",
            0,
        )
    )

    if status in {
        "success",
        "no_results",
    }:
        success_count += 1
        consecutive_failures = 0
    else:
        consecutive_failures += 1

    state[
        "queries"
    ][
        query_id
    ] = {
        "last_run_at": (
            timestamp
        ),
        "last_status": (
            status
        ),
        "last_result_count": (
            int(
                result_count
                or 0
            )
        ),
        "last_error": (
            error
        ),
        "run_count": (
            run_count
        ),
        "success_count": (
            success_count
        ),
        "consecutive_failures": (
            consecutive_failures
        ),
    }

    save_query_state(
        state
    )

    return state[
        "queries"
    ][
        query_id
    ]


def get_query_state(
    query_id,
):
    state = (
        load_query_state()
    )

    return (
        state[
            "queries"
        ].get(
            query_id
        )
    )


def get_queue_summary(
    now=None,
):
    all_queries = (
        generate_discovery_queries()
    )

    due_queries = (
        get_due_queries(
            now=now
        )
    )

    total = len(
        all_queries
    )

    due = len(
        due_queries
    )

    return {
        "total_queries": total,
        "due_queries": due,
        "cooling_down": (
            total - due
        ),
        "next_batch_size": len(
            select_queries_for_run(
                now=now
            )
        ),
    }