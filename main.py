import requests

from app.collectors.remotive import fetch_jobs
from app.collectors.greenhouse import fetch_greenhouse_jobs
from app.normalizers import (
    normalize_remotive_job,
    normalize_greenhouse_job,
    normalize_personio_job,
    normalize_lever_job,
    normalize_ashby_job,
)
from app.job_filter import filter_jobs
from app.job_scorer import calculate_job_score
from app.job_utils import remove_duplicates
from app.config_loader import load_sources
from app.logger import setup_logger
from app.database import create_jobs_table, save_job
from app.collectors.personio import fetch_personio_jobs
from app.collectors.lever import fetch_lever_jobs
from app.collectors.ashby import fetch_ashby_jobs
from app.job_enricher import enrich_job


MINIMUM_SCORE = 30

logger = setup_logger()


def collect_remotive_jobs(search_terms):
    normalized_jobs = []

    for term in search_terms:
        print(f"Searching Remotive: {term}")

        logger.info(
            "Collecting Remotive jobs for search term: %s",
            term,
        )

        try:
            jobs = fetch_jobs(term)

            logger.info(
                "Remotive search '%s' returned %d jobs",
                term,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Remotive search '%s' HTTP error: %s",
                term,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Remotive search '%s' timed out",
                term,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Remotive search '%s' connection failed",
                term,
            )
            continue

        for job in jobs:
            normalized_jobs.append(
                normalize_remotive_job(job)
            )

    return normalized_jobs


def collect_greenhouse_jobs(boards):
    normalized_jobs = []

    for board in boards:
        board_name = board["board_name"]
        company = board["company"]

        print(f"Collecting Greenhouse: {company}")

        logger.info(
            "Collecting Greenhouse jobs for %s",
            company,
        )

        try:
            jobs = fetch_greenhouse_jobs(board_name)

            logger.info(
                "Greenhouse %s returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Greenhouse %s HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Greenhouse %s request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Greenhouse %s connection failed",
                company,
            )
            continue

        for job in jobs:
            normalized_jobs.append(
                normalize_greenhouse_job(
                    job,
                    company,
                )
            )

    return normalized_jobs


def collect_personio_jobs(accounts):
    normalized_jobs = []

    for account_config in accounts:
        account = account_config["account"]
        company = account_config["company"]
        language = account_config.get(
            "language",
            "en",
        )

        print(f"Collecting Personio: {company}")

        logger.info(
            "Collecting Personio jobs for %s",
            company,
        )

        try:
            jobs = fetch_personio_jobs(
                account,
                language=language,
            )

            logger.info(
                "Personio %s returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Personio %s HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Personio %s request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Personio %s connection failed",
                company,
            )
            continue

        for job in jobs:
            normalized_jobs.append(
                normalize_personio_job(
                    job,
                    company,
                    account,
                )
            )

    return normalized_jobs


def collect_lever_jobs(sites):
    normalized_jobs = []

    for site_config in sites:
        site = site_config["site"]
        company = site_config["company"]
        region = site_config.get(
            "region",
            "global",
        )

        print(f"Collecting Lever: {company}")

        logger.info(
            "Collecting Lever jobs for %s",
            company,
        )

        try:
            jobs = fetch_lever_jobs(
                site,
                region=region,
            )

            logger.info(
                "Lever %s returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Lever %s HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Lever %s request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Lever %s connection failed",
                company,
            )
            continue

        for job in jobs:
            normalized_jobs.append(
                normalize_lever_job(
                    job,
                    company,
                    site,
                )
            )

    return normalized_jobs


def collect_ashby_jobs(boards):
    normalized_jobs = []

    for board in boards:
        board_name = board["board_name"]
        company = board["company"]

        print(f"Collecting Ashby: {company}")

        logger.info(
            "Collecting Ashby jobs for %s",
            company,
        )

        try:
            jobs = fetch_ashby_jobs(board_name)

            logger.info(
                "Ashby %s returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Ashby %s HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Ashby %s request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Ashby %s connection failed",
                company,
            )
            continue

        for job in jobs:
            normalized_jobs.append(
                normalize_ashby_job(
                    job,
                    company,
                    board_name,
                )
            )

    return normalized_jobs


def main():
    print("InfraJob Agent")
    print("=" * 60)

    logger.info("InfraJob Agent started")
    create_jobs_table()

    sources = load_sources()

    remotive_jobs = collect_remotive_jobs(
        sources["remotive"]["search_terms"]
    )

    greenhouse_jobs = collect_greenhouse_jobs(
        sources["greenhouse"]["boards"]
    )

    personio_jobs = collect_personio_jobs(
    sources["personio"]["accounts"]
    )

    lever_jobs = collect_lever_jobs(
    sources["lever"]["sites"]
    )

    ashby_jobs = collect_ashby_jobs(
    sources["ashby"]["boards"]
    )

    all_jobs = (
    remotive_jobs
    + greenhouse_jobs
    + personio_jobs
    + lever_jobs
    + ashby_jobs
    )

    enriched_jobs = [
    enrich_job(job)
    for job in all_jobs
    ]

    unique_jobs = remove_duplicates(enriched_jobs)

    relevant_jobs = filter_jobs(unique_jobs)

    scored_jobs = []

    for job in relevant_jobs:
        score, matched_skills = calculate_job_score(job)

        if score >= MINIMUM_SCORE:
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

    for item in scored_jobs:
        job = item["job"]
        score = item["score"]

        save_job(job, score)

        logger.info(
            "Saved job to database: %s | %s | score=%d",
            job["company"],
            job["title"],
            score,
        )

    print()
    print("=" * 60)
    print(f"Remotive jobs: {len(remotive_jobs)}")
    print(f"Greenhouse jobs: {len(greenhouse_jobs)}")
    print(f"Personio jobs: {len(personio_jobs)}")
    print(f"Lever jobs: {len(lever_jobs)}")
    print(f"Ashby jobs: {len(ashby_jobs)}")
    print(f"Total jobs: {len(all_jobs)}")
    print(f"Unique jobs: {len(unique_jobs)}")
    print(f"Relevant jobs: {len(relevant_jobs)}")
    print(f"Qualified jobs: {len(scored_jobs)}")
    print("=" * 60)
    print()

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

    logger.info(
        "Pipeline completed: %d total, %d unique, %d relevant, %d qualified",
        len(all_jobs),
        len(unique_jobs),
        len(relevant_jobs),
        len(scored_jobs),
    )


if __name__ == "__main__":
    main()