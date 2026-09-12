from __future__ import annotations

from psycopg2.extras import Json

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"
MATCHER_VERSION = "m23.1"


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
            "No InfraJob candidate-match changes were performed."
        )


def ensure_candidate_match_columns():
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
                candidate_match JSONB;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_status VARCHAR(40);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_score INTEGER;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_coverage INTEGER;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_skip_reason TEXT;
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_version VARCHAR(30);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_profile_schema VARCHAR(30);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_run_id VARCHAR(36);
                """,
                """
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS
                candidate_match_at TIMESTAMPTZ;
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


def save_candidate_match(
    job,
    run_id,
    candidate_profile_schema,
):
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        candidate_match = job.get(
            "candidate_match"
        )

        skip_reason = job.get(
            "candidate_match_skip_reason"
        )

        if candidate_match:
            summary = candidate_match.get(
                "summary",
                {},
            )

            status = summary.get(
                "overall",
                "unclassified",
            )

            score = summary.get(
                "score"
            )

            coverage = summary.get(
                "coverage_percent"
            )

            version = candidate_match.get(
                "version",
                MATCHER_VERSION,
            )

            payload = Json(
                candidate_match
            )

        else:
            status = "skipped"
            score = None
            coverage = None
            version = MATCHER_VERSION
            payload = None

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET
                    candidate_match = %(candidate_match)s,
                    candidate_match_status = %(status)s,
                    candidate_match_score = %(score)s,
                    candidate_match_coverage = %(coverage)s,
                    candidate_match_skip_reason = %(skip_reason)s,
                    candidate_match_version = %(version)s,
                    candidate_profile_schema = %(profile_schema)s,
                    candidate_match_run_id = %(run_id)s,
                    candidate_match_at = NOW()
                WHERE external_id = %(external_id)s;
                """,
                {
                    "external_id": job[
                        "external_id"
                    ],
                    "candidate_match": payload,
                    "status": status,
                    "score": score,
                    "coverage": coverage,
                    "skip_reason": skip_reason,
                    "version": version,
                    "profile_schema": (
                        candidate_profile_schema
                    ),
                    "run_id": run_id,
                },
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
