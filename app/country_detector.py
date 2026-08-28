import json
import re
import unicodedata
from pathlib import Path


CONFIG_PATH = Path("config/country_aliases.json")


def normalize_location(value):
    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(value.split())


def load_country_aliases():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def contains_alias(location, alias):
    normalized_alias = normalize_location(alias)

    location_with_spaces = f" {location} "
    alias_with_spaces = f" {normalized_alias} "

    return alias_with_spaces in location_with_spaces


def detect_country(location):
    normalized_location = normalize_location(
        location
    )

    if not normalized_location:
        return {
            "country_code": None,
            "country": None,
            "matched_on": None,
            "confidence": "unknown",
        }

    config = load_country_aliases()

    # First prefer explicit country names.
    for country in config["countries"]:
        for alias in country["country_aliases"]:
            if contains_alias(
                normalized_location,
                alias,
            ):
                return {
                    "country_code": country["code"],
                    "country": country["name"],
                    "matched_on": alias,
                    "confidence": "high",
                }

    # If no country name exists, try known cities.
    for country in config["countries"]:
        for city in country["city_aliases"]:
            if contains_alias(
                normalized_location,
                city,
            ):
                return {
                    "country_code": country["code"],
                    "country": country["name"],
                    "matched_on": city,
                    "confidence": "medium",
                }

    return {
        "country_code": None,
        "country": None,
        "matched_on": None,
        "confidence": "unknown",
    }