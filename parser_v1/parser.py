import re


SECTION_HEADER = re.compile(r"^[A-Z][A-Z &/\-]{2,}$")


def split_sections(text):
	"""Split resume-like text into section blocks by uppercase headers."""
	sections = {}
	current = "GENERAL"
	sections[current] = []

	for raw_line in text.splitlines():
		line = raw_line.strip()
		if not line:
			continue

		if SECTION_HEADER.match(line):
			current = line
			if current not in sections:
				sections[current] = []
			continue

		sections[current].append(line)

	result = {}
	for name, lines in sections.items():
		if lines:
			result[name] = "\n".join(lines).strip()
	return result