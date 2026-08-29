import json
from pathlib import Path

from app.opportunity_scorer import (
    load_scoring_config,
)


CONFIG_PATH = Path(
    "config/actionability.json"
)


def load_actionability_config():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_market_group(job):
    scoring_config = (
        load_scoring_config()
    )

    country_code = job.get(
        "country_code"
    )

    if not country_code:
        return "unknown"

    return scoring_config[
        "country_groups"
    ].get(
        country_code,
        "unknown",
    )


def get_actionability_priority(
    actionability,
):
    config = (
        load_actionability_config()
    )

    return config.get(
        "sort_priority",
        {},
    ).get(
        actionability,
        0,
    )


def classify_actionability(job):
    config = (
        load_actionability_config()
    )

    market_group = get_market_group(
        job
    )

    opportunity_score = job.get(
        "opportunity_score",
        0,
    )

    immigration_assessment = job.get(
        "immigration_assessment",
        "not_evaluated",
    )

    hard_blocked = job.get(
        "hard_blocked",
        False,
    )

    reasons = []

    # --------------------------------------------------
    # 1. Hard blockers always win.
    # --------------------------------------------------

    if hard_blocked:
        reasons.append(
            "hard_blocker_detected"
        )

        return {
            "actionability": "blocked",
            "market_group": market_group,
            "reasons": reasons,
        }

    if immigration_assessment in config[
        "blocking_immigration_assessments"
    ]:
        reasons.append(
            immigration_assessment
        )

        return {
            "actionability": "blocked",
            "market_group": market_group,
            "reasons": reasons,
        }

    # --------------------------------------------------
    # 2. Countries outside the strategy.
    # --------------------------------------------------

    if market_group in config[
        "not_targeted_groups"
    ]:
        reasons.append(
            f"market_group:{market_group}"
        )

        return {
            "actionability": "not_targeted",
            "market_group": market_group,
            "reasons": reasons,
        }

    # --------------------------------------------------
    # 3. Explicit low-priority markets.
    # --------------------------------------------------

    if market_group in config[
        "low_priority_groups"
    ]:
        reasons.append(
            f"market_group:{market_group}"
        )

        return {
            "actionability": "low_priority",
            "market_group": market_group,
            "reasons": reasons,
        }

    # --------------------------------------------------
    # 4. Weak immigration route.
    # --------------------------------------------------

    if immigration_assessment in config[
        "low_priority_immigration_assessments"
    ]:
        reasons.append(
            immigration_assessment
        )

        return {
            "actionability": "low_priority",
            "market_group": market_group,
            "reasons": reasons,
        }

    # --------------------------------------------------
    # 5. Score-based decision.
    # --------------------------------------------------

    high_priority_threshold = config[
        "thresholds"
    ][
        "high_priority"
    ]

    review_threshold = config[
        "thresholds"
    ][
        "review"
    ]

    if (
        opportunity_score
        >= high_priority_threshold
    ):
        reasons.append(
            "opportunity_score_high"
        )

        return {
            "actionability": "high_priority",
            "market_group": market_group,
            "reasons": reasons,
        }

    if (
        opportunity_score
        >= review_threshold
    ):
        reasons.append(
            "opportunity_score_review_range"
        )

        return {
            "actionability": "review",
            "market_group": market_group,
            "reasons": reasons,
        }

    reasons.append(
        "opportunity_score_low"
    )

    return {
        "actionability": "low_priority",
        "market_group": market_group,
        "reasons": reasons,
    }