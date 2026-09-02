from __future__ import annotations


READY = "ready"
REVIEW = "review"
NOT_READY = "not_ready"


READINESS_PRIORITY = {
    READY: 3,
    REVIEW: 2,
    NOT_READY: 1,
    "unclassified": 0,
}


READY_ACTIONABILITY = {
    "high_priority",
}


REVIEW_ACTIONABILITY = {
    "review",
}


NOT_READY_ACTIONABILITY = {
    "low_priority",
    "not_targeted",
    "blocked",
}


HARD_BLOCKING_IMMIGRATION = {
    "blocked_by_job_posting",
}


REVIEW_IMMIGRATION = {
    "needs_verification",
}


LOW_VALUE_IMMIGRATION = {
    "market_disabled",
    "no_current_pathway",
}


def _append_unique(
    items: list[str],
    value: str,
) -> None:
    if value not in items:
        items.append(value)


def classify_vacancy_readiness(
    job: dict,
) -> dict:
    reasons = []
    blockers = []
    review_flags = []

    actionability = job.get(
        "actionability",
        "unclassified",
    )

    immigration_assessment = job.get(
        "immigration_assessment",
        "not_evaluated",
    )

    hard_blocked = bool(
        job.get(
            "hard_blocked",
            False,
        )
    )

    sponsorship_evidence = bool(
        job.get(
            "sponsorship_evidence",
            False,
        )
    )

    relocation_evidence = bool(
        job.get(
            "relocation_evidence",
            False,
        )
    )

    language_requirement = job.get(
        "language_requirement",
        "unknown",
    )

    country_code = job.get(
        "country_code"
    )

    opportunity_score = job.get(
        "opportunity_score",
        0,
    )

    # Hard blockers
    if hard_blocked:
        _append_unique(
            blockers,
            "opportunity layer reported a hard blocker",
        )

    if (
        immigration_assessment
        in HARD_BLOCKING_IMMIGRATION
    ):
        _append_unique(
            blockers,
            "job posting blocks required work authorization",
        )

    if actionability == "blocked":
        _append_unique(
            blockers,
            "job is classified as blocked",
        )

    if blockers:
        return {
            "readiness": NOT_READY,
            "reasons": reasons,
            "blockers": blockers,
            "review_flags": review_flags,
        }

    # Low-value / non-target jobs
    if actionability in NOT_READY_ACTIONABILITY:
        _append_unique(
            reasons,
            f"actionability is {actionability}",
        )

        return {
            "readiness": NOT_READY,
            "reasons": reasons,
            "blockers": blockers,
            "review_flags": review_flags,
        }

    if (
        immigration_assessment
        in LOW_VALUE_IMMIGRATION
    ):
        _append_unique(
            reasons,
            (
                "immigration pathway is "
                f"{immigration_assessment}"
            ),
        )

        return {
            "readiness": NOT_READY,
            "reasons": reasons,
            "blockers": blockers,
            "review_flags": review_flags,
        }

    # Basic vacancy completeness
    if not job.get("title"):
        _append_unique(
            review_flags,
            "missing job title",
        )

    if not job.get("company"):
        _append_unique(
            review_flags,
            "missing company",
        )

    url = (
        job.get("url")
        or job.get("job_url")
        or job.get("apply_url")
    )

    if not url:
        _append_unique(
            review_flags,
            "missing vacancy URL",
        )

    if not country_code:
        _append_unique(
            review_flags,
            "country could not be confidently determined",
        )

    # Immigration uncertainty
    if (
        immigration_assessment
        in REVIEW_IMMIGRATION
    ):
        _append_unique(
            review_flags,
            "immigration eligibility requires verification",
        )

    if immigration_assessment in {
        None,
        "",
        "unknown",
        "not_evaluated",
    }:
        _append_unique(
            review_flags,
            "immigration assessment is unavailable",
        )

    # Positive evidence
    if sponsorship_evidence:
        _append_unique(
            reasons,
            "job posting contains sponsorship evidence",
        )

    if relocation_evidence:
        _append_unique(
            reasons,
            "job posting contains relocation evidence",
        )

    if (
        not sponsorship_evidence
        and not relocation_evidence
        and immigration_assessment
        == "needs_verification"
    ):
        _append_unique(
            review_flags,
            (
                "no explicit sponsorship or relocation "
                "evidence found"
            ),
        )

    # Language
    if language_requirement in {
        "unknown",
        "unclear",
        None,
        "",
    }:
        _append_unique(
            review_flags,
            "language requirement is unclear",
        )

    elif language_requirement in {
        "local_language_required",
        "non_english_required",
    }:
        _append_unique(
            review_flags,
            "vacancy appears to require a non-English language",
        )

    # Actionability
    if actionability in READY_ACTIONABILITY:
        _append_unique(
            reasons,
            "vacancy is high priority",
        )

    elif actionability in REVIEW_ACTIONABILITY:
        _append_unique(
            review_flags,
            "vacancy actionability requires review",
        )

    else:
        _append_unique(
            review_flags,
            f"unexpected actionability state: {actionability}",
        )

    # Opportunity score
    if opportunity_score >= 55:
        _append_unique(
            reasons,
            "opportunity score meets high-priority threshold",
        )

    elif opportunity_score >= 40:
        _append_unique(
            review_flags,
            "opportunity score is in review range",
        )

    else:
        _append_unique(
            review_flags,
            "opportunity score is below review threshold",
        )

    readiness = (
        REVIEW
        if review_flags
        else READY
    )

    return {
        "readiness": readiness,
        "reasons": reasons,
        "blockers": blockers,
        "review_flags": review_flags,
    }


def get_readiness_priority(
    readiness: str,
) -> int:
    return READINESS_PRIORITY.get(
        readiness,
        0,
    )
