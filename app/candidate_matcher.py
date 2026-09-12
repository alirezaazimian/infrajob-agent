from __future__ import annotations

from typing import Any

from app.candidate_profile import (
    get_language_index,
    get_skill_index,
    supports_work_arrangement,
    validate_candidate_profile,
)


MATCHER_VERSION = "m23.1"

STATUS_MATCH = "match"
STATUS_PARTIAL = "partial"
STATUS_GAP = "gap"
STATUS_UNKNOWN = "unknown"
STATUS_NOT_APPLICABLE = "not_applicable"

STATUS_SCORES = {
    STATUS_MATCH: 1.0,
    STATUS_PARTIAL: 0.5,
    STATUS_GAP: 0.0,
}

SKILL_LEVEL_RANK = {
    "basic": 1,
    "working": 2,
    "strong": 3,
    "expert": 4,
}

LANGUAGE_LEVEL_RANK = {
    "unknown": 0,
    "basic": 1,
    "intermediate": 2,
    "advanced": 3,
    "native": 4,
}

EDUCATION_LEVEL_RANK = {
    "high_school": 1,
    "associate": 2,
    "bachelors": 3,
    "masters": 4,
    "doctorate": 5,
    "phd": 5,
}


def match_candidate_to_requirements(
    profile: dict[str, Any],
    requirements: dict[str, Any],
    *,
    country: str | None = None,
) -> dict[str, Any]:
    """
    Compare one structured candidate profile with one structured vacancy
    requirement payload.

    This matcher is conservative:
    - Missing candidate evidence becomes UNKNOWN rather than a fabricated match.
    - Exact years are never inferred from skill presence.
    - Training is not treated as certification.
    - Remote is not a gate when the candidate accepts onsite/hybrid.
    """

    validate_candidate_profile(profile)

    if not isinstance(requirements, dict):
        raise ValueError(
            "requirements must be a dictionary"
        )

    skills = _match_skills(
        profile,
        requirements.get(
            "skills",
            {},
        ),
    )

    languages = _match_languages(
        profile,
        requirements.get(
            "languages",
            {},
        ),
    )

    experience = _match_experience(
        profile,
        requirements.get(
            "experience",
            {},
        ),
    )

    education = _match_education(
        profile,
        requirements.get(
            "education",
            {},
        ),
    )

    work_authorization = (
        _match_work_authorization(
            profile,
            requirements.get(
                "work_authorization",
                {},
            ),
            country=country,
        )
    )

    location = _match_location(
        profile,
        requirements.get(
            "location",
            {},
        ),
    )

    categories = {
        "skills": skills,
        "languages": languages,
        "experience": experience,
        "education": education,
        "work_authorization": work_authorization,
        "location": location,
    }

    flattened = _flatten_results(
        categories
    )

    summary = _build_summary(
        flattened
    )

    return {
        "version": MATCHER_VERSION,
        "summary": summary,
        "categories": categories,
    }


def _match_skills(
    profile: dict[str, Any],
    skill_requirements: Any,
) -> dict[str, Any]:
    if not isinstance(
        skill_requirements,
        dict,
    ):
        skill_requirements = {}

    skill_index = get_skill_index(
        profile
    )

    required = _normalized_list(
        skill_requirements.get(
            "required",
            [],
        )
    )

    preferred = _normalized_list(
        skill_requirements.get(
            "preferred",
            [],
        )
    )

    mentioned = _normalized_list(
        skill_requirements.get(
            "mentioned",
            [],
        )
    )

    required_results = [
        _match_one_skill(
            skill_index,
            name,
            importance="required",
        )
        for name in required
    ]

    preferred_results = [
        _match_one_skill(
            skill_index,
            name,
            importance="preferred",
        )
        for name in preferred
        if name not in required
    ]

    neutral_results = [
        _match_one_skill(
            skill_index,
            name,
            importance="mentioned",
        )
        for name in mentioned
        if (
            name not in required
            and name not in preferred
        )
    ]

    return {
        "required": required_results,
        "preferred": preferred_results,
        "mentioned": neutral_results,
    }


def _match_one_skill(
    skill_index: dict[str, dict[str, Any]],
    name: str,
    *,
    importance: str,
) -> dict[str, Any]:
    candidate = skill_index.get(
        name
    )

    if candidate is None:
        return {
            "requirement": name,
            "importance": importance,
            "status": (
                STATUS_GAP
                if importance == "required"
                else STATUS_UNKNOWN
            ),
            "candidate_level": None,
            "candidate_years": None,
            "reason": "skill is not present in the candidate profile",
        }

    level = candidate.get(
        "level",
        "basic",
    )

    confidence = candidate.get(
        "confidence",
        "unknown",
    )

    rank = SKILL_LEVEL_RANK.get(
        level,
        0,
    )

    if rank >= 2:
        status = STATUS_MATCH
    elif rank == 1:
        status = STATUS_PARTIAL
    else:
        status = STATUS_UNKNOWN

    if confidence in {
        "training_only",
        "limited_evidence",
    } and status == STATUS_MATCH:
        status = STATUS_PARTIAL

    return {
        "requirement": name,
        "importance": importance,
        "status": status,
        "candidate_level": level,
        "candidate_years": candidate.get(
            "years"
        ),
        "confidence": confidence,
        "reason": _skill_reason(
            status,
            level,
            confidence,
        ),
    }


def _match_languages(
    profile: dict[str, Any],
    language_requirements: Any,
) -> dict[str, Any]:
    if not isinstance(
        language_requirements,
        dict,
    ):
        language_requirements = {}

    language_index = get_language_index(
        profile
    )

    required = _normalized_list(
        language_requirements.get(
            "required",
            [],
        )
    )

    preferred = _normalized_list(
        language_requirements.get(
            "preferred",
            [],
        )
    )

    mentioned = _normalized_list(
        language_requirements.get(
            "mentioned",
            [],
        )
    )

    required_results = [
        _match_one_language(
            language_index,
            language,
            importance="required",
        )
        for language in required
    ]

    preferred_results = [
        _match_one_language(
            language_index,
            language,
            importance="preferred",
        )
        for language in preferred
        if language not in required
    ]

    mentioned_results = [
        _match_one_language(
            language_index,
            language,
            importance="mentioned",
        )
        for language in mentioned
        if (
            language not in required
            and language not in preferred
        )
    ]

    return {
        "required": required_results,
        "preferred": preferred_results,
        "mentioned": mentioned_results,
    }


def _match_one_language(
    language_index: dict[str, dict[str, Any]],
    language: str,
    *,
    importance: str,
) -> dict[str, Any]:
    candidate = language_index.get(
        language
    )

    if candidate is None:
        return {
            "requirement": language,
            "importance": importance,
            "status": (
                STATUS_GAP
                if importance == "required"
                else STATUS_UNKNOWN
            ),
            "candidate_level": None,
            "reason": "required language is not present in the candidate profile",
        }

    level = candidate.get(
        "level",
        "unknown",
    )

    rank = LANGUAGE_LEVEL_RANK.get(
        level,
        0,
    )

    if rank >= 2:
        status = STATUS_MATCH
    elif rank == 1:
        status = STATUS_PARTIAL
    else:
        status = STATUS_UNKNOWN

    return {
        "requirement": language,
        "importance": importance,
        "status": status,
        "candidate_level": level,
        "confidence": candidate.get(
            "confidence",
            "unknown",
        ),
        "reason": (
            f"candidate language level is {level}"
        ),
    }


def _match_experience(
    profile: dict[str, Any],
    experience_requirements: Any,
) -> dict[str, Any]:
    if not isinstance(
        experience_requirements,
        dict,
    ):
        experience_requirements = {}

    explicit = bool(
        experience_requirements.get(
            "explicit",
            False,
        )
    )

    minimum_years = (
        experience_requirements.get(
            "minimum_years"
        )
    )

    if (
        not explicit
        or minimum_years is None
    ):
        return {
            "status": STATUS_NOT_APPLICABLE,
            "minimum_years": minimum_years,
            "candidate_years": profile[
                "experience"
            ].get(
                "total_years"
            ),
            "reason": "no explicit overall minimum-experience requirement was extracted",
        }

    candidate_years = profile[
        "experience"
    ].get(
        "total_years"
    )

    if candidate_years is None:
        return {
            "status": STATUS_UNKNOWN,
            "minimum_years": minimum_years,
            "candidate_years": None,
            "reason": "candidate total experience years are not verified",
        }

    if candidate_years >= minimum_years:
        status = STATUS_MATCH
        reason = (
            "verified candidate experience meets or exceeds "
            "the extracted minimum"
        )
    else:
        status = STATUS_GAP
        reason = (
            "verified candidate experience is below "
            "the extracted minimum"
        )

    return {
        "status": status,
        "minimum_years": minimum_years,
        "candidate_years": candidate_years,
        "reason": reason,
    }


def _match_education(
    profile: dict[str, Any],
    education_requirements: Any,
) -> dict[str, Any]:
    if not isinstance(
        education_requirements,
        dict,
    ):
        education_requirements = {}

    explicit = bool(
        education_requirements.get(
            "explicit",
            False,
        )
    )

    levels = _normalized_list(
        education_requirements.get(
            "levels",
            [],
        )
    )

    required = bool(
        education_requirements.get(
            "required",
            False,
        )
    )

    preferred_only = bool(
        education_requirements.get(
            "preferred_only",
            False,
        )
    )

    if (
        not explicit
        or not levels
    ):
        return {
            "status": STATUS_NOT_APPLICABLE,
            "required_levels": levels,
            "reason": "no explicit education level requirement was extracted",
        }

    candidate_levels = [
        str(
            item.get(
                "level",
                "",
            )
        ).strip().lower()
        for item in profile[
            "education"
        ]
        if item.get(
            "status"
        ) == "completed"
    ]

    candidate_rank = max(
        (
            EDUCATION_LEVEL_RANK.get(
                level,
                0,
            )
            for level in candidate_levels
        ),
        default=0,
    )

    required_rank = min(
        (
            EDUCATION_LEVEL_RANK.get(
                level,
                999,
            )
            for level in levels
        ),
        default=999,
    )

    if (
        candidate_rank > 0
        and required_rank < 999
        and candidate_rank >= required_rank
    ):
        status = STATUS_MATCH
        reason = (
            "candidate completed education meets or exceeds "
            "the extracted level"
        )
    elif required:
        status = STATUS_GAP
        reason = (
            "candidate completed education does not meet "
            "the extracted required level"
        )
    elif preferred_only:
        status = STATUS_PARTIAL
        reason = (
            "candidate education does not meet the extracted preferred level"
        )
    else:
        status = STATUS_UNKNOWN
        reason = (
            "education equivalence cannot be determined confidently"
        )

    return {
        "status": status,
        "required_levels": levels,
        "candidate_levels": candidate_levels,
        "required": required,
        "preferred_only": preferred_only,
        "reason": reason,
    }


def _match_work_authorization(
    profile: dict[str, Any],
    authorization_requirements: Any,
    *,
    country: str | None,
) -> dict[str, Any]:
    if not isinstance(
        authorization_requirements,
        dict,
    ):
        authorization_requirements = {}

    explicit_local = bool(
        authorization_requirements.get(
            "explicit_local_authorization_required",
            False,
        )
    )

    if not explicit_local:
        return {
            "status": STATUS_NOT_APPLICABLE,
            "country": country,
            "reason": "no explicit local work-authorization requirement was extracted",
        }

    if not country:
        return {
            "status": STATUS_UNKNOWN,
            "country": None,
            "reason": "vacancy country is unknown",
        }

    authorization_map = profile[
        "mobility"
    ].get(
        "work_authorization_by_country",
        {},
    )

    normalized_map = {
        str(key).strip().lower(): value
        for key, value in authorization_map.items()
    }

    value = normalized_map.get(
        country.strip().lower()
    )

    if value is True:
        status = STATUS_MATCH
        reason = (
            "candidate profile confirms work authorization "
            "for the vacancy country"
        )
    elif value is False:
        status = STATUS_GAP
        reason = (
            "candidate profile confirms no current work authorization "
            "for the vacancy country"
        )
    else:
        status = STATUS_UNKNOWN
        reason = (
            "candidate work authorization for the vacancy country "
            "has not been verified"
        )

    return {
        "status": status,
        "country": country,
        "reason": reason,
    }


def _match_location(
    profile: dict[str, Any],
    location_requirements: Any,
) -> dict[str, Any]:
    if not isinstance(
        location_requirements,
        dict,
    ):
        location_requirements = {}

    mode = (
        location_requirements.get(
            "mode",
            "unknown",
        )
        or "unknown"
    ).strip().lower()

    if mode in {
        "unknown",
        "mixed_or_unclear",
    }:
        return {
            "status": STATUS_UNKNOWN,
            "mode": mode,
            "reason": "vacancy work-location mode is not clear",
        }

    supported = supports_work_arrangement(
        profile,
        mode,
    )

    return {
        "status": (
            STATUS_MATCH
            if supported
            else STATUS_GAP
        ),
        "mode": mode,
        "reason": (
            f"candidate {'accepts' if supported else 'does not accept'} "
            f"{mode} work"
        ),
    }


def _flatten_results(
    categories: dict[str, Any],
) -> list[dict[str, Any]]:
    results = []

    for bucket in (
        categories[
            "skills"
        ].get(
            "required",
            [],
        ),
        categories[
            "languages"
        ].get(
            "required",
            [],
        ),
    ):
        results.extend(
            bucket
        )

    for category in (
        "experience",
        "education",
        "work_authorization",
        "location",
    ):
        item = categories[
            category
        ]

        if (
            item.get(
                "status"
            )
            != STATUS_NOT_APPLICABLE
        ):
            results.append(
                {
                    "requirement": category,
                    "importance": "required_or_gate",
                    **item,
                }
            )

    return results


def _build_summary(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = {
        STATUS_MATCH: 0,
        STATUS_PARTIAL: 0,
        STATUS_GAP: 0,
        STATUS_UNKNOWN: 0,
    }

    known_score_total = 0.0
    known_score_count = 0

    for item in results:
        status = item.get(
            "status",
            STATUS_UNKNOWN,
        )

        if status in counts:
            counts[
                status
            ] += 1

        if status in STATUS_SCORES:
            known_score_total += (
                STATUS_SCORES[
                    status
                ]
            )

            known_score_count += 1

    score = (
        round(
            (
                known_score_total
                / known_score_count
            )
            * 100
        )
        if known_score_count
        else None
    )

    total = sum(
        counts.values()
    )

    known = (
        counts[
            STATUS_MATCH
        ]
        + counts[
            STATUS_PARTIAL
        ]
        + counts[
            STATUS_GAP
        ]
    )

    coverage = (
        round(
            known
            / total
            * 100
        )
        if total
        else 0
    )

    if counts[
        STATUS_GAP
    ] > 0:
        overall = "gap_present"
    elif counts[
        STATUS_UNKNOWN
    ] > 0:
        overall = "needs_review"
    elif counts[
        STATUS_PARTIAL
    ] > 0:
        overall = "partial_match"
    elif counts[
        STATUS_MATCH
    ] > 0:
        overall = "strong_match"
    else:
        overall = "insufficient_requirements"

    return {
        "overall": overall,
        "score": score,
        "coverage_percent": coverage,
        "counts": counts,
        "evaluated_requirement_count": total,
    }


def _normalized_list(
    values: Any,
) -> list[str]:
    if not isinstance(
        values,
        list,
    ):
        return []

    output = []

    for value in values:
        normalized = (
            str(value)
            .strip()
            .lower()
        )

        if (
            normalized
            and normalized not in output
        ):
            output.append(
                normalized
            )

    return output


def _skill_reason(
    status: str,
    level: str,
    confidence: str,
) -> str:
    if status == STATUS_MATCH:
        return (
            f"candidate skill level is {level} "
            f"with {confidence} evidence"
        )

    if status == STATUS_PARTIAL:
        return (
            f"candidate has limited evidence or basic level "
            f"for this skill ({level}, {confidence})"
        )

    return (
        "candidate evidence for this skill is insufficient"
    )
