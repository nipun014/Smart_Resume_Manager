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


def _alias_to_pattern(alias):
    escaped = re.escape(alias.lower())
    escaped = escaped.replace(r"\ ", r"[\s\-\._/]+")
    return re.compile(r"(?<![A-Za-z0-9+#])" + escaped + r"(?![A-Za-z0-9+#])", re.IGNORECASE)


def _normalize_text(text):
    text = PREFIX_PATTERN.sub(" ", text)
    text = re.sub(r"\b\d+\+?\s*(years?|yrs?)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_skills(job_description):
    text = _normalize_text(job_description)
    text_lower = text.lower()

    for phrase in NOISE_PHRASES:
        text_lower = text_lower.replace(phrase, " ")

    first_positions = {}

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
            first_positions[canonical] = best_pos

    ordered = sorted(first_positions.items(), key=lambda item: item[1])
    return [name for name, _ in ordered]


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
