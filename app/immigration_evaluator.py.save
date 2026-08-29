from app.immigration_rules import (
    get_country_rule,
    get_current_pathways,
)


def normalize_text(value):
    if not value:
        return ""

    return " ".join(
        value.lower().split()
    )


def role_matches_known_rule(
    job_title,
    pathway,
):
    normalized_title = normalize_text(
        job_title
    )

    known_matches = pathway.get(
        "known_role_matches",
        [],
    )

    matches = []

    for role_rule in known_matches:
        role = role_rule.get(
            "role",
            ""
        )

        normalized_role = normalize_text(
            role
        )

        if (
            normalized_role
            and normalized_role
            in normalized_title
        ):
            matches.append(
                {
                    "role": role,
                    "education": role_rule.get(
                        "education"
                    ),
                    "valid_until": role_rule.get(
                        "valid_until"
                    ),
                }
            )

    return matches


def evaluate_pathway(
    job,
    pathway,
):
    title = job.get(
        "title",
        ""
    )

    role_matches = (
        role_matches_known_rule(
            title,
            pathway,
        )
    )

    checks = []

    # ---------------------------------------------
    # Explicit blocker from the job posting
    # ---------------------------------------------

    if job.get(
        "work_authorization_blocked",
        False,
    ):
        checks.append(
            {
                "check": "job_work_authorization",
                "status": "blocked",
                "reason": (
                    "Explicit work authorization "
                    "restriction detected in job posting."
                ),
            }
        )

    else:
        checks.append(
            {
                "check": "job_work_authorization",
                "status": "no_explicit_blocker",
            }
        )

    # ---------------------------------------------
    # Known occupation / role matching
    # ---------------------------------------------

    if role_matches:
        checks.append(
            {
                "check": "known_role_match",
                "status": "matched",
                "evidence": role_matches,
            }
        )

    elif pathway.get(
        "occupation_rule"
    ):
        checks.append(
            {
                "check": "occupation",
                "status": "needs_verification",
                "rule": pathway[
                    "occupation_rule"
                ],
            }
        )

    else:
        checks.append(
            {
                "check": "occupation",
                "status": "not_explicitly_restricted",
            }
        )

    # ---------------------------------------------
    # Salary
    # ---------------------------------------------

    salary_rule = pathway.get(
        "salary"
    )

    if salary_rule:
        checks.append(
            {
                "check": "salary",
                "status": "needs_verification",
                "requirement": salary_rule,
            }
        )

    elif pathway.get(
        "salary_rule"
    ):
        checks.append(
            {
                "check": "salary",
                "status": "needs_verification",
                "requirement": pathway[
                    "salary_rule"
                ],
            }
        )

    else:
        checks.append(
            {
                "check": "salary",
                "status": "no_fixed_threshold_configured",
            }
        )

    # ---------------------------------------------
    # Sponsorship requirements
    # ---------------------------------------------

    if pathway.get(
        "recognized_sponsor_required",
        False,
    ):
        checks.append(
            {
                "check": "recognized_sponsor",
                "status": "needs_verification",
            }
        )

    if pathway.get(
        "approved_sponsor_required",
        False,
    ):
        checks.append(
            {
                "check": "approved_sponsor",
                "status": "needs_verification",
            }
        )

    if pathway.get(
        "employer_sponsorship_required",
        False,
    ):
        if job.get(
            "sponsorship_evidence",
            False,
        ):
            checks.append(
                {
                    "check": "employer_sponsorship",
                    "status": "positive_evidence",
                }
            )

        else:
            checks.append(
                {
                    "check": "employer_sponsorship",
                    "status": "needs_verification",
                }
            )

    # ---------------------------------------------
    # Relocation evidence
    # ---------------------------------------------

    if job.get(
        "relocation_evidence",
        False,
    ):
        checks.append(
            {
                "check": "relocation",
                "status": "positive_evidence",
            }
        )

    # ---------------------------------------------
    # International hiring evidence
    # ---------------------------------------------

    if job.get(
        "international_hiring_evidence",
        False,
    ):
        checks.append(
            {
                "check": "international_hiring",
                "status": "positive_evidence",
            }
        )

    # ---------------------------------------------
    # Overall pathway assessment
    # ---------------------------------------------

    blocked = any(
        check["status"] == "blocked"
        for check in checks
    )

    needs_verification = any(
        check["status"]
        == "needs_verification"
        for check in checks
    )

    if blocked:
        assessment = (
            "blocked_by_job_posting"
        )

    elif role_matches:
        assessment = (
            "potentially_eligible"
        )

    elif needs_verification:
        assessment = (
            "needs_verification"
        )

    else:
        assessment = (
            "potentially_eligible"
        )

    return {
        "pathway_id": pathway["id"],
        "pathway_name": pathway["name"],
        "assessment": assessment,
        "role_matches": role_matches,
        "checks": checks,
        "confidence": pathway.get(
            "confidence",
            "unknown",
        ),
        "source_name": pathway.get(
            "source_name"
        ),
        "source_domain": pathway.get(
            "source_domain"
        ),
    }


def evaluate_job_immigration(job):
    country_code = job.get(
        "country_code"
    )

    if not country_code:
        return {
            "country_code": None,
            "country": None,
            "market_enabled": False,
            "assessment": "country_unknown",
            "pathways": [],
        }

    country = get_country_rule(
        country_code
    )

    if not country:
        return {
            "country_code": country_code,
            "country": job.get(
                "country"
            ),
            "market_enabled": False,
            "assessment": "rules_not_configured",
            "pathways": [],
        }

    pathways = get_current_pathways(
        country_code
    )

    if not pathways:
        return {
            "country_code": country_code,
            "country": country["name"],
            "market_enabled": country.get(
                "enabled",
                False,
            ),
            "assessment": "no_current_pathway",
            "pathways": [],
        }

    pathway_results = [
        evaluate_pathway(
            job,
            pathway,
        )
        for pathway in pathways
    ]

    assessments = {
        result["assessment"]
        for result in pathway_results
    }

    if "potentially_eligible" in assessments:
        overall = "potentially_eligible"

    elif "needs_verification" in assessments:
        overall = "needs_verification"

    elif (
        "blocked_by_job_posting"
        in assessments
    ):
        overall = "blocked_by_job_posting"

    else:
        overall = "needs_verification"

    if not country.get(
        "enabled",
        False,
    ):
        overall = "market_disabled"

    return {
        "country_code": country_code,
        "country": country["name"],
        "market_enabled": country.get(
            "enabled",
            False,
        ),
        "assessment": overall,
        "pathways": pathway_results,
    }
