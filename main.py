from app.collectors.remotive import fetch_jobs
from app.job_filter import filter_jobs


def main():
    print("InfraJob Agent")
    print("=" * 50)

    jobs = fetch_jobs()

    relevant_jobs = filter_jobs(jobs)

    print(f"Jobs received: {len(jobs)}")
    print(f"Relevant jobs: {len(relevant_jobs)}")
    print()

    for index, job in enumerate(relevant_jobs, start=1):
        print(f"{index}. {job['title']}")
        print(f"   Company: {job['company_name']}")
        print(
            f"   Location: "
            f"{job['candidate_required_location']}"
        )
        print()


if __name__ == "__main__":
    main()