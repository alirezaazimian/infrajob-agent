import requests


API_URL = "https://remotive.com/api/remote-jobs"


def fetch_jobs(search=None):
    params = {}

    if search:
        params["search"] = search

    response = requests.get(
        API_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("jobs", [])