from psycopg2.extras import Json

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"


def _assert_infrajob_database(
    connection,
):
    """
    Refuse schema/data writes unless PostgreSQL is connected
    to the InfraJob Agent database.
    """

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database();"
        )

        current_database = (
            cursor.fetchone()[0]
        )

    if current_database != EXPECTED_DATABASE:
        raise RuntimeError(
            "Database safety check failed: "
            f"expected '{EXPECTED_DATABASE}', "
            f"but connected to '{current_database}'. "
            "No InfraJob schema/data changes were performed."
        )


def ensure_vacancy_readiness_columns():
    """
    Add Vacancy Readiness columns only to the InfraJob database.
    The database-name safety check runs before ALTER TABLE.
    """

    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

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

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_vacancy_readiness(
    job,
):
    """
    Persist the readiness decision only inside the InfraJob DB.
    """

    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

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
                    "external_id": job[
                        "external_id"
                    ],
                    "vacancy_readiness": (
                        job.get(
                            "vacancy_readiness",
                            "unclassified",
                        )
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

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
