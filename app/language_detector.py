import re


GERMAN_REQUIRED_PATTERNS = [
    r"\bfluent german required\b",
    r"\bgerman required\b",
    r"\bgerman language required\b",
    r"\bgerman is required\b",
    r"\bgerman mandatory\b",
    r"\bgerman is mandatory\b",
    r"\bmust speak german\b",
    r"\bmust be fluent in german\b",
    r"\bfluent in german\b",
    r"\bprofessional german required\b",
    r"\bnative german\b",

    r"\bgerman.*\bc1\b",
    r"\bgerman.*\bc2\b",
    r"\bgerman.*\bb2\b",

    r"\bdeutschkenntnisse erforderlich\b",
    r"\bsehr gute deutschkenntnisse\b",
    r"\bfließende deutschkenntnisse\b",
    r"\bfliessende deutschkenntnisse\b",
    r"\bverhandlungssichere deutschkenntnisse\b",
]


GERMAN_PREFERRED_PATTERNS = [
    r"\bgerman preferred\b",
    r"\bgerman is preferred\b",
    r"\bgerman desirable\b",
    r"\bgerman is desirable\b",
    r"\bgerman is a plus\b",
    r"\bgerman would be a plus\b",
    r"\bgerman nice to have\b",
    r"\bbasic german preferred\b",

    r"\bdeutschkenntnisse von vorteil\b",
    r"\bdeutschkenntnisse wünschenswert\b",
    r"\bdeutschkenntnisse wuenschenswert\b",
]


ENGLISH_REQUIRED_PATTERNS = [
    r"\bfluent english required\b",
    r"\benglish required\b",
    r"\benglish language required\b",
    r"\benglish is required\b",
    r"\bmust speak english\b",
    r"\bmust be fluent in english\b",
    r"\bfluent in english\b",
    r"\bprofessional english required\b",

    r"\benglish.*\bc1\b",
    r"\benglish.*\bc2\b",
    r"\benglish.*\bb2\b",
]


OTHER_LANGUAGE_REQUIRED_PATTERNS = {
    "french": [
        r"\bfrench required\b",
        r"\bfrench is required\b",
        r"\bmust speak french\b",
        r"\bfluent french\b",
        r"\bfluent in french\b",
    ],

    "dutch": [
        r"\bdutch required\b",
        r"\bdutch is required\b",
        r"\bmust speak dutch\b",
        r"\bfluent dutch\b",
        r"\bfluent in dutch\b",
    ],

    "danish": [
        r"\bdanish required\b",
        r"\bdanish is required\b",
        r"\bmust speak danish\b",
        r"\bfluent danish\b",
        r"\bfluent in danish\b",
    ],

    "finnish": [
        r"\bfinnish required\b",
        r"\bfinnish is required\b",
        r"\bmust speak finnish\b",
        r"\bfluent finnish\b",
        r"\bfluent in finnish\b",
    ],
}


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


def find_matches(text, patterns):
    matches = []

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            matches.append(
                match.group(0)
            )

    return matches


def detect_language_requirements(job):
    text = get_job_text(job)

    german_required_matches = find_matches(
        text,
        GERMAN_REQUIRED_PATTERNS,
    )

    german_preferred_matches = find_matches(
        text,
        GERMAN_PREFERRED_PATTERNS,
    )

    english_required_matches = find_matches(
        text,
        ENGLISH_REQUIRED_PATTERNS,
    )

    other_required_languages = []

    for language, patterns in (
        OTHER_LANGUAGE_REQUIRED_PATTERNS.items()
    ):
        matches = find_matches(
            text,
            patterns,
        )

        if matches:
            other_required_languages.append(
                {
                    "language": language,
                    "matches": matches,
                }
            )

    signals = []

    if german_required_matches:
        signals.append(
            {
                "type": "german_required",
                "matches": german_required_matches,
            }
        )

    if german_preferred_matches:
        signals.append(
            {
                "type": "german_preferred",
                "matches": german_preferred_matches,
            }
        )

    if english_required_matches:
        signals.append(
            {
                "type": "english_required",
                "matches": english_required_matches,
            }
        )

    for language_result in other_required_languages:
        signals.append(
            {
                "type": (
                    f"{language_result['language']}"
                    "_required"
                ),
                "matches": language_result["matches"],
            }
        )

    if german_required_matches:
        classification = "german_required"

    elif other_required_languages:
        classification = "other_language_required"

    elif german_preferred_matches:
        classification = "german_preferred"

    elif english_required_matches:
        classification = "english_required"

    else:
        classification = "unknown"

    return {
        "language_requirement": classification,
        "german_required": bool(
            german_required_matches
        ),
        "german_preferred": bool(
            german_preferred_matches
        ),
        "english_required": bool(
            english_required_matches
        ),
        "other_required_languages": [
            item["language"]
            for item in other_required_languages
        ],
        "language_signals": signals,
    }