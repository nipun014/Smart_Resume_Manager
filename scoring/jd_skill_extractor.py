import argparse
import json
import re
import sys


SKILL_ALIASES = {
    "Python": ["python", "python3", "python 3"],
    "Java": ["java", "core java"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "c sharp"],
    "JavaScript": ["javascript", "js", "java script"],
    "TypeScript": ["typescript", "ts", "type script"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sql server", "sqlite"],
    "NoSQL": ["nosql", "mongo", "mongodb", "cassandra", "dynamodb"],
    "React": ["react", "reactjs", "react js", "react.js"],
    "Angular": ["angular", "angularjs", "angular js"],
    "Vue.js": ["vue", "vuejs", "vue js", "vue.js"],
    "Node.js": ["node", "nodejs", "node js", "node.js"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi", "fast api"],
    "Spring Boot": ["spring boot", "springboot"],
    "TensorFlow": ["tensorflow", "tensor flow"],
    "PyTorch": ["pytorch", "py torch"],
    "Scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy", "num py"],
    "Git": ["git", "github", "gitlab", "bitbucket"],
    "Docker": ["docker", "containerization", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "Jenkins": ["jenkins"],
    "CI/CD": ["ci/cd", "ci cd", "continuous integration", "continuous delivery"],
    "Linux": ["linux", "unix"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "REST APIs": ["rest api", "rest apis", "restful api", "restful apis"],
    "GraphQL": ["graphql", "graph ql"],
    "Microservices": ["microservices", "micro services"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "cv"],
    "Data Structures": ["data structures", "dsa", "data structure"],
    "Algorithms": ["algorithms", "algorithm design"],
    "OOP": ["oop", "object oriented programming", "object-oriented programming"],
}


NOISE_PHRASES = [
    "good communication skills",
    "team player",
    "hardworking",
    "self motivated",
    "self-motivated",
    "problem solving",
    "leadership",
    "collaboration",
]


PREFIX_PATTERN = re.compile(
    r"\b(experience with|experience in|knowledge of|familiarity with|proficient in|hands on|hands-on)\b",
    re.IGNORECASE,
)

YEARS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)

HIGH_PRIORITY_MARKERS = (
    "must have",
    "mandatory",
    "required",
    "requirement",
)

LOW_PRIORITY_MARKERS = (
    "nice to have",
    "good to have",
    "preferred",
    "plus",
    "bonus",
)

PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _alias_to_pattern(alias):
    escaped = re.escape(alias.lower())
    escaped = escaped.replace(r"\ ", r"[\s\-\._/]+")
    return re.compile(r"(?<![A-Za-z0-9+#])" + escaped + r"(?![A-Za-z0-9+#])", re.IGNORECASE)


def _normalize_text(text):
    text = PREFIX_PATTERN.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_sentences(text):
    normalized = re.sub(r"[\r\n]+", "\n", text)
    chunks = re.split(r"[\n\.\;]+", normalized)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _detect_priority(text):
    lowered = text.lower()
    if any(marker in lowered for marker in HIGH_PRIORITY_MARKERS):
        return "high"
    if any(marker in lowered for marker in LOW_PRIORITY_MARKERS):
        return "low"
    return "medium"


def _extract_years(text):
    matches = YEARS_PATTERN.findall(text)
    if not matches:
        return 0.0
    return max(float(item) for item in matches)


def extract_jd_profile(job_description):
    text = _normalize_text(job_description or "")
    text_lower = text.lower()

    for phrase in NOISE_PHRASES:
        text_lower = text_lower.replace(phrase, " ")

    skill_positions = {}
    for canonical, aliases in SKILL_ALIASES.items():
        patterns = [_alias_to_pattern(alias) for alias in aliases]
        best_pos = None
        for pattern in patterns:
            match = pattern.search(text_lower)
            if match:
                pos = match.start()
                if best_pos is None or pos < best_pos:
                    best_pos = pos
        if best_pos is not None:
            skill_positions[canonical] = best_pos

    jd_profile = {"skills": {}}
    sentences = _split_sentences(job_description or "")

    for skill_name, _ in sorted(skill_positions.items(), key=lambda item: item[1]):
        aliases = SKILL_ALIASES.get(skill_name, [skill_name])
        patterns = [_alias_to_pattern(alias) for alias in aliases]

        required_years = 0.0
        priority_signals = set()

        for sentence in sentences:
            for pattern in patterns:
                if pattern.search(sentence):
                    sentence_years = _extract_years(sentence)
                    if sentence_years > required_years:
                        required_years = sentence_years

                    priority_signals.add(_detect_priority(sentence))
                    break

        if "high" in priority_signals:
            priority = "high"
        elif "low" in priority_signals:
            priority = "low"
        else:
            priority = "medium"

        jd_profile["skills"][skill_name] = {
            "required_years": required_years,
            "priority": priority,
        }

    return jd_profile


def extract_skills(job_description):
    jd_profile = extract_jd_profile(job_description)
    return list(jd_profile.get("skills", {}).keys())


def _read_input(input_file):
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            return f.read()

    if not sys.stdin.isatty():
        return sys.stdin.read()

    return ""


def main():
    parser = argparse.ArgumentParser(description="Strict job description skill extractor")
    parser.add_argument("--input-file", help="Path to a job description file")
    args = parser.parse_args()

    text = _read_input(args.input_file)
    skills = extract_skills(text)
    print(json.dumps(skills))


if __name__ == "__main__":
    main()
