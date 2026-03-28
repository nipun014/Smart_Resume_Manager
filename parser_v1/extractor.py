import re


# Email patterns - expanded with multiple variations
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Phone patterns for various formats and countries.
# Higher priority patterns first (more specific to country/format).

# India: +91-XXXXX-XXXXX, +91 XXXXX XXXXX, 91XXXXX XXXXX, etc.
PHONE_INDIA_WITH_CC = re.compile(r"\+91[\s\-]?\d[\d\s\-]{8,10}\d")

# India without country code: 10 digits starting with valid prefixes (6-9).
PHONE_INDIA_LOCAL = re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")

# UK: +44-XXXX-XXXXXX, +44 20 XXXX XXXX, etc.
PHONE_UK_WITH_CC = re.compile(r"\+44[\s\-]?\d[\d\s\-]{9,11}\d")

# UK local: 10-11 digits starting with 0.
PHONE_UK_LOCAL = re.compile(r"(?<!\d)0\d{9,10}(?!\d)")

# US: +1-XXX-XXX-XXXX, (XXX) XXX-XXXX, 1-XXX-XXX-XXXX, etc.
PHONE_US_WITH_CC = re.compile(r"\+1[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}")

# US local: (XXX) XXX-XXXX or XXX-XXX-XXXX or XXX XXX XXXX.
PHONE_US_LOCAL = re.compile(r"(?<!\d)\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}(?!\d)")

# General international format: +CC-X...X with 7-15 digits total.
PHONE_INTERNATIONAL = re.compile(r"\+\d{1,3}[\s\-]?\d[\d\s\-]{6,15}\d")

# Generic: 7-15 digits with optional separators but no country code prefix.
PHONE_GENERIC = re.compile(r"(?<!\d)[\d\s\-()]{10,20}(?!\d)")


def extract_email(text):
	"""Return the most likely primary email, or None."""
	candidates = list(EMAIL_PATTERN.finditer(text))
	if not candidates:
		return None

	# Prefer top-of-document emails and avoid reference-signature contexts.
	context_penalties = ["reference", "referee", "principal", "prof", "hod", "department", "email id"]
	best_match = None
	best_score = float("inf")
	non_reference_found = False

	for match in candidates:
		start = match.start()
		window_start = max(0, start - 120)
		window_end = min(len(text), match.end() + 120)
		window = text[window_start:window_end].lower()

		penalty = start
		is_reference_context = False
		for token in context_penalties:
			if token in window:
				penalty += 3000
				is_reference_context = True

		if not is_reference_context:
			non_reference_found = True

		if penalty < best_score:
			best_score = penalty
			best_match = match.group(0)

	if not non_reference_found:
		return None

	return best_match


def extract_phone(text):
	"""
	Extract first phone number found in text.
	Tries international and country-specific patterns in priority order.
	Handles India, UK, US, and generic formats with/without country codes.
	Returns cleaned phone number string or None.
	"""
	patterns = [
		PHONE_INDIA_WITH_CC,
		PHONE_INDIA_LOCAL,
		PHONE_UK_WITH_CC,
		PHONE_UK_LOCAL,
		PHONE_US_WITH_CC,
		PHONE_US_LOCAL,
		PHONE_INTERNATIONAL,
		PHONE_GENERIC,
	]

	all_matches = []
	for pattern in patterns:
		for match in pattern.finditer(text):
			phone = re.sub(r"\s+", " ", match.group(0)).strip()
			if len(re.sub(r"\D", "", phone)) < 7:
				continue
			all_matches.append((match.start(), phone))

	if all_matches:
		# Favor top-most phone candidate; resume contact details usually appear early.
		all_matches.sort(key=lambda item: item[0])
		return all_matches[0][1]

	return None


def extract_all_phones(text):
	"""
	Extract all phone numbers found in text.
	Uses the same pattern priority as extract_phone().
	Returns a list of unique phone number strings.
	"""
	all_phones = []
	seen = set()

	patterns = [
		PHONE_INDIA_WITH_CC,
		PHONE_INDIA_LOCAL,
		PHONE_UK_WITH_CC,
		PHONE_UK_LOCAL,
		PHONE_US_WITH_CC,
		PHONE_US_LOCAL,
		PHONE_INTERNATIONAL,
		PHONE_GENERIC,
	]

	for pattern in patterns:
		for match in pattern.finditer(text):
			phone = match.group(0).strip()
			if phone not in seen:
				all_phones.append(phone)
				seen.add(phone)

	return all_phones
