from __future__ import annotations


DECISION_VERSION = "m21.4.1"

DECISION_APPLY = "apply"
DECISION_REVIEW = "review"
DECISION_SKIP = "skip"


def classify_final_vacancy_decision(
    job: dict,
) -> dict:
    """
    Produce the final vacancy-level routing decision.

    Important:
    - This stage evaluates the vacancy only.
    - It does NOT compare vacancy requirements with a candidate profile.
    - APPLY means "advance into the application workflow", not
      "submit an application automatically".
    """

    readiness = (
        job.get(
            "vacancy_readiness",
            "unclassified",
        )
        or "unclassified"
    ).lower()

    actionability = (
        job.get(
            "actionability",
            "unclassified",
        )
        or "unclassified"
    ).lower()

    hard_blocked = bool(
        job.get(
            "hard_blocked",
            False,
        )
    )

    hard_blockers = list(
        job.get(
            "hard_blockers",
            [],
        )
        or []
    )

    requirements = (
        job.get(
            "requirements"
        )
        or {}
    )

    completion = (
        requirements.get(
            "completion"
        )
        or {}
    )

    completion_status = (
        completion.get(
            "status",
            "unclassified",
        )
        or "unclassified"
    ).lower()

    live_validation = (
        job.get(
            "live_validation"
        )
        or {}
    )

    live_status = (
        live_validation.get(
            "status",
            "unclassified",
        )
        or "unclassified"
    ).lower()

    reasons = []
    blockers = []
    review_flags = []

    # --------------------------------------------------
    # Hard skip conditions
    # --------------------------------------------------

    if hard_blocked:
        blockers.append(
            "job is hard blocked"
        )

    blockers.extend(
        hard_blockers
    )

    if actionability == "blocked":
        blockers.append(
            "actionability is blocked"
        )

    if readiness == "not_ready":
        blockers.append(
            "vacancy readiness is not_ready"
        )

    if live_status == "closed":
        blockers.append(
            "live vacancy validation confirmed the posting is closed"
        )

    if blockers:
        return {
            "version": DECISION_VERSION,
            "decision": DECISION_SKIP,
            "reasons": [
                "vacancy has a blocking condition and should not advance"
            ],
            "blockers": _unique(
                blockers
            ),
            "review_flags": [],
            "inputs": {
                "vacancy_readiness": readiness,
                "actionability": actionability,
                "requirement_completion": completion_status,
                "live_validation": live_status,
            },
        }

    # --------------------------------------------------
    # Review conditions
    # --------------------------------------------------

    if readiness == "review":
        review_flags.append(
            "vacancy readiness requires review"
        )

    elif readiness != "ready":
        review_flags.append(
            f"vacancy readiness is {readiness}"
        )

    if completion_status == "review":
        review_flags.append(
            "requirement extraction completion requires review"
        )

    elif completion_status == "incomplete":
        review_flags.append(
            "requirement extraction is incomplete"
        )

    elif completion_status != "complete":
        review_flags.append(
            f"requirement extraction completion is {completion_status}"
        )

    if live_status == "review":
        review_flags.append(
            "live vacancy validation requires review"
        )

    elif live_status == "skipped":
        review_flags.append(
            "live vacancy validation was skipped"
        )

    elif live_status != "live":
        review_flags.append(
            f"live vacancy validation is {live_status}"
        )

    if actionability == "review":
        review_flags.append(
            "actionability requires review"
        )

    elif actionability not in {
        "high_priority",
        "review",
    }:
        review_flags.append(
            f"actionability is {actionability}"
        )

    if review_flags:
        reasons.append(
            "vacancy is potentially actionable but one or more gates still require review"
        )

        return {
            "version": DECISION_VERSION,
            "decision": DECISION_REVIEW,
            "reasons": reasons,
            "blockers": [],
            "review_flags": _unique(
                review_flags
            ),
            "inputs": {
                "vacancy_readiness": readiness,
                "actionability": actionability,
                "requirement_completion": completion_status,
                "live_validation": live_status,
            },
        }

    # --------------------------------------------------
    # Apply / advance condition
    # --------------------------------------------------

    reasons.append(
        "vacancy passed readiness, requirement-completion, and live-validation gates"
    )

    return {
        "version": DECISION_VERSION,
        "decision": DECISION_APPLY,
        "reasons": reasons,
        "blockers": [],
        "review_flags": [],
        "inputs": {
            "vacancy_readiness": readiness,
            "actionability": actionability,
            "requirement_completion": completion_status,
            "live_validation": live_status,
        },
    }


def get_final_decision_priority(
    decision: str,
) -> int:
    return {
        DECISION_APPLY: 3,
        DECISION_REVIEW: 2,
        DECISION_SKIP: 1,
    }.get(
        decision,
        0,
    )


def _unique(
    items: list,
) -> list:
    output = []

    for item in items:
        if item not in output:
            output.append(
                item
            )

    return output
