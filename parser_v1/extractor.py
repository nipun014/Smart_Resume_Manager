import re


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def extract_email(text):
	"""Return the first email found in text, or None."""
	match = EMAIL_PATTERN.search(text)
	return match.group(0) if match else None
