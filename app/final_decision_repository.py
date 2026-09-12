from __future__ import annotations

from psycopg2.extras import Json

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"
DECISION_VERSION = "m21.4.1"


def _assert_infrajob_database(connection):
    """
    Safety guard.

    Refuse final-decision schema/data writes unless the active
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
            "No InfraJob final-decision changes were performed."
        )


def ensure_final_decision_columns():
    """
    Add final vacancy decision persistence columns to jobs.

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
                final_decision VARCHAR(20);
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                final_decision_reasons JSONB;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                final_decision_blockers JSONB;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                final_decision_review_flags JSONB;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                final_decision_version VARCHAR(30);
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                final_decision_at TIMESTAMPTZ;
                """
            )

            cursor.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                final_decision_run_id VARCHAR(36);
                """
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_final_vacancy_decision(job, run_id):
    """
    Persist the final vacancy routing decision.

    APPLY / REVIEW / SKIP describe whether the vacancy may advance
    into the later application workflow. This does not submit an
    application and does not compare against a candidate profile.
    """

    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        decision = (
            job.get(
                "final_decision"
            )
            or "unclassified"
        )

        reasons = (
            job.get(
                "final_decision_reasons"
            )
            or []
        )

        blockers = (
            job.get(
                "final_decision_blockers"
            )
            or []
        )

        review_flags = (
            job.get(
                "final_decision_review_flags"
            )
            or []
        )

        version = (
            job.get(
                "final_decision_version"
            )
            or DECISION_VERSION
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET
                    final_decision = %(decision)s,
                    final_decision_reasons = %(reasons)s,
                    final_decision_blockers = %(blockers)s,
                    final_decision_review_flags = %(review_flags)s,
                    final_decision_version = %(version)s,
                    final_decision_at = NOW(),
                    final_decision_run_id = %(run_id)s
                WHERE external_id = %(external_id)s;
                """,
                {
                    "external_id": job[
                        "external_id"
                    ],
                    "decision": decision,
                    "reasons": Json(
                        reasons
                    ),
                    "blockers": Json(
                        blockers
                    ),
                    "review_flags": Json(
                        review_flags
                    ),
                    "version": version,
                    "run_id": run_id,
                },
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
