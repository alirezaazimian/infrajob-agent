import json

from datetime import datetime, timezone
from pathlib import Path


CONFIG_PATH = Path(
    "config/discovered_sources.json"
)


VALID_STATUSES = {
    "discovered",
    "verifying",
    "verified",
    "rejected",
    "promoted",
}


SUPPORTED_ATS = {
    "greenhouse",
    "personio",
    "lever",
    "ashby",
    "unknown",
}


REQUIRED_FIELDS = {
    "id",
    "company",
    "ats",
    "identifier",
    "market",
    "status",
    "discovered_via",
    "discovered_at",
}


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


def load_discovery_registry():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Discovery registry not found: "
            f"{CONFIG_PATH}"
        )

    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    validate_discovery_registry(
        config
    )

    return config


def save_discovery_registry(
    config,
):
    validate_discovery_registry(
        config
    )

    config[
        "last_updated"
    ] = datetime.now().date().isoformat()

    with CONFIG_PATH.open(
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


def validate_discovery_registry(
    config,
):
    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "Discovery registry must "
            "be a JSON object."
        )

    sources = config.get(
        "sources"
    )

    if not isinstance(
        sources,
        list,
    ):
        raise ValueError(
            "Discovery registry must "
            "contain a 'sources' list."
        )

    seen_ids = set()

    for index, source in enumerate(
        sources,
        start=1,
    ):
        if not isinstance(
            source,
            dict,
        ):
            raise ValueError(
                f"Discovery source #{index} "
                "must be an object."
            )

        missing = (
            REQUIRED_FIELDS
            - source.keys()
        )

        if missing:
            raise ValueError(
                f"Discovery source #{index} "
                f"is missing fields: "
                f"{sorted(missing)}"
            )

        source_id = source[
            "id"
        ]

        if source_id in seen_ids:
            raise ValueError(
                f"Duplicate discovery "
                f"source id: {source_id}"
            )

        seen_ids.add(
            source_id
        )

        ats = source[
            "ats"
        ]

        if ats not in SUPPORTED_ATS:
            raise ValueError(
                f"Unsupported ATS "
                f"'{ats}' for "
                f"{source_id}"
            )

        status = source[
            "status"
        ]

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid discovery "
                f"status '{status}' "
                f"for {source_id}"
            )

    return True


def get_all_discovered_sources():
    config = (
        load_discovery_registry()
    )

    return config[
        "sources"
    ]


def get_sources_by_status(
    status,
):
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid discovery "
            f"status: {status}"
        )

    return [
        source
        for source in (
            get_all_discovered_sources()
        )
        if source[
            "status"
        ] == status
    ]


def get_discovered_source(
    source_id,
):
    for source in (
        get_all_discovered_sources()
    ):
        if source[
            "id"
        ] == source_id:
            return source

    return None


def source_exists(
    source_id,
):
    return (
        get_discovered_source(
            source_id
        )
        is not None
    )


def build_source_id(
    company,
    ats,
    identifier,
):
    company_part = (
        company
        .strip()
        .lower()
        .replace(
            " ",
            "-",
        )
    )

    company_part = "".join(
        character
        for character in company_part
        if (
            character.isalnum()
            or character == "-"
        )
    )

    ats_part = (
        ats
        .strip()
        .lower()
    )

    identifier_part = (
        identifier
        .strip()
        .lower()
        .replace(
            " ",
            "-",
        )
    )

    identifier_part = "".join(
        character
        for character in identifier_part
        if (
            character.isalnum()
            or character in {
                "-",
                "_",
            }
        )
    )

    return (
        f"{company_part}:"
        f"{ats_part}:"
        f"{identifier_part}"
    )


def add_discovered_source(
    company,
    ats,
    identifier,
    market,
    discovered_via,
    source_url=None,
    metadata=None,
):
    if ats not in SUPPORTED_ATS:
        raise ValueError(
            f"Unsupported ATS: "
            f"{ats}"
        )

    source_id = build_source_id(
        company,
        ats,
        identifier,
    )

    config = (
        load_discovery_registry()
    )

    for existing in config[
        "sources"
    ]:
        if existing[
            "id"
        ] == source_id:
            return existing

    source = {
        "id": source_id,
        "company": company,
        "ats": ats,
        "identifier": identifier,
        "market": (
            market
            .strip()
            .upper()
        ),
        "status": "discovered",
        "discovered_via": (
            discovered_via
        ),
        "discovered_at": (
            utc_now_iso()
        ),
        "source_url": (
            source_url
        ),
        "verified_at": None,
        "rejection_reason": None,
        "metadata": (
            metadata
            or {}
        ),
    }

    config[
        "sources"
    ].append(
        source
    )

    save_discovery_registry(
        config
    )

    return source


def update_discovery_status(
    source_id,
    status,
    rejection_reason=None,
):
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid discovery "
            f"status: {status}"
        )

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

        source[
            "status"
        ] = status

        if status == "verified":
            source[
                "verified_at"
            ] = utc_now_iso()

            source[
                "rejection_reason"
            ] = None

        elif status == "rejected":
            source[
                "rejection_reason"
            ] = (
                rejection_reason
                or "unspecified"
            )

        elif status == "promoted":
            source[
                "rejection_reason"
            ] = None

        save_discovery_registry(
            config
        )

        return source

    raise KeyError(
        f"Discovery source not found: "
        f"{source_id}"
    )


def remove_discovered_source(
    source_id,
):
    config = (
        load_discovery_registry()
    )

    original_count = len(
        config[
            "sources"
        ]
    )

    config[
        "sources"
    ] = [
        source
        for source in config[
            "sources"
        ]
        if source[
            "id"
        ] != source_id
    ]

    if len(
        config[
            "sources"
        ]
    ) == original_count:
        return False

    save_discovery_registry(
        config
    )

    return True