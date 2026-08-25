import json
from pathlib import Path


CONFIG_PATH = Path("config/sources.json")


def load_sources():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)