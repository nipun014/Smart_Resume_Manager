import re


SECTION_MAP = {
    "summary": [
        "summary",
        "professional summary",
        "career summary",
        "profile",
        "professional profile",
        "about me",
        "overview",
        "executive summary",
        "personal statement",
        "career profile",
        "career snapshot",
        "candidate profile",
        "highlights",
        "key highlights",
    ],
    "objective": [
        "objective",
        "career objective",
        "professional objective",
        "employment objective",
        "job objective",
        "objective statement",
    ],
    "contact": [
        "contact",
        "contact details",
        "contact information",
        "personal details",
        "personal information",
        "reach me",
        "get in touch",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
        "job history",
        "relevant experience",
        "industry experience",
        "internship",
        "internships",
        "internship experience",
        "apprenticeship",
        "apprenticeships",
        "positions held",
        "roles and responsibilities",
        "work background",
    ],
    "education": [
        "education",
        "academic",
        "academic background",
        "academic history",
        "education background",
        "education history",
        "qualifications",
        "academic qualifications",
        "educational qualifications",
        "scholastic background",
        "degrees",
        "degree",
        "coursework",
        "relevant coursework",
    ],
    "projects": [
        "projects",
        "project",
        "academic projects",
        "professional projects",
        "personal projects",
        "key projects",
        "selected projects",
        "project experience",
        "portfolio projects",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "professional skills",
        "competencies",
        "core competencies",
        "key competencies",
        "strengths",
        "areas of expertise",
        "expertise",
        "technical expertise",
        "tools and technologies",
        "technologies",
        "technology stack",
        "software skills",
        "hard skills",
        "soft skills",
        "skills & interests",
        "skills and interests", 
        "technical skills",
        "skills & competencies"
    ],
    "certifications": [
        "certifications",
        "certification",
        "licenses",
        "licences",
        "license",
        "licence",
        "certificates",
        "courses",
        "training",
        "professional development",
        "credentials",
        "accreditations",
        "completed courses",
    ],
    "achievements": [
        "achievements",
        "accomplishments",
        "key achievements",
        "career achievements",
        "professional achievements",
        "milestones",
        "successes",
    ],
    "awards": [
        "awards",
        "honors",
        "honours",
        "awards and honors",
        "awards and honours",
        "recognition",
        "distinctions",
    ],
    "publications": [
        "publications",
        "publication",
        "papers",
        "research publications",
        "journal publications",
        "articles",
        "patents",
    ],
    "research": [
        "research",
        "research experience",
        "research work",
        "thesis",
        "dissertation",
    ],
    "volunteer": [
        "volunteer",
        "volunteering",
        "volunteer experience",
        "community service",
        "social work",
        "community involvement",
    ],
    "leadership": [
        "leadership",
        "leadership experience",
        "positions of responsibility",
        "position of responsibility",
        "extracurricular leadership",
    ],
    "activities": [
        "activities",
        "extracurricular activities",
        "co curricular activities",
        "clubs",
        "associations",
        "student activities",
    ],
    "languages": [
        "languages",
        "language",
        "language proficiency",
        "spoken languages",
        "linguistic skills",
    ],
    "interests": [
        "interests",
        "hobbies",
        "hobbies and interests",
        "personal interests",
    ],
    "references": [
        "references",
        "reference",
        "referees",
    ],
}


def normalize_header(text):
    """
    Normalize header text for case-insensitive comparison.
    Handles UPPERCASE, lowercase, Title Case, MiXeD CaSe, and other variations.
    Removes non-alphanumeric characters and collapses whitespace.
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def header_matches(input_text, keyword_text):
    """
    Check if input_text matches keyword_text in a case-insensitive manner.
    Supports exact match, prefix match, suffix match, and word-boundary match.
    All case variations (UPPERCASE, lowercase, Title Case, etc.) are normalized first.
    """
    input_norm = normalize_header(input_text)
    keyword_norm = normalize_header(keyword_text)

    # Exact match after normalization.
    if input_norm == keyword_norm:
        return True

    # Match at start with space boundary.
    if input_norm.startswith(keyword_norm + " "):
        return True

    # Match at end with space boundary.
    if input_norm.endswith(" " + keyword_norm):
        return True

    # Match in middle with word boundaries.
    wrapped_input = " " + input_norm + " "
    wrapped_keyword = " " + keyword_norm + " "
    words = input_norm.split()
    if keyword_norm in words:
        return True

    return False


def is_likely_header(line):
    """
    Simple heuristic to check if a line looks like a section header.
    Avoids matching body text that happens to contain keywords.
    Works with any case variation.
    """
    if len(line) > 80:
        return False

    words = line.strip().split()
    if len(words) > 8:
        return False

    if line.count(".") > 1:
        return False

    return True


def detect_section(line):
    """
    Detect if line is a section header and return the section name.
    Case-insensitive matching handles UPPERCASE, lowercase, Title Case, MiXeD CaSe.
    Returns the section key or None if no match found.
    """
    if not is_likely_header(line):
        return None

    for section, keywords in SECTION_MAP.items():
        for kw in keywords:
            if header_matches(line, kw):
                return section

    return None

def group_blocks(text):
    blocks = []
    current = []

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def looks_like_experience_line(line):
    """Heuristic for lines that likely belong to experience, even without a header."""
    lower = line.lower()

    # Avoid routing project headers into experience.
    if "team size" in lower or "first author" in lower:
        return False

    role_words = [
        "intern", "internship", "engineer", "developer", "analyst", "manager",
        "researcher", "research intern", "lead", "associate", "consultant",
    ]
    activity_words = ["conducted", "studied", "developed", "implemented", "worked"]
    org_words = [
        "department", "university", "college", "institute", "academy", "company",
        "technologies", "systems", "laboratory", "labs", "campus",
    ]

    has_duration = bool(re.search(r"\b\d+\s+(month|months|year|years)\b", lower))
    has_date_range = bool(re.search(r"\b(\d{4}|\d{1,2}/\d{4})\s*[-–]\s*(\d{4}|\d{1,2}/\d{4}|present|current)\b", lower))
    has_role = any(word in lower for word in role_words)
    has_activity = any(word in lower for word in activity_words)
    has_org = any(word in lower for word in org_words)

    return has_role or has_duration or has_date_range or has_activity or (has_org and "," in line)


def looks_like_skill_line(line):
    """Heuristic for lines that likely list skills/tools."""
    lower = line.lower()

    header_words = [
        "skills", "technical skills", "core skills", "key skills",
        "technologies used", "tools", "frameworks", "languages",
    ]
    tech_tokens = [
        "python", "java", "javascript", "html", "css", "sql", "node", "react",
        "express", "mongodb", "tensorflow", "pytorch", "c++", "c#", "c",
    ]

    if any(word in lower for word in header_words):
        return True

    tech_hits = sum(1 for token in tech_tokens if token in lower)
    return tech_hits >= 2

def split_sections(text):
    sections = {}
    current = "general"
    sections[current] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        detected = detect_section(line)

        if detected:
            current = detected
            if current not in sections:
                sections[current] = []
            continue

        # Recover from OCR/header misses by routing lines to a better section.
        if current == "skills":
            lower_line = line.lower()
            explicit_skill_markers = [
                "technical skills",
                "skills:",
                "technologies used",
                "tools:",
                "frameworks:",
                "languages:",
            ]
            is_explicit_skill_line = any(marker in lower_line for marker in explicit_skill_markers)

            # If line looks like experience and is not an explicit skill listing line, move it.
            if looks_like_experience_line(line) and not is_explicit_skill_line:
                current = "experience"
                if current not in sections:
                    sections[current] = []

        elif current == "experience" and looks_like_skill_line(line) and not looks_like_experience_line(line):
            current = "skills"
            if current not in sections:
                sections[current] = []

        sections[current].append(line)

    result = {}
    for key, values in sections.items():
        if values:
            result[key] = "\n".join(values).strip()
    if not result:
                result["general"] = text.strip()
    return result