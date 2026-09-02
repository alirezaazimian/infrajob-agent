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

from app.vacancy_readiness import (
    classify_vacancy_readiness,
    get_readiness_priority,
)

from app.vacancy_readiness_repository import (
    ensure_vacancy_readiness_columns,
    save_vacancy_readiness,
)

from app.requirement_extractor import (
    extract_requirements,
)

from app.requirement_completion import (
    evaluate_requirement_completion,
)

from app.requirement_repository import (
    ensure_requirement_columns,
    save_job_requirements,
)

from app.live_vacancy_validator import (
    validate_live_vacancy,
    skipped_live_validation,
)

from app.live_validation_repository import (
    ensure_live_validation_columns,
    save_live_validation,
)

from app.source_registry import (
    get_all_company_sources,
    get_enabled_company_sources,
)


MINIMUM_SCORE = 30

logger = setup_logger()


# ======================================================
# Remotive
# ======================================================


def collect_remotive_jobs(
    search_terms,
):
    normalized_jobs = []

    for term in search_terms:
        print(
            f"Searching Remotive: "
            f"{term}"
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


# ======================================================
# Greenhouse registry source
# ======================================================


def collect_greenhouse_source(
    source,
):
    company = source[
        "company"
    ]

    board_name = source[
        "identifier"
    ]

    print(
        f"Collecting Greenhouse: "
        f"{company}"
    )

    logger.info(
        "Collecting Greenhouse jobs "
        "for %s",
        company,
    )

    try:
        jobs = fetch_greenhouse_jobs(
            board_name
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

        return []

    except requests.exceptions.Timeout:
        logger.error(
            "Greenhouse %s "
            "request timed out",
            company,
        )

        return []

    except requests.exceptions.ConnectionError:
        logger.error(
            "Greenhouse %s "
            "connection failed",
            company,
        )

        return []

    return [
        normalize_greenhouse_job(
            job,
            company,
        )
        for job in jobs
    ]


# ======================================================
# Personio registry source
# ======================================================


def collect_personio_source(
    source,
):
    company = source[
        "company"
    ]

    account = source[
        "identifier"
    ]

    options = source.get(
        "options",
        {},
    )

    language = options.get(
        "language",
        "en",
    )

    print(
        f"Collecting Personio: "
        f"{company}"
    )

    logger.info(
        "Collecting Personio jobs "
        "for %s",
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

        return []

    except requests.exceptions.Timeout:
        logger.error(
            "Personio %s "
            "request timed out",
            company,
        )

        return []

    except requests.exceptions.ConnectionError:
        logger.error(
            "Personio %s "
            "connection failed",
            company,
        )

        return []

    return [
        normalize_personio_job(
            job,
            company,
            account,
        )
        for job in jobs
    ]


# ======================================================
# Lever registry source
# ======================================================


def collect_lever_source(
    source,
):
    company = source[
        "company"
    ]

    site = source[
        "identifier"
    ]

    options = source.get(
        "options",
        {},
    )

    region = options.get(
        "region",
        "global",
    )

    print(
        f"Collecting Lever: "
        f"{company}"
    )

    logger.info(
        "Collecting Lever jobs "
        "for %s",
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

        return []

    except requests.exceptions.Timeout:
        logger.error(
            "Lever %s "
            "request timed out",
            company,
        )

        return []

    except requests.exceptions.ConnectionError:
        logger.error(
            "Lever %s "
            "connection failed",
            company,
        )

        return []

    return [
        normalize_lever_job(
            job,
            company,
            site,
        )
        for job in jobs
    ]


# ======================================================
# Ashby registry source
# ======================================================


def collect_ashby_source(
    source,
):
    company = source[
        "company"
    ]

    board_name = source[
        "identifier"
    ]

    print(
        f"Collecting Ashby: "
        f"{company}"
    )

    logger.info(
        "Collecting Ashby jobs "
        "for %s",
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

        return []

    except requests.exceptions.Timeout:
        logger.error(
            "Ashby %s "
            "request timed out",
            company,
        )

        return []

    except requests.exceptions.ConnectionError:
        logger.error(
            "Ashby %s "
            "connection failed",
            company,
        )

        return []

    return [
        normalize_ashby_job(
            job,
            company,
            board_name,
        )
        for job in jobs
    ]


# ======================================================
# Registry dispatcher
# ======================================================


def collect_company_source(
    source,
):
    ats = source[
        "ats"
    ]

    if ats == "greenhouse":
        return collect_greenhouse_source(
            source
        )

    if ats == "personio":
        return collect_personio_source(
            source
        )

    if ats == "lever":
        return collect_lever_source(
            source
        )

    if ats == "ashby":
        return collect_ashby_source(
            source
        )

    logger.error(
        "Unsupported ATS '%s' "
        "for company %s",
        ats,
        source.get(
            "company",
            "Unknown",
        ),
    )

    return []


# ======================================================
# Disabled registry sources
# ======================================================


def log_disabled_registry_sources(
    sources,
):
    for source in sources:
        if source.get(
            "enabled",
            False,
        ):
            continue

        company = source[
            "company"
        ]

        ats = source[
            "ats"
        ]

        reason = source.get(
            "disabled_reason"
        )

        message = (
            f"Skipping {company} "
            f"({ats}): source disabled"
        )

        if reason:
            message += (
                f" ({reason})"
            )

        print(
            message
        )

        logger.warning(
            message
        )


# ======================================================
# Registry statistics
# ======================================================


def create_ats_job_counts():
    return {
        "greenhouse": 0,
        "personio": 0,
        "lever": 0,
        "ashby": 0,
    }


def count_sources_by_ats(
    sources,
    ats,
):
    return sum(
        1
        for source in sources
        if source.get(
            "ats"
        ) == ats
    )


# ======================================================
# Main pipeline
# ======================================================


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
    ensure_vacancy_readiness_columns()
    ensure_requirement_columns()
    ensure_live_validation_columns()

    # --------------------------------------------------
    # General source configuration
    # --------------------------------------------------

    sources = load_sources()

    # --------------------------------------------------
    # Company / ATS registry
    # --------------------------------------------------

    all_company_sources = (
        get_all_company_sources()
    )

    enabled_company_sources = (
        get_enabled_company_sources()
    )

    log_disabled_registry_sources(
        all_company_sources
    )

    # --------------------------------------------------
    # Remotive collection
    # --------------------------------------------------

    remotive_config = sources.get(
        "remotive",
        {},
    )

    if remotive_config.get(
        "enabled",
        True,
    ):
        remotive_jobs = (
            collect_remotive_jobs(
                remotive_config.get(
                    "search_terms",
                    [],
                )
            )
        )

    else:
        print(
            "Skipping Remotive: "
            "source disabled"
        )

        logger.warning(
            "Skipping Remotive: "
            "source disabled"
        )

        remotive_jobs = []

    # --------------------------------------------------
    # Registry-driven company collection
    # --------------------------------------------------

    company_jobs = []

    ats_job_counts = (
        create_ats_job_counts()
    )

    for source in (
        enabled_company_sources
    ):
        jobs = collect_company_source(
            source
        )

        company_jobs.extend(
            jobs
        )

        ats = source[
            "ats"
        ]

        if ats not in ats_job_counts:
            ats_job_counts[
                ats
            ] = 0

        ats_job_counts[
            ats
        ] += len(
            jobs
        )

    # --------------------------------------------------
    # Merge all sources
    # --------------------------------------------------

    all_jobs = (
        remotive_jobs
        + company_jobs
    )

    # --------------------------------------------------
    # Intelligence enrichment
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
    # Technical relevance filtering
    # --------------------------------------------------

    relevant_jobs = (
        filter_jobs(
            unique_jobs
        )
    )

    scored_jobs = []

    # --------------------------------------------------
    # Technical Score
    # Opportunity Score
    # Actionability
    # Vacancy Readiness
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
        # Actionability
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

        # ----------------------------------------------
        # Vacancy readiness
        # ----------------------------------------------

        readiness_result = (
            classify_vacancy_readiness(
                job
            )
        )

        job[
            "vacancy_readiness"
        ] = readiness_result[
            "readiness"
        ]

        job[
            "readiness_reasons"
        ] = readiness_result[
            "reasons"
        ]

        job[
            "readiness_blockers"
        ] = readiness_result[
            "blockers"
        ]

        job[
            "readiness_review_flags"
        ] = readiness_result[
            "review_flags"
        ]

        # ----------------------------------------------
        # Requirement extraction
        # ----------------------------------------------

        if job[
            "vacancy_readiness"
        ] in {
            "ready",
            "review",
        }:
            job[
                "requirements"
            ] = extract_requirements(
                job
            )

            job[
                "requirements"
            ][
                "completion"
            ] = evaluate_requirement_completion(
                job[
                    "requirements"
                ]
            )

            completion_status = job[
                "requirements"
            ][
                "completion"
            ].get(
                "status",
                "unclassified",
            )

            # ------------------------------------------
            # M21.3.1 Live vacancy validation
            #
            # Only continue when requirement extraction
            # is COMPLETE or REVIEW. INCOMPLETE
            # extractions are intentionally skipped.
            # ------------------------------------------

            if completion_status in {
                "complete",
                "review",
            }:
                job[
                    "live_validation"
                ] = validate_live_vacancy(
                    job
                )

            else:
                job[
                    "live_validation"
                ] = skipped_live_validation(
                    "requirement extraction is incomplete"
                )

        else:
            job[
                "requirements"
            ] = None

            job[
                "live_validation"
            ] = skipped_live_validation(
                "vacancy readiness is not actionable"
            )

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
    # 1. Vacancy Readiness
    # 2. Actionability
    # 3. Opportunity Score
    # 4. Technical Score
    # --------------------------------------------------

    scored_jobs.sort(
        key=lambda item: (
            get_readiness_priority(
                item["job"].get(
                    "vacancy_readiness",
                    "unclassified",
                )
            ),

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
        job = item[
            "job"
        ]

        score = item[
            "score"
        ]

        save_job(
            job,
            score,
        )

        save_vacancy_readiness(
            job
        )

        save_job_requirements(
            job
        )

        save_live_validation(
            job
        )

        logger.info(
            "Saved job to database: "
            "%s | %s | "
            "technical=%d | "
            "opportunity=%d | "
            "actionability=%s | "
            "readiness=%s",
            job["company"],
            job["title"],
            score,
            job[
                "opportunity_score"
            ],
            job[
                "actionability"
            ],
            job[
                "vacancy_readiness"
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
        f"Company sources: "
        f"{len(enabled_company_sources)} enabled "
        f"/ {len(all_company_sources)} total"
    )

    print(
        f"Remotive jobs: "
        f"{len(remotive_jobs)}"
    )

    for ats in [
        "greenhouse",
        "personio",
        "lever",
        "ashby",
    ]:
        total_sources = (
            count_sources_by_ats(
                all_company_sources,
                ats,
            )
        )

        enabled_sources = (
            count_sources_by_ats(
                enabled_company_sources,
                ats,
            )
        )

        label = ats.capitalize()

        if (
            total_sources > 0
            and enabled_sources == 0
        ):
            print(
                f"{label} jobs: "
                f"DISABLED"
            )

        else:
            print(
                f"{label} jobs: "
                f"{ats_job_counts.get(
                    ats,
                    0
                )}"
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
    # Ranked jobs
    # --------------------------------------------------

    for index, item in enumerate(
        scored_jobs,
        start=1,
    ):
        job = item[
            "job"
        ]

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
            f"   Vacancy Readiness: "
            f"{job.get(
                'vacancy_readiness',
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

        readiness_reasons = (
            job.get(
                "readiness_reasons",
                [],
            )
        )

        if readiness_reasons:
            print(
                "   Readiness Reasons: "
                + ", ".join(
                    readiness_reasons
                )
            )

        readiness_review_flags = (
            job.get(
                "readiness_review_flags",
                [],
            )
        )

        if readiness_review_flags:
            print(
                "   Readiness Review Flags: "
                + ", ".join(
                    readiness_review_flags
                )
            )

        readiness_blockers = (
            job.get(
                "readiness_blockers",
                [],
            )
        )

        if readiness_blockers:
            print(
                "   Readiness Blockers: "
                + ", ".join(
                    readiness_blockers
                )
            )

        requirements = job.get(
            "requirements"
        )

        if requirements:
            print(
                "   Requirements: "
                f"experience_min="
                f"{requirements['experience']['minimum_years']}, "
                f"degree="
                f"{requirements['education']['levels']}, "
                f"languages_required="
                f"{requirements['languages']['required']}, "
                f"location_mode="
                f"{requirements['location']['mode']}, "
                f"required_skills="
                f"{requirements['skills']['required']}"
            )

            completion = requirements.get(
                "completion",
                {},
            )

            print(
                "   Requirement Completion: "
                f"{completion.get('status', 'unclassified').upper()} "
                f"(signals={completion.get('signal_count', 0)}, "
                f"strong={completion.get('strong_requirement_count', 0)})"
            )

            completion_flags = completion.get(
                "review_flags",
                [],
            )

            if completion_flags:
                print(
                    "   Requirement Completion Flags: "
                    + ", ".join(
                        completion_flags
                    )
                )

        live_validation = job.get(
            "live_validation",
            {},
        )

        if (
            live_validation
            and live_validation.get(
                "status"
            )
            != "skipped"
        ):
            print(
                "   Live Validation: "
                f"{live_validation.get('status', 'unclassified').upper()} "
                f"(http={live_validation.get('http_status')})"
            )

            print(
                "   Live Validation Reason: "
                f"{live_validation.get('reason', '')}"
            )

            live_flags = live_validation.get(
                "review_flags",
                [],
            )

            if live_flags:
                print(
                    "   Live Validation Flags: "
                    + ", ".join(
                        live_flags
                    )
                )

        hard_blockers = (
            job.get(
                "hard_blockers",
                [],
            )
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
    # Requirement extraction completion summary
    # --------------------------------------------------

    completion_counts = {}

    for item in scored_jobs:
        requirements = item[
            "job"
        ].get(
            "requirements"
        )

        if not requirements:
            continue

        completion = requirements.get(
            "completion",
            {},
        )

        status = completion.get(
            "status",
            "unclassified",
        )

        completion_counts[
            status
        ] = (
            completion_counts.get(
                status,
                0,
            )
            + 1
        )

    print(
        "=" * 60
    )

    print(
        "Requirement Extraction Completion Summary"
    )

    print(
        "=" * 60
    )

    for category in [
        "complete",
        "review",
        "incomplete",
        "unclassified",
    ]:
        print(
            f"{category.upper()}: "
            f"{completion_counts.get(category, 0)}"
        )

    # --------------------------------------------------
    # M21.3.1 Live vacancy validation summary
    # --------------------------------------------------

    live_counts = {}

    for item in scored_jobs:
        live_validation = (
            item["job"].get(
                "live_validation",
                {},
            )
            or {}
        )

        status = live_validation.get(
            "status",
            "unclassified",
        )

        live_counts[
            status
        ] = (
            live_counts.get(
                status,
                0,
            )
            + 1
        )

    print(
        "=" * 60
    )

    print(
        "Live Vacancy Validation Summary"
    )

    print(
        "=" * 60
    )

    for category in [
        "live",
        "closed",
        "review",
        "skipped",
        "unclassified",
    ]:
        print(
            f"{category.upper()}: "
            f"{live_counts.get(category, 0)}"
        )

    # --------------------------------------------------
    # Vacancy readiness summary
    # --------------------------------------------------

    readiness_counts = {}

    for item in scored_jobs:
        readiness = (
            item["job"].get(
                "vacancy_readiness",
                "unclassified",
            )
        )

        readiness_counts[
            readiness
        ] = (
            readiness_counts.get(
                readiness,
                0,
            )
            + 1
        )

    print(
        "=" * 60
    )

    print(
        "Vacancy Readiness Summary"
    )

    print(
        "=" * 60
    )

    for category in [
        "ready",
        "review",
        "not_ready",
        "unclassified",
    ]:
        print(
            f"{category.upper()}: "
            f"{readiness_counts.get(
                category,
                0
            )}"
        )

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
        print(
            f"{category.upper()}: "
            f"{actionability_counts.get(
                category,
                0
            )}"
        )

    # --------------------------------------------------
    # Final logging
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