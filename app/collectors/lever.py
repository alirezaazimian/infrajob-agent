import requests


GLOBAL_BASE_URL = "https://api.lever.co/v0/postings"
EU_BASE_URL = "https://api.eu.lever.co/v0/postings"


def fetch_lever_jobs(site, region="global"):
    if region == "eu":
        base_url = EU_BASE_URL
    else:
        base_url = GLOBAL_BASE_URL

    url = f"{base_url}/{site}"

    response = requests.get(
        url,
        params={"mode": "json"},
        timeout=15,
    )

    response.raise_for_status()

    return response.json()