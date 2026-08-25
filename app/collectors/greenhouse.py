import requests


BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def fetch_greenhouse_jobs(board_name):
    url = f"{BASE_URL}/{board_name}/jobs"

    response = requests.get(
        url,
        params={"content": "true"},
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("jobs", [])