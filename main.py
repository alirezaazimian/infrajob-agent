from app.collectors.remotive import fetch_jobs


def main():
    print("InfraJob Agent")
    print("=" * 50)

    jobs = fetch_jobs(limit=5)

    print(f"Jobs received: {len(jobs)}")
    print()

    for index, job in enumerate(jobs, start=1):
        print(f"{index}. {job['title']}")
        print(f"   Company: {job['company_name']}")
        print(
            f"   Location: "
            f"{job['candidate_required_location']}"
        )
        print()


if __name__ == "__main__":
    main()