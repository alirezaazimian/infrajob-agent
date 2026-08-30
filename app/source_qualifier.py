import json
import re

from collections import (
    Counter,
)

from pathlib import Path

from app.config_loader import (
    get_enabled_markets,
)

from app.country_detector import (
    detect_country,
)

from app.discovery_registry import (
    get_discovered_source,
)

from app.job_filter import (
    match_job_role,
)

from app.normalizers import (
    normalize_ashby_job,
    normalize_greenhouse_job,
    normalize_lever_job,
    normalize_personio_job,
)

from app.source_verifier import (
    fetch_source_jobs,
)


CONFIG_PATH = Path(
    "config/source_qualification.json"
)


QUALIFICATION_STATUSES = {
    "qualified",
    "review_large_board",
    "review_market_mismatch",
    "review_unknown_location",
    "reject_no_target_roles",
    "reject_wrong_market",
    "reject_nonproduction_source",
    "not_ready",
}


def load_qualification_config():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    validate_qualification_config(
        config
    )

    return config


def validate_qualification_config(
    config,
):
    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "Source qualification config "
            "must be a JSON object."
        )

    required_fields = {
        "minimum_market_role_jobs",
        "large_board_threshold",
        "sample_job_limit",
        "nonproduction_identifier_patterns",
    }

    missing = (
        required_fields
        - config.keys()
    )

    if missing:
        raise ValueError(
            "Source qualification config "
            f"is missing: {sorted(missing)}"
        )

    for field in {
        "minimum_market_role_jobs",
        "large_board_threshold",
        "sample_job_limit",
    }:
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

    patterns = config[
        "nonproduction_identifier_patterns"
    ]

    if not isinstance(
        patterns,
        list,
    ):
        raise ValueError(
            "'nonproduction_identifier_patterns' "
            "must be a list."
        )

    for pattern in patterns:
        re.compile(
            pattern
        )

    return True


def get_enabled_market_codes():
    return {
        market[
            "code"
        ]
        for market in (
            get_enabled_markets()
        )
    }


def normalize_source_job(
    raw_job,
    source,
):
    ats = source[
        "ats"
    ]

    company = source[
        "company"
    ]

    identifier = source[
        "identifier"
    ]

    if ats == "greenhouse":
        return normalize_greenhouse_job(
            raw_job,
            company,
        )

    if ats == "personio":
        return normalize_personio_job(
            raw_job,
            company,
            identifier,
        )

    if ats == "lever":
        return normalize_lever_job(
            raw_job,
            company,
            identifier,
        )

    if ats == "ashby":
        return normalize_ashby_job(
            raw_job,
            company,
            identifier,
        )

    raise ValueError(
        f"Unsupported ATS: {ats}"
    )


def is_nonproduction_identifier(
    identifier,
    config,
):
    normalized = (
        identifier
        or ""
    ).strip().lower()

    for pattern in config[
        "nonproduction_identifier_patterns"
    ]:
        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        ):
            return True

    return False


def analyze_job(
    normalized_job,
):
    country_result = detect_country(
        normalized_job.get(
            "location",
            "",
        )
    )

    role_result = match_job_role(
        normalized_job
    )

    return {
        "job": normalized_job,
        "country_code": (
            country_result[
                "country_code"
            ]
        ),
        "country": (
            country_result[
                "country"
            ]
        ),
        "country_confidence": (
            country_result[
                "confidence"
            ]
        ),
        "role_match": role_result,
        "is_target_role": (
            role_result is not None
        ),
    }


def build_job_sample(
    analyzed_job,
):
    job = analyzed_job[
        "job"
    ]

    role_match = analyzed_job.get(
        "role_match"
    )

    return {
        "title": job.get(
            "title",
            "",
        ),
        "location": job.get(
            "location",
            "",
        ),
        "country_code": (
            analyzed_job.get(
                "country_code"
            )
        ),
        "country": (
            analyzed_job.get(
                "country"
            )
        ),
        "role": (
            role_match.get(
                "role"
            )
            if role_match
            else None
        ),
        "role_priority": (
            role_match.get(
                "priority"
            )
            if role_match
            else None
        ),
        "url": job.get(
            "url",
            "",
        ),
    }


def determine_qualification(
    source,
    analysis,
    config,
):
    requested_market = (
        source.get(
            "market"
        )
        or ""
    ).upper()

    minimum_market_jobs = config[
        "minimum_market_role_jobs"
    ]

    large_board_threshold = config[
        "large_board_threshold"
    ]

    total_jobs = analysis[
        "total_jobs"
    ]

    target_role_jobs = analysis[
        "target_role_jobs"
    ]

    requested_market_role_jobs = (
        analysis[
            "requested_market_role_jobs"
        ]
    )

    enabled_market_role_jobs = (
        analysis[
            "enabled_market_role_jobs"
        ]
    )

    unknown_country_role_jobs = (
        analysis[
            "unknown_country_role_jobs"
        ]
    )

    if is_nonproduction_identifier(
        source.get(
            "identifier"
        ),
        config,
    ):
        return {
            "status": (
                "reject_nonproduction_source"
            ),
            "qualified": False,
            "reason": (
                "Source identifier appears "
                "to be a demo or sandbox board."
            ),
        }

    if target_role_jobs == 0:
        return {
            "status": (
                "reject_no_target_roles"
            ),
            "qualified": False,
            "reason": (
                "Verified board contains no "
                "jobs matching the target "
                "role taxonomy."
            ),
        }

    if (
        total_jobs
        >= large_board_threshold
    ):
        return {
            "status": (
                "review_large_board"
            ),
            "qualified": False,
            "reason": (
                "Board size exceeds the "
                "automatic promotion threshold "
                "and requires review."
            ),
        }

    if (
        requested_market_role_jobs
        >= minimum_market_jobs
    ):
        return {
            "status": "qualified",
            "qualified": True,
            "reason": (
                "Source contains target-role "
                "jobs in the requested market."
            ),
        }

    if enabled_market_role_jobs > 0:
        return {
            "status": (
                "review_market_mismatch"
            ),
            "qualified": False,
            "reason": (
                "Source contains target-role "
                "jobs in enabled markets, but "
                "not in the market assigned "
                "during discovery."
            ),
        }

    if unknown_country_role_jobs > 0:
        return {
            "status": (
                "review_unknown_location"
            ),
            "qualified": False,
            "reason": (
                "Target-role jobs exist, but "
                "their locations could not be "
                "mapped reliably to a country."
            ),
        }

    return {
        "status": (
            "reject_wrong_market"
        ),
        "qualified": False,
        "reason": (
            "Target-role jobs exist, but none "
            "were found in enabled target "
            "markets."
        ),
    }


def qualify_source(
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

    if source.get(
        "status"
    ) != "verified":
        return {
            "source_id": source_id,
            "company": source.get(
                "company"
            ),
            "ats": source.get(
                "ats"
            ),
            "identifier": source.get(
                "identifier"
            ),
            "requested_market": (
                source.get(
                    "market"
                )
            ),
            "qualification_status": (
                "not_ready"
            ),
            "qualified": False,
            "reason": (
                "Source must be verified "
                "before qualification."
            ),
        }

    config = (
        load_qualification_config()
    )

    metadata = source.get(
        "metadata",
        {},
    )

    options = metadata.get(
        "options",
        {},
    )

    raw_jobs = fetch_source_jobs(
        source[
            "ats"
        ],
        source[
            "identifier"
        ],
        options=options,
    )

    enabled_market_codes = (
        get_enabled_market_codes()
    )

    requested_market = (
        source.get(
            "market"
        )
        or ""
    ).upper()

    country_counts = Counter()

    target_role_country_counts = (
        Counter()
    )

    role_counts = Counter()

    analyzed_jobs = []

    target_role_samples = []

    target_role_jobs = 0

    requested_market_role_jobs = 0

    enabled_market_role_jobs = 0

    unknown_country_role_jobs = 0

    for raw_job in raw_jobs:
        normalized_job = (
            normalize_source_job(
                raw_job,
                source,
            )
        )

        analyzed = analyze_job(
            normalized_job
        )

        analyzed_jobs.append(
            analyzed
        )

        country_code = (
            analyzed.get(
                "country_code"
            )
        )

        if country_code:
            country_counts[
                country_code
            ] += 1
        else:
            country_counts[
                "UNKNOWN"
            ] += 1

        role_match = analyzed.get(
            "role_match"
        )

        if role_match is None:
            continue

        target_role_jobs += 1

        role_name = role_match[
            "role"
        ]

        role_counts[
            role_name
        ] += 1

        if country_code:
            target_role_country_counts[
                country_code
            ] += 1
        else:
            target_role_country_counts[
                "UNKNOWN"
            ] += 1

        if (
            country_code
            == requested_market
        ):
            requested_market_role_jobs += 1

        if (
            country_code
            in enabled_market_codes
        ):
            enabled_market_role_jobs += 1

        if country_code is None:
            unknown_country_role_jobs += 1

        if (
            len(
                target_role_samples
            )
            < config[
                "sample_job_limit"
            ]
        ):
            target_role_samples.append(
                build_job_sample(
                    analyzed
                )
            )

    analysis = {
        "total_jobs": len(
            raw_jobs
        ),
        "target_role_jobs": (
            target_role_jobs
        ),
        "requested_market_role_jobs": (
            requested_market_role_jobs
        ),
        "enabled_market_role_jobs": (
            enabled_market_role_jobs
        ),
        "unknown_country_role_jobs": (
            unknown_country_role_jobs
        ),
        "country_counts": dict(
            country_counts
        ),
        "target_role_country_counts": (
            dict(
                target_role_country_counts
            )
        ),
        "role_counts": dict(
            role_counts
        ),
        "target_role_samples": (
            target_role_samples
        ),
    }

    decision = (
        determine_qualification(
            source,
            analysis,
            config,
        )
    )

    verified_markets = sorted(
        country_code
        for country_code, count
        in target_role_country_counts.items()
        if (
            country_code
            in enabled_market_codes
            and count > 0
        )
    )

    return {
        "source_id": source[
            "id"
        ],
        "company": source[
            "company"
        ],
        "ats": source[
            "ats"
        ],
        "identifier": source[
            "identifier"
        ],
        "requested_market": (
            requested_market
        ),
        "qualification_status": (
            decision[
                "status"
            ]
        ),
        "qualified": (
            decision[
                "qualified"
            ]
        ),
        "reason": (
            decision[
                "reason"
            ]
        ),
        "verified_markets": (
            verified_markets
        ),
        **analysis,
    }