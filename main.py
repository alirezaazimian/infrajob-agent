from app.collectors.remotive import fetch_jobs
from app.job_filter import filter_jobs
from app.job_scorer import calculate_job_score
from app.job_utils import remove_duplicates


SEARCH_TERMS = [
    "linux",
    "system administrator",
    "infrastructure",
    "systems engineer",
    "devops",
]


def main():
    print("InfraJob Agent")
    print("=" * 50)

    all_jobs = []

    for term in SEARCH_TERMS:
        print(f"Searching: {term}")

        jobs = fetch_jobs(term)

        all_jobs.extend(jobs)

    unique_jobs = remove_duplicates(all_jobs)

    relevant_jobs = filter_jobs(unique_jobs)

    print()
    print(f"Jobs collected: {len(all_jobs)}")
    print(f"Unique jobs: {len(unique_jobs)}")
    print(f"Relevant jobs: {len(relevant_jobs)}")
    print()

    for index, job in enumerate(relevant_jobs, start=1):
        score, matched_skills = calculate_job_score(job)

        print(f"{index}. {job['title']}")
        print(f"   Company: {job['company_name']}")
        print(
            f"   Location: "
            f"{job['candidate_required_location']}"
        )
        print(f"   Score: {score}/100")

        if matched_skills:
            print(
                f"   Matched skills: "
                f"{', '.join(matched_skills)}"
            )

        print()


if __name__ == "__main__":
    main()