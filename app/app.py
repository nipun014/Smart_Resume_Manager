from flask import Flask, render_template, request
from pathlib import Path
import sys, os
import time


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scoring.jd_skill_extractor import extract_jd_profile, extract_skills
from scoring.scorer import score_candidate
from scoring.justification import generate_justification
from parser_v1.loader import load_file        # reads the file -> gives you raw text
from parser_v1.parser import split_sections   # splits text into sections
from parser_v1.section_parsers import parse_experience, parse_skills  # extracts skills from parsed sections
from parser_v1.cleaner import clean_text
from scoring.final_scorer import final_score
from profile.builder import build_profile



app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    request_start = time.perf_counter()
    jd_text = request.form.get("jd_text")        # get from form
    files = request.files.getlist("resumes")         # get uploaded files list
    candidates = []
    
    # Extract JD skills/profile once
    jd_profile = extract_jd_profile(jd_text)
    jd_skills = extract_skills(jd_text)

    for file in files:
        if not file or file.filename == '':
            continue
        
        # 1. save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        # 2. extract name from filename
        candidate_name = os.path.splitext(file.filename)[0]
        file_start = time.perf_counter()

        try:
            # 3. load → clean → parse → extract skills
            parse_start = time.perf_counter()
            resume_text = load_file(file_path)
            cleaned = clean_text(resume_text)
            sections = split_sections(cleaned)
            skills_text = " ".join([
                sections.get("skills", ""),
                sections.get("projects", ""),
                sections.get("experience", ""),
            ])
            candidate_skills = parse_skills(skills_text)
            experience_entries = parse_experience(sections.get("experience", ""))
            profile = build_profile(experience_entries, candidate_skills)
            parse_elapsed = time.perf_counter() - parse_start
            app.logger.info("[TIMING] %s parse/load: %.2fs", candidate_name, parse_elapsed)

            # 4. score
            score_start = time.perf_counter()
            scores = final_score(
                jd_text,
                jd_skills,
                resume_text,
                candidate_skills,
                profile=profile,
                jd_profile=jd_profile,
            )
            score_elapsed = time.perf_counter() - score_start
            app.logger.info("[TIMING] %s scoring: %.2fs", candidate_name, score_elapsed)
            

            matched_skills = [s for s in candidate_skills if s in jd_skills]
            missing_skills = [s for s in jd_skills if s not in candidate_skills]
            # 5. build candidate dict
            candidate = {
                "name": candidate_name,
                "filename": file.filename,
                "score": scores["final"],
                "keyword_score": scores["keyword"],
                "semantic_score": scores["semantic"],
                "experience_score": scores.get("experience", 0),
                "score_breakdown": scores,
                "skills": candidate_skills,
                "jd_skills": jd_skills,
                "resume_text": resume_text,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "profile": profile,
            }
            
            # 6. append to candidates
            candidates.append(candidate)
            app.logger.info(
                "[TIMING] %s loop total: %.2fs",
                candidate_name,
                time.perf_counter() - file_start,
            )
        except Exception as e:
            candidates.append({
                "name": candidate_name,
                "filename": file.filename,
                "error": str(e),
                "score": 0
            })
            app.logger.exception("Failed to process %s", candidate_name)
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    # sort candidates by score descending
    candidates = sorted([c for c in candidates if "error" not in c], 
                       key=lambda x: x["score"], reverse=True)
    
    # generate justification for top 5
    try:
        for candidate in candidates[:5]:
            just_start = time.perf_counter()
            candidate["justification"] = generate_justification(
                jd_text, 
                candidate.get("resume_text", ""),
                candidate["score"],
                jd_skills=jd_skills,
                candidate_skills=candidate.get("skills", []),
                scores=candidate.get("score_breakdown", {}),
                profile=candidate.get("profile", {}),
            )
            app.logger.info(
                "[TIMING] %s justification: %.2fs",
                candidate.get("name", "unknown"),
                time.perf_counter() - just_start,
            )
        for candidate in candidates:
            candidate.pop("resume_text", None)
    except Exception:
        # Justification generation may fail if API key missing; results still work
        pass

    app.logger.info("[TIMING] analyze request total: %.2fs", time.perf_counter() - request_start)
    
    # render results
    return render_template("results.html", candidates=candidates, jd_text=jd_text)
    
if __name__ == "__main__":
    app.run(debug=True)