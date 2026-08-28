import time

import requests


BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"


def fetch_ashby_jobs(
    board_name,
    include_compensation=False,
    max_attempts=3,
):
    url = f"{BASE_URL}/{board_name}"

    params = {}

    if include_compensation:
        params["includeCompensation"] = "true"

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=(5, 20),
            )

            # Ashby/Cloudflare occasionally returns a temporary
            # forbidden response from this network path.
            if response.status_code in {
                403,
                429,
                500,
                502,
                503,
                504,
            }:
                response.raise_for_status()

            response.raise_for_status()

            data = response.json()

            return data.get("jobs", [])

        except (
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as error:
            last_error = error

            if attempt == max_attempts:
                raise

            time.sleep(attempt * 2)

    raise last_error