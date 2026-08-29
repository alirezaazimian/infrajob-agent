import json
from datetime import date
from pathlib import Path


CONFIG_PATH = Path(
    "config/immigration_rules.json"
)


def load_immigration_rules():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_country_rule(country_code):
    if not country_code:
        return None

    config = load_immigration_rules()

    normalized_code = (
        country_code
        .strip()
        .upper()
    )

    for country in config["countries"]:
        if (
            country["code"]
            == normalized_code
        ):
            return country

    return None


def get_enabled_country_rules():
    config = load_immigration_rules()

    return [
        country
        for country in config["countries"]
        if country.get(
            "enabled",
            False,
        )
    ]


def get_country_pathways(
    country_code,
):
    country = get_country_rule(
        country_code
    )

    if not country:
        return []

    return country.get(
        "pathways",
        [],
    )


def parse_date(value):
    if not value:
        return None

    return date.fromisoformat(
        value
    )


def is_pathway_current(
    pathway,
    current_date=None,
):
    if current_date is None:
        current_date = date.today()

    valid_from = parse_date(
        pathway.get(
            "valid_from"
        )
    )

    valid_until = parse_date(
        pathway.get(
            "valid_until"
        )
    )

    if (
        valid_from
        and current_date < valid_from
    ):
        return False

    if (
        valid_until
        and current_date > valid_until
    ):
        return False

    return True


def get_current_pathways(
    country_code,
    current_date=None,
):
    pathways = get_country_pathways(
        country_code
    )

    return [
        pathway
        for pathway in pathways
        if is_pathway_current(
            pathway,
            current_date,
        )
    ]