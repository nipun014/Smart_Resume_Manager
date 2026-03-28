try:
    from .jd_skill_extractor import SKILL_ALIASES
except ImportError:
    # Fallback when running this file directly.
    from jd_skill_extractor import SKILL_ALIASES
def score_candidate(jd_skills, candidate_skills):
    # jd_skills = list of skills the job needs
    # candidate_skills = list of skills the candidate has
    # returns a number between 0 and 100
    score=0
    for i in jd_skills:
        for j in candidate_skills:
            if j.lower() in SKILL_ALIASES.get(i, [i]):
                score+= (1/len(jd_skills))*100
                break

    return round(score)

if __name__ == "__main__":
    jd = ["Python", "Machine Learning", "Docker"]
    candidate = ["python", "ML", "Django"]
    print(score_candidate(jd, candidate))