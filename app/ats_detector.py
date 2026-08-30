from urllib.parse import (
    urlparse,
)


SUPPORTED_ATS = {
    "lever",
    "greenhouse",
    "personio",
    "ashby",
}


PERSONIO_DOMAINS = {
    "jobs.personio.de",
    "jobs.personio.com",
    "jobs.personio.at",
    "jobs.personio.es",
    "jobs.personio.fr",
    "jobs.personio.it",
    "jobs.personio.nl",
}


def normalize_url(
    url,
):
    value = (
        url
        or ""
    ).strip()

    if not value:
        return ""

    if "://" not in value:
        value = (
            "https://"
            + value
        )

    return value


def split_path(
    path,
):
    return [
        part
        for part in path.split("/")
        if part
    ]


def detect_lever(
    hostname,
    path_parts,
):
    # --------------------------------------------------
    # Public job board
    #
    # jobs.lever.co/company
    # jobs.lever.co/company/job-id
    # --------------------------------------------------

    if hostname == "jobs.lever.co":
        if not path_parts:
            return None

        return {
            "ats": "lever",
            "identifier": path_parts[0],
            "confidence": "high",
        }

    # --------------------------------------------------
    # Lever API
    #
    # api.lever.co/v0/postings/company
    # --------------------------------------------------

    if hostname == "api.lever.co":
        try:
            postings_index = (
                path_parts.index(
                    "postings"
                )
            )
        except ValueError:
            return None

        identifier_index = (
            postings_index + 1
        )

        if identifier_index >= len(
            path_parts
        ):
            return None

        return {
            "ats": "lever",
            "identifier": (
                path_parts[
                    identifier_index
                ]
            ),
            "confidence": "high",
        }

    return None


def detect_greenhouse(
    hostname,
    path_parts,
):
    # --------------------------------------------------
    # Public Greenhouse boards
    # --------------------------------------------------

    public_hosts = {
        "boards.greenhouse.io",
        "job-boards.greenhouse.io",
    }

    if hostname in public_hosts:
        if not path_parts:
            return None

        return {
            "ats": "greenhouse",
            "identifier": path_parts[0],
            "confidence": "high",
        }

    # --------------------------------------------------
    # Greenhouse API
    #
    # boards-api.greenhouse.io/
    # v1/boards/company/jobs
    # --------------------------------------------------

    if hostname == (
        "boards-api.greenhouse.io"
    ):
        try:
            boards_index = (
                path_parts.index(
                    "boards"
                )
            )
        except ValueError:
            return None

        identifier_index = (
            boards_index + 1
        )

        if identifier_index >= len(
            path_parts
        ):
            return None

        return {
            "ats": "greenhouse",
            "identifier": (
                path_parts[
                    identifier_index
                ]
            ),
            "confidence": "high",
        }

    return None


def detect_personio(
    hostname,
    path_parts,
):
    # --------------------------------------------------
    # Common Personio hosted career sites:
    #
    # company.jobs.personio.de
    # company.jobs.personio.com
    # --------------------------------------------------

    for domain in (
        PERSONIO_DOMAINS
    ):
        suffix = (
            "."
            + domain
        )

        if hostname.endswith(
            suffix
        ):
            identifier = hostname[
                :-len(
                    suffix
                )
            ]

            if not identifier:
                return None

            return {
                "ats": "personio",
                "identifier": identifier,
                "confidence": "high",
            }

    return None


def detect_ashby(
    hostname,
    path_parts,
):
    # --------------------------------------------------
    # Public Ashby board:
    #
    # jobs.ashbyhq.com/company
    # jobs.ashbyhq.com/company/job-id
    # --------------------------------------------------

    if hostname == (
        "jobs.ashbyhq.com"
    ):
        if not path_parts:
            return None

        return {
            "ats": "ashby",
            "identifier": path_parts[0],
            "confidence": "high",
        }

    # --------------------------------------------------
    # Ashby public posting API:
    #
    # api.ashbyhq.com/
    # posting-api/job-board/company
    # --------------------------------------------------

    if hostname == (
        "api.ashbyhq.com"
    ):
        for index, part in enumerate(
            path_parts
        ):
            if part != "job-board":
                continue

            identifier_index = (
                index + 1
            )

            if identifier_index >= len(
                path_parts
            ):
                return None

            return {
                "ats": "ashby",
                "identifier": (
                    path_parts[
                        identifier_index
                    ]
                ),
                "confidence": "high",
            }

    return None


def detect_ats_source(
    url,
):
    normalized_url = (
        normalize_url(
            url
        )
    )

    if not normalized_url:
        return {
            "ats": "unknown",
            "identifier": None,
            "confidence": "none",
            "url": "",
        }

    parsed = urlparse(
        normalized_url
    )

    hostname = (
        parsed.hostname
        or ""
    ).lower()

    path_parts = split_path(
        parsed.path
    )

    detectors = [
        detect_lever,
        detect_greenhouse,
        detect_personio,
        detect_ashby,
    ]

    for detector in detectors:
        result = detector(
            hostname,
            path_parts,
        )

        if result:
            result[
                "url"
            ] = normalized_url

            return result

    return {
        "ats": "unknown",
        "identifier": None,
        "confidence": "none",
        "url": normalized_url,
    }


def detect_ats(
    url,
):
    return detect_ats_source(
        url
    )[
        "ats"
    ]


def extract_identifier(
    url,
):
    return detect_ats_source(
        url
    )[
        "identifier"
    ]