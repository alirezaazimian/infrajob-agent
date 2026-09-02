from __future__ import annotations


COMPLETION_VERSION = "m21.2.4"

STATUS_COMPLETE = "complete"
STATUS_REVIEW = "review"
STATUS_INCOMPLETE = "incomplete"


def _list(value):
    if isinstance(value, list):
        return value
    return []


def evaluate_requirement_completion(
    requirements: dict,
) -> dict:
    """
    Evaluate whether an extracted vacancy-requirement snapshot is
    sufficiently informative for downstream vacancy validation.

    This gate does not invent requirements and does not compare the
    vacancy with a candidate profile. It only grades the extraction
    result already produced by Requirement Extractor.
    """

    has_description = bool(
        requirements.get(
            "has_description"
        )
    )

    description_length = int(
        requirements.get(
            "description_length",
            0,
        )
        or 0
    )

    experience = (
        requirements.get(
            "experience"
        )
        or {}
    )

    education = (
        requirements.get(
            "education"
        )
        or {}
    )

    languages = (
        requirements.get(
            "languages"
        )
        or {}
    )

    work_authorization = (
        requirements.get(
            "work_authorization"
        )
        or {}
    )

    location = (
        requirements.get(
            "location"
        )
        or {}
    )

    skills = (
        requirements.get(
            "skills"
        )
        or {}
    )

    required_skills = _list(
        skills.get(
            "required"
        )
    )

    preferred_skills = _list(
        skills.get(
            "preferred"
        )
    )

    mentioned_skills = _list(
        skills.get(
            "mentioned"
        )
    )

    required_languages = _list(
        languages.get(
            "required"
        )
    )

    mentioned_languages = _list(
        languages.get(
            "mentioned"
        )
    )

    experience_explicit = bool(
        experience.get(
            "explicit"
        )
    )

    education_explicit = bool(
        education.get(
            "explicit"
        )
    )

    work_auth_signal = any(
        (
            bool(
                work_authorization.get(
                    "explicit_local_authorization_required"
                )
            ),
            bool(
                work_authorization.get(
                    "sponsorship_mentioned"
                )
            ),
            bool(
                work_authorization.get(
                    "relocation_mentioned"
                )
            ),
        )
    )

    location_mode = (
        location.get(
            "mode",
            "unknown",
        )
        or "unknown"
    )

    location_known = (
        location_mode
        not in {
            "unknown",
            "",
        }
    )

    coverage = {
        "skills": bool(
            required_skills
            or preferred_skills
            or mentioned_skills
        ),
        "experience": (
            experience_explicit
        ),
        "education": (
            education_explicit
        ),
        "languages": bool(
            required_languages
            or mentioned_languages
        ),
        "work_authorization": (
            work_auth_signal
        ),
        "location": (
            location_known
        ),
    }

    signal_count = sum(
        1
        for value in coverage.values()
        if value
    )

    explicit_requirement_count = int(
        requirements.get(
            "explicit_requirement_count",
            0,
        )
        or 0
    )

    strong_requirement_count = (
        len(required_skills)
        + len(required_languages)
        + (
            1
            if experience_explicit
            else 0
        )
        + (
            1
            if education.get(
                "required"
            )
            else 0
        )
        + (
            1
            if work_authorization.get(
                "explicit_local_authorization_required"
            )
            else 0
        )
    )

    reasons = []
    review_flags = []

    if not has_description:
        status = STATUS_INCOMPLETE
        reasons.append(
            "vacancy description is missing"
        )

    elif description_length < 80:
        status = STATUS_INCOMPLETE
        reasons.append(
            "vacancy description is too short for reliable requirement extraction"
        )

    elif signal_count == 0:
        status = STATUS_INCOMPLETE
        reasons.append(
            "no meaningful structured requirement signals were extracted"
        )

    elif (
        explicit_requirement_count >= 3
        or strong_requirement_count >= 3
        or (
            len(required_skills) >= 2
            and signal_count >= 1
        )
        or signal_count >= 4
    ):
        status = STATUS_COMPLETE
        reasons.append(
            "structured requirement evidence is sufficient for downstream validation"
        )

    else:
        status = STATUS_REVIEW
        reasons.append(
            "some requirement evidence was extracted but coverage is still limited"
        )

    if has_description and not required_skills:
        review_flags.append(
            "no explicit required technical skills were extracted"
        )

    if not experience_explicit:
        review_flags.append(
            "no explicit experience requirement was extracted"
        )

    if not education_explicit:
        review_flags.append(
            "no explicit education requirement was extracted"
        )

    if not mentioned_languages:
        review_flags.append(
            "no language requirement or language signal was extracted"
        )

    if not work_auth_signal:
        review_flags.append(
            "no work-authorization, sponsorship, or relocation requirement was extracted"
        )

    if not location_known:
        review_flags.append(
            "work-location mode remains unknown"
        )

    return {
        "version": COMPLETION_VERSION,
        "status": status,
        "signal_count": signal_count,
        "strong_requirement_count": (
            strong_requirement_count
        ),
        "explicit_requirement_count": (
            explicit_requirement_count
        ),
        "coverage": coverage,
        "reasons": reasons,
        "review_flags": review_flags,
    }


def get_completion_priority(
    status: str,
) -> int:
    return {
        STATUS_COMPLETE: 3,
        STATUS_REVIEW: 2,
        STATUS_INCOMPLETE: 1,
    }.get(
        status,
        0,
    )
