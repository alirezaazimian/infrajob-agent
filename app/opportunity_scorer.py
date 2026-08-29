import json
from pathlib import Path


CONFIG_PATH = Path(
    "config/opportunity_scoring.json"
)


def load_scoring_config():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def clamp(value, minimum, maximum):
    return max(
        minimum,
        min(value, maximum),
    )


def calculate_technical_fit(
    technical_score,
    config,
):
    maximum = config["weights"][
        "technical_fit"
    ]

    normalized_score = clamp(
        technical_score or 0,
        0,
        100,
    )

    return round(
        (
            normalized_score
            / 100
        )
        * maximum
    )


def calculate_country_fit(
    job,
    config,
):
    country_code = job.get(
        "country_code"
    )

    if not country_code:
        group = "unknown"

    else:
        group = config[
            "country_groups"
        ].get(
            country_code,
            "unknown",
        )

    score = config[
        "country_fit"
    ].get(
        group,
        0,
    )

    return {
        "score": score,
        "group": group,
    }


def calculate_immigration_fit(
    job,
    config,
):
    assessment = job.get(
        "immigration_assessment",
        "not_evaluated",
    )

    score = config[
        "immigration_fit"
    ].get(
        assessment,
        0,
    )

    return {
        "score": score,
        "assessment": assessment,
    }


def calculate_sponsorship_fit(
    job,
    config,
):
    if job.get(
        "sponsorship_evidence",
        False,
    ):
        classification = (
            "sponsorship_evidence"
        )

    elif job.get(
        "relocation_evidence",
        False,
    ):
        classification = (
            "relocation_only"
        )

    else:
        classification = (
            "no_evidence"
        )

    score = config[
        "sponsorship_fit"
    ][classification]

    return {
        "score": score,
        "classification": classification,
    }


def calculate_language_fit(
    job,
    config,
):
    requirement = job.get(
        "language_requirement",
        "unknown",
    )

    score = config[
        "language_fit"
    ].get(
        requirement,
        0,
    )

    return {
        "score": score,
        "requirement": requirement,
    }


def calculate_international_hiring_fit(
    job,
    config,
):
    if job.get(
        "international_hiring_evidence",
        False,
    ):
        classification = "evidence"

    else:
        classification = "no_evidence"

    score = config[
        "international_hiring_fit"
    ][classification]

    return {
        "score": score,
        "classification": classification,
    }


def detect_hard_blockers(
    job,
    config,
):
    blockers = []

    for blocker_field in config.get(
        "hard_blockers",
        [],
    ):
        if job.get(
            blocker_field,
            False,
        ):
            blockers.append(
                blocker_field
            )

    return blockers


def calculate_opportunity_score(
    job,
    technical_score=None,
):
    config = load_scoring_config()

    if technical_score is None:
        technical_score = job.get(
            "score",
            0,
        )

    technical_fit = (
        calculate_technical_fit(
            technical_score,
            config,
        )
    )

    country_fit = (
        calculate_country_fit(
            job,
            config,
        )
    )

    immigration_fit = (
        calculate_immigration_fit(
            job,
            config,
        )
    )

    sponsorship_fit = (
        calculate_sponsorship_fit(
            job,
            config,
        )
    )

    language_fit = (
        calculate_language_fit(
            job,
            config,
        )
    )

    international_fit = (
        calculate_international_hiring_fit(
            job,
            config,
        )
    )

    hard_blockers = (
        detect_hard_blockers(
            job,
            config,
        )
    )

    raw_score = (
        technical_fit
        + country_fit["score"]
        + immigration_fit["score"]
        + sponsorship_fit["score"]
        + language_fit["score"]
        + international_fit["score"]
    )

    raw_score = clamp(
        raw_score,
        0,
        100,
    )

    hard_blocked = bool(
        hard_blockers
    )

    if hard_blocked:
        final_score = 0

    else:
        final_score = raw_score

    return {
        "opportunity_score": final_score,
        "raw_opportunity_score": raw_score,
        "hard_blocked": hard_blocked,
        "hard_blockers": hard_blockers,

        "breakdown": {
            "technical_fit": {
                "score": technical_fit,
                "max": config[
                    "weights"
                ][
                    "technical_fit"
                ],
                "technical_score": technical_score,
            },

            "country_fit": {
                "score": country_fit[
                    "score"
                ],
                "max": config[
                    "weights"
                ][
                    "country_fit"
                ],
                "group": country_fit[
                    "group"
                ],
                "country_code": job.get(
                    "country_code"
                ),
            },

            "immigration_fit": {
                "score": immigration_fit[
                    "score"
                ],
                "max": config[
                    "weights"
                ][
                    "immigration_fit"
                ],
                "assessment": (
                    immigration_fit[
                        "assessment"
                    ]
                ),
            },

            "sponsorship_fit": {
                "score": sponsorship_fit[
                    "score"
                ],
                "max": config[
                    "weights"
                ][
                    "sponsorship_fit"
                ],
                "classification": (
                    sponsorship_fit[
                        "classification"
                    ]
                ),
            },

            "language_fit": {
                "score": language_fit[
                    "score"
                ],
                "max": config[
                    "weights"
                ][
                    "language_fit"
                ],
                "requirement": (
                    language_fit[
                        "requirement"
                    ]
                ),
            },

            "international_hiring_fit": {
                "score": international_fit[
                    "score"
                ],
                "max": config[
                    "weights"
                ][
                    "international_hiring_fit"
                ],
                "classification": (
                    international_fit[
                        "classification"
                    ]
                ),
            },
        },
    }