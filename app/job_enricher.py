from app.country_detector import detect_country

from app.eligibility_detector import (
    detect_work_authorization,
    detect_positive_eligibility_signals,
)

from app.language_detector import (
    detect_language_requirements,
)


def enrich_job(job):
    enriched_job = job.copy()

    # --------------------------------------------------
    # Country detection
    # --------------------------------------------------

    country_result = detect_country(
        job.get("location", "")
    )

    enriched_job["country_code"] = (
        country_result["country_code"]
    )

    enriched_job["country"] = (
        country_result["country"]
    )

    enriched_job["country_confidence"] = (
        country_result["confidence"]
    )

    # --------------------------------------------------
    # Negative work authorization signals
    # --------------------------------------------------

    authorization_result = (
        detect_work_authorization(job)
    )

    enriched_job[
        "work_authorization_blocked"
    ] = authorization_result[
        "work_authorization_blocked"
    ]

    enriched_job[
        "work_authorization_signals"
    ] = authorization_result[
        "work_authorization_signals"
    ]

    # --------------------------------------------------
    # Positive eligibility signals
    # --------------------------------------------------

    positive_result = (
        detect_positive_eligibility_signals(job)
    )

    enriched_job[
        "sponsorship_evidence"
    ] = positive_result[
        "sponsorship_evidence"
    ]

    enriched_job[
        "relocation_evidence"
    ] = positive_result[
        "relocation_evidence"
    ]

    enriched_job[
        "international_hiring_evidence"
    ] = positive_result[
        "international_hiring_evidence"
    ]

    enriched_job[
        "positive_eligibility_signals"
    ] = positive_result[
        "positive_eligibility_signals"
    ]

    # --------------------------------------------------
    # Language requirements
    # --------------------------------------------------

    language_result = (
        detect_language_requirements(job)
    )

    enriched_job[
        "language_requirement"
    ] = language_result[
        "language_requirement"
    ]

    enriched_job[
        "german_required"
    ] = language_result[
        "german_required"
    ]

    enriched_job[
        "german_preferred"
    ] = language_result[
        "german_preferred"
    ]

    enriched_job[
        "english_required"
    ] = language_result[
        "english_required"
    ]

    enriched_job[
        "other_required_languages"
    ] = language_result[
        "other_required_languages"
    ]

    enriched_job[
        "language_signals"
    ] = language_result[
        "language_signals"
    ]

    return enriched_job