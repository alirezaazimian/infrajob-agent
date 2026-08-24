POSITIVE_KEYWORDS = {
    "linux": 25,
    "ubuntu": 10,
    "rhel": 10,
    "red hat": 10,
    "system administrator": 20,
    "systems administrator": 20,
    "sysadmin": 20,
    "infrastructure": 15,
    "vmware": 15,
    "vcenter": 10,
    "esxi": 10,
    "zabbix": 10,
    "docker": 10,
    "networking": 10,
    "veeam": 10,
    "bash": 5,
    "aws": 5,
    "monitoring": 10,
    "active directory": 5,
}


NEGATIVE_KEYWORDS = {
    "senior software engineer": -20,
    "software developer": -20,
    "golang": -15,
    "react": -15,
    "frontend": -20,
    "machine learning": -15,
    "data scientist": -20,
}


def calculate_job_score(job):
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()

    text = f"{title} {description}"

    score = 0
    matched_skills = []

    for keyword, points in POSITIVE_KEYWORDS.items():
        if keyword in text:
            score += points
            matched_skills.append(keyword)

    for keyword, points in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            score += points

    score = max(0, min(score, 100))

    return score, matched_skills