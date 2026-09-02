from psycopg2.extras import Json

from app.database import get_connection


def ensure_vacancy_readiness_columns():
    """
    Add Vacancy Readiness persistence columns to the existing
    jobs table without changing application-state behavior.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                vacancy_readiness VARCHAR(30)
                NOT NULL
                DEFAULT 'unclassified';
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                readiness_reasons JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                readiness_blockers JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                readiness_review_flags JSONB
                NOT NULL
                DEFAULT '[]'::jsonb;
                """
            )

        connection.commit()

    finally:
        connection.close()


def save_vacancy_readiness(
    job,
):
    """
    Persist the latest readiness decision for an already
    UPSERTed job row.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET
                    vacancy_readiness =
                        %(vacancy_readiness)s,

                    readiness_reasons =
                        %(readiness_reasons)s,

                    readiness_blockers =
                        %(readiness_blockers)s,

                    readiness_review_flags =
                        %(readiness_review_flags)s

                WHERE external_id =
                    %(external_id)s;
                """,
                {
                    "external_id": job["external_id"],
                    "vacancy_readiness": job.get(
                        "vacancy_readiness",
                        "unclassified",
                    ),
                    "readiness_reasons": Json(
                        job.get(
                            "readiness_reasons",
                            [],
                        )
                    ),
                    "readiness_blockers": Json(
                        job.get(
                            "readiness_blockers",
                            [],
                        )
                    ),
                    "readiness_review_flags": Json(
                        job.get(
                            "readiness_review_flags",
                            [],
                        )
                    ),
                },
            )

        connection.commit()

    finally:
        connection.close()
