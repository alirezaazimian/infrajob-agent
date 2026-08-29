import json
from pathlib import Path


CONFIG_PATH = Path(
    "config/company_sources.json"
)


SUPPORTED_ATS = {
    "greenhouse",
    "personio",
    "lever",
    "ashby",
}


REQUIRED_FIELDS = {
    "id",
    "company",
    "ats",
    "identifier",
    "enabled",
    "priority",
    "markets",
}


def validate_company_sources(
    config,
):
    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "Company source registry "
            "must be a JSON object."
        )

    companies = config.get(
        "companies"
    )

    if not isinstance(
        companies,
        list,
    ):
        raise ValueError(
            "Registry must contain "
            "a 'companies' list."
        )

    seen_ids = set()

    for index, source in enumerate(
        companies,
        start=1,
    ):
        if not isinstance(
            source,
            dict,
        ):
            raise ValueError(
                f"Registry entry #{index} "
                "must be an object."
            )

        missing_fields = (
            REQUIRED_FIELDS
            - source.keys()
        )

        if missing_fields:
            raise ValueError(
                f"Registry entry #{index} "
                f"is missing fields: "
                f"{sorted(missing_fields)}"
            )

        source_id = source[
            "id"
        ]

        if source_id in seen_ids:
            raise ValueError(
                f"Duplicate source id: "
                f"{source_id}"
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

        markets = source[
            "markets"
        ]

        if not isinstance(
            markets,
            list,
        ):
            raise ValueError(
                f"'markets' must be "
                f"a list for "
                f"{source_id}"
            )

        if not markets:
            raise ValueError(
                f"'markets' cannot be "
                f"empty for "
                f"{source_id}"
            )

        options = source.get(
            "options",
            {},
        )

        if not isinstance(
            options,
            dict,
        ):
            raise ValueError(
                f"'options' must be "
                f"an object for "
                f"{source_id}"
            )

    return True


def load_company_sources():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    validate_company_sources(
        config
    )

    return config


def get_all_company_sources():
    config = (
        load_company_sources()
    )

    return config[
        "companies"
    ]


def get_enabled_company_sources():
    return [
        source
        for source in (
            get_all_company_sources()
        )
        if source.get(
            "enabled",
            False,
        )
    ]


def get_source_by_id(
    source_id,
):
    for source in (
        get_all_company_sources()
    ):
        if source[
            "id"
        ] == source_id:
            return source

    return None


def get_sources_by_ats(
    ats,
    include_disabled=False,
):
    sources = (
        get_all_company_sources()
    )

    results = []

    for source in sources:
        if source[
            "ats"
        ] != ats:
            continue

        if (
            not include_disabled
            and not source.get(
                "enabled",
                False,
            )
        ):
            continue

        results.append(
            source
        )

    return results


def get_sources_for_market(
    country_code,
    include_global=True,
    include_disabled=False,
):
    normalized_code = (
        country_code
        .strip()
        .upper()
    )

    results = []

    for source in (
        get_all_company_sources()
    ):
        if (
            not include_disabled
            and not source.get(
                "enabled",
                False,
            )
        ):
            continue

        markets = source.get(
            "markets",
            [],
        )

        direct_match = (
            normalized_code
            in markets
        )

        global_match = (
            include_global
            and "GLOBAL"
            in markets
        )

        if (
            direct_match
            or global_match
        ):
            results.append(
                source
            )

    return results