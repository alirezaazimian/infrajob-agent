from app.country_detector import detect_country


def enrich_job_country(job):
    country_result = detect_country(
        job.get("location", "")
    )

    enriched_job = job.copy()

    enriched_job["country_code"] = (
        country_result["country_code"]
    )

    enriched_job["country"] = (
        country_result["country"]
    )

    enriched_job["country_confidence"] = (
        country_result["confidence"]
    )

    return enriched_job