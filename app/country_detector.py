import json
import re
import unicodedata

from pathlib import Path


CONFIG_PATH = Path(
    "config/country_aliases.json"
)


def normalize_location(
    value,
):
    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def normalize_region_source(
    value,
):
    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = value.upper()

    # D.C. -> DC
    value = value.replace(
        ".",
        "",
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def load_country_aliases():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


def contains_alias(
    location,
    alias,
):
    normalized_alias = (
        normalize_location(
            alias
        )
    )

    if not normalized_alias:
        return False

    location_with_spaces = (
        f" {location} "
    )

    alias_with_spaces = (
        f" {normalized_alias} "
    )

    return (
        alias_with_spaces
        in location_with_spaces
    )


def is_short_region_alias(
    alias,
):
    compact = re.sub(
        r"[^A-Za-z]",
        "",
        alias or "",
    )

    return (
        compact.isalpha()
        and 2 <= len(compact) <= 3
    )


def contains_short_region_alias(
    raw_location,
    alias,
):
    source = (
        normalize_region_source(
            raw_location
        )
    )

    compact_alias = re.sub(
        r"[^A-Za-z]",
        "",
        alias or "",
    ).upper()

    if not compact_alias:
        return False

    # --------------------------------------------------
    # Short region codes are dangerous.
    #
    # Examples:
    #   IN  -> Indiana, but also English "in"
    #   OR  -> Oregon, but also English "or"
    #   DE  -> Delaware, but also Germany's ISO code
    #
    # Therefore a short region abbreviation is only
    # accepted in a structured location segment.
    #
    # Valid:
    #   Annapolis Junction, MD
    #   Melbourne, FL
    #   Washington, DC
    #   Palo Alto, CA
    #
    # Not valid:
    #   Remote in Germany
    # --------------------------------------------------

    pattern = (
        r"(?:^|[,;/|]\s*)"
        + re.escape(
            compact_alias
        )
        + r"(?=\s*(?:$|[,;/|()\[\]\-]))"
    )

    return (
        re.search(
            pattern,
            source,
        )
        is not None
    )


def contains_region_alias(
    raw_location,
    normalized_location,
    alias,
):
    if is_short_region_alias(
        alias
    ):
        return (
            contains_short_region_alias(
                raw_location,
                alias,
            )
        )

    return contains_alias(
        normalized_location,
        alias,
    )


def build_country_result(
    country,
    matched_on,
    matched_type,
    confidence,
):
    return {
        "country_code": (
            country[
                "code"
            ]
        ),
        "country": (
            country[
                "name"
            ]
        ),
        "matched_on": (
            matched_on
        ),
        "matched_type": (
            matched_type
        ),
        "confidence": (
            confidence
        ),
    }


def unknown_country_result():
    return {
        "country_code": None,
        "country": None,
        "matched_on": None,
        "matched_type": None,
        "confidence": "unknown",
    }


def detect_country(
    location,
):
    raw_location = (
        location
        or ""
    )

    normalized_location = (
        normalize_location(
            raw_location
        )
    )

    if not normalized_location:
        return (
            unknown_country_result()
        )

    config = (
        load_country_aliases()
    )

    countries = config[
        "countries"
    ]

    # --------------------------------------------------
    # 1. Explicit country names
    #
    # Highest-confidence source of geographic data.
    #
    # Examples:
    #   Berlin, Germany
    #   London, United Kingdom
    #   Paris, France
    # --------------------------------------------------

    for country in countries:
        for alias in country.get(
            "country_aliases",
            [],
        ):
            if contains_alias(
                normalized_location,
                alias,
            ):
                return (
                    build_country_result(
                        country,
                        alias,
                        "country",
                        "high",
                    )
                )

    # --------------------------------------------------
    # 2. Region / state / province
    #
    # IMPORTANT:
    # Region matching happens BEFORE city matching.
    #
    # This fixes ambiguous cities such as:
    #
    #   Melbourne, FL
    #
    # Without region awareness:
    #   Melbourne -> Australia
    #
    # With region awareness:
    #   FL -> Florida -> United States
    # --------------------------------------------------

    for country in countries:
        for alias in country.get(
            "region_aliases",
            [],
        ):
            if contains_region_alias(
                raw_location,
                normalized_location,
                alias,
            ):
                return (
                    build_country_result(
                        country,
                        alias,
                        "region",
                        "high",
                    )
                )

    # --------------------------------------------------
    # 3. Known cities
    #
    # Lower confidence because city names may be
    # ambiguous across countries.
    # --------------------------------------------------

    for country in countries:
        for city in country.get(
            "city_aliases",
            [],
        ):
            if contains_alias(
                normalized_location,
                city,
            ):
                return (
                    build_country_result(
                        country,
                        city,
                        "city",
                        "medium",
                    )
                )

    return unknown_country_result()