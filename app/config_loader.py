import json
from pathlib import Path


CONFIG_DIR = Path("config")


def load_sources():
    config_path = CONFIG_DIR / "sources.json"

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_target_markets():
    config_path = CONFIG_DIR / "target_markets.json"

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_enabled_markets():
    config = load_target_markets()

    return [
        market
        for market in config["markets"]
        if market.get("enabled", False)
    ]


def load_target_roles():
    config_path = CONFIG_DIR / "target_roles.json"

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)