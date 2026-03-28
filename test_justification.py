from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SCORING_DIR = ROOT / "scoring"
if str(SCORING_DIR) not in sys.path:
	sys.path.insert(0, str(SCORING_DIR))

from jd_skill_extractor import extract_skills
from scorer import score_candidate
from justification import generate_justification
from parser_v1.loader import load_file
from parser_v1.cleaner import clean_text
from parser_v1.parser import split_sections
from parser_v1.section_parsers import parse_skills

jd_path = ROOT / "sample_job_description.txt"
resume_path = ROOT / "computer-scientist-resume-example.png"

jd_text = jd_path.read_text(encoding="utf-8")
resume_text = load_file(str(resume_path))

jd_skills = extract_skills(jd_text)
candidate_skills = parse_skills(split_sections(clean_text(resume_text)).get("skills", ""))
score = score_candidate(jd_skills, candidate_skills)

print(f"Score: {score}%")
print(generate_justification(jd_text, resume_text, score))
