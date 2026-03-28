try:
    from .scorer import score_candidate
    from .semantic_scorer import semantic_score
except ImportError:
    # Fallback when running this file directly.
    from scorer import score_candidate
    from semantic_scorer import semantic_score

def final_score(jd_text, jd_skills, resume_text, candidate_skills):
    
    keyword = score_candidate(jd_skills, candidate_skills)
    semantic = semantic_score(jd_text,resume_text)
    
    combined = round((keyword * 0.4) + (semantic * 0.6))
    
    return {
        "final": combined,
        "keyword": keyword,
        "semantic": semantic
    }