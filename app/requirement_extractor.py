from __future__ import annotations

import html
import re
from typing import Any


# ==========================================================
# Requirement Extractor
#
# Extracts explicit vacancy requirements from normalized
# job descriptions without using an LLM.
#
# This layer is evidence-oriented. It does not decide whether
# the candidate satisfies the requirement. Candidate matching
# belongs to a later stage.
# ==========================================================


DEGREE_PATTERNS = {
    "bachelor": (
        r"\bbachelor(?:'s)?\b",
        r"\bb\.?sc\.?\b",
        r"\bundergraduate degree\b",
    ),
    "master": (
        r"\bmaster(?:'s)?\b",
        r"\bm\.?sc\.?\b",
        r"\bgraduate degree\b",
    ),
    "phd": (
        r"\bph\.?d\.?\b",
        r"\bdoctorate\b",
        r"\bdoctoral degree\b",
    ),
}


LANGUAGE_PATTERNS = {
    "english": (
        r"\benglish\b",
    ),
    "german": (
        r"\bgerman\b",
        r"\bdeutsch\b",
    ),
    "danish": (
        r"\bdanish\b",
        r"\bdansk\b",
    ),
    "dutch": (
        r"\bdutch\b",
        r"\bnederlands\b",
    ),
    "finnish": (
        r"\bfinnish\b",
        r"\bsuomi\b",
    ),
    "swedish": (
        r"\bswedish\b",
        r"\bsvenska\b",
    ),
    "norwegian": (
        r"\bnorwegian\b",
        r"\bnorsk\b",
    ),
    "french": (
        r"\bfrench\b",
        r"\bfrançais\b",
        r"\bfrancais\b",
    ),
}


TECH_SKILLS = (
    "linux",
    "ubuntu",
    "debian",
    "red hat",
    "rhel",
    "centos",
    "bash",
    "python",
    "powershell",
    "ansible",
    "terraform",
    "docker",
    "kubernetes",
    "vmware",
    "esxi",
    "vcenter",
    "veeam",
    "zabbix",
    "prometheus",
    "grafana",
    "aws",
    "azure",
    "gcp",
    "active directory",
    "windows server",
    "networking",
    "tcp/ip",
    "dns",
    "dhcp",
    "firewall",
    "vpn",
    "postgresql",
    "mysql",
    "git",
    "ci/cd",
    "jenkins",
)


REQUIRED_MARKERS = (
    "required",
    "requirement",
    "requirements",
    "must have",
    "must-have",
    "must be",
    "you have",
    "you bring",
    "we expect",
    "minimum",
    "at least",
    "essential",
    "mandatory",
)


PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "desirable",
    "bonus",
    "advantage",
    "plus",
)


REMOTE_PATTERNS = (
    r"\b100%\s+remote\b",
    r"\bfully remote\b",
    r"\bremote[- ]first\b",
    r"\bwork remotely\b",
)


HYBRID_PATTERNS = (
    r"\bhybrid\b",
    r"\bhybrid work\b",
    r"\bhybrid working\b",
)


ONSITE_PATTERNS = (
    r"\bon[- ]site\b",
    r"\bonsite\b",
    r"\bin[- ]office\b",
    r"\bwork from (?:the )?office\b",
)


WORK_AUTH_BLOCK_PATTERNS = (
    r"\bmust (?:already )?have (?:the )?(?:right|authorization) to work\b",
    r"\bmust be (?:legally )?authorized to work\b",
    r"\bno (?:visa )?sponsorship\b",
    r"\bwithout (?:visa )?sponsorship\b",
    r"\bwe (?:do not|don't) sponsor\b",
    r"\bsponsorship (?:is )?not available\b",
)


SPONSORSHIP_POSITIVE_PATTERNS = (
    r"\bvisa sponsorship\b",
    r"\bwork permit sponsorship\b",
    r"\bsponsorship available\b",
    r"\bwe sponsor\b",
    r"\bimmigration support\b",
)


RELOCATION_PATTERNS = (
    r"\brelocation assistance\b",
    r"\brelocation support\b",
    r"\brelocation package\b",
    r"\brelocation provided\b",
)


EXPERIENCE_PATTERNS = (
    re.compile(
        r"\b(?:minimum|min\.?|at least)\s+"
        r"(?P<years>\d{1,2})\+?\s+years?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<years>\d{1,2})\+\s+years?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<years>\d{1,2})\s*(?:-|–|to)\s*"
        r"(?P<max_years>\d{1,2})\s+years?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<years>\d{1,2})\s+years?\s+"
        r"(?:of\s+)?(?:professional\s+)?experience\b",
        re.IGNORECASE,
    ),
)


def _strip_html(value: Any) -> str:
    if not value:
        return ""

    text = html.unescape(str(value))

    text = re.sub(
        r"<\s*br\s*/?\s*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</\s*(?:p|li|div|h[1-6])\s*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n",
        text,
    )

    return text.strip()


def _sentences(text: str) -> list[str]:
    if not text:
        return []

    pieces = re.split(
        r"(?<=[.!?])\s+|\n+|(?:\s*[•●▪]\s*)",
        text,
    )

    return [
        piece.strip(" \t\r\n-–—•")
        for piece in pieces
        if piece.strip(" \t\r\n-–—•")
    ]


def _contains_any(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _unique(items: list[Any]) -> list[Any]:
    output = []

    for item in items:
        if item not in output:
            output.append(item)

    return output


def _find_experience(
    sentences: list[str],
) -> dict:
    evidence = []
    years = []

    for sentence in sentences:
        lowered = sentence.lower()

        if "year" not in lowered:
            continue

        if not any(
            token in lowered
            for token in (
                "experience",
                "experienced",
                "professional",
                "administrator",
                "engineer",
                "linux",
                "infrastructure",
                "system",
                "network",
                "cloud",
                "devops",
                "platform",
                "sre",
            )
        ):
            continue

        for pattern in EXPERIENCE_PATTERNS:
            match = pattern.search(sentence)

            if not match:
                continue

            minimum = int(
                match.group("years")
            )

            maximum = (
                int(match.group("max_years"))
                if match.groupdict().get(
                    "max_years"
                )
                else None
            )

            years.append(minimum)

            evidence.append(
                {
                    "minimum_years": minimum,
                    "maximum_years": maximum,
                    "evidence": sentence,
                }
            )

            break

    return {
        "explicit": bool(evidence),
        "minimum_years": (
            max(years)
            if years
            else None
        ),
        "evidence": evidence,
    }


def _find_education(
    sentences: list[str],
) -> dict:
    levels = []
    evidence = []
    preferred_only = True

    for sentence in sentences:
        lowered = sentence.lower()

        matched_levels = []

        for level, patterns in (
            DEGREE_PATTERNS.items()
        ):
            if _contains_any(
                lowered,
                patterns,
            ):
                matched_levels.append(
                    level
                )

        if not matched_levels:
            continue

        is_preferred = any(
            marker in lowered
            for marker in PREFERRED_MARKERS
        )

        if not is_preferred:
            preferred_only = False

        levels.extend(
            matched_levels
        )

        evidence.append(
            sentence
        )

    return {
        "explicit": bool(evidence),
        "levels": _unique(levels),
        "required": (
            bool(evidence)
            and not preferred_only
        ),
        "preferred_only": (
            bool(evidence)
            and preferred_only
        ),
        "evidence": evidence,
    }


def _find_languages(
    sentences: list[str],
) -> dict:
    required = []
    preferred = []
    mentioned = []
    evidence = []

    for sentence in sentences:
        lowered = sentence.lower()

        languages = []

        for language, patterns in (
            LANGUAGE_PATTERNS.items()
        ):
            if _contains_any(
                lowered,
                patterns,
            ):
                languages.append(
                    language
                )

        if not languages:
            continue

        mentioned.extend(
            languages
        )

        preferred_signal = any(
            marker in lowered
            for marker in PREFERRED_MARKERS
        )

        required_signal = any(
            marker in lowered
            for marker in REQUIRED_MARKERS
        ) or any(
            phrase in lowered
            for phrase in (
                "fluent",
                "fluency",
                "proficient",
                "professional proficiency",
                "business level",
                "working proficiency",
                "written and spoken",
                "spoken and written",
            )
        )

        if preferred_signal:
            preferred.extend(
                languages
            )

        elif required_signal:
            required.extend(
                languages
            )

        evidence.append(
            sentence
        )

    return {
        "mentioned": _unique(
            mentioned
        ),
        "required": _unique(
            required
        ),
        "preferred": _unique(
            preferred
        ),
        "evidence": evidence,
    }


def _find_work_authorization(
    sentences: list[str],
) -> dict:
    blocker_evidence = []
    sponsorship_evidence = []
    relocation_evidence = []

    for sentence in sentences:
        if _contains_any(
            sentence,
            WORK_AUTH_BLOCK_PATTERNS,
        ):
            blocker_evidence.append(
                sentence
            )

        if _contains_any(
            sentence,
            SPONSORSHIP_POSITIVE_PATTERNS,
        ):
            sponsorship_evidence.append(
                sentence
            )

        if _contains_any(
            sentence,
            RELOCATION_PATTERNS,
        ):
            relocation_evidence.append(
                sentence
            )

    return {
        "explicit_local_authorization_required": (
            bool(blocker_evidence)
        ),
        "sponsorship_mentioned": (
            bool(sponsorship_evidence)
        ),
        "relocation_mentioned": (
            bool(relocation_evidence)
        ),
        "blocker_evidence": blocker_evidence,
        "sponsorship_evidence": (
            sponsorship_evidence
        ),
        "relocation_evidence": (
            relocation_evidence
        ),
    }


def _find_location_mode(
    text: str,
) -> dict:
    remote = _contains_any(
        text,
        REMOTE_PATTERNS,
    )

    hybrid = _contains_any(
        text,
        HYBRID_PATTERNS,
    )

    onsite = _contains_any(
        text,
        ONSITE_PATTERNS,
    )

    if remote and not hybrid and not onsite:
        mode = "remote"

    elif hybrid:
        mode = "hybrid"

    elif onsite:
        mode = "onsite"

    else:
        mode = "unknown"

    return {
        "mode": mode,
        "remote_signal": remote,
        "hybrid_signal": hybrid,
        "onsite_signal": onsite,
    }


def _find_skills(
    sentences: list[str],
) -> dict:
    required = []
    preferred = []
    mentioned = []
    evidence = []

    for sentence in sentences:
        lowered = sentence.lower()

        matched = [
            skill
            for skill in TECH_SKILLS
            if skill in lowered
        ]

        if not matched:
            continue

        mentioned.extend(
            matched
        )

        preferred_signal = any(
            marker in lowered
            for marker in PREFERRED_MARKERS
        )

        required_signal = any(
            marker in lowered
            for marker in REQUIRED_MARKERS
        )

        if preferred_signal:
            preferred.extend(
                matched
            )

        elif required_signal:
            required.extend(
                matched
            )

        evidence.append(
            sentence
        )

    return {
        "mentioned": _unique(
            mentioned
        ),
        "required": _unique(
            required
        ),
        "preferred": _unique(
            preferred
        ),
        "evidence": evidence,
    }


def extract_requirements(
    job: dict,
) -> dict:
    raw_description = job.get(
        "description",
        "",
    )

    text = _strip_html(
        raw_description
    )

    sentences = _sentences(
        text
    )

    experience = _find_experience(
        sentences
    )

    education = _find_education(
        sentences
    )

    languages = _find_languages(
        sentences
    )

    work_authorization = (
        _find_work_authorization(
            sentences
        )
    )

    location = _find_location_mode(
        text
    )

    skills = _find_skills(
        sentences
    )

    has_description = bool(
        text.strip()
    )

    explicit_requirement_count = sum(
        (
            1
            if experience["explicit"]
            else 0,

            1
            if education["explicit"]
            else 0,

            len(
                languages["required"]
            ),

            1
            if work_authorization[
                "explicit_local_authorization_required"
            ]
            else 0,

            len(
                skills["required"]
            ),
        )
    )

    return {
        "has_description": (
            has_description
        ),
        "description_length": len(
            text
        ),
        "experience": experience,
        "education": education,
        "languages": languages,
        "work_authorization": (
            work_authorization
        ),
        "location": location,
        "skills": skills,
        "explicit_requirement_count": (
            explicit_requirement_count
        ),
    }
