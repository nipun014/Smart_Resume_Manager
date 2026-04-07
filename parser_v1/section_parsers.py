import re
from datetime import datetime

DATE_RANGE_PATTERN = re.compile(
	r"(?P<start>(?:\d{1,2}[/-]\d{4}|[A-Za-z]{3,9}\s+\d{4}|\d{4}))\s*(?:-|–|—|to)\s*(?P<end>(?:\d{1,2}[/-]\d{4}|[A-Za-z]{3,9}\s+\d{4}|\d{4}|Present|Current|Now))",
	re.IGNORECASE,
)

EXPLICIT_DURATION_PATTERN = re.compile(
	r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)",
	re.IGNORECASE,
)


def parse_date(date_str):
	"""Parse resume date tokens into datetime. Handles Present/Current as now."""
	if not date_str:
		return None

	token = date_str.strip()
	token_lower = token.lower()
	if token_lower in {"present", "current", "now"}:
		return datetime.now()

	month_year_match = re.fullmatch(r"(\d{1,2})[/-](\d{4})", token)
	if month_year_match:
		month = int(month_year_match.group(1))
		year = int(month_year_match.group(2))
		if 1 <= month <= 12:
			return datetime(year, month, 1)

	year_only_match = re.fullmatch(r"\d{4}", token)
	if year_only_match:
		return datetime(int(token), 1, 1)

	for fmt in ("%b %Y", "%B %Y"):
		try:
			return datetime.strptime(token, fmt)
		except ValueError:
			continue

	return None


def compute_duration(start, end):
	"""Compute duration in years between two datetimes as a non-negative float."""
	if not start or not end:
		return 0.0

	months = (end.year - start.year) * 12 + (end.month - start.month)
	if end.day < start.day:
		months -= 1

	if months < 0:
		return 0.0

	return round(months / 12.0, 2)

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


def parse_experience(text):
	result = []

	role_keywords = [
		"developer", "engineer", "designer", "manager", "analyst",
		"consultant", "lead", "senior", "junior", "intern",
		"associate", "specialist", "coordinator", "officer", "executive",
		"director", "head", "chief", "principal", "architect",
		"scientist", "researcher", "administrator", "technician", "author",
		"team member",
	]

	def clean_line(value):
		return value.replace("•", "").replace("◦", "").strip(" ,-")

	def looks_like_role(value):
		value_lower = value.lower()
		return any(word in value_lower for word in role_keywords)

	def split_role_company_from_line(value):
		patterns = [
			r"^(.+?)\s+at\s+(.+)$",
			r"^(.+?)\s+@\s+(.+)$",
			r"^(.+?)\s+\|\s+(.+)$",
			r"^(.+?)\s+-\s+(.+)$",
		]
		for pattern in patterns:
			match = re.match(pattern, value, flags=re.IGNORECASE)
			if match:
				left = clean_line(match.group(1))
				right = clean_line(match.group(2))
				if looks_like_role(left):
					return left, right
				if looks_like_role(right):
					return right, left
				return left, right
		return "", ""

	def strip_duration_tail(value):
		return re.sub(r"\s+\d+\s+(Month|Months|Year|Years)\b.*$", "", value, flags=re.IGNORECASE).strip(" ,-")

	# Split into entry blocks by bullets so multiple experiences are preserved.
	entry_blocks = []
	current = []
	for raw_line in text.split("\n"):
		line = raw_line.strip()
		if not line:
			continue

		is_bullet_start = raw_line.strip().startswith("•") or raw_line.strip().startswith("◦")
		if is_bullet_start and current:
			entry_blocks.append(current)
			current = [line]
		else:
			current.append(line)

	if current:
		entry_blocks.append(current)

	for block in entry_blocks:
		cleaned_lines = [clean_line(line) for line in block if clean_line(line)]
		if not cleaned_lines:
			continue

		title = cleaned_lines[0]
		if "team size" in title.lower() or "first author" in title.lower():
			continue
		description = " ".join(cleaned_lines)

		date_range = ""
		duration_years = 0.0
		duration_source = "none"
		confidence = "low"

		best_date_years = 0.0
		best_date_range = ""
		for date_match in DATE_RANGE_PATTERN.finditer(description):
			start_raw = date_match.group("start")
			end_raw = date_match.group("end")
			start_date = parse_date(start_raw)
			end_date = parse_date(end_raw)
			computed_years = compute_duration(start_date, end_date)
			if computed_years > best_date_years:
				best_date_years = computed_years
				best_date_range = f"{start_raw} - {end_raw}"

		if best_date_years > 0:
			date_range = best_date_range
			duration_years = best_date_years
			duration_source = "date_range"
			confidence = "high"

		if duration_source == "none":
			explicit_duration = extract_duration_from_text(description)
			if explicit_duration > 0:
				duration_years = explicit_duration
				duration_source = "explicit_text"
				confidence = "medium"

		if duration_source == "none":
			desc_lower = description.lower()
			if "summer intern" in desc_lower:
				duration_years = 0.25
				duration_source = "heuristic"
				confidence = "low"
			elif "internship" in desc_lower:
				explicit_intern_duration = extract_duration_from_text(description)
				if explicit_intern_duration > 0:
					duration_years = explicit_intern_duration
					duration_source = "explicit_text"
					confidence = "medium"
				else:
					duration_years = 0.3
					duration_source = "heuristic"
					confidence = "low"
			elif "intern" in desc_lower:
				duration_years = 0.3
				duration_source = "heuristic"
				confidence = "low"

		role = "Not specified"
		company = strip_duration_tail(title) if title else "Not specified"

		# One-line role/company parsing when possible.
		parsed_role, parsed_company = split_role_company_from_line(title)
		if parsed_role and parsed_company:
			role = parsed_role
			company = strip_duration_tail(parsed_company)

		# Find role from the remaining lines (supports role on next line).
		if role == "Not specified":
			for candidate in cleaned_lines[1:]:
				if looks_like_role(candidate):
					role = strip_duration_tail(candidate)
					break

		# Research-intern fallback when OCR misses exact role title.
		desc_lower = description.lower()
		if role == "Not specified" and ("conducted research" in desc_lower or "research" in desc_lower):
			role = "Research Intern"

		entry = {
			"title": title,
			"company": company if company else "Not specified",
			"role": role if role else "Not specified",
			"date_range": date_range,
			"duration_years": float(duration_years),
			"duration_source": duration_source,
			"confidence": confidence,
			"description": description,
		}
		result.append(entry)

	return result

def is_valid_skill(skill):
	"""Validate that extracted text is actually a skill, not a fragment."""
	if not skill:
		return False

	skill_lower = skill.lower()

	# Reject obvious fragments and non-skills
	reject_fragments = [
		# Articles and prepositions
		"the ", "a ", "an ", "and ", "or ", "with ", "of ", "in ", "at ", "to ", "for ",
		# Time-related (fragments like "1 Month", "3 Months")
		"month", "months", "week", "weeks", "day", "days", "hour", "hours", "year", "years",
		# Structural markers from descriptions
		"guidance of", "under the", "based on", "related to", "responsible for",
		"experience in", "familiar with", "proficient", "knowledge of",
		# Incomplete phrases  
		"and time", "classroom", "faculty", "satisfying", "scheduling",
		# Labels/headers
		"technologies used", "skills:", "technical skills", "requirements",
		# Education/org markers
		"department of", "university of", "college of", "academy", "campus",
		"hod", "principal", "professor", "dr.", "prof.",
	]

	for fragment in reject_fragments:
		if fragment in skill_lower:
			return False

	if "team size" in skill_lower:
		return False

	# Reject if starts with lowercase or special chars (likely mid-sentence fragment)
	

	# Reject if too long or too short
	if len(skill.strip()) < 2 or len(skill.strip()) > 50:
		return False

	# Reject if mostly numbers
	if sum(c.isdigit() for c in skill) > len(skill) * 0.5:
		return False

	return True
def parse_skills(text):
	"""Extract skills from text with smart description detection."""
	skills = []

	# Common prefixes/delimiters to remove
	skill_prefixes = [
		"•", "◦", "◆", "-", "*", "+", "→",
		"Technical Skills:", "Soft Skills:", "Hard Skills:",
		"Proficiencies:", "Competencies:", "Tools:", "Technologies:",
		"Languages:", "Frameworks:", "Platforms:", "Libraries:",
		"Software:", "Hardware:", "Databases:", "Systems:",
		"Key Skills:", "Core Skills:", "Specialized Skills:",
	]

	# Red flags indicating a description/narrative line (not a skill list)
	description_verbs = [
		"conducted", "developed", "built", "created", "designed", "implemented",
		"managed", "led", "executed", "improved", "enhanced", "optimized",
		"analyzed", "worked", "contributed", "collaborated", "achieved",
		"completed", "delivered", "resolved", "solved", "installed",
		"configured", "trained", "taught", "supervised", "organized",
		"satisfied", "scheduled", "automated", "generated"
	]

	description_prepositions = [
		"under the", "on the", "in the", "for the", "where", "while satisfying",
		"using", "based on", "throughout"
	]

	for line in text.split("\n"):
		line = line.strip()

		# Skip empty lines
		if not line:
			continue

		# ❌ Skip lines that are long descriptions (likely narrative text)
		# Check for description indicators: length + verb + preposition
		if len(line) > 80:
			line_lower = line.lower()
			has_verb = any(verb in line_lower for verb in description_verbs)
			has_prep = any(prep in line_lower for prep in description_prepositions)
			is_skill_list = line.count(",") >= 3
			
			if (has_verb or has_prep) and not is_skill_list:
				continue

		# Remove known prefixes
		for prefix in skill_prefixes:
			line = line.replace(prefix, "")

		line = line.strip()
		if not line:
			continue

		# If line is still very long, it's probably a description
		if len(line) > 100 and line.count(",") < 3:
			continue

		# Split by common delimiters
		parts = line.replace("|", ",").replace(";", ",").replace("/", ",").split(",")

		for p in parts:
			skill = p.strip()

			# Basic length check
			if len(skill) < 2 or len(skill) > 50:
				continue

			# Reject obvious fragments/non-skills
			if skill.lower() in ["and", "the", "of", "or", "in", "at", "to"]:
				continue

			skills.append(skill)
	
	# Validate and deduplicate
	validated_skills = []
	for skill in skills:
		if is_valid_skill(skill):
			validated_skills.append(skill)
	
	return list(set(validated_skills))


def extract_duration_from_text(text):
	"""Extract explicit durations like '2 years', '1 year 6 months', or '6 months'."""
	best_years = 0.0
	last_year_value = None
	last_year_end = -1

	for match in EXPLICIT_DURATION_PATTERN.finditer(text):
		value = float(match.group(1))
		unit = match.group(2).lower()

		if "year" in unit or "yr" in unit:
			if value > best_years:
				best_years = value
			last_year_value = value
			last_year_end = match.end()
		elif "month" in unit or "mo" in unit:
			month_years = value / 12.0
			if month_years > best_years:
				best_years = month_years

			# Combine adjacent year + month tokens such as "1 year 6 months".
			if last_year_value is not None:
				gap = match.start() - last_year_end
				if 0 <= gap <= 8:
					combined = last_year_value + month_years
					if combined > best_years:
						best_years = combined

	return round(best_years, 2)