from __future__ import annotations

from psycopg2.extras import Json

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"
APPLICATION_DECISION_VERSION = "m24.1"


def _assert_infrajob_database(connection):
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
            "No InfraJob application-decision changes were performed."
        )


def ensure_application_decision_columns():
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        with connection.cursor() as cursor:
            statements = [
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision VARCHAR(40);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_reasons JSONB;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_blockers JSONB;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_review_flags JSONB;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_inputs JSONB;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_version VARCHAR(30);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_run_id VARCHAR(36);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                application_decision_at TIMESTAMPTZ;
                """,
            ]

            for statement in statements:
                cursor.execute(
                    statement
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_application_decision(
    job,
    run_id,
):
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        decision = (
            job.get(
                "application_decision",
                "unclassified",
            )
            or "unclassified"
        )

        reasons = (
            job.get(
                "application_decision_reasons",
                [],
            )
            or []
        )

        blockers = (
            job.get(
                "application_decision_blockers",
                [],
            )
            or []
        )

        review_flags = (
            job.get(
                "application_decision_review_flags",
                [],
            )
            or []
        )

        inputs = (
            job.get(
                "application_decision_inputs",
                {},
            )
            or {}
        )

        version = (
            job.get(
                "application_decision_version",
                APPLICATION_DECISION_VERSION,
            )
            or APPLICATION_DECISION_VERSION
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET
                    application_decision = %(decision)s,
                    application_decision_reasons = %(reasons)s,
                    application_decision_blockers = %(blockers)s,
                    application_decision_review_flags = %(review_flags)s,
                    application_decision_inputs = %(inputs)s,
                    application_decision_version = %(version)s,
                    application_decision_run_id = %(run_id)s,
                    application_decision_at = NOW()
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
                    "inputs": Json(
                        inputs
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
