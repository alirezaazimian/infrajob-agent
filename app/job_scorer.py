TITLE_POSITIVE_KEYWORDS = {
    "linux": 35,
    "system administrator": 40,
    "systems administrator": 40,
    "sysadmin": 40,
    "infrastructure engineer": 35,
    "systems engineer": 30,
    "system engineer": 30,
    "it operations engineer": 30,
    "devops engineer": 25,
    "site reliability engineer": 20,
    "cloud support engineer": 20,
    "service desk engineer": 10,
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


def calculate_job_score(job):
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()

    score = 0
    matched_skills = []

    for keyword, points in TITLE_POSITIVE_KEYWORDS.items():
        if keyword in title:
            score += points
            matched_skills.append(f"title:{keyword}")

    for keyword, points in DESCRIPTION_POSITIVE_KEYWORDS.items():
        if keyword in description:
            score += points
            matched_skills.append(keyword)

    for keyword, points in TITLE_NEGATIVE_KEYWORDS.items():
        if keyword in title:
            score += points

    for keyword, points in DESCRIPTION_NEGATIVE_KEYWORDS.items():
        if keyword in description:
            score += points

    score = max(0, min(score, 100))

    return score, matched_skills