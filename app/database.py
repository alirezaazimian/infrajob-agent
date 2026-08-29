import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json


load_dotenv(".env")


VALID_STATUSES = {
    "new",
    "reviewing",
    "approved",
    "applied",
    "interview",
    "rejected",
    "archived",
}


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def create_jobs_table():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,

                    external_id VARCHAR(255)
                        UNIQUE
                        NOT NULL,

                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,

                    country_code VARCHAR(10),
                    country VARCHAR(100),
                    country_confidence VARCHAR(20),

                    work_authorization_blocked BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    work_authorization_signals JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    sponsorship_evidence BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    relocation_evidence BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    international_hiring_evidence BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    positive_eligibility_signals JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    language_requirement VARCHAR(50)
                        NOT NULL
                        DEFAULT 'unknown',

                    german_required BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    german_preferred BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    english_required BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    other_required_languages JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    language_signals JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    immigration_assessment VARCHAR(50)
                        NOT NULL
                        DEFAULT 'not_evaluated',

                    immigration_market_enabled BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    immigration_pathways JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    opportunity_score INTEGER
                        NOT NULL
                        DEFAULT 0,

                    raw_opportunity_score INTEGER
                        NOT NULL
                        DEFAULT 0,

                    hard_blocked BOOLEAN
                        NOT NULL
                        DEFAULT FALSE,

                    hard_blockers JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    opportunity_breakdown JSONB
                        NOT NULL
                        DEFAULT '{}'::jsonb,

                    actionability VARCHAR(30)
                        NOT NULL
                        DEFAULT 'unclassified',

                    market_group VARCHAR(30)
                        NOT NULL
                        DEFAULT 'unknown',

                    actionability_reasons JSONB
                        NOT NULL
                        DEFAULT '[]'::jsonb,

                    description TEXT,
                    url TEXT,
                    source VARCHAR(50),
                    score INTEGER,

                    status VARCHAR(30)
                        NOT NULL
                        DEFAULT 'new',

                    first_seen TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    last_seen TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # --------------------------------------------------
            # Country migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                country_code VARCHAR(10);
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                country VARCHAR(100);
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                country_confidence VARCHAR(20);
                """
            )

            # --------------------------------------------------
            # Work authorization migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                work_authorization_blocked BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                work_authorization_signals JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            # --------------------------------------------------
            # Eligibility evidence migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                sponsorship_evidence BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                relocation_evidence BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                international_hiring_evidence BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                positive_eligibility_signals JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            # --------------------------------------------------
            # Language migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                language_requirement VARCHAR(50)
                NOT NULL
                DEFAULT 'unknown';
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                german_required BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                german_preferred BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                english_required BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                other_required_languages JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                language_signals JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            # --------------------------------------------------
            # Immigration migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                immigration_assessment VARCHAR(50)
                NOT NULL
                DEFAULT 'not_evaluated';
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                immigration_market_enabled BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                immigration_pathways JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            # --------------------------------------------------
            # Opportunity scoring migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                opportunity_score INTEGER
                NOT NULL
                DEFAULT 0;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                raw_opportunity_score INTEGER
                NOT NULL
                DEFAULT 0;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                hard_blocked BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                hard_blockers JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                opportunity_breakdown JSONB
                NOT NULL
                DEFAULT '{}'::jsonb;
                """
            )

            # --------------------------------------------------
            # Actionability migrations
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                actionability VARCHAR(30)
                NOT NULL
                DEFAULT 'unclassified';
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                market_group VARCHAR(30)
                NOT NULL
                DEFAULT 'unknown';
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                actionability_reasons JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            # --------------------------------------------------
            # Application status
            # --------------------------------------------------

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                status VARCHAR(30)
                NOT NULL
                DEFAULT 'new';
                """
            )

        connection.commit()

    finally:
        connection.close()


def save_job(job, score):
    connection = get_connection()

    params = {
        "external_id": job["external_id"],
        "title": job["title"],
        "company": job.get("company"),
        "location": job.get("location"),

        "country_code": job.get("country_code"),
        "country": job.get("country"),
        "country_confidence": job.get(
            "country_confidence"
        ),

        "work_authorization_blocked": job.get(
            "work_authorization_blocked",
            False,
        ),

        "work_authorization_signals": Json(
            job.get(
                "work_authorization_signals",
                [],
            )
        ),

        "sponsorship_evidence": job.get(
            "sponsorship_evidence",
            False,
        ),

        "relocation_evidence": job.get(
            "relocation_evidence",
            False,
        ),

        "international_hiring_evidence": job.get(
            "international_hiring_evidence",
            False,
        ),

        "positive_eligibility_signals": Json(
            job.get(
                "positive_eligibility_signals",
                [],
            )
        ),

        "language_requirement": job.get(
            "language_requirement",
            "unknown",
        ),

        "german_required": job.get(
            "german_required",
            False,
        ),

        "german_preferred": job.get(
            "german_preferred",
            False,
        ),

        "english_required": job.get(
            "english_required",
            False,
        ),

        "other_required_languages": Json(
            job.get(
                "other_required_languages",
                [],
            )
        ),

        "language_signals": Json(
            job.get(
                "language_signals",
                [],
            )
        ),

        "immigration_assessment": job.get(
            "immigration_assessment",
            "not_evaluated",
        ),

        "immigration_market_enabled": job.get(
            "immigration_market_enabled",
            False,
        ),

        "immigration_pathways": Json(
            job.get(
                "immigration_pathways",
                [],
            )
        ),

        "opportunity_score": job.get(
            "opportunity_score",
            0,
        ),

        "raw_opportunity_score": job.get(
            "raw_opportunity_score",
            0,
        ),

        "hard_blocked": job.get(
            "hard_blocked",
            False,
        ),

        "hard_blockers": Json(
            job.get(
                "hard_blockers",
                [],
            )
        ),

        "opportunity_breakdown": Json(
            job.get(
                "opportunity_breakdown",
                {},
            )
        ),

        "actionability": job.get(
            "actionability",
            "unclassified",
        ),

        "market_group": job.get(
            "market_group",
            "unknown",
        ),

        "actionability_reasons": Json(
            job.get(
                "actionability_reasons",
                [],
            )
        ),

        "description": job.get(
            "description",
            "",
        ),

        "url": job.get(
            "url",
            "",
        ),

        "source": job.get(
            "source",
            "",
        ),

        "score": score,
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs (
                    external_id,
                    title,
                    company,
                    location,

                    country_code,
                    country,
                    country_confidence,

                    work_authorization_blocked,
                    work_authorization_signals,

                    sponsorship_evidence,
                    relocation_evidence,
                    international_hiring_evidence,
                    positive_eligibility_signals,

                    language_requirement,
                    german_required,
                    german_preferred,
                    english_required,
                    other_required_languages,
                    language_signals,

                    immigration_assessment,
                    immigration_market_enabled,
                    immigration_pathways,

                    opportunity_score,
                    raw_opportunity_score,
                    hard_blocked,
                    hard_blockers,
                    opportunity_breakdown,

                    actionability,
                    market_group,
                    actionability_reasons,

                    description,
                    url,
                    source,
                    score
                )
                VALUES (
                    %(external_id)s,
                    %(title)s,
                    %(company)s,
                    %(location)s,

                    %(country_code)s,
                    %(country)s,
                    %(country_confidence)s,

                    %(work_authorization_blocked)s,
                    %(work_authorization_signals)s,

                    %(sponsorship_evidence)s,
                    %(relocation_evidence)s,
                    %(international_hiring_evidence)s,
                    %(positive_eligibility_signals)s,

                    %(language_requirement)s,
                    %(german_required)s,
                    %(german_preferred)s,
                    %(english_required)s,
                    %(other_required_languages)s,
                    %(language_signals)s,

                    %(immigration_assessment)s,
                    %(immigration_market_enabled)s,
                    %(immigration_pathways)s,

                    %(opportunity_score)s,
                    %(raw_opportunity_score)s,
                    %(hard_blocked)s,
                    %(hard_blockers)s,
                    %(opportunity_breakdown)s,

                    %(actionability)s,
                    %(market_group)s,
                    %(actionability_reasons)s,

                    %(description)s,
                    %(url)s,
                    %(source)s,
                    %(score)s
                )

                ON CONFLICT (external_id)

                DO UPDATE SET
                    title =
                        EXCLUDED.title,

                    company =
                        EXCLUDED.company,

                    location =
                        EXCLUDED.location,

                    country_code =
                        EXCLUDED.country_code,

                    country =
                        EXCLUDED.country,

                    country_confidence =
                        EXCLUDED.country_confidence,

                    work_authorization_blocked =
                        EXCLUDED.work_authorization_blocked,

                    work_authorization_signals =
                        EXCLUDED.work_authorization_signals,

                    sponsorship_evidence =
                        EXCLUDED.sponsorship_evidence,

                    relocation_evidence =
                        EXCLUDED.relocation_evidence,

                    international_hiring_evidence =
                        EXCLUDED.international_hiring_evidence,

                    positive_eligibility_signals =
                        EXCLUDED.positive_eligibility_signals,

                    language_requirement =
                        EXCLUDED.language_requirement,

                    german_required =
                        EXCLUDED.german_required,

                    german_preferred =
                        EXCLUDED.german_preferred,

                    english_required =
                        EXCLUDED.english_required,

                    other_required_languages =
                        EXCLUDED.other_required_languages,

                    language_signals =
                        EXCLUDED.language_signals,

                    immigration_assessment =
                        EXCLUDED.immigration_assessment,

                    immigration_market_enabled =
                        EXCLUDED.immigration_market_enabled,

                    immigration_pathways =
                        EXCLUDED.immigration_pathways,

                    opportunity_score =
                        EXCLUDED.opportunity_score,

                    raw_opportunity_score =
                        EXCLUDED.raw_opportunity_score,

                    hard_blocked =
                        EXCLUDED.hard_blocked,

                    hard_blockers =
                        EXCLUDED.hard_blockers,

                    opportunity_breakdown =
                        EXCLUDED.opportunity_breakdown,

                    actionability =
                        EXCLUDED.actionability,

                    market_group =
                        EXCLUDED.market_group,

                    actionability_reasons =
                        EXCLUDED.actionability_reasons,

                    description =
                        EXCLUDED.description,

                    url =
                        EXCLUDED.url,

                    source =
                        EXCLUDED.source,

                    score =
                        EXCLUDED.score,

                    last_seen =
                        CURRENT_TIMESTAMP;
                """,
                params,
            )

        connection.commit()

    finally:
        connection.close()


def update_job_status(
    external_id,
    status,
):
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status}. "
            f"Allowed statuses: "
            f"{', '.join(sorted(VALID_STATUSES))}"
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET status = %s
                WHERE external_id = %s;
                """,
                (
                    status,
                    external_id,
                ),
            )

        connection.commit()

    finally:
        connection.close()