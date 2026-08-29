TITLE_POSITIVE_KEYWORDS = {
    "linux": 35,

    "system administrator": 40,
    "systems administrator": 40,
    "sysadmin": 40,
    "server administrator": 35,

    "infrastructure engineer": 35,

    "it operations engineer": 30,

    "data center engineer": 30,
    "datacenter engineer": 30,
    "data center operations engineer": 30,
    "datacenter operations engineer": 30,

    "virtualization engineer": 30,
    "vmware engineer": 30,

    "cloud operations engineer": 25,
    "platform operations engineer": 25,

    "network & security engineer": 30,
    "network and security engineer": 30,
    "network security engineer": 30,

    "infrastructure and cloud security engineer": 30,
    "cloud infrastructure security engineer": 30,

    "devops engineer": 25,
    "site reliability engineer": 20,

    "cloud support engineer": 20,
    "service desk engineer": 10,
}


CONDITIONAL_TITLE_KEYWORDS = {
    "systems engineer": 15,
    "system engineer": 15,
    "platform engineer": 15,
    "sre engineer": 15,
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
    "kubernetes": 8,

    "networking": 8,

    "veeam": 8,

    "bash": 6,

    "aws": 5,
    "azure": 5,
    "gcp": 5,

    "monitoring": 8,

    "active directory": 5,

    "infrastructure": 5,
}


INFRASTRUCTURE_EVIDENCE = {
    "linux",
    "ubuntu",
    "rhel",
    "red hat",

    "server",
    "servers",

    "vmware",
    "vcenter",
    "esxi",
    "virtualization",

    "zabbix",
    "monitoring",

    "networking",
    "network",

    "firewall",
    "vpn",

    "veeam",

    "bash",

    "active directory",

    "infrastructure",

    "aws",
    "azure",
    "gcp",

    "docker",
    "kubernetes",

    "data center",
    "datacenter",
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
        INFRASTRUCTURE_EVIDENCE
    ):
        if keyword in description:
            matched_evidence.append(
                keyword
            )

    return matched_evidence


def score_conditional_title(
    title,
    description,
):
    infrastructure_evidence = (
        count_infrastructure_evidence(
            description
        )
    )

    # --------------------------------------------------
    # Generic titles such as:
    #
    # System Engineer
    # Platform Engineer
    # SRE Engineer
    #
    # are only useful when the description contains
    # real infrastructure evidence.
    # --------------------------------------------------

    if len(
        infrastructure_evidence
    ) < 2:
        return (
            0,
            None,
        )

    for keyword, points in (
        CONDITIONAL_TITLE_KEYWORDS.items()
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
    # Strong / explicit title matches
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
    # Conditional / generic titles
    # --------------------------------------------------

    (
        conditional_score,
        conditional_match,
    ) = score_conditional_title(
        title,
        description,
    )

    if conditional_score:
        score += (
            conditional_score
        )

        matched_skills.append(
            (
                f"title:{conditional_match}"
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
    # Clamp
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