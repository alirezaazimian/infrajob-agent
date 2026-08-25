def remove_duplicates(jobs):
    unique_jobs = {}

    for job in jobs:
        external_id = job.get("external_id")

        if external_id:
            unique_jobs[external_id] = job

    return list(unique_jobs.values())