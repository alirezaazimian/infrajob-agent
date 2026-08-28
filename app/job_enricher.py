from app.country_detector import detect_country
from app.eligibility_detector import detect_work_authorization


def enrich_job(job):
    enriched_job = job.copy()

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

    return enriched_job