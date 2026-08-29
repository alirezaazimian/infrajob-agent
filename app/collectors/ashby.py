import time

import requests


BASE_URL = (
    "https://api.ashbyhq.com/"
    "posting-api/job-board"
)


RETRYABLE_STATUS_CODES = {
    403,
    408,
    429,
    500,
    502,
    503,
    504,
}


def fetch_ashby_jobs(
    board_name,
    include_compensation=False,
    max_attempts=3,
):
    url = (
        f"{BASE_URL}/{board_name}"
    )

    params = {}

    if include_compensation:
        params[
            "includeCompensation"
        ] = "true"

    last_error = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=(5, 20),
            )

            if (
                response.status_code
                in RETRYABLE_STATUS_CODES
            ):
                response.raise_for_status()

            response.raise_for_status()

            data = response.json()

            jobs = data.get(
                "jobs",
                [],
            )

            if not isinstance(
                jobs,
                list,
            ):
                raise ValueError(
                    "Ashby jobs response "
                    "is not a list."
                )

            return jobs

        except (
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as error:
            last_error = error

            if (
                attempt
                == max_attempts
            ):
                raise

            time.sleep(
                attempt * 2
            )

    if last_error:
        raise last_error

    return []