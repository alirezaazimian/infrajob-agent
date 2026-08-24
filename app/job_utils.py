def remove_duplicates(jobs):
    unique_jobs = {}

    for job in jobs:
        job_id = job.get("id")

        if job_id is not None:
            unique_jobs[job_id] = job

    return list(unique_jobs.values())