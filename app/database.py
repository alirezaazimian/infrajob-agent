import os

import psycopg2
from dotenv import load_dotenv


load_dotenv(".env")


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
                    external_id VARCHAR(255) UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    source VARCHAR(50),
                    score INTEGER,
                    status VARCHAR(30) NOT NULL DEFAULT 'new',
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        connection.commit()

    finally:
        connection.close()


def save_job(job, score):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs (
                    external_id,
                    title,
                    company,
                    location,
                    description,
                    url,
                    source,
                    score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

                ON CONFLICT (external_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    url = EXCLUDED.url,
                    source = EXCLUDED.source,
                    score = EXCLUDED.score,
                    last_seen = CURRENT_TIMESTAMP;
                """,
                (
                    job["external_id"],
                    job["title"],
                    job["company"],
                    job["location"],
                    job["description"],
                    job["url"],
                    job["source"],
                    score,
                ),
            )

        connection.commit()

    finally:
        connection.close()


VALID_STATUSES = {
    "new",
    "reviewing",
    "approved",
    "applied",
    "interview",
    "rejected",
    "archived",
}


def update_job_status(external_id, status):
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status}. "
            f"Allowed statuses: {', '.join(sorted(VALID_STATUSES))}"
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