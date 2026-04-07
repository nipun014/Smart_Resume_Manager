try:
    from .scorer import score_candidate
    from .semantic_scorer import semantic_score
    from .jd_skill_extractor import SKILL_ALIASES
except ImportError:
    # Fallback when running this file directly.
    from scorer import score_candidate
    from semantic_scorer import semantic_score
    from jd_skill_extractor import SKILL_ALIASES


def _clamp(value, low, high):
    return max(low, min(high, value))


def _alias_set_for_skill(skill):
    key = str(skill or "").strip()
    if not key:
        return set()

    aliases = SKILL_ALIASES.get(key)
    if aliases is None:
        for canonical, alias_list in SKILL_ALIASES.items():
            if canonical.lower() == key.lower():
                aliases = alias_list
                key = canonical
                break

    if aliases is None:
        aliases = [key]

    normalized = {str(item).strip().lower() for item in aliases if str(item).strip()}
    normalized.add(key.lower())
    return normalized


def _normalize_jd_profile(jd_skills, jd_profile=None):
    profile_skills = (jd_profile or {}).get("skills", {})
    if profile_skills:
        normalized = {}
        for skill, details in profile_skills.items():
            payload = details or {}
            normalized[str(skill)] = {
                "required_years": float(payload.get("required_years", 0.0) or 0.0),
                "priority": str(payload.get("priority", "medium") or "medium").lower(),
            }
        return {"skills": normalized}

    fallback = {}
    for skill in jd_skills or []:
        fallback[str(skill)] = {"required_years": 0.0, "priority": "medium"}
    return {"skills": fallback}


def score_candidate_experience(jd_profile, skill_experience):
    score = 0.0
    skills = (jd_profile or {}).get("skills", {})
    total = len(skills)
    if total == 0:
        return 0

    skill_experience = skill_experience or {}

    for skill, requirements in skills.items():
        alias_set = _alias_set_for_skill(skill)
        best_match = 0.0
        required_years = float((requirements or {}).get("required_years", 0.0) or 0.0)

        for cand_skill, years in skill_experience.items():
            cand_skill_norm = str(cand_skill).strip().lower()
            if cand_skill_norm in alias_set:
                years_value = float(years or 0.0)
                if required_years > 0:
                    ratio = years_value / required_years
                else:
                    ratio = min(years_value / 2.0, 1.0)
                best_match = max(best_match, min(ratio, 1.0))

        score += (best_match / total) * 100.0

    return round(score)


def _calculate_high_priority_penalty(jd_profile, candidate_skills):
    skills = (jd_profile or {}).get("skills", {})
    if not skills:
        return 0.0, 0, 0

    candidate_normalized = {str(skill or "").strip().lower() for skill in (candidate_skills or [])}
    high_priority_skills = [
        skill for skill, details in skills.items()
        if str((details or {}).get("priority", "medium")).lower() == "high"
    ]

    total_high = len(high_priority_skills)
    if total_high == 0:
        return 0.0, 0, 0

    missing_high = 0
    for skill in high_priority_skills:
        alias_set = _alias_set_for_skill(skill)
        if not any(alias in candidate_normalized for alias in alias_set):
            missing_high += 1

    penalty_ratio = missing_high / total_high
    return penalty_ratio, missing_high, total_high


def final_score(jd_text, jd_skills, resume_text, candidate_skills, profile=None, jd_profile=None):

    jd_profile = _normalize_jd_profile(jd_skills, jd_profile)
    keyword = score_candidate(jd_skills, candidate_skills)
    semantic_raw = semantic_score(jd_text, resume_text)

    profile = profile or {}
    skill_experience = profile.get("skill_experience", {})
    avg_confidence = float(profile.get("avg_confidence", 1.0) or 1.0)
    avg_confidence = _clamp(avg_confidence, 0.0, 1.0)

    experience = score_candidate_experience(jd_profile, skill_experience)
    experience = experience * avg_confidence
    experience = _clamp(experience, 0.0, 100.0)

    semantic = semantic_raw * (0.5 + 0.5 * (experience / 100.0))
    semantic = _clamp(semantic, 0.0, 100.0)

    penalty_ratio, missing_high_priority, total_high_priority = _calculate_high_priority_penalty(
        jd_profile,
        candidate_skills,
    )

    combined = (0.20 * keyword) + (0.40 * semantic) + (0.40 * experience)
    combined *= (1.0 - 0.5 * penalty_ratio)
    combined = round(combined)
    combined = int(_clamp(combined, 0, 100))

    return {
        "final": combined,
        "keyword": keyword,
        "semantic": round(semantic),
        "semantic_raw": semantic_raw,
        "experience": round(experience),
        "missing_high_priority": missing_high_priority,
        "total_high_priority": total_high_priority,
        "jd_profile": jd_profile,
    }