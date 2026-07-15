"""
Krishi Setu — Deterministic Eligibility Engine
Compares farmer profile against scheme eligibility criteria.
Returns Met / Not Met / N/A with plain-language explanation per criterion.
Never uses LLM for eligibility decisions — purely rule-based.
"""

from typing import Any

from app.models.models import EligibilityResult, FarmerProfile, Scheme


# ── Result helpers ─────────────────────────────────────────────────────────────

def _met(explanation: str) -> dict[str, str]:
    return {"result": EligibilityResult.MET, "explanation": explanation}


def _not_met(explanation: str) -> dict[str, str]:
    return {"result": EligibilityResult.NOT_MET, "explanation": explanation}


def _na(explanation: str) -> dict[str, str]:
    return {"result": EligibilityResult.NA, "explanation": explanation}


# ── Individual criterion checkers ──────────────────────────────────────────────

def check_land_holding(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check land holding against min/max criteria."""
    land_criteria = criteria.get("land_holding_acres")
    if not land_criteria:
        return _na("No land holding requirement specified for this scheme.")

    if farmer.land_holding_acres is None:
        return _na("Land holding not provided in your profile.")

    acres = farmer.land_holding_acres
    min_acres = land_criteria.get("min")
    max_acres = land_criteria.get("max")

    if min_acres is not None and acres < min_acres:
        return _not_met(
            f"You hold {acres} acres, but this scheme requires at least {min_acres} acres."
        )
    if max_acres is not None and acres > max_acres:
        return _not_met(
            f"You hold {acres} acres, but this scheme is only for farmers with up to {max_acres} acres."
        )

    parts = []
    if min_acres is not None:
        parts.append(f"minimum {min_acres} acres")
    if max_acres is not None:
        parts.append(f"maximum {max_acres} acres")

    return _met(
        f"Your land holding of {acres} acres meets the requirement ({', '.join(parts)})."
    )


def check_caste(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check caste category eligibility."""
    caste_criteria = criteria.get("caste")
    if not caste_criteria:
        return _na("No caste requirement specified for this scheme.")

    if farmer.caste is None:
        return _na("Caste category not provided in your profile.")

    allowed = [c.upper() for c in caste_criteria] if isinstance(caste_criteria, list) else []
    farmer_caste = farmer.caste.upper()

    if "ALL" in allowed:
        return _met("This scheme is open to all caste categories.")

    if farmer_caste in allowed:
        return _met(
            f"Your caste category ({farmer.caste}) is eligible for this scheme."
        )

    return _not_met(
        f"Your caste category ({farmer.caste}) is not in the eligible list: {', '.join(caste_criteria)}."
    )


def check_annual_income(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check annual income against max limit."""
    income_criteria = criteria.get("annual_income")
    if not income_criteria:
        return _na("No income requirement specified for this scheme.")

    if farmer.annual_income is None:
        return _na("Annual income not provided in your profile.")

    max_income = income_criteria.get("max")
    min_income = income_criteria.get("min")

    if max_income is not None and farmer.annual_income > max_income:
        return _not_met(
            f"Your annual income of ₹{farmer.annual_income:,} exceeds the limit of ₹{max_income:,} for this scheme."
        )
    if min_income is not None and farmer.annual_income < min_income:
        return _not_met(
            f"Your annual income of ₹{farmer.annual_income:,} is below the minimum of ₹{min_income:,} required."
        )

    return _met(
        f"Your annual income of ₹{farmer.annual_income:,} meets the scheme's income requirement."
    )


def check_age(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check age against min/max criteria."""
    age_criteria = criteria.get("age")
    if not age_criteria:
        return _na("No age requirement specified for this scheme.")

    if farmer.age is None:
        return _na("Age not provided in your profile.")

    min_age = age_criteria.get("min")
    max_age = age_criteria.get("max")

    if min_age is not None and farmer.age < min_age:
        return _not_met(
            f"You are {farmer.age} years old, but this scheme requires a minimum age of {min_age}."
        )
    if max_age is not None and farmer.age > max_age:
        return _not_met(
            f"You are {farmer.age} years old, but this scheme is only for farmers up to age {max_age}."
        )

    return _met(f"Your age ({farmer.age}) meets the scheme's age requirement.")


def check_state(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check if farmer's state is covered by the scheme."""
    state_criteria = criteria.get("states") or criteria.get("state")
    if not state_criteria:
        return _na("No state restriction specified — scheme is available nationwide.")

    allowed_states = [s.lower() for s in state_criteria] if isinstance(state_criteria, list) else []

    if "all" in allowed_states:
        return _met("This scheme is available in all states.")

    if farmer.state is None:
        return _na("State not provided in your profile.")

    if farmer.state.lower() in allowed_states:
        return _met(f"Your state ({farmer.state}) is covered by this scheme.")

    return _not_met(
        f"This scheme is not available in {farmer.state}. "
        f"Available states: {', '.join(state_criteria)}."
    )


def check_bpl(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check BPL (Below Poverty Line) requirement."""
    bpl_required = criteria.get("is_bpl") or criteria.get("bpl_required")
    if bpl_required is None:
        return _na("No BPL requirement specified for this scheme.")

    if farmer.is_bpl is None:
        return _na("BPL status not provided in your profile.")

    if bpl_required and not farmer.is_bpl:
        return _not_met("This scheme requires BPL (Below Poverty Line) status.")

    if bpl_required and farmer.is_bpl:
        return _met("You meet the BPL requirement for this scheme.")

    return _na("BPL status check is not applicable for this scheme.")


def check_gender(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check gender eligibility."""
    gender_criteria = criteria.get("gender")
    if not gender_criteria:
        return _na("No gender restriction for this scheme.")

    if farmer.gender is None:
        return _na("Gender not provided in your profile.")

    if isinstance(gender_criteria, list):
        allowed = [g.lower() for g in gender_criteria]
    else:
        allowed = [gender_criteria.lower()]

    if "all" in allowed:
        return _met("This scheme is open to all genders.")

    if farmer.gender.lower() in allowed:
        return _met(f"Your gender ({farmer.gender}) meets the scheme requirement.")

    return _not_met(
        f"This scheme is for {', '.join(gender_criteria)} farmers only."
    )


def check_excluded_categories(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check if farmer falls in any excluded category."""
    excluded = criteria.get("excluded")
    if not excluded:
        return _na("No exclusion criteria specified for this scheme.")

    # We can only check exclusions we have data for
    # For now we flag known exclusions as N/A since we don't collect tax data etc.
    return _na(
        f"Exclusion categories exist for this scheme: {', '.join(excluded)}. "
        "Please verify you do not fall in any excluded category before applying."
    )


def check_occupation(
    farmer: FarmerProfile,
    criteria: dict[str, Any],
) -> dict[str, str]:
    """Check occupation/activity requirement."""
    occupation = criteria.get("occupation")
    if not occupation:
        return _na("No specific occupation requirement for this scheme.")

    # Since this is a farmer platform, we assume all registered users are farmers
    allowed = [occupation] if isinstance(occupation, str) else occupation
    allowed_lower = [o.lower() for o in allowed]

    if "farmer" in allowed_lower:
        return _met("As a registered farmer, you meet the occupation requirement.")

    return _na(
        f"Occupation requirement: {', '.join(allowed)}. Please verify your eligibility."
    )


# ── Main eligibility check function ───────────────────────────────────────────

def check_eligibility(
    farmer: FarmerProfile,
    scheme: Scheme,
) -> dict:
    """
    Run all applicable eligibility checks for a farmer against a scheme.
    Returns:
      - overall_result: met / not_met / na
      - criteria_results: per-criterion breakdown
      - summary: plain-language explanation
    """
    criteria = scheme.eligibility_criteria or {}
    results: dict[str, dict[str, str]] = {}

    # Run all checkers
    checkers = [
        ("land_holding", check_land_holding),
        ("caste", check_caste),
        ("annual_income", check_annual_income),
        ("age", check_age),
        ("state", check_state),
        ("bpl_status", check_bpl),
        ("gender", check_gender),
        ("excluded_categories", check_excluded_categories),
        ("occupation", check_occupation),
    ]

    for criterion_name, checker_fn in checkers:
        results[criterion_name] = checker_fn(farmer, criteria)

    # ── Determine overall result ───────────────────────────────────────────────
    # Rule: if ANY criterion is NOT_MET → overall is NOT_MET
    # Rule: if all criteria are MET or N/A → overall is MET
    # Rule: if all criteria are N/A → overall is N/A (insufficient data)

    not_met_criteria = [
        name for name, r in results.items()
        if r["result"] == EligibilityResult.NOT_MET
    ]
    met_criteria = [
        name for name, r in results.items()
        if r["result"] == EligibilityResult.MET
    ]

    if not_met_criteria:
        overall = EligibilityResult.NOT_MET
        summary = (
            f"You are NOT eligible for {scheme.name}. "
            f"Failed criteria: {', '.join(not_met_criteria)}."
        )
    elif met_criteria:
        overall = EligibilityResult.MET
        summary = (
            f"You appear ELIGIBLE for {scheme.name}. "
            f"All checked criteria are met. Please verify any N/A criteria before applying."
        )
    else:
        overall = EligibilityResult.NA
        summary = (
            f"Eligibility for {scheme.name} could not be fully determined. "
            "Please complete your profile with land holding, income, and other details."
        )

    return {
        "overall_result": overall,
        "criteria_results": results,
        "summary": summary,
    }
