from __future__ import annotations

from typing import Any


APPLICATION_DECISION_VERSION = "m24.1"

APPLY_NOW = "apply_now"
APPLY_WITH_TAILORED_CV = "apply_with_tailored_cv"
HUMAN_REVIEW = "human_review"
DO_NOT_APPLY = "do_not_apply"


def classify_application_decision(
    job: dict[str, Any],
) -> dict[str, Any]:
    """
    Combine vacancy-level routing with candidate matching.

    This stage answers:
        "What should we do with this vacancy for this candidate?"

    It does NOT submit an application automatically.

    Conservative policy:
    - Vacancy SKIP always becomes DO_NOT_APPLY.
    - Explicit candidate work-authorization gap is a hard blocker.
    - Vacancy REVIEW remains HUMAN_REVIEW.
    - Candidate uncertainty/gaps remain HUMAN_REVIEW unless there is
      a clear hard blocker.
    - A clean vacancy APPLY + strong candidate match can APPLY_NOW.
    - A clean vacancy APPLY + partial candidate match advances with
      a tailored CV rather than pretending the candidate is perfect.
    """

    vacancy_decision = (
        job.get(
            "final_decision",
            "unclassified",
        )
        or "unclassified"
    ).strip().lower()

    candidate_match = (
        job.get(
            "candidate_match"
        )
        or {}
    )

    candidate_skip_reason = (
        job.get(
            "candidate_match_skip_reason"
        )
        or ""
    ).strip()

    candidate_summary = (
        candidate_match.get(
            "summary"
        )
        or {}
    )

    candidate_overall = (
        candidate_summary.get(
            "overall",
            "unclassified",
        )
        or "unclassified"
    ).strip().lower()

    score = candidate_summary.get(
        "score"
    )

    coverage = candidate_summary.get(
        "coverage_percent"
    )

    reasons: list[str] = []
    blockers: list[str] = []
    review_flags: list[str] = []

    # --------------------------------------------------
    # Vacancy-level hard stop
    # --------------------------------------------------

    if vacancy_decision == "skip":
        blockers.append(
            "vacancy-level decision is skip"
        )

        return _result(
            decision=DO_NOT_APPLY,
            reasons=[
                "vacancy should not advance to an application"
            ],
            blockers=blockers,
            review_flags=[],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    # --------------------------------------------------
    # Candidate-level hard blockers
    # --------------------------------------------------

    blockers.extend(
        _candidate_hard_blockers(
            candidate_match
        )
    )

    if blockers:
        return _result(
            decision=DO_NOT_APPLY,
            reasons=[
                "candidate has a confirmed blocking mismatch"
            ],
            blockers=blockers,
            review_flags=[],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    # --------------------------------------------------
    # Vacancy uncertainty always requires human review
    # --------------------------------------------------

    if vacancy_decision == "review":
        review_flags.append(
            "vacancy-level decision requires review"
        )

        if candidate_overall == "gap_present":
            review_flags.append(
                "candidate match contains one or more non-hard gaps"
            )

        elif candidate_overall == "needs_review":
            review_flags.append(
                "candidate match contains unresolved evidence"
            )

        elif candidate_overall == "partial_match":
            review_flags.append(
                "candidate is only a partial match"
            )

        elif candidate_overall == "unclassified":
            if candidate_skip_reason:
                review_flags.append(
                    f"candidate matching was skipped: {candidate_skip_reason}"
                )
            else:
                review_flags.append(
                    "candidate matching is unclassified"
                )

        return _result(
            decision=HUMAN_REVIEW,
            reasons=[
                "vacancy is potentially actionable but unresolved gates remain"
            ],
            blockers=[],
            review_flags=review_flags,
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    # Unknown vacancy routing should never auto-apply.
    if vacancy_decision != "apply":
        return _result(
            decision=HUMAN_REVIEW,
            reasons=[
                "vacancy-level routing is not sufficiently classified"
            ],
            blockers=[],
            review_flags=[
                f"vacancy-level decision is {vacancy_decision}"
            ],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    # --------------------------------------------------
    # Clean vacancy APPLY: candidate-level routing
    # --------------------------------------------------

    if not candidate_match:
        return _result(
            decision=HUMAN_REVIEW,
            reasons=[
                "vacancy passed its gates but candidate matching is unavailable"
            ],
            blockers=[],
            review_flags=[
                (
                    f"candidate matching was skipped: {candidate_skip_reason}"
                    if candidate_skip_reason
                    else "candidate match is missing"
                )
            ],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    if candidate_overall == "strong_match":
        if _meets_auto_apply_quality(
            score,
            coverage,
        ):
            return _result(
                decision=APPLY_NOW,
                reasons=[
                    "vacancy passed all vacancy gates and candidate match is strong"
                ],
                blockers=[],
                review_flags=[],
                vacancy_decision=vacancy_decision,
                candidate_overall=candidate_overall,
                score=score,
                coverage=coverage,
            )

        return _result(
            decision=HUMAN_REVIEW,
            reasons=[
                "candidate match is strong but evidence coverage is not sufficient for automatic advancement"
            ],
            blockers=[],
            review_flags=[
                "candidate match quality thresholds were not fully met"
            ],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    if candidate_overall == "partial_match":
        return _result(
            decision=APPLY_WITH_TAILORED_CV,
            reasons=[
                "vacancy passed its gates and candidate has a usable partial match"
            ],
            blockers=[],
            review_flags=[
                "application materials should emphasize matching strengths and avoid overstating gaps"
            ],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    if candidate_overall == "gap_present":
        return _result(
            decision=HUMAN_REVIEW,
            reasons=[
                "vacancy passed its gates but candidate match contains non-hard gaps"
            ],
            blockers=[],
            review_flags=[
                "review candidate gaps before deciding whether to apply"
            ],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    if candidate_overall == "needs_review":
        return _result(
            decision=HUMAN_REVIEW,
            reasons=[
                "vacancy passed its gates but candidate evidence remains unresolved"
            ],
            blockers=[],
            review_flags=[
                "verify unknown candidate requirements before applying"
            ],
            vacancy_decision=vacancy_decision,
            candidate_overall=candidate_overall,
            score=score,
            coverage=coverage,
        )

    return _result(
        decision=HUMAN_REVIEW,
        reasons=[
            "application routing cannot be determined confidently"
        ],
        blockers=[],
        review_flags=[
            f"candidate match status is {candidate_overall}"
        ],
        vacancy_decision=vacancy_decision,
        candidate_overall=candidate_overall,
        score=score,
        coverage=coverage,
    )


def get_application_decision_priority(
    decision: str,
) -> int:
    return {
        APPLY_NOW: 4,
        APPLY_WITH_TAILORED_CV: 3,
        HUMAN_REVIEW: 2,
        DO_NOT_APPLY: 1,
    }.get(
        decision,
        0,
    )


def _candidate_hard_blockers(
    candidate_match: dict[str, Any],
) -> list[str]:
    if not candidate_match:
        return []

    categories = (
        candidate_match.get(
            "categories"
        )
        or {}
    )

    blockers: list[str] = []

    authorization = (
        categories.get(
            "work_authorization"
        )
        or {}
    )

    if (
        authorization.get(
            "status"
        )
        == "gap"
    ):
        blockers.append(
            "candidate does not have required local work authorization"
        )

    return _unique(
        blockers
    )


def _meets_auto_apply_quality(
    score: Any,
    coverage: Any,
) -> bool:
    if score is None or coverage is None:
        return False

    try:
        numeric_score = float(
            score
        )
        numeric_coverage = float(
            coverage
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    return (
        numeric_score >= 75
        and numeric_coverage >= 70
    )


def _result(
    *,
    decision: str,
    reasons: list[str],
    blockers: list[str],
    review_flags: list[str],
    vacancy_decision: str,
    candidate_overall: str,
    score: Any,
    coverage: Any,
) -> dict[str, Any]:
    return {
        "version": APPLICATION_DECISION_VERSION,
        "decision": decision,
        "reasons": _unique(
            reasons
        ),
        "blockers": _unique(
            blockers
        ),
        "review_flags": _unique(
            review_flags
        ),
        "inputs": {
            "vacancy_decision": vacancy_decision,
            "candidate_match": candidate_overall,
            "candidate_match_score": score,
            "candidate_match_coverage": coverage,
        },
    }


def _unique(
    items: list[str],
) -> list[str]:
    output: list[str] = []

    for item in items:
        if item and item not in output:
            output.append(
                item
            )

    return output
