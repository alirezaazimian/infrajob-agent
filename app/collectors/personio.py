import xml.etree.ElementTree as ET

import requests


BASE_URL = "https://{account}.jobs.personio.de/xml"


def fetch_personio_jobs(account, language="en"):
    url = BASE_URL.format(account=account)

    response = requests.get(
        url,
        params={"language": language},
        timeout=10,
    )

    response.raise_for_status()

    root = ET.fromstring(response.content)

    jobs = []

    for position in root.findall("position"):
        descriptions = []

        job_descriptions = position.find("jobDescriptions")

        if job_descriptions is not None:
            for block in job_descriptions.findall(
                "jobDescription"
            ):
                section_name = (
                    block.findtext("name") or ""
                ).strip()

                section_value = (
                    block.findtext("value") or ""
                ).strip()

                if section_value:
                    descriptions.append(
                        f"{section_name}\n{section_value}".strip()
                    )

        job_id = (
            position.findtext("id")
            or position.get("id")
            or ""
        )

        jobs.append(
            {
                "id": str(job_id),
                "name": (
                    position.findtext("name") or ""
                ).strip(),
                "subcompany": (
                    position.findtext("subcompany") or ""
                ).strip(),
                "office": (
                    position.findtext("office") or ""
                ).strip(),
                "department": (
                    position.findtext("department") or ""
                ).strip(),
                "employment_type": (
                    position.findtext("employmentType") or ""
                ).strip(),
                "seniority": (
                    position.findtext("seniority") or ""
                ).strip(),
                "schedule": (
                    position.findtext("schedule") or ""
                ).strip(),
                "description": "\n\n".join(descriptions),
            }
        )

    return jobs