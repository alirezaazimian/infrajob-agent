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


def normalize_text(value):
    if not value:
        return ""

    return " ".join(
        value.lower().split()
    )


def detect_work_authorization(job):
    title = normalize_text(
        job.get("title", "")
    )

    description = normalize_text(
        job.get("description", "")
    )

    text = f"{title} {description}"

    detected_signals = []

    for signal_type, patterns in (
        WORK_AUTHORIZATION_PATTERNS.items()
    ):
        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                detected_signals.append(
                    {
                        "type": signal_type,
                        "matched_text": match.group(0),
                    }
                )

                break

    blocked = bool(detected_signals)

    return {
        "work_authorization_blocked": blocked,
        "work_authorization_signals": detected_signals,
    }