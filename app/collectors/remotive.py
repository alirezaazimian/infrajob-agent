import requests


API_URL = "https://remotive.com/api/remote-jobs"


def fetch_jobs(limit=5):
    response = requests.get(
        API_URL,
        params={"limit": limit},
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return data["jobs"]