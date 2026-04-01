import re


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

		date_pattern = r"(\d{1,2}/?\d{4}|\d{4})\s*[-–]\s*(\d{1,2}/?\d{4}|\d{4}|Present|Current)"
		dates = re.findall(date_pattern, description)
		date_range = ""
		if dates:
			date_range = f"{dates[0][0]} - {dates[0][1]}"

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

		# ✅ Only process short listing-style lines (skill lists, comma-separated)
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