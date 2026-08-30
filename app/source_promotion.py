import json
import re

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from app.discovery_registry import (
    get_all_discovered_sources,
    get_discovered_source,
    load_discovery_registry,
    save_discovery_registry,
    update_discovery_status,
)

from app.source_registry import (
    get_all_company_sources,
    validate_company_sources,
)


PROMOTION_CONFIG_PATH = Path(
    "config/source_promotion.json"
)

COMPANY_SOURCES_PATH = Path(
    "config/company_sources.json"
)


def utc_now_iso():
    return (
        datetime.now(
            timezone.utc
        )
        .replace(
            microsecond=0
        )
        .isoformat()
    )


def utc_today():
    return (
        datetime.now(
            timezone.utc
        )
        .date()
        .isoformat()
    )


def load_promotion_config():
    with PROMOTION_CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(file)

    validate_promotion_config(
        config
    )

    return config


def validate_promotion_config(
    config,
):
    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "Source promotion config "
            "must be a JSON object."
        )

    required_fields = {
        "auto_promotion_enabled",
        "max_promotions_per_run",
        "allowed_qualification_statuses",
        "default_enabled",
        "default_priority",
    }

    missing = (
        required_fields
        - config.keys()
    )

    if missing:
        raise ValueError(
            "Source promotion config "
            f"is missing: "
            f"{sorted(missing)}"
        )

    if not isinstance(
        config[
            "auto_promotion_enabled"
        ],
        bool,
    ):
        raise ValueError(
            "'auto_promotion_enabled' "
            "must be boolean."
        )

    if not isinstance(
        config[
            "default_enabled"
        ],
        bool,
    ):
        raise ValueError(
            "'default_enabled' "
            "must be boolean."
        )

    if (
        not isinstance(
            config[
                "max_promotions_per_run"
            ],
            int,
        )
        or config[
            "max_promotions_per_run"
        ] < 1
    ):
        raise ValueError(
            "'max_promotions_per_run' "
            "must be a positive integer."
        )

    allowed_statuses = config[
        "allowed_qualification_statuses"
    ]

    if not isinstance(
        allowed_statuses,
        list,
    ):
        raise ValueError(
            "'allowed_qualification_statuses' "
            "must be a list."
        )

    if not allowed_statuses:
        raise ValueError(
            "'allowed_qualification_statuses' "
            "cannot be empty."
        )

    if not isinstance(
        config[
            "default_priority"
        ],
        str,
    ):
        raise ValueError(
            "'default_priority' "
            "must be a string."
        )

    return True


def load_company_sources_config():
    with COMPANY_SOURCES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(file)

    # IMPORTANT:
    # Production registry schema uses:
    #
    # {
    #     "schema_version": 1,
    #     "companies": [...]
    # }
    #
    # We validate against the exact same
    # source_registry schema used by main.py.
    validate_company_sources(
        config
    )

    return config


def save_company_sources_config(
    config,
):
    config[
        "last_updated"
    ] = utc_today()

    validate_company_sources(
        config
    )

    temporary_path = (
        COMPANY_SOURCES_PATH.with_suffix(
            ".tmp"
        )
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            config,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write(
            "\n"
        )

    temporary_path.replace(
        COMPANY_SOURCES_PATH
    )


def normalize_identity_value(
    value,
):
    return (
        value
        or ""
    ).strip().lower()


def source_identity(
    ats,
    identifier,
):
    return (
        normalize_identity_value(
            ats
        ),
        normalize_identity_value(
            identifier
        ),
    )


def get_production_identity_map():
    result = {}

    for source in (
        get_all_company_sources()
    ):
        identity = source_identity(
            source.get(
                "ats"
            ),
            source.get(
                "identifier"
            ),
        )

        result[
            identity
        ] = source

    return result


def slugify(
    value,
):
    text = (
        value
        or ""
    ).strip().lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )

    return text.strip(
        "-"
    )


def build_production_source_id(
    source,
    existing_ids,
):
    identifier_part = slugify(
        source.get(
            "identifier"
        )
    )

    ats_part = slugify(
        source.get(
            "ats"
        )
    )

    base_id = (
        f"{identifier_part}-"
        f"{ats_part}"
    )

    if base_id not in existing_ids:
        return base_id

    company_part = slugify(
        source.get(
            "company"
        )
    )

    base_id = (
        f"{company_part}-"
        f"{ats_part}-"
        f"{identifier_part}"
    )

    if base_id not in existing_ids:
        return base_id

    counter = 2

    while True:
        candidate = (
            f"{base_id}-{counter}"
        )

        if candidate not in existing_ids:
            return candidate

        counter += 1


def get_qualification(
    source,
):
    metadata = source.get(
        "metadata",
        {},
    )

    return metadata.get(
        "qualification"
    )


def evaluate_promotion(
    source,
):
    config = (
        load_promotion_config()
    )

    identity = source_identity(
        source.get(
            "ats"
        ),
        source.get(
            "identifier"
        ),
    )

    production_map = (
        get_production_identity_map()
    )

    # --------------------------------------------------
    # Production registry always wins.
    #
    # Even if discovery state was not updated because
    # of an interrupted previous run, never create a
    # duplicate ATS + identifier entry.
    # --------------------------------------------------

    if identity in production_map:
        return {
            "eligible": False,
            "decision": (
                "already_in_production"
            ),
            "reason": (
                "ATS source already exists "
                "in company_sources.json."
            ),
            "production_source": (
                production_map[
                    identity
                ]
            ),
        }

    if source.get(
        "status"
    ) == "promoted":
        return {
            "eligible": False,
            "decision": (
                "already_promoted"
            ),
            "reason": (
                "Discovery source is already "
                "marked as promoted."
            ),
            "production_source": None,
        }

    if source.get(
        "status"
    ) != "verified":
        return {
            "eligible": False,
            "decision": (
                "source_not_verified"
            ),
            "reason": (
                "Source must be verified "
                "before promotion."
            ),
            "production_source": None,
        }

    qualification = (
        get_qualification(
            source
        )
    )

    if not qualification:
        return {
            "eligible": False,
            "decision": (
                "qualification_missing"
            ),
            "reason": (
                "Source has not completed "
                "qualification."
            ),
            "production_source": None,
        }

    qualification_status = (
        qualification.get(
            "status"
        )
    )

    allowed_statuses = set(
        config[
            "allowed_qualification_statuses"
        ]
    )

    if (
        qualification_status
        not in allowed_statuses
    ):
        return {
            "eligible": False,
            "decision": (
                "qualification_not_allowed"
            ),
            "reason": (
                "Qualification status "
                f"'{qualification_status}' "
                "is not eligible for "
                "automatic promotion."
            ),
            "production_source": None,
        }

    if not qualification.get(
        "qualified",
        False,
    ):
        return {
            "eligible": False,
            "decision": (
                "not_qualified"
            ),
            "reason": (
                "Qualification result "
                "is not approved."
            ),
            "production_source": None,
        }

    verified_markets = (
        qualification.get(
            "verified_markets",
            []
        )
    )

    if not isinstance(
        verified_markets,
        list,
    ):
        return {
            "eligible": False,
            "decision": (
                "invalid_verified_markets"
            ),
            "reason": (
                "Qualification "
                "'verified_markets' "
                "must be a list."
            ),
            "production_source": None,
        }

    if not verified_markets:
        return {
            "eligible": False,
            "decision": (
                "no_verified_markets"
            ),
            "reason": (
                "Source has no verified "
                "target markets."
            ),
            "production_source": None,
        }

    return {
        "eligible": True,
        "decision": "promotable",
        "reason": (
            "Verified source passed "
            "qualification and has "
            "verified target markets."
        ),
        "production_source": None,
    }


def build_production_source(
    source,
    existing_ids,
):
    config = (
        load_promotion_config()
    )

    qualification = (
        get_qualification(
            source
        )
    )

    metadata = source.get(
        "metadata",
        {},
    )

    discovery_metadata = (
        metadata.get(
            "discovery",
            {},
        )
    )

    production_id = (
        build_production_source_id(
            source,
            existing_ids,
        )
    )

    options = metadata.get(
        "options",
        {},
    )

    if not isinstance(
        options,
        dict,
    ):
        options = {}

    verified_markets = sorted(
        set(
            qualification.get(
                "verified_markets",
                [],
            )
        )
    )

    return {
        "id": production_id,
        "company": source[
            "company"
        ],
        "ats": source[
            "ats"
        ],
        "identifier": source[
            "identifier"
        ],
        "enabled": config[
            "default_enabled"
        ],
        "priority": config[
            "default_priority"
        ],
        "markets": (
            verified_markets
        ),
        "discovered_via": (
            source.get(
                "discovered_via",
                "web_search",
            )
        ),
        "last_verified": (
            utc_today()
        ),
        "options": options,
        "discovery_origin": {
            "discovery_source_id": (
                source[
                    "id"
                ]
            ),
            "requested_market": (
                source.get(
                    "market"
                )
            ),
            "query_ids": (
                discovery_metadata.get(
                    "query_ids",
                    [],
                )
            ),
            "matched_roles": (
                discovery_metadata.get(
                    "matched_roles",
                    [],
                )
            ),
        },
    }


def persist_promotion_metadata(
    source_id,
    production_source,
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
            "promotion"
        ] = {
            "promoted_at": (
                utc_now_iso()
            ),
            "production_source_id": (
                production_source[
                    "id"
                ]
            ),
            "markets": (
                production_source[
                    "markets"
                ]
            ),
        }

        save_discovery_registry(
            config
        )

        return

    raise KeyError(
        "Discovery source "
        f"not found: {source_id}"
    )


def promote_source(
    source_id,
    dry_run=False,
):
    source = get_discovered_source(
        source_id
    )

    if source is None:
        raise KeyError(
            "Discovery source "
            f"not found: {source_id}"
        )

    evaluation = (
        evaluate_promotion(
            source
        )
    )

    if not evaluation[
        "eligible"
    ]:
        return {
            "source": source,
            "evaluation": evaluation,
            "promoted": False,
            "dry_run": dry_run,
            "production_source": (
                evaluation.get(
                    "production_source"
                )
            ),
        }

    company_config = (
        load_company_sources_config()
    )

    existing_ids = {
        item[
            "id"
        ]
        for item in company_config[
            "companies"
        ]
    }

    production_source = (
        build_production_source(
            source,
            existing_ids,
        )
    )

    if dry_run:
        return {
            "source": source,
            "evaluation": evaluation,
            "promoted": False,
            "dry_run": True,
            "production_source": (
                production_source
            ),
        }

    # --------------------------------------------------
    # Final duplicate check immediately before write.
    #
    # This protects against accidental double promotion
    # if the registry changed after evaluation.
    # --------------------------------------------------

    identity = source_identity(
        source.get(
            "ats"
        ),
        source.get(
            "identifier"
        ),
    )

    for existing in company_config[
        "companies"
    ]:
        existing_identity = (
            source_identity(
                existing.get(
                    "ats"
                ),
                existing.get(
                    "identifier"
                ),
            )
        )

        if existing_identity == identity:
            return {
                "source": source,
                "evaluation": {
                    "eligible": False,
                    "decision": (
                        "already_in_production"
                    ),
                    "reason": (
                        "ATS source already "
                        "exists in production."
                    ),
                    "production_source": (
                        existing
                    ),
                },
                "promoted": False,
                "dry_run": False,
                "production_source": (
                    existing
                ),
            }

    company_config[
        "companies"
    ].append(
        production_source
    )

    # Validate exact production registry schema
    # before touching the real JSON file.
    validate_company_sources(
        company_config
    )

    save_company_sources_config(
        company_config
    )

    persist_promotion_metadata(
        source_id,
        production_source,
    )

    update_discovery_status(
        source_id,
        "promoted",
    )

    return {
        "source": source,
        "evaluation": evaluation,
        "promoted": True,
        "dry_run": False,
        "production_source": (
            production_source
        ),
    }


def get_promotable_sources():
    promotable = []

    for source in (
        get_all_discovered_sources()
    ):
        evaluation = (
            evaluate_promotion(
                source
            )
        )

        if evaluation[
            "eligible"
        ]:
            promotable.append(
                source
            )

    return promotable


def promote_eligible_sources(
    dry_run=False,
):
    config = (
        load_promotion_config()
    )

    if (
        not config[
            "auto_promotion_enabled"
        ]
        and not dry_run
    ):
        return []

    sources = (
        get_promotable_sources()
    )

    limit = config[
        "max_promotions_per_run"
    ]

    results = []

    for source in sources[
        :limit
    ]:
        result = promote_source(
            source[
                "id"
            ],
            dry_run=dry_run,
        )

        results.append(
            result
        )

    return results