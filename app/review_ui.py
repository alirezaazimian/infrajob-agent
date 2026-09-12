from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from app.database import get_connection


EXPECTED_DATABASE = "infrajob"

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = FastAPI(
    title="InfraJob Review UI",
    version="m25.1.1",
)

templates = Jinja2Templates(
    directory=str(TEMPLATE_DIR)
)


def _assert_infrajob_database(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database();"
        )
        current_database = cursor.fetchone()[0]

    if current_database != EXPECTED_DATABASE:
        raise RuntimeError(
            "Database safety check failed: "
            f"expected '{EXPECTED_DATABASE}', "
            f"but connected to '{current_database}'."
        )


def _jobs_columns(connection) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'jobs';
            """
        )

        return {
            row[0]
            for row in cursor.fetchall()
        }


def _resolve_column(
    available: set[str],
    candidates: tuple[str, ...],
) -> str | None:
    for candidate in candidates:
        if candidate in available:
            return candidate

    return None


def _select_expr(
    available: set[str],
    candidates: tuple[str, ...],
    alias: str,
):
    resolved = _resolve_column(
        available,
        candidates,
    )

    if resolved is None:
        return sql.SQL(
            "NULL AS {}"
        ).format(
            sql.Identifier(alias)
        )

    return sql.SQL(
        "{} AS {}"
    ).format(
        sql.Identifier(resolved),
        sql.Identifier(alias),
    )


def _latest_run_id() -> str | None:
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        available = _jobs_columns(
            connection
        )

        if "application_decision_run_id" not in available:
            return None

        order_column = (
            "application_decision_at"
            if "application_decision_at" in available
            else "application_decision_run_id"
        )

        query = sql.SQL(
            """
            SELECT application_decision_run_id
            FROM jobs
            WHERE application_decision_run_id IS NOT NULL
            ORDER BY {} DESC
            LIMIT 1;
            """
        ).format(
            sql.Identifier(order_column)
        )

        with connection.cursor() as cursor:
            cursor.execute(
                query
            )
            row = cursor.fetchone()

        if not row:
            return None

        return row[0]

    finally:
        connection.close()


def _dashboard_select_columns(
    available: set[str],
):
    specs = [
        (("external_id",), "external_id"),
        (("title",), "title"),
        (("company",), "company"),
        (("location",), "location"),
        (("url",), "url"),

        # Historical InfraJob database versions may persist
        # technical score under different names.
        (
            (
                "technical_score",
                "score",
                "job_score",
            ),
            "technical_score",
        ),

        (
            (
                "opportunity_score",
                "opportunity",
            ),
            "opportunity_score",
        ),

        (("actionability",), "actionability"),
        (("vacancy_readiness",), "vacancy_readiness"),
        (("final_decision",), "final_decision"),

        (
            ("candidate_match_status",),
            "candidate_match_status",
        ),
        (
            ("candidate_match_score",),
            "candidate_match_score",
        ),
        (
            ("candidate_match_coverage",),
            "candidate_match_coverage",
        ),
        (
            ("candidate_match_skip_reason",),
            "candidate_match_skip_reason",
        ),

        (
            ("application_decision",),
            "application_decision",
        ),
        (
            ("application_decision_reasons",),
            "application_decision_reasons",
        ),
        (
            ("application_decision_blockers",),
            "application_decision_blockers",
        ),
        (
            ("application_decision_review_flags",),
            "application_decision_review_flags",
        ),
        (
            ("application_decision_version",),
            "application_decision_version",
        ),
        (
            ("application_decision_at",),
            "application_decision_at",
        ),
    ]

    return [
        _select_expr(
            available,
            candidates,
            alias,
        )
        for candidates, alias in specs
    ]


def _detail_select_columns(
    available: set[str],
):
    specs = [
        (("external_id",), "external_id"),
        (("title",), "title"),
        (("company",), "company"),
        (("location",), "location"),
        (("source",), "source"),
        (("url",), "url"),
        (("description",), "description"),

        (
            (
                "technical_score",
                "score",
                "job_score",
            ),
            "technical_score",
        ),

        (
            (
                "opportunity_score",
                "opportunity",
            ),
            "opportunity_score",
        ),

        (("actionability",), "actionability"),
        (
            ("actionability_reasons",),
            "actionability_reasons",
        ),

        (
            ("vacancy_readiness",),
            "vacancy_readiness",
        ),
        (
            ("readiness_reasons",),
            "readiness_reasons",
        ),
        (
            ("readiness_blockers",),
            "readiness_blockers",
        ),
        (
            ("readiness_review_flags",),
            "readiness_review_flags",
        ),

        (("requirements",), "requirements"),

        (
            ("live_validation_status",),
            "live_validation_status",
        ),
        (
            ("live_validation",),
            "live_validation",
        ),

        (
            ("final_decision",),
            "final_decision",
        ),
        (
            ("final_decision_reasons",),
            "final_decision_reasons",
        ),
        (
            ("final_decision_blockers",),
            "final_decision_blockers",
        ),
        (
            ("final_decision_review_flags",),
            "final_decision_review_flags",
        ),

        (
            ("candidate_match",),
            "candidate_match",
        ),
        (
            ("candidate_match_status",),
            "candidate_match_status",
        ),
        (
            ("candidate_match_score",),
            "candidate_match_score",
        ),
        (
            ("candidate_match_coverage",),
            "candidate_match_coverage",
        ),
        (
            ("candidate_match_skip_reason",),
            "candidate_match_skip_reason",
        ),

        (
            ("application_decision",),
            "application_decision",
        ),
        (
            ("application_decision_reasons",),
            "application_decision_reasons",
        ),
        (
            ("application_decision_blockers",),
            "application_decision_blockers",
        ),
        (
            ("application_decision_review_flags",),
            "application_decision_review_flags",
        ),
        (
            ("application_decision_inputs",),
            "application_decision_inputs",
        ),
        (
            ("application_decision_version",),
            "application_decision_version",
        ),
        (
            ("application_decision_at",),
            "application_decision_at",
        ),
    ]

    return [
        _select_expr(
            available,
            candidates,
            alias,
        )
        for candidates, alias in specs
    ]


def _fetch_dashboard_jobs(
    run_id: str,
    decision_filter: str | None = None,
) -> list[dict[str, Any]]:
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        available = _jobs_columns(
            connection
        )

        required = {
            "application_decision_run_id",
            "external_id",
        }

        missing_required = (
            required
            - available
        )

        if missing_required:
            raise RuntimeError(
                "Review UI cannot query the jobs table. "
                "Missing required columns: "
                + ", ".join(
                    sorted(
                        missing_required
                    )
                )
            )

        params: dict[str, Any] = {
            "run_id": run_id,
        }

        where_parts = [
            sql.SQL(
                "application_decision_run_id = %(run_id)s"
            )
        ]

        if (
            decision_filter
            and "application_decision" in available
        ):
            where_parts.append(
                sql.SQL(
                    "application_decision = %(decision_filter)s"
                )
            )

            params[
                "decision_filter"
            ] = decision_filter

        select_columns = (
            _dashboard_select_columns(
                available
            )
        )

        order_parts = []

        if "application_decision" in available:
            order_parts.append(
                sql.SQL(
                    """
                    CASE application_decision
                        WHEN 'apply_now' THEN 1
                        WHEN 'apply_with_tailored_cv' THEN 2
                        WHEN 'human_review' THEN 3
                        WHEN 'do_not_apply' THEN 4
                        ELSE 5
                    END
                    """
                )
            )

        opportunity_column = (
            _resolve_column(
                available,
                (
                    "opportunity_score",
                    "opportunity",
                ),
            )
        )

        technical_column = (
            _resolve_column(
                available,
                (
                    "technical_score",
                    "score",
                    "job_score",
                ),
            )
        )

        if opportunity_column:
            order_parts.append(
                sql.SQL(
                    "{} DESC NULLS LAST"
                ).format(
                    sql.Identifier(
                        opportunity_column
                    )
                )
            )

        if technical_column:
            order_parts.append(
                sql.SQL(
                    "{} DESC NULLS LAST"
                ).format(
                    sql.Identifier(
                        technical_column
                    )
                )
            )

        if "company" in available:
            order_parts.append(
                sql.SQL(
                    "company ASC"
                )
            )

        if "title" in available:
            order_parts.append(
                sql.SQL(
                    "title ASC"
                )
            )

        if not order_parts:
            order_parts.append(
                sql.SQL(
                    "external_id ASC"
                )
            )

        query = sql.SQL(
            """
            SELECT
                {select_columns}
            FROM jobs
            WHERE {where_clause}
            ORDER BY {order_clause};
            """
        ).format(
            select_columns=sql.SQL(
                ",\n"
            ).join(
                select_columns
            ),
            where_clause=sql.SQL(
                " AND "
            ).join(
                where_parts
            ),
            order_clause=sql.SQL(
                ",\n"
            ).join(
                order_parts
            ),
        )

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(
                query,
                params,
            )

            rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def _fetch_summary(
    run_id: str,
) -> dict[str, int]:
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        available = _jobs_columns(
            connection
        )

        summary = {
            "apply_now": 0,
            "apply_with_tailored_cv": 0,
            "human_review": 0,
            "do_not_apply": 0,
            "unclassified": 0,
            "total": 0,
        }

        if (
            "application_decision_run_id"
            not in available
        ):
            return summary

        if (
            "application_decision"
            not in available
        ):
            return summary

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(
                        application_decision,
                        'unclassified'
                    ) AS decision,
                    COUNT(*)
                FROM jobs
                WHERE application_decision_run_id = %s
                GROUP BY decision;
                """,
                (
                    run_id,
                ),
            )

            for decision, count in cursor.fetchall():
                if decision not in summary:
                    decision = "unclassified"

                summary[
                    decision
                ] += count

                summary[
                    "total"
                ] += count

        return summary

    finally:
        connection.close()


def _fetch_job(
    run_id: str,
    external_id: str,
) -> dict[str, Any] | None:
    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        available = _jobs_columns(
            connection
        )

        required = {
            "application_decision_run_id",
            "external_id",
        }

        missing_required = (
            required
            - available
        )

        if missing_required:
            raise RuntimeError(
                "Review UI cannot query job details. "
                "Missing required columns: "
                + ", ".join(
                    sorted(
                        missing_required
                    )
                )
            )

        select_columns = (
            _detail_select_columns(
                available
            )
        )

        query = sql.SQL(
            """
            SELECT
                {select_columns}
            FROM jobs
            WHERE application_decision_run_id = %s
              AND external_id = %s
            LIMIT 1;
            """
        ).format(
            select_columns=sql.SQL(
                ",\n"
            ).join(
                select_columns
            )
        )

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(
                query,
                (
                    run_id,
                    external_id,
                ),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return dict(
            row
        )

    finally:
        connection.close()


@app.get(
    "/",
    response_class=HTMLResponse,
)
def dashboard(
    request: Request,
    decision: str | None = Query(
        default=None
    ),
):
    allowed_filters = {
        None,
        "apply_now",
        "apply_with_tailored_cv",
        "human_review",
        "do_not_apply",
    }

    if decision not in allowed_filters:
        raise HTTPException(
            status_code=400,
            detail="Unsupported decision filter",
        )

    run_id = _latest_run_id()

    if run_id is None:
        return templates.TemplateResponse(
            request=request,
            name="review_dashboard.html",
            context={
                "run_id": None,
                "summary": {
                    "apply_now": 0,
                    "apply_with_tailored_cv": 0,
                    "human_review": 0,
                    "do_not_apply": 0,
                    "unclassified": 0,
                    "total": 0,
                },
                "jobs": [],
                "decision_filter": decision,
            },
        )

    jobs = _fetch_dashboard_jobs(
        run_id,
        decision_filter=decision,
    )

    summary = _fetch_summary(
        run_id
    )

    return templates.TemplateResponse(
        request=request,
        name="review_dashboard.html",
        context={
            "run_id": run_id,
            "summary": summary,
            "jobs": jobs,
            "decision_filter": decision,
        },
    )


@app.get(
    "/jobs/{external_id:path}",
    response_class=HTMLResponse,
)
def job_detail(
    request: Request,
    external_id: str,
):
    run_id = _latest_run_id()

    if run_id is None:
        raise HTTPException(
            status_code=404,
            detail="No application-decision run is available",
        )

    job = _fetch_job(
        run_id,
        external_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found in the latest run",
        )

    return templates.TemplateResponse(
        request=request,
        name="review_job.html",
        context={
            "run_id": run_id,
            "job": job,
        },
    )


@app.get(
    "/health",
)
def health():
    run_id = _latest_run_id()

    connection = get_connection()

    try:
        _assert_infrajob_database(
            connection
        )

        available = sorted(
            _jobs_columns(
                connection
            )
        )

        technical_column = (
            _resolve_column(
                set(available),
                (
                    "technical_score",
                    "score",
                    "job_score",
                ),
            )
        )

        opportunity_column = (
            _resolve_column(
                set(available),
                (
                    "opportunity_score",
                    "opportunity",
                ),
            )
        )

    finally:
        connection.close()

    return {
        "status": "ok",
        "database": EXPECTED_DATABASE,
        "latest_run_id": run_id,
        "ui_version": "m25.1.1",
        "resolved_columns": {
            "technical_score": technical_column,
            "opportunity_score": opportunity_column,
        },
    }
