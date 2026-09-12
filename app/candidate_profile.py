from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PROFILE_PATH = Path("config/candidate_profile.json")

ALLOWED_SKILL_LEVELS = {
    "basic",
    "working",
    "strong",
    "expert",
}

ALLOWED_LANGUAGE_LEVELS = {
    "unknown",
    "basic",
    "intermediate",
    "advanced",
    "native",
}

ALLOWED_RELOCATION_VALUES = {
    "open",
    "conditional",
    "not_open",
    "unknown",
}


class CandidateProfileError(ValueError):
    pass


def load_candidate_profile(
    path: str | Path = DEFAULT_PROFILE_PATH,
) -> dict[str, Any]:
    profile_path = Path(path)

    if not profile_path.exists():
        raise CandidateProfileError(
            f"Candidate profile not found: {profile_path}"
        )

    try:
        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as exc:
        raise CandidateProfileError(
            f"Candidate profile is not valid JSON: {exc}"
        ) from exc

    validate_candidate_profile(
        profile
    )

    return profile


def validate_candidate_profile(
    profile: dict[str, Any],
) -> None:
    required_top_level = {
        "schema_version",
        "target_roles",
        "work_arrangement",
        "mobility",
        "education",
        "certifications",
        "training",
        "languages",
        "skills",
        "experience",
        "matching_policy",
    }

    missing = sorted(
        required_top_level
        - set(
            profile.keys()
        )
    )

    if missing:
        raise CandidateProfileError(
            "Candidate profile is missing required fields: "
            + ", ".join(
                missing
            )
        )

    _validate_target_roles(
        profile["target_roles"]
    )

    _validate_work_arrangement(
        profile[
            "work_arrangement"
        ]
    )

    _validate_mobility(
        profile[
            "mobility"
        ]
    )

    _validate_languages(
        profile[
            "languages"
        ]
    )

    _validate_skills(
        profile[
            "skills"
        ]
    )

    _validate_experience(
        profile[
            "experience"
        ]
    )


def get_skill_index(
    profile: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    validate_candidate_profile(
        profile
    )

    return {
        skill["name"].strip().lower(): skill
        for skill in profile["skills"]
    }


def get_language_index(
    profile: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    validate_candidate_profile(
        profile
    )

    return {
        item["language"].strip().lower(): item
        for item in profile["languages"]
    }


def supports_work_arrangement(
    profile: dict[str, Any],
    mode: str,
) -> bool:
    validate_candidate_profile(
        profile
    )

    normalized = (
        mode
        or "unknown"
    ).strip().lower()

    if normalized in {
        "unknown",
        "mixed_or_unclear",
    }:
        return True

    return bool(
        profile[
            "work_arrangement"
        ].get(
            normalized,
            False,
        )
    )


def _validate_target_roles(
    target_roles: Any,
) -> None:
    if not isinstance(
        target_roles,
        dict,
    ):
        raise CandidateProfileError(
            "target_roles must be an object"
        )

    primary = target_roles.get(
        "primary",
        [],
    )

    if (
        not isinstance(
            primary,
            list,
        )
        or not primary
    ):
        raise CandidateProfileError(
            "target_roles.primary must contain at least one role"
        )


def _validate_work_arrangement(
    arrangement: Any,
) -> None:
    if not isinstance(
        arrangement,
        dict,
    ):
        raise CandidateProfileError(
            "work_arrangement must be an object"
        )

    for field in (
        "remote",
        "hybrid",
        "onsite",
        "remote_required",
    ):
        if not isinstance(
            arrangement.get(
                field
            ),
            bool,
        ):
            raise CandidateProfileError(
                f"work_arrangement.{field} must be boolean"
            )

    if (
        arrangement[
            "remote_required"
        ]
        and not arrangement[
            "remote"
        ]
    ):
        raise CandidateProfileError(
            "remote_required cannot be true when remote is false"
        )


def _validate_mobility(
    mobility: Any,
) -> None:
    if not isinstance(
        mobility,
        dict,
    ):
        raise CandidateProfileError(
            "mobility must be an object"
        )

    relocation = mobility.get(
        "relocation",
        "unknown",
    )

    if (
        relocation
        not in ALLOWED_RELOCATION_VALUES
    ):
        raise CandidateProfileError(
            f"Unsupported relocation value: {relocation}"
        )


def _validate_languages(
    languages: Any,
) -> None:
    if not isinstance(
        languages,
        list,
    ):
        raise CandidateProfileError(
            "languages must be a list"
        )

    seen = set()

    for item in languages:
        if not isinstance(
            item,
            dict,
        ):
            raise CandidateProfileError(
                "Each language entry must be an object"
            )

        language = (
            item.get(
                "language",
                "",
            )
            .strip()
            .lower()
        )

        if not language:
            raise CandidateProfileError(
                "Language name cannot be empty"
            )

        if language in seen:
            raise CandidateProfileError(
                f"Duplicate language: {language}"
            )

        seen.add(
            language
        )

        level = item.get(
            "level",
            "unknown",
        )

        if (
            level
            not in ALLOWED_LANGUAGE_LEVELS
        ):
            raise CandidateProfileError(
                f"Unsupported language level for {language}: {level}"
            )


def _validate_skills(
    skills: Any,
) -> None:
    if not isinstance(
        skills,
        list,
    ):
        raise CandidateProfileError(
            "skills must be a list"
        )

    seen = set()

    for skill in skills:
        if not isinstance(
            skill,
            dict,
        ):
            raise CandidateProfileError(
                "Each skill entry must be an object"
            )

        name = (
            skill.get(
                "name",
                "",
            )
            .strip()
            .lower()
        )

        if not name:
            raise CandidateProfileError(
                "Skill name cannot be empty"
            )

        if name in seen:
            raise CandidateProfileError(
                f"Duplicate skill: {name}"
            )

        seen.add(
            name
        )

        level = skill.get(
            "level"
        )

        if (
            level
            not in ALLOWED_SKILL_LEVELS
        ):
            raise CandidateProfileError(
                f"Unsupported skill level for {name}: {level}"
            )

        years = skill.get(
            "years"
        )

        if (
            years is not None
            and (
                not isinstance(
                    years,
                    (
                        int,
                        float,
                    ),
                )
                or years < 0
            )
        ):
            raise CandidateProfileError(
                f"Skill years must be null or non-negative for {name}"
            )


def _validate_experience(
    experience: Any,
) -> None:
    if not isinstance(
        experience,
        dict,
    ):
        raise CandidateProfileError(
            "experience must be an object"
        )

    for field in (
        "total_years",
        "linux_admin_years",
        "infrastructure_years",
    ):
        value = experience.get(
            field
        )

        if (
            value is not None
            and (
                not isinstance(
                    value,
                    (
                        int,
                        float,
                    ),
                )
                or value < 0
            )
        ):
            raise CandidateProfileError(
                f"experience.{field} must be null or non-negative"
            )
