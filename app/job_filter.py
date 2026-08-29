import json
import re

from functools import lru_cache
from pathlib import Path


CONFIG_PATH = Path(
    "config/target_roles.json"
)


def normalize_text(value):
    text = (
        value
        or ""
    ).lower()

    text = text.replace(
        "&",
        " and ",
    )

    text = re.sub(
        r"[\u2010-\u2015_/(),:]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def contains_phrase(
    text,
    phrase,
):
    normalized_phrase = (
        normalize_text(
            phrase
        )
    )

    if not normalized_phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(
            normalized_phrase
        )
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text,
        )
    )


@lru_cache(
    maxsize=1
)
def load_target_roles():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(
            file
        )

    roles = config.get(
        "roles"
    )

    if not isinstance(
        roles,
        list,
    ):
        raise ValueError(
            "target_roles.json must "
            "contain a 'roles' list."
        )

    return config


def get_evidence_matches(
    description,
    evidence_keywords,
):
    matches = []

    for keyword in (
        evidence_keywords
    ):
        if contains_phrase(
            description,
            keyword,
        ):
            matches.append(
                keyword
            )

    return matches


def is_excluded_title(
    title,
    excluded_patterns,
):
    for pattern in (
        excluded_patterns
    ):
        if contains_phrase(
            title,
            pattern,
        ):
            return True

    return False


def match_job_role(job):
    config = (
        load_target_roles()
    )

    title = normalize_text(
        job.get(
            "title",
            "",
        )
    )

    description = normalize_text(
        job.get(
            "description",
            "",
        )
    )

    excluded_patterns = (
        config.get(
            "excluded_title_patterns",
            [],
        )
    )

    if is_excluded_title(
        title,
        excluded_patterns,
    ):
        return None

    evidence_keywords = (
        config.get(
            "evidence_keywords",
            [],
        )
    )

    evidence_matches = (
        get_evidence_matches(
            description,
            evidence_keywords,
        )
    )

    roles = config[
        "roles"
    ]

    for role in roles:
        aliases = role.get(
            "aliases",
            [],
        )

        matched_alias = None

        for alias in aliases:
            if contains_phrase(
                title,
                alias,
            ):
                matched_alias = alias
                break

        if not matched_alias:
            continue

        requires_evidence = (
            role.get(
                "requires_evidence",
                False,
            )
        )

        minimum_evidence = (
            role.get(
                "minimum_evidence_matches",
                0,
            )
        )

        if (
            requires_evidence
            and len(
                evidence_matches
            ) < minimum_evidence
        ):
            continue

        return {
            "role": role[
                "name"
            ],
            "priority": role.get(
                "priority",
                "unknown",
            ),
            "matched_alias": (
                matched_alias
            ),
            "evidence_matches": (
                evidence_matches
            ),
        }

    return None


def is_relevant_job(job):
    return (
        match_job_role(
            job
        )
        is not None
    )


def filter_jobs(jobs):
    relevant_jobs = []

    for job in jobs:
        if is_relevant_job(
            job
        ):
            relevant_jobs.append(
                job
            )

    return relevant_jobs