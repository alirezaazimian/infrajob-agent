from psycopg2.extras import Json

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"
EXTRACTOR_VERSION = "m21.2.2"


def _assert_infrajob_database(connection):
    """
    Safety guard.

    Refuse requirement schema/data writes unless the active
    PostgreSQL connection points to the InfraJob Agent database.
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
            "No InfraJob requirement changes were performed."
        )


def ensure_requirement_columns():
    """
    Add Requirement Extractor persistence columns to the jobs table.
    The database-name safety guard runs before ALTER TABLE.
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
                requirements JSONB;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                requirements_extracted_at TIMESTAMPTZ;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                requirements_extractor_version VARCHAR(30);
                """
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_job_requirements(job):
    """
    Persist the current extracted requirement snapshot.

    READY/REVIEW jobs receive the complete JSON payload.
    If a job is no longer extraction-eligible, stale requirement
    data is cleared so the database reflects current pipeline state.
    """

    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        requirements = job.get(
            "requirements"
        )

        with connection.cursor() as cursor:
            if requirements is None:
                cursor.execute(
                    """
                    UPDATE jobs
                    SET
                        requirements = NULL,
                        requirements_extracted_at = NULL,
                        requirements_extractor_version = NULL
                    WHERE external_id = %(external_id)s;
                    """,
                    {
                        "external_id": job[
                            "external_id"
                        ],
                    },
                )

            else:
                cursor.execute(
                    """
                    UPDATE jobs
                    SET
                        requirements = %(requirements)s,
                        requirements_extracted_at = NOW(),
                        requirements_extractor_version = %(version)s
                    WHERE external_id = %(external_id)s;
                    """,
                    {
                        "external_id": job[
                            "external_id"
                        ],
                        "requirements": Json(
                            requirements
                        ),
                        "version": EXTRACTOR_VERSION,
                    },
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
