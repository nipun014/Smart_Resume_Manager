import re


def clean_text(text):
	"""Normalize text to make extraction and splitting more reliable."""
	# Normalize line endings first so downstream regex works consistently.
	text = text.replace("\r\n", "\n").replace("\r", "\n")
	# Collapse tabs and repeated spaces into a single space.
	text = re.sub(r"\t+", " ", text)
	text = re.sub(r"[ ]{2,}", " ", text)
	# Keep at most one blank line between content blocks.
	text = re.sub(r"\n{3,}", "\n\n", text)
	return text.strip()
