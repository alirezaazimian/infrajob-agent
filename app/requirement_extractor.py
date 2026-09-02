from __future__ import annotations

import html
import re
from typing import Any


# ==========================================================
# Requirement Extractor
#
# M21.2.2 hardened rule-based vacancy requirement extraction.
#
# Important:
# - This module extracts vacancy requirements only.
# - It does NOT compare them with a candidate profile.
# - Evidence is preserved for later validation/matching stages.
# ==========================================================


DEGREE_PATTERNS = {
    "bachelor": (
        r"\bbachelor(?:'s)?(?: degree)?\b",
        r"\bb\.?\s*sc\.?\b",
        r"\bundergraduate degree\b",
    ),
    "master": (
        r"\bmaster(?:'s)?(?: degree)?\b",
        r"\bm\.?\s*sc\.?\b",
        r"\bgraduate degree\b",
    ),
    "phd": (
        r"\bph\.?\s*d\.?\b",
        r"\bdoctorate\b",
        r"\bdoctoral degree\b",
    ),
}


GENERIC_DEGREE_PATTERNS = (
    r"\buniversity degree\b",
    r"\bacademic degree\b",
    r"\bcollege degree\b",
    r"\bdegree in\b",
)


EQUIVALENT_EXPERIENCE_PATTERNS = (
    r"\bor equivalent experience\b",
    r"\bor equivalent practical experience\b",
    r"\bor comparable experience\b",
    r"\bor relevant experience\b",
    r"\bequivalent combination of education and experience\b",
)


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
        r"\bfran(?:ç|c)ais\b",
    ),
}


LANGUAGE_REQUIREMENT_PATTERNS = (
    r"\bfluent\b",
    r"\bfluency\b",
    r"\bproficien(?:t|cy)\b",
    r"\bprofessional proficiency\b",
    r"\bbusiness[- ]level\b",
    r"\bworking proficiency\b",
    r"\bwritten and spoken\b",
    r"\bspoken and written\b",
    r"\bexcellent (?:written|spoken|communication)\b",
    r"\bstrong (?:written|spoken|communication)\b",
    r"\bmust (?:speak|write|communicate)\b",
    r"\brequired\b",
    r"\bmandatory\b",
)


SKILL_PATTERNS = {
    "linux": (
        r"\blinux\b",
    ),
    "ubuntu": (
        r"\bubuntu\b",
    ),
    "debian": (
        r"\bdebian\b",
    ),
    "red hat": (
        r"\bred hat\b",
        r"\bredhat\b",
    ),
    "rhel": (
        r"\brhel\b",
    ),
    "centos": (
        r"\bcentos\b",
    ),
    "bash": (
        r"\bbash\b",
        r"\bshell scripting\b",
    ),
    "python": (
        r"\bpython\b",
    ),
    "powershell": (
        r"\bpowershell\b",
    ),
    "ansible": (
        r"\bansible\b",
    ),
    "terraform": (
        r"\bterraform\b",
    ),
    "docker": (
        r"\bdocker\b",
    ),
    "kubernetes": (
        r"\bkubernetes\b",
        r"\bk8s\b",
    ),
    "vmware": (
        r"\bvmware\b",
    ),
    "esxi": (
        r"\besxi\b",
    ),
    "vcenter": (
        r"\bvcenter\b",
    ),
    "veeam": (
        r"\bveeam\b",
    ),
    "zabbix": (
        r"\bzabbix\b",
    ),
    "prometheus": (
        r"\bprometheus\b",
    ),
    "grafana": (
        r"\bgrafana\b",
    ),
    "aws": (
        r"\baws\b",
        r"\bamazon web services\b",
    ),
    "azure": (
        r"\bazure\b",
    ),
    "gcp": (
        r"\bgcp\b",
        r"\bgoogle cloud(?: platform)?\b",
    ),
    "active directory": (
        r"\bactive directory\b",
        r"\bmicrosoft ad\b",
    ),
    "windows server": (
        r"\bwindows server\b",
    ),
    "networking": (
        r"\bnetworking\b",
        r"\bnetwork infrastructure\b",
    ),
    "tcp/ip": (
        r"\btcp\s*/\s*ip\b",
        r"\btcp-ip\b",
    ),
    "dns": (
        r"\bdns\b",
    ),
    "dhcp": (
        r"\bdhcp\b",
    ),
    "firewall": (
        r"\bfirewalls?\b",
    ),
    "vpn": (
        r"\bvpns?\b",
    ),
    "postgresql": (
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ),
    "mysql": (
        r"\bmysql\b",
    ),
    "git": (
        r"\bgit\b",
    ),
    "ci/cd": (
        r"\bci\s*/\s*cd\b",
        r"\bci-cd\b",
        r"\bcontinuous integration\b",
        r"\bcontinuous delivery\b",
        r"\bcontinuous deployment\b",
    ),
    "jenkins": (
        r"\bjenkins\b",
    ),
}


REQUIRED_MARKER_PATTERNS = (
    r"\brequired\b",
    r"\brequirements?\b",
    r"\bmust[- ]have\b",
    r"\bmust be\b",
    r"\byou must\b",
    r"\bmandatory\b",
    r"\bessential\b",
    r"\bminimum\b",
    r"\bat least\b",
    r"\bwe expect\b",
    r"\byou bring\b",
    r"\bproven experience\b",
    r"\bhands[- ]on experience\b",
    r"\bstrong experience\b",
    r"\bstrong knowledge\b",
    r"\bsolid experience\b",
    r"\bsolid knowledge\b",
)


PREFERRED_MARKER_PATTERNS = (
    r"\bpreferred\b",
    r"\bnice[- ]to[- ]have\b",
    r"\bnice to have\b",
    r"\bdesirable\b",
    r"\bbonus(?: points?)?\b",
    r"\ban advantage\b",
    r"\badvantageous\b",
    r"\bis a plus\b",
    r"\bwould be a plus\b",
)


REQUIRED_SECTION_PATTERNS = (
    r"^\s*requirements?\s*:?\s*$",
    r"^\s*qualifications?\s*:?\s*$",
    r"^\s*required qualifications?\s*:?\s*$",
    r"^\s*minimum qualifications?\s*:?\s*$",
    r"^\s*what you bring\s*:?\s*$",
    r"^\s*what you(?:'|’)ll bring\s*:?\s*$",
    r"^\s*what we(?:'|’)re looking for\s*:?\s*$",
    r"^\s*what we are looking for\s*:?\s*$",
    r"^\s*your profile\s*:?\s*$",
    r"^\s*your background\s*:?\s*$",
    r"^\s*skills and experience\s*:?\s*$",
    r"^\s*experience and skills\s*:?\s*$",
)


PREFERRED_SECTION_PATTERNS = (
    r"^\s*preferred qualifications?\s*:?\s*$",
    r"^\s*nice[- ]to[- ]have\s*:?\s*$",
    r"^\s*nice to have\s*:?\s*$",
    r"^\s*bonus(?: points?)?\s*:?\s*$",
    r"^\s*additional qualifications?\s*:?\s*$",
)


NON_REQUIREMENT_SECTION_PATTERNS = (
    r"^\s*responsibilities\s*:?\s*$",
    r"^\s*your responsibilities\s*:?\s*$",
    r"^\s*what you(?:'|’)ll do\s*:?\s*$",
    r"^\s*what you will do\s*:?\s*$",
    r"^\s*the role\s*:?\s*$",
    r"^\s*about the role\s*:?\s*$",
    r"^\s*what we offer\s*:?\s*$",
    r"^\s*benefits\s*:?\s*$",
    r"^\s*perks\s*:?\s*$",
    r"^\s*about us\s*:?\s*$",
    r"^\s*about the company\s*:?\s*$",
)


REMOTE_PATTERNS = (
    r"\b100%\s+remote\b",
    r"\bfully remote\b",
    r"\bremote[- ]first\b",
    r"\bwork remotely\b",
    r"\bremote role\b",
    r"\bremote position\b",
    r"\bremote within\b",
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
    r"\boffice[- ]based\b",
)


WORK_AUTH_BLOCK_PATTERNS = (
    r"\bmust (?:already )?have (?:the )?(?:right|authorization) to work\b",
    r"\bmust be (?:legally )?authorized to work\b",
    r"\blegally authorized to work\b",
    r"\bno (?:visa )?sponsorship\b",
    r"\bwithout (?:visa )?sponsorship\b",
    r"\bwe (?:do not|don't) sponsor\b",
    r"\bsponsorship (?:is )?not available\b",
    r"\bunable to sponsor\b",
)


SPONSORSHIP_POSITIVE_PATTERNS = (
    r"\bvisa sponsorship (?:is )?available\b",
    r"\bwork permit sponsorship\b",
    r"\bsponsorship available\b",
    r"\bwe sponsor\b",
    r"\bimmigration support\b",
    r"\bvisa support\b",
)


RELOCATION_PATTERNS = (
    r"\brelocation assistance\b",
    r"\brelocation support\b",
    r"\brelocation package\b",
    r"\brelocation provided\b",
)


OVERALL_EXPERIENCE_PATTERNS = (
    re.compile(
        r"\b(?:minimum|min\.?|at least)\s+"
        r"(?P<years>\d{1,2})\+?\s+years?\s+"
        r"(?:of\s+)?(?:professional\s+|relevant\s+|work\s+)?experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<years>\d{1,2})\+\s+years?\s+"
        r"(?:of\s+)?(?:professional\s+|relevant\s+|work\s+)?experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<years>\d{1,2})\s*(?:-|–|to)\s*"
        r"(?P<max_years>\d{1,2})\s+years?\s+"
        r"(?:of\s+)?(?:professional\s+|relevant\s+|work\s+)?experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<years>\d{1,2})\s+years?\s+"
        r"(?:of\s+)?(?:professional\s+|relevant\s+|work\s+)?experience\b",
        re.IGNORECASE,
    ),
)


GENERIC_YEARS_PATTERNS = (
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
        r"</\s*(?:p|li|div|h[1-6]|ul|ol)\s*>",
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
        r"\r\n?",
        "\n",
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


def _section_kind(line: str) -> str | None:
    if _contains_any(
        line,
        PREFERRED_SECTION_PATTERNS,
    ):
        return "preferred"

    if _contains_any(
        line,
        REQUIRED_SECTION_PATTERNS,
    ):
        return "required"

    if _contains_any(
        line,
        NON_REQUIREMENT_SECTION_PATTERNS,
    ):
        return "neutral"

    return None


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    if len(stripped) > 80:
        return False

    if stripped.endswith((".", "!", "?")):
        return False

    if _section_kind(stripped):
        return True

    return stripped.endswith(":") and len(
        stripped.split()
    ) <= 8


def _entries(text: str) -> list[dict]:
    if not text:
        return []

    entries = []
    current_section = "neutral"

    for raw_line in text.splitlines():
        line = raw_line.strip(
            " \t\r\n-–—•●▪"
        )

        if not line:
            continue

        kind = _section_kind(
            line
        )

        if kind and _looks_like_heading(
            line
        ):
            current_section = kind
            continue

        pieces = re.split(
            r"(?<=[.!?])\s+|(?:\s*[•●▪]\s*)",
            line,
        )

        for piece in pieces:
            piece = piece.strip(
                " \t\r\n-–—•●▪"
            )

            if not piece:
                continue

            entries.append(
                {
                    "text": piece,
                    "section": current_section,
                }
            )

    return entries


def _entry_strength(
    entry: dict,
) -> str:
    text = entry["text"]

    if _contains_any(
        text,
        PREFERRED_MARKER_PATTERNS,
    ):
        return "preferred"

    if _contains_any(
        text,
        REQUIRED_MARKER_PATTERNS,
    ):
        return "required"

    if entry["section"] == "preferred":
        return "preferred"

    if entry["section"] == "required":
        return "required"

    return "mentioned"


def _matched_skills(
    text: str,
) -> list[str]:
    matched = []

    for skill, patterns in (
        SKILL_PATTERNS.items()
    ):
        if _contains_any(
            text,
            patterns,
        ):
            matched.append(
                skill
            )

    return matched


def _extract_years(
    match: re.Match,
) -> tuple[int, int | None]:
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

    return minimum, maximum


def _find_experience(
    entries: list[dict],
) -> dict:
    overall_evidence = []
    skill_specific_evidence = []

    for entry in entries:
        sentence = entry["text"]

        if not re.search(
            r"\byears?\b",
            sentence,
            flags=re.IGNORECASE,
        ):
            continue

        overall_match = None

        for pattern in (
            OVERALL_EXPERIENCE_PATTERNS
        ):
            overall_match = (
                pattern.search(
                    sentence
                )
            )

            if overall_match:
                break

        if overall_match:
            minimum, maximum = (
                _extract_years(
                    overall_match
                )
            )

            overall_evidence.append(
                {
                    "minimum_years": minimum,
                    "maximum_years": maximum,
                    "strength": _entry_strength(
                        entry
                    ),
                    "scope": "overall",
                    "evidence": sentence,
                }
            )

            continue

        generic_match = None

        for pattern in (
            GENERIC_YEARS_PATTERNS
        ):
            generic_match = (
                pattern.search(
                    sentence
                )
            )

            if generic_match:
                break

        if not generic_match:
            continue

        skills = _matched_skills(
            sentence
        )

        # A naked "3+ years" is too ambiguous unless the sentence
        # clearly anchors it to a technical skill/domain.
        if not skills:
            continue

        minimum, maximum = (
            _extract_years(
                generic_match
            )
        )

        skill_specific_evidence.append(
            {
                "minimum_years": minimum,
                "maximum_years": maximum,
                "skills": skills,
                "strength": _entry_strength(
                    entry
                ),
                "scope": "skill_specific",
                "evidence": sentence,
            }
        )

    required_overall = [
        item
        for item in overall_evidence
        if item["strength"] == "required"
    ]

    usable_overall = (
        required_overall
        or overall_evidence
    )

    minimum_years = (
        max(
            item["minimum_years"]
            for item in usable_overall
        )
        if usable_overall
        else None
    )

    return {
        "explicit": bool(
            overall_evidence
            or skill_specific_evidence
        ),
        "minimum_years": (
            minimum_years
        ),
        "evidence": (
            overall_evidence
            + skill_specific_evidence
        ),
        "overall_evidence": (
            overall_evidence
        ),
        "skill_specific_evidence": (
            skill_specific_evidence
        ),
    }


def _find_education(
    entries: list[dict],
) -> dict:
    levels = []
    evidence = []
    required = False
    preferred = False
    equivalent_experience_accepted = (
        False
    )

    for entry in entries:
        sentence = entry["text"]

        matched_levels = []

        for level, patterns in (
            DEGREE_PATTERNS.items()
        ):
            if _contains_any(
                sentence,
                patterns,
            ):
                matched_levels.append(
                    level
                )

        generic_degree = _contains_any(
            sentence,
            GENERIC_DEGREE_PATTERNS,
        )

        if not matched_levels and not (
            generic_degree
        ):
            continue

        strength = _entry_strength(
            entry
        )

        if strength == "required":
            required = True

        elif strength == "preferred":
            preferred = True

        equivalent = _contains_any(
            sentence,
            EQUIVALENT_EXPERIENCE_PATTERNS,
        )

        if equivalent:
            equivalent_experience_accepted = (
                True
            )

        levels.extend(
            matched_levels
        )

        evidence.append(
            {
                "levels": matched_levels,
                "generic_degree": (
                    generic_degree
                ),
                "strength": strength,
                "equivalent_experience_accepted": (
                    equivalent
                ),
                "evidence": sentence,
            }
        )

    strict_degree_required = (
        required
        and not (
            equivalent_experience_accepted
        )
    )

    return {
        "explicit": bool(evidence),
        "levels": _unique(
            levels
        ),
        "required": required,
        "preferred_only": (
            bool(evidence)
            and preferred
            and not required
        ),
        "equivalent_experience_accepted": (
            equivalent_experience_accepted
        ),
        "strict_degree_required": (
            strict_degree_required
        ),
        "evidence": evidence,
    }


def _find_languages(
    entries: list[dict],
) -> dict:
    required = []
    preferred = []
    mentioned = []
    evidence = []

    for entry in entries:
        sentence = entry["text"]

        languages = []

        for language, patterns in (
            LANGUAGE_PATTERNS.items()
        ):
            if _contains_any(
                sentence,
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

        strength = _entry_strength(
            entry
        )

        explicit_language_requirement = (
            _contains_any(
                sentence,
                LANGUAGE_REQUIREMENT_PATTERNS,
            )
        )

        if strength == "preferred":
            preferred.extend(
                languages
            )

        elif (
            strength == "required"
            or explicit_language_requirement
        ):
            required.extend(
                languages
            )

            strength = "required"

        evidence.append(
            {
                "languages": languages,
                "strength": strength,
                "evidence": sentence,
            }
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
    entries: list[dict],
) -> dict:
    blocker_evidence = []
    sponsorship_evidence = []
    relocation_evidence = []

    for entry in entries:
        sentence = entry["text"]

        blocker = _contains_any(
            sentence,
            WORK_AUTH_BLOCK_PATTERNS,
        )

        # Important: "no visa sponsorship" contains the words
        # "visa sponsorship". A blocker sentence must never also
        # be recorded as positive sponsorship evidence.
        if blocker:
            blocker_evidence.append(
                sentence
            )

        elif _contains_any(
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
        "blocker_evidence": (
            blocker_evidence
        ),
        "sponsorship_evidence": (
            sponsorship_evidence
        ),
        "relocation_evidence": (
            relocation_evidence
        ),
    }


def _find_location_mode(
    job: dict,
    text: str,
) -> dict:
    context = " ".join(
        part
        for part in (
            str(job.get("title", "")),
            str(job.get("location", "")),
            text,
        )
        if part
    )

    remote = _contains_any(
        context,
        REMOTE_PATTERNS,
    )

    hybrid = _contains_any(
        context,
        HYBRID_PATTERNS,
    )

    onsite = _contains_any(
        context,
        ONSITE_PATTERNS,
    )

    if hybrid:
        mode = "hybrid"

    elif remote and not onsite:
        mode = "remote"

    elif onsite and not remote:
        mode = "onsite"

    elif remote and onsite:
        mode = "mixed_or_unclear"

    else:
        mode = "unknown"

    return {
        "mode": mode,
        "remote_signal": remote,
        "hybrid_signal": hybrid,
        "onsite_signal": onsite,
        "conflicting_signals": (
            sum(
                (
                    bool(remote),
                    bool(hybrid),
                    bool(onsite),
                )
            )
            > 1
        ),
    }


def _find_skills(
    entries: list[dict],
) -> dict:
    required = []
    preferred = []
    mentioned = []
    evidence = []

    for entry in entries:
        sentence = entry["text"]

        matched = _matched_skills(
            sentence
        )

        if not matched:
            continue

        mentioned.extend(
            matched
        )

        strength = _entry_strength(
            entry
        )

        if strength == "required":
            required.extend(
                matched
            )

        elif strength == "preferred":
            preferred.extend(
                matched
            )

        evidence.append(
            {
                "skills": matched,
                "strength": strength,
                "section": entry["section"],
                "evidence": sentence,
            }
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

    entries = _entries(
        text
    )

    experience = _find_experience(
        entries
    )

    education = _find_education(
        entries
    )

    languages = _find_languages(
        entries
    )

    work_authorization = (
        _find_work_authorization(
            entries
        )
    )

    location = _find_location_mode(
        job,
        text,
    )

    skills = _find_skills(
        entries
    )

    has_description = bool(
        text.strip()
    )

    explicit_requirement_count = sum(
        (
            1
            if (
                experience[
                    "minimum_years"
                ]
                is not None
            )
            else 0,

            1
            if education["required"]
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
