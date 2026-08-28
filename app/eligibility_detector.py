import re


WORK_AUTHORIZATION_PATTERNS = {
    "no_sponsorship": [
        r"\bno visa sponsorship\b",
        r"\bvisa sponsorship is not available\b",
        r"\bwe do not sponsor visas\b",
        r"\bwe cannot sponsor visas\b",
        r"\bunable to sponsor\b",
        r"\bwithout sponsorship\b",
        r"\bwill not sponsor\b",
    ],

    "existing_work_authorization_required": [
        r"\bmust be authorized to work\b",
        r"\bauthorized to work in\b",
        r"\bright to work in\b",
        r"\bexisting work authorization\b",
        r"\bvalid work permit required\b",
        r"\bmust already have.*work authorization\b",
    ],

    "citizenship_required": [
        r"\bus citizens only\b",
        r"\bus citizenship required\b",
        r"\bu\.s\. citizenship required\b",
        r"\bcitizenship is required\b",
    ],

    "eu_authorization_required": [
        r"\beu work authorization required\b",
        r"\bright to work in the eu\b",
        r"\bauthorized to work in the eu\b",
        r"\beu citizens only\b",
        r"\beu citizenship required\b",
    ],
}


SPONSORSHIP_PATTERNS = [
    r"\bvisa sponsorship available\b",
    r"\bvisa sponsorship provided\b",
    r"\bwe provide visa sponsorship\b",
    r"\bwe offer visa sponsorship\b",
    r"\bvisa support available\b",
    r"\bwork permit support\b",
    r"\bwork visa support\b",
    r"\bsponsorship available\b",
]


RELOCATION_PATTERNS = [
    r"\brelocation assistance\b",
    r"\brelocation support\b",
    r"\brelocation package\b",
    r"\brelocation provided\b",
    r"\bwe support relocation\b",
    r"\bwe offer relocation\b",
]


INTERNATIONAL_HIRING_PATTERNS = [
    r"\binternational applicants welcome\b",
    r"\binternational candidates welcome\b",

    r"\bwelcome international applicants\b",
    r"\bwelcome international candidates\b",

    r"\bwe welcome international applicants\b",
    r"\bwe welcome international candidates\b",

    r"\bglobal applicants welcome\b",
    r"\bglobal candidates welcome\b",

    r"\bwelcome global applicants\b",
    r"\bwelcome global candidates\b",

    r"\bcandidates worldwide\b",
    r"\bapplicants worldwide\b",

    r"\bworldwide applicants\b",
    r"\bworldwide candidates\b",

    r"\bopen to international applicants\b",
    r"\bopen to international candidates\b",

    r"\bapplications from abroad\b",
]


def normalize_text(value):
    if not value:
        return ""

    return " ".join(
        value.lower().split()
    )


def get_job_text(job):
    title = normalize_text(
        job.get("title", "")
    )

    description = normalize_text(
        job.get("description", "")
    )

    return f"{title} {description}"


def find_pattern_match(text, patterns):
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(0)

    return None


def detect_work_authorization(job):
    text = get_job_text(job)

    detected_signals = []

    for signal_type, patterns in (
        WORK_AUTHORIZATION_PATTERNS.items()
    ):
        matched_text = find_pattern_match(
            text,
            patterns,
        )

        if matched_text:
            detected_signals.append(
                {
                    "type": signal_type,
                    "matched_text": matched_text,
                }
            )

    blocked = bool(detected_signals)

    return {
        "work_authorization_blocked": blocked,
        "work_authorization_signals": detected_signals,
    }


def detect_positive_eligibility_signals(job):
    text = get_job_text(job)

    sponsorship_match = find_pattern_match(
        text,
        SPONSORSHIP_PATTERNS,
    )

    relocation_match = find_pattern_match(
        text,
        RELOCATION_PATTERNS,
    )

    international_match = find_pattern_match(
        text,
        INTERNATIONAL_HIRING_PATTERNS,
    )

    signals = []

    if sponsorship_match:
        signals.append(
            {
                "type": "sponsorship",
                "matched_text": sponsorship_match,
            }
        )

    if relocation_match:
        signals.append(
            {
                "type": "relocation",
                "matched_text": relocation_match,
            }
        )

    if international_match:
        signals.append(
            {
                "type": "international_hiring",
                "matched_text": international_match,
            }
        )

    return {
        "sponsorship_evidence": bool(
            sponsorship_match
        ),
        "relocation_evidence": bool(
            relocation_match
        ),
        "international_hiring_evidence": bool(
            international_match
        ),
        "positive_eligibility_signals": signals,
    }