TITLE_POSITIVE_KEYWORDS = {
    "linux": 35,
    "system administrator": 40,
    "systems administrator": 40,
    "sysadmin": 40,
    "infrastructure engineer": 35,
    "it operations engineer": 30,
    "devops engineer": 25,
    "site reliability engineer": 20,
    "cloud support engineer": 20,
    "service desk engineer": 10,
}


GENERIC_SYSTEM_ENGINEER_TITLES = {
    "systems engineer": 15,
    "system engineer": 15,
}


DESCRIPTION_POSITIVE_KEYWORDS = {
    "linux": 10,
    "ubuntu": 8,
    "rhel": 8,
    "red hat": 8,
    "vmware": 10,
    "vcenter": 8,
    "esxi": 8,
    "zabbix": 8,
    "docker": 8,
    "networking": 8,
    "veeam": 8,
    "bash": 6,
    "aws": 5,
    "monitoring": 8,
    "active directory": 5,
    "infrastructure": 5,
}


CORE_INFRASTRUCTURE_EVIDENCE = {
    "linux",
    "ubuntu",
    "rhel",
    "red hat",
    "vmware",
    "vcenter",
    "esxi",
    "zabbix",
    "networking",
    "veeam",
    "bash",
    "monitoring",
    "active directory",
    "infrastructure",
}


TITLE_NEGATIVE_KEYWORDS = {
    "graphic designer": -100,
    "marketing": -100,
    "sales": -100,
    "analyst": -35,
    "hardware developer": -50,
    "software developer": -40,
    "software engineer": -35,
    "data engineer": -40,
    "data scientist": -50,
    "machine learning": -50,
    "frontend": -100,
    "backend": -40,
    "golang": -50,

    # --------------------------------------------------
    # False-positive reduction
    # --------------------------------------------------

    "pega": -50,
    "java": -25,
    "programmer": -30,
    "security consultant": -50,
}


DESCRIPTION_NEGATIVE_KEYWORDS = {
    "graphic design": -20,
    "sales": -20,
    "marketing": -20,
    "machine learning": -15,
    "data science": -15,
    "react": -15,
    "frontend": -15,
}


def count_infrastructure_evidence(
    description,
):
    matched_evidence = []

    for keyword in (
        CORE_INFRASTRUCTURE_EVIDENCE
    ):
        if keyword in description:
            matched_evidence.append(
                keyword
            )

    return matched_evidence


def score_generic_system_engineer_title(
    title,
    description,
):
    infrastructure_evidence = (
        count_infrastructure_evidence(
            description
        )
    )

    # --------------------------------------------------
    # "System Engineer" is too broad by itself.
    #
    # We only treat it as infrastructure-relevant
    # when the job description contains at least
    # two strong infrastructure signals.
    # --------------------------------------------------

    if len(
        infrastructure_evidence
    ) < 2:
        return (
            0,
            None,
        )

    for keyword, points in (
        GENERIC_SYSTEM_ENGINEER_TITLES.items()
    ):
        if keyword in title:
            return (
                points,
                keyword,
            )

    return (
        0,
        None,
    )


def calculate_job_score(job):
    title = job.get(
        "title",
        "",
    ).lower()

    description = job.get(
        "description",
        "",
    ).lower()

    score = 0

    matched_skills = []

    # --------------------------------------------------
    # Strong title matches
    # --------------------------------------------------

    for keyword, points in (
        TITLE_POSITIVE_KEYWORDS.items()
    ):
        if keyword in title:
            score += points

            matched_skills.append(
                f"title:{keyword}"
            )

    # --------------------------------------------------
    # Generic System Engineer titles
    #
    # These titles are not sufficient by themselves.
    # Infrastructure evidence must exist in the
    # description before title points are awarded.
    # --------------------------------------------------

    (
        generic_title_score,
        generic_title_match,
    ) = score_generic_system_engineer_title(
        title,
        description,
    )

    if generic_title_score:
        score += (
            generic_title_score
        )

        matched_skills.append(
            (
                f"title:{generic_title_match}"
                ":validated"
            )
        )

    # --------------------------------------------------
    # Description positives
    # --------------------------------------------------

    for keyword, points in (
        DESCRIPTION_POSITIVE_KEYWORDS.items()
    ):
        if keyword in description:
            score += points

            matched_skills.append(
                keyword
            )

    # --------------------------------------------------
    # Title negatives
    # --------------------------------------------------

    for keyword, points in (
        TITLE_NEGATIVE_KEYWORDS.items()
    ):
        if keyword in title:
            score += points

    # --------------------------------------------------
    # Description negatives
    # --------------------------------------------------

    for keyword, points in (
        DESCRIPTION_NEGATIVE_KEYWORDS.items()
    ):
        if keyword in description:
            score += points

    # --------------------------------------------------
    # Clamp score
    # --------------------------------------------------

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    return (
        score,
        matched_skills,
    )