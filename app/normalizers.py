def normalize_greenhouse_job(job, company):
    return {
        "external_id": f"greenhouse:{job.get('id')}",
        "title": job.get("title", ""),
        "company": company,
        "location": job.get("location", {}).get("name", ""),
        "description": job.get("content", ""),
        "url": job.get("absolute_url", ""),
        "source": "greenhouse",
    }


def normalize_remotive_job(job):
    return {
        "external_id": f"remotive:{job.get('id')}",
        "title": job.get("title", ""),
        "company": job.get("company_name", ""),
        "location": job.get("candidate_required_location", ""),
        "description": job.get("description", ""),
        "url": job.get("url", ""),
        "source": "remotive",
    }


def normalize_personio_job(job, company, account):
    job_id = str(job.get("id", ""))

    return {
        "external_id": f"personio:{job_id}",
        "title": job.get("name", ""),
        "company": company,
        "location": job.get("office", ""),
        "description": job.get("description", ""),
        "url": (
            f"https://{account}.jobs.personio.de/job/{job_id}"
            if job_id
            else ""
        ),
        "source": "personio",
    }