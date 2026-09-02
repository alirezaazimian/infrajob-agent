from __future__ import annotations

from psycopg2.extras import Json

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"
VALIDATION_VERSION = "m21.3.2"


def _assert_infrajob_database(connection):
    """
    Safety guard.

    Refuse live-validation schema/data writes unless the active
    PostgreSQL connection is the InfraJob Agent database.
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
            "No InfraJob live-validation changes were performed."
        )


def ensure_live_validation_columns():
    """
    Add live-vacancy-validation persistence columns to jobs.
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
                live_validation JSONB;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                live_validation_status VARCHAR(20);
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                live_validation_checked_at TIMESTAMPTZ;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                live_validation_version VARCHAR(30);
                """
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_live_validation(job):
    """
    Persist the current live-validation snapshot.

    LIVE/CLOSED/REVIEW/SKIPPED are all persisted so later stages
    can distinguish "not checked because ineligible" from
    "checked and confirmed live".
    """

    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        live_validation = (
            job.get(
                "live_validation"
            )
            or {}
        )

        status = (
            live_validation.get(
                "status"
            )
            or "unclassified"
        )

        version = (
            live_validation.get(
                "version"
            )
            or VALIDATION_VERSION
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET
                    live_validation = %(live_validation)s,
                    live_validation_status = %(status)s,
                    live_validation_checked_at = NOW(),
                    live_validation_version = %(version)s
                WHERE external_id = %(external_id)s;
                """,
                {
                    "external_id": job[
                        "external_id"
                    ],
                    "live_validation": Json(
                        live_validation
                    ),
                    "status": status,
                    "version": version,
                },
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
