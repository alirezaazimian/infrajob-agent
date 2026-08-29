import requests

from app.collectors.remotive import fetch_jobs
from app.collectors.greenhouse import fetch_greenhouse_jobs
from app.collectors.personio import fetch_personio_jobs
from app.collectors.lever import fetch_lever_jobs
from app.collectors.ashby import fetch_ashby_jobs

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
from app.database import (
    create_jobs_table,
    save_job,
)
from app.job_enricher import enrich_job

from app.opportunity_scorer import (
    calculate_opportunity_score,
)

from app.actionability import (
    classify_actionability,
    get_actionability_priority,
)


MINIMUM_SCORE = 30

logger = setup_logger()


def collect_remotive_jobs(search_terms):
    normalized_jobs = []

    for term in search_terms:
        print(
            f"Searching Remotive: {term}"
        )

        logger.info(
            "Collecting Remotive jobs "
            "for search term: %s",
            term,
        )

        try:
            jobs = fetch_jobs(
                term
            )

            logger.info(
                "Remotive search '%s' "
                "returned %d jobs",
                term,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Remotive search '%s' "
                "HTTP error: %s",
                term,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Remotive search '%s' "
                "timed out",
                term,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Remotive search '%s' "
                "connection failed",
                term,
            )
            continue

        for job in jobs:
            normalized_jobs.append(
                normalize_remotive_job(
                    job
                )
            )

    return normalized_jobs


def collect_greenhouse_jobs(boards):
    normalized_jobs = []

    for board in boards:
        board_name = (
            board["board_name"]
        )

        company = (
            board["company"]
        )

        print(
            f"Collecting Greenhouse: "
            f"{company}"
        )

        logger.info(
            "Collecting Greenhouse "
            "jobs for %s",
            company,
        )

        try:
            jobs = (
                fetch_greenhouse_jobs(
                    board_name
                )
            )

            logger.info(
                "Greenhouse %s "
                "returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Greenhouse %s "
                "HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Greenhouse %s "
                "request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Greenhouse %s "
                "connection failed",
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
        account = (
            account_config["account"]
        )

        company = (
            account_config["company"]
        )

        language = account_config.get(
            "language",
            "en",
        )

        print(
            f"Collecting Personio: "
            f"{company}"
        )

        logger.info(
            "Collecting Personio "
            "jobs for %s",
            company,
        )

        try:
            jobs = fetch_personio_jobs(
                account,
                language=language,
            )

            logger.info(
                "Personio %s "
                "returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Personio %s "
                "HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Personio %s "
                "request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Personio %s "
                "connection failed",
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
        site = (
            site_config["site"]
        )

        company = (
            site_config["company"]
        )

        region = site_config.get(
            "region",
            "global",
        )

        print(
            f"Collecting Lever: "
            f"{company}"
        )

        logger.info(
            "Collecting Lever "
            "jobs for %s",
            company,
        )

        try:
            jobs = fetch_lever_jobs(
                site,
                region=region,
            )

            logger.info(
                "Lever %s "
                "returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Lever %s "
                "HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Lever %s "
                "request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Lever %s "
                "connection failed",
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
        board_name = (
            board["board_name"]
        )

        company = (
            board["company"]
        )

        print(
            f"Collecting Ashby: "
            f"{company}"
        )

        logger.info(
            "Collecting Ashby "
            "jobs for %s",
            company,
        )

        try:
            jobs = fetch_ashby_jobs(
                board_name
            )

            logger.info(
                "Ashby %s "
                "returned %d jobs",
                company,
                len(jobs),
            )

        except requests.exceptions.HTTPError as error:
            logger.error(
                "Ashby %s "
                "HTTP error: %s",
                company,
                error,
            )
            continue

        except requests.exceptions.Timeout:
            logger.error(
                "Ashby %s "
                "request timed out",
                company,
            )
            continue

        except requests.exceptions.ConnectionError:
            logger.error(
                "Ashby %s "
                "connection failed",
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
    print(
        "InfraJob Agent"
    )

    print(
        "=" * 60
    )

    logger.info(
        "InfraJob Agent started"
    )

    create_jobs_table()

    sources = load_sources()

    # --------------------------------------------------
    # Collection
    # --------------------------------------------------

    remotive_jobs = (
        collect_remotive_jobs(
            sources[
                "remotive"
            ][
                "search_terms"
            ]
        )
    )

    greenhouse_jobs = (
        collect_greenhouse_jobs(
            sources[
                "greenhouse"
            ][
                "boards"
            ]
        )
    )

    personio_jobs = (
        collect_personio_jobs(
            sources[
                "personio"
            ][
                "accounts"
            ]
        )
    )

    lever_jobs = (
        collect_lever_jobs(
            sources[
                "lever"
            ][
                "sites"
            ]
        )
    )

    ashby_jobs = (
        collect_ashby_jobs(
            sources[
                "ashby"
            ][
                "boards"
            ]
        )
    )

    # --------------------------------------------------
    # Merge
    # --------------------------------------------------

    all_jobs = (
        remotive_jobs
        + greenhouse_jobs
        + personio_jobs
        + lever_jobs
        + ashby_jobs
    )

    # --------------------------------------------------
    # Enrichment
    #
    # Country
    # Work authorization
    # Sponsorship
    # Relocation
    # Language
    # Immigration
    # --------------------------------------------------

    enriched_jobs = [
        enrich_job(job)
        for job in all_jobs
    ]

    # --------------------------------------------------
    # Deduplication
    # --------------------------------------------------

    unique_jobs = (
        remove_duplicates(
            enriched_jobs
        )
    )

    # --------------------------------------------------
    # Relevance filtering
    # --------------------------------------------------

    relevant_jobs = (
        filter_jobs(
            unique_jobs
        )
    )

    scored_jobs = []

    # --------------------------------------------------
    # Technical scoring
    # --------------------------------------------------

    for job in relevant_jobs:
        (
            score,
            matched_skills,
        ) = calculate_job_score(
            job
        )

        if score < MINIMUM_SCORE:
            continue

        # ----------------------------------------------
        # Opportunity scoring
        # ----------------------------------------------

        opportunity_result = (
            calculate_opportunity_score(
                job,
                score,
            )
        )

        job[
            "opportunity_score"
        ] = opportunity_result[
            "opportunity_score"
        ]

        job[
            "raw_opportunity_score"
        ] = opportunity_result[
            "raw_opportunity_score"
        ]

        job[
            "hard_blocked"
        ] = opportunity_result[
            "hard_blocked"
        ]

        job[
            "hard_blockers"
        ] = opportunity_result[
            "hard_blockers"
        ]

        job[
            "opportunity_breakdown"
        ] = opportunity_result[
            "breakdown"
        ]

        # ----------------------------------------------
        # Actionability classification
        # ----------------------------------------------

        actionability_result = (
            classify_actionability(
                job
            )
        )

        job[
            "actionability"
        ] = actionability_result[
            "actionability"
        ]

        job[
            "market_group"
        ] = actionability_result[
            "market_group"
        ]

        job[
            "actionability_reasons"
        ] = actionability_result[
            "reasons"
        ]

        scored_jobs.append(
            {
                "job": job,
                "score": score,
                "matched_skills": (
                    matched_skills
                ),
            }
        )

    # --------------------------------------------------
    # Final ranking
    #
    # 1. Actionability
    # 2. Opportunity Score
    # 3. Technical Score
    # --------------------------------------------------

    scored_jobs.sort(
        key=lambda item: (
            get_actionability_priority(
                item["job"].get(
                    "actionability",
                    "unclassified",
                )
            ),

            item["job"].get(
                "opportunity_score",
                0,
            ),

            item["score"],
        ),
        reverse=True,
    )

    # --------------------------------------------------
    # Persistence
    # --------------------------------------------------

    for item in scored_jobs:
        job = item["job"]
        score = item["score"]

        save_job(
            job,
            score,
        )

        logger.info(
            "Saved job to database: "
            "%s | %s | "
            "technical=%d | "
            "opportunity=%d | "
            "actionability=%s",
            job["company"],
            job["title"],
            score,
            job[
                "opportunity_score"
            ],
            job[
                "actionability"
            ],
        )

    # --------------------------------------------------
    # Pipeline summary
    # --------------------------------------------------

    print()

    print(
        "=" * 60
    )

    print(
        f"Remotive jobs: "
        f"{len(remotive_jobs)}"
    )

    print(
        f"Greenhouse jobs: "
        f"{len(greenhouse_jobs)}"
    )

    print(
        f"Personio jobs: "
        f"{len(personio_jobs)}"
    )

    print(
        f"Lever jobs: "
        f"{len(lever_jobs)}"
    )

    print(
        f"Ashby jobs: "
        f"{len(ashby_jobs)}"
    )

    print(
        f"Total jobs: "
        f"{len(all_jobs)}"
    )

    print(
        f"Unique jobs: "
        f"{len(unique_jobs)}"
    )

    print(
        f"Relevant jobs: "
        f"{len(relevant_jobs)}"
    )

    print(
        f"Qualified jobs: "
        f"{len(scored_jobs)}"
    )

    print(
        "=" * 60
    )

    print()

    # --------------------------------------------------
    # Ranked output
    # --------------------------------------------------

    for index, item in enumerate(
        scored_jobs,
        start=1,
    ):
        job = item["job"]

        score = item[
            "score"
        ]

        matched_skills = item[
            "matched_skills"
        ]

        print(
            f"{index}. "
            f"{job['title']}"
        )

        print(
            f"   Company: "
            f"{job['company']}"
        )

        print(
            f"   Location: "
            f"{job['location']}"
        )

        print(
            f"   Country: "
            f"{job.get(
                'country'
            ) or 'Unknown'}"
        )

        print(
            f"   Source: "
            f"{job['source']}"
        )

        print(
            f"   Technical Score: "
            f"{score}/100"
        )

        print(
            f"   Opportunity Score: "
            f"{job.get(
                'opportunity_score',
                0
            )}/100"
        )

        print(
            f"   Actionability: "
            f"{job.get(
                'actionability',
                'unclassified'
            ).upper()}"
        )

        print(
            f"   Market Group: "
            f"{job.get(
                'market_group',
                'unknown'
            )}"
        )

        print(
            f"   Immigration: "
            f"{job.get(
                'immigration_assessment',
                'not_evaluated'
            )}"
        )

        print(
            f"   Language: "
            f"{job.get(
                'language_requirement',
                'unknown'
            )}"
        )

        print(
            f"   Sponsorship Evidence: "
            f"{job.get(
                'sponsorship_evidence',
                False
            )}"
        )

        print(
            f"   Relocation Evidence: "
            f"{job.get(
                'relocation_evidence',
                False
            )}"
        )

        print(
            f"   Hard Blocked: "
            f"{job.get(
                'hard_blocked',
                False
            )}"
        )

        actionability_reasons = (
            job.get(
                "actionability_reasons",
                [],
            )
        )

        if actionability_reasons:
            print(
                "   Actionability Reasons: "
                + ", ".join(
                    actionability_reasons
                )
            )

        hard_blockers = job.get(
            "hard_blockers",
            [],
        )

        if hard_blockers:
            print(
                "   Hard Blockers: "
                + ", ".join(
                    hard_blockers
                )
            )

        if matched_skills:
            print(
                "   Matched skills: "
                + ", ".join(
                    matched_skills
                )
            )

        print()

    # --------------------------------------------------
    # Actionability summary
    # --------------------------------------------------

    actionability_counts = {}

    for item in scored_jobs:
        actionability = (
            item["job"].get(
                "actionability",
                "unclassified",
            )
        )

        actionability_counts[
            actionability
        ] = (
            actionability_counts.get(
                actionability,
                0,
            )
            + 1
        )

    print(
        "=" * 60
    )

    print(
        "Actionability Summary"
    )

    print(
        "=" * 60
    )

    for category in [
        "high_priority",
        "review",
        "low_priority",
        "not_targeted",
        "blocked",
        "unclassified",
    ]:
        count = (
            actionability_counts.get(
                category,
                0,
            )
        )

        print(
            f"{category.upper()}: "
            f"{count}"
        )

    # --------------------------------------------------
    # Final log
    # --------------------------------------------------

    logger.info(
        "Pipeline completed: "
        "%d total, "
        "%d unique, "
        "%d relevant, "
        "%d qualified",
        len(all_jobs),
        len(unique_jobs),
        len(relevant_jobs),
        len(scored_jobs),
    )


if __name__ == "__main__":
    main()