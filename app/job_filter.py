KEYWORDS = [
    "linux",
    "system administrator",
    "systems administrator",
    "sysadmin",
    "infrastructure engineer",
    "systems engineer",
    "system engineer",
    "server administrator",
    "cloud support",
    "technical support engineer",
    "service desk engineer",
    "devops engineer",
    "site reliability engineer",
    "it operations engineer",
]


def is_relevant_job(job):
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()

    text = f"{title} {description}"

    for keyword in KEYWORDS:
        if keyword in text:
            return True

    return False


def filter_jobs(jobs):
    relevant_jobs = []

    for job in jobs:
        if is_relevant_job(job):
            relevant_jobs.append(job)

    return relevant_jobs