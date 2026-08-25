from app.collectors.remotive import fetch_jobs
from app.collectors.greenhouse import fetch_greenhouse_jobs
from app.normalizers import (
    normalize_remotive_job,
    normalize_greenhouse_job,
)
from app.job_filter import filter_jobs
from app.job_scorer import calculate_job_score
from app.job_utils import remove_duplicates


REMOTIVE_SEARCH_TERMS = [
    "linux",
    "system administrator",
    "infrastructure",
    "systems engineer",
    "devops",
]


GREENHOUSE_BOARDS = [
    {
        "board_name": "quantiq",
        "company": "Quantiq",
    },
]


def collect_remotive_jobs():
    normalized_jobs = []

    for term in REMOTIVE_SEARCH_TERMS:
        print(f"Searching Remotive: {term}")

        jobs = fetch_jobs(term)

        for job in jobs:
            normalized_jobs.append(
                normalize_remotive_job(job)
            )

    return normalized_jobs


def collect_greenhouse_jobs():
    normalized_jobs = []

    for board in GREENHOUSE_BOARDS:
        board_name = board["board_name"]
        company = board["company"]

        print(f"Collecting Greenhouse: {company}")

        jobs = fetch_greenhouse_jobs(board_name)

        for job in jobs:
            normalized_jobs.append(
                normalize_greenhouse_job(
                    job,
                    company,
                )
            )

    return normalized_jobs


def main():
    print("InfraJob Agent")
    print("=" * 60)

    remotive_jobs = collect_remotive_jobs()
    greenhouse_jobs = collect_greenhouse_jobs()

    all_jobs = remotive_jobs + greenhouse_jobs

    unique_jobs = remove_duplicates(all_jobs)

    relevant_jobs = filter_jobs(unique_jobs)

    print()
    print("=" * 60)
    print(f"Remotive jobs: {len(remotive_jobs)}")
    print(f"Greenhouse jobs: {len(greenhouse_jobs)}")
    print(f"Total jobs: {len(all_jobs)}")
    print(f"Unique jobs: {len(unique_jobs)}")
    print(f"Relevant jobs: {len(relevant_jobs)}")
    print("=" * 60)
    print()

    scored_jobs = []

    for job in relevant_jobs:
        score, matched_skills = calculate_job_score(job)

        scored_jobs.append(
            {
                "job": job,
                "score": score,
                "matched_skills": matched_skills,
            }
        )

    scored_jobs.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    for index, item in enumerate(scored_jobs, start=1):
        job = item["job"]
        score = item["score"]
        matched_skills = item["matched_skills"]

        print(f"{index}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Source: {job['source']}")
        print(f"   Score: {score}/100")

        if matched_skills:
            print(
                "   Matched skills: "
                + ", ".join(matched_skills)
            )

        print()


if __name__ == "__main__":
    main()