import os
import sys

# Allow running as `python scoring/match.py` from repo root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from jd_skill_extractor import extract_skills
from scorer import score_candidate
from parser_v1.loader import load_file        # reads the file -> gives you raw text
from parser_v1.parser import split_sections   # splits text into sections
from parser_v1.section_parsers import parse_skills  # extracts skills from the skills section
from parser_v1.cleaner import clean_text
from final_scorer import final_score

import argparse
def match(jd_file, resume_file):
    jd_text =open(jd_file).read()
    
    jd_skills =extract_skills(jd_text)

    raw = load_file(resume_file)
    cleaned = clean_text(raw)
    sections = split_sections(cleaned)
    candidate_skills = parse_skills(sections.get("skills", ""))
    result = final_score(jd_text, jd_skills, raw, candidate_skills)


    print(f"Final Score:    {result['final']}%")
    print(f"Keyword Score:  {result['keyword']}%")
    print(f"Semantic Score: {result['semantic']}%")
    print(f"JD Skills:      {jd_skills}")
    print(f"Candidate Skills: {candidate_skills}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", required=True)
    parser.add_argument("--resume", required=True)
    args = parser.parse_args()
    match(args.jd, args.resume)
