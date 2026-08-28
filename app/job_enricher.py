from app.country_detector import detect_country

from app.eligibility_detector import (
    detect_work_authorization,
    detect_positive_eligibility_signals,
)


def enrich_job(job):
    enriched_job = job.copy()

    # Country detection
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

    # Negative eligibility signals
    authorization_result = detect_work_authorization(
        job
    )

    enriched_job["work_authorization_blocked"] = (
        authorization_result[
            "work_authorization_blocked"
        ]
    )

    enriched_job["work_authorization_signals"] = (
        authorization_result[
            "work_authorization_signals"
        ]
    )

    # Positive eligibility signals
    positive_result = (
        detect_positive_eligibility_signals(job)
    )

    enriched_job["sponsorship_evidence"] = (
        positive_result[
            "sponsorship_evidence"
        ]
    )

    enriched_job["relocation_evidence"] = (
        positive_result[
            "relocation_evidence"
        ]
    )

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

    return enriched_job